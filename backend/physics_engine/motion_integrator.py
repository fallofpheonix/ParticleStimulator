"""Motion integrators for relativistic charged particles.

Implements the **Boris push** algorithm — the gold-standard integrator for
charged particles in electromagnetic fields used in PIC codes and accelerator
simulations.  Also provides a simpler Euler-based ``advance_particle`` for
quick prototyping.

The Boris algorithm correctly preserves the magnetic moment and avoids
artificial energy gain/loss from the magnetic field.
"""

from __future__ import annotations

import math

from backend.core_math.constants import SPEED_OF_LIGHT
from backend.core_math.vector3 import Vector3
from backend.physics_engine.particle_model import Particle
from backend.physics_engine.relativistic_dynamics import gamma_factor

C = SPEED_OF_LIGHT


def boris_push(
    particle: Particle,
    electric_field: Vector3,
    magnetic_field: Vector3,
    dt: float,
) -> None:
    """Advance particle (position, velocity) by one step using Boris algorithm.

    The Boris push is a symplectic, second-order integrator that correctly
    handles the magnetic force without artificial energy change.

    Steps:
        1. Half-step E-field kick        (u⁻ = u^n + qE Δt/2m)
        2. Magnetic rotation              (u′ via t and s vectors)
        3. Half-step E-field kick        (u⁺ = u′ + qE Δt/2m)
        4. Position update               (x^{n+1} = x^n + v Δt)
    """
    if not particle.alive or particle.mass_kg is None or particle.mass_kg <= 0.0:
        return

    q = particle.charge_c or 0.0
    m = particle.mass_kg

    # Current velocity → "u" (γv) representation for relativistic Boris
    v = particle.velocity
    speed = v.magnitude()
    gamma = gamma_factor(speed)
    u = v * gamma  # u = γv

    # Half electric acceleration
    half_impulse = electric_field * (q * dt / (2.0 * m))
    u_minus = u + half_impulse

    # Magnetic rotation
    gamma_minus = math.sqrt(1.0 + u_minus.magnitude_squared() / (C * C))
    t_vec = magnetic_field * (q * dt / (2.0 * m * gamma_minus))
    u_prime = u_minus + u_minus.cross(t_vec)
    t_sq = t_vec.magnitude_squared()
    s_vec = t_vec * (2.0 / (1.0 + t_sq))
    u_plus = u_minus + u_prime.cross(s_vec)

    # Second half electric acceleration
    u_new = u_plus + half_impulse

    # Convert back to velocity: v = u / γ
    gamma_new = math.sqrt(1.0 + u_new.magnitude_squared() / (C * C))
    new_velocity = u_new / gamma_new

    # Clamp to 0.999c
    new_velocity = new_velocity.limit(0.999 * C)

    # Position update
    new_position = particle.position + new_velocity * dt

    particle.velocity = new_velocity
    particle.position = new_position
    particle.age_s += dt


def advance_particle(
    particle: Particle,
    electric_field: Vector3,
    magnetic_field: Vector3,
    dt: float,
) -> None:
    """Simple Euler-step particle advance (non-symplectic).

    For production simulations use ``boris_push`` instead.
    """
    if not particle.alive:
        return

    q = particle.charge_c or 0.0
    m = particle.mass_kg or 0.0
    if m <= 0.0:
        return

    # Force
    force = (electric_field + particle.velocity.cross(magnetic_field)) * q
    acceleration = force / m

    # Update velocity then position
    new_velocity = particle.velocity + acceleration * dt
    new_velocity = new_velocity.limit(0.995 * C)
    particle.velocity = new_velocity
    particle.position = particle.position + new_velocity * dt
    particle.age_s += dt
