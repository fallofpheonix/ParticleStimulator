"""Relativistic four-vector (Minkowski space).

Provides Energy-momentum 4-vectors with the metric signature (+, −, −, −).
Used for invariant mass calculations, Lorentz boosts, and relativistic
kinematics throughout the collision and analysis engines.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from backend.core_math.vector3 import Vector3


@dataclass(frozen=True, slots=True)
class FourVector:
    """Minkowski 4-vector with signature (+, −, −, −).

    Components:
        t — timelike / energy component (E/c or E in natural units)
        x, y, z — spacelike / momentum components
    """

    t: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # -- construction helpers -----------------------------------------------

    @classmethod
    def from_energy_momentum(cls, energy: float, px: float, py: float, pz: float) -> FourVector:
        """Create a 4-vector from (E, px, py, pz)."""
        return cls(t=energy, x=px, y=py, z=pz)

    @classmethod
    def from_mass_and_momentum(cls, mass: float, momentum: Vector3, c: float = 1.0) -> FourVector:
        """Build from rest mass and 3-momentum.  E² = p²c² + m²c⁴."""
        p_sq = momentum.magnitude_squared()
        energy = math.sqrt(p_sq * c * c + mass * mass * c ** 4)
        return cls(t=energy, x=momentum.x, y=momentum.y, z=momentum.z)

    # -- arithmetic ---------------------------------------------------------

    def __add__(self, other: FourVector) -> FourVector:
        return FourVector(self.t + other.t, self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: FourVector) -> FourVector:
        return FourVector(self.t - other.t, self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> FourVector:
        return FourVector(self.t * scalar, self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> FourVector:
        return self.__mul__(scalar)

    def __neg__(self) -> FourVector:
        return FourVector(-self.t, -self.x, -self.y, -self.z)

    # -- Minkowski inner product --------------------------------------------

    def dot(self, other: FourVector) -> float:
        """Minkowski inner product η_μν a^μ b^ν with (+,−,−,−) signature."""
        return self.t * other.t - self.x * other.x - self.y * other.y - self.z * other.z

    def invariant_mass_squared(self) -> float:
        """p² = E² − |p⃗|² (natural units).  Equals m²c⁴ for on-shell particles."""
        return self.dot(self)

    def invariant_mass(self) -> float:
        """√(p²);  returns 0.0 for spacelike or lightlike 4-momenta."""
        m2 = self.invariant_mass_squared()
        return math.sqrt(max(0.0, m2))

    # -- spatial components -------------------------------------------------

    @property
    def spatial(self) -> Vector3:
        """Extract the 3-momentum / spatial part."""
        return Vector3(self.x, self.y, self.z)

    @property
    def energy(self) -> float:
        return self.t

    # -- transverse kinematics ----------------------------------------------

    def pt(self) -> float:
        """Transverse momentum p_T = √(px² + py²)."""
        return math.hypot(self.x, self.y)

    def phi(self) -> float:
        """Azimuthal angle."""
        return math.atan2(self.y, self.x)

    def eta(self) -> float:
        """Pseudorapidity."""
        p = self.spatial.magnitude()
        if p == 0.0:
            return 0.0
        theta = math.acos(max(-1.0, min(1.0, self.z / p)))
        if theta <= 0.0 or theta >= math.pi:
            return float("inf") if theta <= 0.0 else float("-inf")
        return -math.log(math.tan(theta / 2.0))

    def rapidity(self) -> float:
        """True rapidity y = ½ ln((E + pz) / (E − pz))."""
        denom = self.t - self.z
        if denom <= 0.0:
            return float("inf")
        return 0.5 * math.log((self.t + self.z) / denom)

    def delta_r(self, other: FourVector) -> float:
        """Angular distance ΔR = √(Δη² + Δφ²) in η-φ space."""
        d_eta = self.eta() - other.eta()
        d_phi = self.phi() - other.phi()
        # Wrap Δφ into (−π, π]
        while d_phi > math.pi:
            d_phi -= 2.0 * math.pi
        while d_phi <= -math.pi:
            d_phi += 2.0 * math.pi
        return math.sqrt(d_eta * d_eta + d_phi * d_phi)

    # -- Lorentz boost (along arbitrary axis) --------------------------------

    def boost(self, beta_vec: Vector3) -> FourVector:
        """Apply a Lorentz boost defined by velocity vector β⃗ = v⃗/c.

        Uses the general boost formula for arbitrary direction.
        """
        beta_sq = beta_vec.magnitude_squared()
        if beta_sq == 0.0:
            return self
        if beta_sq >= 1.0:
            raise ValueError("β² must be < 1 for a valid Lorentz boost")

        gamma = 1.0 / math.sqrt(1.0 - beta_sq)
        p_vec = self.spatial
        bp = beta_vec.dot(p_vec)

        new_t = gamma * (self.t - bp)
        factor = (gamma - 1.0) * bp / beta_sq - gamma * self.t
        new_spatial = p_vec + beta_vec * factor

        return FourVector(new_t, new_spatial.x, new_spatial.y, new_spatial.z)

    # -- serialisation -------------------------------------------------------

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.t, self.x, self.y, self.z)

    def as_dict(self) -> dict[str, float]:
        return {"energy": self.t, "px": self.x, "py": self.y, "pz": self.z}
