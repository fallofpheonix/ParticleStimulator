"""Dataset loader — loads physics datasets for ML training."""

from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DatasetLoader:
    """Loads event datasets from CSV/JSON files for ML training."""

    def load_csv(self, path: str | Path, max_rows: int | None = None) -> list[dict[str, float]]:
        """Load a CSV file where the first row is headers."""
        rows: list[dict[str, float]] = []
        with open(path) as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if max_rows and i >= max_rows:
                    break
                rows.append({k: float(v) for k, v in row.items()})
        return rows

    def load_simulation_events(self, events: list[dict[str, Any]]) -> list[dict[str, float]]:
        """Convert raw simulation events to flat feature vectors."""
        features = []
        for e in events:
            features.append({
                "n_jets": float(e.get("n_jets", 0)),
                "met_gev": float(e.get("met_gev", 0)),
                "n_tracks": float(e.get("n_tracks", 0)),
                "n_muons": float(e.get("n_muon_hits", 0)),
                "n_em_deposits": float(e.get("n_em_deposits", 0)),
                "label": float(e.get("label", 0)),
            })
        return features
