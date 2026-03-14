"""Simulation controller — orchestrates the full backend pipeline.

This is the central entry point that connects:
    Accelerator → Physics Engine → Collision Engine → Detector →
    Reconstruction → Analysis → Event Streaming

All subsystems communicate through shared data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.accelerator.beam_source import BeamSource
from backend.accelerator.synchrotron_ring import SynchrotronRing
from backend.accelerator.beam_monitor import BeamMonitor
from backend.collision_engine.event_generator import EventGenerator
from backend.detector.silicon_tracker import SiliconTracker
from backend.detector.calorimeter_em import EMCalorimeter
from backend.detector.calorimeter_hadronic import HadronicCalorimeter
from backend.detector.muon_detector import MuonDetector
from backend.detector.trigger_system import TriggerSystem
from backend.reconstruction.track_reconstruction import TrackReconstructor
from backend.reconstruction.vertex_finding import VertexFinder
from backend.reconstruction.jet_clustering import JetClusterer
from backend.reconstruction.missing_energy import MissingEnergyCalculator
from backend.analysis.histogram_engine import HistogramEngine
from backend.analysis.significance_test import SignificanceCalculator
from backend.api_server.event_stream import EventStream
from backend.infrastructure.config_manager import ConfigManager
from backend.infrastructure.logging_system import SimulationLogger
from backend.physics_engine.motion_integrator import boris_push


@dataclass(slots=True)
class SimulationController:
    """Runs the complete accelerator → analysis pipeline.

    Attributes:
        config: simulation configuration.
    """

    config: ConfigManager = field(default_factory=ConfigManager)
    event_stream: EventStream = field(default_factory=EventStream)
    _logger: Any = field(init=False, repr=False, default=None)

    def __post_init__(self) -> None:
        self._logger = SimulationLogger().get_logger()

    def run_full_pipeline(self) -> dict[str, Any]:
        """Execute the full simulation pipeline and return results.

        Pipeline:
            1. Generate beams (accelerator)
            2. Advance particles (physics engine)
            3. Detect collisions and generate events (collision engine)
            4. Simulate detector response (detector)
            5. Reconstruct events (reconstruction)
            6. Analyse results (analysis)
            7. Stream events (API)
        """
        cfg = self.config
        self._logger.info("Starting full simulation pipeline")

        # --- 1. Beam generation ---
        beam_source = BeamSource(
            species=cfg.get("beam_species", "proton"),
            beam_energy_gev=cfg.get("beam_energy_gev", 6500.0),
            particles_per_bunch=cfg.get("particles_per_bunch", 6),
            seed=cfg.get("random_seed", 42),
        )
        particles = beam_source.generate_counter_beams()
        self._logger.info(f"Generated {len(particles)} beam particles")

        # --- 2. Accelerator / physics engine ---
        ring = SynchrotronRing()
        monitor = BeamMonitor()
        n_steps = cfg.get("simulation_steps", 500)
        dt = cfg.get("time_step_s", 1.0e-10)

        for step in range(n_steps):
            for p in particles:
                if not p.alive:
                    continue
                e_field = ring.electric_field_at(p.position, step * dt)
                b_field = ring.magnetic_field_at(p.position)
                boris_push(p, e_field, b_field, dt)
                if not ring.contains(p.position):
                    p.alive = False
            if step % 100 == 0:
                monitor.measure(particles, step * dt)

        alive = [p for p in particles if p.alive]
        self._logger.info(f"After {n_steps} steps: {len(alive)} alive particles")

        # --- 3. Collision engine ---
        event_gen = EventGenerator(
            interaction_radius_m=cfg.get("collision_radius_m", 0.06),
            seed=cfg.get("random_seed", 42),
        )
        collision_events = event_gen.process_collisions(alive)
        self._logger.info(f"Generated {len(collision_events)} collision events")

        all_final_particles = []
        for ce in collision_events:
            all_final_particles.extend([p for p in ce.final_particles if p.alive])

        # --- 4. Detector simulation ---
        time_s = n_steps * dt
        tracker = SiliconTracker()
        em_cal = EMCalorimeter()
        had_cal = HadronicCalorimeter()
        muon_det = MuonDetector()
        trigger = TriggerSystem(min_total_energy_gev=cfg.get("trigger_min_energy_gev", 20.0))

        tracker_hits = tracker.simulate(all_final_particles, time_s)
        em_deposits = em_cal.simulate(all_final_particles, time_s)
        had_deposits = had_cal.simulate(all_final_particles, time_s)
        muon_hits = muon_det.simulate(all_final_particles, time_s)

        trigger_result = trigger.evaluate(tracker_hits, em_deposits, had_deposits, muon_hits)
        self._logger.info(f"Trigger: {trigger_result.passed} ({trigger_result.trigger_name})")

        # --- 5. Reconstruction ---
        track_reco = TrackReconstructor(min_hits=cfg.get("track_min_hits", 3))
        tracks = track_reco.reconstruct(tracker_hits)

        vertex_finder = VertexFinder()
        vertices = vertex_finder.find_vertices(tracks)

        jet_clusterer = JetClusterer(
            jet_radius=cfg.get("jet_radius", 0.4),
            min_pt_gev=cfg.get("jet_min_pt_gev", 5.0),
        )
        jets = jet_clusterer.cluster(em_deposits, had_deposits)

        met_calc = MissingEnergyCalculator()
        met = met_calc.compute(em_deposits, had_deposits)

        self._logger.info(f"Reconstructed: {len(tracks)} tracks, {len(jets)} jets, MET={met.met_gev:.1f} GeV")

        # --- 6. Analysis ---
        hist_engine = HistogramEngine()
        h_energy = hist_engine.create("jet_energy", 50, 0.0, 200.0)
        for j in jets:
            h_energy.fill(j.energy_gev)

        sig_calc = SignificanceCalculator()

        # --- 7. Build event output ---
        event_output: dict[str, Any] = {
            "event_id": collision_events[0].event_id if collision_events else 0,
            "n_collisions": len(collision_events),
            "n_final_particles": len(all_final_particles),
            "trigger_passed": trigger_result.passed,
            "trigger_name": trigger_result.trigger_name,
            "n_tracker_hits": len(tracker_hits),
            "n_em_deposits": len(em_deposits),
            "n_had_deposits": len(had_deposits),
            "n_muon_hits": len(muon_hits),
            "n_tracks": len(tracks),
            "n_vertices": len(vertices),
            "n_jets": len(jets),
            "met_gev": met.met_gev,
            "jets": [{"pt": j.pt_gev, "eta": j.eta, "phi": j.phi, "energy": j.energy_gev} for j in jets],
            "vertices": [{"x": v.position.x, "y": v.position.y, "z": v.position.z, "ntracks": v.n_tracks} for v in vertices],
        }

        self.event_stream.push(event_output)
        self._logger.info("Pipeline complete")

        return event_output
