"""Monte Carlo sampling tools for event generation.

Provides random samplers used throughout the collision engine: uniform,
Gaussian, exponential, Breit-Wigner (relativistic resonance), power-law,
and generic accept/reject and importance sampling algorithms.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable


@dataclass(slots=True)
class MonteCarloSampler:
    """Seeded random sampler with physics-oriented distributions.

    All methods are deterministic for a fixed ``seed``.
    """

    seed: int = 42
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def reset(self, seed: int | None = None) -> None:
        """Re-seed the sampler."""
        self.seed = seed if seed is not None else self.seed
        self._rng = random.Random(self.seed)

    # -- basic distributions -------------------------------------------------

    def uniform(self, low: float = 0.0, high: float = 1.0) -> float:
        """Uniform random in [low, high)."""
        return self._rng.uniform(low, high)

    def gaussian(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        """Gaussian (normal) distribution."""
        return self._rng.gauss(mu, sigma)

    def exponential(self, mean: float = 1.0) -> float:
        """Exponential distribution with given mean (= 1/λ)."""
        return self._rng.expovariate(1.0 / mean)

    def poisson_count(self, lam: float) -> int:
        """Poisson-distributed integer count (Knuth algorithm for small λ)."""
        if lam <= 0.0:
            return 0
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while True:
            k += 1
            p *= self._rng.random()
            if p < L:
                return k - 1

    # -- physics distributions -----------------------------------------------

    def breit_wigner(self, mass: float, width: float) -> float:
        """Relativistic Breit-Wigner (Cauchy) sampling.

        Used for resonance mass sampling (e.g. Z, W, Higgs bosons).
        The distribution is: f(m) ∝ Γ / [(m − M₀)² + (Γ/2)²]
        """
        u = self._rng.random()
        half_width = width / 2.0
        return mass + half_width * math.tan(math.pi * (u - 0.5))

    def power_law(self, x_min: float, x_max: float, alpha: float) -> float:
        """Power-law distribution p(x) ∝ x^{-α} between x_min and x_max.

        Used in parton distribution function (PDF) sampling.
        """
        if alpha == 1.0:
            return x_min * math.exp(self._rng.random() * math.log(x_max / x_min))
        u = self._rng.random()
        exp = 1.0 - alpha
        return ((x_max ** exp - x_min ** exp) * u + x_min ** exp) ** (1.0 / exp)

    def isotropic_direction(self) -> tuple[float, float, float]:
        """Sample a unit vector uniformly on the sphere.

        Returns (x, y, z) components.
        """
        cos_theta = 2.0 * self._rng.random() - 1.0
        sin_theta = math.sqrt(max(0.0, 1.0 - cos_theta * cos_theta))
        phi = 2.0 * math.pi * self._rng.random()
        return (sin_theta * math.cos(phi), sin_theta * math.sin(phi), cos_theta)

    # -- generic sampling algorithms -----------------------------------------

    def accept_reject(
        self,
        pdf: Callable[[float], float],
        x_min: float,
        x_max: float,
        pdf_max: float,
        max_trials: int = 100_000,
    ) -> float:
        """Von Neumann accept/reject sampling.

        Generates a sample from *pdf(x)* over [x_min, x_max] using a flat
        envelope of height *pdf_max*.
        """
        for _ in range(max_trials):
            x = self.uniform(x_min, x_max)
            y = self.uniform(0.0, pdf_max)
            if y <= pdf(x):
                return x
        raise RuntimeError("accept_reject failed to converge")

    def importance_sample(
        self,
        target: Callable[[float], float],
        proposal_sample: Callable[[], float],
        proposal_pdf: Callable[[float], float],
        n_samples: int = 1000,
    ) -> tuple[list[float], list[float]]:
        """Importance sampling.

        Returns ``(samples, weights)`` where each weight is ``target(x) / proposal(x)``.
        """
        samples: list[float] = []
        weights: list[float] = []
        for _ in range(n_samples):
            x = proposal_sample()
            q = proposal_pdf(x)
            if q > 0.0:
                w = target(x) / q
            else:
                w = 0.0
            samples.append(x)
            weights.append(w)
        return samples, weights
