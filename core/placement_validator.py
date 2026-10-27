"""
core/placement_validator.py
Independent physical and operational constraint validator for truck cargo arrangements.
Performs verification independent of the packing algorithm.
"""

from typing import List, Dict, Tuple, Set
from core.models import Vehicle, PlacedCargoInstance, ValidationResult

EPSILON = 1e-4  # Coordinate tolerance in cm
MIN_SUPPORT_RATIO = 0.50  # Minimum 50% base support required for non-floor items


class PlacementValidator:
    """
    Independently inspects an arrangement of PlacedCargoInstance objects inside a Vehicle.
    Validates:
    1. Vehicle boundary constraints (X, Y, Z within vehicle internal limits)
    2. Door entry profile feasibility
    3. Pairwise 3D collisions (AABB non-overlap)
    4. Permitted rotation and orientation compliance
    5. Gravity support and floating box prevention
    6. Non-stackable cargo violations
    7. Fragile cargo stacking violations
    8. Cumulative maximum top load violations
    9. Total vehicle payload limits
    """

    @staticmethod
    def validate(vehicle: Vehicle, placements: List[PlacedCargoInstance]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        item_diag: Dict[str, List[str]] = {}
        summary_checks = {
            "boundary_within_limits": True,
            "door_entry_feasible": True,
            "no_3d_overlap": True,
            "orientation_allowed": True,
            "floor_or_box_supported": True,
            "stackability_respected": True,
            "fragility_respected": True,
            "top_load_within_limits": True,
            "payload_within_limits": True,
        }

        def add_error(item_id: str, msg: str, check_key: str):
            errors.append(msg)
            item_diag.setdefault(item_id, []).append(f"ERROR: {msg}")
            summary_checks[check_key] = False

        def add_warning(item_id: str, msg: str):
            warnings.append(msg)
            item_diag.setdefault(item_id, []).append(f"WARN: {msg}")

        # 1. Total payload check
        total_weight = sum(p.weight_kg for p in placements)
        if total_weight > vehicle.max_payload_kg + EPSILON:
            excess = total_weight - vehicle.max_payload_kg
            errors.append(
                f"Total loaded weight ({total_weight:.1f} kg) exceeds vehicle payload limit "
                f"({vehicle.max_payload_kg:.1f} kg) by {excess:.1f} kg."
            )
            summary_checks["payload_within_limits"] = False

        # 2. Check each item individually
        for p in placements:
            iid = p.instance_id

            # Boundary checks
            if p.x_cm < -EPSILON or p.y_cm < -EPSILON or p.z_cm < -EPSILON:
                add_error(iid, f"Item '{iid}' has negative coordinates: ({p.x_cm}, {p.y_cm}, {p.z_cm}).", "boundary_within_limits")

            if p.x_max > vehicle.internal_length_cm + EPSILON:
                add_error(
                    iid,
                    f"Item '{iid}' extends beyond vehicle length: X-max {p.x_max:.1f} cm > vehicle length {vehicle.internal_length_cm:.1f} cm.",
                    "boundary_within_limits"
                )

            if p.y_max > vehicle.internal_width_cm + EPSILON:
                add_error(
                    iid,
                    f"Item '{iid}' extends beyond vehicle width: Y-max {p.y_max:.1f} cm > vehicle width {vehicle.internal_width_cm:.1f} cm.",
                    "boundary_within_limits"
                )

            if p.z_max > vehicle.internal_height_cm + EPSILON:
                add_error(
                    iid,
                    f"Item '{iid}' extends beyond vehicle height: Z-max {p.z_max:.1f} cm > vehicle height {vehicle.internal_height_cm:.1f} cm.",
                    "boundary_within_limits"
                )

            # Door clearance check: verify if cross-section can clear rear door
            dims_sorted = sorted([p.instance.length_cm, p.instance.width_cm, p.instance.height_cm])
            min_cross_dim1, min_cross_dim2 = dims_sorted[0], dims_sorted[1]
            door_w, door_h = vehicle.door_width_cm, vehicle.door_height_cm
            door_fits = (
                (min_cross_dim1 <= door_w + EPSILON and min_cross_dim2 <= door_h + EPSILON) or
                (min_cross_dim2 <= door_w + EPSILON and min_cross_dim1 <= door_h + EPSILON)
            )
            if not door_fits:
                add_warning(
                    iid,
                    f"Item '{iid}' dimensions ({min_cross_dim1}x{min_cross_dim2} cm) exceed door opening ({door_w}x{door_h} cm)."
                )
                summary_checks["door_entry_feasible"] = False

            # Orientation check
            valid_orients = p.instance.get_valid_orientations()
            matched = False
            for ox, oy, oz, _ in valid_orients:
                if (
                    abs(p.placed_length_cm - ox) < EPSILON and
                    abs(p.placed_width_cm - oy) < EPSILON and
                    abs(p.placed_height_cm - oz) < EPSILON
                ):
                    matched = True
                    break
            if not matched:
                add_error(
                    iid,
                    f"Item '{iid}' has orientation ({p.placed_length_cm:.1f} x {p.placed_width_cm:.1f} x {p.placed_height_cm:.1f} cm) "
                    f"which is prohibited for mode '{p.instance.orientation_mode}'.",
                    "orientation_allowed"
                )

        # 3. Pairwise 3D collision check
        n = len(placements)
        for i in range(n):
            p1 = placements[i]
            for j in range(i + 1, n):
                p2 = placements[j]
                # AABB intersection
                ox = min(p1.x_max, p2.x_max) - max(p1.x_cm, p2.x_cm)
                oy = min(p1.y_max, p2.y_max) - max(p1.y_cm, p2.y_cm)
                oz = min(p1.z_max, p2.z_max) - max(p1.z_cm, p2.z_cm)

                if ox > EPSILON and oy > EPSILON and oz > EPSILON:
                    overlap_vol = (ox * oy * oz) / 1000.0  # litres / thousands cm3
                    msg = (
                        f"Collision detected: Item '{p1.instance_id}' overlaps with Item '{p2.instance_id}' "
                        f"by {ox:.1f}x{oy:.1f}x{oz:.1f} cm (~{overlap_vol:.2f} dm³)."
                    )
                    add_error(p1.instance_id, msg, "no_3d_overlap")
                    add_error(p2.instance_id, msg, "no_3d_overlap")

        # 4. Vertical support, Stacking & Fragility rules
        # Map support relationships: which items directly support which items
        direct_supports: Dict[int, List[int]] = {i: [] for i in range(n)} # i supports list of items above it
        supported_by: Dict[int, List[int]] = {i: [] for i in range(n)}    # i is supported by items below it

        for i in range(n):
            top_item = placements[i]
            if top_item.z_cm <= EPSILON:
                # Placed directly on the truck floor
                continue

            # Item is elevated; calculate support area from items below whose top touches top_item.z_cm
            total_support_area = 0.0
            top_base_area = top_item.placed_length_cm * top_item.placed_width_cm

            for j in range(n):
                if i == j:
                    continue
                bottom_item = placements[j]
                # Check if bottom_item top face is at top_item bottom face
                if abs(bottom_item.z_max - top_item.z_cm) < 0.5: # 0.5 cm tolerance
                    # Overlap in XY plane
                    ox = max(0.0, min(top_item.x_max, bottom_item.x_max) - max(top_item.x_cm, bottom_item.x_cm))
                    oy = max(0.0, min(top_item.y_max, bottom_item.y_max) - max(top_item.y_cm, bottom_item.y_cm))
                    contact_area = ox * oy
                    if contact_area > EPSILON:
                        total_support_area += contact_area
                        direct_supports[j].append(i)
                        supported_by[i].append(j)

                        # Check stackability of supporting item
                        if not bottom_item.stackable:
                            add_error(
                                top_item.instance_id,
                                f"Item '{top_item.instance_id}' is stacked on top of '{bottom_item.instance_id}', which is marked NON-STACKABLE.",
                                "stackability_respected"
                            )

                        # Check fragility of supporting item
                        if bottom_item.fragile:
                            add_error(
                                top_item.instance_id,
                                f"Item '{top_item.instance_id}' is stacked on top of '{bottom_item.instance_id}', which is marked FRAGILE.",
                                "fragility_respected"
                            )

            if top_base_area > 0:
                support_ratio = total_support_area / top_base_area
                if support_ratio < EPSILON:
                    add_error(
                        top_item.instance_id,
                        f"Item '{top_item.instance_id}' is floating in mid-air at height Z={top_item.z_cm:.1f} cm with no support underneath.",
                        "floor_or_box_supported"
                    )
                elif support_ratio < MIN_SUPPORT_RATIO:
                    add_warning(
                        top_item.instance_id,
                        f"Item '{top_item.instance_id}' is only {support_ratio * 100:.1f}% supported underneath (minimum recommended is {MIN_SUPPORT_RATIO * 100:.0f}%)."
                    )

        # 5. Top load calculation (transitive load supported on top of each item)
        # Compute transitive closure of items above item j
        def get_all_items_above(item_idx: int, visited: Set[int]) -> Set[int]:
            for direct_above in direct_supports[item_idx]:
                if direct_above not in visited:
                    visited.add(direct_above)
                    get_all_items_above(direct_above, visited)
            return visited

        for j in range(n):
            base_item = placements[j]
            if base_item.max_top_load_kg > 0:
                above_indices = get_all_items_above(j, set())
                cumulative_top_weight = sum(placements[k].weight_kg for k in above_indices)
                if cumulative_top_weight > base_item.max_top_load_kg + EPSILON:
                    add_error(
                        base_item.instance_id,
                        f"Cumulative load above item '{base_item.instance_id}' is {cumulative_top_weight:.1f} kg, "
                        f"exceeding its maximum permissible top load limit of {base_item.max_top_load_kg:.1f} kg.",
                        "top_load_within_limits"
                    )

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            item_diagnostics=item_diag,
            summary_checks=summary_checks,
        )
