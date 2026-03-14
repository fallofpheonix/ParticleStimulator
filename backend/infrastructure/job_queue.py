from __future__ import annotations

import heapq
from typing import Optional


class JobQueue:
    def __init__(self):
        self._heap: list = []
        self._counter = 0

    def enqueue(self, job_id: str, payload: dict, priority: int = 0) -> None:
        # Use negative priority so that higher numbers come out first (max-heap via min-heap).
        heapq.heappush(self._heap, (-priority, self._counter, job_id, payload))
        self._counter += 1

    def dequeue(self) -> Optional[dict]:
        if not self._heap:
            return None
        _, _, job_id, payload = heapq.heappop(self._heap)
        return {"job_id": job_id, **payload}

    @property
    def is_empty(self) -> bool:
        return len(self._heap) == 0

    @property
    def size(self) -> int:
        return len(self._heap)

    def drain(self) -> list[dict]:
        jobs = []
        while not self.is_empty:
            jobs.append(self.dequeue())
        return jobs
