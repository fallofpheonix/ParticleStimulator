"""Kalman filter — sequential state estimation for track fitting.

Implements a 1D Kalman filter as a building block for track fitting.
Real detectors use extended Kalman filters in full 3D phase space.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class KalmanFilter1D:
    """Simple 1D Kalman filter for position/velocity estimation."""

    state: float = 0.0
    covariance: float = 1.0
    process_noise: float = 0.01
    measurement_noise: float = 0.1

    def predict(self, dt: float = 1.0, velocity: float = 0.0) -> None:
        """Prediction step: advance state by dt."""
        self.state += velocity * dt
        self.covariance += self.process_noise

    def update(self, measurement: float) -> None:
        """Update step: incorporate a new measurement."""
        gain = self.covariance / (self.covariance + self.measurement_noise)
        self.state += gain * (measurement - self.state)
        self.covariance *= (1.0 - gain)

    def filter_sequence(self, measurements: list[float], dt: float = 1.0) -> list[float]:
        """Run the filter over a sequence of measurements."""
        results = []
        for m in measurements:
            self.predict(dt)
            self.update(m)
            results.append(self.state)
        return results
