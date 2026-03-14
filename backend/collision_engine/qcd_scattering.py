"""QCD scattering — parton-level 2→2 interactions.

Implements simplified QCD scattering processes:
    q + q → q + q,  g + g → g + g,  q + q̄ → g + g,  g + g → q + q̄
Cross-section weighting determines which process is selected.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from backend.collision_engine.parton_distribution import Parton


@dataclass(frozen=True, slots=True)
class ScatteredParton:
    """Output parton from a scattering interaction."""
    flavour: str
    energy_gev: float
    theta: float  # scattering angle (radians)
    phi: float


@dataclass(slots=True)
class QCDScattering:
    """Simplified QCD 2→2 scattering engine.

    Attributes:
        alpha_s: strong coupling constant (fixed).
    """

    alpha_s: float = 0.118

    def scatter(self, p1: Parton, p2: Parton, sqrt_s_gev: float, sampler) -> list[ScatteredParton]:
        """Simulate 2→2 scattering and return outgoing partons."""
        if sqrt_s_gev <= 0.1:
            return []

        # Determine process
        is_gluon_1 = p1.flavour == "gluon"
        is_gluon_2 = p2.flavour == "gluon"

        if is_gluon_1 and is_gluon_2:
            out_flavours = self._gg_scatter(sampler)
        elif is_gluon_1 or is_gluon_2:
            quark = p1 if not is_gluon_1 else p2
            out_flavours = [quark.flavour, "gluon"]
        else:
            # q + q or q + q̄
            is_annihilation = (
                p1.flavour.replace("anti_", "") == p2.flavour.replace("anti_", "")
                and (p1.flavour.startswith("anti_") != p2.flavour.startswith("anti_"))
            )
            if is_annihilation and sampler.uniform() < 0.3:
                out_flavours = ["gluon", "gluon"]
            else:
                out_flavours = [p1.flavour, p2.flavour]

        # Kinematics: split energy, sample angles
        e_each = sqrt_s_gev / max(len(out_flavours), 1)
        result = []
        for flav in out_flavours:
            theta = sampler.uniform(0.1, math.pi - 0.1)
            phi = sampler.uniform(0.0, 2.0 * math.pi)
            e_smear = e_each * sampler.uniform(0.7, 1.3)
            result.append(ScatteredParton(flavour=flav, energy_gev=e_smear, theta=theta, phi=phi))
        return result

    def _gg_scatter(self, sampler) -> list[str]:
        """g + g → ? process selection."""
        r = sampler.uniform()
        if r < 0.6:
            return ["gluon", "gluon"]  # g+g → g+g
        elif r < 0.8:
            return ["u", "anti_u"]  # g+g → qq̄
        elif r < 0.9:
            return ["d", "anti_d"]
        else:
            return ["s", "anti_s"]
