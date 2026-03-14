from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.particle import Particle
from src.core.vector import Vector3
from src.simulation.engine import SimulationEngine
from src.visualization.renderer import render_text_report


def main() -> None:
    engine = SimulationEngine()
    # Two head-on pairs within interaction range (0.06 m) on converging paths.
    particles = [
        Particle("proton",   Vector3(-0.03, 0.0,  0.0), Vector3( 4.5e7,  0.0, 0.0)),
        Particle("proton",   Vector3( 0.03, 0.0,  0.0), Vector3(-4.5e7,  0.0, 0.0)),
        Particle("electron", Vector3(-0.02, 0.01, 0.0), Vector3( 2.0e7,  0.0, 0.0)),
        Particle("positron", Vector3( 0.02, 0.01, 0.0), Vector3(-2.0e7,  0.0, 0.0)),
    ]
    result = engine.run(particles, steps=200)
    print(render_text_report(result))
    print(
        json.dumps(
            {
                "events": len(result.collisions),
                "tracker_hits": len(result.tracker_hits),
                "calorimeter_hits": len(result.calorimeter_hits),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
