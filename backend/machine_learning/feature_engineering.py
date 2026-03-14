"""Feature engineering — derives ML features from reconstructed events."""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FeatureEngineer:
    """Computes derived features from reconstructed event data."""

    def compute_features(self, event: dict[str, Any]) -> dict[str, float]:
        jets = event.get("jets", [])
        n_jets = float(len(jets))
        met = float(event.get("met_gev", 0))
        n_tracks = float(event.get("n_tracks", 0))
        ht = sum(j.get("pt", 0) for j in jets)
        lead_jet_pt = jets[0].get("pt", 0) if jets else 0.0
        lead_jet_eta = jets[0].get("eta", 0) if jets else 0.0
        return {
            "n_jets": n_jets,
            "met_gev": met,
            "n_tracks": n_tracks,
            "ht_gev": ht,
            "lead_jet_pt": lead_jet_pt,
            "lead_jet_eta": abs(lead_jet_eta),
            "met_over_ht": met / ht if ht > 0 else 0.0,
        }
