"""Runtime parameters — manages live parameter overrides during a simulation run.

Provides a mutable parameter store that can be updated at runtime without
restarting the simulation process.  Supports validation against a schema of
allowed keys and value types.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


# Expected types for known simulation parameters.
_PARAM_SCHEMA: dict[str, type | tuple[type, ...]] = {
    "beam_energy_gev": (int, float),
    "beam_species": str,
    "particles_per_bunch": int,
    "simulation_steps": int,
    "time_step_s": float,
    "collision_radius_m": float,
    "tracker_layers": int,
    "em_cal_bins_eta": int,
    "em_cal_bins_phi": int,
    "had_cal_bins_eta": int,
    "had_cal_bins_phi": int,
    "jet_radius": float,
    "jet_min_pt_gev": (int, float),
    "trigger_min_energy_gev": (int, float),
    "random_seed": int,
    "max_workers": int,
    "log_level": str,
    "storage_dir": str,
    "websocket_host": str,
    "websocket_port": int,
    "api_host": str,
    "api_port": int,
}


@dataclass
class RuntimeParameters:
    """Thread-safe store for live simulation parameter overrides.

    Parameters are validated against ``_PARAM_SCHEMA`` when ``strict``
    mode is enabled.  In non-strict mode unknown keys are accepted.

    Attributes:
        strict: if True, reject unknown parameter names on ``set``.
    """

    strict: bool = False

    _params: dict[str, Any] = field(default_factory=dict, repr=False, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, init=False)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def set(self, key: str, value: Any) -> None:
        """Set a runtime parameter.

        Args:
            key: parameter name.
            value: new value (type-checked against schema if known).

        Raises:
            KeyError: if ``strict=True`` and *key* is not in the schema.
            TypeError: if *value* does not match the expected type.
        """
        if self.strict and key not in _PARAM_SCHEMA:
            raise KeyError(f"Unknown runtime parameter: {key!r}")
        if key in _PARAM_SCHEMA:
            expected = _PARAM_SCHEMA[key]
            if not isinstance(value, expected):
                raise TypeError(
                    f"Parameter {key!r} expects {expected}, got {type(value).__name__}"
                )
        with self._lock:
            self._params[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get the current value for *key*, or *default* if not set."""
        with self._lock:
            return self._params.get(key, default)

    def update(self, params: dict[str, Any]) -> None:
        """Bulk-set multiple parameters."""
        for k, v in params.items():
            self.set(k, v)

    def delete(self, key: str) -> None:
        """Remove a runtime override, reverting to the base default."""
        with self._lock:
            self._params.pop(key, None)

    def clear(self) -> None:
        """Remove all runtime overrides."""
        with self._lock:
            self._params.clear()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def all(self) -> dict[str, Any]:
        """Return a copy of all current runtime overrides."""
        with self._lock:
            return dict(self._params)

    @staticmethod
    def schema() -> dict[str, str]:
        """Return the parameter schema as {key: type_name} for docs."""
        return {
            k: (v.__name__ if isinstance(v, type) else " | ".join(t.__name__ for t in v))
            for k, v in _PARAM_SCHEMA.items()
        }
