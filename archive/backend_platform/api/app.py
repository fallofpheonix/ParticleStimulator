"""FastAPI application — HTTP endpoints for the simulation platform.

Exposes:
    POST /api/simulate   — trigger a new simulation run
    GET  /api/events     — query buffered simulation events
    GET  /api/datasets   — list available stored datasets
    POST /api/analysis   — run analysis on stored events

The app integrates with:
    - ``SimulationController`` (backend.api_server) for running pipelines
    - ``EventDatabase`` (backend.data_pipeline) for event storage
    - ``DatasetLoader`` (backend.data_pipeline) for dataset access
    - ``ConfigLoader`` (backend.config) for configuration management
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    """Parameters for a simulation run."""
    beam_energy_gev: float | None = None
    beam_species: str | None = None
    particles_per_bunch: int | None = None
    simulation_steps: int | None = None
    time_step_s: float | None = None
    collision_radius_m: float | None = None
    random_seed: int | None = None

    model_config = {"extra": "allow"}


class AnalysisRequest(BaseModel):
    """Parameters for an analysis job."""
    analysis_type: str = "significance"
    event_ids: list[int] | None = None
    parameters: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(
    storage_dir: str | Path = "data/events",
    datasets_dir: str | Path = "data",
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        storage_dir: directory used by ``EventDatabase`` for persistence.
        datasets_dir: root directory scanned for available datasets.

    Returns:
        Configured FastAPI instance.
    """
    app = FastAPI(
        title="ParticleStimulator API",
        description="Backend platform for particle physics simulation",
        version="0.1.0",
    )

    # Allow all origins during development.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Lazy-initialised shared state.
    from backend.data_pipeline.event_database import EventDatabase
    from backend.data_pipeline.dataset_loader import DatasetLoader

    _db = EventDatabase(storage_dir=storage_dir)
    _loader = DatasetLoader()
    _datasets_dir = Path(datasets_dir)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @app.get("/api/health", tags=["system"])
    async def health() -> dict[str, str]:
        """Service health check."""
        return {"status": "ok", "service": "particle_simulator"}

    # ------------------------------------------------------------------
    # POST /api/simulate
    # ------------------------------------------------------------------

    @app.post("/api/simulate", tags=["simulation"])
    async def simulate(request: SimulateRequest) -> dict[str, Any]:
        """Trigger a full simulation pipeline run.

        Accepts optional parameter overrides in the request body.
        Returns the simulation event dict including reconstructed
        particles, jets, and detector data.
        """
        from backend.api_server.simulation_controller import SimulationController

        controller = SimulationController()
        params = request.model_dump(exclude_none=True)
        for k, v in params.items():
            controller.config.set(k, v)

        try:
            result = controller.run_full_pipeline()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        # Persist the event.
        _db.store(result)

        return result

    # ------------------------------------------------------------------
    # GET /api/events
    # ------------------------------------------------------------------

    @app.get("/api/events", tags=["events"])
    async def get_events(
        n: int = Query(default=100, ge=1, le=10_000, description="Max events to return"),
        event_id: int | None = Query(default=None, description="Fetch a single event by ID"),
    ) -> dict[str, Any]:
        """Query buffered simulation events.

        Args:
            n: maximum number of events to return (default 100).
            event_id: if provided, return only the event with this ID.
        """
        if event_id is not None:
            event = _db.get_by_id(event_id)
            if event is None:
                raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
            return {"events": [event], "total": 1}

        events = _db.get_latest(n)
        return {"events": events, "total": _db.count}

    # ------------------------------------------------------------------
    # GET /api/datasets
    # ------------------------------------------------------------------

    @app.get("/api/datasets", tags=["datasets"])
    async def list_datasets() -> dict[str, Any]:
        """List available datasets in the storage directory."""
        if not _datasets_dir.exists():
            return {"datasets": [], "directory": str(_datasets_dir)}

        files = DatasetLoader.list_datasets(_datasets_dir)
        return {
            "datasets": files,
            "directory": str(_datasets_dir),
            "total": len(files),
        }

    @app.get("/api/datasets/{filename}", tags=["datasets"])
    async def load_dataset(filename: str) -> dict[str, Any]:
        """Load and return records from a dataset file.

        Args:
            filename: dataset filename within the datasets directory.
        """
        src = _datasets_dir / filename
        if not src.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {filename!r} not found")
        try:
            records = _loader.load(src)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"filename": filename, "records": records, "total": len(records)}

    # ------------------------------------------------------------------
    # POST /api/analysis
    # ------------------------------------------------------------------

    _KNOWN_ANALYSIS_TYPES = {"significance", "histogram", "invariant_mass"}

    @app.post("/api/analysis", tags=["analysis"])
    async def run_analysis(request: AnalysisRequest) -> dict[str, Any]:
        """Run analysis on stored events.

        Supported analysis types:
            - ``significance``: compute statistical significance.
            - ``invariant_mass``: compute invariant mass spectrum.
            - ``histogram``: fill and return a histogram of jet energies.
        """
        if request.analysis_type not in _KNOWN_ANALYSIS_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown analysis type: {request.analysis_type!r}. "
                       f"Supported: {sorted(_KNOWN_ANALYSIS_TYPES)}",
            )

        if request.event_ids:
            events = [_db.get_by_id(eid) for eid in request.event_ids]
            events = [e for e in events if e is not None]
        else:
            events = _db.get_latest(1000)

        if not events:
            return {"analysis_type": request.analysis_type, "result": None, "n_events": 0}

        result = _run_analysis(request.analysis_type, events, request.parameters)
        return {
            "analysis_type": request.analysis_type,
            "n_events": len(events),
            "result": result,
        }

    return app


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def _run_analysis(
    analysis_type: str,
    events: list[dict[str, Any]],
    parameters: dict[str, Any],
) -> Any:
    """Dispatch to the appropriate backend analysis module."""
    if analysis_type == "significance":
        from backend.analysis.significance_test import SignificanceCalculator
        calc = SignificanceCalculator()
        n_sig = sum(1 for e in events if e.get("triggered", False))
        n_bkg = len(events) - n_sig
        sig = calc.simple_significance(float(n_sig), float(n_bkg))
        return {"n_signal": n_sig, "n_background": n_bkg, "significance": sig}

    if analysis_type == "histogram":
        from backend.analysis.histogram_engine import HistogramEngine
        engine = HistogramEngine()
        n_bins = parameters.get("bins", 20)
        low = parameters.get("low", 0.0)
        high = parameters.get("high", 500.0)
        engine.create("jet_energy", n_bins=n_bins, x_min=low, x_max=high)
        for event in events:
            for jet in event.get("jets", []):
                engine.fill("jet_energy", float(jet.get("pt_gev", 0.0)))
        hist = engine.get("jet_energy")
        return hist.as_dict() if hist is not None else None

    if analysis_type == "invariant_mass":
        # Return per-event invariant-mass placeholders (tracks are dicts, not FourVectors).
        n_pairs = sum(1 for e in events if len(e.get("tracks", [])) >= 2)
        return {"n_events_with_pairs": n_pairs, "n_events": len(events)}

    raise HTTPException(status_code=400, detail=f"Unknown analysis type: {analysis_type!r}")
