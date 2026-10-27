"""
tests/test_models.py
Tests for data models, property calculations, and instance expansion.
"""

from core.models import Vehicle, CargoItem, OrientationType, CargoInstance


def test_vehicle_properties():
    v = Vehicle(
        id="T1",
        label="14 ft Test",
        category="14 ft",
        nominal_volume_m3=15.63,
        max_payload_kg=3500.0,
        internal_length_cm=420.0,
        internal_width_cm=205.0,
        internal_height_cm=190.0,
        door_width_cm=195.0,
        door_height_cm=180.0
    )
    # (420 * 205 * 190) / 1,000,000 = 16.359 m3
    assert abs(v.internal_volume_m3 - 16.359) < 0.01


def test_cargo_item_expansion():
    item = CargoItem(
        item_id="BOX-EXP",
        name="Expanded Carton",
        length_cm=50.0,
        width_cm=40.0,
        height_cm=30.0,
        unit_weight_kg=12.5,
        quantity=3,
        fragile=True,
        stackable=False,
        upright_only=True
    )
    instances = item.expand_instances()
    assert len(instances) == 3
    assert instances[0].instance_id == "BOX-EXP#1"
    assert instances[1].instance_id == "BOX-EXP#2"
    assert instances[2].instance_id == "BOX-EXP#3"
    assert instances[0].parent_item_id == "BOX-EXP"
    assert instances[0].fragile is True
    assert instances[0].stackable is False


def test_instance_orientations():
    # Upright only
    inst_upright = CargoInstance(
        instance_id="I1",
        parent_item_id="P1",
        name="Upright Box",
        length_cm=100.0,
        width_cm=60.0,
        height_cm=40.0,
        weight_kg=20.0,
        upright_only=True,
        orientation_mode=OrientationType.UPRIGHT_ONLY
    )
    orients = inst_upright.get_valid_orientations()
    # Should only allow Z = 40 (length 100, width 60) and (length 60, width 100)
    assert len(orients) == 2
    for ox, oy, oz, lbl in orients:
        assert oz == 40.0

    # Fixed (no rotation)
    inst_fixed = CargoInstance(
        instance_id="I2",
        parent_item_id="P2",
        name="Fixed Box",
        length_cm=100.0,
        width_cm=60.0,
        height_cm=40.0,
        weight_kg=20.0,
        upright_only=False,
        orientation_mode=OrientationType.FIXED
    )
    orients_fixed = inst_fixed.get_valid_orientations()
    assert len(orients_fixed) == 1
    assert orients_fixed[0][:3] == (100.0, 60.0, 40.0)

    # All 6 orientations
    inst_all = CargoInstance(
        instance_id="I3",
        parent_item_id="P3",
        name="Free Box",
        length_cm=100.0,
        width_cm=60.0,
        height_cm=40.0,
        weight_kg=20.0,
        upright_only=False,
        orientation_mode=OrientationType.ALL
    )
    orients_all = inst_all.get_valid_orientations()
    assert len(orients_all) == 6
