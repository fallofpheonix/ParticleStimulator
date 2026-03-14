import { memo, useMemo, useState } from "react";

const ChatPanel = memo(function ChatPanel({ messages, onSend }) {
  const [draft, setDraft] = useState("");
  const renderedMessages = useMemo(() => messages.slice(-8), [messages]);

  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Chat</h3>
        <span>{renderedMessages.length} messages</span>
      </div>
      <div className="chat-window">
        {renderedMessages.map((message) => (
          <div key={message.id} className={`chat-message chat-message--${message.kind ?? "text"}`}>
            <strong>{message.author}</strong>
            <p>{message.body}</p>
          </div>
        ))}
      </div>
      <form
        className="chat-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (!draft.trim()) {
            return;
          }
          onSend(draft.trim());
          setDraft("");
        }}
      >
        <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Share run notes or detector anomalies" />
        <button type="submit">Send</button>
      </form>
    </section>
  );
});

export default ChatPanel;
