"""Config loader — reads configuration from JSON or YAML files.

Wraps ``ConfigManager`` from ``backend.infrastructure`` and adds
file-discovery logic so the system can locate config files in
standard locations automatically.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from backend.infrastructure.config_manager import ConfigManager, DEFAULT_CONFIG


# Standard locations to search for a config file, in priority order.
_DEFAULT_SEARCH_PATHS = [
    Path("config/simulation.json"),
    Path("config/settings.json"),
    Path("backend/config/defaults.json"),
]


class ConfigLoader:
    """Discover and load simulation configuration files.

    Priority order:
    1. Explicit *path* argument.
    2. ``PARTICLE_SIM_CONFIG`` environment variable.
    3. Well-known default file locations (see ``_DEFAULT_SEARCH_PATHS``).
    4. Built-in defaults from ``ConfigManager``.

    Args:
        path: explicit path to a JSON config file (optional).
        base_dir: root directory used to resolve relative paths.
    """

    def __init__(
        self,
        path: str | Path | None = None,
        base_dir: str | Path | None = None,
    ) -> None:
        self._base_dir = Path(base_dir) if base_dir else Path.cwd()
        self._path: Path | None = None

        if path:
            self._path = Path(path)
        else:
            env_path = os.environ.get("PARTICLE_SIM_CONFIG")
            if env_path:
                self._path = Path(env_path)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def find_config_file(self) -> Path | None:
        """Return the first existing config file, or None."""
        if self._path and self._path.exists():
            return self._path
        for relative in _DEFAULT_SEARCH_PATHS:
            candidate = self._base_dir / relative
            if candidate.exists():
                return candidate
        return None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> dict[str, Any]:
        """Load configuration, merging file overrides onto defaults.

        Returns:
            Effective configuration dict (defaults + any file overrides).
        """
        cfg = ConfigManager()
        config_file = self.find_config_file()
        if config_file:
            cfg.load_json(config_file)
        return cfg.effective

    def load_raw(self, path: str | Path) -> dict[str, Any]:
        """Load a raw JSON config file without merging with defaults."""
        with Path(path).open() as fh:
            return json.load(fh)

    def save_defaults(self, path: str | Path) -> Path:
        """Write the default configuration to *path* for reference."""
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w") as fh:
            json.dump(DEFAULT_CONFIG, fh, indent=2)
        return dest
