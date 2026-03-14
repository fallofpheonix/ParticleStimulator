"""Detector geometry — layered cylindrical detector model.

Defines the radial structure: beam pipe → tracker → EM calorimeter
→ hadronic calorimeter → muon chamber, each with inner/outer radii.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DetectorLayer:
    """A single cylindrical detector layer."""
    name: str
    inner_radius_m: float
    outer_radius_m: float
    half_length_m: float

    def contains_radial(self, r: float) -> bool:
        return self.inner_radius_m <= r <= self.outer_radius_m


@dataclass(frozen=True, slots=True)
class DetectorGeometry:
    """Full ATLAS/CMS-style cylindrical detector geometry."""

    beam_pipe: DetectorLayer = DetectorLayer("beam_pipe", 0.0, 0.024, 10.0)
    tracker: DetectorLayer = DetectorLayer("tracker", 0.025, 0.12, 2.7)
    em_calorimeter: DetectorLayer = DetectorLayer("em_cal", 0.13, 0.20, 3.2)
    had_calorimeter: DetectorLayer = DetectorLayer("had_cal", 0.21, 0.40, 4.0)
    muon_chamber: DetectorLayer = DetectorLayer("muon", 0.45, 1.0, 6.0)

    def layer_at_radius(self, r: float) -> DetectorLayer | None:
        for layer in (self.beam_pipe, self.tracker, self.em_calorimeter,
                      self.had_calorimeter, self.muon_chamber):
            if layer.contains_radial(r):
                return layer
        return None

    @property
    def all_layers(self) -> list[DetectorLayer]:
        return [self.beam_pipe, self.tracker, self.em_calorimeter,
                self.had_calorimeter, self.muon_chamber]
