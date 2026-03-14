import { memo, useMemo, useState } from "react";

import { useSimulationStore } from "@store/simulationStore";

import ChatPanel from "./ChatPanel.jsx";
import SessionManager from "./SessionManager.jsx";
import SharedControls from "./SharedControls.jsx";
import UserPresence from "./UserPresence.jsx";

const CollaborationPanel = memo(function CollaborationPanel() {
  const session = useSimulationStore((state) => state.userSession);
  const [messages, setMessages] = useState([
    { id: "m-1", author: "system", body: "Shared session ready.", kind: "system" },
    { id: "m-2", author: "A. Chen", body: "Monitoring jet multiplicity in the latest run." }
  ]);

  const users = useMemo(
    () => [
      { id: session.sessionId, name: "You", role: "host", color: "#7dd3fc", online: true },
      { id: "u-2", name: "A. Chen", role: "analysis", color: "#fb7185", online: true },
      { id: "u-3", name: "M. Iqbal", role: "detector", color: "#34d399", online: true }
    ],
    [session.sessionId]
  );

  return (
    <div className="collaboration-grid">
      <UserPresence users={users} />
      <SharedControls users={users} />
      <ChatPanel
        messages={messages}
        onSend={(body) =>
          setMessages((current) => [...current, { id: `m-${current.length + 1}`, author: "You", body, kind: "text" }])
        }
      />
      <SessionManager
        onShare={() =>
          setMessages((current) => [
            ...current,
            { id: `m-${current.length + 1}`, author: "system", body: "Current configuration shared with room.", kind: "system" }
          ])
        }
      />
    </div>
  );
});

export default CollaborationPanel;
