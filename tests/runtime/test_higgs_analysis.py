from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

from analysis.higgs import HiggsTrainingConfig, _try_import_xgboost, discover_higgs_dataset, train_higgs_baseline


_HAS_ML_STACK = all(
    importlib.util.find_spec(module_name) is not None
    for module_name in ("numpy", "pandas", "sklearn", "joblib")
)


class HiggsDatasetTests(unittest.TestCase):
    def test_discover_higgs_dataset_prefers_known_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dataset = root / "data" / "HIGGS.csv.gz"
            dataset.parent.mkdir(parents=True)
            dataset.write_bytes(b"test")
            resolved = discover_higgs_dataset(project_root=root)
            self.assertEqual(resolved, dataset.resolve())


@unittest.skipUnless(_HAS_ML_STACK, "ML stack not available in interpreter")
class HiggsTrainingTests(unittest.TestCase):
    def test_training_pipeline_produces_metrics_and_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dataset = root / "HIGGS.csv"
            artifact = root / "artifact.joblib"

            with dataset.open("w", newline="") as handle:
                writer = csv.writer(handle)
                for index in range(200):
                    label = 1 if index % 2 == 0 else 0
                    signal_shift = 1.0 if label else -1.0
                    features = [
                        signal_shift + (feature_index * 0.01) + ((index % 7) * 0.02)
                        for feature_index in range(28)
                    ]
                    writer.writerow([label, *features])

            result = train_higgs_baseline(
                dataset_path=dataset,
                config=HiggsTrainingConfig(
                    model_backend="hist_gbdt",
                    sample_size=None,
                    n_estimators=12,
                    max_depth=3,
                    learning_rate=0.2,
                ),
                artifact_path=artifact,
            )

            self.assertEqual(result.dataset_path, dataset.resolve())
            self.assertTrue(artifact.exists())
            self.assertGreaterEqual(result.metrics.accuracy, 0.8)
            self.assertGreaterEqual(result.metrics.roc_auc, 0.8)

    def test_explicit_xgboost_backend_fails_with_actionable_error_when_runtime_missing(self) -> None:
        if _try_import_xgboost() is not None:
            self.skipTest("xgboost runtime is available in this interpreter")

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dataset = root / "HIGGS.csv"

            with dataset.open("w", newline="") as handle:
                writer = csv.writer(handle)
                for index in range(40):
                    label = index % 2
                    writer.writerow([label, *([float(index)] * 28)])

            with self.assertRaisesRegex(RuntimeError, "hist_gbdt"):
                train_higgs_baseline(
                    dataset_path=dataset,
                    config=HiggsTrainingConfig(
                        model_backend="xgboost",
                        sample_size=None,
                        n_estimators=4,
                        max_depth=2,
                    ),
                )


if __name__ == "__main__":
    unittest.main()
