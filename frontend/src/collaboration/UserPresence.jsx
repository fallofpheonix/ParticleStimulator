import { memo } from "react";

const UserPresence = memo(function UserPresence({ users }) {
  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>User Presence</h3>
        <span>{users.length} active</span>
      </div>
      <div className="presence-list">
        {users.map((user) => (
          <div key={user.id} className="presence-row">
            <div className="presence-avatar" style={{ "--presence-color": user.color }}>
              <span>{user.name.slice(0, 1)}</span>
            </div>
            <div className="presence-meta">
              <strong>{user.name}</strong>
              <small>{user.role}</small>
            </div>
            <span className={user.online ? "presence-state presence-state--online" : "presence-state"}>
              {user.online ? "online" : "idle"}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
});

export default UserPresence;
