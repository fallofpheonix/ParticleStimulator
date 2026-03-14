"""Background model — estimates non-signal event contributions."""

from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(slots=True)
class BackgroundModel:
    """Parametric background model for mass spectrum analysis.

    Supports exponential, polynomial, and power-law shapes.
    """

    def exponential(self, x: float, norm: float, slope: float) -> float:
        """Exponential background: N · exp(slope · x)."""
        return norm * math.exp(slope * x)

    def polynomial(self, x: float, coefficients: list[float]) -> float:
        """Polynomial background."""
        return sum(c * x ** i for i, c in enumerate(coefficients))

    def estimate_background(self, bin_values: list[float], signal_region: tuple[int, int]) -> list[float]:
        """Estimate background by interpolating sideband regions.

        Fits a linear model to bins outside the signal region and
        interpolates into the signal window.
        """
        lo, hi = signal_region
        sideband_x, sideband_y = [], []
        for i, v in enumerate(bin_values):
            if i < lo or i > hi:
                sideband_x.append(float(i))
                sideband_y.append(v)

        if len(sideband_x) < 2:
            return bin_values[:]

        # Linear fit: y = a + b*x
        n = len(sideband_x)
        sx = sum(sideband_x)
        sy = sum(sideband_y)
        sxx = sum(x * x for x in sideband_x)
        sxy = sum(x * y for x, y in zip(sideband_x, sideband_y))
        denom = n * sxx - sx * sx
        if abs(denom) < 1e-10:
            avg = sy / n
            return [avg] * len(bin_values)

        b = (n * sxy - sx * sy) / denom
        a = (sy - b * sx) / n

        return [a + b * i for i in range(len(bin_values))]

    def signal_minus_background(self, data: list[float], background: list[float]) -> list[float]:
        """Subtract background from data."""
        return [d - bg for d, bg in zip(data, background)]
