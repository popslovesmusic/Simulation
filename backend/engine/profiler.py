"""Profiling helpers for CPU and GPU telemetry capture."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ProfileRecord:
    """Describes a single profiled section."""

    name: str
    duration_ms: float
    cpu_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GpuSample:
    """GPU telemetry captured during a mission run."""

    name: str
    utilisation: Optional[float] = None
    memory_mb: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProfilerSession:
    """Collects profiling events and persists them as structured JSON."""

    def __init__(
        self,
        run_id: Optional[str] = None,
        output_dir: Path | None = Path("results/perf"),
    ) -> None:
        self.run_id = run_id or datetime.utcnow().strftime("mission-profiler-%Y%m%dT%H%M%SZ")
        self.output_dir = output_dir or Path("results/perf")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._records: List[ProfileRecord] = []
        self._gpu_samples: List[GpuSample] = []
        self._open = True
        self._artifact_path: Optional[Path] = None

    def profile_block(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager recording CPU and wall-clock duration for ``name``."""

        metadata = metadata or {}
        start_wall = time.perf_counter()
        start_cpu = time.process_time()

        class _ProfileContext:
            def __enter__(inner_self):  # noqa: D401 - simple wrapper
                return inner_self

            def __exit__(inner_self, exc_type, exc, exc_tb) -> None:
                end_wall = time.perf_counter()
                end_cpu = time.process_time()
                self._records.append(
                    ProfileRecord(
                        name=name,
                        duration_ms=(end_wall - start_wall) * 1000.0,
                        cpu_time_ms=(end_cpu - start_cpu) * 1000.0,
                        metadata=dict(metadata),
                    )
                )
                # Do not suppress exceptions
                return False

        return _ProfileContext()

    def record_gpu_metrics(
        self,
        name: str,
        utilisation: Optional[float] = None,
        memory_mb: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append a GPU telemetry sample to the session."""

        if not self._open:
            raise RuntimeError("Cannot record GPU metrics after session is closed")
        self._gpu_samples.append(
            GpuSample(
                name=name,
                utilisation=utilisation,
                memory_mb=memory_mb,
                metadata=dict(metadata or {}),
            )
        )

    def close(self) -> Path:
        """Persist profiling artifacts to disk."""

        if not self._open and self._artifact_path is not None:
            return self._artifact_path

        self._open = False
        summary = self._build_summary()
        payload = {
            "run_id": self.run_id,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "records": [
                {
                    "name": record.name,
                    "duration_ms": record.duration_ms,
                    "cpu_time_ms": record.cpu_time_ms,
                    "metadata": record.metadata,
                }
                for record in self._records
            ],
            "gpu_samples": [
                {
                    "name": sample.name,
                    "utilisation": sample.utilisation,
                    "memory_mb": sample.memory_mb,
                    "metadata": sample.metadata,
                }
                for sample in self._gpu_samples
            ],
            "summary": summary,
        }

        artifact_path = self.output_dir / f"{self.run_id}.json"
        artifact_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        self._artifact_path = artifact_path
        return artifact_path

    def _build_summary(self) -> Dict[str, Any]:
        if not self._records:
            return {"total_duration_ms": 0.0, "total_cpu_time_ms": 0.0, "sections": 0}

        total_duration = sum(record.duration_ms for record in self._records)
        total_cpu = sum(record.cpu_time_ms for record in self._records)
        longest = max(self._records, key=lambda record: record.duration_ms)
        return {
            "total_duration_ms": total_duration,
            "total_cpu_time_ms": total_cpu,
            "sections": len(self._records),
            "longest_section": {
                "name": longest.name,
                "duration_ms": longest.duration_ms,
                "cpu_time_ms": longest.cpu_time_ms,
            },
        }


__all__ = ["ProfilerSession", "ProfileRecord", "GpuSample"]
