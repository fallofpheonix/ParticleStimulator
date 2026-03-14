"""Electromagnetic calorimeter — energy measurement for electrons and photons.

Models EM shower sampling where electrons and photons deposit their full
energy in the calorimeter through electromagnetic cascades.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from backend.core_math.constants import GEV_TO_JOULE
from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle


EM_SPECIES = {"electron", "positron", "photon"}


@dataclass(frozen=True, slots=True)
class EMDeposit:
    """Energy deposit in the EM calorimeter."""
    particle_id: int
    eta_bin: int
    phi_bin: int
    energy_gev: float
    time_s: float
    species: str = ""


@dataclass(slots=True)
class EMCalorimeter:
    """Electromagnetic calorimeter with η-φ segmentation.

    Attributes:
        inner_radius_m: inner boundary.
        outer_radius_m: outer boundary.
        n_eta_bins: segmentation in pseudorapidity.
        n_phi_bins: segmentation in azimuth.
        energy_resolution: σ_E/E = resolution/√E (stochastic term).
    """

    inner_radius_m: float = 0.13
    outer_radius_m: float = 0.20
    n_eta_bins: int = 50
    n_phi_bins: int = 64
    energy_resolution: float = 0.10

    def deposit(self, particle: Particle, time_s: float, deposited_ids: set[int]) -> list[EMDeposit]:
        """Record energy deposit for EM-interacting particles."""
        if not particle.alive or particle.particle_id in deposited_ids:
            return []
        if particle.species not in EM_SPECIES:
            return []
        r = particle.position.radial_xy()
        if r < self.inner_radius_m or r > self.outer_radius_m:
            return []

        deposited_ids.add(particle.particle_id)

        # Compute η and φ bins
        phi = particle.position.phi()
        phi_norm = (phi + math.pi) / (2.0 * math.pi)
        phi_bin = min(self.n_phi_bins - 1, int(phi_norm * self.n_phi_bins))

        eta = particle.position.eta()
        eta_norm = (eta + 5.0) / 10.0  # map η ∈ [-5,5] → [0,1]
        eta_norm = max(0.0, min(1.0, eta_norm))
        eta_bin = min(self.n_eta_bins - 1, int(eta_norm * self.n_eta_bins))

        from backend.physics_engine.relativistic_dynamics import kinetic_energy
        ke = kinetic_energy(particle.mass_kg or 0, particle.speed())
        energy_gev = ke / GEV_TO_JOULE

        return [EMDeposit(particle.particle_id, eta_bin, phi_bin, energy_gev, time_s, particle.species)]

    def simulate(self, particles: list[Particle], time_s: float) -> list[EMDeposit]:
        deposited: set[int] = set()
        all_deps: list[EMDeposit] = []
        for p in particles:
            all_deps.extend(self.deposit(p, time_s, deposited))
        return all_deps
