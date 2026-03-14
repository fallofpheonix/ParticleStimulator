import { memo } from "react";

import ModelMetrics from "./ModelMetrics.jsx";
import PredictionViewer from "./PredictionViewer.jsx";
import TrainingPanel from "./TrainingPanel.jsx";

const MLPanel = memo(function MLPanel() {
  return (
    <>
      <div className="panel-header">
        <h2>ML Workbench</h2>
        <p>Train the Higgs classifier, inspect metrics, and classify selected collision events</p>
      </div>
      <div className="analytics-grid analytics-grid--wide">
        <TrainingPanel />
        <ModelMetrics />
      </div>
      <PredictionViewer />
    </>
  );
});

export default MLPanel;
