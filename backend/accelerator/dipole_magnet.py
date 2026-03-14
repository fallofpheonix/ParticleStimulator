"""Dipole magnet — provides uniform B-field for beam bending.

A dipole magnet produces a constant magnetic field perpendicular to the
beam direction, causing charged particles to follow circular arcs.
The bending radius is ρ = p / (qB).
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.core_math.vector3 import Vector3


@dataclass(frozen=True, slots=True)
class DipoleMagnet:
    """Uniform dipole magnet with field along the z-axis.

    Attributes:
        field_strength_t: magnetic field strength in Tesla.
        length_m: effective magnet length along the beamline.
        aperture_m: half-aperture of the magnet bore.
    """

    field_strength_t: float = 3.5
    length_m: float = 14.3
    aperture_m: float = 0.028

    def field_at(self, _position: Vector3) -> Vector3:
        """Return uniform B-field (0, 0, B_z)."""
        return Vector3(0.0, 0.0, self.field_strength_t)

    def bending_radius(self, momentum_kgms: float, charge_c: float) -> float:
        """ρ = p / (|q|B) in metres."""
        qb = abs(charge_c * self.field_strength_t)
        if qb == 0.0:
            return float("inf")
        return abs(momentum_kgms) / qb

    def bending_angle(self, momentum_kgms: float, charge_c: float) -> float:
        """θ = L / ρ  (radians) for the magnet length."""
        rho = self.bending_radius(momentum_kgms, charge_c)
        if rho == float("inf"):
            return 0.0
        return self.length_m / rho
