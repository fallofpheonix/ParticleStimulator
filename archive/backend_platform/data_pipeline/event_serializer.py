"""Event serializer — converts simulation events to JSON, Parquet, and HDF5 formats.

Supports multi-format serialization so that the data pipeline can persist
events in the format most appropriate for downstream consumers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EventSerializer:
    """Serializes simulation event dicts to multiple storage formats.

    Supported formats:
        - JSON  (.json)
        - Parquet (.parquet)  — requires pyarrow
        - HDF5  (.h5 / .hdf5) — requires h5py
    """

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    @staticmethod
    def to_json(events: list[dict[str, Any]], path: str | Path) -> Path:
        """Write *events* list to a JSON file.

        Args:
            events: list of event dicts to serialize.
            path: destination file path.

        Returns:
            Resolved Path of the written file.
        """
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w") as fh:
            json.dump(events, fh, indent=2, default=str)
        return dest

    @staticmethod
    def from_json(path: str | Path) -> list[dict[str, Any]]:
        """Load events from a JSON file."""
        with Path(path).open() as fh:
            return json.load(fh)

    # ------------------------------------------------------------------
    # Parquet
    # ------------------------------------------------------------------

    @staticmethod
    def to_parquet(events: list[dict[str, Any]], path: str | Path) -> Path:
        """Write *events* to a Parquet file using pyarrow.

        Nested dicts / lists are serialized to JSON strings so that the
        flat column schema remains valid.

        Args:
            events: list of event dicts.
            path: destination .parquet file path.

        Returns:
            Resolved Path of the written file.
        """
        try:
            import pyarrow as pa  # type: ignore
            import pyarrow.parquet as pq  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "pyarrow is required for Parquet serialization. "
                "Install it with: pip install pyarrow"
            ) from exc

        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Flatten nested values to JSON strings for schema compatibility.
        flat_events = [
            {k: (json.dumps(v, default=str) if isinstance(v, (dict, list)) else v)
             for k, v in event.items()}
            for event in events
        ]
        table = pa.Table.from_pylist(flat_events)
        pq.write_table(table, str(dest))
        return dest

    @staticmethod
    def from_parquet(path: str | Path) -> list[dict[str, Any]]:
        """Load events from a Parquet file."""
        try:
            import pyarrow.parquet as pq  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pyarrow is required.") from exc

        table = pq.read_table(str(path))
        return table.to_pylist()

    # ------------------------------------------------------------------
    # HDF5
    # ------------------------------------------------------------------

    @staticmethod
    def to_hdf5(events: list[dict[str, Any]], path: str | Path, dataset_name: str = "events") -> Path:
        """Write *events* to an HDF5 file.

        Each scalar value is stored as a separate dataset column under
        *dataset_name*.  Non-scalar values are serialized as UTF-8 JSON.

        Args:
            events: list of event dicts.
            path: destination .h5 file path.
            dataset_name: HDF5 group name to store events under.

        Returns:
            Resolved Path of the written file.
        """
        try:
            import h5py  # type: ignore
            import numpy as np  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "h5py and numpy are required for HDF5 serialization."
            ) from exc

        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if not events:
            # Write an empty group and return.
            with h5py.File(str(dest), "w") as hf:
                hf.create_group(dataset_name)
            return dest

        # Collect all keys across all events.
        all_keys: list[str] = list({k for e in events for k in e})

        with h5py.File(str(dest), "w") as hf:
            grp = hf.create_group(dataset_name)
            for key in all_keys:
                values = [e.get(key) for e in events]
                # Try to store as a numpy numeric array first.
                try:
                    arr = np.array(values, dtype=float)
                    grp.create_dataset(key, data=arr)
                except (TypeError, ValueError):
                    # Fall back to variable-length UTF-8 strings.
                    str_values = [json.dumps(v, default=str) for v in values]
                    dt = h5py.string_dtype(encoding="utf-8")
                    grp.create_dataset(key, data=str_values, dtype=dt)

        return dest

    @staticmethod
    def from_hdf5(path: str | Path, dataset_name: str = "events") -> list[dict[str, Any]]:
        """Load events from an HDF5 file.

        Args:
            path: source .h5 file path.
            dataset_name: HDF5 group name that was used when writing.
        """
        try:
            import h5py  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("h5py is required.") from exc

        with h5py.File(str(path), "r") as hf:
            grp = hf[dataset_name]
            keys = list(grp.keys())
            if not keys:
                return []
            n = len(grp[keys[0]])
            rows: list[dict[str, Any]] = [{} for _ in range(n)]
            for key in keys:
                for i, val in enumerate(grp[key][()]):
                    if isinstance(val, bytes):
                        val = val.decode("utf-8")
                    # Attempt to parse JSON-encoded complex values.
                    if isinstance(val, str):
                        try:
                            val = json.loads(val)
                        except (json.JSONDecodeError, ValueError):
                            pass
                    rows[i][key] = val
        return rows
