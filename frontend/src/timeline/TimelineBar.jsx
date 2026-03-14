import { memo, useEffect } from "react";

import { useSimulationStore } from "@store/simulationStore";

const TimelineBar = memo(function TimelineBar() {
  const timeline = useSimulationStore((state) => state.timelineState);
  const setTimelinePlayback = useSimulationStore((state) => state.setTimelinePlayback);
  const advanceTimeline = useSimulationStore((state) => state.advanceTimeline);
  const resetTimeline = useSimulationStore((state) => state.resetTimeline);
  const setTimelineSpeed = useSimulationStore((state) => state.setTimelineSpeed);

  useEffect(() => {
    if (!timeline.isPlaying) {
      return undefined;
    }
    const handle = window.setInterval(advanceTimeline, timeline.playbackSpeedMs);
    return () => window.clearInterval(handle);
  }, [advanceTimeline, timeline.isPlaying, timeline.playbackSpeedMs]);

  const activeEntry = timeline.entries[timeline.replayIndex] ?? null;
  const progress = timeline.entries.length ? ((timeline.replayIndex + 1) / timeline.entries.length) * 100 : 0;

  return (
    <>
      <div className="panel-header">
        <h2>Timeline</h2>
        <p>Replay and inspect the event log produced by the backend simulation service</p>
      </div>
      <div className="replay-controls">
        <button type="button" onClick={() => setTimelinePlayback(!timeline.isPlaying)} disabled={!timeline.entries.length}>
          {timeline.isPlaying ? "Pause" : "Play"}
        </button>
        <button type="button" className="ghost" onClick={resetTimeline}>
          Reset
        </button>
        <select value={timeline.playbackSpeedMs} onChange={(event) => setTimelineSpeed(Number(event.target.value))}>
          <option value={1200}>0.5x</option>
          <option value={900}>1x</option>
          <option value={500}>2x</option>
          <option value={180}>5x</option>
        </select>
      </div>
      <div className="timeline-progress">
        <div className="bar-track">
          <div className="bar-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>
      <div className="timeline-list">
        {timeline.entries.slice(0, 24).map((entry, index) => (
          <div key={`${entry.type}-${index}`} className={`log-row ${index === timeline.replayIndex ? "log-row--active" : ""}`}>
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
