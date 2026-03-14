"""Invariant mass calculator — computes di-particle invariant mass spectra."""

from __future__ import annotations
import math
from dataclasses import dataclass
from backend.core_math.vector4 import FourVector


@dataclass(slots=True)
class InvariantMassCalculator:
    """Computes invariant mass from 4-momenta of reconstructed objects."""

    def di_object_mass(self, p1: FourVector, p2: FourVector) -> float:
        """Invariant mass of two objects: m = √((p1+p2)²)."""
        combined = p1 + p2
        return combined.invariant_mass()

    def all_pairs(self, momenta: list[FourVector]) -> list[float]:
        """Compute invariant masses for all unique pairs."""
        masses = []
        for i in range(len(momenta)):
            for j in range(i + 1, len(momenta)):
                masses.append(self.di_object_mass(momenta[i], momenta[j]))
        return masses

    def best_z_candidate(self, momenta: list[FourVector], target_mass_gev: float = 91.2) -> float | None:
        """Find the pair closest to the Z boson mass."""
        masses = self.all_pairs(momenta)
        if not masses:
            return None
        return min(masses, key=lambda m: abs(m - target_mass_gev))

    def best_higgs_candidate(self, momenta: list[FourVector], target_mass_gev: float = 125.0) -> float | None:
        """Find the pair closest to the Higgs boson mass."""
        masses = self.all_pairs(momenta)
        if not masses:
            return None
        return min(masses, key=lambda m: abs(m - target_mass_gev))
