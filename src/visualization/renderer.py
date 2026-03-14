from __future__ import annotations

from simulation.engine import SimulationResult


def render_text_report(result: SimulationResult) -> str:
    return "\n".join(
        [
            "Particle Stimulator MVP Report",
            f"collisions={len(result.collisions)}",
            f"tracker_hits={len(result.tracker_hits)}",
            f"calorimeter_hits={len(result.calorimeter_hits)}",
            f"final_particles={len(result.final_particles)}",
        ]
    )
