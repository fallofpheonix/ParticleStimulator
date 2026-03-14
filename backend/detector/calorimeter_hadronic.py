"""Hadronic calorimeter — energy measurement for hadrons.

Measures energy of protons, neutrons, pions, kaons via hadronic showers.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from backend.core_math.constants import GEV_TO_JOULE
from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle

HADRONIC_SPECIES = {"proton", "antiproton", "neutron", "pi+", "pi-", "K+", "K-", "K0"}


@dataclass(frozen=True, slots=True)
class HadronicDeposit:
    """Energy deposit in the hadronic calorimeter."""
    particle_id: int
    eta_bin: int
    phi_bin: int
    energy_gev: float
    time_s: float
    species: str = ""


@dataclass(slots=True)
class HadronicCalorimeter:
    """Hadronic calorimeter with η-φ segmentation."""

    inner_radius_m: float = 0.21
    outer_radius_m: float = 0.40
    n_eta_bins: int = 25
    n_phi_bins: int = 32
    energy_resolution: float = 0.50  # σ/E ∝ 50%/√E

    def deposit(self, particle: Particle, time_s: float, deposited_ids: set[int]) -> list[HadronicDeposit]:
        if not particle.alive or particle.particle_id in deposited_ids:
            return []
        if particle.species not in HADRONIC_SPECIES:
            return []
        r = particle.position.radial_xy()
        if r < self.inner_radius_m or r > self.outer_radius_m:
            return []

        deposited_ids.add(particle.particle_id)

        phi = particle.position.phi()
        phi_bin = min(self.n_phi_bins - 1, int(((phi + math.pi) / (2.0 * math.pi)) * self.n_phi_bins))
        eta = particle.position.eta()
        eta_norm = max(0.0, min(1.0, (eta + 5.0) / 10.0))
        eta_bin = min(self.n_eta_bins - 1, int(eta_norm * self.n_eta_bins))

        from backend.physics_engine.relativistic_dynamics import kinetic_energy
        energy_gev = kinetic_energy(particle.mass_kg or 0, particle.speed()) / GEV_TO_JOULE

        return [HadronicDeposit(particle.particle_id, eta_bin, phi_bin, energy_gev, time_s, particle.species)]

    def simulate(self, particles: list[Particle], time_s: float) -> list[HadronicDeposit]:
        deposited: set[int] = set()
        return [d for p in particles for d in self.deposit(p, time_s, deposited)]
