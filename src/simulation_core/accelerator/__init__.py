"""
accelerator — Beamline hardware simulation.

Subsystem responsibilities:
  • Beam source: generate initial particle bunches
  • Dipole magnet: uniform Bz field for bending
  • Quadrupole magnet: gradient field for focusing
  • RF cavity: electric field for energy boost
  • Vacuum chamber: aperture / acceptance boundary
  • Beam dynamics: advance particles through the full lattice
"""

from __future__ import annotations

import math
import random
from typing import List, Optional, Callable, Tuple

import numpy as np

from src.simulation_core.core_models.models import (
    ParticleState,
    BeamParameters,
    Vec3,
    PARTICLE_PROPERTIES,
    C,
    GEV_TO_J,
)
from src.simulation_core.physics_engine import (
    make_particle,
    ElectromagneticField,
    propagate_step,
    boris_push,
    speed_from_momentum_gev,
    velocity_vector_ms,
)


# ─────────────────────────────────────────────────────────────────────────────
# beam_source.py — Generate initial particle beams
# ─────────────────────────────────────────────────────────────────────────────

class BeamSource:
    """
    Generates a Gaussian beam bunch with configurable energy and emittance.

    Produces two counter-propagating bunches (beam A: +z, beam B: −z)
    for head-on collisions.
    """

    def __init__(self, params: BeamParameters):
        self.params = params
        self._rng = random.Random(params.seed)

    def _momentum_for_particle(self, species: str, energy_gev: float, direction: Vec3) -> Vec3:
        """Compute momentum vector for given kinetic energy and direction."""
        props = PARTICLE_PROPERTIES.get(species, {"mass_gev": 0.938272})
        m = props["mass_gev"]
        # Total energy = KE + m
        E_total = energy_gev + m
        p_mag = math.sqrt(max(0.0, E_total**2 - m**2))  # GeV/c
        dx, dy, dz = direction
        norm = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
        return (p_mag * dx / norm, p_mag * dy / norm, p_mag * dz / norm)

    def _sample_transverse_offset(self) -> Tuple[float, float]:
        """Sample a (y, z) transverse position from a Gaussian distribution."""
        sigma = self.params.bunch_spread_m
        dy = self._rng.gauss(0.0, sigma)
        dz = self._rng.gauss(0.0, sigma * 0.3)
        return dy, dz

    def _sample_longitudinal_offset(self, index: int) -> float:
        """Longitudinal (x) offset for the i-th particle in the bunch."""
        n = self.params.n_particles
        spacing = self.params.longitudinal_spread_m / max(n - 1, 1)
        center_offset = (index - (n - 1) / 2.0) * spacing
        jitter = self._rng.gauss(0.0, spacing * 0.1)
        return center_offset + jitter

    def emit_beam(self, base_x: float = 0.04) -> List[ParticleState]:
        """
        Emit counter-propagating beam bunches.

        Args:
            base_x: longitudinal separation from IP (metres)

        Returns:
            List of particles — beam A (+x direction) and beam B (−x direction).
        """
        particles = []
        for beam_sign, direction in [(-1, (1.0, 0.0, 0.0)), (1, (-1.0, 0.0, 0.0))]:
            for i in range(self.params.n_particles):
                long_offset = self._sample_longitudinal_offset(i)
                dy, dz = self._sample_transverse_offset()
                x = base_x * beam_sign + long_offset * beam_sign
                pos: Vec3 = (x, dy, dz)
                mom = self._momentum_for_particle(
                    self.params.species, self.params.energy_gev, direction
                )
                p = make_particle(self.params.species, pos, mom, generation=0)
                particles.append(p)
        return particles


# ─────────────────────────────────────────────────────────────────────────────
# dipole_magnet.py — uniform B_z bending magnet
# ─────────────────────────────────────────────────────────────────────────────

class DipoleMagnet:
    """
    Uniform dipole magnet: B = B_z ẑ (constant, no spatial variation).

    Bending radius ρ = p / (|q|B).
    Used for beam steering in the synchrotron ring.
    """

    def __init__(self, field_t: float = 3.8, length_m: float = 14.3, aperture_m: float = 0.028):
        self.field_t = field_t        # Tesla (LHC dipole ≈ 8.33 T)
        self.length_m = length_m      # Effective magnetic length
        self.aperture_m = aperture_m  # Half-aperture

    def field_at(self, position: Vec3) -> Tuple[np.ndarray, np.ndarray]:
        """Return (E=0, B=B_z ẑ) at any position."""
        return np.zeros(3), np.array([0.0, 0.0, self.field_t])

    def bending_radius_m(self, p_gev: float, charge_e: float) -> float:
        """ρ = p / (|q|B) where p in GeV/c, converted to SI."""
        e = 1.602_176_634e-19
        p_si = p_gev * GEV_TO_J / C
        q_b = abs(charge_e) * e * self.field_t
        return p_si / q_b if q_b > 0 else float("inf")

    def bending_angle_rad(self, p_gev: float, charge_e: float) -> float:
        """θ = L / ρ in radians."""
        rho = self.bending_radius_m(p_gev, charge_e)
        return self.length_m / rho if not math.isinf(rho) else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# quadrupole_magnet.py — linear gradient focusing
# ─────────────────────────────────────────────────────────────────────────────

class QuadrupoleMagnet:
    """
    Quadrupole magnet: B = G·(y x̂ + x ŷ), focusing in one plane, defocusing in the other.
    G = dB/dr is the field gradient in T/m.
    """

    def __init__(self, gradient_t_per_m: float = 0.08, length_m: float = 3.1, bore_r_m: float = 0.028):
        self.gradient = gradient_t_per_m
        self.length_m = length_m
        self.bore_r_m = bore_r_m

    def field_at(self, position: Vec3) -> Tuple[np.ndarray, np.ndarray]:
        """B = G·y x̂ + G·x ŷ (linear gradient field)."""
        x, y, z = position
        return np.zeros(3), np.array([self.gradient * y, self.gradient * x, 0.0])

    def focal_length_m(self, p_gev: float, charge_e: float) -> float:
        """Thin-lens focal length f = p / (|q|·G·L)."""
        e = 1.602_176_634e-19
        p_si = p_gev * GEV_TO_J / C
        qgl = abs(charge_e) * e * self.gradient * self.length_m
        return p_si / qgl if qgl > 0 else float("inf")


# ─────────────────────────────────────────────────────────────────────────────
# rf_cavity.py — RF acceleration cavity
# ─────────────────────────────────────────────────────────────────────────────

class RFCavity:
    """
    Radiofrequency accelerating cavity. Provides a longitudinal electric field
    E_y = V_peak / gap × cos(ω_RF·t + φ_s) inside the cavity gap.

    Used for energy ramping and longitudinal focusing (synchrotron oscillations).
    """

    def __init__(
        self,
        center: Vec3 = (0.0, 0.0, 0.0),
        half_gap_m: float = 0.15,
        peak_voltage_v: float = 2.0e6,
        frequency_hz: float = 400.789e6,
        sync_phase_rad: float = 0.0,
    ):
        self.center = np.array(center)
        self.half_gap_m = half_gap_m
        self.peak_voltage_v = peak_voltage_v
        self.frequency_hz = frequency_hz
        self.sync_phase_rad = sync_phase_rad
        self._omega = 2.0 * math.pi * frequency_hz

    def field_at(self, position: Vec3, time_s: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (E, B=0) at a given position and time.
        E is along ŷ inside the cavity gap.
        """
        pos = np.array(position)
        delta = pos - self.center
        if abs(delta[0]) > self.half_gap_m or abs(delta[1]) > self.half_gap_m:
            return np.zeros(3), np.zeros(3)

        gap = 2.0 * self.half_gap_m
        e_peak = self.peak_voltage_v / gap
        phase = self._omega * time_s + self.sync_phase_rad
        e_y = e_peak * math.cos(phase)
        return np.array([0.0, e_y, 0.0]), np.zeros(3)

    def energy_gain_per_pass_gev(self) -> float:
        """Maximum energy gain per cavity traversal: ΔE = q·V·cos(φ_s) in GeV."""
        e = 1.602_176_634e-19
        return self.peak_voltage_v * math.cos(self.sync_phase_rad) * e / GEV_TO_J


# ─────────────────────────────────────────────────────────────────────────────
# vacuum_chamber.py — beam pipe acceptance boundary
# ─────────────────────────────────────────────────────────────────────────────

class VacuumChamber:
    """
    Cylindrical vacuum beam pipe. Particles outside the aperture are lost.
    """

    def __init__(self, aperture_r_m: float = 1.5, half_length_m: float = 10.0):
        self.aperture_r_m = aperture_r_m
        self.half_length_m = half_length_m

    def contains(self, position: Vec3) -> bool:
        """Return True if position is inside the beam pipe."""
        x, y, z = position
        r_transverse = math.sqrt(x*x + y*y)
        return r_transverse <= self.aperture_r_m and abs(z) <= self.half_length_m

    def distance_to_wall_m(self, position: Vec3) -> float:
        """Transverse distance from current position to the aperture wall."""
        x, y, _ = position
        r = math.sqrt(x*x + y*y)
        return max(0.0, self.aperture_r_m - r)


# ─────────────────────────────────────────────────────────────────────────────
# beam_dynamics.py — thread the lattice; advance beams to the IP
# ─────────────────────────────────────────────────────────────────────────────

class AcceleratorLattice:
    """
    Simplified linear accelerator lattice.

    Elements are applied in sequence via their field_at() methods.
    The combined field is fed into the Boris-push integrator to advance
    each particle from injection to the interaction point (IP).
    """

    def __init__(
        self,
        dipole: DipoleMagnet = None,
        quadrupole: QuadrupoleMagnet = None,
        rf_cavity: RFCavity = None,
        vacuum: VacuumChamber = None,
    ):
        self.dipole = dipole or DipoleMagnet()
        self.quadrupole = quadrupole or QuadrupoleMagnet()
        self.rf_cavity = rf_cavity or RFCavity()
        self.vacuum = vacuum or VacuumChamber()

    def field_at(self, position: Vec3, time_s: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
        """Sum of all lattice element fields at a given position and time."""
        E_total = np.zeros(3)
        B_total = np.zeros(3)

        E, B = self.dipole.field_at(position)
        E_total += E; B_total += B

        E, B = self.quadrupole.field_at(position)
        E_total += E; B_total += B

        E, B = self.rf_cavity.field_at(position, time_s)
        E_total += E; B_total += B

        return E_total, B_total

    def as_em_field(self) -> ElectromagneticField:
        """Wrap this lattice as an ElectromagneticField for the physics engine."""
        field = ElectromagneticField()
        field.add_source(lambda pos: self.field_at(pos))
        return field


class BeamDynamics:
    """
    Advance a beam bunch through the accelerator lattice to the IP.
    Returns particles at the interaction point, ready for collision detection.
    """

    def __init__(
        self,
        lattice: AcceleratorLattice = None,
        dt_s: float = 1.0e-11,
        max_steps: int = 500,
    ):
        self.lattice = lattice or AcceleratorLattice()
        self.dt_s = dt_s
        self.max_steps = max_steps
        self._em_field = self.lattice.as_em_field()

    def transport_to_ip(self, particles: List[ParticleState]) -> List[ParticleState]:
        """
        Advance all particles through the lattice until they reach the IP (z≈0)
        or are lost on the aperture.

        Returns:
            List of particles at (or near) z=0 in the accelerated state.
        """
        active = list(particles)

        def aperture_ok(pos: Vec3) -> bool:
            return self.lattice.vacuum.contains(pos)

        for step in range(self.max_steps):
            time_s = step * self.dt_s
            # Temporarily add time dependency to RF field
            em_t = ElectromagneticField()
            em_t.add_source(lambda pos, t=time_s: self.lattice.field_at(pos, t))

            active = propagate_step(active, em_t, self.dt_s, aperture_check=aperture_ok)

            # Check convergence: all alive particles near IP
            alive = [p for p in active if p.alive]
            if not alive:
                break
            # Stop when all alive particles are near the IP (|x| < 5 mm)
            if all(abs(p.position[0]) < 0.005 for p in alive):
                break

        return active

    def run_n_turns(self, particles: List[ParticleState], n_turns: int) -> List[ParticleState]:
        """
        Advance particles for n_turns full revolution cycles.
        Used for emittance growth and loss studies.
        """
        active = list(particles)
        for _ in range(n_turns * self.max_steps):
            active = propagate_step(
                active,
                self._em_field,
                self.dt_s,
                aperture_check=self.lattice.vacuum.contains,
            )
        return active
