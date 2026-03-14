from __future__ import annotations

import unittest

from core.particle import Particle
from core.vector import Vector3
from physics.collisions import should_collide, synthesize_collision
from simulation.engine import SimulationEngine


class CollisionTests(unittest.TestCase):
    def test_collision_trigger_requires_closing_particles(self) -> None:
        left = Particle("proton", Vector3(-0.01, 0.0, 0.0), Vector3(1.0, 0.0, 0.0))
        right = Particle("proton", Vector3(0.01, 0.0, 0.0), Vector3(-1.0, 0.0, 0.0))
        self.assertTrue(should_collide(left, right, 0.03))

    def test_synthesized_collision_generates_products(self) -> None:
        left = Particle("proton", Vector3(-0.01, 0.0, 0.0), Vector3(3.0e7, 0.0, 0.0))
        right = Particle("proton", Vector3(0.01, 0.0, 0.0), Vector3(-3.0e7, 0.0, 0.0))
        event = synthesize_collision(left, right, 1.0e-9)
        self.assertEqual(len(event.products), 4)
        self.assertFalse(left.alive)
        self.assertFalse(right.alive)

    def test_engine_produces_collision_and_detector_data(self) -> None:
        engine = SimulationEngine()
        particles = [
            Particle("proton", Vector3(-0.03, 0.0, 0.0), Vector3(4.5e7, 0.0, 0.0)),
            Particle("proton", Vector3(0.03, 0.0, 0.0), Vector3(-4.5e7, 0.0, 0.0)),
        ]
        result = engine.run(particles, steps=20)
        self.assertGreaterEqual(len(result.collisions), 1)
        self.assertGreaterEqual(len(result.calorimeter_hits), 1)


if __name__ == "__main__":
    unittest.main()
