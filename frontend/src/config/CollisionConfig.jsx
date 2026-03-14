import { memo } from "react";

import { RangeField, SectionDivider } from "./Fields.jsx";

const CollisionConfig = memo(function CollisionConfig() {
  return (
    <div className="config-panel-grid">
      <SectionDivider title="Collision Configuration" hint="Interaction region and event-generation pacing" />
      <RangeField
        name="interaction_radius_m"
        label="Interaction Radius"
        min={0.01}
        max={0.12}
        step={0.005}
        unit="m"
      />
      <RangeField name="event_probability" label="Event Probability" min={0.05} max={1} step={0.01} />
      <RangeField name="steps" label="Simulation Steps" min={10} max={400} step={10} />
      <RangeField name="seed" label="Random Seed" min={0} max={999999} step={1} type="number" />
    </div>
  );
});

export default CollisionConfig;
