import { memo, useState } from "react";

import { eventBus } from "@services/eventBus";

const ConnectionSettings = memo(function ConnectionSettings({ apiBaseUrl, websocketUrl, onCommit }) {
  const [draftApi, setDraftApi] = useState(apiBaseUrl);
  const [draftWs, setDraftWs] = useState(websocketUrl);

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Connections</h3>
        <span>transport</span>
      </div>
      <div className="control-grid">
        <label>
          <span>API URL</span>
          <input value={draftApi} onChange={(event) => setDraftApi(event.target.value)} />
        </label>
        <label>
          <span>WebSocket URL</span>
          <input value={draftWs} onChange={(event) => setDraftWs(event.target.value)} />
        </label>
      </div>
      <div className="actions">
        <button
          type="button"
          onClick={() => {
            onCommit({ apiBaseUrl: draftApi, websocketUrl: draftWs });
            eventBus.checkHealth().catch(() => {});
            eventBus.loadDefaults().catch(() => {});
            eventBus.reconnectWebSocket(draftWs);
          }}
        >
          Apply Connection Settings
        </button>
      </div>
    </section>
  );
});

export default ConnectionSettings;
