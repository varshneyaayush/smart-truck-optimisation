"""
tests/test_placement_validator.py
Tests for physical constraint checking in PlacementValidator.
"""

import pytest
from core.models import Vehicle, CargoItem, CargoInstance, PlacedCargoInstance, OrientationType
from core.placement_validator import PlacementValidator


@pytest.fixture
def test_vehicle():
    return Vehicle(
        id="T-TEST",
        label="Test Truck",
        category="Test Category",
        nominal_volume_m3=20.0,
        max_payload_kg=2000.0,
        internal_length_cm=400.0,
        internal_width_cm=200.0,
        internal_height_cm=200.0,
        door_width_cm=190.0,
        door_height_cm=190.0,
        is_verified=True
    )


def test_valid_item_fits_inside(test_vehicle):
    item = CargoItem("B1", "Box 1", 100, 100, 100, 50.0, quantity=1, upright_only=True)
    inst = item.expand_instances()[0]
    p = PlacedCargoInstance(inst, 0.0, 0.0, 0.0, 100.0, 100.0, 100.0, "LWH")
    res = PlacementValidator.validate(test_vehicle, [p])
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_item_extends_outside_vehicle(test_vehicle):
    # Placed past vehicle length (vehicle length = 400, x = 350, length = 100 -> x_max = 450)
    item = CargoItem("B1", "Box 1", 100, 100, 100, 50.0, quantity=1)
    inst = item.expand_instances()[0]
    p = PlacedCargoInstance(inst, 350.0, 0.0, 0.0, 100.0, 100.0, 100.0, "LWH")
    res = PlacementValidator.validate(test_vehicle, [p])
    assert res.is_valid is False
    assert any("extends beyond vehicle length" in err for err in res.errors)


def test_two_items_overlap(test_vehicle):
    # Two boxes at overlapping coordinates
    item1 = CargoItem("B1", "Box 1", 100, 100, 100, 50.0, quantity=1)
    inst1 = item1.expand_instances()[0]
    p1 = PlacedCargoInstance(inst1, 0.0, 0.0, 0.0, 100.0, 100.0, 100.0, "LWH")

    item2 = CargoItem("B2", "Box 2", 100, 100, 100, 50.0, quantity=1)
    inst2 = item2.expand_instances()[0]
    # Overlaps in all 3 dimensions
    p2 = PlacedCargoInstance(inst2, 50.0, 50.0, 50.0, 100.0, 100.0, 100.0, "LWH")

    res = PlacementValidator.validate(test_vehicle, [p1, p2])
    assert res.is_valid is False
    assert any("Collision detected" in err for err in res.errors)


def test_upright_only_orientation_enforced(test_vehicle):
    # Item is marked upright-only, so height must be 80. If laid on side with height 40, must fail.
    item = CargoItem("B-UP", "Upright Box", 100, 60, 80, 50.0, quantity=1, upright_only=True)
    inst = item.expand_instances()[0]
    # Placed with height = 40 (tilted on side)
    p = PlacedCargoInstance(inst, 0.0, 0.0, 0.0, 100.0, 80.0, 60.0, "Tilted")
    res = PlacementValidator.validate(test_vehicle, [p])
    assert res.is_valid is False
    assert any("prohibited for mode" in err for err in res.errors)


def test_non_stackable_restriction(test_vehicle):
    # Bottom box is non-stackable
    bottom_item = CargoItem("B-NO-STACK", "Bottom Box", 100, 100, 100, 50.0, stackable=False)
    b_inst = bottom_item.expand_instances()[0]
    p_bottom = PlacedCargoInstance(b_inst, 0.0, 0.0, 0.0, 100.0, 100.0, 100.0, "LWH")

    top_item = CargoItem("B-TOP", "Top Box", 100, 100, 50, 20.0, stackable=True)
    t_inst = top_item.expand_instances()[0]
    p_top = PlacedCargoInstance(t_inst, 0.0, 0.0, 100.0, 100.0, 100.0, 50.0, "LWH")

    res = PlacementValidator.validate(test_vehicle, [p_bottom, p_top])
    assert res.is_valid is False
    assert any("NON-STACKABLE" in err for err in res.errors)


def test_fragile_restriction(test_vehicle):
    # Bottom box is fragile
    bottom_item = CargoItem("B-FRAGILE", "Glass Carton", 100, 100, 100, 10.0, fragile=True)
    b_inst = bottom_item.expand_instances()[0]
    p_bottom = PlacedCargoInstance(b_inst, 0.0, 0.0, 0.0, 100.0, 100.0, 100.0, "LWH")

    top_item = CargoItem("B-TOP", "Heavy Metal", 100, 100, 50, 80.0)
    t_inst = top_item.expand_instances()[0]
    p_top = PlacedCargoInstance(t_inst, 0.0, 0.0, 100.0, 100.0, 100.0, 50.0, "LWH")

    res = PlacementValidator.validate(test_vehicle, [p_bottom, p_top])
    assert res.is_valid is False
    assert any("FRAGILE" in err for err in res.errors)


def test_max_top_load_enforced(test_vehicle):
    # Bottom box allows max 50 kg on top
    bottom_item = CargoItem("B-BASE", "Base Carton", 100, 100, 100, 30.0, stackable=True, max_top_load_kg=50.0)
    b_inst = bottom_item.expand_instances()[0]
    p_bottom = PlacedCargoInstance(b_inst, 0.0, 0.0, 0.0, 100.0, 100.0, 100.0, "LWH")

    # Top box weighs 90 kg
    top_item = CargoItem("B-HEAVY", "Heavy Top", 100, 100, 50, 90.0)
    t_inst = top_item.expand_instances()[0]
    p_top = PlacedCargoInstance(t_inst, 0.0, 0.0, 100.0, 100.0, 100.0, 50.0, "LWH")

    res = PlacementValidator.validate(test_vehicle, [p_bottom, p_top])
    assert res.is_valid is False
    assert any("exceeding its maximum permissible top load limit" in err for err in res.errors)


def test_cargo_weight_exceeds_payload(test_vehicle):
    # Vehicle payload = 2000 kg, cargo = 2500 kg
    item = CargoItem("B-OVERLOAD", "Heavy Machinery", 200, 150, 150, 2500.0)
    inst = item.expand_instances()[0]
    p = PlacedCargoInstance(inst, 0.0, 0.0, 0.0, 200.0, 150.0, 150.0, "LWH")

    res = PlacementValidator.validate(test_vehicle, [p])
    assert res.is_valid is False
    assert any("exceeds vehicle payload limit" in err for err in res.errors)


def test_floating_box_rejected(test_vehicle):
    # Box placed at z=100 with nothing underneath
    item = CargoItem("B-FLOAT", "Floating Box", 100, 100, 50, 20.0)
    inst = item.expand_instances()[0]
    p = PlacedCargoInstance(inst, 0.0, 0.0, 100.0, 100.0, 100.0, 50.0, "LWH")

    res = PlacementValidator.validate(test_vehicle, [p])
    assert res.is_valid is False
    assert any("floating in mid-air" in err for err in res.errors)


def test_manual_adjustment_triggers_validation(test_vehicle):
    # Start with valid placement
    item = CargoItem("B1", "Box 1", 100, 100, 100, 50.0)
    inst = item.expand_instances()[0]
    p1 = PlacedCargoInstance(inst, 0.0, 0.0, 0.0, 100.0, 100.0, 100.0, "LWH")
    assert PlacementValidator.validate(test_vehicle, [p1]).is_valid is True

    # User manually repositions box to negative X
    p_modified = PlacedCargoInstance(inst, -10.0, 0.0, 0.0, 100.0, 100.0, 100.0, "LWH")
    res_mod = PlacementValidator.validate(test_vehicle, [p_modified])
    assert res_mod.is_valid is False
    assert any("negative coordinates" in err for err in res_mod.errors)
