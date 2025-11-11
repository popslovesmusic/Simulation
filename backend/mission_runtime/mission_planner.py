"""Mission planning utilities providing dry-run validation and summaries."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .schema import MissionSchemaValidator, MissionValidationResult

LOGGER = logging.getLogger("backend.mission_planner")


@dataclass
class MissionSummary:
    """Structured summary of a mission dry-run."""

    mission_path: Path
    num_commands: int
    command_counts: Dict[str, int]
    engine_ids: List[str]
    physics_ranges: Dict[str, Dict[str, float]]
    issues: Dict[str, List[str]]
    report_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, object]:
        """Serialise the mission summary to a JSON-compatible dictionary."""

        return {
            "mission_path": str(self.mission_path),
            "num_commands": self.num_commands,
            "command_counts": dict(self.command_counts),
            "engine_ids": list(self.engine_ids),
            "physics_ranges": {
                key: dict(value) for key, value in self.physics_ranges.items()
            },
            "issues": {"errors": list(self.issues["errors"]), "warnings": list(self.issues["warnings"])},
            "report_path": str(self.report_path) if self.report_path else None,
        }

    @property
    def has_errors(self) -> bool:
        """Return ``True`` when the mission contains blocking issues."""

        return bool(self.issues.get("errors"))

    @property
    def has_warnings(self) -> bool:
        """Return ``True`` when the mission contains non-blocking issues."""

        return bool(self.issues.get("warnings"))


class MissionPlanner:
    """Plan, validate and summarise mission command streams."""

    def __init__(
        self,
        validator: Optional[MissionSchemaValidator] = None,
        report_dir: Path | None = Path("analysis/mission_reports"),
    ) -> None:
        self.validator = validator or MissionSchemaValidator()
        self.report_dir = report_dir
        if self.report_dir is not None:
            self.report_dir.mkdir(parents=True, exist_ok=True)

    def dry_run(self, mission_path: Path) -> MissionSummary:
        """Perform a dry-run validation of the mission at ``mission_path``."""

        commands = self.validator.load_from_file(mission_path)
        validation = self.validator.validate(commands)
        summary = self._build_summary(mission_path, validation)

        if self.report_dir is not None:
            summary.report_path = self._persist_summary(summary)
            if summary.has_errors or summary.has_warnings:
                LOGGER.warning(
                    "Mission %s contains %d errors and %d warnings (report: %s)",
                    mission_path,
                    len(summary.issues["errors"]),
                    len(summary.issues["warnings"]),
                    summary.report_path,
                )
            else:
                LOGGER.info(
                    "Mission %s validated successfully (report: %s)",
                    mission_path,
                    summary.report_path,
                )

        return summary

    def _build_summary(
        self, mission_path: Path, validation: MissionValidationResult
    ) -> MissionSummary:
        commands_total = sum(validation.command_counts.values())
        issues = {
            "errors": list(validation.errors),
            "warnings": list(validation.warnings),
        }
        return MissionSummary(
            mission_path=mission_path,
            num_commands=commands_total,
            command_counts=dict(validation.command_counts),
            engine_ids=list(validation.engine_ids),
            physics_ranges={
                key: dict(value) for key, value in validation.physics_ranges.items()
            },
            issues=issues,
        )

    def _persist_summary(self, summary: MissionSummary) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        mission_name = summary.mission_path.stem
        report_path = self.report_dir / f"{mission_name}_dry_run_{timestamp}.json"
        data = summary.to_dict()
        data["generated_at"] = timestamp
        data["status"] = "invalid" if summary.has_errors else "valid"
        report_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        return report_path


__all__ = ["MissionPlanner", "MissionSummary"]
