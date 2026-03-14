"""Beam source — generates initial particle beams.

Creates bunches of protons (or other species) with configurable energy,
intensity, transverse spread, and longitudinal spacing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from backend.core_math.constants import SPEED_OF_LIGHT, PARTICLE_MASSES, GEV_TO_JOULE
from backend.core_math.monte_carlo import MonteCarloSampler
from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle


@dataclass(slots=True)
class BeamSource:
    """Configurable particle beam generator.

    Attributes:
        species: particle type (e.g. 'proton').
        beam_energy_gev: kinetic energy per particle in GeV.
        particles_per_bunch: number of particles per bunch.
        bunch_spread_m: transverse Gaussian spread σ (metres).
        longitudinal_spacing_m: spacing between particles in a bunch.
        seed: RNG seed for reproducibility.
    """

    species: str = "proton"
    beam_energy_gev: float = 6500.0
    particles_per_bunch: int = 6
    bunch_spread_m: float = 0.018
    longitudinal_spacing_m: float = 0.008
    seed: int = 42
    _sampler: MonteCarloSampler = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._sampler = MonteCarloSampler(seed=self.seed)

    def _beam_speed(self) -> float:
        """Compute speed from kinetic energy using relativistic formula."""
        mass = PARTICLE_MASSES.get(self.species, PARTICLE_MASSES["proton"])
        mc2 = mass * SPEED_OF_LIGHT ** 2
        if mc2 <= 0.0:
            return SPEED_OF_LIGHT
        ke_j = self.beam_energy_gev * GEV_TO_JOULE
        gamma = 1.0 + ke_j / mc2
        if gamma <= 1.0:
            return 0.0
        beta_sq = 1.0 - 1.0 / (gamma * gamma)
        return SPEED_OF_LIGHT * math.sqrt(max(0.0, beta_sq))

    def generate_beam(self, direction: Vector3 = Vector3(1.0, 0.0, 0.0), offset: Vector3 = Vector3()) -> list[Particle]:
        """Generate a single bunch of particles.

        Args:
            direction: unit vector for beam direction.
            offset: transverse offset for the beam centroid.

        Returns:
            List of ``Particle`` objects.
        """
        speed = self._beam_speed()
        velocity = direction.normalized() * speed
        particles: list[Particle] = []

        for i in range(self.particles_per_bunch):
            center_offset = (i - (self.particles_per_bunch - 1) * 0.5) * self.longitudinal_spacing_m
            dy = center_offset + self._sampler.gaussian(0.0, self.bunch_spread_m)
            dz = self._sampler.gaussian(0.0, self.bunch_spread_m * 0.35)
            pos = Vector3(offset.x, offset.y + dy, offset.z + dz)
            particles.append(Particle(species=self.species, position=pos, velocity=velocity))

        return particles

    def generate_counter_beams(self) -> list[Particle]:
        """Generate two head-on bunches (beam 1 and beam 2)."""
        base_x = 0.03
        beam1 = self.generate_beam(
            direction=Vector3(1.0, 0.0, 0.0),
            offset=Vector3(-base_x, 0.0, 0.0),
        )
        beam2 = self.generate_beam(
            direction=Vector3(-1.0, 0.0, 0.0),
            offset=Vector3(base_x, 0.0, 0.0),
        )
        return beam1 + beam2
