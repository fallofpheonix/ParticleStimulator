"""Cross-section calculator — interaction probability computation.

Provides simplified cross-section estimates for various scattering
processes as a function of centre-of-mass energy √s.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(slots=True)
class CrossSectionCalculator:
    """Simplified cross-section estimator.

    Uses parametric fits rather than full matrix-element calculations.
    """

    alpha_s: float = 0.118
    alpha_em: float = 1.0 / 137.0

    def total_pp_cross_section_mb(self, sqrt_s_gev: float) -> float:
        """Total pp cross section in millibarns (Donnachie-Landshoff fit)."""
        if sqrt_s_gev <= 0.0:
            return 0.0
        return 21.7 * sqrt_s_gev ** 0.0808 + 56.08 * sqrt_s_gev ** (-0.4525)

    def inelastic_pp_cross_section_mb(self, sqrt_s_gev: float) -> float:
        """Inelastic pp cross section ≈ 75% of total."""
        return 0.75 * self.total_pp_cross_section_mb(sqrt_s_gev)

    def gg_to_gg_mb(self, s_hat_gev2: float) -> float:
        """gg → gg differential cross section estimate (simplified)."""
        if s_hat_gev2 <= 1.0:
            return 0.0
        return 9.0 * math.pi * self.alpha_s ** 2 / (2.0 * s_hat_gev2) * 0.389e-3

    def qq_to_gg_mb(self, s_hat_gev2: float) -> float:
        """qq̄ → gg cross section estimate."""
        if s_hat_gev2 <= 1.0:
            return 0.0
        return 8.0 * math.pi * self.alpha_s ** 2 / (9.0 * s_hat_gev2) * 0.389e-3

    def higgs_production_pb(self, sqrt_s_gev: float) -> float:
        """Approximate gg → H production cross section in picobarns.

        Uses a rough fit to LHC measurements at √s = 13 TeV ≈ 50 pb.
        """
        if sqrt_s_gev < 200.0:
            return 0.0
        return 50.0 * (sqrt_s_gev / 13000.0) ** 1.7
