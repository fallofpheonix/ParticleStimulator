"""GPU compute interface — abstraction for GPU-accelerated simulation.

Provides a stub interface for GPU acceleration.  When a CUDA/OpenCL
runtime is available the concrete implementations can be swapped in.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class GPUComputeInterface:
    """Abstract GPU compute layer.

    Attributes:
        device_id: GPU device index.
        enabled: whether GPU acceleration is active.
    """

    device_id: int = 0
    enabled: bool = False
    _available: bool = False

    def __post_init__(self) -> None:
        try:
            import numpy  # noqa: F401
            self._available = True
        except ImportError:
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available and self.enabled

    def offload_particle_push(self, positions: list, velocities: list, fields: list, dt: float) -> tuple:
        """Stub: offload Boris push to GPU.

        In production this would call a CUDA kernel.  Falls back to CPU.
        """
        if not self.is_available:
            return positions, velocities  # no-op
        # Placeholder for GPU kernel invocation
        return positions, velocities
