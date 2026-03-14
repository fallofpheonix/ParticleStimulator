"""Dataset loader — loads physics datasets from JSON, Parquet, and HDF5 files.

Provides a unified interface for reading pre-generated or external
particle physics datasets into memory for use by the analysis pipeline
and machine-learning modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DatasetLoader:
    """Load simulation datasets from various storage formats.

    Supported formats:
        - JSON  (.json)
        - Parquet (.parquet) — requires pyarrow
        - HDF5  (.h5 / .hdf5) — requires h5py
        - CSV   (.csv)       — requires pandas or stdlib csv
    """

    # ------------------------------------------------------------------
    # Format dispatch
    # ------------------------------------------------------------------

    def load(self, path: str | Path) -> list[dict[str, Any]]:
        """Load a dataset from *path*, auto-detecting the format.

        Args:
            path: path to the dataset file.

        Returns:
            List of record dicts.

        Raises:
            ValueError: if the file extension is not recognised.
            FileNotFoundError: if the path does not exist.
        """
        src = Path(path)
        if not src.exists():
            raise FileNotFoundError(f"Dataset not found: {src}")

        suffix = src.suffix.lower()
        if suffix == ".json":
            return self.load_json(src)
        if suffix == ".parquet":
            return self.load_parquet(src)
        if suffix in {".h5", ".hdf5"}:
            return self.load_hdf5(src)
        if suffix == ".csv":
            return self.load_csv(src)
        raise ValueError(f"Unsupported dataset format: {suffix!r}")

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    @staticmethod
    def load_json(path: str | Path) -> list[dict[str, Any]]:
        """Load records from a JSON file (list of objects)."""
        with Path(path).open() as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            # Support top-level {records: [...]} envelope.
            return data.get("records", data.get("events", [data]))
        return data

    # ------------------------------------------------------------------
    # Parquet
    # ------------------------------------------------------------------

    @staticmethod
    def load_parquet(path: str | Path) -> list[dict[str, Any]]:
        """Load records from a Parquet file using pyarrow."""
        try:
            import pyarrow.parquet as pq  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pyarrow is required: pip install pyarrow") from exc
        table = pq.read_table(str(path))
        return table.to_pylist()

    # ------------------------------------------------------------------
    # HDF5
    # ------------------------------------------------------------------

    @staticmethod
    def load_hdf5(path: str | Path, dataset_name: str = "events") -> list[dict[str, Any]]:
        """Load records from an HDF5 file.

        Args:
            path: path to the .h5 file.
            dataset_name: HDF5 group name containing the columns.
        """
        try:
            import h5py  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("h5py is required: pip install h5py") from exc

        with h5py.File(str(path), "r") as hf:
            if dataset_name not in hf:
                # Try to load the first group as a fallback.
                keys = list(hf.keys())
                if not keys:
                    return []
                dataset_name = keys[0]
            grp = hf[dataset_name]
            col_keys = list(grp.keys())
            if not col_keys:
                return []
            n = len(grp[col_keys[0]])
            rows: list[dict[str, Any]] = [{} for _ in range(n)]
            for col in col_keys:
                for i, val in enumerate(grp[col][()]):
                    if isinstance(val, bytes):
                        val = val.decode("utf-8")
                    if isinstance(val, str):
                        try:
                            val = json.loads(val)
                        except (json.JSONDecodeError, ValueError):
                            pass
                    rows[i][col] = val
        return rows

    # ------------------------------------------------------------------
    # CSV
    # ------------------------------------------------------------------

    @staticmethod
    def load_csv(path: str | Path) -> list[dict[str, Any]]:
        """Load records from a CSV file.

        Attempts to use pandas for efficient loading; falls back to the
        stdlib ``csv`` module if pandas is not available.
        """
        try:
            import pandas as pd  # type: ignore
            return pd.read_csv(str(path)).to_dict(orient="records")
        except ImportError:
            pass

        import csv
        with Path(path).open(newline="") as fh:
            reader = csv.DictReader(fh)
            return [dict(row) for row in reader]

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def list_datasets(directory: str | Path) -> list[str]:
        """Return all supported dataset files in *directory*."""
        extensions = {".json", ".parquet", ".h5", ".hdf5", ".csv"}
        return [
            p.name
            for p in sorted(Path(directory).iterdir())
            if p.is_file() and p.suffix.lower() in extensions
        ]
