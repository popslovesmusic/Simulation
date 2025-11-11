"""Simulated engine runtime integrating logging and profiling hooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .logging import get_engine_logger
from .profiler import ProfilerSession


@dataclass
class ProfilerSessionResult:
    """Container describing the result of a profiled mission run."""

    artifact_path: Path


class MissionRuntime:
    """Lightweight runtime that instruments mission command execution."""

    def __init__(self, profiler: Optional[ProfilerSession] = None) -> None:
        self.profiler = profiler or ProfilerSession()
        self.logger = get_engine_logger()

    def execute(self, mission_commands: Sequence[Mapping[str, object]]) -> ProfilerSessionResult:
        """Simulate execution of ``mission_commands`` with instrumentation."""

        for index, command in enumerate(mission_commands):
            cmd_name = str(command.get("command", f"step_{index}"))
            params_obj = command.get("params", {})
            params = params_obj if isinstance(params_obj, Mapping) else {}

            metadata = {"index": index, "param_keys": sorted(params.keys())}
            engine_id = params.get("engine_id")
            if isinstance(engine_id, str):
                metadata["engine_id"] = engine_id

            self.logger.info("Simulating command %s with params %s", cmd_name, params)
            with self.profiler.profile_block(cmd_name, metadata=metadata):
                # Placeholder for real engine work; hooking ensures timing is captured.
                pass

            duration_hint = params.get("duration_hint")
            if isinstance(duration_hint, (int, float)):
                self.profiler.record_gpu_metrics(
                    name=cmd_name,
                    utilisation=0.0,
                    memory_mb=0.0,
                    metadata={"duration_hint": float(duration_hint)},
                )

        artifact_path = self.profiler.close()
        self.logger.info("Mission profiling artifact stored at %s", artifact_path)
        return ProfilerSessionResult(artifact_path=artifact_path)


__all__ = ["MissionRuntime", "ProfilerSessionResult"]
