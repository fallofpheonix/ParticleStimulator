"""Tests for the backend platform infrastructure modules.

Covers:
    - data_pipeline: EventSerializer, EventDatabase, DatasetLoader, DataPipelineEventStream
    - config: ConfigLoader, EnvironmentConfig, RuntimeParameters
    - infrastructure: JobQueue, ParallelWorker, GPUExecutor
    - api: FastAPI endpoints via TestClient
    - event_stream: SimulationWebSocketServer (unit-level)
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


# ---------------------------------------------------------------------------
# data_pipeline tests
# ---------------------------------------------------------------------------

class TestEventSerializer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.events = [
            {"event_id": 1, "triggered": True, "n_jets": 2, "jets": [{"pt_gev": 45.0}]},
            {"event_id": 2, "triggered": False, "n_jets": 0, "jets": []},
        ]

    def test_json_round_trip(self):
        from backend.data_pipeline.event_serializer import EventSerializer
        path = EventSerializer.to_json(self.events, f"{self.tmp}/ev.json")
        self.assertTrue(path.exists())
        loaded = EventSerializer.from_json(path)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["event_id"], 1)

    def test_parquet_round_trip(self):
        from backend.data_pipeline.event_serializer import EventSerializer
        path = EventSerializer.to_parquet(self.events, f"{self.tmp}/ev.parquet")
        self.assertTrue(path.exists())
        loaded = EventSerializer.from_parquet(path)
        self.assertEqual(len(loaded), 2)

    def test_hdf5_round_trip(self):
        from backend.data_pipeline.event_serializer import EventSerializer
        path = EventSerializer.to_hdf5(self.events, f"{self.tmp}/ev.h5")
        self.assertTrue(path.exists())
        loaded = EventSerializer.from_hdf5(path)
        self.assertEqual(len(loaded), 2)
        self.assertIn("event_id", loaded[0])

    def test_json_creates_parent_dirs(self):
        from backend.data_pipeline.event_serializer import EventSerializer
        path = EventSerializer.to_json(self.events, f"{self.tmp}/sub/dir/ev.json")
        self.assertTrue(path.exists())


class TestEventDatabase(unittest.TestCase):
    def test_store_and_retrieve(self):
        from backend.data_pipeline.event_database import EventDatabase
        with tempfile.TemporaryDirectory() as tmp:
            db = EventDatabase(storage_dir=tmp)
            db.store({"event_id": 10, "triggered": True})
            db.store({"event_id": 11, "triggered": False})
            self.assertEqual(db.count, 2)
            e = db.get_by_id(10)
            self.assertIsNotNone(e)
            self.assertTrue(e["triggered"])

    def test_query_by_field(self):
        from backend.data_pipeline.event_database import EventDatabase
        with tempfile.TemporaryDirectory() as tmp:
            db = EventDatabase(storage_dir=tmp)
            db.store_batch([
                {"event_id": i, "triggered": i % 2 == 0}
                for i in range(10)
            ])
            triggered = db.query(triggered=True)
            self.assertEqual(len(triggered), 5)

    def test_get_latest(self):
        from backend.data_pipeline.event_database import EventDatabase
        with tempfile.TemporaryDirectory() as tmp:
            db = EventDatabase(storage_dir=tmp)
            for i in range(20):
                db.store({"event_id": i})
            latest = db.get_latest(5)
            self.assertEqual(len(latest), 5)
            self.assertEqual(latest[-1]["event_id"], 19)

    def test_flush_and_reload_json(self):
        from backend.data_pipeline.event_database import EventDatabase
        with tempfile.TemporaryDirectory() as tmp:
            db = EventDatabase(storage_dir=tmp)
            db.store({"event_id": 99, "value": "test"})
            path = db.flush_json("events.json")
            self.assertTrue(path.exists())
            db2 = EventDatabase(storage_dir=tmp)
            n = db2.load_json("events.json")
            self.assertEqual(n, 1)
            self.assertEqual(db2.get_by_id(99)["value"], "test")


class TestDatasetLoader(unittest.TestCase):
    def test_load_json(self):
        from backend.data_pipeline.dataset_loader import DatasetLoader
        with tempfile.TemporaryDirectory() as tmp:
            records = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
            p = Path(tmp) / "data.json"
            p.write_text(json.dumps(records))
            loaded = DatasetLoader().load(p)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0]["x"], 1)

    def test_load_parquet(self):
        from backend.data_pipeline.dataset_loader import DatasetLoader
        from backend.data_pipeline.event_serializer import EventSerializer
        with tempfile.TemporaryDirectory() as tmp:
            events = [{"event_id": 1, "val": 3.14}]
            p = EventSerializer.to_parquet(events, f"{tmp}/ev.parquet")
            loaded = DatasetLoader().load(p)
            self.assertEqual(len(loaded), 1)

    def test_unsupported_format_raises(self):
        from backend.data_pipeline.dataset_loader import DatasetLoader
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "data.xyz"
            p.write_text("irrelevant")
            with self.assertRaises(ValueError):
                DatasetLoader().load(p)

    def test_missing_file_raises(self):
        from backend.data_pipeline.dataset_loader import DatasetLoader
        with self.assertRaises(FileNotFoundError):
            DatasetLoader().load("/nonexistent/path.json")

    def test_list_datasets(self):
        from backend.data_pipeline.dataset_loader import DatasetLoader
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.json").write_text("[]")
            (Path(tmp) / "b.parquet").write_bytes(b"")  # dummy
            (Path(tmp) / "c.txt").write_text("ignored")
            files = DatasetLoader.list_datasets(tmp)
            self.assertIn("a.json", files)
            self.assertNotIn("c.txt", files)


class TestDataPipelineEventStream(unittest.TestCase):
    def test_push_and_get_latest(self):
        from backend.data_pipeline.event_stream import DataPipelineEventStream
        stream = DataPipelineEventStream()
        for i in range(5):
            stream.push({"event_id": i})
        self.assertEqual(stream.count, 5)
        latest = stream.get_latest(3)
        self.assertEqual(len(latest), 3)
        self.assertEqual(latest[-1]["event_id"], 4)

    def test_push_stores_to_database(self):
        from backend.data_pipeline.event_stream import DataPipelineEventStream
        from backend.data_pipeline.event_database import EventDatabase
        with tempfile.TemporaryDirectory() as tmp:
            stream = DataPipelineEventStream()
            db = EventDatabase(storage_dir=tmp)
            stream.attach_database(db)
            stream.push({"event_id": 77, "val": "x"})
            self.assertEqual(db.count, 1)
            self.assertEqual(db.get_by_id(77)["val"], "x")

    def test_max_buffer_truncation(self):
        from backend.data_pipeline.event_stream import DataPipelineEventStream
        stream = DataPipelineEventStream(max_buffer=3)
        for i in range(10):
            stream.push({"event_id": i})
        self.assertEqual(stream.count, 3)
        self.assertEqual(stream.get_latest(1)[0]["event_id"], 9)


# ---------------------------------------------------------------------------
# config tests
# ---------------------------------------------------------------------------

class TestConfigLoader(unittest.TestCase):
    def test_loads_defaults_when_no_file(self):
        from backend.config.config_loader import ConfigLoader
        cfg = ConfigLoader().load()
        self.assertIn("beam_energy_gev", cfg)
        self.assertEqual(cfg["beam_energy_gev"], 6500.0)

    def test_loads_json_override(self):
        from backend.config.config_loader import ConfigLoader
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "cfg.json"
            p.write_text(json.dumps({"beam_energy_gev": 13000.0}))
            cfg = ConfigLoader(path=p).load()
            self.assertEqual(cfg["beam_energy_gev"], 13000.0)

    def test_save_defaults(self):
        from backend.config.config_loader import ConfigLoader
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "defaults.json"
            ConfigLoader().save_defaults(dest)
            self.assertTrue(dest.exists())
            data = json.loads(dest.read_text())
            self.assertIn("beam_energy_gev", data)


class TestEnvironmentConfig(unittest.TestCase):
    def test_load_empty_when_no_env_vars(self):
        from backend.config.environment_config import EnvironmentConfig
        overrides = EnvironmentConfig().load()
        self.assertIsInstance(overrides, dict)

    def test_reads_beam_energy_from_env(self):
        from backend.config.environment_config import EnvironmentConfig
        os.environ["SIM_BEAM_ENERGY_GEV"] = "13000.0"
        try:
            overrides = EnvironmentConfig().load()
            self.assertEqual(overrides["beam_energy_gev"], 13000.0)
        finally:
            del os.environ["SIM_BEAM_ENERGY_GEV"]

    def test_list_recognised(self):
        from backend.config.environment_config import EnvironmentConfig
        names = EnvironmentConfig.list_recognised()
        self.assertIn("SIM_BEAM_ENERGY_GEV", names)
        self.assertIn("SIM_MAX_WORKERS", names)


class TestRuntimeParameters(unittest.TestCase):
    def test_set_and_get(self):
        from backend.config.runtime_parameters import RuntimeParameters
        rp = RuntimeParameters()
        rp.set("max_workers", 8)
        self.assertEqual(rp.get("max_workers"), 8)

    def test_default_returns_none(self):
        from backend.config.runtime_parameters import RuntimeParameters
        rp = RuntimeParameters()
        self.assertIsNone(rp.get("nonexistent"))
        self.assertEqual(rp.get("nonexistent", 42), 42)

    def test_update_bulk(self):
        from backend.config.runtime_parameters import RuntimeParameters
        rp = RuntimeParameters()
        rp.update({"max_workers": 2, "random_seed": 99})
        self.assertEqual(rp.all, {"max_workers": 2, "random_seed": 99})

    def test_strict_mode_rejects_unknown(self):
        from backend.config.runtime_parameters import RuntimeParameters
        rp = RuntimeParameters(strict=True)
        with self.assertRaises(KeyError):
            rp.set("unknown_key", "value")

    def test_type_validation(self):
        from backend.config.runtime_parameters import RuntimeParameters
        rp = RuntimeParameters()
        with self.assertRaises(TypeError):
            rp.set("max_workers", "not_an_int")

    def test_delete_and_clear(self):
        from backend.config.runtime_parameters import RuntimeParameters
        rp = RuntimeParameters()
        rp.set("max_workers", 4)
        rp.delete("max_workers")
        self.assertIsNone(rp.get("max_workers"))
        rp.set("random_seed", 1)
        rp.clear()
        self.assertEqual(rp.all, {})

    def test_schema(self):
        from backend.config.runtime_parameters import RuntimeParameters
        schema = RuntimeParameters.schema()
        self.assertIn("max_workers", schema)
        self.assertIn("beam_energy_gev", schema)


# ---------------------------------------------------------------------------
# infrastructure tests
# ---------------------------------------------------------------------------

class TestJobQueue(unittest.TestCase):
    def test_enqueue_dequeue_fifo(self):
        from backend.infrastructure.job_queue import JobQueue
        q = JobQueue()
        q.enqueue("j1", {"a": 1})
        q.enqueue("j2", {"a": 2})
        job = q.dequeue()
        self.assertEqual(job["job_id"], "j1")

    def test_priority_ordering(self):
        from backend.infrastructure.job_queue import JobQueue
        q = JobQueue()
        q.enqueue("low", {}, priority=1)
        q.enqueue("high", {}, priority=10)
        q.enqueue("med", {}, priority=5)
        first = q.dequeue()
        self.assertEqual(first["job_id"], "high")

    def test_empty_dequeue_returns_none(self):
        from backend.infrastructure.job_queue import JobQueue
        q = JobQueue()
        self.assertIsNone(q.dequeue())

    def test_size_and_is_empty(self):
        from backend.infrastructure.job_queue import JobQueue
        q = JobQueue()
        self.assertTrue(q.is_empty)
        q.enqueue("x", {})
        self.assertEqual(q.size, 1)
        self.assertFalse(q.is_empty)

    def test_drain(self):
        from backend.infrastructure.job_queue import JobQueue
        q = JobQueue()
        for i in range(5):
            q.enqueue(f"j{i}", {})
        all_jobs = q.drain()
        self.assertEqual(len(all_jobs), 5)
        self.assertTrue(q.is_empty)


class TestParallelWorker(unittest.TestCase):
    def test_run_batch_success(self):
        from backend.infrastructure.parallel_worker import ParallelWorker
        pw = ParallelWorker(max_workers=2)
        results = pw.run_batch([1, 2, 3], lambda x: x ** 2)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.success for r in results))
        self.assertEqual(pw.success_count, 3)
        self.assertEqual(pw.failure_count, 0)

    def test_run_batch_handles_errors(self):
        from backend.infrastructure.parallel_worker import ParallelWorker
        pw = ParallelWorker(max_workers=2)

        def bad_runner(x):
            if x == 2:
                raise ValueError("intentional error")
            return x

        results = pw.run_batch([1, 2, 3], bad_runner)
        self.assertEqual(len(results), 3)
        failures = [r for r in results if not r.success]
        self.assertEqual(len(failures), 1)
        self.assertIn("intentional error", failures[0].error)

    def test_run_queue(self):
        from backend.infrastructure.job_queue import JobQueue
        from backend.infrastructure.parallel_worker import ParallelWorker
        q = JobQueue()
        q.enqueue("a", {"value": 10})
        q.enqueue("b", {"value": 20})
        pw = ParallelWorker(max_workers=2)
        results = pw.run_queue(q, lambda payload: payload.get("value", 0) * 2)
        self.assertEqual(len(results), 2)
        self.assertTrue(q.is_empty)


class TestGPUExecutor(unittest.TestCase):
    def test_status(self):
        from backend.infrastructure.gpu_executor import GPUExecutor
        gpu = GPUExecutor(device_id=0)
        s = gpu.status()
        self.assertIn("device_id", s)
        self.assertIn("available", s)

    def test_execute_particle_push_fallback(self):
        from backend.infrastructure.gpu_executor import GPUExecutor
        gpu = GPUExecutor(enabled=False, fallback_to_cpu=True)
        pos = [[0.0, 0.0, 0.0]]
        vel = [[1.0, 0.0, 0.0]]
        fields = [(0.0, 0.0, 0.0)]
        new_pos, new_vel = gpu.execute_particle_push(pos, vel, fields, 1e-10)
        self.assertEqual(new_pos, pos)

    def test_matrix_batch(self):
        import numpy as np
        from backend.infrastructure.gpu_executor import GPUExecutor
        gpu = GPUExecutor()
        mats = [np.eye(2)] * 3
        vecs = [np.array([1.0, 2.0])] * 3
        results = gpu.execute_matrix_batch(mats, vecs)
        self.assertEqual(len(results), 3)


# ---------------------------------------------------------------------------
# FastAPI endpoint tests
# ---------------------------------------------------------------------------

class TestFastAPIEndpoints(unittest.TestCase):
    def setUp(self):
        try:
            from fastapi.testclient import TestClient
        except (ImportError, ModuleNotFoundError):
            self.skipTest("FastAPI or httpx not available")
            return
        from backend.api.app import create_app
        self.tmp = tempfile.mkdtemp()
        self.app = create_app(storage_dir=self.tmp, datasets_dir=self.tmp)
        self.client = TestClient(self.app)

    def test_health(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_events_empty(self):
        r = self.client.get("/api/events")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("events", data)
        self.assertEqual(data["total"], 0)

    def test_datasets_empty(self):
        r = self.client.get("/api/datasets")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["total"], 0)

    def test_simulate(self):
        r = self.client.post(
            "/api/simulate",
            json={"particles_per_bunch": 4, "simulation_steps": 50},
        )
        self.assertEqual(r.status_code, 200)
        result = r.json()
        self.assertIn("event_id", result)

    def test_events_after_simulate(self):
        self.client.post("/api/simulate", json={"simulation_steps": 50})
        r = self.client.get("/api/events?n=10")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertGreaterEqual(data["total"], 1)

    def test_event_not_found(self):
        r = self.client.get("/api/events?event_id=99999")
        self.assertEqual(r.status_code, 404)

    def test_dataset_not_found(self):
        r = self.client.get("/api/datasets/nonexistent.json")
        self.assertEqual(r.status_code, 404)

    def test_analysis_significance(self):
        self.client.post("/api/simulate", json={"simulation_steps": 50})
        r = self.client.post("/api/analysis", json={"analysis_type": "significance"})
        self.assertEqual(r.status_code, 200)
        result = r.json()
        self.assertIn("n_signal", result["result"])

    def test_analysis_histogram(self):
        self.client.post("/api/simulate", json={"simulation_steps": 50})
        r = self.client.post(
            "/api/analysis",
            json={"analysis_type": "histogram", "parameters": {"bins": 10, "high": 200.0}},
        )
        self.assertEqual(r.status_code, 200)

    def test_analysis_unknown_type(self):
        r = self.client.post("/api/analysis", json={"analysis_type": "unknown_type"})
        self.assertEqual(r.status_code, 400)

    def test_analysis_no_events(self):
        from backend.api.app import create_app
        empty_app = create_app(storage_dir=tempfile.mkdtemp(), datasets_dir=tempfile.mkdtemp())
        from fastapi.testclient import TestClient
        c = TestClient(empty_app)
        r = c.post("/api/analysis", json={"analysis_type": "significance"})
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.json()["result"])


# ---------------------------------------------------------------------------
# WebSocket server unit tests
# ---------------------------------------------------------------------------

class TestSimulationWebSocketServer(unittest.TestCase):
    def test_status(self):
        from backend.event_stream.websocket_server import SimulationWebSocketServer
        ws = SimulationWebSocketServer(host="localhost", port=8001)
        s = ws.status()
        self.assertEqual(s["port"], 8001)
        self.assertEqual(s["connected_clients"], 0)
        self.assertIn("ws://", s["endpoint"])
    def test_broadcast_no_clients(self):
        from backend.event_stream.websocket_server import SimulationWebSocketServer
        ws = SimulationWebSocketServer()
        # Should not raise even with no clients.
        ws.broadcast_event({"event_id": 1})
        ws.broadcast_progress({"step": 10, "total": 100})
        ws.broadcast_detector({"tracker_hits": 5})

    def test_attach_to_app(self):
        from fastapi import FastAPI
        from backend.event_stream.websocket_server import SimulationWebSocketServer
        app = FastAPI()
        ws = SimulationWebSocketServer()
        ws.attach_to_app(app, path="/events")
        paths = [r.path for r in app.routes]
        self.assertIn("/events", paths)


if __name__ == "__main__":
    unittest.main()
