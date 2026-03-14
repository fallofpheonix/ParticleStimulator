"""Muon detector — outermost detector layer for muon identification."""

from __future__ import annotations
from dataclasses import dataclass
from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle

MUON_SPECIES = {"muon-", "muon+"}


@dataclass(frozen=True, slots=True)
class MuonHit:
    particle_id: int
    position: Vector3
    momentum_magnitude: float
    time_s: float
    species: str = ""


@dataclass(slots=True)
class MuonDetector:
    """Muon chamber system outside the hadronic calorimeter."""
    inner_radius_m: float = 0.45
    outer_radius_m: float = 1.0
    z_extent_m: float = 6.0

    def detect(self, particle: Particle, time_s: float, seen: set[int]) -> list[MuonHit]:
        if not particle.alive or particle.species not in MUON_SPECIES:
            return []
        if particle.particle_id in seen:
            return []
        r = particle.position.radial_xy()
        if r < self.inner_radius_m or r > self.outer_radius_m:
            return []
        if abs(particle.position.z) > self.z_extent_m:
            return []
        seen.add(particle.particle_id)
        p_mag = particle.velocity.magnitude() * (particle.mass_kg or 0)
        return [MuonHit(particle.particle_id, particle.position, p_mag, time_s, particle.species)]

    def simulate(self, particles: list[Particle], time_s: float) -> list[MuonHit]:
        seen: set[int] = set()
        return [h for p in particles for h in self.detect(p, time_s, seen)]
