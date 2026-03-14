import { memo, useEffect, useMemo, useState } from "react";
import { FormProvider, useForm, useWatch } from "react-hook-form";

import { defaultPhysicsParameters } from "@app/defaults";
import { useSimulationStore } from "@store/simulationStore";

import BeamConfig from "./BeamConfig.jsx";
import CollisionConfig from "./CollisionConfig.jsx";
import DetectorConfig from "./DetectorConfig.jsx";
import MagnetConfig from "./MagnetConfig.jsx";

const PRESET_STORAGE_KEY = "particle-stimulator:physics-presets";

const BUILTIN_PRESETS = {
  "LHC Run 3": {
    ...defaultPhysicsParameters,
    beam_energy_gev: 6800,
    beam_intensity: 0.88,
    magnetic_field_t: 3.8,
    event_probability: 0.81
  },
  "Precision Tracking": {
    ...defaultPhysicsParameters,
    beam_particles_per_side: 8,
    detector_resolution_pct: 4,
    tracker_resolution_um: 18,
    detector_noise_pct: 0.9
  },
  "Low Noise Calorimetry": {
    ...defaultPhysicsParameters,
    detector_resolution_pct: 6,
    detector_noise_pct: 0.4,
    noise_model: "gaussian"
  },
  "Wide Aperture Scan": {
    ...defaultPhysicsParameters,
    aperture_radius_m: 2.8,
    chamber_half_length_m: 3.8,
    beam_spread_m: 0.03
  }
};

const TABS = [
  ["beam", "Beam"],
  ["magnet", "Magnet"],
  ["collision", "Collision"],
  ["detector", "Detector"]
];

function useStoredPresets() {
  const [presets, setPresets] = useState(() => {
    try {
      const raw = window.localStorage.getItem(PRESET_STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  });

  useEffect(() => {
    window.localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(presets));
  }, [presets]);

  return [presets, setPresets];
}

const ConfigSynchronizer = memo(function ConfigSynchronizer({ control, onValidValues }) {
  const values = useWatch({ control });
  useEffect(() => {
    onValidValues(values);
  }, [onValidValues, values]);
  return null;
});

const ConfigPanel = memo(function ConfigPanel() {
  const parameters = useSimulationStore((state) => state.simulationParameters);
  const setPhysicsParameters = useSimulationStore((state) => state.setPhysicsParameters);
  const [tab, setTab] = useState("beam");
  const [showExport, setShowExport] = useState(false);
  const [presets, setPresets] = useStoredPresets();

  const methods = useForm({
    mode: "onChange",
    defaultValues: parameters
  });

  const {
    control,
    reset,
    getValues,
    formState: { errors }
  } = methods;

  useEffect(() => {
    reset(parameters);
  }, [parameters, reset]);

  const presetNames = useMemo(
    () => [...Object.keys(BUILTIN_PRESETS), ...Object.keys(presets)],
    [presets]
  );

  const handleValidValues = (values) => {
    if (Object.keys(errors).length === 0) {
      setPhysicsParameters(values);
    }
  };

  const loadPreset = (name) => {
    const preset = BUILTIN_PRESETS[name] || presets[name];
    if (!preset) {
      return;
    }
    reset(preset);
    setPhysicsParameters(preset);
  };

  const savePreset = () => {
    const name = window.prompt("Preset name");
    if (!name) {
      return;
    }
    const next = getValues();
    setPresets((current) => ({ ...current, [name]: next }));
  };

  const exportJson = JSON.stringify(getValues(), null, 2);

  const currentPanel =
    tab === "beam" ? <BeamConfig /> : tab === "magnet" ? <MagnetConfig /> : tab === "collision" ? <CollisionConfig /> : <DetectorConfig />;

  return (
    <FormProvider {...methods}>
      <ConfigSynchronizer control={control} onValidValues={handleValidValues} />
      <div className="config-shell">
        <div className="config-tabs">
          {TABS.map(([key, label]) => (
            <button
              key={key}
              type="button"
              className={tab === key ? "config-tab config-tab--active" : "config-tab ghost"}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </div>
        {currentPanel}
        <div className="config-preset-bar">
          <select defaultValue="" onChange={(event) => loadPreset(event.target.value)}>
            <option value="" disabled>
              Load preset
            </option>
            {presetNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          <button type="button" className="ghost" onClick={savePreset}>
            Save Preset
          </button>
          <button type="button" className="ghost" onClick={() => { reset(defaultPhysicsParameters); setPhysicsParameters(defaultPhysicsParameters); }}>
            Reset Physics
          </button>
          <button type="button" className="ghost" onClick={() => setShowExport((open) => !open)}>
            {showExport ? "Hide JSON" : "Export JSON"}
          </button>
        </div>
        {Object.keys(errors).length ? (
          <div className="error-banner">Validation errors: {Object.keys(errors).join(", ")}</div>
        ) : null}
        {showExport ? <pre className="debug-pre config-export">{exportJson}</pre> : null}
      </div>
    </FormProvider>
  );
});

export default ConfigPanel;
