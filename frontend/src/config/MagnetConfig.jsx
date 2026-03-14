import { memo } from "react";

import { RangeField, SectionDivider } from "./Fields.jsx";

const MagnetConfig = memo(function MagnetConfig() {
  return (
    <div className="config-panel-grid">
      <SectionDivider title="Magnet Configuration" hint="Beam steering and focusing lattice" />
      <RangeField name="magnetic_field_t" label="Dipole Field" min={0} max={8} step={0.1} unit="T" />
      <RangeField
        name="quadrupole_gradient_t_per_m"
        label="Quadrupole Strength"
        min={0}
        max={1}
        step={0.01}
        unit="T/m"
      />
      <RangeField name="rf_field_v_m" label="RF Voltage" min={0} max={800000} step={10000} unit="V/m" />
      <RangeField name="aperture_radius_m" label="Aperture Radius" min={0.1} max={4} step={0.05} unit="m" />
      <RangeField name="chamber_half_length_m" label="Chamber Half Length" min={0.5} max={6} step={0.1} unit="m" />
    </div>
  );
});

export default MagnetConfig;
