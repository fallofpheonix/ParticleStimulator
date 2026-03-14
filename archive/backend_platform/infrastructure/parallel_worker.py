"""Parallel worker — executes simulation jobs concurrently.

Builds on ``DistributedExecutor`` to provide a higher-level worker pool
that integrates with ``JobQueue`` and reports results back to the
caller via a callback or result list.
"""

from __future__ import annotations

import concurrent.futures
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from backend.infrastructure.job_queue import JobQueue


@dataclass
class WorkerResult:
    """Holds the outcome of a single parallel job execution."""

    job_id: str
    success: bool
    result: Any = None
    error: str | None = None
    duration_s: float = 0.0


@dataclass
class ParallelWorker:
    """Executes jobs from a ``JobQueue`` using a thread pool.

    Attributes:
        max_workers: number of concurrent worker threads.
        use_processes: use ``ProcessPoolExecutor`` instead of threads.
    """

    max_workers: int = 4
    use_processes: bool = False

    _results: list[WorkerResult] = field(default_factory=list, repr=False, init=False)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_job(
        self,
        job_id: str,
        payload: dict[str, Any],
        runner: Callable[[dict[str, Any]], Any],
    ) -> WorkerResult:
        """Execute a single job synchronously.

        Args:
            job_id: unique job identifier.
            payload: job payload forwarded to *runner*.
            runner: callable that accepts the payload and returns a result.

        Returns:
            ``WorkerResult`` with execution details.
        """
        t0 = time.monotonic()
        try:
            result = runner(payload)
            return WorkerResult(
                job_id=job_id,
                success=True,
                result=result,
                duration_s=time.monotonic() - t0,
            )
        except Exception as exc:  # noqa: BLE001
            return WorkerResult(
                job_id=job_id,
                success=False,
                error=str(exc),
                duration_s=time.monotonic() - t0,
            )

    def run_queue(
        self,
        queue: JobQueue,
        runner: Callable[[dict[str, Any]], Any],
        on_result: Callable[[WorkerResult], None] | None = None,
    ) -> list[WorkerResult]:
        """Drain *queue* and execute all jobs in parallel.

        Args:
            queue: job queue to drain.
            runner: callable invoked for each job payload.
            on_result: optional callback invoked after each job completes.

        Returns:
            List of ``WorkerResult`` objects, one per job.
        """
        jobs = queue.drain()
        if not jobs:
            return []

        Executor = (
            concurrent.futures.ProcessPoolExecutor
            if self.use_processes
            else concurrent.futures.ThreadPoolExecutor
        )

        results: list[WorkerResult] = []
        with Executor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(self.run_job, job["job_id"], job, runner): job["job_id"]
                for job in jobs
            }
            for future in concurrent.futures.as_completed(futures):
                wr = future.result()
                self._results.append(wr)
                results.append(wr)
                if on_result:
                    on_result(wr)

        return results

    def run_batch(
        self,
        items: list[Any],
        runner: Callable[[Any], Any],
    ) -> list[WorkerResult]:
        """Execute *runner* on each item in *items* in parallel.

        Args:
            items: arbitrary list of inputs.
            runner: callable accepting one item and returning a result.

        Returns:
            List of ``WorkerResult`` objects in completion order.
        """
        Executor = (
            concurrent.futures.ProcessPoolExecutor
            if self.use_processes
            else concurrent.futures.ThreadPoolExecutor
        )

        results: list[WorkerResult] = []
        with Executor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(runner, item): str(i)
                for i, item in enumerate(items)
            }
            for future in concurrent.futures.as_completed(futures):
                job_id = futures[future]
                t0 = time.monotonic()
                try:
                    result = future.result()
                    wr = WorkerResult(job_id=job_id, success=True, result=result)
                except Exception as exc:  # noqa: BLE001
                    wr = WorkerResult(job_id=job_id, success=False, error=str(exc))
                wr.duration_s = time.monotonic() - t0
                self._results.append(wr)
                results.append(wr)

        return results

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    @property
    def completed_results(self) -> list[WorkerResult]:
        """Return all results from previous ``run_queue`` / ``run_batch`` calls."""
        return list(self._results)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self._results if r.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self._results if not r.success)
