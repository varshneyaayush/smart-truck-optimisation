"""
app.py
Optimove — Smart Truck Loading Optimization System
Enterprise Logistics Control Platform & 3D Cargo Optimization Engine

Brand Theme:
- Primary Wine Red: #7F011F
- Light Sand: #F5EBD0
- Warm White: #FAF7F2
- Deep Charcoal: #1F1F1F
"""

import io
import textwrap
from pathlib import Path
from typing import List, Dict, Any, Optional
import streamlit as st
import pandas as pd

# Core modules
from core.models import Vehicle, CargoItem, PlacedCargoInstance, OptimizationResult, OrientationType
from core.vehicle_catalogue import VehicleCatalogue
from core.input_validation import (
    validate_cargo_item_dict,
    parse_and_validate_dataframe,
    generate_cargo_template
)
from core.optimizer import PackingOptimizer
from core.placement_validator import PlacementValidator
from core.replanner import LateOrderReplanner
from core.metrics import compute_packing_metrics, METRIC_DEFINITIONS
from visualization.loading_3d import create_truck_3d_figure
from visualization.vehicle_art import get_vehicle_svg
from reports.excel_report import generate_excel_report
from reports.pdf_report import generate_pdf_report

# Page configuration
st.set_page_config(
    page_title="Optimove — Enterprise Smart Truck Loading Optimization",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Scoped CSS Design System
CSS_FILE = Path(__file__).resolve().parent / "assets" / "styles.css"
if CSS_FILE.exists():
    with open(CSS_FILE, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Initialize Session State
PAGES = [
    "1. Fleet Selection",
    "2. Cargo Manifest",
    "3. 3D Loading Plan",
    "4. Manual Adjustments",
    "5. Late Orders",
    "6. Reports & Audit"
]

def init_session_state():
    if "catalogue" not in st.session_state:
        st.session_state.catalogue = VehicleCatalogue()

    all_vehicles = st.session_state.catalogue.get_all()
    if "selected_vehicle_id" not in st.session_state:
        st.session_state.selected_vehicle_id = all_vehicles[0].id if all_vehicles else "T1"

    if "current_page" not in st.session_state:
        st.session_state.current_page = "1. Fleet Selection"

    if "cargo_items" not in st.session_state:
        # Standard benchmark starter cargo set
        st.session_state.cargo_items = [
            CargoItem("PLT-STD-01", "Standard Euro Pallet Cargo", 120.0, 80.0, 110.0, 240.0, quantity=4, stackable=True, max_top_load_kg=350.0, upright_only=True),
            CargoItem("BOX-MED-02", "Electronics Cartons (Fragile)", 60.0, 40.0, 40.0, 18.0, quantity=8, fragile=True, stackable=False, upright_only=True),
            CargoItem("CRT-IND-03", "Precision Mechanical Parts", 90.0, 70.0, 60.0, 150.0, quantity=4, stackable=True, max_top_load_kg=400.0, upright_only=False, orientation_mode=OrientationType.ALL),
        ]

    if "optimization_result" not in st.session_state:
        st.session_state.optimization_result = None

    if "highlighted_item_id" not in st.session_state:
        st.session_state.highlighted_item_id = None

    if "camera_view" not in st.session_state:
        st.session_state.camera_view = "isometric"

    if "late_cargo_items" not in st.session_state:
        st.session_state.late_cargo_items = []


init_session_state()


def get_selected_vehicle() -> Vehicle:
    veh = st.session_state.catalogue.get_by_id(st.session_state.selected_vehicle_id)
    if not veh:
        veh = st.session_state.catalogue.get_all()[0]
    return veh


# -------------------------------------------------------------
# Enterprise Header Shell
# -------------------------------------------------------------
def render_brand_header():
    active_v = get_selected_vehicle()
    res = st.session_state.optimization_result

    header_html = f"""
    <div class="optimove-brand-shell">
        <div class="brand-left">
            <div class="brand-icon-box">🚚</div>
            <div>
                <div class="brand-name">OPTIMOVE</div>
                <div class="brand-tagline">Enterprise 3D Truck Loading Optimization & Fleet Constraint Verification</div>
            </div>
        </div>
        <div class="brand-right-pills">
            <span class="shell-pill-fleet">🚛 Active: {active_v.label} ({active_v.id})</span>
            <span class="shell-pill-privacy">🔒 Session-Only State (Zero Disk Storage)</span>
        </div>
    </div>
    """
    st.html(header_html)


render_brand_header()


# -------------------------------------------------------------
# Interactive Navigation Bar (Single Primary Navigation)
# -------------------------------------------------------------
nav_cols = st.columns(len(PAGES))
for i, page_name in enumerate(PAGES):
    is_active = (st.session_state.current_page == page_name)
    btn_type = "primary" if is_active else "secondary"
    with nav_cols[i]:
        if st.button(page_name, key=f"nav_btn_{i}", use_container_width=True, type=btn_type):
            st.session_state.current_page = page_name
            st.rerun()

st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)


# =============================================================
# PAGE 1: FLEET SELECTION
# =============================================================
if st.session_state.current_page == "1. Fleet Selection":
    st.markdown("### Predefined Commercial Fleet Catalogue")
    st.write(
        "Select a verified or reference-configured vehicle chassis. "
        "The optimization engine uses its exact internal dimensions, rear door clearances, and payload rating."
    )

    vehicles = st.session_state.catalogue.get_all()
    v_cols = st.columns(len(vehicles))

    for idx, v in enumerate(vehicles):
        is_selected = (v.id == st.session_state.selected_vehicle_id)
        svg_markup = get_vehicle_svg(v.id, width="100%", height=140)

        with v_cols[idx]:
            with st.container(border=True):
                # Card Header
                active_badge_html = '<span style="background:#7F011F; color:#FFF; font-size:10.5px; font-weight:700; padding:2px 8px; border-radius:10px; float:right;">ACTIVE FLEET</span>' if is_selected else ''
                st.html(f"""
                <div style="margin-bottom:6px;">
                    {active_badge_html}
                    <div style="font-family:'Outfit',sans-serif; font-size:18px; font-weight:700; color:#7F011F;">{v.label}</div>
                    <div style="font-size:11.5px; color:#666; font-weight:500;">Chassis ID: <b>{v.id}</b> | Category: <b>{v.category}</b></div>
                </div>
                """)

                # Distinct Scaled Illustration
                st.html(svg_markup)

                # Organized Specifications Table (Zero code blocks, perfectly formatted)
                specs_html = f"""
                <table style="width:100%; border-collapse:collapse; margin-top:8px; margin-bottom:10px; font-size:12px;">
                    <tr style="border-bottom:1px dashed #EDE5D5;">
                        <td style="padding:4.5px 0; color:#666; font-weight:500;">Internal Length:</td>
                        <td style="padding:4.5px 0; color:#1F1F1F; font-weight:600; text-align:right;">{v.internal_length_cm:.0f} cm ({v.internal_length_cm/100:.2f} m)</td>
                    </tr>
                    <tr style="border-bottom:1px dashed #EDE5D5;">
                        <td style="padding:4.5px 0; color:#666; font-weight:500;">Internal Width:</td>
                        <td style="padding:4.5px 0; color:#1F1F1F; font-weight:600; text-align:right;">{v.internal_width_cm:.0f} cm ({v.internal_width_cm/100:.2f} m)</td>
                    </tr>
                    <tr style="border-bottom:1px dashed #EDE5D5;">
                        <td style="padding:4.5px 0; color:#666; font-weight:500;">Internal Height:</td>
                        <td style="padding:4.5px 0; color:#1F1F1F; font-weight:600; text-align:right;">{v.internal_height_cm:.0f} cm ({v.internal_height_cm/100:.2f} m)</td>
                    </tr>
                    <tr style="border-bottom:1px dashed #EDE5D5;">
                        <td style="padding:4.5px 0; color:#666; font-weight:500;">Doorway (W × H):</td>
                        <td style="padding:4.5px 0; color:#1F1F1F; font-weight:600; text-align:right;">{v.door_width_cm:.0f} × {v.door_height_cm:.0f} cm</td>
                    </tr>
                    <tr style="border-bottom:1px dashed #EDE5D5;">
                        <td style="padding:4.5px 0; color:#666; font-weight:500;">Max Payload Capacity:</td>
                        <td style="padding:4.5px 0; color:#7F011F; font-weight:700; text-align:right;">{v.max_payload_kg:,.0f} kg</td>
                    </tr>
                    <tr>
                        <td style="padding:4.5px 0; color:#666; font-weight:500;">Usable Bay Volume:</td>
                        <td style="padding:4.5px 0; color:#1F1F1F; font-weight:600; text-align:right;">{v.internal_volume_m3:.2f} m³ (Nominal: {v.nominal_volume_m3:.2f} m³)</td>
                    </tr>
                </table>
                """
                st.html(specs_html)

                # Verification Status Banner
                if v.is_verified:
                    st.html('<div style="background:#E8F5E9; color:#2E7D32; border:1px solid #A5D6A7; padding:4px 8px; border-radius:4px; font-size:10px; font-weight:600; margin-bottom:10px;">✓ Verified Fleet Build Sheet</div>')
                else:
                    st.html(f'<div style="background:#FFF8E1; color:#8D6E11; border:1px solid #FFE082; padding:4px 8px; border-radius:4px; font-size:10px; font-weight:600; margin-bottom:10px; line-height:1.3;">⚠️ {v.verification_status}</div>')

                # Integrated Selection Action
                if is_selected:
                    if st.button("✓ Active Selection — Configure Cargo →", key=f"btn_next_{v.id}", type="primary", use_container_width=True):
                        st.session_state.current_page = "2. Cargo Manifest"
                        st.rerun()
                else:
                    if st.button(f"Select {v.label}", key=f"btn_sel_{v.id}", use_container_width=True):
                        st.session_state.selected_vehicle_id = v.id
                        st.session_state.optimization_result = None
                        st.session_state.current_page = "2. Cargo Manifest"
                        st.rerun()

    active_v = get_selected_vehicle()
    st.markdown("---")
    st.info(
        f"**Active Fleet Vehicle:** **{active_v.label} ({active_v.id})** | "
        f"Max Payload: **{active_v.max_payload_kg:,.0f} kg** | "
        f"Internal Dimensions: **{active_v.internal_length_cm:.0f} × {active_v.internal_width_cm:.0f} × {active_v.internal_height_cm:.0f} cm** | "
        f"Doorway: **{active_v.door_width_cm:.0f} × {active_v.door_height_cm:.0f} cm**"
    )
    if not active_v.is_verified:
        st.warning(
            f"⚠️ **Actionable Notice:** {active_v.verification_status}. "
            "Please confirm internal body dimensions and door openings against your actual physical truck prior to dispatch."
        )


# =============================================================
# PAGE 2: CARGO MANIFEST (CLEAN & STRUCTURED)
# =============================================================
elif st.session_state.current_page == "2. Cargo Manifest":
    active_v = get_selected_vehicle()
    st.markdown("### Cargo Manifest Input & Spreadsheet Upload")
    st.write(
        f"Manage cargo consignments for **{active_v.label} ({active_v.id})**. "
        "Consignments can be loaded from quick benchmark presets, uploaded via spreadsheet, or entered manually."
    )

    # Top Control Bar: Presets & Template Downloads
    col_pre, col_tpl_xls, col_tpl_csv = st.columns([2.6, 1, 1])
    with col_pre:
        st.write("**Quick-Load Benchmark Consignments:**")
        p_c1, p_c2, p_c3 = st.columns(3)
        if p_c1.button("📦 Standard E-Commerce", use_container_width=True):
            st.session_state.cargo_items = [
                CargoItem("PLT-STD-01", "Standard Euro Pallets", 120.0, 80.0, 110.0, 220.0, quantity=4, stackable=True, max_top_load_kg=320.0, upright_only=True),
                CargoItem("BOX-MED-02", "Medium Distribution Cartons", 60.0, 40.0, 40.0, 15.0, quantity=12, stackable=True, max_top_load_kg=90.0, upright_only=True),
                CargoItem("BOX-SML-03", "Small Retail Boxes", 40.0, 30.0, 25.0, 8.0, quantity=20, stackable=True, upright_only=False, orientation_mode=OrientationType.ALL),
            ]
            st.session_state.optimization_result = None
            st.rerun()

        if p_c2.button("⚠️ Fragile Glass & Tech", use_container_width=True):
            st.session_state.cargo_items = [
                CargoItem("GLS-01", "Crated Glass Panes (Fragile)", 130.0, 40.0, 100.0, 85.0, quantity=3, fragile=True, stackable=False, upright_only=True),
                CargoItem("TECH-02", "High-Density Server Cartons", 70.0, 50.0, 45.0, 24.0, quantity=6, fragile=True, stackable=False, upright_only=True),
                CargoItem("SUPP-03", "Heavy Support Crates", 100.0, 80.0, 60.0, 280.0, quantity=4, fragile=False, stackable=True, max_top_load_kg=500.0, upright_only=True),
            ]
            st.session_state.optimization_result = None
            st.rerun()

        if p_c3.button("🏗️ Heavy Industrial", use_container_width=True):
            st.session_state.cargo_items = [
                CargoItem("ENG-01", "Diesel Engine Block (Non-Stackable)", 110.0, 90.0, 80.0, 750.0, quantity=2, stackable=False, upright_only=True),
                CargoItem("STEEL-02", "Fabricated Steel Castings", 120.0, 80.0, 70.0, 450.0, quantity=3, stackable=True, max_top_load_kg=900.0, upright_only=False, orientation_mode=OrientationType.ALL),
                CargoItem("PARTS-03", "Heavy Spare Parts Crates", 50.0, 40.0, 35.0, 35.0, quantity=8, stackable=True, max_top_load_kg=180.0, upright_only=True),
            ]
            st.session_state.optimization_result = None
            st.rerun()

    with col_tpl_xls:
        st.write("**Excel Template:**")
        st.download_button(
            label="📥 Download .xlsx Template",
            data=generate_cargo_template("excel"),
            file_name="optimove_cargo_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_tpl_csv:
        st.write("**CSV Template:**")
        st.download_button(
            label="📥 Download .csv Template",
            data=generate_cargo_template("csv"),
            file_name="optimove_cargo_template.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown("---")

    # Real-Time Manifest Capacity Gauges
    total_qty = sum(i.quantity for i in st.session_state.cargo_items)
    total_wt = sum(i.total_weight_kg for i in st.session_state.cargo_items)
    total_vol = sum(i.total_volume_m3 for i in st.session_state.cargo_items)
    payload_pct = (total_wt / active_v.max_payload_kg * 100) if active_v.max_payload_kg > 0 else 0
    vol_pct = (total_vol / active_v.internal_volume_m3 * 100) if active_v.internal_volume_m3 > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cargo SKU Types", f"{len(st.session_state.cargo_items)} lines")
    m2.metric("Total Physical Units", f"{total_qty} units")
    m3.metric("Gross Cargo Mass", f"{total_wt:,.1f} kg", f"{payload_pct:.1f}% of payload limit")
    m4.metric("Gross Cargo Volume", f"{total_vol:.2f} m³", f"{vol_pct:.1f}% of truck volume")

    if total_wt > active_v.max_payload_kg:
        st.warning(
            f"⚠️ **Payload Overload Notice:** Total cargo mass ({total_wt:,.1f} kg) exceeds vehicle payload limit "
            f"({active_v.max_payload_kg:,.0f} kg) by {total_wt - active_v.max_payload_kg:,.1f} kg. "
            "The optimizer will pack units up to legal payload capacity and flag unplaced items with verifiable reasons."
        )

    # Current Manifest Data Table
    st.markdown("#### Current Manifest Consignments")
    cargo_table_data = []
    for it in st.session_state.cargo_items:
        cargo_table_data.append({
            "Item ID": it.item_id,
            "Description": it.name,
            "Length (cm)": it.length_cm,
            "Width (cm)": it.width_cm,
            "Height (cm)": it.height_cm,
            "Unit Mass (kg)": it.unit_weight_kg,
            "Quantity": it.quantity,
            "Total Mass (kg)": it.total_weight_kg,
            "Total Vol (m³)": round(it.total_volume_m3, 3),
            "Fragile": "Yes (Top Isolated)" if it.fragile else "No",
            "Stackable": "Yes" if it.stackable else "No (Top Tier)",
            "Max Top Load": f"{it.max_top_load_kg:.0f} kg" if it.max_top_load_kg > 0 else "None",
            "Orientation Mode": it.orientation_mode.value,
        })
    df_cargo = pd.DataFrame(cargo_table_data)
    st.dataframe(df_cargo, use_container_width=True, hide_index=True)

    # Clean Consignment Management Tabs (Add, Upload, Delete)
    st.markdown("#### Consignment Management")
    c_tab_add, c_tab_upload, c_tab_delete = st.tabs([
        "➕ Add New Consignment Item",
        "📁 Spreadsheet Bulk Import",
        "🗑️ Remove Line Items"
    ])

    with c_tab_add:
        with st.form("add_cargo_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            with f1:
                st.markdown("**1. Identity & Quantities**")
                f_id = st.text_input("Item ID / SKU *", value=f"CRG-{len(st.session_state.cargo_items)+1:02d}")
                f_name = st.text_input("Cargo Description", value="Boxed Cargo")
                f_qty = st.number_input("Quantity (Units) *", min_value=1, max_value=500, value=2, step=1)
            with f2:
                st.markdown("**2. Dimensions & Mass**")
                f_l = st.number_input("Length (cm) *", min_value=1.0, max_value=1000.0, value=80.0, step=5.0)
                f_w = st.number_input("Width (cm) *", min_value=1.0, max_value=1000.0, value=60.0, step=5.0)
                f_h = st.number_input("Height (cm) *", min_value=1.0, max_value=1000.0, value=50.0, step=5.0)
                f_wt = st.number_input("Unit Weight (kg) *", min_value=0.1, max_value=20000.0, value=25.0, step=1.0)
            with f3:
                st.markdown("**3. Stacking & Handling Rules**")
                f_fragile = st.checkbox("Fragile Item (Isolated from top loads)", value=False)
                f_stackable = st.checkbox("Stackable (Can carry other items)", value=True)
                f_top_load = st.number_input("Max Permissible Top Load (kg)", min_value=0.0, max_value=10000.0, value=100.0 if not f_fragile else 0.0)
                f_upright = st.checkbox("Upright Only (Height stays vertical)", value=True)
                f_orient_mode = st.selectbox("Permitted 3D Orientations", ["UPRIGHT_ONLY", "ALL", "FIXED"], index=0)

            submitted = st.form_submit_button("Add Item to Manifest", type="primary")
            if submitted:
                raw_dict = {
                    "item_id": f_id,
                    "name": f_name,
                    "length_cm": f_l,
                    "width_cm": f_w,
                    "height_cm": f_h,
                    "unit_weight_kg": f_wt,
                    "quantity": f_qty,
                    "fragile": f_fragile,
                    "stackable": f_stackable,
                    "max_top_load_kg": f_top_load,
                    "upright_only": f_upright,
                    "orientation_mode": f_orient_mode,
                }
                new_item, errors, warnings = validate_cargo_item_dict(raw_dict)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    if warnings:
                        for w in warnings:
                            st.warning(w)
                    st.session_state.cargo_items.append(new_item)
                    st.session_state.optimization_result = None
                    st.success(f"Added item '{new_item.item_id}' to manifest.")
                    st.rerun()

    with c_tab_upload:
        st.write("Upload a client cargo manifest in `.xlsx` or `.csv` format:")
        uploaded_file = st.file_uploader(
            "Upload Spreadsheet",
            type=["xlsx", "csv"],
            help="Automatic column mapping recognizes Item ID, Dimensions, Weight, Quantity, Fragile, Stackable, and Top Load."
        )
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_up = pd.read_csv(uploaded_file)
                else:
                    df_up = pd.read_excel(uploaded_file)

                items_up, errs_up, warns_up = parse_and_validate_dataframe(df_up)
                if errs_up:
                    st.error("Spreadsheet validation failed with the following issues:")
                    for err in errs_up:
                        st.markdown(f"- ❌ {err}")
                else:
                    if warns_up:
                        st.warning("Spreadsheet uploaded with notifications:")
                        for w in warns_up:
                            st.markdown(f"- ⚠️ {w}")
                    st.session_state.cargo_items = items_up
                    st.session_state.optimization_result = None
                    st.success(f"✓ Successfully imported {len(items_up)} cargo lines ({sum(i.quantity for i in items_up)} total physical units).")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading uploaded spreadsheet: {str(e)}")

    with c_tab_delete:
        if st.session_state.cargo_items:
            del_c1, del_c2 = st.columns([3, 1])
            with del_c1:
                item_to_remove = st.selectbox(
                    "Select Consignment to Delete",
                    options=[f"{i.item_id} — {i.name} ({i.quantity} units)" for i in st.session_state.cargo_items],
                    key="select_remove_item"
                )
            with del_c2:
                st.write("&nbsp;")
                if st.button("🗑️ Delete Selected Line", use_container_width=True):
                    target_id = item_to_remove.split(" — ")[0]
                    st.session_state.cargo_items = [i for i in st.session_state.cargo_items if i.item_id != target_id]
                    st.session_state.optimization_result = None
                    st.rerun()
        else:
            st.info("No cargo items currently in manifest.")

    st.markdown("---")

    # Primary Optimization Trigger
    with st.container(border=True):
        p_c1, p_c2 = st.columns([3, 1])
        with p_c1:
            st.markdown("#### Ready to Calculate Stowage Arrangement?")
            st.caption(
                f"Calculates 3D constrained placement into **{active_v.label} ({active_v.id})**. "
                "Enforces non-overlap collisions, floor/box support, fragile isolation, and payload capacity."
            )
        with p_c2:
            st.write("&nbsp;")
            if st.button("🚀 Optimize & View 3D Loading Plan", type="primary", use_container_width=True):
                if not st.session_state.cargo_items:
                    st.error("Cannot optimize an empty manifest. Please enter or upload cargo items.")
                else:
                    with st.spinner(f"Solving 3D constrained stowage for {active_v.label}..."):
                        optimizer = PackingOptimizer(active_v)
                        opt_res = optimizer.pack(st.session_state.cargo_items)
                        st.session_state.optimization_result = opt_res
                        st.session_state.current_page = "3. 3D Loading Plan"
                        st.rerun()


# =============================================================
# PAGE 3: 3D LOADING PLAN (HERO EXPERIENCE & ACCURATE ANALYTICS)
# =============================================================
elif st.session_state.current_page == "3. 3D Loading Plan":
    res: Optional[OptimizationResult] = st.session_state.optimization_result
    active_v = get_selected_vehicle()

    if res is None:
        st.info("ℹ️ No loading plan has been generated yet.")
        st.write("Navigate to **Cargo Manifest** and click **Optimize & View 3D Loading Plan**.")
        if st.button("Go to Cargo Manifest →", type="primary"):
            st.session_state.current_page = "2. Cargo Manifest"
            st.rerun()
    else:
        # Contextual Action Bar (Only non-duplicate, relevant actions)
        act_col_left, act_col_reopt, act_col_pdf, act_col_xls = st.columns([2.5, 1, 1, 1])
        with act_col_left:
            st.markdown(f"### Loading Results — {active_v.label} ({active_v.id})")
        with act_col_reopt:
            if st.button("🔄 Re-Run Optimization", use_container_width=True):
                with st.spinner("Re-running 3D packing optimizer..."):
                    optimizer = PackingOptimizer(active_v)
                    st.session_state.optimization_result = optimizer.pack(st.session_state.cargo_items)
                    st.rerun()
        with act_col_pdf:
            pdf_bytes = generate_pdf_report(res)
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"optimove_report_{res.vehicle.id}_{res.status.lower()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with act_col_xls:
            excel_bytes = generate_excel_report(res)
            st.download_button(
                label="📥 Download Excel",
                data=excel_bytes,
                file_name=f"optimove_manifest_{res.vehicle.id}_{res.status.lower()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # Plan Feasibility & Validation Status Banner
        val_is_valid = res.validation_result.is_valid if res.validation_result else False
        if res.status == "FEASIBLE" and val_is_valid:
            st.html(f"""
            <div class="audit-banner-valid">
                <span style="font-size: 22px;">✓</span>
                <div>
                    <b>OPTIMAL FEASIBLE PLAN CONFIRMED</b> — All {len(res.placed_instances)} cargo items placed successfully.
                    Independent physical verification: PASSED (Zero collisions, verified floor/box support, payload compliant).
                </div>
            </div>
            """)
        elif res.status == "PARTIAL":
            st.html(f"""
            <div class="audit-banner-partial">
                <span style="font-size: 22px;">⚠️</span>
                <div>
                    <b>PARTIAL STOWAGE PLAN</b> — {len(res.placed_instances)} items placed, {len(res.unplaced_instances)} items unplaced.
                    {res.solver_message}
                </div>
            </div>
            """)
        else:
            st.html(f"""
            <div class="audit-banner-invalid">
                <span style="font-size: 22px;">❌</span>
                <div>
                    <b>PLAN INFEASIBLE OR CONSTRAINT VIOLATIONS DETECTED</b> —
                    {res.solver_message}
                </div>
            </div>
            """)

        # Space Analytics & Capacity Summary (Grouped clearly: Volume, Payload, Placement)
        remaining_vol_m3 = max(0.0, res.vehicle.internal_volume_m3 - res.placed_cargo_volume_m3)
        vol_est_label = " (Estimated)" if not res.vehicle.is_verified else ""

        col_vol, col_payload, col_placement = st.columns(3)

        with col_vol:
            with st.container(border=True):
                st.markdown(f"**📦 Volume Analytics{vol_est_label}**")
                st.markdown(f"Usable Internal Volume: **{res.vehicle.internal_volume_m3:.2f} m³**")
                st.markdown(f"Placed Cargo Volume: **{res.placed_cargo_volume_m3:.2f} m³**")
                st.markdown(f"Remaining Usable Volume: **{remaining_vol_m3:.2f} m³**")
                st.progress(min(1.0, res.volume_utilization_pct / 100.0))
                st.caption(f"**Volume Utilization: {res.volume_utilization_pct:.1f}%** (Unused volume is dispersed airspace).")

        with col_payload:
            with st.container(border=True):
                st.markdown("**⚖️ Payload Analytics**")
                payload_pct = (res.loaded_weight_kg / res.vehicle.max_payload_kg * 100.0) if res.vehicle.max_payload_kg > 0 else 0.0
                st.markdown(f"Maximum Payload: **{res.vehicle.max_payload_kg:,.0f} kg**")
                st.markdown(f"Loaded Cargo Mass: **{res.loaded_weight_kg:,.1f} kg**")
                st.markdown(f"Remaining Payload: **{res.remaining_payload_kg:,.1f} kg**")
                st.progress(min(1.0, payload_pct / 100.0))
                st.caption(f"**Payload Utilization: {payload_pct:.1f}%** of legal weight rating.")

        with col_placement:
            with st.container(border=True):
                st.markdown("**📐 Placement & Spatial Bounding**")
                total_req = len(res.placed_instances) + len(res.unplaced_instances)
                st.markdown(f"Cargo Units Placed: **{len(res.placed_instances)} / {total_req}**")
                st.markdown(f"Unplaced Cargo Units: **{len(res.unplaced_instances)} units**")
                st.markdown(f"Bounding Envelope: **{res.spatial_bounding_volume_m3:.2f} m³**")
                st.progress(min(1.0, res.spatial_utilization_pct / 100.0))
                st.caption(f"**Bounding Space Extent: {res.spatial_utilization_pct:.1f}%** ($X_{{max}} \\times Y_{{max}} \\times Z_{{max}}$).")

        # 3D Loading Viewport Header & Controls
        v_h1, v_h2, v_h3 = st.columns([2, 1, 1])
        with v_h1:
            st.markdown("#### 3D Cargo Loading Arrangement")
            st.caption("Modeled truck container body with rear door entry frame, front cabin bulkhead, and physical box placements.")
        with v_h2:
            cam_options = ["isometric", "top", "side", "rear"]
            cam_labels = {
                "isometric": "📐 Isometric 3D View",
                "top": "🗺️ Top-Down (Plan View)",
                "side": "↔️ Side Elevation",
                "rear": "🚪 Rear Doorway Entry"
            }
            cam_sel = st.selectbox(
                "Camera Perspective",
                cam_options,
                format_func=lambda x: cam_labels[x],
                index=cam_options.index(st.session_state.camera_view)
            )
            if cam_sel != st.session_state.camera_view:
                st.session_state.camera_view = cam_sel
                st.rerun()

        with v_h3:
            placed_ids = [p.instance_id for p in res.placed_instances]
            hl_sel = st.selectbox(
                "Highlight Cargo Item",
                ["None"] + placed_ids,
                index=0 if not st.session_state.highlighted_item_id or st.session_state.highlighted_item_id not in placed_ids else placed_ids.index(st.session_state.highlighted_item_id) + 1
            )
            st.session_state.highlighted_item_id = None if hl_sel == "None" else hl_sel

        # Render 3D Plotly Figure
        fig_3d = create_truck_3d_figure(
            vehicle=res.vehicle,
            placements=res.placed_instances,
            highlight_instance_id=st.session_state.highlighted_item_id,
            validation=res.validation_result,
            camera_view=st.session_state.camera_view
        )
        st.plotly_chart(fig_3d, use_container_width=True)

        # Tabbed Detail Manifests & Audit Log
        m_tab_placed, m_tab_unplaced, m_tab_audit = st.tabs([
            f"📋 Placed Cargo Manifest ({len(res.placed_instances)})",
            f"❌ Unplaced Items & Failure Reasons ({len(res.unplaced_instances)})",
            "🛡️ Independent Physical Constraints Audit Log"
        ])

        with m_tab_placed:
            if not res.placed_instances:
                st.write("No cargo items placed.")
            else:
                placed_rows = []
                for p in res.placed_instances:
                    placed_rows.append({
                        "Seq #": p.loading_sequence_index,
                        "Instance ID": p.instance_id,
                        "SKU / Name": p.name,
                        "Position X (cm)": f"{p.x_cm:.1f}",
                        "Position Y (cm)": f"{p.y_cm:.1f}",
                        "Position Z (cm)": f"{p.z_cm:.1f}",
                        "Placed Dims L×W×H (cm)": f"{p.placed_length_cm:.0f} × {p.placed_width_cm:.0f} × {p.placed_height_cm:.0f}",
                        "Mass (kg)": f"{p.weight_kg:.1f}",
                        "Orientation": p.orientation_label,
                        "Fragile": "Yes (Top Isolated)" if p.fragile else "No",
                        "Stackable": "Yes" if p.stackable else "No",
                        "Late Order": "Yes" if p.is_late_order else "No"
                    })
                st.dataframe(pd.DataFrame(placed_rows), use_container_width=True, hide_index=True)

        with m_tab_unplaced:
            if not res.unplaced_instances:
                st.success("✓ All requested cargo items have been placed into the vehicle.")
            else:
                st.warning(f"{len(res.unplaced_instances)} items could not be loaded into {active_v.label}:")
                unplaced_rows = []
                for u_inst, reason in res.unplaced_instances:
                    unplaced_rows.append({
                        "Instance ID": u_inst.instance_id,
                        "Consignment SKU": u_inst.name,
                        "Dimensions (L×W×H)": f"{u_inst.length_cm:.0f} × {u_inst.width_cm:.0f} × {u_inst.height_cm:.0f} cm",
                        "Unit Mass": f"{u_inst.weight_kg:.1f} kg",
                        "Verifiable Failure Reason": reason
                    })
                st.dataframe(pd.DataFrame(unplaced_rows), use_container_width=True, hide_index=True)

        with m_tab_audit:
            if res.validation_result:
                val = res.validation_result
                st.markdown("#### Independent Physical & Operational Constraints Audit")
                audit_rows = []
                for chk, ok in val.summary_checks.items():
                    readable = chk.replace("_", " ").title()
                    audit_rows.append({
                        "Safety & Operational Constraint": readable,
                        "Audit Status": "PASSED" if ok else "FAILED",
                        "Evaluation Finding": "Fully compliant with physical & fleet limits" if ok else "Constraint violation recorded"
                    })
                st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)

                if val.errors:
                    st.error("Constraint Violations:")
                    for e in val.errors:
                        st.markdown(f"- ❌ {e}")
                if val.warnings:
                    st.warning("Operational Safety Advisories:")
                    for w in val.warnings:
                        st.markdown(f"- ⚠️ {w}")


# =============================================================
# PAGE 4: MANUAL ADJUSTMENTS (OPTIONAL WORKFLOW)
# =============================================================
elif st.session_state.current_page == "4. Manual Adjustments":
    res = st.session_state.optimization_result
    st.markdown("### Manual Placement Adjustments & Fine-Tuning")
    st.write(
        "Fine-tune individual cargo item positions ($X, Y, Z$) or orientations. "
        "Every change immediately triggers the independent constraint validator to check boundaries, "
        "collisions, vertical support, fragility, and payload limits."
    )

    if not res or not res.placed_instances:
        st.info("ℹ️ Run 3D optimization first to generate a base plan before fine-tuning.")
        if st.button("Go to Cargo Manifest →", type="primary"):
            st.session_state.current_page = "2. Cargo Manifest"
            st.rerun()
    else:
        inst_ids = [p.instance_id for p in res.placed_instances]
        selected_adj_id = st.selectbox("Select Cargo Item to Reposition", inst_ids, key="manual_item_select")

        target_idx = next(i for i, p in enumerate(res.placed_instances) if p.instance_id == selected_adj_id)
        target_p = res.placed_instances[target_idx]

        st.markdown(f"**Target Item:** `{target_p.instance_id}` ({target_p.name}) | Weight: **{target_p.weight_kg:.1f} kg**")

        with st.form("manual_adjustment_form"):
            adj_col1, adj_col2, adj_col3, adj_col4 = st.columns(4)
            with adj_col1:
                new_x = st.number_input(
                    f"X Coordinate (cm) [0 to {res.vehicle.internal_length_cm:.0f}]",
                    min_value=-50.0,
                    max_value=float(res.vehicle.internal_length_cm + 50),
                    value=float(target_p.x_cm),
                    step=5.0
                )
            with adj_col2:
                new_y = st.number_input(
                    f"Y Coordinate (cm) [0 to {res.vehicle.internal_width_cm:.0f}]",
                    min_value=-50.0,
                    max_value=float(res.vehicle.internal_width_cm + 50),
                    value=float(target_p.y_cm),
                    step=5.0
                )
            with adj_col3:
                new_z = st.number_input(
                    f"Z Coordinate (cm) [0 to {res.vehicle.internal_height_cm:.0f}]",
                    min_value=-50.0,
                    max_value=float(res.vehicle.internal_height_cm + 50),
                    value=float(target_p.z_cm),
                    step=5.0
                )
            with adj_col4:
                valid_orients = target_p.instance.get_valid_orientations()
                orient_labels = [f"{lbl} ({ox:.0f}×{oy:.0f}×{oz:.0f} cm)" for ox, oy, oz, lbl in valid_orients]
                cur_idx = 0
                for i, (ox, oy, oz, lbl) in enumerate(valid_orients):
                    if (
                        abs(ox - target_p.placed_length_cm) < 0.1 and
                        abs(oy - target_p.placed_width_cm) < 0.1 and
                        abs(oz - target_p.placed_height_cm) < 0.1
                    ):
                        cur_idx = i
                        break
                new_orient_sel = st.selectbox("Permitted Orientation", orient_labels, index=cur_idx)
                chosen_tuple = valid_orients[orient_labels.index(new_orient_sel)]

            apply_adjustment = st.form_submit_button("Apply Changes & Revalidate Constraints", type="primary")

        if apply_adjustment:
            updated_p = PlacedCargoInstance(
                instance=target_p.instance,
                x_cm=round(new_x, 2),
                y_cm=round(new_y, 2),
                z_cm=round(new_z, 2),
                placed_length_cm=chosen_tuple[0],
                placed_width_cm=chosen_tuple[1],
                placed_height_cm=chosen_tuple[2],
                orientation_label=chosen_tuple[3],
                loading_sequence_index=target_p.loading_sequence_index
            )

            revised_placements = list(res.placed_instances)
            revised_placements[target_idx] = updated_p

            val_res = PlacementValidator.validate(res.vehicle, revised_placements)
            metrics = compute_packing_metrics(res.vehicle, revised_placements)

            res.placed_instances = revised_placements
            res.validation_result = val_res
            res.loaded_weight_kg = metrics["total_loaded_weight_kg"]
            res.remaining_payload_kg = metrics["remaining_payload_kg"]
            res.volume_utilization_pct = metrics["volume_utilization_pct"]
            res.spatial_utilization_pct = metrics["spatial_utilization_pct"]
            res.placed_cargo_volume_m3 = metrics["placed_volume_m3"]
            res.spatial_bounding_volume_m3 = metrics["bounding_volume_m3"]
            st.session_state.highlighted_item_id = updated_p.instance_id

            if val_res.is_valid:
                st.success(f"✓ Item '{updated_p.instance_id}' repositioned successfully. All safety constraints satisfied!")
            else:
                st.error("⚠️ Manual placement violated safety constraints:")
                for err in val_res.errors:
                    st.markdown(f"- ❌ {err}")

            st.rerun()

        st.markdown("---")
        if st.button("← Return to 3D Loading Plan", use_container_width=True):
            st.session_state.current_page = "3. 3D Loading Plan"
            st.rerun()


# =============================================================
# PAGE 5: LATE-ORDER REPLANNING
# =============================================================
elif st.session_state.current_page == "5. Late Orders":
    res = st.session_state.optimization_result
    st.markdown("### Late-Order Dynamic Replanning")
    st.write(
        "Incorporate urgent, late-arriving orders into the active loading plan. "
        "The replanner prioritizes inserting new cargo into available residual space without disturbing "
        "existing cargo positions."
    )

    if not res:
        st.info("ℹ️ Run initial optimization before accommodating late orders.")
        if st.button("Go to Cargo Manifest →", type="primary"):
            st.session_state.current_page = "2. Cargo Manifest"
            st.rerun()
    else:
        st.info(f"**Current Remaining Payload:** `{res.remaining_payload_kg:,.1f} kg` | **Remaining Space:** `{res.vehicle.internal_volume_m3 - res.placed_cargo_volume_m3:.2f} m³`")

        with st.form("late_order_form"):
            l1, l2, l3 = st.columns(3)
            with l1:
                late_id = st.text_input("Late Item ID", value=f"LATE-{len(st.session_state.late_cargo_items)+1:02d}")
                late_name = st.text_input("Cargo Description", value="Urgent Dispatch Parcel")
                late_qty = st.number_input("Quantity", min_value=1, max_value=50, value=2)
            with l2:
                late_l = st.number_input("Length (cm)", min_value=1.0, value=60.0)
                late_w = st.number_input("Width (cm)", min_value=1.0, value=50.0)
                late_h = st.number_input("Height (cm)", min_value=1.0, value=40.0)
            with l3:
                late_wt = st.number_input("Unit Weight (kg)", min_value=0.1, value=20.0)
                late_fragile = st.checkbox("Fragile Item", value=False)
                late_stackable = st.checkbox("Stackable", value=True)
                allow_reorg = st.checkbox("Allow reorganization if space-fitting fails", value=False)

            late_submitted = st.form_submit_button("⚡ Add Late Order & Replan Loading", type="primary")

        if late_submitted:
            raw_late = {
                "item_id": late_id,
                "name": late_name,
                "length_cm": late_l,
                "width_cm": late_w,
                "height_cm": late_h,
                "unit_weight_kg": late_wt,
                "quantity": late_qty,
                "fragile": late_fragile,
                "stackable": late_stackable,
                "max_top_load_kg": 50.0 if not late_fragile else 0.0,
                "upright_only": True,
                "is_late_order": True
            }
            late_item, errs, warns = validate_cargo_item_dict(raw_late)
            if errs:
                for err in errs:
                    st.error(err)
            else:
                replanner = LateOrderReplanner(res.vehicle)
                revised_res = replanner.replan(
                    current_result=res,
                    late_items=[late_item],
                    allow_reorganization=allow_reorg
                )
                st.session_state.optimization_result = revised_res
                st.session_state.late_cargo_items.append(late_item)

                if revised_res.status == "FEASIBLE" or "accommodated successfully" in revised_res.solver_message:
                    st.success(f"✓ {revised_res.solver_message}")
                else:
                    st.warning(f"⚠️ {revised_res.solver_message}")
                st.session_state.current_page = "3. 3D Loading Plan"
                st.rerun()


# =============================================================
# PAGE 6: REPORTS & OPERATIONAL AUDIT
# =============================================================
elif st.session_state.current_page == "6. Reports & Audit":
    res = st.session_state.optimization_result
    st.markdown("### Operational Reports & Export Centre")
    st.write(
        "Download official operational loading manifests and constraint audit reports in PDF and Excel formats. "
        "Generated dynamically in session memory without server disk retention."
    )

    if not res:
        st.info("ℹ️ Run optimization first to generate operational reports.")
        if st.button("Go to Cargo Manifest →", type="primary"):
            st.session_state.current_page = "2. Cargo Manifest"
            st.rerun()
    else:
        rep_col1, rep_col2 = st.columns(2)
        with rep_col1:
            st.markdown("""
                <div class="surface-card">
                    <div class="surface-card-title">📄 Printable PDF Loading Manifest</div>
                    <p style="font-size: 13px; color: #555; line-height: 1.4;">
                        Official logistics document containing vehicle specifications, verification audit notes,
                        executive utilization metrics, item placement coordinates, and safety certifications.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            pdf_bytes = generate_pdf_report(res)
            st.download_button(
                label="📥 Download PDF Loading Report",
                data=pdf_bytes,
                file_name=f"optimove_report_{res.vehicle.id}_{res.status.lower()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with rep_col2:
            st.markdown("""
                <div class="surface-card">
                    <div class="surface-card-title">📊 Structured Multi-Sheet Excel Workbook</div>
                    <p style="font-size: 13px; color: #555; line-height: 1.4;">
                        Professional Excel report with 4 formatted sheets: Executive Summary, Placed Cargo Manifest,
                        Unplaced Items with failure reasons, and Complete Constraint Audit Findings.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            excel_bytes = generate_excel_report(res)
            st.download_button(
                label="📥 Download Excel Manifest (.xlsx)",
                data=excel_bytes,
                file_name=f"optimove_manifest_{res.vehicle.id}_{res.status.lower()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("#### Temporary Storage & Data Privacy Certification")
        st.info(
            "🔒 **Data Privacy Enforced:** Optimove operates without a persistent backend database. "
            "All cargo consignments, coordinates, and reports reside in active session memory. "
            "Ending your session automatically discards all temporary plan data."
        )


# Restrained Enterprise Footer
st.html("""
<div style="text-align: center; margin-top: 45px; padding: 18px; border-top: 1px solid #E2D8C3; font-size: 11.5px; color: #777777;">
    <b>OPTIMOVE</b> Enterprise Smart Truck Loading Optimization System | Powered by 3D Extreme-Point Constrained Packing & Independent Safety Auditing
</div>
""")
