"""REST API routes for the simulation backend.

Provides HTTP endpoints for health checks, simulation defaults,
and triggering simulations.  Uses Python stdlib http.server when
FastAPI is not available.
"""

from __future__ import annotations
import json
from typing import Any


def create_routes() -> dict[str, Any]:
    """Return a route map for the REST API.

    Keys are URL paths, values are handler metadata.
    """
    return {
        "/api/health": {"method": "GET", "handler": health_check},
        "/api/defaults": {"method": "GET", "handler": get_defaults},
        "/api/simulate": {"method": "POST", "handler": run_simulation},
        "/api/events": {"method": "GET", "handler": list_events},
        "/api/config": {"method": "GET", "handler": get_config},
    }


def health_check() -> dict[str, Any]:
    return {"status": "ok", "service": "particle_simulator"}


def get_defaults() -> dict[str, Any]:
    from backend.infrastructure.config_manager import DEFAULT_CONFIG
    return DEFAULT_CONFIG


def run_simulation(params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Trigger a simulation run and return the event ID."""
    from backend.api_server.simulation_controller import SimulationController
    controller = SimulationController()
    if params:
        for k, v in params.items():
            controller.config.set(k, v)
    result = controller.run_full_pipeline()
    return result


def list_events() -> dict[str, Any]:
    return {"events": [], "total": 0}


def get_config() -> dict[str, Any]:
    from backend.infrastructure.config_manager import ConfigManager
    return ConfigManager().effective
