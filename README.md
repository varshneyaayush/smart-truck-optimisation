# OPTIMOVE — Smart Truck Loading Optimization System

**Optimove** is a 3D logistics web application designed to optimize cargo arrangements inside freight trucks. It accounts for spatial boundaries, vehicle payloads, rear-door clearances, cargo orientations, gravity support, stackability, fragile cargo protection, and cumulative top loads.

Optimove is engineered with a strict **Data Privacy Architecture**: all calculations, placements, and operational reports are generated dynamically in temporary session memory and are **never** persisted to server-side databases or plan histories.

---

## 🎨 Approved Brand Theme

- **Primary Wine Red:** `#7F011F` (Headings, primary actions, active vehicle cards, key accents)
- **Light Sand:** `#F5EBD0` (Cards, surfaces, download actions, subtle headers)
- **Warm White:** `#FAF7F2` (Clean background and form inputs)
- **Neutral Borders:** `#E2D8C3`
- **Validation Green:** `#1E7E34` (Passed safety constraints)
- **Validation Red:** `#C82333` (Violations, collisions, and overloads)

---

## 🚀 Key Features

1. **Predefined Fleet Catalogue:**
   - Pre-configured vehicle categories: **T1 (14 ft)**, **T2 (17 ft)**, and **T3 (20 ft)**.
   - Transparent auditing of verified vs. reference estimated dimensions. Clear actionable warnings inform dispatchers when dimensions are based on industry benchmarks.
2. **Cargo Manifest Entry & Spreadsheet Upload:**
   - Interactive cargo editor supporting dimensions ($L \times W \times H$ in cm), unit weight (kg), quantity, fragile status, stackability, max top load, upright-only restrictions, and late-order tags.
   - Fast Excel (`.xlsx`) and CSV spreadsheet upload with fuzzy header alias mapping.
   - Built-in downloadable starter Excel and CSV templates.
3. **Genuine 3D Extreme-Point (EP) Packing Optimizer:**
   - Multi-tier Best-Fit-Decreasing (BFD) heuristic:
     - Heavy items anchored to lower tiers for stability and center of gravity.
     - Fragile items protected on top surfaces or isolated.
     - Non-stackable cargo placed without supporting layers above.
   - Collision-free 3D bounding box placements with exact coordinate assignment ($X, Y, Z$).
   - Honest solver reporting: Distinguishes between **Feasible**, **Partial**, and **Infeasible** loading states. Never fabricates fake placements or claims unsupported global optimality.
4. **Independent Physical Constraint Validation:**
   - Boundary limits ($0 \le X+L \le \text{Veh}_L$, $0 \le Y+W \le \text{Veh}_W$, $0 \le Z+H \le \text{Veh}_H$).
   - Rear doorway entry clearance.
   - Pairwise AABB 3D collision check.
   - Floating-box prevention with minimum 50% base contact area.
   - Non-stackable and fragile cargo protection.
   - Cumulative downward weight check against each item's permissible `max_top_load_kg`.
   - Certified vehicle gross payload capacity check.
5. **Interactive 3D Loading Visualization (Plotly):**
   - True-to-scale vehicle body envelope, cabin front marker, and rear door entry frame.
   - Color-coded cargo boxes with high-contrast outlines and distinct highlights for fragile and late items.
   - Hover inspection displaying coordinates, placed dimensions, weight, and sequence index.
   - Instant camera presets: **Isometric 3D**, **Top-Down (Plan)**, **Side Elevation**, and **Rear Door Entry**.
6. **Manual Placement Adjustments & Instant Revalidation:**
   - Allows operators to fine-tune coordinates ($X, Y, Z$) or rotate cargo.
   - Instant re-validation: Flagging collision overlaps, overhangs, or fragile crushing in real-time.
7. **Dynamic Late-Order Replanning:**
   - Seamlessly accommodates late-arriving urgent orders.
   - **Preservation Strategy:** Inserts new cargo into remaining volume without disturbing existing placements.
   - **Reorganization Strategy:** Re-optimizes entire stowage when necessary and authorized.
8. **Operational Reporting (PDF & Excel):**
   - Downloadable, executive PDF report generated using ReportLab.
   - Multi-sheet Excel workbook (`.xlsx`) generated using OpenPyXL with 4 structured sheets: *Executive Summary*, *Placed Cargo Manifest*, *Unplaced Items*, and *Validation Audit*.
   - Documents are compiled directly in-memory and streamed to the user's browser.

---

## 📁 Project Structure

```
optimove/
├── app.py                      # Main Streamlit web application & tab navigation
├── core/
│   ├── models.py               # Data models (Vehicle, CargoItem, PlacedInstance, OptimizationResult)
│   ├── vehicle_catalogue.py    # Predefined vehicle catalogue loader & verification auditor
│   ├── input_validation.py     # Manual input validation, spreadsheet parsing & template generation
│   ├── optimizer.py            # 3D Extreme Points constrained cargo packing engine
│   ├── placement_validator.py  # Independent physical and operational constraint validator
│   ├── replanner.py            # Late-order dynamic replanning module
│   └── metrics.py              # Logistics metrics & volume vs spatial utilization logic
├── visualization/
│   └── loading_3d.py           # Interactive Plotly 3D truck rendering & camera presets
├── reports/
│   ├── pdf_report.py           # Operational PDF report generator (ReportLab)
│   └── excel_report.py         # Multi-sheet Excel manifest generator (OpenPyXL)
├── data/
│   ├── vehicles.json           # Configurable fleet specifications & verification flags
│   ├── cargo_template.xlsx     # Starter Excel upload template
│   └── cargo_template.csv      # Starter CSV upload template
├── assets/
│   └── styles.css              # Custom CSS styling with wine-red & light-sand theme
├── tests/
│   ├── test_models.py          # Data model and instance expansion tests
│   ├── test_validation.py      # Spreadsheet parsing & boundary input tests
│   ├── test_placement_validator.py # Constraint audit, collision, and support tests
│   ├── test_optimizer.py       # 3D packing engine & failure reason tests
│   ├── test_replanner.py       # Late-order replanning & preservation tests
│   └── test_reports.py         # In-memory PDF & Excel consistency tests
├── .streamlit/
│   └── config.toml             # Streamlit server and theme configurations
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # System documentation
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Pip

### 1. Clone or Open the Workspace
```bash
cd "c:\Users\hp\Desktop\Smart Truck Optimisation"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
python -m pytest -v
```
All 25 automated unit and integration tests should pass.

### 4. Launch the Application
```bash
python -m streamlit run app.py
```
The application will launch and open in your default browser at `http://localhost:8501`.

---

## 📊 Units & Measurement Conventions

All internal calculations strictly enforce the following units:
- **Linear Dimensions ($L, W, H$):** Centimetres ($\text{cm}$)
- **Weight / Payload:** Kilograms ($\text{kg}$)
- **Volume:** Cubic Metres ($\text{m}^3$)
- **Coordinate System:**
  - Origin $(0, 0, 0)$ is at the front-left bottom corner (cabin end, floor level).
  - **$X$-axis:** Vehicle length (from front cabin $X=0$ to rear cargo door $X=L$).
  - **$Y$-axis:** Vehicle width (from left sidewall $Y=0$ to right sidewall $Y=W$).
  - **$Z$-axis:** Vehicle height (from floor bed $Z=0$ to roof $Z=H$).

---

## 🔒 Data Privacy & Temporary Storage Guarantee

Optimove does not use a persistent database. Placed coordinates, uploaded spreadsheets, and customer cargo items reside strictly in Python `st.session_state` in volatile server memory. When the user closes the browser or ends the session, temporary calculation states are cleared automatically.

---

## ⚠️ Operational Limitations & Roadmap

- **Axle Load Balance:** The current geometric packing model accounts for total gross payload and centers heavy cargo at lower tiers. Dynamic per-axle weight distribution calculations (front vs. rear axle) are planned for future fleet telemetry integration.
- **Unloading Sequences:** Loading sequence indices are assigned sequentially ($1, 2, \dots, N$) during placement. Multi-drop route sequencing (LIFO unloading) will be added in a subsequent release.
