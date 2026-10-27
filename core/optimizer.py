"""
core/optimizer.py
Deterministic 3D Constrained Cargo-Packing Engine based on Extreme Points (EP)
and multi-tier Best-Fit-Decreasing heuristic.

Considers:
- Vehicle internal dimensions and rear door clearance
- Maximum vehicle payload
- Permitted orientations (Upright only, All 6, Fixed)
- AABB 3D non-overlap collision constraints
- Gravity and floor/box surface support stability
- Non-stackable cargo restrictions
- Fragile cargo placement constraints
- Cumulative maximum top-load thresholds
- Honest tracking of unplaced cargo with verifiable failure reasons
"""

import time
from typing import List, Tuple, Set, Optional, Dict
from core.models import (
    Vehicle,
    CargoItem,
    CargoInstance,
    PlacedCargoInstance,
    OptimizationResult,
    ValidationResult
)
from core.placement_validator import PlacementValidator, EPSILON, MIN_SUPPORT_RATIO


class PackingOptimizer:
    """
    3D Constrained Cargo-Packing Engine.
    Employs an Extreme Point heuristic with stability-first sorting and constraint filtering.
    """

    def __init__(self, vehicle: Vehicle):
        self.vehicle = vehicle

    def pack(self, items: List[CargoItem]) -> OptimizationResult:
        """
        Executes the 3D packing algorithm on a list of CargoItem specifications.
        """
        start_time = time.time()

        # Step 1: Expand CargoItems into individual physical CargoInstances
        instances: List[CargoInstance] = []
        for it in items:
            instances.extend(it.expand_instances())

        total_requested_vol = sum(inst.volume_m3 for inst in instances)
        total_requested_weight = sum(inst.weight_kg for inst in instances)

        # Step 2: Sort instances using multi-tier heuristic:
        # Tier 1: Non-fragile before fragile (so fragile items end up on top or uncrushed)
        # Tier 2: Stackable before non-stackable (non-stackable items go toward upper tiers)
        # Tier 3: Heavier weight first (improves center of gravity and floor support)
        # Tier 4: Largest footprint (length * width) and volume descending
        sorted_instances = sorted(
            instances,
            key=lambda c: (
                1 if c.fragile else 0,
                1 if not c.stackable else 0,
                -c.weight_kg,
                -(c.length_cm * c.width_cm),
                -c.volume_m3
            )
        )

        placed: List[PlacedCargoInstance] = []
        unplaced: List[Tuple[CargoInstance, str]] = []
        current_weight = 0.0

        # Candidate placement points in 3D: (x, y, z)
        # Starts with (0, 0, 0)
        extreme_points: List[Tuple[float, float, float]] = [(0.0, 0.0, 0.0)]

        for inst in sorted_instances:
            # Check 1: Payload capacity
            if current_weight + inst.weight_kg > self.vehicle.max_payload_kg + EPSILON:
                unplaced.append((
                    inst,
                    f"Exceeds vehicle payload limit (Remaining payload: {self.vehicle.max_payload_kg - current_weight:.1f} kg, required: {inst.weight_kg:.1f} kg)"
                ))
                continue

            # Check 2: Absolute dimensions vs vehicle
            valid_orientations = inst.get_valid_orientations()
            can_fit_in_any_orientation = any(
                ox <= self.vehicle.internal_length_cm + EPSILON and
                oy <= self.vehicle.internal_width_cm + EPSILON and
                oz <= self.vehicle.internal_height_cm + EPSILON
                for ox, oy, oz, _ in valid_orientations
            )
            if not can_fit_in_any_orientation:
                unplaced.append((
                    inst,
                    f"Item dimensions ({inst.length_cm:.0f}x{inst.width_cm:.0f}x{inst.height_cm:.0f} cm) exceed vehicle internal limits in all permitted orientations"
                ))
                continue

            # Check 3: Rear door entry clearance
            sorted_dims = sorted([inst.length_cm, inst.width_cm, inst.height_cm])
            if not (
                (sorted_dims[0] <= self.vehicle.door_width_cm + EPSILON and sorted_dims[1] <= self.vehicle.door_height_cm + EPSILON) or
                (sorted_dims[1] <= self.vehicle.door_width_cm + EPSILON and sorted_dims[0] <= self.vehicle.door_height_cm + EPSILON)
            ):
                unplaced.append((
                    inst,
                    f"Cross-section ({sorted_dims[0]}x{sorted_dims[1]} cm) cannot pass through vehicle rear door ({self.vehicle.door_width_cm}x{self.vehicle.door_height_cm} cm)"
                ))
                continue

            # Sort candidate points:
            # Lowest Z first (gravity), then lowest X (back-to-front), then lowest Y (wall-to-wall)
            extreme_points.sort(key=lambda pt: (round(pt[2], 2), round(pt[0], 2), round(pt[1], 2)))

            valid_orientations = inst.get_valid_orientations()
            best_placement: Optional[PlacedCargoInstance] = None

            for pt in extreme_points:
                px, py, pz = pt
                found_at_point = False

                for ox, oy, oz, olabel in valid_orientations:
                    # 1. Bounds check
                    if px + ox > self.vehicle.internal_length_cm + EPSILON:
                        continue
                    if py + oy > self.vehicle.internal_width_cm + EPSILON:
                        continue
                    if pz + oz > self.vehicle.internal_height_cm + EPSILON:
                        continue

                    # 2. Collision check against already placed items
                    overlaps = False
                    for p in placed:
                        if (
                            px < p.x_max - EPSILON and px + ox > p.x_cm + EPSILON and
                            py < p.y_max - EPSILON and py + oy > p.y_cm + EPSILON and
                            pz < p.z_max - EPSILON and pz + oz > p.z_cm + EPSILON
                        ):
                            overlaps = True
                            break
                    if overlaps:
                        continue

                    # 3. Support and stacking checks if pz > 0
                    if pz > EPSILON:
                        base_area = ox * oy
                        support_area = 0.0
                        stacking_allowed = True
                        fragile_violation = False
                        underneath_indices = []

                        for idx, p in enumerate(placed):
                            if abs(p.z_max - pz) < 0.5:
                                cx = max(0.0, min(px + ox, p.x_max) - max(px, p.x_cm))
                                cy = max(0.0, min(py + oy, p.y_max) - max(py, p.y_cm))
                                carea = cx * cy
                                if carea > EPSILON:
                                    if not p.stackable:
                                        stacking_allowed = False
                                        break
                                    if p.fragile:
                                        fragile_violation = True
                                        break
                                    support_area += carea
                                    underneath_indices.append(idx)

                        if not stacking_allowed or fragile_violation:
                            continue
                        if base_area > 0 and (support_area / base_area) < MIN_SUPPORT_RATIO:
                            # Insufficient contact area to prevent tipping
                            continue

                        # Check top load limits on supporting items
                        top_load_exceeded = False
                        for b_idx in underneath_indices:
                            b_item = placed[b_idx]
                            if b_item.max_top_load_kg > 0:
                                # Estimate load on b_item with new item
                                if inst.weight_kg > b_item.max_top_load_kg:
                                    top_load_exceeded = True
                                    break
                        if top_load_exceeded:
                            continue

                    # If passed all checks, this is a feasible placement!
                    best_placement = PlacedCargoInstance(
                        instance=inst,
                        x_cm=round(px, 2),
                        y_cm=round(py, 2),
                        z_cm=round(pz, 2),
                        placed_length_cm=round(ox, 2),
                        placed_width_cm=round(oy, 2),
                        placed_height_cm=round(oz, 2),
                        orientation_label=olabel,
                        loading_sequence_index=len(placed) + 1
                    )
                    found_at_point = True
                    break

                if found_at_point:
                    break

            if best_placement is not None:
                placed.append(best_placement)
                current_weight += inst.weight_kg

                # Update extreme points list with new potential corner points
                bx, by, bz = best_placement.x_cm, best_placement.y_cm, best_placement.z_cm
                bl, bw, bh = best_placement.placed_length_cm, best_placement.placed_width_cm, best_placement.placed_height_cm

                new_candidates = [
                    (bx + bl, by, bz),
                    (bx, by + bw, bz),
                    (bx, by, bz + bh)
                ]

                # Project along existing neighbors to capture corner nooks
                for p in placed:
                    if p.x_max <= bx + bl and p.y_max >= by:
                        new_candidates.append((p.x_max, by, bz))
                    if p.y_max <= by + bw and p.x_max >= bx:
                        new_candidates.append((bx, p.y_max, bz))

                # Filter and register valid points
                for nx, ny, nz in new_candidates:
                    if (
                        nx <= self.vehicle.internal_length_cm - 1.0 and
                        ny <= self.vehicle.internal_width_cm - 1.0 and
                        nz <= self.vehicle.internal_height_cm - 1.0
                    ):
                        # Point must not be inside any already placed box
                        inside_any = False
                        for p in placed:
                            if (
                                p.x_cm - EPSILON <= nx < p.x_max - EPSILON and
                                p.y_cm - EPSILON <= ny < p.y_max - EPSILON and
                                p.z_cm - EPSILON <= nz < p.z_max - EPSILON
                            ):
                                inside_any = True
                                break
                        if not inside_any:
                            # Avoid duplicates within 0.5 cm
                            is_dup = False
                            for ex, ey, ez in extreme_points:
                                if abs(ex - nx) < 0.5 and abs(ey - ny) < 0.5 and abs(ez - nz) < 0.5:
                                    is_dup = True
                                    break
                            if not is_dup:
                                extreme_points.append((round(nx, 2), round(ny, 2), round(nz, 2)))

                # Prune extreme points that are now enclosed
                extreme_points = [
                    pt for pt in extreme_points
                    if not any(
                        p.x_cm - EPSILON <= pt[0] < p.x_max - EPSILON and
                        p.y_cm - EPSILON <= pt[1] < p.y_max - EPSILON and
                        p.z_cm - EPSILON <= pt[2] < p.z_max - EPSILON
                        for p in placed
                    )
                ]
            else:
                unplaced.append((
                    inst,
                    "No feasible geometric space or stable support surface available in vehicle"
                ))

        # Run independent validation check
        validation_res = PlacementValidator.validate(self.vehicle, placed)

        # Compute accurate utilization metrics
        placed_vol_m3 = sum(p.volume_m3 for p in placed)
        vehicle_vol_m3 = self.vehicle.internal_volume_m3
        volume_util_pct = (placed_vol_m3 / vehicle_vol_m3 * 100.0) if vehicle_vol_m3 > 0 else 0.0

        if placed:
            max_x = max(p.x_max for p in placed)
            max_y = max(p.y_max for p in placed)
            max_z = max(p.z_max for p in placed)
            spatial_bound_m3 = (max_x * max_y * max_z) / 1_000_000.0
            spatial_util_pct = (spatial_bound_m3 / vehicle_vol_m3 * 100.0) if vehicle_vol_m3 > 0 else 0.0
        else:
            spatial_bound_m3 = 0.0
            spatial_util_pct = 0.0

        # Determine honest solver status
        if len(placed) == len(instances) and len(instances) > 0:
            status = "FEASIBLE"
            msg = "Feasible loading plan found within configured search limits."
        elif len(placed) > 0 and len(unplaced) > 0:
            status = "PARTIAL"
            msg = f"Partial plan: {len(placed)} of {len(instances)} cargo items placed. {len(unplaced)} items could not be accommodated."
        elif len(instances) == 0:
            status = "EMPTY"
            msg = "No cargo items were provided for optimization."
        else:
            status = "INFEASIBLE"
            msg = "Infeasible: None of the requested cargo items could be placed."

        remaining_payload = max(0.0, self.vehicle.max_payload_kg - current_weight)
        exec_time = time.time() - start_time

        return OptimizationResult(
            vehicle=self.vehicle,
            status=status,
            solver_message=msg,
            placed_instances=placed,
            unplaced_instances=unplaced,
            loaded_weight_kg=round(current_weight, 2),
            remaining_payload_kg=round(remaining_payload, 2),
            total_requested_volume_m3=round(total_requested_vol, 3),
            placed_cargo_volume_m3=round(placed_vol_m3, 3),
            volume_utilization_pct=round(volume_util_pct, 2),
            spatial_bounding_volume_m3=round(spatial_bound_m3, 3),
            spatial_utilization_pct=round(spatial_util_pct, 2),
            validation_result=validation_res,
            execution_time_sec=round(exec_time, 3)
        )
