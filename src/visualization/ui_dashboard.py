from __future__ import annotations

from simulation.engine import SimulationResult


def dashboard_metrics(result: SimulationResult) -> dict[str, float]:
    return {
        "collision_count": float(len(result.collisions)),
        "tracker_hit_count": float(len(result.tracker_hits)),
        "calorimeter_hit_count": float(len(result.calorimeter_hits)),
        "active_particle_count": float(sum(1 for particle in result.final_particles if particle.alive)),
    }
