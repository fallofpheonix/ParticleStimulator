"""Synchrotron ring — circular accelerator model.

Represents the full accelerator ring as a sequence of lattice elements
(dipoles, quadrupoles, sextupoles, RF cavities) with circumference and
revolution frequency calculations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from backend.accelerator.dipole_magnet import DipoleMagnet
from backend.accelerator.quadrupole_magnet import QuadrupoleMagnet
from backend.accelerator.rf_cavity import RFCavity
from backend.accelerator.vacuum_chamber import VacuumChamber
from backend.core_math.constants import SPEED_OF_LIGHT
from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle


@dataclass(slots=True)
class SynchrotronRing:
    """Model of a circular synchrotron accelerator.

    Attributes:
        circumference_m: ring circumference in metres (LHC ≈ 26659 m).
        dipole: bending magnet model.
        quadrupole: focusing magnet model.
        rf_cavity: accelerating cavity.
        vacuum: beam pipe.
        num_dipoles: number of dipoles in the ring.
        num_quadrupoles: number of quadrupoles in the ring.
    """

    circumference_m: float = 26_659.0
    dipole: DipoleMagnet = field(default_factory=DipoleMagnet)
    quadrupole: QuadrupoleMagnet = field(default_factory=QuadrupoleMagnet)
    rf_cavity: RFCavity = field(default_factory=RFCavity)
    vacuum: VacuumChamber = field(default_factory=VacuumChamber)
    num_dipoles: int = 1232
    num_quadrupoles: int = 392

    def revolution_frequency(self, beta: float) -> float:
        """f_rev = βc / C  (Hz)."""
        return beta * SPEED_OF_LIGHT / self.circumference_m

    def revolution_period(self, beta: float) -> float:
        """T_rev = C / (βc)  (seconds)."""
        f = self.revolution_frequency(beta)
        return 1.0 / f if f > 0.0 else float("inf")

    def electric_field_at(self, position: Vector3, time_s: float = 0.0) -> Vector3:
        """Total E-field from RF cavities at this position."""
        return self.rf_cavity.field_at(position, time_s)

    def magnetic_field_at(self, position: Vector3) -> Vector3:
        """Total B-field from dipoles + quadrupoles."""
        return self.dipole.field_at(position) + self.quadrupole.field_at(position)

    def contains(self, position: Vector3) -> bool:
        return self.vacuum.contains(position)
