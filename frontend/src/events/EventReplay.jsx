import { memo, useEffect } from "react";

import { useSimulationStore } from "@store/simulationStore";

const EventReplay = memo(function EventReplay() {
  const replayEvents = useSimulationStore((state) => state.getReplayEvents());
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

  const progress = replayEvents.length ? ((timeline.replayIndex + 1) / replayEvents.length) * 100 : 0;

  return (
    <section className="subpanel">
      <div className="replay-header">
        <span className="replay-title">Event Replay</span>
        <span className={`replay-status ${timeline.isPlaying ? "replay-status--live" : ""}`}>
          {timeline.isPlaying ? "Playing" : "Stopped"}
        </span>
      </div>
      <div className="replay-controls">
        <button
          type="button"
          onClick={() => setTimelinePlayback(!timeline.isPlaying)}
          disabled={!replayEvents.length}
        >
          {timeline.isPlaying ? "Pause" : "Play"}
        </button>
        <button
          type="button"
          className="ghost"
          onClick={advanceTimeline}
          disabled={timeline.isPlaying || !replayEvents.length}
        >
          Step
        </button>
        <button type="button" className="ghost" onClick={resetTimeline} disabled={!replayEvents.length}>
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
      <div className="rp-labels">
        <span>event {replayEvents.length ? timeline.replayIndex + 1 : 0}</span>
        <span>of {replayEvents.length}</span>
      </div>
    </section>
  );
});

export default EventReplay;
