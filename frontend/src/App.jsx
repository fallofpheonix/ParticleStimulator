import { Suspense, lazy, useEffect } from "react";

import { defaultPhysicsParameters } from "@app/defaults";
import { useSimulationStore } from "@store/simulationStore";
import { eventBus } from "@services/eventBus";

const MainLayout = lazy(() => import("@layout/MainLayout.jsx"));
const ParticleScene = lazy(() => import("@renderer/ParticleScene.jsx"));
const ControlPanel = lazy(() => import("@ui/ControlPanel.jsx"));
const AnalyticsDashboard = lazy(() => import("@analytics/Dashboard.jsx"));
const EventStream = lazy(() => import("@events/EventStream.jsx"));
const Timeline = lazy(() => import("@timeline/TimelineBar.jsx"));
const DebugPanel = lazy(() => import("@debug/DebugPanel.jsx"));

const fallback = <div className="empty-state">Loading simulator module…</div>;

export default function App() {
  const defaultsLoaded = useSimulationStore((state) => state.simulationState.defaultsLoaded);
  const status = useSimulationStore((state) => state.simulationState.status);
  const payload = useSimulationStore((state) => state.simulationState.payload);
  const parameters = useSimulationStore((state) => state.physicsParameters);
  const hydrateDefaults = useSimulationStore((state) => state.hydrateDefaults);

  useEffect(() => {
    eventBus.checkHealth();
    eventBus.loadDefaults();
    eventBus.connectWebSocket();
    return () => eventBus.disconnectWebSocket();
  }, []);

  useEffect(() => {
    if (!defaultsLoaded) {
      hydrateDefaults(defaultPhysicsParameters);
    }
  }, [defaultsLoaded, hydrateDefaults]);

  useEffect(() => {
    if (defaultsLoaded && !payload && status === "idle") {
      eventBus.runSimulation(parameters).catch(() => {});
    }
  }, [defaultsLoaded, payload, status, parameters]);

  return (
    <Suspense fallback={fallback}>
      <MainLayout
        controlPanel={
          <Suspense fallback={fallback}>
            <ControlPanel />
          </Suspense>
        }
        scene={
          <Suspense fallback={fallback}>
            <ParticleScene />
          </Suspense>
        }
        analytics={
          <Suspense fallback={fallback}>
            <AnalyticsDashboard />
          </Suspense>
        }
        eventStream={
          <Suspense fallback={fallback}>
            <EventStream />
          </Suspense>
        }
        timeline={
          <Suspense fallback={fallback}>
            <Timeline />
          </Suspense>
        }
        debugPanel={
          <Suspense fallback={fallback}>
            <DebugPanel />
          </Suspense>
        }
      />
    </Suspense>
  );
}
