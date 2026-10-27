"""
tests/test_validation.py
Tests for input validation, spreadsheet parsing, and unit consistency.
"""

import pytest
import pandas as pd
from core.input_validation import (
    validate_cargo_item_dict,
    parse_and_validate_dataframe,
    generate_cargo_template
)
from core.models import OrientationType


def test_valid_cargo_item_dict():
    raw = {
        "item_id": "BOX-01",
        "name": "Standard Carton",
        "length_cm": 50,
        "width_cm": 40,
        "height_cm": 30,
        "unit_weight_kg": 15.5,
        "quantity": 2,
        "fragile": "No",
        "stackable": "Yes",
        "max_top_load_kg": 100.0,
        "upright_only": "Yes"
    }
    item, errors, warnings = validate_cargo_item_dict(raw)
    assert errors == []
    assert item is not None
    assert item.item_id == "BOX-01"
    assert item.length_cm == 50.0
    assert item.quantity == 2
    assert item.orientation_mode == OrientationType.UPRIGHT_ONLY
    assert len(item.expand_instances()) == 2


def test_invalid_negative_and_zero_dimensions():
    raw = {
        "item_id": "BAD-DIM",
        "length_cm": -10,
        "width_cm": 0,
        "height_cm": "invalid",
        "unit_weight_kg": -5,
        "quantity": 0
    }
    item, errors, warnings = validate_cargo_item_dict(raw)
    assert item is None
    assert any("Length must be greater than 0" in e for e in errors)
    assert any("Width must be greater than 0" in e for e in errors)
    assert any("Height must be a valid positive number" in e for e in errors)
    assert any("Unit Weight must be greater than 0" in e for e in errors)
    assert any("Quantity must be a positive whole number" in e for e in errors)


def test_non_stackable_consistency():
    raw = {
        "item_id": "NO-STACK",
        "length_cm": 60,
        "width_cm": 40,
        "height_cm": 50,
        "unit_weight_kg": 20,
        "quantity": 1,
        "stackable": "No",
        "max_top_load_kg": 200 # Inconsistent: non-stackable with top load
    }
    item, errors, warnings = validate_cargo_item_dict(raw)
    assert errors == []
    assert item is not None
    assert item.stackable is False
    assert item.max_top_load_kg == 0.0 # Automatically zeroed for safety
    assert any("non-stackable; max top load is automatically set to 0 kg" in w for w in warnings)


def test_dataframe_missing_required_columns():
    df = pd.DataFrame([{"title": "Missing essential columns", "count": 5}])
    items, errors, warnings = parse_and_validate_dataframe(df)
    assert len(items) == 0
    assert any("missing required columns" in e for e in errors)


def test_dataframe_valid_upload():
    df = pd.DataFrame([
        {
            "Item ID": "CARTON-A",
            "Name": "Component A",
            "Length (cm)": 80,
            "Width (cm)": 60,
            "Height (cm)": 40,
            "Weight (kg)": 30,
            "Quantity": 3,
            "Fragile": False,
            "Stackable": True
        }
    ])
    items, errors, warnings = parse_and_validate_dataframe(df)
    assert errors == []
    assert len(items) == 1
    assert items[0].quantity == 3


def test_template_generation():
    excel_bytes = generate_cargo_template("excel")
    assert len(excel_bytes) > 1000
    csv_bytes = generate_cargo_template("csv")
    assert b"item_id" in csv_bytes
    assert b"length_cm" in csv_bytes
