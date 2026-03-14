"""Collision Engine — Monte Carlo event generation, parton physics, showers, hadronization, decay."""

from backend.collision_engine.event_generator import EventGenerator, CollisionEvent
from backend.collision_engine.parton_distribution import PartonDistribution
from backend.collision_engine.qcd_scattering import QCDScattering
from backend.collision_engine.cross_section import CrossSectionCalculator
from backend.collision_engine.particle_shower import ParticleShower
from backend.collision_engine.hadronization import Hadronizer
from backend.collision_engine.particle_decay import DecayEngine

__all__ = [
    "EventGenerator", "CollisionEvent", "PartonDistribution",
    "QCDScattering", "CrossSectionCalculator", "ParticleShower",
    "Hadronizer", "DecayEngine",
]
