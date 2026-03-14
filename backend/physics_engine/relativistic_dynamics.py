"""Relativistic dynamics: Lorentz factor, momentum, energy, and kinematics.

All functions use SI units.  The speed of light is imported from
``backend.core_math.constants``.
"""

from __future__ import annotations

import math

from backend.core_math.constants import SPEED_OF_LIGHT, GEV_TO_JOULE


C = SPEED_OF_LIGHT
C2 = C * C


def gamma_factor(speed: float) -> float:
    """Lorentz factor γ = 1 / √(1 − v²/c²).

    Clamps speed to 0.999999999c to avoid singularity.
    """
    v = min(abs(speed), 0.999_999_999 * C)
    beta = v / C
    return 1.0 / math.sqrt(1.0 - beta * beta)


def beta_factor(speed: float) -> float:
    """β = v/c, clamped to [0, 1)."""
    return min(abs(speed), C) / C


def relativistic_momentum(mass_kg: float, velocity_magnitude: float) -> float:
    """Scalar relativistic momentum p = γmv."""
    g = gamma_factor(velocity_magnitude)
    return g * mass_kg * abs(velocity_magnitude)


def relativistic_energy(mass_kg: float, speed: float) -> float:
    """Total relativistic energy E = γmc²."""
    return gamma_factor(speed) * mass_kg * C2


def kinetic_energy(mass_kg: float, speed: float) -> float:
    """Kinetic energy T = (γ − 1)mc²."""
    return (gamma_factor(speed) - 1.0) * mass_kg * C2


def rest_energy(mass_kg: float) -> float:
    """Rest energy E₀ = mc²."""
    return mass_kg * C2


def invariant_mass_from_energy_momentum(energy_j: float, momentum_magnitude: float) -> float:
    """Invariant mass m = √(E² − p²c²) / c²."""
    m2c4 = energy_j * energy_j - (momentum_magnitude * C) ** 2
    if m2c4 < 0.0:
        return 0.0
    return math.sqrt(m2c4) / C2


def speed_from_kinetic_energy(mass_kg: float, kinetic_energy_gev: float) -> float:
    """Compute speed from kinetic energy T (given in GeV).

    T = (γ − 1)mc²  ⟹  γ = 1 + T/(mc²)  ⟹  β = √(1 − 1/γ²)
    """
    ke_j = kinetic_energy_gev * GEV_TO_JOULE
    mc2 = mass_kg * C2
    if mc2 <= 0.0:
        return C  # massless
    g = 1.0 + ke_j / mc2
    if g <= 1.0:
        return 0.0
    beta_sq = 1.0 - 1.0 / (g * g)
    return C * math.sqrt(max(0.0, beta_sq))


def velocity_from_momentum(momentum_magnitude: float, mass_kg: float) -> float:
    """Invert p = γmv to find v.

    v = pc / √(p² + m²c²)
    """
    if mass_kg <= 0.0:
        return C  # massless
    p = abs(momentum_magnitude)
    mc = mass_kg * C
    return p * C / math.sqrt(p * p + mc * mc)


def mandelstam_s(e1: float, e2: float, p1_mag: float, p2_mag: float, cos_angle: float) -> float:
    """Mandelstam variable s = (p1 + p2)² for two-body collision.

    s = (E1 + E2)² − |p⃗1 + p⃗2|²c²

    For head-on collisions (cos_angle = −1), this simplifies to
    s = (E1 + E2)² − (p1 − p2)²c² ≈ 4E1E2 (ultra-relativistic).
    """
    e_total = e1 + e2
    p_total_sq = p1_mag ** 2 + p2_mag ** 2 + 2.0 * p1_mag * p2_mag * cos_angle
    return e_total ** 2 - p_total_sq * C2
