"""
core/metrics.py
Standardized metric calculations and educational definitions for truck loading logistics.
Clearly differentiates physical volume utilization from geometric bounding spatial utilization.
"""

from typing import Dict, Any, List
from core.models import Vehicle, PlacedCargoInstance


def compute_packing_metrics(vehicle: Vehicle, placements: List[PlacedCargoInstance]) -> Dict[str, Any]:
    """
    Computes rigorous metrics for an arrangement of cargo items inside a vehicle.
    """
    total_loaded_weight_kg = sum(p.weight_kg for p in placements)
    remaining_payload_kg = max(0.0, vehicle.max_payload_kg - total_loaded_weight_kg)
    payload_utilization_pct = (total_loaded_weight_kg / vehicle.max_payload_kg * 100.0) if vehicle.max_payload_kg > 0 else 0.0

    placed_volume_m3 = sum(p.volume_m3 for p in placements)
    vehicle_internal_volume_m3 = vehicle.internal_volume_m3
    remaining_volume_m3 = max(0.0, vehicle_internal_volume_m3 - placed_volume_m3)
    volume_utilization_pct = (placed_volume_m3 / vehicle_internal_volume_m3 * 100.0) if vehicle_internal_volume_m3 > 0 else 0.0

    if placements:
        max_x = max(p.x_max for p in placements)
        max_y = max(p.y_max for p in placements)
        max_z = max(p.z_max for p in placements)
        bounding_volume_m3 = (max_x * max_y * max_z) / 1_000_000.0
        spatial_utilization_pct = (bounding_volume_m3 / vehicle_internal_volume_m3 * 100.0) if vehicle_internal_volume_m3 > 0 else 0.0
    else:
        max_x = max_y = max_z = 0.0
        bounding_volume_m3 = 0.0
        spatial_utilization_pct = 0.0

    fragile_count = sum(1 for p in placements if p.fragile)
    late_order_count = sum(1 for p in placements if p.is_late_order)

    return {
        "total_instances_placed": len(placements),
        "total_loaded_weight_kg": round(total_loaded_weight_kg, 2),
        "vehicle_max_payload_kg": round(vehicle.max_payload_kg, 2),
        "remaining_payload_kg": round(remaining_payload_kg, 2),
        "payload_utilization_pct": round(payload_utilization_pct, 2),
        "placed_volume_m3": round(placed_volume_m3, 3),
        "vehicle_volume_m3": round(vehicle_internal_volume_m3, 3),
        "remaining_volume_m3": round(remaining_volume_m3, 3),
        "volume_utilization_pct": round(volume_utilization_pct, 2),
        "bounding_length_cm": round(max_x, 1),
        "bounding_width_cm": round(max_y, 1),
        "bounding_height_cm": round(max_z, 1),
        "bounding_volume_m3": round(bounding_volume_m3, 3),
        "spatial_utilization_pct": round(spatial_utilization_pct, 2),
        "fragile_count": fragile_count,
        "late_order_count": late_order_count,
        "is_volume_estimated": not vehicle.is_verified,
    }


METRIC_DEFINITIONS = {
    "volume_utilization": (
        "Volume Utilization represents the sum of individual cargo box volumes divided by "
        "the total internal volume of the vehicle cargo bay. Note: Unused volume represents fragmented airspace "
        "and does not guarantee that further irregular cargo can physically fit."
    ),
    "spatial_utilization": (
        "Spatial Bounding Utilization measures the overall 3D bounding envelope (maximum length x "
        "width x height reached by placed boxes) relative to the truck interior. It indicates how much "
        "of the cargo bay's length, width, and height has been engaged by the current stowage."
    ),
    "payload_utilization": (
        "Payload Utilization measures total gross cargo mass against the certified maximum cargo payload capacity."
    )
}
