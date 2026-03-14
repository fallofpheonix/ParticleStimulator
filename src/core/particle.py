from __future__ import annotations

from dataclasses import dataclass, field
import itertools

from src.core.constants import PARTICLE_DB, SPEED_OF_LIGHT_M_S
from src.core.vector import Vector3
from src.physics.relativity import gamma_from_speed


_particle_ids = itertools.count(1)


@dataclass(slots=True)
class Particle:
    species: str
    position: Vector3
    velocity: Vector3
    mass_kg: float | None = None
    charge_c: float | None = None
    particle_id: int = field(default_factory=lambda: next(_particle_ids))
    alive: bool = True

    def __post_init__(self) -> None:
        spec = PARTICLE_DB.get(self.species)
        if self.mass_kg is None:
            if spec is None:
                raise ValueError(f"unknown particle species: {self.species}")
            self.mass_kg = spec.mass_kg
        if self.charge_c is None:
            if spec is None:
                raise ValueError(f"unknown particle species: {self.species}")
            self.charge_c = spec.charge_c

    def speed(self) -> float:
        return self.velocity.magnitude()

    def gamma(self) -> float:
        return gamma_from_speed(self.speed())

    def momentum(self) -> Vector3:
        return self.velocity * (self.gamma() * self.mass_kg)

    def kinetic_energy_j(self) -> float:
        return (self.gamma() - 1.0) * self.mass_kg * (SPEED_OF_LIGHT_M_S ** 2)

    def apply_acceleration(self, acceleration: Vector3, dt_s: float) -> None:
        updated_velocity = self.velocity + (acceleration * dt_s)
        self.velocity = updated_velocity.limit(0.995 * SPEED_OF_LIGHT_M_S)
        self.position = self.position + (self.velocity * dt_s)

    def copy(self) -> "Particle":
        return Particle(
            species=self.species,
            position=self.position,
            velocity=self.velocity,
            mass_kg=self.mass_kg,
            charge_c=self.charge_c,
            particle_id=self.particle_id,
            alive=self.alive,
        )
