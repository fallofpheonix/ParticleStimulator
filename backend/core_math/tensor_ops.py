"""Tensor operations for relativistic physics.

Provides the Minkowski metric tensor, index contraction, and basic
tensor algebra used in 4-vector kinematics and field-tensor computations.
"""

from __future__ import annotations

from backend.core_math.vector4 import FourVector

# ---------------------------------------------------------------------------
# Minkowski metric (+, −, −, −)
# ---------------------------------------------------------------------------

METRIC_SIGNATURE: tuple[float, ...] = (1.0, -1.0, -1.0, -1.0)


def metric_contract(a: FourVector, b: FourVector) -> float:
    """Contract two 4-vectors using the Minkowski metric: η_μν a^μ b^ν."""
    return a.t * b.t - a.x * b.x - a.y * b.y - a.z * b.z


def raise_index(v: FourVector) -> FourVector:
    """Convert covariant → contravariant (flip spatial sign with +−−− metric)."""
    return FourVector(v.t, -v.x, -v.y, -v.z)


def lower_index(v: FourVector) -> FourVector:
    """Convert contravariant → covariant (same operation for +−−− metric)."""
    return raise_index(v)


# ---------------------------------------------------------------------------
# Electromagnetic field tensor F^μν (antisymmetric)
# ---------------------------------------------------------------------------


class FieldTensor:
    """Antisymmetric rank-2 electromagnetic field tensor F^μν.

    Stores the 6 independent components:
        Electric field: E = (Ex, Ey, Ez)
        Magnetic field: B = (Bx, By, Bz)

    Convention (SI-like natural units):
        F^01 = Ex,  F^02 = Ey,  F^03 = Ez
        F^12 = -Bz, F^13 = By,  F^23 = -Bx
    """

    __slots__ = ("ex", "ey", "ez", "bx", "by", "bz")

    def __init__(
        self,
        ex: float = 0.0, ey: float = 0.0, ez: float = 0.0,
        bx: float = 0.0, by: float = 0.0, bz: float = 0.0,
    ) -> None:
        self.ex = ex
        self.ey = ey
        self.ez = ez
        self.bx = bx
        self.by = by
        self.bz = bz

    def component(self, mu: int, nu: int) -> float:
        """Return F^{mu,nu} for mu, nu in {0,1,2,3}."""
        if mu == nu:
            return 0.0
        # Map index pairs to field components
        mapping = {
            (0, 1): self.ex,  (1, 0): -self.ex,
            (0, 2): self.ey,  (2, 0): -self.ey,
            (0, 3): self.ez,  (3, 0): -self.ez,
            (1, 2): -self.bz, (2, 1): self.bz,
            (1, 3): self.by,  (3, 1): -self.by,
            (2, 3): -self.bx, (3, 2): self.bx,
        }
        return mapping.get((mu, nu), 0.0)

    def lorentz_force_4vector(self, charge: float, u: FourVector) -> FourVector:
        """Compute the 4-force f^μ = q F^{μν} u_ν on a charged particle.

        Args:
            charge: particle charge (Coulombs)
            u: 4-velocity of the particle
        """
        u_lower = lower_index(u)
        components = []
        for mu in range(4):
            val = sum(self.component(mu, nu) * (u_lower.t, u_lower.x, u_lower.y, u_lower.z)[nu] for nu in range(4))
            components.append(charge * val)
        return FourVector(*components)

    def invariant_1(self) -> float:
        """First Lorentz invariant: F_μν F^μν / 2 = B² − E²."""
        return (
            self.bx ** 2 + self.by ** 2 + self.bz ** 2
            - self.ex ** 2 - self.ey ** 2 - self.ez ** 2
        )

    def invariant_2(self) -> float:
        """Second Lorentz invariant: ε_μναβ F^μν F^αβ / 8 = E⃗·B⃗."""
        return self.ex * self.bx + self.ey * self.by + self.ez * self.bz
