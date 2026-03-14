"""Likelihood fitting — parameter estimation for signal+background models."""

from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(slots=True)
class LikelihoodFitter:
    """Binned extended maximum-likelihood fitter.

    Fits a signal+background model to observed bin counts.
    """

    def gaussian_signal(self, x: float, mu: float, sigma: float, amplitude: float) -> float:
        """Gaussian signal shape."""
        if sigma <= 0:
            return 0.0
        return amplitude * math.exp(-0.5 * ((x - mu) / sigma) ** 2)

    def polynomial_background(self, x: float, coeffs: list[float]) -> float:
        """Polynomial background model: bg(x) = c0 + c1*x + c2*x² + ..."""
        return sum(c * x ** i for i, c in enumerate(coeffs))

    def log_likelihood(
        self,
        observed: list[int],
        expected: list[float],
    ) -> float:
        """Poisson log-likelihood: ΣΣ [n_i ln(μ_i) − μ_i − ln(n_i!)]."""
        ll = 0.0
        for obs, exp in zip(observed, expected):
            if exp <= 0:
                exp = 1e-10
            ll += obs * math.log(exp) - exp
            # Omit ln(n!) as constant in optimization
        return ll

    def chi_squared(self, observed: list[int], expected: list[float]) -> float:
        """χ² = Σ (observed − expected)² / expected."""
        chi2 = 0.0
        for o, e in zip(observed, expected):
            if e > 0:
                chi2 += (o - e) ** 2 / e
        return chi2

    def reduced_chi_squared(self, observed: list[int], expected: list[float], n_params: int) -> float:
        """χ²/ndf."""
        ndf = len(observed) - n_params
        if ndf <= 0:
            return float("inf")
        return self.chi_squared(observed, expected) / ndf
