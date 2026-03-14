from __future__ import annotations

from dataclasses import asdict
import json

from src.detectors.calorimeter import EnergyDeposit
from src.detectors.tracker import TrackerHit
from src.physics.collisions import CollisionEvent


class EventLogger:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def log_collision(self, event: CollisionEvent) -> None:
        self.records.append(
            {
                "type": "collision",
                "event_id": event.event_id,
                "time_s": event.time_s,
                "position": event.position.as_tuple(),
                "incoming_ids": event.incoming_ids,
                "invariant_mass_gev": event.invariant_mass_gev,
                "product_species": [particle.species for particle in event.products],
            }
        )

    def log_tracker_hits(self, hits: list[TrackerHit]) -> None:
        for hit in hits:
            payload = asdict(hit)
            payload["position"] = hit.position.as_tuple()
            payload["type"] = "tracker_hit"
            self.records.append(payload)

    def log_calorimeter_hits(self, deposits: list[EnergyDeposit]) -> None:
        for deposit in deposits:
            payload = asdict(deposit)
            payload["type"] = "calorimeter"
            self.records.append(payload)

    def to_json(self) -> str:
        return json.dumps(self.records, indent=2, sort_keys=True)
