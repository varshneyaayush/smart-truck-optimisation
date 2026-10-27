"""
core/vehicle_catalogue.py
Loads, validates, and manages the predefined vehicle catalogue from data/vehicles.json.
Provides full verification audit metadata to prevent unverified dimensions from being
falsely represented as confirmed fleet data.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from core.models import Vehicle

DEFAULT_VEHICLES_PATH = Path(__file__).resolve().parent.parent / "data" / "vehicles.json"


class VehicleCatalogue:
    def __init__(self, json_path: Optional[Path] = None):
        self.json_path = json_path or DEFAULT_VEHICLES_PATH
        self._vehicles: Dict[str, Vehicle] = {}
        self.load()

    def load(self) -> None:
        """Loads vehicle records from the configured JSON file."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"Vehicle catalogue file not found at: {self.json_path}")

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        vehicles_raw = data.get("vehicles", [])
        self._vehicles.clear()

        for raw in vehicles_raw:
            veh = Vehicle(
                id=str(raw["id"]),
                label=str(raw["label"]),
                category=str(raw["category"]),
                nominal_volume_m3=float(raw["nominal_volume_m3"]),
                max_payload_kg=float(raw["max_payload_kg"]),
                internal_length_cm=float(raw["internal_length_cm"]),
                internal_width_cm=float(raw["internal_width_cm"]),
                internal_height_cm=float(raw["internal_height_cm"]),
                door_width_cm=float(raw.get("door_width_cm", raw["internal_width_cm"] * 0.95)),
                door_height_cm=float(raw.get("door_height_cm", raw["internal_height_cm"] * 0.95)),
                is_verified=bool(raw.get("is_verified", False)),
                verification_status=str(raw.get("verification_status", "Unverified - Reference Estimate")),
                curb_weight_kg=float(raw.get("curb_weight_kg", 0.0)),
                max_gross_weight_kg=float(raw.get("max_gross_weight_kg", 0.0)),
                axle_load_limit_front_kg=float(raw.get("axle_load_limit_front_kg", 0.0)),
                axle_load_limit_rear_kg=float(raw.get("axle_load_limit_rear_kg", 0.0)),
                notes=str(raw.get("notes", "")),
            )
            self._vehicles[veh.id] = veh

    def get_all(self) -> List[Vehicle]:
        return list(self._vehicles.values())

    def get_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        return self._vehicles.get(vehicle_id)

    def is_verified(self, vehicle_id: str) -> bool:
        veh = self.get_by_id(vehicle_id)
        return veh.is_verified if veh else False
