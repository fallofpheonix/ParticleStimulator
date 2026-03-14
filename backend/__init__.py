"""ParticleStimulator Backend — production-scale particle physics simulation.

This package provides the modular backend architecture for simulating
the complete particle physics experiment pipeline:

    Accelerator → Physics Engine → Collision Engine → Detector →
    Reconstruction → Analysis → Event Streaming

Usage::

    from backend.api_server.simulation_controller import SimulationController
    controller = SimulationController()
    result = controller.run_full_pipeline()
"""

__version__ = "0.1.0"
