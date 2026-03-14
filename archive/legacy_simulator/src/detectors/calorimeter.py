from __future__ import annotations

from dataclasses import dataclass
import math

from src.core.constants import GEV_TO_J
from src.core.particle import Particle


@dataclass(frozen=True, slots=True)
class EnergyDeposit:
    particle_id: int
    phi_bin: int
    deposited_energy_gev: float
    time_s: float


@dataclass(slots=True)
class Calorimeter:
    inner_radius_m: float = 0.012
    phi_bins: int = 16

    def deposit(self, particle: Particle, time_s: float, deposited_ids: set[int]) -> list[EnergyDeposit]:
        if not particle.alive:
            return []
        if particle.particle_id in deposited_ids:
            return []
        if particle.position.radial_xy() < self.inner_radius_m:
            return []

        deposited_ids.add(particle.particle_id)
        phi = particle.position.phi()
        normalized = (phi + math.pi) / (2.0 * math.pi)
        phi_bin = min(self.phi_bins - 1, int(normalized * self.phi_bins))
        return [EnergyDeposit(particle.particle_id, phi_bin, particle.kinetic_energy_j() / GEV_TO_J, time_s)]
