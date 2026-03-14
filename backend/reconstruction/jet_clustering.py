"""Jet clustering wrapper — builds jets from calorimeter deposits."""

from __future__ import annotations
import math
from dataclasses import dataclass
from backend.detector.calorimeter_em import EMDeposit
from backend.detector.calorimeter_hadronic import HadronicDeposit
from backend.reconstruction.anti_kt import PseudoJet, anti_kt_cluster


@dataclass(frozen=True, slots=True)
class ReconstructedJet:
    """A reconstructed jet with corrected kinematics."""
    jet_id: int
    pt_gev: float
    eta: float
    phi: float
    energy_gev: float
    n_constituents: int


@dataclass(slots=True)
class JetClusterer:
    """Clusters calorimeter deposits into jets using anti-kT."""

    jet_radius: float = 0.4
    min_pt_gev: float = 5.0

    def cluster(self, em: list[EMDeposit], had: list[HadronicDeposit]) -> list[ReconstructedJet]:
        pseudojets = []
        for d in em:
            phi = (d.phi_bin + 0.5) / 64 * 2 * math.pi - math.pi
            eta = (d.eta_bin + 0.5) / 50 * 10 - 5
            pt = d.energy_gev  # approximate
            px = pt * math.cos(phi)
            py = pt * math.sin(phi)
            pz = pt * math.sinh(eta) if abs(eta) < 5 else 0.0
            e = math.sqrt(px**2 + py**2 + pz**2)
            pseudojets.append(PseudoJet(px, py, pz, e))

        for d in had:
            phi = (d.phi_bin + 0.5) / 32 * 2 * math.pi - math.pi
            eta = (d.eta_bin + 0.5) / 25 * 10 - 5
            pt = d.energy_gev
            px = pt * math.cos(phi)
            py = pt * math.sin(phi)
            pz = pt * math.sinh(eta) if abs(eta) < 5 else 0.0
            e = math.sqrt(px**2 + py**2 + pz**2)
            pseudojets.append(PseudoJet(px, py, pz, e))

        if not pseudojets:
            return []

        clustered = anti_kt_cluster(pseudojets, self.jet_radius)
        jets = []
        for i, j in enumerate(clustered):
            pt = j.pt
            if pt < self.min_pt_gev:
                continue
            p_mag = math.sqrt(j.px**2 + j.py**2 + j.pz**2)
            eta = 0.5 * math.log((p_mag + j.pz) / max(p_mag - j.pz, 1e-10)) if p_mag > abs(j.pz) else 0.0
            jets.append(ReconstructedJet(i + 1, pt, eta, j.phi, j.energy, j.constituents))
        return jets
