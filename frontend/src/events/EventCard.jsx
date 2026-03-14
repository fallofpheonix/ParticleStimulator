import { memo, useMemo } from "react";

import { useSimulationStore } from "@store/simulationStore";

import { particleColor } from "./colors.js";

const EventCard = memo(function EventCard({ event }) {
  const selectedEventId = useSimulationStore((state) => state.eventStream.selectedEventId);
  const selectEvent = useSimulationStore((state) => state.selectEvent);
  const typeSet = useMemo(() => [...new Set((event.particles ?? []).map((particle) => particle.type))], [event]);
  const isSelected = selectedEventId === event.event_id;
  const energyTev = ((event.collision_energy ?? 0) / 1000).toFixed(1);

  return (
    <button
      type="button"
      className={`event-card ${isSelected ? "event-card--selected" : ""}`}
      onClick={() => selectEvent(event.event_id)}
    >
      <div className="card-row">
        <span className="eid">#{String(event.event_id).padStart(6, "0")}</span>
        <span className="energy-badge">{energyTev} TeV</span>
        <span className="particle-count">{(event.particles ?? []).length}p</span>
      </div>
      <div className="type-dots">
        {typeSet.slice(0, 5).map((type) => (
          <span key={type} className="type-dot" style={{ background: particleColor(type) }} title={type} />
        ))}
      </div>
    </button>
  );
});

export default EventCard;
