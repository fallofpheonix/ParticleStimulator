import { memo } from "react";

import { EventReplay } from "@events";
import { useSimulationStore } from "@store/simulationStore";

const TimelineBar = memo(function TimelineBar() {
  const timeline = useSimulationStore((state) => state.timelineState);
  const replayEvents = useSimulationStore((state) => state.getReplayEvents());
  const activeTimelineIndex = timeline.entries.length
    ? Math.min(
        timeline.entries.length - 1,
        replayEvents.length > 1
          ? Math.round((timeline.replayIndex / (replayEvents.length - 1)) * (timeline.entries.length - 1))
          : 0
      )
    : 0;
  const activeEntry = timeline.entries[activeTimelineIndex] ?? null;

  return (
    <>
      <div className="panel-header">
        <h2>Timeline</h2>
        <p>Replay and inspect the event log produced by the backend simulation service</p>
      </div>
      <EventReplay />
      <div className="timeline-list">
        {timeline.entries.slice(0, 24).map((entry, index) => (
          <div key={`${entry.type}-${index}`} className={`log-row ${index === activeTimelineIndex ? "log-row--active" : ""}`}>
            <strong>{entry.type}</strong>
            <small>{JSON.stringify(entry)}</small>
          </div>
        ))}
      </div>
      <div className="subpanel">
        <h3>Active Entry</h3>
        {activeEntry ? <pre className="debug-pre">{JSON.stringify(activeEntry, null, 2)}</pre> : <div className="empty-state">No timeline data.</div>}
      </div>
    </>
  );
});

export default TimelineBar;
