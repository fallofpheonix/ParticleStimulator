"""Physics Engine — particle dynamics, forces, and motion integration."""

from backend.physics_engine.particle_model import Particle, ParticleSpecies
from backend.physics_engine.particle_state import ParticleState
from backend.physics_engine.relativistic_dynamics import (
    gamma_factor,
    beta_factor,
    relativistic_energy,
    relativistic_momentum,
    speed_from_kinetic_energy,
)
from backend.physics_engine.lorentz_force import lorentz_force_3d, lorentz_acceleration
from backend.physics_engine.coulomb_force import coulomb_force
from backend.physics_engine.field_solver import FieldConfiguration
from backend.physics_engine.motion_integrator import boris_push, advance_particle

__all__ = [
    "Particle",
    "ParticleSpecies",
    "ParticleState",
    "gamma_factor",
    "beta_factor",
    "relativistic_energy",
    "relativistic_momentum",
    "speed_from_kinetic_energy",
    "lorentz_force_3d",
    "lorentz_acceleration",
    "coulomb_force",
    "FieldConfiguration",
    "boris_push",
    "advance_particle",
]
