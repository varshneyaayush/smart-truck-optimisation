"""
core/models.py
Data models for the Optimove Smart Truck Loading Optimization System.
Standard internal units:
- Length, Width, Height: Centimetres (cm)
- Weight: Kilograms (kg)
- Volume: Cubic Metres (m³)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import enum


class OrientationType(str, enum.Enum):
    UPRIGHT_ONLY = "UPRIGHT_ONLY"    # Allowed: (L, W, H) and (W, L, H) - height along Z
    ALL = "ALL"                      # All 6 combinations (L,W,H), (W,L,H), (H,L,W), (L,H,W), (W,H,L), (H,W,L)
    FIXED = "FIXED"                  # Only (L, W, H) - no rotation allowed


@dataclass
class Vehicle:
    id: str
    label: str
    category: str
    nominal_volume_m3: float
    max_payload_kg: float
    internal_length_cm: float
    internal_width_cm: float
    internal_height_cm: float
    door_width_cm: float
    door_height_cm: float
    is_verified: bool = False
    verification_status: str = "Unverified - Reference Geometric Estimate"
    curb_weight_kg: float = 0.0
    max_gross_weight_kg: float = 0.0
    axle_load_limit_front_kg: float = 0.0
    axle_load_limit_rear_kg: float = 0.0
    notes: str = ""

    @property
    def internal_volume_m3(self) -> float:
        """Computed internal geometric volume in m³."""
        return (self.internal_length_cm * self.internal_width_cm * self.internal_height_cm) / 1_000_000.0


@dataclass
class CargoItem:
    item_id: str
    name: str
    length_cm: float
    width_cm: float
    height_cm: float
    unit_weight_kg: float
    quantity: int = 1
    fragile: bool = False
    stackable: bool = True
    max_top_load_kg: float = 0.0
    upright_only: bool = True
    orientation_mode: OrientationType = OrientationType.UPRIGHT_ONLY
    is_late_order: bool = False

    @property
    def unit_volume_m3(self) -> float:
        return (self.length_cm * self.width_cm * self.height_cm) / 1_000_000.0

    @property
    def total_weight_kg(self) -> float:
        return self.unit_weight_kg * self.quantity

    @property
    def total_volume_m3(self) -> float:
        return self.unit_volume_m3 * self.quantity

    def expand_instances(self) -> List["CargoInstance"]:
        """Expand this batch into discrete physical cargo units for 3D placement."""
        instances = []
        for i in range(1, self.quantity + 1):
            inst_id = f"{self.item_id}#{i}" if self.quantity > 1 else self.item_id
            instances.append(
                CargoInstance(
                    instance_id=inst_id,
                    parent_item_id=self.item_id,
                    name=self.name,
                    length_cm=self.length_cm,
                    width_cm=self.width_cm,
                    height_cm=self.height_cm,
                    weight_kg=self.unit_weight_kg,
                    fragile=self.fragile,
                    stackable=self.stackable,
                    max_top_load_kg=self.max_top_load_kg,
                    upright_only=self.upright_only,
                    orientation_mode=self.orientation_mode,
                    is_late_order=self.is_late_order,
                )
            )
        return instances


@dataclass
class CargoInstance:
    instance_id: str
    parent_item_id: str
    name: str
    length_cm: float
    width_cm: float
    height_cm: float
    weight_kg: float
    fragile: bool = False
    stackable: bool = True
    max_top_load_kg: float = 0.0
    upright_only: bool = True
    orientation_mode: OrientationType = OrientationType.UPRIGHT_ONLY
    is_late_order: bool = False

    @property
    def volume_m3(self) -> float:
        return (self.length_cm * self.width_cm * self.height_cm) / 1_000_000.0

    def get_valid_orientations(self) -> List[Tuple[float, float, float, str]]:
        """
        Returns list of (dim_x, dim_y, dim_z, label) permissible for this instance.
        - UPRIGHT_ONLY: Z must equal height_cm, (L, W, H) or (W, L, H)
        - FIXED: only (L, W, H)
        - ALL: all 6 permutations
        """
        l, w, h = self.length_cm, self.width_cm, self.height_cm
        if self.orientation_mode == OrientationType.FIXED:
            return [(l, w, h, "LWH (Fixed)")]

        if self.upright_only or self.orientation_mode == OrientationType.UPRIGHT_ONLY:
            opts = [(l, w, h, "LWH (Upright 0°)") ]
            if l != w:
                opts.append((w, l, h, "WLH (Upright 90°)"))
            return opts

        # ALL mode (when upright_only is False and ALL requested)
        permutations = [
            (l, w, h, "LWH (Default)"),
            (w, l, h, "WLH (Z-Rotated 90°)"),
            (h, w, l, "HWL (Tilted Side)"),
            (w, h, l, "WHL (Tilted Side 90°)"),
            (l, h, w, "LHW (Tilted Flat)"),
            (h, l, w, "HLW (Tilted Flat 90°)")
        ]
        # Remove duplicate geometries if cube or square sides
        unique = []
        seen = set()
        for px, py, pz, lbl in permutations:
            key = (round(px, 2), round(py, 2), round(pz, 2))
            if key not in seen:
                seen.add(key)
                unique.append((px, py, pz, lbl))
        return unique


@dataclass
class PlacedCargoInstance:
    instance: CargoInstance
    x_cm: float
    y_cm: float
    z_cm: float
    placed_length_cm: float
    placed_width_cm: float
    placed_height_cm: float
    orientation_label: str
    loading_sequence_index: Optional[int] = None

    @property
    def instance_id(self) -> str:
        return self.instance.instance_id

    @property
    def parent_item_id(self) -> str:
        return self.instance.parent_item_id

    @property
    def name(self) -> str:
        return self.instance.name

    @property
    def weight_kg(self) -> float:
        return self.instance.weight_kg

    @property
    def fragile(self) -> bool:
        return self.instance.fragile

    @property
    def stackable(self) -> bool:
        return self.instance.stackable

    @property
    def max_top_load_kg(self) -> float:
        return self.instance.max_top_load_kg

    @property
    def is_late_order(self) -> bool:
        return self.instance.is_late_order

    @property
    def volume_m3(self) -> float:
        return (self.placed_length_cm * self.placed_width_cm * self.placed_height_cm) / 1_000_000.0

    @property
    def x_max(self) -> float:
        return self.x_cm + self.placed_length_cm

    @property
    def y_max(self) -> float:
        return self.y_cm + self.placed_width_cm

    @property
    def z_max(self) -> float:
        return self.z_cm + self.placed_height_cm


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    item_diagnostics: Dict[str, List[str]] = field(default_factory=dict)
    summary_checks: Dict[str, bool] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    vehicle: Vehicle
    status: str                         # "FEASIBLE", "PARTIAL", "INFEASIBLE", "OVERLOAD"
    solver_message: str
    placed_instances: List[PlacedCargoInstance] = field(default_factory=list)
    unplaced_instances: List[Tuple[CargoInstance, str]] = field(default_factory=list)
    loaded_weight_kg: float = 0.0
    remaining_payload_kg: float = 0.0
    total_requested_volume_m3: float = 0.0
    placed_cargo_volume_m3: float = 0.0
    volume_utilization_pct: float = 0.0
    spatial_bounding_volume_m3: float = 0.0
    spatial_utilization_pct: float = 0.0
    validation_result: Optional[ValidationResult] = None
    execution_time_sec: float = 0.0
