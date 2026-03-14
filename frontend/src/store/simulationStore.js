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
  const receivedAt = Date.now();
  return (payload.collisions ?? []).map((event) => ({
    event_id: event.event_id,
    timestamp: receivedAt + Math.round((event.time_s ?? 0) * 1000),
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

const getReplayEventsSnapshot = (state) =>
  [...state.eventStream.events].sort((left, right) => {
    const leftTime = left.time_s ?? Number.MAX_SAFE_INTEGER;
    const rightTime = right.time_s ?? Number.MAX_SAFE_INTEGER;
    if (leftTime !== rightTime) {
      return leftTime - rightTime;
    }
    return (left.event_id ?? 0) - (right.event_id ?? 0);
  });

const computeParticleTracks = (payload) =>
  (payload?.final_particles ?? []).map((particle) => ({
    particle_id: particle.particle_id,
    type: particle.species,
    momentum: particle.velocity,
    position: particle.position
  }));

const computeDetectorHits = (payload) => [
  ...(payload?.tracker_hits ?? []).map((hit) => ({ layer: "tracker", ...hit })),
  ...(payload?.calorimeter_hits ?? []).map((hit) => ({ layer: "calorimeter", ...hit }))
];

export const useSimulationStore = create((set, get) => ({
  simulationParameters: { ...defaultPhysicsParameters },
  simulationRunning: false,
  eventData: [],
  particleTracks: [],
  detectorHits: [],
  timelineFrame: 0,
  debugMetrics: {
    fps: 0,
    heapMb: 0,
    gpuMb: 0,
    latencyMs: 0,
    wsStatus: "disconnected"
  },
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
    debugVisible: true,
    renderPaused: false
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
      simulationParameters: {
        ...state.simulationParameters,
        [name]: value
      },
      physicsParameters: {
        ...state.physicsParameters,
        [name]: value
      }
    })),

  setPhysicsParameters: (values) =>
    set((state) => ({
      simulationParameters: {
        ...state.simulationParameters,
        ...values
      },
      physicsParameters: {
        ...state.physicsParameters,
        ...values
      }
    })),

  hydrateDefaults: (defaults) =>
    set((state) => ({
      simulationParameters: {
        ...state.simulationParameters,
        ...defaults
      },
      physicsParameters: {
        ...state.physicsParameters,
        ...defaults
      },
      simulationRunning: false,
      simulationState: {
        ...state.simulationState,
        defaultsLoaded: true
      }
    })),

  setSimulationStatus: (status, error = null) =>
    set((state) => ({
      simulationRunning: status === "running",
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
      const nextTracks = computeParticleTracks(payload);
      const nextHits = computeDetectorHits(payload);
      return {
        eventData: nextEvents,
        particleTracks: nextTracks,
        detectorHits: nextHits,
        timelineFrame: 0,
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
      const enrichedEvent = {
        timestamp: Date.now(),
        ...event
      };
      const events = [enrichedEvent, ...state.eventStream.events].slice(0, 250);
      return {
        eventData: events,
        eventStream: {
          ...state.eventStream,
          events,
          selectedEventId: state.eventStream.selectedEventId ?? enrichedEvent.event_id
        },
        timelineState: {
          ...state.timelineState,
          entries: [
            { type: "stream", time_s: enrichedEvent.time_s ?? 0, payload: enrichedEvent },
            ...state.timelineState.entries
          ].slice(0, 120)
        }
      };
    }),

  setWsStatus: (wsStatus) =>
    set((state) => ({
      debugMetrics: {
        ...state.debugMetrics,
        wsStatus
      },
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
    set((state) => {
      const replayEvents = getReplayEventsSnapshot(state);
      const replayIndex = replayEvents.findIndex((event) => event.event_id === eventId);
      return {
        timelineFrame: replayIndex >= 0 ? replayIndex : state.timelineFrame,
        eventStream: {
          ...state.eventStream,
          selectedEventId: eventId
        },
        timelineState: replayIndex >= 0
          ? {
              ...state.timelineState,
              replayIndex
            }
          : state.timelineState
      };
    }),

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
    set((state) => {
      const replayEvents = getReplayEventsSnapshot(state);
      const selectedEventId =
        state.eventStream.selectedEventId ?? replayEvents[state.timelineState.replayIndex]?.event_id ?? replayEvents[0]?.event_id ?? null;
      return {
        timelineFrame: state.timelineState.replayIndex,
        eventStream: {
          ...state.eventStream,
          selectedEventId
        },
        timelineState: {
          ...state.timelineState,
          isPlaying: isPlaying && replayEvents.length > 0
        }
      };
    }),

  advanceTimeline: () =>
    set((state) => {
      const replayEvents = getReplayEventsSnapshot(state);
      if (!replayEvents.length) {
        return state;
      }
      const nextIndex = Math.min(replayEvents.length - 1, state.timelineState.replayIndex + 1);
      return {
        timelineFrame: nextIndex,
        eventStream: {
          ...state.eventStream,
          selectedEventId: replayEvents[nextIndex]?.event_id ?? state.eventStream.selectedEventId
        },
        timelineState: {
          ...state.timelineState,
          replayIndex: nextIndex,
          isPlaying: nextIndex < replayEvents.length - 1 ? state.timelineState.isPlaying : false
        }
      };
    }),

  resetTimeline: () =>
    set((state) => {
      const replayEvents = getReplayEventsSnapshot(state);
      return {
        timelineFrame: 0,
        eventStream: {
          ...state.eventStream,
          selectedEventId: replayEvents[0]?.event_id ?? state.eventStream.selectedEventId
        },
        timelineState: {
          ...state.timelineState,
          replayIndex: 0,
          isPlaying: false
        }
      };
    }),

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

  setDebugMetrics: (patch) =>
    set((state) => ({
      debugMetrics: {
        ...state.debugMetrics,
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
  },

  getReplayEvents: () => getReplayEventsSnapshot(get())
}));
