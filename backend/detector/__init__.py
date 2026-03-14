"""Detector Simulation — geometry, tracking, calorimetry, muon detection, trigger."""

from backend.detector.detector_geometry import DetectorGeometry
from backend.detector.beam_pipe import BeamPipe
from backend.detector.silicon_tracker import SiliconTracker, TrackerHit
from backend.detector.calorimeter_em import EMCalorimeter, EMDeposit
from backend.detector.calorimeter_hadronic import HadronicCalorimeter, HadronicDeposit
from backend.detector.muon_detector import MuonDetector, MuonHit
from backend.detector.trigger_system import TriggerSystem

__all__ = [
    "DetectorGeometry", "BeamPipe",
    "SiliconTracker", "TrackerHit",
    "EMCalorimeter", "EMDeposit",
    "HadronicCalorimeter", "HadronicDeposit",
    "MuonDetector", "MuonHit",
    "TriggerSystem",
]
