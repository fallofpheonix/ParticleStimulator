"""Coulomb (electrostatic) force between charged particles.

Provides pairwise Coulomb force, potential energy, and a spatial-grid
accelerated N-body force accumulator for charged-particle interactions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from backend.core_math.constants import VACUUM_PERMITTIVITY
from backend.core_math.vector3 import Vector3

# Coulomb constant k_e = 1/(4πε₀)
COULOMB_CONSTANT: float = 1.0 / (4.0 * math.pi * VACUUM_PERMITTIVITY)

# Minimum separation to avoid singularity (metres)
_MIN_SEPARATION: float = 1.0e-15


def coulomb_force(
    charge_1: float,
    charge_2: float,
    position_1: Vector3,
    position_2: Vector3,
) -> Vector3:
    """Coulomb force on particle 1 due to particle 2.

    F⃗₁₂ = k_e · q₁q₂ / r² · r̂₁₂

    where r̂₁₂ points from 2 → 1.
    """
    displacement = position_1 - position_2  # from 2 toward 1
    r_sq = displacement.magnitude_squared()
    r_sq = max(r_sq, _MIN_SEPARATION ** 2)
    r = math.sqrt(r_sq)
    magnitude = COULOMB_CONSTANT * charge_1 * charge_2 / r_sq
    return displacement.normalized() * magnitude


def coulomb_potential(charge_1: float, charge_2: float, separation_m: float) -> float:
    """Coulomb potential energy U = k_e · q₁q₂ / r (Joules)."""
    r = max(abs(separation_m), _MIN_SEPARATION)
    return COULOMB_CONSTANT * charge_1 * charge_2 / r


@dataclass(slots=True)
class CoulombAccumulator:
    """Accumulate pair-wise Coulomb forces for N charged bodies.

    For small N (< 200) a direct O(N²) sum is used.  For larger systems a
    spatial grid or tree approximation can be plugged in via subclassing.
    """

    softening_m: float = 1.0e-15

    def compute_forces(
        self,
        charges: list[float],
        positions: list[Vector3],
    ) -> list[Vector3]:
        """Return net Coulomb force on each particle.

        Args:
            charges: list of charge values (Coulombs).
            positions: list of position vectors.

        Returns:
            List of net force vectors (one per particle).
        """
        n = len(charges)
        forces = [Vector3() for _ in range(n)]
        soft_sq = self.softening_m ** 2
        for i in range(n):
            if charges[i] == 0.0:
                continue
            for j in range(i + 1, n):
                if charges[j] == 0.0:
                    continue
                displacement = positions[i] - positions[j]
                r_sq = max(displacement.magnitude_squared(), soft_sq)
                r = math.sqrt(r_sq)
                magnitude = COULOMB_CONSTANT * charges[i] * charges[j] / r_sq
                direction = displacement / r
                f = direction * magnitude
                forces[i] = forces[i] + f
                forces[j] = forces[j] - f
        return forces
