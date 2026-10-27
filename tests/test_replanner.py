"""
tests/test_replanner.py
Tests for late-order replanning strategies and constraint preservation.
"""

import pytest
from core.models import Vehicle, CargoItem
from core.optimizer import PackingOptimizer
from core.replanner import LateOrderReplanner


@pytest.fixture
def truck():
    return Vehicle(
        id="T1",
        label="14 ft Test Truck",
        category="14 ft",
        nominal_volume_m3=15.63,
        max_payload_kg=2000.0,
        internal_length_cm=400.0,
        internal_width_cm=200.0,
        internal_height_cm=200.0,
        door_width_cm=190.0,
        door_height_cm=190.0,
        is_verified=True
    )


def test_replanner_preserves_existing_placements(truck):
    # Initial load: 1 pallet
    initial_items = [
        CargoItem("INITIAL-1", "Standard Pallet", 100, 100, 100, 200.0, quantity=1)
    ]
    optimizer = PackingOptimizer(truck)
    initial_result = optimizer.pack(initial_items)
    assert len(initial_result.placed_instances) == 1
    init_x, init_y, init_z = initial_result.placed_instances[0].x_cm, initial_result.placed_instances[0].y_cm, initial_result.placed_instances[0].z_cm

    # Add late item
    late_items = [
        CargoItem("LATE-1", "Late Emergency Box", 50, 50, 50, 30.0, quantity=1)
    ]
    replanner = LateOrderReplanner(truck)
    revised_result = replanner.replan(initial_result, late_items, allow_reorganization=False)

    assert len(revised_result.placed_instances) == 2
    # Verify the initial placement was untouched
    assert revised_result.placed_instances[0].x_cm == init_x
    assert revised_result.placed_instances[0].y_cm == init_y
    assert revised_result.placed_instances[0].z_cm == init_z
    assert revised_result.placed_instances[1].is_late_order is True
    assert revised_result.validation_result.is_valid is True


def test_replanner_rejects_payload_exceeding_late_order(truck):
    # Initial load: 1800 kg (max payload is 2000 kg -> only 200 kg remaining)
    initial_items = [
        CargoItem("INITIAL-HEAVY", "Heavy Core", 150, 150, 100, 1800.0, quantity=1)
    ]
    optimizer = PackingOptimizer(truck)
    initial_result = optimizer.pack(initial_items)

    # Late item weighs 300 kg (exceeds 200 kg remaining)
    late_items = [
        CargoItem("LATE-OVERLOAD", "Heavy Late Order", 50, 50, 50, 300.0, quantity=1)
    ]
    replanner = LateOrderReplanner(truck)
    revised_result = replanner.replan(initial_result, late_items, allow_reorganization=False)

    assert len(revised_result.placed_instances) == 1
    assert len(revised_result.unplaced_instances) == 1
    unp_item, reason = revised_result.unplaced_instances[0]
    assert "exceeds vehicle payload limit" in reason
