"""Quadrupole magnet — linear gradient field for beam focusing.

Quadrupole magnets produce a field that increases linearly with distance
from the beam axis, providing strong focusing in one transverse plane
and defocusing in the other (alternating-gradient principle).
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.core_math.vector3 import Vector3


@dataclass(frozen=True, slots=True)
class QuadrupoleMagnet:
    """Quadrupole with field gradient dB/dr.

    Attributes:
        gradient_t_per_m: field gradient in Tesla/metre.
        length_m: effective length along the beamline.
        bore_radius_m: magnet bore radius.
    """

    gradient_t_per_m: float = 0.08
    length_m: float = 3.1
    bore_radius_m: float = 0.028

    def field_at(self, position: Vector3) -> Vector3:
        """B = (g·y, g·x, 0) — linear gradient field."""
        g = self.gradient_t_per_m
        return Vector3(g * position.y, g * position.x, 0.0)

    def focal_length(self, momentum_kgms: float, charge_c: float) -> float:
        """Thin-lens focal length f = p / (q·g·L) in metres."""
        qgl = abs(charge_c * self.gradient_t_per_m * self.length_m)
        if qgl == 0.0:
            return float("inf")
        return abs(momentum_kgms) / qgl
