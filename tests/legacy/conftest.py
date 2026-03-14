"""pytest configuration for the legacy test suite.

Adds the archive/legacy_simulator directory to sys.path so that the legacy
test modules can import from the ``src`` package (e.g. ``src.core.particle``).
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

# archive/legacy_simulator contains the top-level ``src`` package used by the
# legacy tests.  Insert it at the front so it shadows the main project's
# ``src/`` directory.
_LEGACY_ROOT = Path(__file__).resolve().parents[2] / "archive" / "legacy_simulator"
_LEGACY_ROOT_STR = str(_LEGACY_ROOT)

if _LEGACY_ROOT_STR not in sys.path:
    sys.path.insert(0, _LEGACY_ROOT_STR)

# The main project also has a src/__init__.py which may already be cached in
# sys.modules as 'src'.  Evict it so the legacy archive's src package (at
# archive/legacy_simulator/src/) is used instead.
for key in list(sys.modules):
    if key == "src" or key.startswith("src."):
        del sys.modules[key]

# Pre-import the ``src`` and ``src.core`` packages now, while archive/
# legacy_simulator is guaranteed to be first in sys.path.  This populates
# sys.modules before pytest may rearrange the path during collection.
importlib.import_module("src")
importlib.import_module("src.core")
