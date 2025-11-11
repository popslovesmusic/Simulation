"""Simulated engine runtime integrating logging and profiling hooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .logging import get_engine_logger
from .profiler import ProfilerSession
from .surrogate_adapter import SurrogateAdapter, SurrogateExecutionResult


@dataclass
class ProfilerSessionResult:
    """Container describing the result of a profiled mission run."""

    artifact_path: Path


class MissionRuntime:
    """Lightweight runtime that instruments mission command execution."""

    def __init__(
        self,
        profiler: Optional[ProfilerSession] = None,
        surrogate_adapter: Optional[SurrogateAdapter] = None,
    ) -> None:
        self.profiler = profiler or ProfilerSession()
        self.logger = get_engine_logger()
        self.surrogate_adapter = surrogate_adapter

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

            def _fallback() -> Mapping[str, object]:
                return self._simulate_command(cmd_name, params)

            with self.profiler.profile_block(cmd_name, metadata=metadata):
                if self.surrogate_adapter is not None:
                    result = self.surrogate_adapter.execute(cmd_name, params, fallback=_fallback)
                    self._record_surrogate_metadata(metadata, result)
                else:
                    _fallback()

            duration_hint = params.get("duration_hint")
            if isinstance(duration_hint, (int, float)):
                self.profiler.record_gpu_metrics(
                    name=cmd_name,
                    utilisation=0.0,
                    memory_mb=0.0,
                    metadata={"duration_hint": float(duration_hint)},
                )

        artifact_path = self.profiler.close()
        if self.surrogate_adapter is not None:
            self.surrogate_adapter.flush_benchmarks(
                profiler=self.profiler,
                run_id=self.profiler.run_id,
            )
        self.logger.info("Mission profiling artifact stored at %s", artifact_path)
        return ProfilerSessionResult(artifact_path=artifact_path)

    def _simulate_command(self, cmd_name: str, params: Mapping[str, object]) -> Mapping[str, object]:
        """Placeholder full-precision simulation path."""

        # In a production implementation this would invoke the physical simulation.
        return {"command": cmd_name, "params": dict(params), "mode": "simulation"}

    def _record_surrogate_metadata(
        self,
        metadata: Mapping[str, object],
        result: SurrogateExecutionResult,
    ) -> None:
        """Augment profiling metadata with surrogate execution details."""

        if not isinstance(metadata, dict):  # Defensive guard for Mapping proxies
            return
        metadata["surrogate_used"] = result.used_surrogate
        if result.surrogate_name:
            metadata["surrogate_name"] = result.surrogate_name
        if result.surrogate_latency_ms is not None:
            metadata["surrogate_latency_ms"] = result.surrogate_latency_ms
        if result.fallback_latency_ms is not None:
            metadata["fallback_latency_ms"] = result.fallback_latency_ms
        if result.accuracy_metric is not None:
            metadata["surrogate_accuracy_mae"] = result.accuracy_metric


__all__ = ["MissionRuntime", "ProfilerSessionResult"]
