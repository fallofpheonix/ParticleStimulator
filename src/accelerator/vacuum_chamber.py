from __future__ import annotations

from dataclasses import dataclass

from core.vector import Vector3


@dataclass(frozen=True, slots=True)
class VacuumChamber:
    aperture_radius_m: float
    half_length_m: float

    def contains(self, position: Vector3) -> bool:
        return position.radial_xy() <= self.aperture_radius_m and abs(position.z) <= self.half_length_m
