import { memo } from "react";

import { useSimulationStore } from "@store/simulationStore";

import ConnectionSettings from "./ConnectionSettings.jsx";
import SimulationDefaults from "./SimulationDefaults.jsx";
import ThemeSelector from "./ThemeSelector.jsx";

const SettingsPanel = memo(function SettingsPanel() {
  const settings = useSimulationStore((state) => state.settings);
  const updateSettings = useSimulationStore((state) => state.updateSettings);

  return (
    <>
      <div className="panel-header">
        <h2>Settings</h2>
        <p>Theme, transport endpoints, and persisted simulation defaults</p>
      </div>
      <div className="analytics-grid analytics-grid--wide">
        <ThemeSelector theme={settings.theme} onChange={(theme) => updateSettings({ theme })} />
        <ConnectionSettings
          apiBaseUrl={settings.apiBaseUrl}
          websocketUrl={settings.websocketUrl}
          onCommit={updateSettings}
        />
      </div>
      <SimulationDefaults defaults={settings.defaultPhysicsParameters} onCommit={updateSettings} />
    </>
  );
});

export default SettingsPanel;
