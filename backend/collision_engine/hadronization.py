"""Hadronization — converts partons into observable hadrons.

Implements a simplified string-fragmentation-inspired model where
quarks combine into mesons and baryons, and gluons fragment into
quark pairs that then hadronize.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from backend.collision_engine.particle_shower import ShowerParton
from backend.core_math.constants import SPEED_OF_LIGHT
from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle


@dataclass(slots=True)
class Hadronizer:
    """Simplified hadronization engine.

    Converts shower partons into hadrons (pions, kaons, protons, etc.)
    using a simplified fragmentation model.
    """

    pion_fraction: float = 0.75
    kaon_fraction: float = 0.15
    # remainder → proton/neutron

    def hadronize(self, shower_partons: list[ShowerParton], vertex: Vector3, sampler) -> list[Particle]:
        """Convert shower partons into hadrons."""
        hadrons: list[Particle] = []

        for parton in shower_partons:
            if parton.energy_gev < 0.14:  # below pion mass
                continue

            # Determine hadron species
            r = sampler.uniform()
            if r < self.pion_fraction:
                charge_roll = sampler.uniform()
                if charge_roll < 0.33:
                    species = "pi+"
                elif charge_roll < 0.66:
                    species = "pi-"
                else:
                    species = "pi0"
            elif r < self.pion_fraction + self.kaon_fraction:
                species = "K+" if sampler.uniform() < 0.5 else "K-"
            else:
                species = "proton" if sampler.uniform() < 0.5 else "neutron"

            # Build momentum from parton kinematics
            speed = min(0.95 * SPEED_OF_LIGHT, parton.energy_gev * 1.0e8)
            vx = speed * math.sin(parton.theta) * math.cos(parton.phi)
            vy = speed * math.sin(parton.theta) * math.sin(parton.phi)
            vz = speed * math.cos(parton.theta)

            hadrons.append(Particle(
                species=species,
                position=vertex,
                velocity=Vector3(vx, vy, vz),
            ))

        return hadrons
