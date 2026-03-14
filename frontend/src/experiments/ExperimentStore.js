import { useSimulationStore } from "@store/simulationStore";

export const useExperimentStore = (selector) =>
  useSimulationStore((state) =>
    selector({
      experiments: state.experiments,
      eventData: state.eventData,
      particleTracks: state.particleTracks,
      detectorHits: state.detectorHits,
      selectExperimentDataset: state.selectExperimentDataset,
      selectExperimentRun: state.selectExperimentRun,
    })
  );

export const selectExperimentRuns = (state) => state.experiments.runHistory;
export const selectExperimentDatasets = (state) => state.experiments.datasets;
export const selectSelectedRun = (state) =>
  state.experiments.runHistory.find((run) => run.id === state.experiments.selectedRunId) ?? null;
export const selectSelectedDataset = (state) =>
  state.experiments.datasets.find((dataset) => dataset.id === state.experiments.selectedDatasetId) ?? null;
