"""Missing transverse energy (MET) — momentum balance calculation.

Neutrinos and other invisible particles are inferred from the momentum
imbalance of all visible particles in the transverse plane.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from backend.detector.calorimeter_em import EMDeposit
from backend.detector.calorimeter_hadronic import HadronicDeposit


@dataclass(frozen=True, slots=True)
class MissingET:
    """Missing transverse energy result."""
    met_gev: float
    met_phi: float
    sum_et_gev: float


@dataclass(slots=True)
class MissingEnergyCalculator:
    """Computes missing transverse energy from calorimeter deposits."""

    def compute(self, em: list[EMDeposit], had: list[HadronicDeposit]) -> MissingET:
        px_total = 0.0
        py_total = 0.0
        sum_et = 0.0

        for d in em:
            phi = (d.phi_bin + 0.5) / 64 * 2 * math.pi - math.pi
            px_total += d.energy_gev * math.cos(phi)
            py_total += d.energy_gev * math.sin(phi)
            sum_et += d.energy_gev

        for d in had:
            phi = (d.phi_bin + 0.5) / 32 * 2 * math.pi - math.pi
            px_total += d.energy_gev * math.cos(phi)
            py_total += d.energy_gev * math.sin(phi)
            sum_et += d.energy_gev

        met = math.hypot(px_total, py_total)
        met_phi = math.atan2(-py_total, -px_total)
        return MissingET(met, met_phi, sum_et)
