"""Job queue — priority-aware task queue for simulation jobs.

Extends the basic FIFO ``SimulationScheduler`` with priority levels
and named queues so that high-priority analysis jobs can jump ahead
of background batch runs.
"""

from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass, field
from typing import Any


_counter = itertools.count()


@dataclass(order=True)
class _QueueEntry:
    """Internal heap entry.  ``priority`` is negated so that larger
    priority values are popped first (max-heap via min-heap)."""

    priority: int
    seq: int
    job_id: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False)


@dataclass
class JobQueue:
    """Priority job queue for simulation workloads.

    Jobs with higher *priority* values are dequeued first.  Jobs of
    equal priority are served in FIFO order.

    Attributes:
        default_priority: priority assigned when none is specified.
    """

    default_priority: int = 0

    _heap: list[_QueueEntry] = field(default_factory=list, repr=False, init=False)
    _all_jobs: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False, init=False)

    # ------------------------------------------------------------------
    # Enqueue
    # ------------------------------------------------------------------

    def enqueue(
        self,
        job_id: str,
        payload: dict[str, Any],
        priority: int | None = None,
    ) -> str:
        """Add a job to the queue.

        Args:
            job_id: unique identifier for this job.
            payload: arbitrary job data (config, params, etc.).
            priority: scheduling priority (higher → sooner).  Defaults
                      to ``default_priority``.

        Returns:
            The *job_id* that was enqueued.
        """
        p = priority if priority is not None else self.default_priority
        entry = _QueueEntry(
            priority=-p,  # negate for max-heap behaviour
            seq=next(_counter),
            job_id=job_id,
            payload={**payload, "_enqueued_at": time.time(), "_priority": p},
        )
        heapq.heappush(self._heap, entry)
        self._all_jobs[job_id] = entry.payload
        return job_id

    # ------------------------------------------------------------------
    # Dequeue
    # ------------------------------------------------------------------

    def dequeue(self) -> dict[str, Any] | None:
        """Pop and return the highest-priority job, or None if empty."""
        while self._heap:
            entry = heapq.heappop(self._heap)
            return {"job_id": entry.job_id, **entry.payload}
        return None

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Number of jobs currently waiting in the queue."""
        return len(self._heap)

    @property
    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def peek(self) -> dict[str, Any] | None:
        """Return the next job without removing it, or None if empty."""
        if not self._heap:
            return None
        entry = self._heap[0]
        return {"job_id": entry.job_id, **entry.payload}

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Look up a job by ID (regardless of queue position)."""
        return self._all_jobs.get(job_id)

    def drain(self) -> list[dict[str, Any]]:
        """Dequeue all jobs and return them in priority order."""
        jobs = []
        while not self.is_empty:
            job = self.dequeue()
            if job:
                jobs.append(job)
        return jobs

    def clear(self) -> None:
        """Discard all pending jobs."""
        self._heap.clear()
