import { memo, useMemo } from "react";

import { selectSelectedEvent } from "@app/selectors";
import { useSimulationStore } from "@store/simulationStore";

import CollisionSummary from "./CollisionSummary.jsx";
import EventCard from "./EventCard.jsx";
import ParticleList from "./ParticleList.jsx";

const EventStream = memo(function EventStream() {
  const rawEvents = useSimulationStore((state) => state.eventStream.events);
  const filters = useSimulationStore((state) => state.eventStream.filters);
  const setEventFilter = useSimulationStore((state) => state.setEventFilter);
  const selectedEvent = useSimulationStore(selectSelectedEvent);

  const events = useMemo(() => {
    let filtered = rawEvents;
    if (filters.query) {
      const query = filters.query.toLowerCase();
      filtered = filtered.filter(
        (event) =>
          String(event.event_id).toLowerCase().includes(query) ||
          (event.particles ?? []).some((particle) =>
            (particle.type ?? "").toLowerCase().includes(query)
          )
      );
    }
    if (filters.type && filters.type !== "all") {
      filtered = filtered.filter((event) =>
        (event.particles ?? []).some((particle) => particle.type === filters.type)
      );
    }
    return filtered;
  }, [rawEvents, filters]);

  const particleTypes = useMemo(
    () =>
      [...new Set(rawEvents.flatMap((event) => (event.particles ?? []).map((particle) => particle.type)))].sort(),
    [rawEvents]
  );

  return (
    <>
      <div className="panel-header">
        <h2>Event Stream</h2>
        <p>Normalized collision stream feeding renderer, analytics, and replay</p>
      </div>
      <div className="stream-toolbar">
        <input
          type="search"
          placeholder="Search event id or particle"
          value={filters.query}
          onChange={(event) => setEventFilter("query", event.target.value)}
        />
        <select value={filters.type} onChange={(event) => setEventFilter("type", event.target.value)}>
          <option value="all">all types</option>
          {particleTypes.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>
      <div className="event-stream-list">
        {events.length ? events.map((event) => <EventCard key={event.event_id} event={event} />) : <div className="empty-state">No events yet.</div>}
      </div>
      <section className="subpanel">
        <h3>Selected Event</h3>
        {selectedEvent ? (
          <div className="selected-event-stack">
            <div className="selected-event-summary">
              <div className="kv-row">
                <span>event</span>
                <strong>#{selectedEvent.event_id}</strong>
              </div>
              <div className="kv-row">
                <span>energy</span>
                <strong>{((selectedEvent.collision_energy ?? 0) / 1000).toFixed(2)} TeV</strong>
              </div>
              <div className="kv-row">
                <span>mass</span>
                <strong>{(selectedEvent.collision?.mass ?? 0).toFixed(3)} GeV</strong>
              </div>
            </div>
            <CollisionSummary event={selectedEvent} />
            <ParticleList particles={selectedEvent.particles ?? []} />
          </div>
        ) : (
          <div className="empty-state">Select a collision to inspect it.</div>
        )}
      </section>
    </>
  );
});

export default EventStream;
