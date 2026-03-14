"""Sextupole magnet — chromaticity correction.

Sextupole magnets produce a quadratic field used to correct
chromaticity (energy-dependent focusing) in accelerator lattices.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.core_math.vector3 import Vector3


@dataclass(frozen=True, slots=True)
class SextupoleMagnet:
    """Sextupole with second-order field: B ∝ (x² − y², 2xy, 0).

    Attributes:
        strength_t_per_m2: sextupole strength in T/m².
        length_m: effective length.
    """

    strength_t_per_m2: float = 0.5
    length_m: float = 0.8

    def field_at(self, position: Vector3) -> Vector3:
        """B = S/2 · (x² − y², 2xy, 0)."""
        s = self.strength_t_per_m2 / 2.0
        return Vector3(
            s * (position.x ** 2 - position.y ** 2),
            s * 2.0 * position.x * position.y,
            0.0,
        )
