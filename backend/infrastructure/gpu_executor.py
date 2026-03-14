from __future__ import annotations

from typing import Any


class GPUExecutor:
    def __init__(self, device_id: int = 0, enabled: bool = True, fallback_to_cpu: bool = False):
        self._device_id = device_id
        self._enabled = enabled
        self._fallback_to_cpu = fallback_to_cpu

    def status(self) -> dict:
        try:
            import cupy  # type: ignore
            available = True
        except ImportError:
            available = False
        return {
            "device_id": self._device_id,
            "available": available,
            "enabled": self._enabled,
        }

    def execute_particle_push(self, pos, vel, fields, dt) -> tuple:
        if not self._enabled and self._fallback_to_cpu:
            return (pos, vel)
        return (pos, vel)

    def execute_matrix_batch(self, mats, vecs) -> list:
        import numpy as np
        return [np.asarray(m) @ np.asarray(v) for m, v in zip(mats, vecs)]
