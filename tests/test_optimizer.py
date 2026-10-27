"""
tests/test_optimizer.py
Tests for the 3D packing optimizer: feasibility, unplaced items reporting,
payload enforcement, and temporary state verification.
"""

from pathlib import Path
import pytest
from core.models import Vehicle, CargoItem
from core.optimizer import PackingOptimizer


@pytest.fixture
def truck():
    return Vehicle(
        id="T1",
        label="14 ft Test Truck",
        category="14 ft",
        nominal_volume_m3=15.63,
        max_payload_kg=1000.0,
        internal_length_cm=300.0,
        internal_width_cm=200.0,
        internal_height_cm=200.0,
        door_width_cm=190.0,
        door_height_cm=190.0,
        is_verified=True
    )


def test_optimizer_valid_fit(truck):
    # Two identical pallets that easily fit
    items = [
        CargoItem(
            item_id="PALLET-A",
            name="Euro Pallet",
            length_cm=120.0,
            width_cm=80.0,
            height_cm=100.0,
            unit_weight_kg=100.0,
            quantity=2,
            upright_only=True
        )
    ]
    optimizer = PackingOptimizer(truck)
    result = optimizer.pack(items)

    assert result.status == "FEASIBLE"
    assert len(result.placed_instances) == 2
    assert len(result.unplaced_instances) == 0
    assert result.loaded_weight_kg == 200.0
    assert result.remaining_payload_kg == 800.0
    assert result.validation_result.is_valid is True


def test_optimizer_item_exceeds_dimensions(truck):
    # An oversized item that physically cannot fit in length
    items = [
        CargoItem(
            item_id="OVERSIZED-PIPE",
            name="Long Pipe",
            length_cm=500.0, # Vehicle length is only 300
            width_cm=50.0,
            height_cm=50.0,
            unit_weight_kg=150.0,
            quantity=1
        )
    ]
    optimizer = PackingOptimizer(truck)
    result = optimizer.pack(items)

    assert result.status == "INFEASIBLE"
    assert len(result.placed_instances) == 0
    assert len(result.unplaced_instances) == 1
    unp_item, reason = result.unplaced_instances[0]
    assert "exceed vehicle internal limits" in reason


def test_optimizer_payload_overload(truck):
    # Truck payload is 1000 kg. Item 1 is 800 kg, Item 2 is 400 kg.
    items = [
        CargoItem("HEAVY-1", "Machinery 1", 100, 100, 100, 800.0, quantity=1),
        CargoItem("HEAVY-2", "Machinery 2", 100, 100, 100, 400.0, quantity=1)
    ]
    optimizer = PackingOptimizer(truck)
    result = optimizer.pack(items)

    assert result.status == "PARTIAL"
    assert len(result.placed_instances) == 1
    assert len(result.unplaced_instances) == 1
    unp_item, reason = result.unplaced_instances[0]
    assert "Exceeds vehicle payload limit" in reason


def test_optimizer_partial_packing_volume_exhaustion(truck):
    # Pack small boxes until volume / space fills up
    items = [
        CargoItem("BIG-BOX", "Bulky Box", 140, 95, 100, 50.0, quantity=10)
    ]
    optimizer = PackingOptimizer(truck)
    result = optimizer.pack(items)

    # Some will be placed and some unplaced
    assert len(result.placed_instances) > 0
    assert len(result.unplaced_instances) > 0
    assert result.status == "PARTIAL"


def test_no_permanent_database_or_plan_history():
    """
    Ensure the optimizer does not create sqlite, db, or permanent history files.
    """
    workspace = Path(__file__).resolve().parent.parent
    db_files = list(workspace.glob("**/*.db")) + list(workspace.glob("**/*.sqlite*"))
    assert len(db_files) == 0, f"Found unintended database files: {db_files}"
