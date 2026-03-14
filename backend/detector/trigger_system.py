"""Trigger system — event selection and filtering.

Implements a simplified L1/HLT trigger that decides whether an event
should be recorded based on energy thresholds and object multiplicity.
"""

from __future__ import annotations
from dataclasses import dataclass
from backend.detector.silicon_tracker import TrackerHit
from backend.detector.calorimeter_em import EMDeposit
from backend.detector.calorimeter_hadronic import HadronicDeposit
from backend.detector.muon_detector import MuonHit


@dataclass(frozen=True, slots=True)
class TriggerResult:
    """Result of trigger evaluation."""
    passed: bool
    trigger_name: str
    reason: str


@dataclass(slots=True)
class TriggerSystem:
    """Multi-threshold trigger system.

    Attributes:
        min_tracker_hits: minimum tracker hits to trigger.
        min_em_energy_gev: minimum total EM energy.
        min_had_energy_gev: minimum total hadronic energy.
        require_muon: whether a muon hit is required.
        min_total_energy_gev: minimum total calorimeter energy.
    """

    min_tracker_hits: int = 3
    min_em_energy_gev: float = 5.0
    min_had_energy_gev: float = 10.0
    require_muon: bool = False
    min_total_energy_gev: float = 20.0

    def evaluate(
        self,
        tracker_hits: list[TrackerHit],
        em_deposits: list[EMDeposit],
        had_deposits: list[HadronicDeposit],
        muon_hits: list[MuonHit],
    ) -> TriggerResult:
        """Evaluate whether the event passes the trigger."""
        total_em = sum(d.energy_gev for d in em_deposits)
        total_had = sum(d.energy_gev for d in had_deposits)
        total_energy = total_em + total_had

        if len(tracker_hits) >= self.min_tracker_hits and total_energy >= self.min_total_energy_gev:
            return TriggerResult(True, "energy_trigger", f"total_energy={total_energy:.1f} GeV")

        if total_em >= self.min_em_energy_gev:
            return TriggerResult(True, "em_trigger", f"em_energy={total_em:.1f} GeV")

        if total_had >= self.min_had_energy_gev:
            return TriggerResult(True, "had_trigger", f"had_energy={total_had:.1f} GeV")

        if muon_hits and self.require_muon:
            return TriggerResult(True, "muon_trigger", f"muon_count={len(muon_hits)}")

        if muon_hits:
            return TriggerResult(True, "muon_trigger", f"muon_count={len(muon_hits)}")

        return TriggerResult(False, "none", "below all thresholds")
