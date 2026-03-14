"""Event classifier — simple decision-tree-style signal/background classifier."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class EventClassifier:
    """Rule-based event classifier (placeholder for full ML model).

    Uses simple threshold cuts on event features.
    """

    met_cut_gev: float = 30.0
    n_jets_cut: int = 2
    ht_cut_gev: float = 100.0

    def classify(self, features: dict[str, float]) -> str:
        """Return 'signal' or 'background'."""
        met = features.get("met_gev", 0)
        n_jets = features.get("n_jets", 0)
        ht = features.get("ht_gev", 0)

        if met > self.met_cut_gev and n_jets >= self.n_jets_cut and ht > self.ht_cut_gev:
            return "signal"
        return "background"

    def score(self, features: dict[str, float]) -> float:
        """Return a signal-likelihood score in [0, 1]."""
        s = 0.0
        if features.get("met_gev", 0) > self.met_cut_gev:
            s += 0.33
        if features.get("n_jets", 0) >= self.n_jets_cut:
            s += 0.33
        if features.get("ht_gev", 0) > self.ht_cut_gev:
            s += 0.34
        return min(s, 1.0)
