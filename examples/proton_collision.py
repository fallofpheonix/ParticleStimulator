from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.particle import Particle
from core.vector import Vector3
from simulation.engine import SimulationEngine


def main() -> None:
    engine = SimulationEngine()
    particles = [
        Particle("proton", Vector3(-0.03, 0.0, 0.0), Vector3(4.5e7, 0.0, 0.0)),
        Particle("proton", Vector3(0.03, 0.0, 0.0), Vector3(-4.5e7, 0.0, 0.0)),
    ]
    result = engine.run(particles, steps=20)
    print(result.event_log_json)


if __name__ == "__main__":
    main()
