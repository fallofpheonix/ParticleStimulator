import { useSimulationStore } from "@store/simulationStore";

const DEFAULT_WS_URL = "ws://127.0.0.1:8001/events";
const RECONNECT_DELAY_MS = 3000;
const POLL_RECENT_EVENTS_MS = 2500;

const normalizeBaseUrl = (value) => {
  if (!value) {
    return "";
  }
  return value.endsWith("/") ? value.slice(0, -1) : value;
};

class EventBus {
  constructor() {
    this.listeners = new Map();
    this.socket = null;
    this.reconnectTimer = null;
    this.pollTimer = null;
    this.wsUrl = DEFAULT_WS_URL;
    this.isSocketEnabled = false;
  }

  subscribe(topic, listener) {
    const subscribers = this.listeners.get(topic) ?? new Set();
    subscribers.add(listener);
    this.listeners.set(topic, subscribers);
    return () => {
      subscribers.delete(listener);
    };
  }

  publish(topic, payload) {
    const subscribers = this.listeners.get(topic);
    if (!subscribers) {
      return;
    }
    for (const listener of subscribers) {
      listener(payload);
    }
  }

  buildApiUrl(path) {
    const baseUrl = normalizeBaseUrl(useSimulationStore.getState().settings.apiBaseUrl);
    return `${baseUrl}${path}`;
  }

  async checkHealth() {
    try {
      const response = await fetch(this.buildApiUrl("/api/health"));
      if (!response.ok) {
        throw new Error(`health request failed: ${response.status}`);
      }
      useSimulationStore.getState().setHealth("ok");
      this.publish("health", { status: "ok" });
    } catch (error) {
      useSimulationStore.getState().setHealth("error");
      useSimulationStore.getState().setSimulationStatus("error", String(error));
      this.publish("health", { status: "error", error: String(error) });
    }
  }

  async loadDefaults() {
    try {
      const response = await fetch(this.buildApiUrl("/api/defaults"));
      if (!response.ok) {
        throw new Error(`defaults request failed: ${response.status}`);
      }
      const defaults = await response.json();
      useSimulationStore.getState().hydrateDefaults(defaults);
      this.publish("defaults", defaults);
    } catch (error) {
      useSimulationStore.getState().setSimulationStatus("error", String(error));
    }
  }

  async runSimulation(parameters) {
    const store = useSimulationStore.getState();
    store.setSimulationStatus("running");
    try {
      const response = await fetch(this.buildApiUrl("/api/simulate"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(parameters)
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || `simulation request failed: ${response.status}`);
      }
      const payload = await response.json();
      store.applySimulationPayload(payload);
      this.publish("simulation:update", payload);
      return payload;
    } catch (error) {
      store.setSimulationStatus("error", String(error));
      this.publish("simulation:error", { error: String(error) });
      throw error;
    }
  }

  async trainModel(payload) {
    const response = await fetch(this.buildApiUrl("/api/ml/train"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload ?? {})
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `ml training request failed: ${response.status}`);
    }
    useSimulationStore.getState().setMlStatus(data);
    return data;
  }

  async getModelStatus() {
    const response = await fetch(this.buildApiUrl("/api/ml/status"));
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `ml status request failed: ${response.status}`);
    }
    useSimulationStore.getState().setMlStatus(data);
    return data;
  }

  async fetchRecentEvents() {
    const response = await fetch(this.buildApiUrl("/api/events/recent"));
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `recent events request failed: ${response.status}`);
    }
    for (const event of data.events ?? []) {
      useSimulationStore.getState().appendStreamEvent(event);
    }
    return data.events ?? [];
  }

  async predictEvent(payload) {
    const response = await fetch(this.buildApiUrl("/api/ml/predict"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `ml prediction request failed: ${response.status}`);
    }
    useSimulationStore.getState().setMlStatus({ lastPrediction: data, error: null });
    return data;
  }

  connectWebSocket(url = null) {
    if (this.socket || this.isSocketEnabled) {
      return;
    }
    this.isSocketEnabled = true;
    this.wsUrl = url ?? useSimulationStore.getState().settings.websocketUrl ?? DEFAULT_WS_URL;
    this.#openSocket();
  }

  disconnectWebSocket() {
    this.isSocketEnabled = false;
    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    clearInterval(this.pollTimer);
    this.pollTimer = null;
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    useSimulationStore.getState().setWsStatus("disconnected");
  }

  reconnectWebSocket(url = null) {
    const shouldResume = this.isSocketEnabled || Boolean(this.socket);
    this.disconnectWebSocket();
    if (shouldResume) {
      this.connectWebSocket(url);
    }
  }

  startRecentEventsPolling() {
    if (this.pollTimer) {
      return;
    }
    this.pollTimer = window.setInterval(() => {
      if (useSimulationStore.getState().eventStream.wsStatus === "connected") {
        return;
      }
      this.fetchRecentEvents().catch(() => {});
    }, POLL_RECENT_EVENTS_MS);
  }

  #openSocket() {
    if (!this.isSocketEnabled) {
      return;
    }

    useSimulationStore.getState().setWsStatus("connecting");
    try {
      this.socket = new WebSocket(this.wsUrl);
    } catch (error) {
      useSimulationStore.getState().setWsStatus("error");
      this.#scheduleReconnect();
      return;
    }

    this.socket.onopen = () => {
      useSimulationStore.getState().setWsStatus("connected");
      useSimulationStore.getState().updateSession({ connectedAt: new Date().toISOString() });
      this.publish("socket:status", { status: "connected" });
    };

    this.socket.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data);
        if (payload?.event_id != null) {
          useSimulationStore.getState().appendStreamEvent(payload);
          this.publish("stream:event", payload);
        } else if (payload?.timeline) {
          useSimulationStore.getState().applySimulationPayload(payload);
          this.publish("simulation:update", payload);
        }
      } catch (error) {
        this.publish("socket:error", { error: String(error) });
      }
    };

    this.socket.onerror = () => {
      useSimulationStore.getState().setWsStatus("error");
      this.publish("socket:status", { status: "error" });
    };

    this.socket.onclose = () => {
      this.socket = null;
      useSimulationStore.getState().setWsStatus("disconnected");
      this.publish("socket:status", { status: "disconnected" });
      this.#scheduleReconnect();
    };
  }

  #scheduleReconnect() {
    if (!this.isSocketEnabled) {
      return;
    }
    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = window.setTimeout(() => this.#openSocket(), RECONNECT_DELAY_MS);
  }
}

export const eventBus = new EventBus();
