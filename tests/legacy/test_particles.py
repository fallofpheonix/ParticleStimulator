from __future__ import annotations

import unittest

from src.core.constants import PARTICLE_DB
from src.core.particle import Particle
from src.core.vector import Vector3


class ParticleTests(unittest.TestCase):
    def test_particle_defaults_from_database(self) -> None:
        proton = Particle("proton", Vector3(), Vector3(1.0, 0.0, 0.0))
        self.assertEqual(proton.mass_kg, PARTICLE_DB["proton"].mass_kg)
        self.assertEqual(proton.charge_c, PARTICLE_DB["proton"].charge_c)

    def test_speed_and_momentum_are_positive(self) -> None:
        electron = Particle("electron", Vector3(), Vector3(2.0e6, 0.0, 0.0))
        self.assertGreater(electron.speed(), 0.0)
        self.assertGreater(electron.momentum().magnitude(), 0.0)


if __name__ == "__main__":
    unittest.main()
