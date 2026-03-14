import { memo } from "react";

import { RangeField, SectionDivider } from "./Fields.jsx";

const BeamConfig = memo(function BeamConfig() {
  return (
    <div className="config-panel-grid">
      <SectionDivider title="Beam Configuration" hint="Injection and bunch population controls" />
      <RangeField name="beam_energy_gev" label="Beam Energy" min={100} max={7000} step={50} unit="GeV" />
      <RangeField name="beam_intensity" label="Beam Intensity" min={0.1} max={1} step={0.01} />
      <RangeField name="beam_particles_per_side" label="Particle Count / Side" min={2} max={16} step={1} />
      <RangeField name="beam_spread_m" label="Beam Spread" min={0.002} max={0.08} step={0.002} unit="m" />
      <RangeField name="longitudinal_spacing_m" label="Bunch Spacing" min={0.002} max={0.05} step={0.002} unit="m" />
    </div>
  );
});

export default BeamConfig;
