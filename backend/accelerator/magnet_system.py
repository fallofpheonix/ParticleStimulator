"""Magnet system — composite magnet lattice for the beamline.

Aggregates dipoles, quadrupoles, and sextupoles into a single lattice
that provides the total B-field at any point.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.accelerator.dipole_magnet import DipoleMagnet
from backend.accelerator.quadrupole_magnet import QuadrupoleMagnet
from backend.accelerator.sextupole_magnet import SextupoleMagnet
from backend.core_math.vector3 import Vector3


@dataclass(slots=True)
class MagnetLattice:
    """Collection of magnets forming the accelerator lattice.

    Attributes:
        dipoles: list of dipole magnets.
        quadrupoles: list of quadrupole magnets.
        sextupoles: list of sextupole magnets.
    """

    dipoles: list[DipoleMagnet] = field(default_factory=lambda: [DipoleMagnet()])
    quadrupoles: list[QuadrupoleMagnet] = field(default_factory=lambda: [QuadrupoleMagnet()])
    sextupoles: list[SextupoleMagnet] = field(default_factory=list)

    def total_field_at(self, position: Vector3) -> Vector3:
        """Sum of all magnet contributions at a position."""
        total = Vector3()
        for d in self.dipoles:
            total = total + d.field_at(position)
        for q in self.quadrupoles:
            total = total + q.field_at(position)
        for s in self.sextupoles:
            total = total + s.field_at(position)
        return total

    def add_dipole(self, magnet: DipoleMagnet) -> None:
        self.dipoles.append(magnet)

    def add_quadrupole(self, magnet: QuadrupoleMagnet) -> None:
        self.quadrupoles.append(magnet)

    def add_sextupole(self, magnet: SextupoleMagnet) -> None:
        self.sextupoles.append(magnet)
