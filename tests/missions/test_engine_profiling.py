"""Profiling integration tests for the backend engine."""

from __future__ import annotations

import json
from pathlib import Path

from backend.engine import MissionRuntime, ProfilerSession
from backend.mission_runtime.schema import MissionSchemaValidator


def test_profiler_session_emits_artifact(tmp_path: Path) -> None:
    session = ProfilerSession(run_id="unit-test", output_dir=tmp_path)
    with session.profile_block("setup", {"engine_id": "engine_001"}):
        pass
    session.record_gpu_metrics("setup", utilisation=0.0, memory_mb=0.0)
    artifact = session.close()

    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["run_id"] == "unit-test"
    assert data["records"][0]["name"] == "setup"
    assert data["summary"]["sections"] == 1


def test_mission_runtime_profiles_execution(tmp_path: Path) -> None:
    validator = MissionSchemaValidator()
    mission = validator.load_from_file(Path("missions/mission_short.json"))

    session = ProfilerSession(run_id="runtime-test", output_dir=tmp_path)
    runtime = MissionRuntime(profiler=session)
    result = runtime.execute(mission)

    artifact = result.artifact_path
    assert artifact.exists()

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["run_id"] == "runtime-test"
    assert payload["summary"]["sections"] == len(mission)
