"""Particle shower — parton cascade via gluon emission and splitting.

Models the DGLAP-style parton shower where high-energy partons radiate
gluons and split into quark pairs, building up a cascade of secondary
partons that eventually forms jets.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from backend.collision_engine.qcd_scattering import ScatteredParton


@dataclass(frozen=True, slots=True)
class ShowerParton:
    """A parton produced during the showering process."""
    flavour: str
    energy_gev: float
    theta: float
    phi: float
    generation: int  # shower depth


@dataclass(slots=True)
class ParticleShower:
    """Simplified parton shower generator.

    Attributes:
        cutoff_gev: minimum energy to continue showering.
        splitting_probability: probability of splitting at each step.
        max_generations: maximum cascade depth.
    """

    cutoff_gev: float = 1.0
    splitting_probability: float = 0.4
    max_generations: int = 6

    def generate_shower(self, partons: list[ScatteredParton], sampler) -> list[ShowerParton]:
        """Run the parton shower cascade."""
        result: list[ShowerParton] = []
        queue = [
            ShowerParton(p.flavour, p.energy_gev, p.theta, p.phi, 0) for p in partons
        ]

        while queue:
            parton = queue.pop(0)
            result.append(parton)

            if parton.generation >= self.max_generations:
                continue
            if parton.energy_gev < self.cutoff_gev:
                continue
            if sampler.uniform() > self.splitting_probability:
                continue

            # Split parton into two daughters
            z = sampler.uniform(0.1, 0.9)  # momentum fraction
            e1 = parton.energy_gev * z
            e2 = parton.energy_gev * (1.0 - z)

            d_theta = sampler.gaussian(0.0, 0.15)
            d_phi = sampler.uniform(0.0, 2.0 * math.pi)

            if parton.flavour == "gluon":
                if sampler.uniform() < 0.5:
                    flav1, flav2 = "gluon", "gluon"
                else:
                    flav1, flav2 = "u", "anti_u"
            else:
                flav1 = parton.flavour
                flav2 = "gluon"

            gen = parton.generation + 1
            queue.append(ShowerParton(flav1, e1, parton.theta + d_theta, parton.phi, gen))
            queue.append(ShowerParton(flav2, e2, parton.theta - d_theta, d_phi, gen))

        return result
