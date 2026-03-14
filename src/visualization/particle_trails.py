from __future__ import annotations

from src.core.particle import Particle


def summarize_particles(particles: list[Particle]) -> list[dict[str, object]]:
    return [
        {
            "particle_id": particle.particle_id,
            "species": particle.species,
            "alive": particle.alive,
            "position": particle.position.as_tuple(),
            "velocity": particle.velocity.as_tuple(),
        }
        for particle in particles
    ]
