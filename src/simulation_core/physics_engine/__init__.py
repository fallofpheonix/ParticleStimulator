"""
physics_engine — Relativistic particle dynamics kernel.

Subsystem responsibilities:
  • Relativistic kinematics (γ, β, E, p conversions)
  • Lorentz force computation:  F = q(E + v × B)
  • Boris push integrator (symplectic, 2nd-order, preserves magnetic moment)
  • Timestep-by-timestep simulation kernel

All functions are pure and stateless.
Input/output: ParticleState objects from core_models.
"""

from __future__ import annotations

import math
import itertools
from typing import List, Tuple, Callable

import numpy as np

from simulation_core.core_models.models import (
    ParticleState,
    FieldPoint,
    Vec3,
    PARTICLE_PROPERTIES,
    C,
    GEV_TO_J,
)

# Particle ID counter (module-level for thread-safety via itertools)
_pid_counter = itertools.count(1)


def new_particle_id() -> int:
    return next(_pid_counter)


def make_particle(
    species: str,
    position: Vec3,
    momentum_gev: Vec3,
    parent_id: int = None,
    generation: int = 0,
) -> ParticleState:
    """Factory: create a ParticleState from species name and kinematics."""
    props = PARTICLE_PROPERTIES.get(species, {"mass_gev": 0.0, "charge": 0})
    return ParticleState(
        id=new_particle_id(),
        species=species,
        position=position,
        momentum=momentum_gev,
        mass_gev=props["mass_gev"],
        charge=float(props["charge"]),
        alive=True,
        parent_id=parent_id,
        generation=generation,
    )


# ─────────────────────────────────────────────────────────────────────────────
# relativistic_kinematics.py
# ─────────────────────────────────────────────────────────────────────────────

def gamma_factor(p_mag_gev: float, mass_gev: float) -> float:
    """Lorentz factor γ = E / mc² = √(1 + (p/mc)²)."""
    if mass_gev == 0.0:
        return float("inf")
    return math.sqrt(1.0 + (p_mag_gev / mass_gev) ** 2)


def beta_from_gamma(gamma: float) -> float:
    """β = v/c = √(1 − 1/γ²)."""
    if math.isinf(gamma):
        return 1.0
    return math.sqrt(max(0.0, 1.0 - 1.0 / (gamma * gamma)))


def momentum_from_energy_and_mass(energy_gev: float, mass_gev: float) -> float:
    """|p| = √(E² − m²) in GeV/c."""
    return math.sqrt(max(0.0, energy_gev**2 - mass_gev**2))


def speed_from_momentum_gev(p_mag_gev: float, mass_gev: float) -> float:
    """Speed in m/s from |p| in GeV/c and mass in GeV/c²."""
    energy = math.sqrt(p_mag_gev**2 + mass_gev**2)
    if energy == 0.0:
        return 0.0
    return C * p_mag_gev / energy


def velocity_vector_ms(particle: ParticleState) -> np.ndarray:
    """3-velocity vector in m/s as a numpy array."""
    p = np.array(particle.momentum, dtype=np.float64)
    p_mag = float(np.linalg.norm(p))
    if p_mag == 0.0:
        return np.zeros(3)
    spd = speed_from_momentum_gev(p_mag, particle.mass_gev)
    return p * (spd / p_mag)


def four_momentum(particle: ParticleState) -> np.ndarray:
    """Returns [E, px, py, pz] in GeV."""
    return np.array([particle.energy_gev, *particle.momentum], dtype=np.float64)


def invariant_mass_pair(p1: ParticleState, p2: ParticleState) -> float:
    """Invariant mass m_inv = √((p1+p2)²) in GeV."""
    e_sum = p1.energy_gev + p2.energy_gev
    px = p1.momentum[0] + p2.momentum[0]
    py = p1.momentum[1] + p2.momentum[1]
    pz = p1.momentum[2] + p2.momentum[2]
    m2 = e_sum**2 - px**2 - py**2 - pz**2
    return math.sqrt(max(0.0, m2))


def sqrt_s(p1: ParticleState, p2: ParticleState) -> float:
    """Centre-of-mass energy √s for a particle pair in GeV."""
    return invariant_mass_pair(p1, p2)


# ─────────────────────────────────────────────────────────────────────────────
# lorentz_force.py
# ─────────────────────────────────────────────────────────────────────────────

def lorentz_force_si(
    charge_e: float,
    velocity_ms: np.ndarray,
    E_field_vm: np.ndarray,
    B_field_T: np.ndarray,
) -> np.ndarray:
    """
    Lorentz force in Newtons (SI):
        F = q × (E + v × B)

    Args:
        charge_e: particle charge in units of elementary charge e
        velocity_ms: velocity vector in m/s
        E_field_vm: electric field in V/m
        B_field_T: magnetic field in Tesla

    Returns:
        Force vector in Newtons
    """
    e = 1.602_176_634e-19  # C
    q = charge_e * e
    return q * (E_field_vm + np.cross(velocity_ms, B_field_T))


def cyclotron_radius_m(p_transverse_gev: float, charge_e: float, B_T: float) -> float:
    """Larmor radius r = p_⊥ / (|q|B) in metres."""
    e = 1.602_176_634e-19
    q_mag = abs(charge_e) * e
    p_si = p_transverse_gev * GEV_TO_J / C  # kg·m/s
    if q_mag * B_T == 0.0:
        return float("inf")
    return p_si / (q_mag * B_T)


# ─────────────────────────────────────────────────────────────────────────────
# motion_integrator.py — Boris push algorithm
# ─────────────────────────────────────────────────────────────────────────────

def boris_push(
    particle: ParticleState,
    E_field_vm: np.ndarray,
    B_field_T: np.ndarray,
    dt_s: float,
) -> ParticleState:
    """
    Boris push — the gold-standard symplectic integrator for charged particles
    in electromagnetic fields. Preserves the magnetic moment and avoids
    artificial energy gain/loss from the magnetic field.

    Algorithm (relativistic):
      1. Half-step E kick:   u⁻ = u + (qE·Δt)/(2m)
      2. Magnetic rotation:  u⁺ via t-vector and s-vector
      3. Half-step E kick:   u_new = u⁺ + (qE·Δt)/(2m)
      4. Position advance:   x_new = x + v·Δt

    All internal computation in SI units; output is converted back to GeV.

    Args:
        particle: current ParticleState
        E_field_vm: electric field in V/m (numpy array, shape (3,))
        B_field_T: magnetic field in T (numpy array, shape (3,))
        dt_s: timestep in seconds

    Returns:
        Updated ParticleState
    """
    if not particle.alive or particle.mass_gev == 0.0:
        return particle

    e = 1.602_176_634e-19   # C
    q = particle.charge * e  # Coulombs
    m_kg = particle.mass_gev * GEV_TO_J / (C * C)  # kg

    # Convert momentum from GeV/c to SI (kg·m/s) via γmv = p[SI]
    # p[SI] = p[GeV/c] × (e/c × 1e9)
    gev_c_to_si = GEV_TO_J / C
    p_si = np.array(particle.momentum, dtype=np.float64) * gev_c_to_si
    x = np.array(particle.position, dtype=np.float64)

    # γ from |p_SI|: γ = √(1 + (|p_SI|/(mc))²)
    p_mag_si = float(np.linalg.norm(p_si))
    mc = m_kg * C
    gamma = math.sqrt(1.0 + (p_mag_si / mc) ** 2)

    # Boris uses u = γv (momentum per unit mass in m/s)
    u = p_si / m_kg

    # Half-step electric impulse
    half_impulse = q * E_field_vm * dt_s / (2.0 * m_kg)
    u_minus = u + half_impulse

    # Magnetic rotation
    gamma_minus = math.sqrt(1.0 + float(np.dot(u_minus, u_minus)) / (C * C))
    t_vec = q * B_field_T * dt_s / (2.0 * m_kg * gamma_minus)
    s_vec = 2.0 * t_vec / (1.0 + float(np.dot(t_vec, t_vec)))
    u_prime = u_minus + np.cross(u_minus, t_vec)
    u_plus = u_minus + np.cross(u_prime, s_vec)

    # Second half-step electric impulse
    u_new = u_plus + half_impulse

    # Convert u_new back to SI momentum then to GeV/c
    gamma_new = math.sqrt(1.0 + float(np.dot(u_new, u_new)) / (C * C))
    p_new_si = m_kg * u_new
    p_new_gev = tuple(float(v) / gev_c_to_si for v in p_new_si)

    # Velocity for position advance: v = u / γ
    v_new = u_new / gamma_new
    x_new = x + v_new * dt_s
    pos_new = tuple(float(v) for v in x_new)

    return ParticleState(
        id=particle.id,
        species=particle.species,
        position=pos_new,
        momentum=p_new_gev,
        mass_gev=particle.mass_gev,
        charge=particle.charge,
        alive=particle.alive,
        parent_id=particle.parent_id,
        generation=particle.generation,
    )


# ─────────────────────────────────────────────────────────────────────────────
# electromagnetic_field.py — composite field evaluation
# ─────────────────────────────────────────────────────────────────────────────

class ElectromagneticField:
    """
    Composite electromagnetic field that sums contributions from multiple
    field sources. Used by the simulation kernel.

    Each source is a callable: position (Vec3) → (E: np.ndarray, B: np.ndarray)
    """

    def __init__(self):
        self._sources: List[Callable[[Vec3], Tuple[np.ndarray, np.ndarray]]] = []

    def add_source(self, source: Callable[[Vec3], Tuple[np.ndarray, np.ndarray]]):
        """Register a field source function."""
        self._sources.append(source)
        return self

    def evaluate(self, position: Vec3) -> Tuple[np.ndarray, np.ndarray]:
        """Return total (E, B) at a given position."""
        E_total = np.zeros(3)
        B_total = np.zeros(3)
        for src in self._sources:
            E, B = src(position)
            E_total += E
            B_total += B
        return E_total, B_total

    def uniform_magnetic(self, B_vec: Vec3) -> "ElectromagneticField":
        """Convenience: add a spatially uniform magnetic field."""
        B_arr = np.array(B_vec, dtype=np.float64)
        self.add_source(lambda pos: (np.zeros(3), B_arr.copy()))
        return self

    def uniform_electric(self, E_vec: Vec3) -> "ElectromagneticField":
        """Convenience: add a spatially uniform electric field."""
        E_arr = np.array(E_vec, dtype=np.float64)
        self.add_source(lambda pos: (E_arr.copy(), np.zeros(3)))
        return self


# ─────────────────────────────────────────────────────────────────────────────
# simulation_kernel.py — single-step and multi-step propagation
# ─────────────────────────────────────────────────────────────────────────────

def propagate_step(
    particles: List[ParticleState],
    field: ElectromagneticField,
    dt_s: float,
    aperture_check: Callable[[Vec3], bool] = None,
) -> List[ParticleState]:
    """
    Advance all alive particles by one timestep using the Boris push.

    Args:
        particles: list of current particle states
        field: composite electromagnetic field
        dt_s: timestep in seconds
        aperture_check: callable(position) → True if inside acceptance.
                        Particles outside are killed.

    Returns:
        Updated list of ParticleState objects.
    """
    updated = []
    for p in particles:
        if not p.alive:
            updated.append(p)
            continue

        E, B = field.evaluate(p.position)
        p_new = boris_push(p, E, B, dt_s)

        # Aperture / boundary check
        if aperture_check is not None and not aperture_check(p_new.position):
            updated.append(p_new.killed())
        else:
            updated.append(p_new)

    return updated


def propagate_to_z(
    particle: ParticleState,
    target_z: float,
    field: ElectromagneticField,
    dt_s: float = 1e-12,
    max_steps: int = 10_000,
) -> ParticleState:
    """
    Propagate a single particle until it reaches target_z (metres),
    stepping with the Boris push.
    """
    p = particle
    for _ in range(max_steps):
        if not p.alive:
            break
        z = p.position[2]
        if (particle.momentum[2] > 0 and z >= target_z) or \
           (particle.momentum[2] < 0 and z <= target_z):
            break
        E, B = field.evaluate(p.position)
        p = boris_push(p, E, B, dt_s)
    return p


def adaptive_timestep(particle: ParticleState, base_dt_s: float, cfl_factor: float = 0.3) -> float:
    """
    CFL-style adaptive timestep: Δt = cfl_factor × Δx_min / v
    where Δx_min is a minimum spatial scale (1 mm default).
    """
    speed = speed_from_momentum_gev(particle.p_mag, particle.mass_gev)
    if speed <= 0.0:
        return base_dt_s
    dx_min = 1.0e-3  # 1 mm
    dt_cfl = cfl_factor * dx_min / speed
    return min(base_dt_s, dt_cfl)
