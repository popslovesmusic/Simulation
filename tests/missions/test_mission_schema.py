"""Regression coverage for mission schema validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.mission_runtime.schema import MissionSchemaValidator


TEST_MISSIONS = Path("missions")


@pytest.mark.parametrize(
    "mission_name",
    [
        "mission_rc_0.5.json",
        "mission_rc_2.0.json",
        "mission_static.json",
    ],
)
def test_known_mission_files_validate(mission_name: str) -> None:
    mission_path = TEST_MISSIONS / mission_name
    validator = MissionSchemaValidator()
    commands = validator.load_from_file(mission_path)
    result = validator.validate(commands)

    assert result.is_valid(), result.errors
    assert result.command_counts.get("create_engine") == 1
    assert "run_mission" in result.command_counts
    assert "R_c" in result.physics_ranges


def test_invalid_mission_detects_physics_issue(tmp_path: Path) -> None:
    mission_definition = tmp_path / "invalid_mission.json"
    mission_definition.write_text(
        """
        [
          {"command": "create_engine", "params": {"engine_type": "igsoa_complex", "num_nodes": -1}},
          {"command": "run_mission", "params": {"engine_id": "engine_001", "num_steps": 0, "iterations_per_node": 5}}
        ]
        """,
        encoding="utf-8",
    )

    validator = MissionSchemaValidator()
    commands = validator.load_from_file(mission_definition)
    result = validator.validate(commands)

    assert not result.is_valid()
    assert any("num_nodes" in error for error in result.errors)
    assert any("num_steps" in error for error in result.errors)


def test_unrecognised_command_generates_warning(tmp_path: Path) -> None:
    mission_definition = tmp_path / "unknown_command.json"
    mission_definition.write_text(
        """
        {"command": "telemetry", "params": {"engine_id": "engine_001"}}
        """,
        encoding="utf-8",
    )

    validator = MissionSchemaValidator()
    commands = validator.load_from_file(mission_definition)
    result = validator.validate(commands)

    assert result.is_valid()
    assert result.warnings, "Expected warning for unknown command"
    assert "telemetry" in result.warnings[0]
