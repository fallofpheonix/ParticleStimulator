"""Beam packet — represents a structured bunch of particles.

A beam packet groups particles with shared metadata (bunch ID, timestamp,
aggregate properties) for tracking through the accelerator lattice.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle


@dataclass(slots=True)
class BeamPacket:
    """A bunch of particles travelling together.

    Attributes:
        bunch_id: unique identifier for this bunch.
        particles: list of particles in this bunch.
        timestamp_s: creation time of the bunch.
    """

    bunch_id: int = 0
    particles: list[Particle] = field(default_factory=list)
    timestamp_s: float = 0.0

    @property
    def size(self) -> int:
        return len(self.particles)

    @property
    def alive_count(self) -> int:
        return sum(1 for p in self.particles if p.alive)

    def centroid(self) -> Vector3:
        """Mean position of alive particles."""
        alive = [p for p in self.particles if p.alive]
        if not alive:
            return Vector3()
        sx = sum(p.position.x for p in alive)
        sy = sum(p.position.y for p in alive)
        sz = sum(p.position.z for p in alive)
        n = len(alive)
        return Vector3(sx / n, sy / n, sz / n)

    def rms_spread(self) -> float:
        """RMS transverse spread of alive particles."""
        alive = [p for p in self.particles if p.alive]
        if len(alive) < 2:
            return 0.0
        c = self.centroid()
        var = sum((p.position - c).magnitude_squared() for p in alive) / len(alive)
        return math.sqrt(var)

    def mean_energy_j(self) -> float:
        """Mean kinetic energy of alive particles (Joules)."""
        alive = [p for p in self.particles if p.alive]
        if not alive:
            return 0.0
        from backend.physics_engine.relativistic_dynamics import kinetic_energy
        return sum(kinetic_energy(p.mass_kg or 0.0, p.speed()) for p in alive) / len(alive)
