import Stats from "stats.js";
import { lazy, memo, Suspense, useEffect, useMemo, useRef, useState } from "react";

import { useSimulationStore } from "@store/simulationStore";

import FPSMonitor from "./FPSMonitor.jsx";
import LatencyGraph from "./LatencyGraph.jsx";
import MemoryMonitor from "./MemoryMonitor.jsx";

const CollaborationPanel = lazy(() => import("@collaboration/CollaborationPanel.jsx"));

const tabs = ["perf", "sys", "alerts", "log", "collab"];

const DebugPanel = memo(function DebugPanel() {
  const simulationState = useSimulationStore((state) => state.simulationState);
  const eventStream = useSimulationStore((state) => state.eventStream);
  const payload = useSimulationStore((state) => state.simulationState.payload);
  const uiLayout = useSimulationStore((state) => state.uiLayout);
  const toggleLayoutPanel = useSimulationStore((state) => state.toggleLayoutPanel);
  const setDebugMetrics = useSimulationStore((state) => state.setDebugMetrics);
  const [tab, setTab] = useState("perf");
  const [paused, setPaused] = useState(false);
  const [history, setHistory] = useState([]);
  const [logs, setLogs] = useState([]);
  const statsMountRef = useRef(null);
  const statsRef = useRef(null);
  const latestEventRef = useRef(null);
  const wsStatusRef = useRef(eventStream.wsStatus);
  const particleCountRef = useRef(payload?.final_particles?.length ?? 0);

  useEffect(() => {
    latestEventRef.current = eventStream.events.at(0) ?? null;
    wsStatusRef.current = eventStream.wsStatus;
    particleCountRef.current = payload?.final_particles?.length ?? 0;
  }, [eventStream.events, eventStream.wsStatus, payload]);

  useEffect(() => {
    const stats = new Stats();
    stats.showPanel(0);
    stats.dom.className = "stats-dom";
    statsMountRef.current?.appendChild(stats.dom);
    statsRef.current = stats;
    let frameCounter = 0;
    let lastSample = performance.now();
    let rafId = 0;

    const measure = (now) => {
      stats.begin();
      frameCounter += 1;
      if (now - lastSample >= 400) {
        const fps = (frameCounter * 1000) / (now - lastSample);
        const particleCount = particleCountRef.current;
        const latencyMs = (() => {
          const latestEvent = latestEventRef.current;
          if (latestEvent?.timestamp) {
            return Math.max(0, Date.now() - latestEvent.timestamp);
          }
          return 16 + Math.abs(Math.sin(now / 700)) * 22;
        })();
        const heapMb = typeof performance.memory?.usedJSHeapSize === "number" ? performance.memory.usedJSHeapSize / (1024 * 1024) : 48 + particleCount * 0.16;
        const gpuMb = 96 + particleCount * 0.42;
        if (!paused) {
          const metrics = { fps, heapMb, gpuMb, latencyMs, wsStatus: wsStatusRef.current };
          setDebugMetrics(metrics);
          setHistory((current) => [
            ...current.slice(-59),
            { ...metrics, particleCount, time: now }
          ]);
          setLogs((current) => [
            ...current.slice(-29),
            `${new Date().toISOString()} fps=${fps.toFixed(1)} latency=${latencyMs.toFixed(1)}ms particles=${particleCount}`
          ]);
        }
        frameCounter = 0;
        lastSample = now;
      }
      stats.end();
      rafId = window.requestAnimationFrame(measure);
    };

    rafId = window.requestAnimationFrame(measure);
    return () => {
      window.cancelAnimationFrame(rafId);
      stats.dom.remove();
    };
  }, [paused, setDebugMetrics]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "`") {
        toggleLayoutPanel("debugVisible");
      }
      if (event.ctrlKey && event.key.toLowerCase() === "p") {
        event.preventDefault();
        setPaused((current) => !current);
        toggleLayoutPanel("renderPaused");
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [toggleLayoutPanel]);

  const alerts = useMemo(
    () =>
      history
        .flatMap((entry) => [
          entry.fps < 40 ? `LOW FPS ${entry.fps.toFixed(1)}` : null,
          entry.latencyMs > 100 ? `LATENCY SPIKE ${entry.latencyMs.toFixed(1)}ms` : null,
          entry.gpuMb > 180 ? `GPU PRESSURE ${entry.gpuMb.toFixed(1)}MB` : null
        ])
        .filter(Boolean)
        .slice(-8),
    [history]
  );

  const latest = history.at(-1);

  return (
    <div className="debug-shell">
      <div className="debug-toggle-row">
        <button type="button" className="ghost" onClick={() => toggleLayoutPanel("debugVisible")}>
          {uiLayout.debugVisible ? "Hide Debug" : "Show Debug"}
        </button>
        <button type="button" className="ghost" onClick={() => { setPaused((current) => !current); toggleLayoutPanel("renderPaused"); }}>
          {uiLayout.renderPaused ? "Resume Rendering" : "Pause Rendering"}
        </button>
      </div>
      {uiLayout.debugVisible ? (
        <div className="debug-panel debug-panel--wide">
          <div className="debug-tab-row">
            {tabs.map((entry) => (
              <button key={entry} type="button" className={tab === entry ? "config-tab config-tab--active" : "config-tab ghost"} onClick={() => setTab(entry)}>
                {entry.toUpperCase()}
              </button>
            ))}
          </div>
          <div className="metric-grid">
            {[
              ["FPS", latest?.fps?.toFixed(1) ?? "0.0"],
              ["Particles", latest?.particleCount ?? payload?.final_particles?.length ?? 0],
              ["Latency", `${latest?.latencyMs?.toFixed(1) ?? "0.0"} ms`],
              ["WS", eventStream.wsStatus]
            ].map(([label, value]) => (
              <article className="metric-card" key={label}>
                <strong>{value}</strong>
                <span>{label}</span>
              </article>
            ))}
          </div>
          {tab === "perf" ? (
            <div className="debug-grid">
              <FPSMonitor history={history} statsNode={statsMountRef} />
              <MemoryMonitor history={history} />
              <LatencyGraph history={history} wsStatus={eventStream.wsStatus} />
            </div>
          ) : null}
          {tab === "sys" ? (
            <section className="subpanel">
              <h3>System</h3>
              <pre className="debug-pre">
                {JSON.stringify(
                  {
                    health: simulationState.health,
                    status: simulationState.status,
                    transport: simulationState.transport,
                    renderPaused: uiLayout.renderPaused,
                    payloadSummary: payload?.summary?.metrics ?? null
                  },
                  null,
                  2
                )}
              </pre>
            </section>
          ) : null}
          {tab === "alerts" ? (
            <section className="subpanel">
              <h3>Alerts</h3>
              {alerts.length ? alerts.map((alert) => <div key={alert} className="error-banner">{alert}</div>) : <div className="empty-state">No active alerts.</div>}
            </section>
          ) : null}
          {tab === "log" ? (
            <section className="subpanel">
              <h3>Log</h3>
              <pre className="debug-pre">{logs.slice().reverse().join("\n")}</pre>
            </section>
          ) : null}
          {tab === "collab" ? (
            <Suspense fallback={<div className="empty-state">Loading collaboration panel…</div>}>
              <CollaborationPanel />
            </Suspense>
          ) : null}
        </div>
      ) : null}
    </div>
  );
});

export default DebugPanel;
