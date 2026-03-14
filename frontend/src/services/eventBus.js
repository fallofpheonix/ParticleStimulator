import { useSimulationStore } from "@store/simulationStore";

const API_BASE = "";
const DEFAULT_WS_URL = "ws://127.0.0.1:8001/events";
const RECONNECT_DELAY_MS = 3000;

class EventBus {
  constructor() {
    this.listeners = new Map();
    this.socket = null;
    this.reconnectTimer = null;
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

  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE}/api/health`);
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
      const response = await fetch(`${API_BASE}/api/defaults`);
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
      const response = await fetch(`${API_BASE}/api/simulate`, {
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

  connectWebSocket(url = DEFAULT_WS_URL) {
    if (this.socket || this.isSocketEnabled) {
      return;
    }
    this.isSocketEnabled = true;
    this.wsUrl = url;
    this.#openSocket();
  }

  disconnectWebSocket() {
    this.isSocketEnabled = false;
    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    useSimulationStore.getState().setWsStatus("disconnected");
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
