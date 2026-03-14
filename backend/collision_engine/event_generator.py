"""Event generator — orchestrates the full collision pipeline.

Drives: collision detection → parton sampling → scattering → shower →
hadronization → decay chain → final-state particles.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from backend.core_math.constants import GEV_TO_JOULE
from backend.core_math.vector3 import Vector3
from backend.core_math.monte_carlo import MonteCarloSampler
from backend.physics_engine.particle_model import Particle
from backend.collision_engine.parton_distribution import PartonDistribution
from backend.collision_engine.qcd_scattering import QCDScattering
from backend.collision_engine.particle_shower import ParticleShower
from backend.collision_engine.hadronization import Hadronizer
from backend.collision_engine.particle_decay import DecayEngine


_event_ids = itertools.count(1)


@dataclass(slots=True)
class CollisionEvent:
    """Result of a single proton-proton collision."""
    event_id: int
    vertex: Vector3
    sqrt_s_gev: float
    incoming_ids: tuple[int, int]
    final_particles: list[Particle]
    parton_x1: float = 0.0
    parton_x2: float = 0.0
    process: str = "pp"


def _should_collide(p1: Particle, p2: Particle, radius: float) -> bool:
    if not p1.alive or not p2.alive:
        return False
    sep = (p1.position - p2.position).magnitude()
    if sep > radius:
        return False
    rel_pos = p2.position - p1.position
    rel_vel = p2.velocity - p1.velocity
    return rel_pos.dot(rel_vel) < 0.0


@dataclass(slots=True)
class EventGenerator:
    """Full collision event generator (PYTHIA-style pipeline).

    Attributes:
        interaction_radius_m: proximity threshold for collision.
        seed: RNG seed.
        pdf: parton distribution function sampler.
        scattering: QCD scattering engine.
        shower: parton shower generator.
        hadronizer: hadronization engine.
        decay: particle decay engine.
    """

    interaction_radius_m: float = 0.06
    seed: int = 42
    pdf: PartonDistribution = field(default_factory=PartonDistribution)
    scattering: QCDScattering = field(default_factory=QCDScattering)
    shower: ParticleShower = field(default_factory=ParticleShower)
    hadronizer: Hadronizer = field(default_factory=Hadronizer)
    decay: DecayEngine = field(default_factory=DecayEngine)
    _sampler: MonteCarloSampler = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._sampler = MonteCarloSampler(seed=self.seed)

    def find_collisions(self, particles: list[Particle]) -> list[tuple[Particle, Particle]]:
        """Find all colliding pairs."""
        pairs = []
        for i, p1 in enumerate(particles):
            if not p1.alive:
                continue
            for p2 in particles[i + 1:]:
                if _should_collide(p1, p2, self.interaction_radius_m):
                    pairs.append((p1, p2))
        return pairs

    def generate_event(self, p1: Particle, p2: Particle) -> CollisionEvent:
        """Run full collision pipeline for one proton-proton pair."""
        vertex = (p1.position + p2.position) * 0.5

        # Compute centre-of-mass energy
        total_ke = p1.kinetic_energy_j() + p2.kinetic_energy_j() if hasattr(p1, 'kinetic_energy_j') else 0.0
        try:
            from backend.physics_engine.relativistic_dynamics import kinetic_energy
            total_ke = kinetic_energy(p1.mass_kg or 0, p1.speed()) + kinetic_energy(p2.mass_kg or 0, p2.speed())
        except Exception:
            pass
        sqrt_s_gev = total_ke / GEV_TO_JOULE if GEV_TO_JOULE > 0 else 0.0

        # Sample partons
        x1, parton1 = self.pdf.sample_parton(self._sampler)
        x2, parton2 = self.pdf.sample_parton(self._sampler)

        # Scattering
        scattered = self.scattering.scatter(parton1, parton2, x1 * sqrt_s_gev, self._sampler)

        # Parton shower
        showered = self.shower.generate_shower(scattered, self._sampler)

        # Hadronization
        hadrons = self.hadronizer.hadronize(showered, vertex, self._sampler)

        # Decay chain
        final = self.decay.decay_all(hadrons, vertex, self._sampler)

        # Kill incoming
        p1.alive = False
        p2.alive = False

        return CollisionEvent(
            event_id=next(_event_ids),
            vertex=vertex,
            sqrt_s_gev=sqrt_s_gev,
            incoming_ids=(p1.particle_id, p2.particle_id),
            final_particles=final,
            parton_x1=x1,
            parton_x2=x2,
        )

    def process_collisions(self, particles: list[Particle]) -> list[CollisionEvent]:
        """Find and process all collisions in a particle list."""
        pairs = self.find_collisions(particles)
        events = []
        for p1, p2 in pairs:
            if p1.alive and p2.alive:
                events.append(self.generate_event(p1, p2))
        return events
