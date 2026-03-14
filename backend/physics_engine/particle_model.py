"""Particle model and species registry.

Defines the ``Particle`` data class that carries position, velocity, mass,
charge, and lifecycle info.  The ``SPECIES_REGISTRY`` provides look-up for
all supported particle types (leptons, quarks, hadrons, bosons).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from backend.core_math.constants import (
    PARTICLE_CHARGES,
    PARTICLE_LIFETIMES,
    PARTICLE_MASSES,
    PARTICLE_SPINS,
    SPEED_OF_LIGHT,
)
from backend.core_math.vector3 import Vector3


_particle_ids = itertools.count(1)


@dataclass(frozen=True, slots=True)
class ParticleSpecies:
    """Immutable record of a particle species' intrinsic properties."""

    name: str
    mass_kg: float
    charge_c: float
    spin: float = 0.0
    lifetime_s: float = 0.0  # 0 = stable
    is_antiparticle: bool = False


def _build_species_registry() -> dict[str, ParticleSpecies]:
    """Build the registry from the constants database."""
    registry: dict[str, ParticleSpecies] = {}
    for name, mass in PARTICLE_MASSES.items():
        charge = PARTICLE_CHARGES.get(name, 0.0)
        spin = PARTICLE_SPINS.get(name, 0.0)
        lifetime = PARTICLE_LIFETIMES.get(name, 0.0)
        is_anti = name.startswith("anti") or name in ("positron", "muon+", "tau+")
        registry[name] = ParticleSpecies(
            name=name,
            mass_kg=mass,
            charge_c=charge,
            spin=spin,
            lifetime_s=lifetime,
            is_antiparticle=is_anti,
        )
    return registry


SPECIES_REGISTRY: dict[str, ParticleSpecies] = _build_species_registry()


@dataclass(slots=True)
class Particle:
    """Mutable particle state used in simulation.

    Attributes:
        species: name key into ``SPECIES_REGISTRY``
        position: current 3-position in metres
        velocity: current 3-velocity in m/s
        mass_kg: rest mass (auto-resolved from registry if None)
        charge_c: electric charge (auto-resolved from registry if None)
        particle_id: unique ID (auto-assigned)
        alive: whether the particle is still active
        age_s: accumulated proper time since creation
        parent_id: ID of the particle that created this one (0 = primary)
    """

    species: str
    position: Vector3
    velocity: Vector3
    mass_kg: float | None = None
    charge_c: float | None = None
    particle_id: int = field(default_factory=lambda: next(_particle_ids))
    alive: bool = True
    age_s: float = 0.0
    parent_id: int = 0

    def __post_init__(self) -> None:
        spec = SPECIES_REGISTRY.get(self.species)
        if self.mass_kg is None:
            if spec is None:
                raise ValueError(f"unknown particle species: {self.species}")
            self.mass_kg = spec.mass_kg
        if self.charge_c is None:
            if spec is None:
                raise ValueError(f"unknown particle species: {self.species}")
            self.charge_c = spec.charge_c

    def speed(self) -> float:
        """Magnitude of the velocity vector."""
        return self.velocity.magnitude()

    def is_charged(self) -> bool:
        return self.charge_c is not None and self.charge_c != 0.0

    def lifetime(self) -> float:
        """Mean lifetime in seconds (0.0 = stable)."""
        spec = SPECIES_REGISTRY.get(self.species)
        return spec.lifetime_s if spec else 0.0

    def copy(self) -> Particle:
        """Deep copy with the same particle_id."""
        return Particle(
            species=self.species,
            position=self.position,
            velocity=self.velocity,
            mass_kg=self.mass_kg,
            charge_c=self.charge_c,
            particle_id=self.particle_id,
            alive=self.alive,
            age_s=self.age_s,
            parent_id=self.parent_id,
        )
