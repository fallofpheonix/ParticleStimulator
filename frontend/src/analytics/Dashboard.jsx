import { memo, useMemo } from "react";

import { useSimulationStore } from "@store/simulationStore";

import DetectorHeatmap from "./DetectorHeatmap.jsx";
import EnergyGraph from "./EnergyGraph.jsx";
import JetCountGraph from "./JetCountGraph.jsx";
import MomentumHistogram from "./MomentumHistogram.jsx";
import ParticleDistribution from "./ParticleDistribution.jsx";

const sortedEvents = (events) =>
  [...events].sort((left, right) => (left.timestamp ?? left.time_s ?? 0) - (right.timestamp ?? right.time_s ?? 0));

const Dashboard = memo(function Dashboard() {
  const streamEvents = useSimulationStore((state) => state.eventStream.events);
  const payload = useSimulationStore((state) => state.simulationState.payload);

  const events = useMemo(() => {
    if (streamEvents.length) {
      return sortedEvents(streamEvents);
    }
    return sortedEvents(
      (payload?.collisions ?? []).map((collision) => ({
        event_id: collision.event_id,
        timestamp: (collision.time_s ?? 0) * 1000,
        time_s: collision.time_s,
        collision_energy: (payload?.config?.beam_energy_gev ?? 0) * 2,
        jets: (collision.product_species ?? []).filter((species) => species.startsWith("pi")).length,
        particles: (collision.product_species ?? []).map((species) => ({ type: species, px: 0, py: 0, pz: 0 })),
        collision: {
          jets: (collision.product_species ?? []).filter((species) => species.startsWith("pi")).length,
          mass: collision.invariant_mass_gev ?? 0
        }
      }))
    );
  }, [payload, streamEvents]);

  const eventStats = useMemo(() => {
    const energies = events.map((event) => event.collision_energy ?? 0);
    const jets = events.map((event) => event.collision?.jets ?? event.jets ?? 0);
    const particleCount = events.reduce((sum, event) => sum + (event.particles?.length ?? 0), 0);
    return {
      events: events.length,
      meanEnergyTeV: energies.length ? energies.reduce((sum, value) => sum + value, 0) / energies.length / 1000 : 0,
      maxJets: jets.length ? Math.max(...jets) : 0,
      particles: particleCount
    };
  }, [events]);

  return (
    <>
      <div className="panel-header">
        <h2>Analytics Dashboard</h2>
        <p>Streaming physics statistics and detector outputs</p>
      </div>
      <div className="metric-grid">
        {[
          ["Events", eventStats.events],
          ["Mean Energy", `${eventStats.meanEnergyTeV.toFixed(2)} TeV`],
          ["Max Jets", eventStats.maxJets],
          ["Particles", eventStats.particles]
        ].map(([label, value]) => (
          <article className="metric-card" key={label}>
            <strong>{value}</strong>
            <span>{label}</span>
          </article>
        ))}
      </div>
      <div className="analytics-grid analytics-grid--wide">
        <EnergyGraph events={events} />
        <MomentumHistogram events={events} />
      </div>
      <div className="analytics-grid">
        <DetectorHeatmap events={events} />
        <JetCountGraph events={events} />
        <ParticleDistribution events={events} />
      </div>
    </>
  );
});

export default Dashboard;
