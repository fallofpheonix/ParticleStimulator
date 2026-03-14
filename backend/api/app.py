from __future__ import annotations

import random
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.data_pipeline.event_database import EventDatabase
from backend.data_pipeline.dataset_loader import DatasetLoader


class SimulateRequest(BaseModel):
    particles_per_bunch: int = 4
    simulation_steps: int = 50


class AnalysisRequest(BaseModel):
    analysis_type: str
    parameters: dict = {}


def create_app(storage_dir: str, datasets_dir: str) -> FastAPI:
    app = FastAPI()
    db = EventDatabase(storage_dir=storage_dir)
    datasets_path = Path(datasets_dir)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/events")
    def get_events(n: Optional[int] = None, event_id: Optional[int] = None):
        if event_id is not None:
            event = db.get_by_id(event_id)
            if event is None:
                raise HTTPException(status_code=404, detail="Event not found")
            return {"events": [event], "total": db.count}
        events = db.get_latest(n) if n is not None else db.get_latest(db.count)
        return {"events": events, "total": db.count}

    @app.get("/api/datasets")
    def list_datasets():
        files = DatasetLoader.list_datasets(datasets_path)
        return {"datasets": files, "total": len(files)}

    @app.get("/api/datasets/{filename}")
    def get_dataset(filename: str):
        path = datasets_path / filename
        if not path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")
        loader = DatasetLoader()
        try:
            data = loader.load(path)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"filename": filename, "records": data, "total": len(data)}

    @app.post("/api/simulate")
    def simulate(req: SimulateRequest):
        event_id = str(uuid.uuid4())
        jets = [
            {"pt_gev": round(random.uniform(20.0, 200.0), 2)}
            for _ in range(random.randint(0, 4))
        ]
        event = {
            "event_id": event_id,
            "triggered": random.random() > 0.3,
            "n_jets": len(jets),
            "jets": jets,
            "particles_per_bunch": req.particles_per_bunch,
            "simulation_steps": req.simulation_steps,
        }
        db.store(event)
        return {"event_id": event_id}

    @app.post("/api/analysis")
    def analysis(req: AnalysisRequest):
        if req.analysis_type not in ("significance", "histogram"):
            raise HTTPException(status_code=400, detail=f"Unknown analysis_type: {req.analysis_type!r}")

        events = db.get_latest(db.count)

        if req.analysis_type == "significance":
            if not events:
                return {"result": None}
            n_signal = sum(1 for e in events if e.get("triggered"))
            n_background = len(events) - n_signal
            significance = n_signal / max(n_background ** 0.5, 1.0)
            return {"result": {"n_signal": n_signal, "n_background": n_background, "significance": significance}}

        # histogram
        bins = req.parameters.get("bins", 10)
        low = req.parameters.get("low", 0.0)
        high = req.parameters.get("high", 100.0)
        pt_values = [jet["pt_gev"] for e in events for jet in e.get("jets", [])]
        counts = [0] * bins
        if pt_values:
            bin_width = (high - low) / bins
            for v in pt_values:
                idx = int((v - low) / bin_width)
                idx = max(0, min(bins - 1, idx))
                counts[idx] += 1
        return {"result": {"bins": bins, "counts": counts, "low": low, "high": high}}

    return app
