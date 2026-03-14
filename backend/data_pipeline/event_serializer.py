from __future__ import annotations

import json
from pathlib import Path


class EventSerializer:

    @staticmethod
    def to_json(events: list[dict], path_str: str) -> Path:
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(events, default=str))
        return path

    @staticmethod
    def from_json(path) -> list[dict]:
        return json.loads(Path(path).read_text())

    @staticmethod
    def to_parquet(events: list[dict], path_str: str) -> Path:
        import pandas as pd
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Serialize each event as a JSON string to handle nested structures.
        rows = [{"_json": json.dumps(e, default=str)} for e in events]
        df = pd.DataFrame(rows)
        df.to_parquet(str(path), index=False)
        return path

    @staticmethod
    def from_parquet(path) -> list[dict]:
        import pandas as pd
        df = pd.read_parquet(str(path))
        return [json.loads(row["_json"]) for _, row in df.iterrows()]

    @staticmethod
    def to_hdf5(events: list[dict], path_str: str) -> Path:
        import h5py
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        with h5py.File(str(path), "w") as f:
            encoded = [json.dumps(e, default=str).encode("utf-8") for e in events]
            dt = h5py.special_dtype(vlen=bytes)
            ds = f.create_dataset("events", (len(encoded),), dtype=dt)
            for i, b in enumerate(encoded):
                ds[i] = b
        return path

    @staticmethod
    def from_hdf5(path) -> list[dict]:
        import h5py
        with h5py.File(str(path), "r") as f:
            ds = f["events"]
            return [json.loads(b.decode("utf-8") if isinstance(b, (bytes, bytearray)) else b) for b in ds[:]]
