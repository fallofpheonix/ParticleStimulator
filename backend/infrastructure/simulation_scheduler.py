"""Simulation scheduler — job queue and dispatch for simulation workloads."""

from __future__ import annotations
import time
import itertools
from dataclasses import dataclass, field
from typing import Any, Callable


_job_ids = itertools.count(1)


@dataclass(slots=True)
class SimulationJob:
    """A scheduled simulation job."""
    job_id: int
    name: str
    config: dict[str, Any]
    status: str = "queued"
    result: Any = None
    submitted_at: float = 0.0
    completed_at: float = 0.0


@dataclass(slots=True)
class SimulationScheduler:
    """Manages a queue of simulation jobs.

    Attributes:
        max_concurrent: maximum concurrent jobs.
    """

    max_concurrent: int = 4
    _queue: list[SimulationJob] = field(default_factory=list, repr=False)
    _completed: list[SimulationJob] = field(default_factory=list, repr=False)

    def submit(self, name: str, config: dict[str, Any] | None = None) -> SimulationJob:
        """Submit a new simulation job."""
        job = SimulationJob(
            job_id=next(_job_ids),
            name=name,
            config=config or {},
            submitted_at=time.time(),
        )
        self._queue.append(job)
        return job

    def next_job(self) -> SimulationJob | None:
        """Pop the next queued job."""
        for job in self._queue:
            if job.status == "queued":
                job.status = "running"
                return job
        return None

    def complete_job(self, job: SimulationJob, result: Any = None) -> None:
        """Mark a job as completed."""
        job.status = "completed"
        job.result = result
        job.completed_at = time.time()
        self._completed.append(job)

    @property
    def pending_count(self) -> int:
        return sum(1 for j in self._queue if j.status == "queued")

    @property
    def completed_count(self) -> int:
        return len(self._completed)

    def run_all(self, runner: Callable[[SimulationJob], Any]) -> list[SimulationJob]:
        """Execute all queued jobs sequentially."""
        results = []
        while True:
            job = self.next_job()
            if job is None:
                break
            result = runner(job)
            self.complete_job(job, result)
            results.append(job)
        return results
