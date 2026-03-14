import { memo } from "react";

const MainLayout = memo(function MainLayout({
  controlPanel,
  scene,
  analytics,
  eventStream,
  timeline,
  debugPanel
}) {
  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Particle Stimulator</p>
          <h1>Integrated Simulator Workspace</h1>
        </div>
        {debugPanel}
      </header>

      <main className="workspace">
        <aside className="panel controls">{controlPanel}</aside>
        <section className="panel visualization">{scene}</section>
        <aside className="panel summary">{eventStream}</aside>
      </main>

      <section className="bottom-row">
        <section className="panel chart-panel">{analytics}</section>
        <section className="panel chart-panel">{timeline}</section>
      </section>
    </div>
  );
});

export default MainLayout;
