"""Beam injector — transfers particles into the accelerator ring."""

from __future__ import annotations

from dataclasses import dataclass

from backend.accelerator.beam_packet import BeamPacket
from backend.accelerator.beam_source import BeamSource
from backend.core_math.vector3 import Vector3


@dataclass(slots=True)
class BeamInjector:
    """Manages injection of beam packets into the synchrotron ring.

    Attributes:
        injection_point: 3D position where particles enter the ring.
        kicker_strength: transverse kick applied during injection (m/s).
        max_injections: maximum injection attempts before abort.
    """

    injection_point: Vector3 = Vector3(-0.5, 0.0, 0.0)
    kicker_strength: float = 1.0e4
    max_injections: int = 100

    def inject(self, source: BeamSource) -> BeamPacket:
        """Generate and inject a beam packet from a source.

        Applies the injection kicker to shift particles onto the closed orbit.
        """
        particles = source.generate_beam(
            direction=Vector3(1.0, 0.0, 0.0),
            offset=self.injection_point,
        )
        # Apply kicker: small transverse velocity bump
        for p in particles:
            p.velocity = p.velocity + Vector3(0.0, self.kicker_strength, 0.0)
        return BeamPacket(particles=particles)
