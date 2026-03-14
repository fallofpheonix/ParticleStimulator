"""Lorentz force computation.

The Lorentz force governs charged-particle motion in electromagnetic fields:

    F⃗ = q(E⃗ + v⃗ × B⃗)

This module provides vectorized 3D force and acceleration functions used
by the motion integrator.
"""

from __future__ import annotations

from backend.core_math.vector3 import Vector3


def lorentz_force_3d(
    charge: float,
    velocity: Vector3,
    electric_field: Vector3,
    magnetic_field: Vector3,
) -> Vector3:
    """Compute the Lorentz force F⃗ = q(E⃗ + v⃗ × B⃗).

    Args:
        charge: particle charge in Coulombs.
        velocity: particle velocity in m/s.
        electric_field: E-field at particle position in V/m.
        magnetic_field: B-field at particle position in Tesla.

    Returns:
        Force vector in Newtons.
    """
    if charge == 0.0:
        return Vector3()
    return (electric_field + velocity.cross(magnetic_field)) * charge


def lorentz_acceleration(
    charge: float,
    mass_kg: float,
    velocity: Vector3,
    electric_field: Vector3,
    magnetic_field: Vector3,
) -> Vector3:
    """Compute acceleration a⃗ = F⃗/m from the Lorentz force.

    Note: this uses the *non-relativistic* form a = F/m.  For relativistic
    particles the ``boris_push`` integrator in ``motion_integrator`` should
    be used instead (it accounts for γ implicitly).
    """
    if mass_kg <= 0.0:
        return Vector3()
    force = lorentz_force_3d(charge, velocity, electric_field, magnetic_field)
    return force / mass_kg


def magnetic_rigidity(momentum_kgms: float, charge: float) -> float:
    """Magnetic rigidity Bρ = p / |q| (Tesla·metres).

    Determines the bending radius of a charged particle in a dipole field.
    """
    if charge == 0.0:
        return float("inf")
    return abs(momentum_kgms / charge)


def cyclotron_frequency(charge: float, mass_kg: float, b_field: float) -> float:
    """Non-relativistic cyclotron frequency ω = |q|B / m (rad/s)."""
    if mass_kg <= 0.0:
        return 0.0
    return abs(charge) * abs(b_field) / mass_kg


def larmor_radius(momentum_perp: float, charge: float, b_field: float) -> float:
    """Larmor (gyro) radius r_L = p⊥ / (|q|B) in metres."""
    qb = abs(charge * b_field)
    if qb == 0.0:
        return float("inf")
    return abs(momentum_perp) / qb
