"""Jet tagging — classifies jets as quark-jets, gluon-jets, or b-jets."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class JetTagger:
    """Simple jet tagger based on constituent multiplicity and energy.

    In production, this would use a neural network (e.g. ParticleNet).
    """

    b_tag_threshold: float = 0.6

    def tag(self, jet_features: dict[str, float]) -> str:
        """Return jet tag: 'light', 'b', or 'gluon'."""
        n_const = jet_features.get("n_constituents", 1)
        pt = jet_features.get("pt", 0)

        if n_const > 10 and pt > 30:
            return "gluon"
        if jet_features.get("b_score", 0) > self.b_tag_threshold:
            return "b"
        return "light"
