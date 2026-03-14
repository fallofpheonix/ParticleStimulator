"""Anti-kT jet clustering algorithm.

The anti-kT algorithm is the standard jet finder at the LHC.
It clusters particles by angular proximity, prioritizing hard
(high-pT) particles, producing cone-like jets.
"""

from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(slots=True)
class PseudoJet:
    """Lightweight jet candidate (px, py, pz, E)."""
    px: float = 0.0
    py: float = 0.0
    pz: float = 0.0
    energy: float = 0.0
    constituents: int = 1

    @property
    def pt(self) -> float:
        return math.hypot(self.px, self.py)

    @property
    def pt_squared(self) -> float:
        return self.px ** 2 + self.py ** 2

    @property
    def phi(self) -> float:
        return math.atan2(self.py, self.px)

    @property
    def rapidity(self) -> float:
        if self.energy <= abs(self.pz):
            return 0.0
        return 0.5 * math.log((self.energy + self.pz) / (self.energy - self.pz))

    def merge(self, other: PseudoJet) -> PseudoJet:
        return PseudoJet(
            px=self.px + other.px,
            py=self.py + other.py,
            pz=self.pz + other.pz,
            energy=self.energy + other.energy,
            constituents=self.constituents + other.constituents,
        )


def _delta_r_squared(a: PseudoJet, b: PseudoJet) -> float:
    dy = a.rapidity - b.rapidity
    dphi = a.phi - b.phi
    while dphi > math.pi:
        dphi -= 2.0 * math.pi
    while dphi <= -math.pi:
        dphi += 2.0 * math.pi
    return dy * dy + dphi * dphi


def anti_kt_cluster(particles: list[PseudoJet], R: float = 0.4) -> list[PseudoJet]:
    """Run the anti-kT jet clustering algorithm.

    Args:
        particles: list of PseudoJets to cluster.
        R: jet radius parameter.

    Returns:
        List of clustered jets.
    """
    jets: list[PseudoJet] = list(particles)
    if not jets:
        return []

    R_sq = R * R
    final_jets: list[PseudoJet] = []

    while len(jets) > 0:
        n = len(jets)
        min_d = float("inf")
        min_i = -1
        min_j = -1
        is_beam = True

        # Compute 1/pt² for anti-kT
        inv_pt2 = []
        for j in jets:
            pt2 = j.pt_squared
            inv_pt2.append(1.0 / pt2 if pt2 > 0 else 1.0e30)

        # Find minimum distance
        for i in range(n):
            d_iB = inv_pt2[i]
            if d_iB < min_d:
                min_d = d_iB
                min_i = i
                min_j = -1
                is_beam = True

            for j in range(i + 1, n):
                d_ij = min(inv_pt2[i], inv_pt2[j]) * _delta_r_squared(jets[i], jets[j]) / R_sq
                if d_ij < min_d:
                    min_d = d_ij
                    min_i = i
                    min_j = j
                    is_beam = False

        if is_beam or min_j < 0:
            final_jets.append(jets.pop(min_i))
        else:
            merged = jets[min_i].merge(jets[min_j])
            jets.pop(max(min_i, min_j))
            jets.pop(min(min_i, min_j))
            jets.append(merged)

    return final_jets
