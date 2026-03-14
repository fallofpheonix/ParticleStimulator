"""Numerical integration methods for particle motion.

Implements Euler, Velocity-Verlet, Leapfrog, and 4th-order Runge-Kutta (RK4)
integrators.  Each integrator advances ``(position, velocity)`` by one time-step
given an acceleration function ``a(position, velocity, t)``.

The ``AdaptiveTimestep`` controller adjusts Δt based on estimated force
gradients and a CFL-like stability criterion.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from backend.core_math.vector3 import Vector3

# Type alias: acceleration = f(position, velocity, time) → Vector3
AccelFunc = Callable[[Vector3, Vector3, float], Vector3]


@dataclass(slots=True)
class IntegratorState:
    """Mutable state bundle updated by integrators."""

    position: Vector3
    velocity: Vector3
    time: float = 0.0


# ---------------------------------------------------------------------------
# Euler integrator (1st order, simplest)
# ---------------------------------------------------------------------------


def euler_step(state: IntegratorState, accel: AccelFunc, dt: float) -> None:
    """Forward-Euler integration (O(Δt) local error)."""
    a = accel(state.position, state.velocity, state.time)
    state.velocity = state.velocity + a * dt
    state.position = state.position + state.velocity * dt
    state.time += dt


# ---------------------------------------------------------------------------
# Velocity-Verlet (2nd order, symplectic)
# ---------------------------------------------------------------------------


def velocity_verlet_step(state: IntegratorState, accel: AccelFunc, dt: float) -> None:
    """Velocity-Verlet (Störmer-Verlet) — symplectic, time-reversible, O(Δt²).

    Preferred for long-duration orbital / accelerator simulations where energy
    conservation matters.
    """
    a_current = accel(state.position, state.velocity, state.time)
    new_position = state.position + state.velocity * dt + a_current * (0.5 * dt * dt)
    a_next = accel(new_position, state.velocity, state.time + dt)
    new_velocity = state.velocity + (a_current + a_next) * (0.5 * dt)
    state.position = new_position
    state.velocity = new_velocity
    state.time += dt


# ---------------------------------------------------------------------------
# Leapfrog integrator (2nd order, symplectic)
# ---------------------------------------------------------------------------


def leapfrog_step(state: IntegratorState, accel: AccelFunc, dt: float) -> None:
    """Leapfrog (kick-drift-kick) — symplectic, O(Δt²).

    Interleaves half-step velocity kicks with full-step position drifts.
    """
    a = accel(state.position, state.velocity, state.time)
    half_v = state.velocity + a * (0.5 * dt)
    state.position = state.position + half_v * dt
    a_next = accel(state.position, half_v, state.time + dt)
    state.velocity = half_v + a_next * (0.5 * dt)
    state.time += dt


# ---------------------------------------------------------------------------
# RK4 integrator (4th order, most accurate per-step)
# ---------------------------------------------------------------------------


def rk4_step(state: IntegratorState, accel: AccelFunc, dt: float) -> None:
    """Classic 4th-order Runge-Kutta (O(Δt⁴) local error).

    Most accurate single-step integrator but **not** symplectic — energy may
    drift over very long runs.
    """
    p, v, t = state.position, state.velocity, state.time

    k1v = accel(p, v, t)
    k1x = v

    p2 = p + k1x * (0.5 * dt)
    v2 = v + k1v * (0.5 * dt)
    k2v = accel(p2, v2, t + 0.5 * dt)
    k2x = v2

    p3 = p + k2x * (0.5 * dt)
    v3 = v + k2v * (0.5 * dt)
    k3v = accel(p3, v3, t + 0.5 * dt)
    k3x = v3

    p4 = p + k3x * dt
    v4 = v + k3v * dt
    k4v = accel(p4, v4, t + dt)
    k4x = v4

    state.velocity = v + (k1v + k2v * 2.0 + k3v * 2.0 + k4v) * (dt / 6.0)
    state.position = p + (k1x + k2x * 2.0 + k3x * 2.0 + k4x) * (dt / 6.0)
    state.time += dt


# ---------------------------------------------------------------------------
# Adaptive time-step controller
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class AdaptiveTimestep:
    """CFL-style adaptive time-step controller.

    Picks Δt so that the fastest particle moves at most ``cfl_factor × length_scale``
    per step.  Also enforces minimum and maximum bounds.
    """

    base_dt: float = 1.0e-10
    min_dt: float = 1.0e-13
    max_dt: float = 1.0e-8
    cfl_factor: float = 0.4
    length_scale: float = 0.01  # metres

    def compute(self, max_speed: float) -> float:
        """Return the adaptive Δt for the current fastest speed."""
        if max_speed <= 0.0:
            return self.base_dt
        dt = self.cfl_factor * self.length_scale / max_speed
        return max(self.min_dt, min(self.max_dt, dt))
