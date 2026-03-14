"""Histogram engine — flexible binned data accumulation and statistics."""

from __future__ import annotations
import math
from dataclasses import dataclass, field


@dataclass(slots=True)
class Histogram:
    """1D histogram with fixed-width bins."""
    name: str
    n_bins: int
    x_min: float
    x_max: float
    counts: list[int] = field(default_factory=list)
    weighted: list[float] = field(default_factory=list)
    overflow: int = 0
    underflow: int = 0
    total_entries: int = 0

    def __post_init__(self) -> None:
        if not self.counts:
            self.counts = [0] * self.n_bins
        if not self.weighted:
            self.weighted = [0.0] * self.n_bins

    @property
    def bin_width(self) -> float:
        return (self.x_max - self.x_min) / self.n_bins

    def fill(self, value: float, weight: float = 1.0) -> None:
        self.total_entries += 1
        if value < self.x_min:
            self.underflow += 1
            return
        if value >= self.x_max:
            self.overflow += 1
            return
        idx = int((value - self.x_min) / self.bin_width)
        idx = min(idx, self.n_bins - 1)
        self.counts[idx] += 1
        self.weighted[idx] += weight

    def bin_center(self, idx: int) -> float:
        return self.x_min + (idx + 0.5) * self.bin_width

    def mean(self) -> float:
        total_w = sum(self.weighted)
        if total_w <= 0:
            return 0.0
        return sum(self.bin_center(i) * self.weighted[i] for i in range(self.n_bins)) / total_w

    def max_bin(self) -> tuple[int, int]:
        """Return (bin_index, count) of the bin with most entries."""
        if not self.counts:
            return (0, 0)
        idx = max(range(self.n_bins), key=lambda i: self.counts[i])
        return (idx, self.counts[idx])

    def as_dict(self) -> dict:
        return {
            "name": self.name, "n_bins": self.n_bins,
            "x_min": self.x_min, "x_max": self.x_max,
            "counts": self.counts, "total_entries": self.total_entries,
        }


@dataclass(slots=True)
class HistogramEngine:
    """Manages a collection of named histograms."""

    histograms: dict[str, Histogram] = field(default_factory=dict)

    def create(self, name: str, n_bins: int, x_min: float, x_max: float) -> Histogram:
        h = Histogram(name=name, n_bins=n_bins, x_min=x_min, x_max=x_max)
        self.histograms[name] = h
        return h

    def fill(self, name: str, value: float, weight: float = 1.0) -> None:
        if name in self.histograms:
            self.histograms[name].fill(value, weight)

    def get(self, name: str) -> Histogram | None:
        return self.histograms.get(name)
