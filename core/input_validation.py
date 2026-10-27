"""
core/input_validation.py
Provides robust input parsing and validation for cargo items entered manually
or uploaded via Excel/CSV spreadsheets.
Converts and normalises all measurements to standard internal units (cm, kg).
"""

import io
import re
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
from core.models import CargoItem, OrientationType


COLUMN_ALIASES = {
    "item_id": ["item_id", "id", "item id", "item code", "sku", "code", "cargo_id"],
    "name": ["name", "item_name", "description", "cargo name", "title"],
    "length_cm": ["length_cm", "length (cm)", "length", "l (cm)", "len", "length_in_cm"],
    "width_cm": ["width_cm", "width (cm)", "width", "w (cm)", "wid", "width_in_cm"],
    "height_cm": ["height_cm", "height (cm)", "height", "h (cm)", "hgt", "height_in_cm"],
    "unit_weight_kg": ["unit_weight_kg", "weight_kg", "unit weight (kg)", "weight (kg)", "weight", "unit weight"],
    "quantity": ["quantity", "qty", "count", "units", "pieces"],
    "fragile": ["fragile", "is_fragile", "fragile_status"],
    "stackable": ["stackable", "is_stackable", "can_stack", "stackable_status"],
    "max_top_load_kg": ["max_top_load_kg", "max_top_load (kg)", "max_top_load", "top_load_kg", "max load on top (kg)"],
    "upright_only": ["upright_only", "keep_upright", "upright", "vertical_only"],
    "orientation_mode": ["orientation_mode", "permitted_orientations", "orientation", "rotations_allowed"],
    "is_late_order": ["is_late_order", "late_order", "late", "late_order_indicator"]
}


def _match_column(col_name: str) -> Optional[str]:
    cleaned = re.sub(r"[_\s\-]+", " ", str(col_name).strip().lower())
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if cleaned == alias or cleaned == alias.replace("_", " "):
                return canonical
    return None


def parse_boolean(val: Any, default: bool = False) -> bool:
    if val is None or pd.isna(val):
        return default
    s = str(val).strip().lower()
    if s in ["true", "1", "yes", "y", "t"]:
        return True
    if s in ["false", "0", "no", "n", "f"]:
        return False
    return default


def parse_orientation_mode(val: Any, upright_only: bool) -> OrientationType:
    if upright_only:
        return OrientationType.UPRIGHT_ONLY
    if val is None or pd.isna(val):
        return OrientationType.UPRIGHT_ONLY
    s = str(val).strip().upper()
    if "FIX" in s or "NO" in s or "NONE" in s:
        return OrientationType.FIXED
    if "ALL" in s or "6" in s or "ANY" in s:
        return OrientationType.ALL
    return OrientationType.UPRIGHT_ONLY


def validate_cargo_item_dict(raw: Dict[str, Any], row_idx: Optional[int] = None) -> Tuple[Optional[CargoItem], List[str], List[str]]:
    """
    Validates a single cargo item dictionary.
    Returns: (CargoItem or None, list_of_errors, list_of_warnings)
    """
    errors = []
    warnings = []
    prefix = f"Row {row_idx}: " if row_idx is not None else ""

    item_id = str(raw.get("item_id", "")).strip()
    name = str(raw.get("name", "")).strip()
    if not item_id and not name:
        errors.append(f"{prefix}Missing required item identifier (Item ID or Name).")
    elif not item_id:
        item_id = name
    elif not name:
        name = item_id

    # Dimensions
    dim_keys = [("length_cm", "Length"), ("width_cm", "Width"), ("height_cm", "Height")]
    dims = {}
    for key, label in dim_keys:
        val = raw.get(key)
        if val is None or pd.isna(val) or str(val).strip() == "":
            errors.append(f"{prefix}{label} dimension is required.")
            continue
        try:
            num = float(val)
            if num <= 0:
                errors.append(f"{prefix}{label} must be greater than 0 (got {num}).")
            else:
                dims[key] = num
        except (ValueError, TypeError):
            errors.append(f"{prefix}{label} must be a valid positive number (got '{val}').")

    # Weight
    weight_val = raw.get("unit_weight_kg")
    weight = 0.0
    if weight_val is None or pd.isna(weight_val) or str(weight_val).strip() == "":
        errors.append(f"{prefix}Unit Weight (kg) is required.")
    else:
        try:
            weight = float(weight_val)
            if weight <= 0:
                errors.append(f"{prefix}Unit Weight must be greater than 0 (got {weight}).")
        except (ValueError, TypeError):
            errors.append(f"{prefix}Unit Weight must be a valid positive number (got '{weight_val}').")

    # Quantity
    qty_val = raw.get("quantity", 1)
    quantity = 1
    if qty_val is None or pd.isna(qty_val) or str(qty_val).strip() == "":
        quantity = 1
    else:
        try:
            qty_num = float(qty_val)
            if not qty_num.is_integer() or qty_num < 1:
                errors.append(f"{prefix}Quantity must be a positive whole number >= 1 (got {qty_val}).")
            else:
                quantity = int(qty_num)
        except (ValueError, TypeError):
            errors.append(f"{prefix}Quantity must be an integer (got '{qty_val}').")

    # Booleans & constraints
    fragile = parse_boolean(raw.get("fragile"), default=False)
    stackable = parse_boolean(raw.get("stackable"), default=True)
    upright_only = parse_boolean(raw.get("upright_only"), default=True)
    is_late_order = parse_boolean(raw.get("is_late_order"), default=False)
    orientation_mode = parse_orientation_mode(raw.get("orientation_mode"), upright_only=upright_only)

    # Max top load
    max_top_val = raw.get("max_top_load_kg", 0.0)
    max_top_load = 0.0
    if max_top_val is not None and not pd.isna(max_top_val) and str(max_top_val).strip() != "":
        try:
            max_top_load = float(max_top_val)
            if max_top_load < 0:
                errors.append(f"{prefix}Maximum top load cannot be negative (got {max_top_load}).")
        except (ValueError, TypeError):
            errors.append(f"{prefix}Maximum top load must be numeric (got '{max_top_val}').")

    # Constraint consistency checks
    if fragile and stackable:
        warnings.append(f"{prefix}Item '{item_id}' is marked as fragile. Fragile items will not allow heavy items stacked on top.")
        if max_top_load > 50.0:
            warnings.append(f"{prefix}Item '{item_id}' is fragile with high top load ({max_top_load} kg). Capped top load for safety.")
            max_top_load = min(max_top_load, 20.0)

    if not stackable and max_top_load > 0:
        warnings.append(f"{prefix}Item '{item_id}' is non-stackable; max top load is automatically set to 0 kg.")
        max_top_load = 0.0

    if errors:
        return None, errors, warnings

    item = CargoItem(
        item_id=item_id,
        name=name,
        length_cm=dims["length_cm"],
        width_cm=dims["width_cm"],
        height_cm=dims["height_cm"],
        unit_weight_kg=weight,
        quantity=quantity,
        fragile=fragile,
        stackable=stackable,
        max_top_load_kg=max_top_load,
        upright_only=upright_only,
        orientation_mode=orientation_mode,
        is_late_order=is_late_order,
    )
    return item, errors, warnings


def parse_and_validate_dataframe(df: pd.DataFrame) -> Tuple[List[CargoItem], List[str], List[str]]:
    """
    Parses a pandas DataFrame, maps column names, and validates all rows.
    Returns: (list_of_valid_items, list_of_errors, list_of_warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []
    items: List[CargoItem] = []

    if df.empty:
        errors.append("Uploaded spreadsheet is empty. Please provide at least one cargo row.")
        return items, errors, warnings

    # Map column headers to canonical names
    col_mapping = {}
    for col in df.columns:
        canonical = _match_column(col)
        if canonical:
            col_mapping[col] = canonical

    # Check for essential required dimensions
    mapped_canonicals = set(col_mapping.values())
    required_canonicals = ["length_cm", "width_cm", "height_cm", "unit_weight_kg"]
    missing_required = [c for c in required_canonicals if c not in mapped_canonicals]
    if missing_required:
        readable = [c.replace("_cm", " (cm)").replace("_kg", " (kg)") for c in missing_required]
        errors.append(f"Spreadsheet is missing required columns: {', '.join(readable)}.")
        return items, errors, warnings

    # Rename dataframe columns
    df_renamed = df.rename(columns=col_mapping)

    for idx, row in df_renamed.iterrows():
        row_dict = row.to_dict()
        item, row_errors, row_warnings = validate_cargo_item_dict(row_dict, row_idx=idx + 2) # 1-based + header
        if row_errors:
            errors.extend(row_errors)
        else:
            if item:
                items.append(item)
        if row_warnings:
            warnings.extend(row_warnings)

    return items, errors, warnings


def generate_cargo_template(format_type: str = "excel") -> bytes:
    """
    Generates a starter cargo template with documentation and standard sample records.
    Supported formats: 'excel' (xlsx) or 'csv'.
    """
    sample_data = [
        {
            "item_id": "CRG-PLT-01",
            "name": "Standard Euro Pallet Goods",
            "length_cm": 120.0,
            "width_cm": 80.0,
            "height_cm": 140.0,
            "unit_weight_kg": 320.0,
            "quantity": 4,
            "fragile": "No",
            "stackable": "Yes",
            "max_top_load_kg": 400.0,
            "upright_only": "Yes",
            "orientation_mode": "UPRIGHT_ONLY",
            "is_late_order": "No"
        },
        {
            "item_id": "CRG-BOX-02",
            "name": "Electronics Cartons (Fragile)",
            "length_cm": 60.0,
            "width_cm": 40.0,
            "height_cm": 50.0,
            "unit_weight_kg": 25.0,
            "quantity": 10,
            "fragile": "Yes",
            "stackable": "No",
            "max_top_load_kg": 0.0,
            "upright_only": "Yes",
            "orientation_mode": "UPRIGHT_ONLY",
            "is_late_order": "No"
        },
        {
            "item_id": "CRG-CRATE-03",
            "name": "Heavy Industrial Castings",
            "length_cm": 90.0,
            "width_cm": 70.0,
            "height_cm": 65.0,
            "unit_weight_kg": 180.0,
            "quantity": 6,
            "fragile": "No",
            "stackable": "Yes",
            "max_top_load_kg": 500.0,
            "upright_only": "No",
            "orientation_mode": "ALL",
            "is_late_order": "No"
        },
        {
            "item_id": "CRG-LATE-04",
            "name": "Priority Medical Supplies (Late Dispatch)",
            "length_cm": 50.0,
            "width_cm": 50.0,
            "height_cm": 40.0,
            "unit_weight_kg": 18.0,
            "quantity": 2,
            "fragile": "Yes",
            "stackable": "No",
            "max_top_load_kg": 0.0,
            "upright_only": "Yes",
            "orientation_mode": "UPRIGHT_ONLY",
            "is_late_order": "Yes"
        }
    ]
    df = pd.DataFrame(sample_data)

    if format_type.lower() == "csv":
        return df.to_csv(index=False).encode("utf-8")

    # Excel format
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Cargo List", index=False)
        # Add Instructions sheet
        instructions = pd.DataFrame([
            {"Column": "item_id", "Required": "Yes", "Unit": "Text", "Description": "Unique identifier for the item (e.g., BOX-101)"},
            {"Column": "name", "Required": "No", "Unit": "Text", "Description": "Human readable cargo description"},
            {"Column": "length_cm", "Required": "Yes", "Unit": "cm", "Description": "External length of item in centimetres (>0)"},
            {"Column": "width_cm", "Required": "Yes", "Unit": "cm", "Description": "External width of item in centimetres (>0)"},
            {"Column": "height_cm", "Required": "Yes", "Unit": "cm", "Description": "External height of item in centimetres (>0)"},
            {"Column": "unit_weight_kg", "Required": "Yes", "Unit": "kg", "Description": "Weight per individual unit in kilograms (>0)"},
            {"Column": "quantity", "Required": "Yes", "Unit": "Count", "Description": "Number of identical units (integer >= 1)"},
            {"Column": "fragile", "Required": "No", "Unit": "Yes/No", "Description": "If Yes, cannot support heavy items on top"},
            {"Column": "stackable", "Required": "No", "Unit": "Yes/No", "Description": "If No, other items cannot be placed on top"},
            {"Column": "max_top_load_kg", "Required": "No", "Unit": "kg", "Description": "Maximum permissible cumulative weight stacked on top"},
            {"Column": "upright_only", "Required": "No", "Unit": "Yes/No", "Description": "If Yes, height must stay vertical (rotations around Z allowed)"},
            {"Column": "orientation_mode", "Required": "No", "Unit": "UPRIGHT_ONLY / ALL / FIXED", "Description": "Allowed 3D rotation modes"},
            {"Column": "is_late_order", "Required": "No", "Unit": "Yes/No", "Description": "Late-arriving cargo flag for replanning workflows"}
        ])
        instructions.to_excel(writer, sheet_name="Instructions & Units", index=False)

    buf.seek(0)
    return buf.getvalue()
