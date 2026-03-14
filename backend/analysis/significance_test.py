"""Statistical significance testing for particle discovery."""

from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(slots=True)
class SignificanceCalculator:
    """Compute discovery significance from signal and background counts."""

    def simple_significance(self, signal: float, background: float) -> float:
        """S / √B significance estimate."""
        if background <= 0:
            return 0.0
        return signal / math.sqrt(background)

    def profile_likelihood_significance(self, signal: float, background: float) -> float:
        """Approximate significance using profile likelihood ratio.

        Z = √(2[(s+b)ln(1+s/b) − s])  (Asimov formula)
        """
        if background <= 0 or signal <= 0:
            return 0.0
        sb = signal + background
        z_sq = 2.0 * (sb * math.log(1.0 + signal / background) - signal)
        return math.sqrt(max(0.0, z_sq))

    def p_value_from_sigma(self, sigma: float) -> float:
        """Approximate p-value from significance (σ).

        Uses normal distribution survival function approximation.
        """
        return 0.5 * math.erfc(sigma / math.sqrt(2.0))

    def is_discovery(self, sigma: float) -> bool:
        """5σ discovery threshold."""
        return sigma >= 5.0

    def is_evidence(self, sigma: float) -> bool:
        """3σ evidence threshold."""
        return sigma >= 3.0
