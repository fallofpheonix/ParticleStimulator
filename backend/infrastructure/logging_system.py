"""Structured logging system for the simulation backend."""

from __future__ import annotations
import logging
import sys
from dataclasses import dataclass


@dataclass(slots=True)
class SimulationLogger:
    """Configures and provides structured logging for the simulator.

    Attributes:
        name: logger name.
        level: logging level string.
        log_file: optional file path for persistent logs.
    """

    name: str = "particle_simulator"
    level: str = "INFO"
    log_file: str | None = None

    def get_logger(self) -> logging.Logger:
        """Create and configure a logger."""
        logger = logging.getLogger(self.name)
        if logger.handlers:
            return logger

        logger.setLevel(getattr(logging, self.level.upper(), logging.INFO))

        fmt = logging.Formatter(
            "[%(asctime)s] %(name)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(fmt)
        logger.addHandler(console)

        if self.log_file:
            fh = logging.FileHandler(self.log_file)
            fh.setFormatter(fmt)
            logger.addHandler(fh)

        return logger
