from __future__ import annotations

import os


_ENV_MAP: dict[str, tuple[str, type]] = {
    "SIM_BEAM_ENERGY_GEV": ("beam_energy_gev", float),
    "SIM_MAX_WORKERS": ("max_workers", int),
}


class EnvironmentConfig:

    def load(self) -> dict:
        result = {}
        for env_var, (key, cast) in _ENV_MAP.items():
            val = os.environ.get(env_var)
            if val is not None:
                result[key] = cast(val)
        return result

    @staticmethod
    def list_recognised() -> list[str]:
        return list(_ENV_MAP.keys())
