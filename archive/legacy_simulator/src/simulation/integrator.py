from __future__ import annotations

from src.accelerator.beamline import Beamline
from src.core.particle import Particle
from src.physics.electromagnetism import acceleration_from_force, lorentz_force


def advance_particle(particle: Particle, beamline: Beamline, dt_s: float) -> None:
    electric_field = beamline.electric_field_at(particle.position)
    magnetic_field = beamline.magnetic_field_at(particle.position)
    force = lorentz_force(particle, electric_field, magnetic_field)
    acceleration = acceleration_from_force(force, particle)
    particle.apply_acceleration(acceleration, dt_s)
