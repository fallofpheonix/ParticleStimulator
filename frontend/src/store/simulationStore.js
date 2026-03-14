import { create } from "zustand";

import { defaultPhysicsParameters } from "@app/defaults";

const buildSessionId = () =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `session-${Date.now()}`;

const sortReplayEvents = (events) =>
  [...events].sort((left, right) => {
    const leftTime = left.time_s ?? left.timestamp ?? Number.MAX_SAFE_INTEGER;
    const rightTime = right.time_s ?? right.timestamp ?? Number.MAX_SAFE_INTEGER;
    if (leftTime !== rightTime) {
      return leftTime - rightTime;
    }
    return (left.event_id ?? 0) - (right.event_id ?? 0);
  });

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

const buildTimelineState = (payload, currentTimeline) => ({
  entries: payload?.timeline ?? [],
  replayIndex: 0,
  isPlaying: false,
  playbackSpeedMs: currentTimeline.playbackSpeedMs
});

const summarizeExperimentDatasets = (events, tracks, hits) => [
  {
    id: "event-stream",
    name: "Event Stream",
    description: "Normalized collision records from the backend event bus.",
    records: events.length,
    metric: "events"
  },
  {
    id: "particle-tracks",
    name: "Particle Tracks",
    description: "Renderable particle trajectories derived from simulation output.",
    records: tracks.length,
    metric: "tracks"
  },
  {
    id: "detector-hits",
    name: "Detector Hits",
    description: "Tracker and calorimeter readout samples used by analysis panels.",
    records: hits.length,
    metric: "hits"
  }
];

const buildRunSummary = (parameters, payload, events, tracks, hits) => ({
  id: `run-${Date.now()}`,
  startedAt: new Date().toISOString(),
  beamEnergyTeV: (parameters.beam_energy_gev ?? 0) / 1000,
  collisions: events.length,
  particles: tracks.length,
  detectorHits: hits.length,
  massPeak: Math.max(0, ...events.map((event) => event.collision?.mass ?? 0)),
  transport: payload ? "backend" : "stream",
  status: "completed"
});

const buildCollaborationState = (sessionId) => ({
  users: [
    { id: sessionId, name: "You", role: "host", color: "#7dd3fc", online: true },
    { id: "u-2", name: "A. Chen", role: "analysis", color: "#fb7185", online: true },
    { id: "u-3", name: "M. Iqbal", role: "detector", color: "#34d399", online: true }
  ],
  messages: [
    { id: "m-1", author: "system", body: "Shared session ready.", kind: "system" },
    { id: "m-2", author: "A. Chen", body: "Monitoring jet multiplicity in the latest run.", kind: "text" }
  ],
  locks: {}
});

const settingsStorageKey = "particle-stimulator:settings";

const buildDefaultSettings = () => ({
  theme: "dark",
  apiBaseUrl: "http://127.0.0.1:8000",
  websocketUrl: "ws://127.0.0.1:8001/events",
  defaultPhysicsParameters: { ...defaultPhysicsParameters }
});

const readStoredSettings = () => {
  if (typeof window === "undefined") {
    return buildDefaultSettings();
  }
  try {
    const raw = window.localStorage.getItem(settingsStorageKey);
    if (!raw) {
      return buildDefaultSettings();
    }
    const parsed = JSON.parse(raw);
    return {
      ...buildDefaultSettings(),
      ...parsed,
      defaultPhysicsParameters: {
        ...defaultPhysicsParameters,
        ...(parsed.defaultPhysicsParameters ?? {})
      }
    };
  } catch {
    return buildDefaultSettings();
  }
};

const sessionId = buildSessionId();
const initialSettings = readStoredSettings();

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
    replayEvents: [],
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
    sessionId,
    connectedAt: null,
    preferences: {
      theme: initialSettings.theme
    }
  },
  settings: initialSettings,
  experiments: {
    selectedDatasetId: "event-stream",
    selectedRunId: null,
    runHistory: [],
    datasets: summarizeExperimentDatasets([], [], [])
  },
  collaboration: buildCollaborationState(sessionId),
  ml: {
    status: "idle",
    progress: 0,
    dataset: "auto",
    metrics: null,
    artifactPath: null,
    lastPrediction: null,
    error: null
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
      const replayEvents = sortReplayEvents(nextEvents);
      const nextTracks = computeParticleTracks(payload);
      const nextHits = computeDetectorHits(payload);
      const datasets = summarizeExperimentDatasets(nextEvents, nextTracks, nextHits);
      const runSummary = buildRunSummary(state.simulationParameters, payload, nextEvents, nextTracks, nextHits);

      return {
        eventData: nextEvents,
        particleTracks: nextTracks,
        detectorHits: nextHits,
        timelineFrame: 0,
        simulationRunning: false,
        simulationState: {
          ...state.simulationState,
          status: "ready",
          payload,
          error: null,
          transport: state.eventStream.wsStatus === "connected" ? "websocket" : "http",
          lastRunAt: runSummary.startedAt
        },
        eventStream: {
          ...state.eventStream,
          events: nextEvents,
          replayEvents,
          selectedEventId: replayEvents[0]?.event_id ?? null
        },
        timelineState: buildTimelineState(payload, state.timelineState),
        experiments: {
          ...state.experiments,
          datasets,
          selectedRunId: runSummary.id,
          runHistory: [runSummary, ...state.experiments.runHistory].slice(0, 24)
        }
      };
    }),

  appendStreamEvent: (event) =>
    set((state) => {
      if (state.eventStream.events.some((current) => current.event_id === event.event_id)) {
        return {};
      }
      const enrichedEvent = {
        timestamp: Date.now(),
        ...event
      };
      const events = [enrichedEvent, ...state.eventStream.events].slice(0, 250);
      const replayEvents = sortReplayEvents(events);
      const datasets = summarizeExperimentDatasets(events, state.particleTracks, state.detectorHits);

      return {
        eventData: events,
        eventStream: {
          ...state.eventStream,
          events,
          replayEvents,
          selectedEventId: state.eventStream.selectedEventId ?? enrichedEvent.event_id
        },
        timelineState: {
          ...state.timelineState,
          entries: [
            { type: "stream", time_s: enrichedEvent.time_s ?? 0, payload: enrichedEvent },
            ...state.timelineState.entries
          ].slice(0, 120)
        },
        experiments: {
          ...state.experiments,
          datasets
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
      const replayEvents = state.eventStream.replayEvents;
      const replayIndex = replayEvents.findIndex((event) => event.event_id === eventId);
      return {
        timelineFrame: replayIndex >= 0 ? replayIndex : state.timelineFrame,
        eventStream: {
          ...state.eventStream,
          selectedEventId: eventId
        },
        timelineState:
          replayIndex >= 0
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
      const replayEvents = state.eventStream.replayEvents;
      const selectedEventId =
        state.eventStream.selectedEventId ??
        replayEvents[state.timelineState.replayIndex]?.event_id ??
        replayEvents[0]?.event_id ??
        null;
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
      const replayEvents = state.eventStream.replayEvents;
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
      const replayEvents = state.eventStream.replayEvents;
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

  updateSettings: (patch) =>
    set((state) => {
      const settings = {
        ...state.settings,
        ...patch,
        defaultPhysicsParameters: {
          ...state.settings.defaultPhysicsParameters,
          ...(patch.defaultPhysicsParameters ?? {})
        }
      };
      if (typeof window !== "undefined") {
        window.localStorage.setItem(settingsStorageKey, JSON.stringify(settings));
      }
      return {
        settings,
        userSession: {
          ...state.userSession,
          preferences: {
            ...state.userSession.preferences,
            theme: settings.theme
          }
        }
      };
    }),

  setDebugMetrics: (patch) =>
    set((state) => ({
      debugMetrics: {
        ...state.debugMetrics,
        ...patch
      }
    })),

  selectExperimentDataset: (datasetId) =>
    set((state) => ({
      experiments: {
        ...state.experiments,
        selectedDatasetId: datasetId
      }
    })),

  selectExperimentRun: (runId) =>
    set((state) => ({
      experiments: {
        ...state.experiments,
        selectedRunId: runId
      }
    })),

  sendCollaborationMessage: (body, kind = "text", author = "You") =>
    set((state) => ({
      collaboration: {
        ...state.collaboration,
        messages: [
          ...state.collaboration.messages,
          {
            id: `m-${Date.now()}`,
            author,
            body,
            kind
          }
        ].slice(-40)
      }
    })),

  toggleCollaborationLock: (key, ownerId = null) =>
    set((state) => {
      const existing = state.collaboration.locks[key];
      const nextLocks = { ...state.collaboration.locks };
      if (existing) {
        delete nextLocks[key];
      } else {
        const resolvedOwnerId = ownerId ?? state.userSession.sessionId;
        const owner =
          state.collaboration.users.find((user) => user.id === resolvedOwnerId) ?? state.collaboration.users[0];
        nextLocks[key] = owner;
      }
      return {
        collaboration: {
          ...state.collaboration,
          locks: nextLocks
        }
      };
    }),

  setMlStatus: (patch) =>
    set((state) => ({
      ml: {
        ...state.ml,
        ...patch
      }
    })),

  clearError: () =>
    set((state) => ({
      simulationState: {
        ...state.simulationState,
        error: null
      }
    }))
}));
