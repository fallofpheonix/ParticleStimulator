from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from web.server import ParticleStimulatorHandler, main


__all__ = ["ParticleStimulatorHandler", "main"]


if __name__ == "__main__":
    main()
