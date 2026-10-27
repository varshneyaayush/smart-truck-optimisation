"""
core/replanner.py
Handles dynamic addition of late-arriving cargo to an active loading plan.

Strategy:
1. First Attempt: Preserve existing placements and insert late items into remaining available space.
2. Second Attempt (if allowed & needed): Re-optimize entire load with safety constraints prioritized.
3. Completely re-validates the final revised plan.
"""

from typing import List, Tuple, Optional
from core.models import (
    Vehicle,
    CargoItem,
    CargoInstance,
    PlacedCargoInstance,
    OptimizationResult
)
from core.optimizer import PackingOptimizer
from core.placement_validator import PlacementValidator, EPSILON, MIN_SUPPORT_RATIO


class LateOrderReplanner:
    """
    Manages late-order addition and loading plan revisions.
    """

    def __init__(self, vehicle: Vehicle):
        self.vehicle = vehicle

    def replan(
        self,
        current_result: OptimizationResult,
        late_items: List[CargoItem],
        allow_reorganization: bool = False
    ) -> OptimizationResult:
        """
        Attempts to accommodate late items into the current vehicle loading plan.
        """
        # Ensure all late items have is_late_order = True
        for it in late_items:
            it.is_late_order = True

        late_instances: List[CargoInstance] = []
        for it in late_items:
            late_instances.extend(it.expand_instances())

        if not late_instances:
            return current_result

        # Strategy 1: Preserve existing placements and fit into remaining space
        existing_placed = list(current_result.placed_instances)
        current_weight = sum(p.weight_kg for p in existing_placed)

        # Build candidate extreme points from existing placed items
        extreme_points = [(0.0, 0.0, 0.0)]
        for p in existing_placed:
            bx, by, bz = p.x_cm, p.y_cm, p.z_cm
            bl, bw, bh = p.placed_length_cm, p.placed_width_cm, p.placed_height_cm
            extreme_points.extend([
                (bx + bl, by, bz),
                (bx, by + bw, bz),
                (bx, by, bz + bh),
            ])

        # Prune extreme points that are inside existing boxes or beyond vehicle boundaries
        valid_ep = []
        for pt in extreme_points:
            x, y, z = pt
            if (
                x < self.vehicle.internal_length_cm - 1.0 and
                y < self.vehicle.internal_width_cm - 1.0 and
                z < self.vehicle.internal_height_cm - 1.0
            ):
                inside = any(
                    p.x_cm - EPSILON <= x < p.x_max - EPSILON and
                    p.y_cm - EPSILON <= y < p.y_max - EPSILON and
                    p.z_cm - EPSILON <= z < p.z_max - EPSILON
                    for p in existing_placed
                )
                if not inside:
                    valid_ep.append((round(x, 2), round(y, 2), round(z, 2)))

        # Unique points
        unique_ep = []
        for pt in valid_ep:
            if not any(abs(pt[0]-u[0])<0.5 and abs(pt[1]-u[1])<0.5 and abs(pt[2]-u[2])<0.5 for u in unique_ep):
                unique_ep.append(pt)

        newly_placed: List[PlacedCargoInstance] = []
        unplaced_late: List[Tuple[CargoInstance, str]] = []

        # Sort late items
        sorted_late = sorted(
            late_instances,
            key=lambda c: (
                1 if c.fragile else 0,
                1 if not c.stackable else 0,
                -c.weight_kg,
                -c.volume_m3
            )
        )

        all_current_placed = list(existing_placed)

        for inst in sorted_late:
            # Check payload
            if current_weight + inst.weight_kg > self.vehicle.max_payload_kg + EPSILON:
                unplaced_late.append((
                    inst,
                    f"Late order exceeds vehicle payload limit ({self.vehicle.max_payload_kg - current_weight:.1f} kg remaining)"
                ))
                continue

            # Sort EP
            unique_ep.sort(key=lambda pt: (round(pt[2], 2), round(pt[0], 2), round(pt[1], 2)))
            placed_inst: Optional[PlacedCargoInstance] = None

            for pt in unique_ep:
                px, py, pz = pt
                found = False
                for ox, oy, oz, olabel in inst.get_valid_orientations():
                    if px + ox > self.vehicle.internal_length_cm + EPSILON:
                        continue
                    if py + oy > self.vehicle.internal_width_cm + EPSILON:
                        continue
                    if pz + oz > self.vehicle.internal_height_cm + EPSILON:
                        continue

                    # Collision against all currently placed
                    overlaps = False
                    for p in all_current_placed:
                        if (
                            px < p.x_max - EPSILON and px + ox > p.x_cm + EPSILON and
                            py < p.y_max - EPSILON and py + oy > p.y_cm + EPSILON and
                            pz < p.z_max - EPSILON and pz + oz > p.z_cm + EPSILON
                        ):
                            overlaps = True
                            break
                    if overlaps:
                        continue

                    # Support check if pz > 0
                    if pz > EPSILON:
                        base_area = ox * oy
                        support_area = 0.0
                        stacking_ok = True
                        fragile_violation = False
                        for p in all_current_placed:
                            if abs(p.z_max - pz) < 0.5:
                                cx = max(0.0, min(px + ox, p.x_max) - max(px, p.x_cm))
                                cy = max(0.0, min(py + oy, p.y_max) - max(py, p.y_cm))
                                carea = cx * cy
                                if carea > EPSILON:
                                    if not p.stackable:
                                        stacking_ok = False
                                        break
                                    if p.fragile:
                                        fragile_violation = True
                                        break
                                    support_area += carea
                        if not stacking_ok or fragile_violation:
                            continue
                        if base_area > 0 and (support_area / base_area) < MIN_SUPPORT_RATIO:
                            continue

                    placed_inst = PlacedCargoInstance(
                        instance=inst,
                        x_cm=round(px, 2),
                        y_cm=round(py, 2),
                        z_cm=round(pz, 2),
                        placed_length_cm=round(ox, 2),
                        placed_width_cm=round(oy, 2),
                        placed_height_cm=round(oz, 2),
                        orientation_label=olabel,
                        loading_sequence_index=len(all_current_placed) + 1
                    )
                    found = True
                    break

                if found:
                    break

            if placed_inst is not None:
                newly_placed.append(placed_inst)
                all_current_placed.append(placed_inst)
                current_weight += inst.weight_kg

                # Add new corner candidate points
                bx, by, bz = placed_inst.x_cm, placed_inst.y_cm, placed_inst.z_cm
                bl, bw, bh = placed_inst.placed_length_cm, placed_inst.placed_width_cm, placed_inst.placed_height_cm
                for npt in [(bx + bl, by, bz), (bx, by + bw, bz), (bx, by, bz + bh)]:
                    if (
                        npt[0] < self.vehicle.internal_length_cm - 1.0 and
                        npt[1] < self.vehicle.internal_width_cm - 1.0 and
                        npt[2] < self.vehicle.internal_height_cm - 1.0
                    ):
                        unique_ep.append(npt)
            else:
                unplaced_late.append((
                    inst,
                    "Insufficient residual space without disturbing existing loaded cargo"
                ))

        # Check if all late items were successfully placed with preservation
        if len(newly_placed) == len(late_instances):
            # Perfect fit!
            combined_placed = existing_placed + newly_placed
            val_res = PlacementValidator.validate(self.vehicle, combined_placed)
            placed_vol = sum(p.volume_m3 for p in combined_placed)
            veh_vol = self.vehicle.internal_volume_m3
            vol_util = (placed_vol / veh_vol * 100.0) if veh_vol > 0 else 0.0
            max_x = max(p.x_max for p in combined_placed)
            max_y = max(p.y_max for p in combined_placed)
            max_z = max(p.z_max for p in combined_placed)
            spatial_bound = (max_x * max_y * max_z) / 1_000_000.0
            spatial_util = (spatial_bound / veh_vol * 100.0) if veh_vol > 0 else 0.0

            return OptimizationResult(
                vehicle=self.vehicle,
                status="FEASIBLE" if current_result.status == "FEASIBLE" else "PARTIAL",
                solver_message=f"Late orders accommodated successfully! {len(newly_placed)} late items added while preserving existing cargo positions.",
                placed_instances=combined_placed,
                unplaced_instances=current_result.unplaced_instances,
                loaded_weight_kg=round(current_weight, 2),
                remaining_payload_kg=round(max(0.0, self.vehicle.max_payload_kg - current_weight), 2),
                total_requested_volume_m3=round(current_result.total_requested_volume_m3 + sum(i.volume_m3 for i in late_instances), 3),
                placed_cargo_volume_m3=round(placed_vol, 3),
                volume_utilization_pct=round(vol_util, 2),
                spatial_bounding_volume_m3=round(spatial_bound, 3),
                spatial_utilization_pct=round(spatial_util, 2),
                validation_result=val_res,
                execution_time_sec=current_result.execution_time_sec
            )

        # If preservation did not fit all late items and reorganization is allowed:
        if allow_reorganization:
            # Reconstruct original items + late items
            # We recreate CargoItems from existing placed and unplaced + late_items
            all_items: List[CargoItem] = []
            seen_items = {}
            for p in current_result.placed_instances:
                parent_id = p.parent_item_id
                if parent_id not in seen_items:
                    seen_items[parent_id] = CargoItem(
                        item_id=p.parent_item_id,
                        name=p.name,
                        length_cm=p.instance.length_cm,
                        width_cm=p.instance.width_cm,
                        height_cm=p.instance.height_cm,
                        unit_weight_kg=p.weight_kg,
                        quantity=1,
                        fragile=p.fragile,
                        stackable=p.stackable,
                        max_top_load_kg=p.max_top_load_kg,
                        upright_only=p.instance.upright_only,
                        orientation_mode=p.instance.orientation_mode,
                        is_late_order=p.is_late_order
                    )
                else:
                    seen_items[parent_id].quantity += 1

            for u_inst, _ in current_result.unplaced_instances:
                parent_id = u_inst.parent_item_id
                if parent_id not in seen_items:
                    seen_items[parent_id] = CargoItem(
                        item_id=u_inst.parent_item_id,
                        name=u_inst.name,
                        length_cm=u_inst.length_cm,
                        width_cm=u_inst.width_cm,
                        height_cm=u_inst.height_cm,
                        unit_weight_kg=u_inst.weight_kg,
                        quantity=1,
                        fragile=u_inst.fragile,
                        stackable=u_inst.stackable,
                        max_top_load_kg=u_inst.max_top_load_kg,
                        upright_only=u_inst.upright_only,
                        orientation_mode=u_inst.orientation_mode,
                        is_late_order=u_inst.is_late_order
                    )
                else:
                    seen_items[parent_id].quantity += 1

            all_items = list(seen_items.values()) + late_items
            optimizer = PackingOptimizer(self.vehicle)
            revised_result = optimizer.pack(all_items)
            revised_result.solver_message = (
                f"Reorganized plan with late orders: {len(revised_result.placed_instances)} placed, "
                f"{len(revised_result.unplaced_instances)} unplaced."
            )
            return revised_result

        # Reorganization was not permitted or not selected: return partial preservation result
        combined_placed = existing_placed + newly_placed
        combined_unplaced = list(current_result.unplaced_instances) + unplaced_late
        val_res = PlacementValidator.validate(self.vehicle, combined_placed)
        placed_vol = sum(p.volume_m3 for p in combined_placed)
        veh_vol = self.vehicle.internal_volume_m3
        vol_util = (placed_vol / veh_vol * 100.0) if veh_vol > 0 else 0.0
        max_x = max((p.x_max for p in combined_placed), default=0.0)
        max_y = max((p.y_max for p in combined_placed), default=0.0)
        max_z = max((p.z_max for p in combined_placed), default=0.0)
        spatial_bound = (max_x * max_y * max_z) / 1_000_000.0
        spatial_util = (spatial_bound / veh_vol * 100.0) if veh_vol > 0 else 0.0

        return OptimizationResult(
            vehicle=self.vehicle,
            status="PARTIAL",
            solver_message=(
                f"Late replanning completed: {len(newly_placed)} of {len(late_instances)} late items accommodated "
                f"in remaining space without disturbing existing cargo. {len(unplaced_late)} late items could not fit."
            ),
            placed_instances=combined_placed,
            unplaced_instances=combined_unplaced,
            loaded_weight_kg=round(current_weight, 2),
            remaining_payload_kg=round(max(0.0, self.vehicle.max_payload_kg - current_weight), 2),
            total_requested_volume_m3=round(current_result.total_requested_volume_m3 + sum(i.volume_m3 for i in late_instances), 3),
            placed_cargo_volume_m3=round(placed_vol, 3),
            volume_utilization_pct=round(vol_util, 2),
            spatial_bounding_volume_m3=round(spatial_bound, 3),
            spatial_utilization_pct=round(spatial_util, 2),
            validation_result=val_res,
            execution_time_sec=current_result.execution_time_sec
        )
