from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, NamedTuple, Optional

from backend.infrastructure.job_queue import JobQueue


class WorkerResult(NamedTuple):
    success: bool
    result: Any
    error: Optional[str]


class ParallelWorker:
    def __init__(self, max_workers: int = 4):
        self._max_workers = max_workers
        self._success_count = 0
        self._failure_count = 0

    def run_batch(self, items, fn: Callable) -> list[WorkerResult]:
        results: list[WorkerResult] = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [(item, executor.submit(fn, item)) for item in items]
            for _item, future in futures:
                exc = future.exception()
                if exc is not None:
                    results.append(WorkerResult(success=False, result=None, error=str(exc)))
                    self._failure_count += 1
                else:
                    results.append(WorkerResult(success=True, result=future.result(), error=None))
                    self._success_count += 1
        return results

    def run_queue(self, q: JobQueue, fn: Callable) -> list[WorkerResult]:
        jobs = q.drain()
        return self.run_batch([j for j in jobs], lambda job: fn(job))

    @property
    def success_count(self) -> int:
        return self._success_count

    @property
    def failure_count(self) -> int:
        return self._failure_count
