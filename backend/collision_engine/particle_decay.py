"""Particle decay engine — recursive decay chains until stable particles.

Implements decay channels for unstable hadrons and leptons with branching
ratios.  Decay continues until only stable particles remain.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from backend.core_math.constants import SPEED_OF_LIGHT
from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle


# Decay channel: (daughter species list, branching ratio)
DECAY_TABLE: dict[str, list[tuple[list[str], float]]] = {
    "pi0": [
        (["photon", "photon"], 0.988),
        (["photon", "electron", "positron"], 0.012),
    ],
    "K+": [
        (["muon+", "nu_mu"], 0.636),
        (["pi+", "pi0"], 0.209),
        (["pi+", "pi+", "pi-"], 0.056),
    ],
    "K-": [
        (["muon-", "anti_nu_mu"], 0.636),
        (["pi-", "pi0"], 0.209),
        (["pi-", "pi-", "pi+"], 0.056),
    ],
    "muon-": [
        (["electron", "anti_nu_e", "nu_mu"], 1.0),
    ],
    "muon+": [
        (["positron", "nu_e", "anti_nu_mu"], 1.0),
    ],
}

STABLE_SPECIES: set[str] = {
    "electron", "positron", "proton", "antiproton", "neutron",
    "photon", "nu_e", "nu_mu", "nu_tau", "anti_nu_e", "anti_nu_mu", "anti_nu_tau",
    "pi+", "pi-",  # long-lived, treat as stable for detector timescale
}


@dataclass(slots=True)
class DecayEngine:
    """Recursive particle decay engine.

    Attributes:
        max_depth: maximum decay chain depth.
        decay_probability: probability of an unstable particle decaying
            within the simulation timescale (simplified model).
    """

    max_depth: int = 10
    decay_probability: float = 0.9

    def should_decay(self, particle: Particle, sampler) -> bool:
        """Decide whether a particle decays in this step."""
        if particle.species in STABLE_SPECIES:
            return False
        if particle.species not in DECAY_TABLE:
            return False
        return sampler.uniform() < self.decay_probability

    def decay_particle(self, particle: Particle, sampler) -> list[Particle]:
        """Decay a single particle into daughters."""
        channels = DECAY_TABLE.get(particle.species, [])
        if not channels:
            return [particle]

        # Sample decay channel by branching ratio
        r = sampler.uniform()
        cumulative = 0.0
        selected_daughters = channels[0][0]
        for daughters, br in channels:
            cumulative += br
            if r <= cumulative:
                selected_daughters = daughters
                break

        # Generate daughter particles with isotropic decay
        n = len(selected_daughters)
        result = []
        for i, species in enumerate(selected_daughters):
            dx, dy, dz = sampler.isotropic_direction()
            speed = min(0.9 * SPEED_OF_LIGHT, particle.speed() * 0.8)
            velocity = Vector3(dx * speed, dy * speed, dz * speed)
            result.append(Particle(
                species=species,
                position=particle.position,
                velocity=velocity,
                parent_id=particle.particle_id,
            ))

        particle.alive = False
        return result

    def decay_all(self, particles: list[Particle], vertex: Vector3, sampler) -> list[Particle]:
        """Recursively decay all unstable particles."""
        final: list[Particle] = []
        queue = list(particles)
        depth = 0

        while queue and depth < self.max_depth:
            next_queue: list[Particle] = []
            for p in queue:
                if not p.alive:
                    final.append(p)
                    continue
                if self.should_decay(p, sampler):
                    daughters = self.decay_particle(p, sampler)
                    next_queue.extend(daughters)
                    final.append(p)  # dead parent
                else:
                    final.append(p)
            queue = next_queue
            depth += 1

        final.extend(queue)  # any remaining at max depth
        return final
