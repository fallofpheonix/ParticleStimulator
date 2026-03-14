"""Vacuum chamber — beam pipe boundary constraints.

Defines the physical aperture within which particles must remain.
Particles outside the chamber are considered lost.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.core_math.vector3 import Vector3


@dataclass(frozen=True, slots=True)
class VacuumChamber:
    """Cylindrical vacuum chamber around the beamline.

    Attributes:
        aperture_radius_m: transverse aperture radius.
        half_length_m: half-length along the beam (z) axis.
        pressure_pa: residual gas pressure (Pa), affects beam lifetime.
    """

    aperture_radius_m: float = 1.5
    half_length_m: float = 2.0
    pressure_pa: float = 1.0e-7

    def contains(self, position: Vector3) -> bool:
        """Return True if position is inside the chamber."""
        return (
            position.radial_xy() <= self.aperture_radius_m
            and abs(position.z) <= self.half_length_m
        )

    def distance_to_wall(self, position: Vector3) -> float:
        """Radial distance from position to the chamber wall (metres)."""
        return max(0.0, self.aperture_radius_m - position.radial_xy())
