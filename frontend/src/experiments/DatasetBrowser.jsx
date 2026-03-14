import { memo } from "react";

const DatasetBrowser = memo(function DatasetBrowser({ datasets, selectedDatasetId, onSelect }) {
  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Datasets</h3>
        <span>simulation outputs</span>
      </div>
      <div className="control-grid">
        {datasets.map((dataset) => (
          <button
            key={dataset.id}
            type="button"
            className={selectedDatasetId === dataset.id ? "config-tab config-tab--active" : "ghost"}
            onClick={() => onSelect(dataset.id)}
          >
            {dataset.name} ({dataset.records})
          </button>
        ))}
      </div>
    </section>
  );
});

export default DatasetBrowser;
