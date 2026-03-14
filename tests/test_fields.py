from __future__ import annotations

import unittest

from core.constants import ELEMENTARY_CHARGE_C
from core.particle import Particle
from core.vector import Vector3
from physics.electromagnetism import acceleration_from_force, lorentz_force


class FieldTests(unittest.TestCase):
    def test_lorentz_force_matches_cross_product_direction(self) -> None:
        particle = Particle("proton", Vector3(), Vector3(2.0, 0.0, 0.0))
        force = lorentz_force(particle, Vector3(), Vector3(0.0, 0.0, 3.0))
        self.assertAlmostEqual(force.x, 0.0)
        self.assertAlmostEqual(force.y, -6.0 * ELEMENTARY_CHARGE_C)
        self.assertAlmostEqual(force.z, 0.0)

    def test_acceleration_uses_particle_mass(self) -> None:
        particle = Particle("electron", Vector3(), Vector3())
        acceleration = acceleration_from_force(Vector3(1.0, 0.0, 0.0), particle)
        self.assertGreater(acceleration.x, 1.0e25)


if __name__ == "__main__":
    unittest.main()
