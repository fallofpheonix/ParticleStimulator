import { create } from "zustand";

import { defaultPhysicsParameters } from "@app/defaults";

const buildSessionId = () =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `session-${Date.now()}`;

const normalizeSimulationEvents = (payload) => {
  if (!payload) {
    return [];
  }

  const particleMap = new Map((payload.final_particles ?? []).map((particle) => [particle.particle_id, particle]));
  return (payload.collisions ?? []).map((event) => ({
    event_id: event.event_id,
    collision_energy: (payload.config?.beam_energy_gev ?? 0) * 2,
    product_ids: event.product_ids ?? [],
    product_species: event.product_species ?? [],
    particles: (event.product_ids ?? [])
      .map((particleId) => particleMap.get(particleId))
      .filter(Boolean)
      .map((particle) => ({
        type: particle.species,
        px: particle.velocity.x,
        py: particle.velocity.y,
        pz: particle.velocity.z
      })),
    collision: {
      mass: event.invariant_mass_gev ?? 0,
      jets: (event.product_species ?? []).filter((species) => species.startsWith("pi")).length,
      muons: (event.product_species ?? []).filter((species) => species.startsWith("muon")).length
    },
    time_s: event.time_s
  }));
};

const normalizeTimelineState = (payload, currentTimeline) => ({
  entries: payload?.timeline ?? [],
  replayIndex: 0,
  isPlaying: false,
  playbackSpeedMs: currentTimeline.playbackSpeedMs
});

export const useSimulationStore = create((set, get) => ({
  simulationState: {
    status: "idle",
    health: "checking",
    transport: "http",
    defaultsLoaded: false,
    payload: null,
    error: null,
    lastRunAt: null
  },
  eventStream: {
    events: [],
    selectedEventId: null,
    wsStatus: "disconnected",
    filters: {
      query: "",
      type: "all"
    }
  },
  physicsParameters: { ...defaultPhysicsParameters },
  uiLayout: {
    leftCollapsed: false,
    rightCollapsed: false,
    bottomCollapsed: false,
    debugVisible: true
  },
  timelineState: {
    entries: [],
    replayIndex: 0,
    isPlaying: false,
    playbackSpeedMs: 900
  },
  userSession: {
    sessionId: buildSessionId(),
    connectedAt: null,
    preferences: {
      theme: "control-surface"
    }
  },

  setPhysicsParameter: (name, value) =>
    set((state) => ({
      physicsParameters: {
        ...state.physicsParameters,
        [name]: value
      }
    })),

  hydrateDefaults: (defaults) =>
    set((state) => ({
      physicsParameters: {
        ...state.physicsParameters,
        ...defaults
      },
      simulationState: {
        ...state.simulationState,
        defaultsLoaded: true
      }
    })),

  setSimulationStatus: (status, error = null) =>
    set((state) => ({
      simulationState: {
        ...state.simulationState,
        status,
        error
      }
    })),

  setHealth: (health) =>
    set((state) => ({
      simulationState: {
        ...state.simulationState,
        health
      }
    })),

  applySimulationPayload: (payload) =>
    set((state) => {
      const nextEvents = normalizeSimulationEvents(payload);
      return {
        simulationState: {
          ...state.simulationState,
          status: "ready",
          payload,
          error: null,
          transport: state.eventStream.wsStatus === "connected" ? "websocket" : "http",
          lastRunAt: new Date().toISOString()
        },
        eventStream: {
          ...state.eventStream,
          events: nextEvents,
          selectedEventId: nextEvents[0]?.event_id ?? null
        },
        timelineState: normalizeTimelineState(payload, state.timelineState)
      };
    }),

  appendStreamEvent: (event) =>
    set((state) => {
      const events = [event, ...state.eventStream.events].slice(0, 250);
      return {
        eventStream: {
          ...state.eventStream,
          events,
          selectedEventId: state.eventStream.selectedEventId ?? event.event_id
        },
        timelineState: {
          ...state.timelineState,
          entries: [
            { type: "stream", time_s: event.time_s ?? 0, payload: event },
            ...state.timelineState.entries
          ].slice(0, 120)
        }
      };
    }),

  setWsStatus: (wsStatus) =>
    set((state) => ({
      eventStream: {
        ...state.eventStream,
        wsStatus
      },
      simulationState: {
        ...state.simulationState,
        transport: wsStatus === "connected" ? "websocket" : state.simulationState.transport
      }
    })),

  selectEvent: (eventId) =>
    set((state) => ({
      eventStream: {
        ...state.eventStream,
        selectedEventId: eventId
      }
    })),

  setEventFilter: (key, value) =>
    set((state) => ({
      eventStream: {
        ...state.eventStream,
        filters: {
          ...state.eventStream.filters,
          [key]: value
        }
      }
    })),

  toggleLayoutPanel: (panelKey) =>
    set((state) => ({
      uiLayout: {
        ...state.uiLayout,
        [panelKey]: !state.uiLayout[panelKey]
      }
    })),

  setTimelinePlayback: (isPlaying) =>
    set((state) => ({
      timelineState: {
        ...state.timelineState,
        isPlaying
      }
    })),

  advanceTimeline: () =>
    set((state) => ({
      timelineState: {
        ...state.timelineState,
        replayIndex: state.timelineState.entries.length
          ? Math.min(state.timelineState.entries.length - 1, state.timelineState.replayIndex + 1)
          : 0
      }
    })),

  resetTimeline: () =>
    set((state) => ({
      timelineState: {
        ...state.timelineState,
        replayIndex: 0,
        isPlaying: false
      }
    })),

  setTimelineSpeed: (playbackSpeedMs) =>
    set((state) => ({
      timelineState: {
        ...state.timelineState,
        playbackSpeedMs
      }
    })),

  updateSession: (patch) =>
    set((state) => ({
      userSession: {
        ...state.userSession,
        ...patch
      }
    })),

  clearError: () =>
    set((state) => ({
      simulationState: {
        ...state.simulationState,
        error: null
      }
    })),

  getFilteredEvents: () => {
    const state = get();
    const query = state.eventStream.filters.query.toLowerCase();
    const type = state.eventStream.filters.type;
    return state.eventStream.events.filter((event) => {
      const matchesQuery =
        !query ||
        String(event.event_id).includes(query) ||
        (event.particles ?? []).some((particle) => particle.type.toLowerCase().includes(query));
      const matchesType = type === "all" || (event.particles ?? []).some((particle) => particle.type === type);
      return matchesQuery && matchesType;
    });
  }
}));
