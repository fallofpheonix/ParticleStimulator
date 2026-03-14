"""Configuration manager — centralised simulation parameters.

Loads experiment configuration from dicts or JSON files and provides
typed access to all simulation parameters with defaults.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "beam_energy_gev": 6500.0,
    "beam_species": "proton",
    "particles_per_bunch": 6,
    "simulation_steps": 500,
    "time_step_s": 1.0e-10,
    "collision_radius_m": 0.06,
    "tracker_layers": 5,
    "em_cal_bins_eta": 50,
    "em_cal_bins_phi": 64,
    "had_cal_bins_eta": 25,
    "had_cal_bins_phi": 32,
    "jet_radius": 0.4,
    "jet_min_pt_gev": 5.0,
    "trigger_min_energy_gev": 20.0,
    "random_seed": 42,
    "max_workers": 4,
}


@dataclass(slots=True)
class ConfigManager:
    """Central configuration store with defaults.

    Attributes:
        overrides: user-provided overrides on top of defaults.
    """

    overrides: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value (override → default → fallback)."""
        if key in self.overrides:
            return self.overrides[key]
        if key in DEFAULT_CONFIG:
            return DEFAULT_CONFIG[key]
        return default

    def set(self, key: str, value: Any) -> None:
        self.overrides[key] = value

    def load_json(self, path: str | Path) -> None:
        """Load overrides from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        self.overrides.update(data)

    def save_json(self, path: str | Path) -> None:
        """Save current effective config to JSON."""
        effective = {**DEFAULT_CONFIG, **self.overrides}
        with open(path, "w") as f:
            json.dump(effective, f, indent=2)

    @property
    def effective(self) -> dict[str, Any]:
        return {**DEFAULT_CONFIG, **self.overrides}
