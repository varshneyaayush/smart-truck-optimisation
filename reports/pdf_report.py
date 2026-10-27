"""
reports/pdf_report.py
Generates downloadable, operational PDF reports using ReportLab.
Strictly in-memory generation; does not store plan history or files on disk.
"""

import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from core.models import OptimizationResult

# Approved brand colors
WINE_RED = colors.HexColor("#7F011F")
LIGHT_SAND = colors.HexColor("#F5EBD0")
WARM_WHITE = colors.HexColor("#FAF7F2")
DARK_CHARCOAL = colors.HexColor("#2C2C2C")
BORDER_COLOR = colors.HexColor("#D4C5A9")
VALID_GREEN = colors.HexColor("#1E7E34")
INVALID_RED = colors.HexColor("#C82333")


def generate_pdf_report(result: OptimizationResult) -> bytes:
    """
    Generates a PDF report bytes buffer from an OptimizationResult.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=WINE_RED
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=13,
        textColor=DARK_CHARCOAL
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=WINE_RED,
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=DARK_CHARCOAL
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=DARK_CHARCOAL
    )
    cell_regular = ParagraphStyle(
        "CellRegular",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=DARK_CHARCOAL
    )
    cell_header = ParagraphStyle(
        "CellHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # Title & Header
    story.append(Paragraph("OPTIMOVE — Smart Truck Loading Optimization", title_style))
    story.append(Paragraph(f"Operational Loading Manifest & Constraint Audit | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    story.append(Spacer(1, 10))

    # Vehicle Specifications Table
    v = result.vehicle
    veh_data = [
        [Paragraph("Selected Vehicle", cell_header), Paragraph(f"{v.label} ({v.id})", cell_regular),
         Paragraph("Category / Chassis", cell_header), Paragraph(f"{v.category}", cell_regular)],
        [Paragraph("Internal Length x Width x Height", cell_header), Paragraph(f"{v.internal_length_cm} x {v.internal_width_cm} x {v.internal_height_cm} cm", cell_regular),
         Paragraph("Door Opening (W x H)", cell_header), Paragraph(f"{v.door_width_cm} x {v.door_height_cm} cm", cell_regular)],
        [Paragraph("Internal Cargo Volume", cell_header), Paragraph(f"{v.internal_volume_m3:.2f} m³ (Nominal: {v.nominal_volume_m3:.2f} m³)", cell_regular),
         Paragraph("Maximum Certified Payload", cell_header), Paragraph(f"{v.max_payload_kg:,.1f} kg", cell_regular)],
    ]
    veh_table = Table(veh_data, colWidths=[130, 140, 130, 140])
    veh_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), WINE_RED),
        ("BACKGROUND", (2, 0), (2, -1), WINE_RED),
        ("BACKGROUND", (1, 0), (1, -1), WARM_WHITE),
        ("BACKGROUND", (3, 0), (3, -1), WARM_WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(veh_table)

    # Verification warning banner
    if not v.is_verified:
        warn_text = (
            f"<b>NOTICE:</b> {v.verification_status}. "
            "Internal boundaries and door clearance must be verified against actual physical chassis prior to real-world loading."
        )
        warn_p = Paragraph(warn_text, ParagraphStyle("Warn", parent=body_style, textColor=INVALID_RED, fontSize=8, leading=10))
        story.append(Spacer(1, 4))
        warn_table = Table([[warn_p]], colWidths=[540])
        warn_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_SAND),
            ("BOX", (0, 0), (-1, -1), 1, WINE_RED),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(warn_table)

    story.append(Spacer(1, 10))

    # Executive Metrics Summary
    story.append(Paragraph("Executive Loading Summary", section_heading))
    val_status_str = "VALID (Passed All Constraints)" if result.validation_result and result.validation_result.is_valid else "NON-COMPLIANT / REVISIONS NEEDED"
    val_color = VALID_GREEN if result.validation_result and result.validation_result.is_valid else INVALID_RED

    kpi_data = [
        [Paragraph("Optimization Status", cell_header), Paragraph(f"<b>{result.status}</b>", cell_bold),
         Paragraph("Independent Audit", cell_header), Paragraph(f"<b>{val_status_str}</b>", ParagraphStyle("Val", parent=cell_bold, textColor=val_color))],
        [Paragraph("Placed Items", cell_header), Paragraph(f"{len(result.placed_instances)} items", cell_regular),
         Paragraph("Unplaced Items", cell_header), Paragraph(f"{len(result.unplaced_instances)} items", cell_regular)],
        [Paragraph("Loaded Gross Weight", cell_header), Paragraph(f"{result.loaded_weight_kg:,.1f} kg", cell_regular),
         Paragraph("Remaining Payload Capacity", cell_header), Paragraph(f"{result.remaining_payload_kg:,.1f} kg", cell_regular)],
        [Paragraph("Volume Utilization", cell_header), Paragraph(f"{result.volume_utilization_pct:.1f}% ({result.placed_cargo_volume_m3:.2f} m³)", cell_regular),
         Paragraph("Spatial Bounding Envelope", cell_header), Paragraph(f"{result.spatial_utilization_pct:.1f}% ({result.spatial_bounding_volume_m3:.2f} m³)", cell_regular)]
    ]
    kpi_table = Table(kpi_data, colWidths=[130, 140, 130, 140])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#540015")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#540015")),
        ("BACKGROUND", (1, 0), (1, -1), LIGHT_SAND),
        ("BACKGROUND", (3, 0), (3, -1), LIGHT_SAND),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(kpi_table)

    story.append(Spacer(1, 10))

    # Placed Items Table (up to top 30 in PDF to maintain compact multi-page layout)
    story.append(Paragraph(f"Placed Cargo Manifest ({len(result.placed_instances)} items)", section_heading))
    manifest_headers = ["Seq #", "Instance ID", "Dimensions (L x W x H)", "Position (X, Y, Z)", "Weight", "Flags"]
    manifest_data = [[Paragraph(h, cell_header) for h in manifest_headers]]

    for p in result.placed_instances[:40]: # Show up to 40 items in PDF
        flags = []
        if p.fragile:
            flags.append("Fragile")
        if not p.stackable:
            flags.append("NoStack")
        if p.is_late_order:
            flags.append("Late")
        flag_str = ", ".join(flags) if flags else "Std"

        manifest_data.append([
            Paragraph(str(p.loading_sequence_index or "-"), cell_regular),
            Paragraph(p.instance_id, cell_bold),
            Paragraph(f"{p.placed_length_cm:.0f}x{p.placed_width_cm:.0f}x{p.placed_height_cm:.0f} cm", cell_regular),
            Paragraph(f"({p.x_cm:.0f}, {p.y_cm:.0f}, {p.z_cm:.0f}) cm", cell_regular),
            Paragraph(f"{p.weight_kg:.1f} kg", cell_regular),
            Paragraph(flag_str, cell_regular)
        ])

    manifest_table = Table(manifest_data, colWidths=[40, 110, 120, 120, 70, 80])
    manifest_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), WINE_RED),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WARM_WHITE, LIGHT_SAND]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(manifest_table)

    if len(result.placed_instances) > 40:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<i>... Showing first 40 of {len(result.placed_instances)} placed items. Download full Excel report for complete manifest.</i>", subtitle_style))

    # Unplaced Items
    if result.unplaced_instances:
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Unplaced Items ({len(result.unplaced_instances)} items)", section_heading))
        unplaced_data = [[
            Paragraph("Item ID", cell_header),
            Paragraph("Name", cell_header),
            Paragraph("Dimensions & Weight", cell_header),
            Paragraph("Verifiable Rejection Reason", cell_header)
        ]]
        for u_inst, reason in result.unplaced_instances[:20]:
            unplaced_data.append([
                Paragraph(u_inst.instance_id, cell_bold),
                Paragraph(u_inst.name, cell_regular),
                Paragraph(f"{u_inst.length_cm:.0f}x{u_inst.width_cm:.0f}x{u_inst.height_cm:.0f} cm ({u_inst.weight_kg:.1f} kg)", cell_regular),
                Paragraph(reason, cell_regular)
            ])
        unp_table = Table(unplaced_data, colWidths=[90, 110, 120, 220])
        unp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INVALID_RED),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WARM_WHITE, LIGHT_SAND]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(unp_table)

    # Privacy & Temporary Storage Notice
    story.append(Spacer(1, 14))
    notice = (
        "<b>DATA PRIVACY NOTICE:</b> Optimove processes all cargo arrangements dynamically in temporary session memory. "
        "No customer cargo manifests, dimensions, or vehicle loading outputs have been permanently stored on server-side databases."
    )
    story.append(Paragraph(notice, ParagraphStyle("Privacy", parent=body_style, fontSize=7.5, leading=10, textColor=DARK_CHARCOAL)))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
