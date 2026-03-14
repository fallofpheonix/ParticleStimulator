import { memo } from "react";

import {
  selectExperimentDatasets,
  selectExperimentRuns,
  selectSelectedDataset,
  selectSelectedRun,
  useExperimentStore,
} from "./ExperimentStore.js";
import DatasetBrowser from "./DatasetBrowser.jsx";
import ExperimentList from "./ExperimentList.jsx";
import ExperimentViewer from "./ExperimentViewer.jsx";
import RunHistory from "./RunHistory.jsx";

const ExperimentManager = memo(function ExperimentManager() {
  const runs = useExperimentStore(selectExperimentRuns);
  const datasets = useExperimentStore(selectExperimentDatasets);
  const selectedDataset = useExperimentStore(selectSelectedDataset);
  const selectedRun = useExperimentStore(selectSelectedRun);
  const eventData = useExperimentStore((state) => state.eventData);
  const particleTracks = useExperimentStore((state) => state.particleTracks);
  const selectExperimentRun = useExperimentStore((state) => state.selectExperimentRun);
  const selectExperimentDataset = useExperimentStore((state) => state.selectExperimentDataset);

  return (
    <>
      <div className="panel-header">
        <h2>Experiment Manager</h2>
        <p>Run registry, dataset browser, and export surface for simulation results</p>
      </div>
      <div className="analytics-grid analytics-grid--wide">
        <ExperimentList runs={runs} selectedRunId={selectedRun?.id ?? null} onSelect={selectExperimentRun} />
        <DatasetBrowser
          datasets={datasets}
          selectedDatasetId={selectedDataset?.id ?? null}
          onSelect={selectExperimentDataset}
        />
      </div>
      <div className="analytics-grid analytics-grid--wide">
        <ExperimentViewer
          run={selectedRun}
          datasets={datasets}
          eventData={eventData}
          particleTracks={particleTracks}
        />
        <RunHistory runs={runs} />
      </div>
    </>
  );
});

export default ExperimentManager;
