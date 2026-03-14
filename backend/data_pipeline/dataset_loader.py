from __future__ import annotations

import json
from pathlib import Path


class DatasetLoader:

    def load(self, path) -> list[dict]:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")
        suffix = path.suffix.lower()
        if suffix == ".json":
            return json.loads(path.read_text())
        if suffix == ".parquet":
            from backend.data_pipeline.event_serializer import EventSerializer
            return EventSerializer.from_parquet(path)
        raise ValueError(f"Unsupported file format: {suffix!r}")

    @staticmethod
    def list_datasets(directory) -> list[str]:
        directory = Path(directory)
        return [
            p.name
            for p in directory.iterdir()
            if p.suffix.lower() in {".json", ".parquet"}
        ]
