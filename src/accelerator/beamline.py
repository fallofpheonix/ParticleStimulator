from __future__ import annotations

from dataclasses import dataclass, field

from src.accelerator.magnets import DipoleMagnet, QuadrupoleMagnet
from src.accelerator.rf_cavity import RFCavity
from src.accelerator.vacuum_chamber import VacuumChamber
from src.core.vector import Vector3


@dataclass(slots=True)
class Beamline:
    dipole: DipoleMagnet = field(default_factory=lambda: DipoleMagnet(3.5))
    quadrupole: QuadrupoleMagnet = field(default_factory=lambda: QuadrupoleMagnet(0.08))
    rf_cavity: RFCavity = field(
        default_factory=lambda: RFCavity(center=Vector3(0.0, 0.0, 0.0), half_width_m=0.15, electric_field_v_m=1.5e5)
    )
    vacuum_chamber: VacuumChamber = field(default_factory=lambda: VacuumChamber(aperture_radius_m=1.5, half_length_m=2.0))
    interaction_radius_m: float = 0.06

    def electric_field_at(self, position: Vector3) -> Vector3:
        return self.rf_cavity.field_at(position)

    def magnetic_field_at(self, position: Vector3) -> Vector3:
        return self.dipole.field_at(position) + self.quadrupole.field_at(position)

    def contains(self, position: Vector3) -> bool:
        return self.vacuum_chamber.contains(position)
