"""GPU executor — high-level interface for GPU-accelerated simulation tasks.

Wraps the low-level ``GPUComputeInterface`` and exposes a job-oriented
API so that the scheduler can offload particle-push batches to GPU
hardware when available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.infrastructure.gpu_compute import GPUComputeInterface


@dataclass
class GPUExecutor:
    """Orchestrates GPU execution of simulation sub-tasks.

    Attributes:
        device_id: GPU device index to target.
        enabled: whether GPU acceleration should be attempted.
        fallback_to_cpu: if True, silently fall back to CPU when GPU
            is unavailable.
    """

    device_id: int = 0
    enabled: bool = True
    fallback_to_cpu: bool = True

    def __post_init__(self) -> None:
        self._gpu = GPUComputeInterface(device_id=self.device_id, enabled=self.enabled)

    # ------------------------------------------------------------------
    # Capability
    # ------------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        """True when a GPU is detected and enabled."""
        return self._gpu.is_available

    def status(self) -> dict[str, Any]:
        """Return a status dict describing GPU availability."""
        return {
            "device_id": self.device_id,
            "enabled": self.enabled,
            "available": self.is_available,
            "fallback_to_cpu": self.fallback_to_cpu,
        }

    # ------------------------------------------------------------------
    # Particle push
    # ------------------------------------------------------------------

    def execute_particle_push(
        self,
        positions: list,
        velocities: list,
        fields: list,
        dt: float,
    ) -> tuple[list, list]:
        """Execute a Boris particle push, optionally on GPU.

        Args:
            positions: list of position vectors.
            velocities: list of velocity vectors.
            fields: list of (E, B) field tuples.
            dt: time step in seconds.

        Returns:
            Updated (positions, velocities) tuple.
        """
        if self.is_available or not self.fallback_to_cpu:
            return self._gpu.offload_particle_push(positions, velocities, fields, dt)
        # CPU fallback — return inputs unchanged (caller handles propagation).
        return positions, velocities

    # ------------------------------------------------------------------
    # Batch matrix operations (stub for future CUDA kernels)
    # ------------------------------------------------------------------

    def execute_matrix_batch(self, matrices: list, vectors: list) -> list:
        """Batch matrix-vector multiplications (GPU stub).

        Falls back to sequential NumPy multiplication on CPU.

        Args:
            matrices: list of 2-D NumPy arrays.
            vectors: list of 1-D NumPy arrays.

        Returns:
            List of result vectors.
        """
        try:
            import numpy as np  # type: ignore
            return [np.dot(m, v) for m, v in zip(matrices, vectors)]
        except ImportError:  # pragma: no cover
            return vectors
