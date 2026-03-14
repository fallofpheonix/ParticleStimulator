from __future__ import annotations

from src.core.particle import Particle
from src.core.vector import Vector3


def lorentz_force(particle: Particle, electric_field: Vector3, magnetic_field: Vector3) -> Vector3:
    if particle.charge_c == 0.0:
        return Vector3()
    return (electric_field + particle.velocity.cross(magnetic_field)) * particle.charge_c


def acceleration_from_force(force: Vector3, particle: Particle) -> Vector3:
    if particle.mass_kg == 0.0:
        return Vector3()
    return force / particle.mass_kg
