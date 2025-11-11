"""Tests for mission planner dry-run workflows."""

from __future__ import annotations

from pathlib import Path

from backend.mission_runtime import MissionPlanner


def test_dry_run_generates_summary(tmp_path: Path) -> None:
    planner = MissionPlanner(report_dir=tmp_path)
    summary = planner.dry_run(Path("missions/mission_rc_0.5.json"))

    assert summary.num_commands >= 1
    assert "run_mission" in summary.command_counts
    assert summary.report_path is not None
    assert summary.report_path.exists()

    report_content = summary.report_path.read_text(encoding="utf-8")
    assert "mission_rc_0.5" in report_content
    assert "generated_at" in report_content


def test_dry_run_records_discrepancies(tmp_path: Path) -> None:
    mission_definition = tmp_path / "bad_mission.json"
    mission_definition.write_text(
        """
        {"command": "run_mission", "params": {"engine_id": "engine_001", "num_steps": 0, "iterations_per_node": 5}}
        """,
        encoding="utf-8",
    )

    planner = MissionPlanner(report_dir=tmp_path)
    summary = planner.dry_run(mission_definition)

    assert summary.has_errors
    assert any("num_steps" in error for error in summary.issues["errors"])
