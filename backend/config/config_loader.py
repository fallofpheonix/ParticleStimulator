from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


_DEFAULTS = {
    "beam_energy_gev": 6500.0,
    "max_workers": 4,
    "random_seed": 42,
}


class ConfigLoader:
    def __init__(self, path: Optional[Path] = None):
        self._path = Path(path) if path else None

    def load(self) -> dict:
        cfg = dict(_DEFAULTS)
        if self._path and self._path.exists():
            overrides = json.loads(self._path.read_text())
            cfg.update(overrides)
        return cfg

    def save_defaults(self, dest: Path) -> None:
        dest = Path(dest)
        dest.write_text(json.dumps(_DEFAULTS, indent=2))
