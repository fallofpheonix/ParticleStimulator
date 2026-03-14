"""Distributed executor — parallel simulation across multiple workers."""

from __future__ import annotations
import concurrent.futures
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True)
class DistributedExecutor:
    """Thread/process pool executor for parallel Monte Carlo events.

    Attributes:
        max_workers: number of concurrent workers.
        use_processes: use ProcessPoolExecutor if True, else ThreadPool.
    """

    max_workers: int = 4
    use_processes: bool = False

    def map(self, func: Callable[..., Any], items: list[Any]) -> list[Any]:
        """Execute func on each item in parallel, return results."""
        Executor = (
            concurrent.futures.ProcessPoolExecutor
            if self.use_processes
            else concurrent.futures.ThreadPoolExecutor
        )
        with Executor(max_workers=self.max_workers) as pool:
            return list(pool.map(func, items))

    def submit_batch(self, func: Callable[..., Any], configs: list[dict]) -> list[Any]:
        """Submit a batch of jobs with config dicts."""
        return self.map(lambda cfg: func(**cfg), configs)
