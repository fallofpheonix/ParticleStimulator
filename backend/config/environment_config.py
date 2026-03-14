"""Environment config — reads simulation parameters from environment variables.

Allows deployment environments (Docker, CI, cloud) to override default
simulation settings without modifying JSON config files.
"""

from __future__ import annotations

import os
from typing import Any


# Mapping: environment variable name → (config key, type converter).
_ENV_MAP: dict[str, tuple[str, type]] = {
    "SIM_BEAM_ENERGY_GEV": ("beam_energy_gev", float),
    "SIM_BEAM_SPECIES": ("beam_species", str),
    "SIM_PARTICLES_PER_BUNCH": ("particles_per_bunch", int),
    "SIM_SIMULATION_STEPS": ("simulation_steps", int),
    "SIM_TIME_STEP_S": ("time_step_s", float),
    "SIM_COLLISION_RADIUS_M": ("collision_radius_m", float),
    "SIM_TRACKER_LAYERS": ("tracker_layers", int),
    "SIM_JET_RADIUS": ("jet_radius", float),
    "SIM_JET_MIN_PT_GEV": ("jet_min_pt_gev", float),
    "SIM_TRIGGER_MIN_ENERGY_GEV": ("trigger_min_energy_gev", float),
    "SIM_RANDOM_SEED": ("random_seed", int),
    "SIM_MAX_WORKERS": ("max_workers", int),
    "SIM_LOG_LEVEL": ("log_level", str),
    "SIM_STORAGE_DIR": ("storage_dir", str),
    "SIM_WEBSOCKET_HOST": ("websocket_host", str),
    "SIM_WEBSOCKET_PORT": ("websocket_port", int),
    "SIM_API_HOST": ("api_host", str),
    "SIM_API_PORT": ("api_port", int),
}


class EnvironmentConfig:
    """Read simulation configuration from environment variables.

    Environment variable names follow the pattern ``SIM_<PARAM_NAME>``
    (upper-cased).  For example, ``SIM_BEAM_ENERGY_GEV=13000.0`` sets
    ``beam_energy_gev`` to 13 TeV.

    Usage::

        env_cfg = EnvironmentConfig()
        overrides = env_cfg.load()
        # overrides contains only the env vars that are currently set.
    """

    def load(self) -> dict[str, Any]:
        """Read all recognised environment variables.

        Returns:
            Dict of ``{config_key: typed_value}`` for every env var
            that is currently set.  Unrecognised or unset env vars are
            silently ignored.
        """
        result: dict[str, Any] = {}
        for env_var, (cfg_key, converter) in _ENV_MAP.items():
            raw = os.environ.get(env_var)
            if raw is not None:
                try:
                    result[cfg_key] = converter(raw)
                except (ValueError, TypeError):
                    pass  # Skip malformed values gracefully.
        return result

    @staticmethod
    def get(env_var: str, default: Any = None) -> Any:
        """Read a single environment variable by its ``SIM_*`` name."""
        return os.environ.get(env_var, default)

    @staticmethod
    def list_recognised() -> list[str]:
        """Return all recognised ``SIM_*`` environment variable names."""
        return list(_ENV_MAP.keys())
