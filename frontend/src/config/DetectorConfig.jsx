import { memo } from "react";

import { RangeField, SectionDivider, SelectField } from "./Fields.jsx";

const DetectorConfig = memo(function DetectorConfig() {
  return (
    <div className="config-panel-grid">
      <SectionDivider title="Detector Configuration" hint="Tracker precision and calorimeter noise shaping" />
      <RangeField
        name="tracker_resolution_um"
        label="Tracker Resolution"
        min={5}
        max={150}
        step={1}
        unit="um"
      />
      <RangeField
        name="detector_resolution_pct"
        label="Detector Resolution"
        min={1}
        max={20}
        step={0.5}
        unit="%"
      />
      <RangeField name="detector_noise_pct" label="Noise Level" min={0} max={15} step={0.5} unit="%" />
      <SelectField
        name="noise_model"
        label="Noise Model"
        options={["poisson", "gaussian", "none"]}
        hint="Applied only in the frontend readout layer for now"
      />
    </div>
  );
});

export default DetectorConfig;
