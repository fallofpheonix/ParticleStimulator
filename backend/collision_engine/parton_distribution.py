"""Parton distribution functions (PDFs) for proton structure.

Implements a simplified model of proton parton content: up/down quarks
carry most of the momentum, with sea quarks and gluons at lower x.
Momentum fraction x is sampled using a power-law fitted to
approximate CTEQ/MRST-style PDFs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Parton:
    """A sampled parton from inside a proton."""
    flavour: str  # e.g. "u", "d", "gluon", "anti_u"
    momentum_fraction: float  # x ∈ (0, 1)


@dataclass(slots=True)
class PartonDistribution:
    """Simplified parton distribution function for protons.

    Valence quarks (u, u, d) dominate at high x.
    Sea quarks and gluons dominate at low x.
    """

    valence_probability: float = 0.55
    gluon_probability: float = 0.30
    # remainder = sea quarks

    def sample_parton(self, sampler) -> tuple[float, Parton]:
        """Sample a parton and its momentum fraction x.

        Returns:
            (x, Parton) tuple.
        """
        roll = sampler.uniform(0.0, 1.0)

        if roll < self.valence_probability:
            # Valence quark: higher x (peaked near 0.15-0.3)
            x = sampler.power_law(0.01, 0.8, 1.5)
            flavour = "u" if sampler.uniform() < 0.67 else "d"
        elif roll < self.valence_probability + self.gluon_probability:
            # Gluon: peaked at low x
            x = sampler.power_law(0.001, 0.5, 2.5)
            flavour = "gluon"
        else:
            # Sea quark: low x
            x = sampler.power_law(0.001, 0.3, 3.0)
            sea_flavours = ["anti_u", "anti_d", "s", "anti_s", "c", "anti_c"]
            idx = int(sampler.uniform(0, len(sea_flavours)))
            idx = min(idx, len(sea_flavours) - 1)
            flavour = sea_flavours[idx]

        return x, Parton(flavour=flavour, momentum_fraction=x)
