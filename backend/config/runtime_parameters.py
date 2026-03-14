from __future__ import annotations


_SCHEMA: dict[str, type] = {
    "max_workers": int,
    "beam_energy_gev": float,
    "random_seed": int,
}


class RuntimeParameters:
    def __init__(self, strict: bool = False):
        self._strict = strict
        self._params: dict = {}

    def set(self, key: str, value) -> None:
        if self._strict and key not in _SCHEMA:
            raise KeyError(f"Unknown parameter: {key!r}")
        if key in _SCHEMA:
            expected = _SCHEMA[key]
            if not isinstance(value, expected):
                raise TypeError(
                    f"Parameter {key!r} expects {expected.__name__}, got {type(value).__name__}"
                )
        self._params[key] = value

    def get(self, key: str, default=None):
        return self._params.get(key, default)

    def update(self, mapping: dict) -> None:
        for k, v in mapping.items():
            self.set(k, v)

    def delete(self, key: str) -> None:
        self._params.pop(key, None)

    def clear(self) -> None:
        self._params.clear()

    @property
    def all(self) -> dict:
        return dict(self._params)

    @staticmethod
    def schema() -> dict:
        return dict(_SCHEMA)
