"""Particle state vector for simulation tracking.

Provides a compact state representation ``S = (x, y, z, px, py, pz, E, m, q)``
used by integrators, the collision engine, and serialization layers.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from backend.core_math.constants import SPEED_OF_LIGHT
from backend.core_math.vector3 import Vector3
from backend.core_math.vector4 import FourVector


@dataclass(slots=True)
class ParticleState:
    """Phase-space state vector of a single particle.

    Stores both 3-vector and derived 4-vector representations for use
    by different engine subsystems.
    """

    particle_id: int
    species: str
    position: Vector3
    momentum: Vector3  # relativistic 3-momentum (kg m/s)
    energy_j: float  # total relativistic energy (Joules)
    mass_kg: float
    charge_c: float
    active: bool = True

    # -- derived quantities --------------------------------------------------

    @property
    def four_momentum(self) -> FourVector:
        """Build (E, px, py, pz) 4-momentum."""
        return FourVector(self.energy_j, self.momentum.x, self.momentum.y, self.momentum.z)

    @property
    def velocity(self) -> Vector3:
        """v⃗ = p⃗c² / E  (relativistic velocity from momentum)."""
        if self.energy_j <= 0.0:
            return Vector3()
        factor = SPEED_OF_LIGHT * SPEED_OF_LIGHT / self.energy_j
        return self.momentum * factor

    @property
    def gamma(self) -> float:
        """Lorentz factor γ = E / (mc²)."""
        mc2 = self.mass_kg * SPEED_OF_LIGHT * SPEED_OF_LIGHT
        if mc2 <= 0.0:
            return float("inf")
        return self.energy_j / mc2

    @property
    def beta(self) -> float:
        """Speed as fraction of c: β = v/c."""
        g = self.gamma
        if g <= 1.0:
            return 0.0
        return math.sqrt(1.0 - 1.0 / (g * g))

    @property
    def kinetic_energy_j(self) -> float:
        """Kinetic energy T = E − mc²."""
        return self.energy_j - self.mass_kg * SPEED_OF_LIGHT ** 2

    @property
    def transverse_momentum(self) -> float:
        """pT = √(px² + py²)."""
        return math.hypot(self.momentum.x, self.momentum.y)

    @property
    def pseudorapidity(self) -> float:
        """η = −ln[tan(θ/2)] where θ is the polar angle of the momentum."""
        p = self.momentum.magnitude()
        if p == 0.0:
            return 0.0
        cos_theta = self.momentum.z / p
        cos_theta = max(-1.0, min(1.0, cos_theta))
        theta = math.acos(cos_theta)
        if theta <= 0.0 or theta >= math.pi:
            return float("inf") if theta <= 0.0 else float("-inf")
        return -math.log(math.tan(theta / 2.0))

    # -- factories -----------------------------------------------------------

    @classmethod
    def from_velocity(
        cls,
        particle_id: int,
        species: str,
        position: Vector3,
        velocity: Vector3,
        mass_kg: float,
        charge_c: float,
    ) -> ParticleState:
        """Construct state from position + velocity (computes momentum/energy)."""
        speed = velocity.magnitude()
        beta_val = min(speed / SPEED_OF_LIGHT, 0.999_999_999)
        gamma_val = 1.0 / math.sqrt(1.0 - beta_val * beta_val)
        momentum = velocity * (gamma_val * mass_kg)
        energy = gamma_val * mass_kg * SPEED_OF_LIGHT ** 2
        return cls(
            particle_id=particle_id,
            species=species,
            position=position,
            momentum=momentum,
            energy_j=energy,
            mass_kg=mass_kg,
            charge_c=charge_c,
        )

    # -- serialization -------------------------------------------------------

    def as_dict(self) -> dict[str, object]:
        return {
            "particle_id": self.particle_id,
            "species": self.species,
            "position": self.position.as_dict(),
            "momentum": self.momentum.as_dict(),
            "energy_j": self.energy_j,
            "mass_kg": self.mass_kg,
            "charge_c": self.charge_c,
            "active": self.active,
        }
