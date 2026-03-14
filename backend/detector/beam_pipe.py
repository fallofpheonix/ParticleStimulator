"""Beam pipe — innermost detector element."""

from __future__ import annotations
from dataclasses import dataclass
from backend.core_math.vector3 import Vector3


@dataclass(frozen=True, slots=True)
class BeamPipe:
    """Thin-walled vacuum beam pipe."""
    radius_m: float = 0.024
    wall_thickness_m: float = 0.0008
    material: str = "beryllium"

    def is_inside(self, position: Vector3) -> bool:
        return position.radial_xy() < self.radius_m

    def traverses_wall(self, r_prev: float, r_curr: float) -> bool:
        """Check if a particle crossed the beam pipe wall between two radii."""
        return (r_prev < self.radius_m) != (r_curr < self.radius_m)
