"""Integration helpers connecting surrogate models to the simulation runtime."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, MutableMapping, Optional

from .logging import get_engine_logger

try:  # Optional import: surrogate packages live under igsoa_analysis
    from igsoa_analysis.surrogates import SurrogateModelBase
except Exception:  # pragma: no cover - adapter can operate without surrogates present
    SurrogateModelBase = Any  # type: ignore[assignment]

FallbackCallable = Callable[[], Mapping[str, Any] | Any]


@dataclass
class SurrogateExecutionResult:
    """Structured result capturing surrogate and fallback outcomes."""

    command: str
    used_surrogate: bool
    surrogate_name: Optional[str]
    surrogate_latency_ms: Optional[float] = None
    fallback_latency_ms: Optional[float] = None
    accuracy_metric: Optional[float] = None
    surrogate_output: Any = None
    fallback_output: Any = None
    metadata: MutableMapping[str, Any] = field(default_factory=dict)


@dataclass
class SurrogateBenchmarkRecord:
    """Persistable benchmark entry stored for governance reviews."""

    command: str
    surrogate: Optional[str]
    used_surrogate: bool
    surrogate_latency_ms: Optional[float]
    fallback_latency_ms: Optional[float]
    accuracy_metric: Optional[float]
    metadata: Mapping[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "surrogate": self.surrogate,
            "used_surrogate": self.used_surrogate,
            "surrogate_latency_ms": self.surrogate_latency_ms,
            "fallback_latency_ms": self.fallback_latency_ms,
            "accuracy_metric": self.accuracy_metric,
            "metadata": dict(self.metadata),
        }


class SurrogateAdapter:
    """Dispatcher that attempts surrogate inference with automatic fallbacks."""

    def __init__(
        self,
        registry: Optional[Mapping[str, SurrogateModelBase]] = None,
        *,
        benchmark_dir: Path | None = Path("analysis/datasets/surrogate_benchmarks"),
        validate_surrogates: bool = True,
    ) -> None:
        self._registry: Dict[str, SurrogateModelBase] = dict(registry or {})
        self.validate_surrogates = validate_surrogates
        self.logger = get_engine_logger()
        self.benchmark_dir = benchmark_dir
        if self.benchmark_dir is not None:
            self.benchmark_dir.mkdir(parents=True, exist_ok=True)
        self._benchmarks: List[SurrogateBenchmarkRecord] = []

    def register(self, command: str, model: SurrogateModelBase) -> None:
        """Register ``model`` to serve surrogate predictions for ``command``."""

        self._registry[command] = model
        self.logger.info("Registered surrogate %s for command %s", model.__class__.__name__, command)

    def has_surrogate(self, command: str) -> bool:
        return command in self._registry

    def execute(
        self,
        command: str,
        params: Mapping[str, Any],
        fallback: Optional[FallbackCallable] = None,
    ) -> SurrogateExecutionResult:
        """Attempt surrogate inference, falling back to ``fallback`` when required."""

        model = self._registry.get(command)
        record_metadata: Dict[str, Any] = {"requested_at": datetime.utcnow().isoformat()}
        surrogate_output = None
        fallback_output = None
        surrogate_latency = None
        fallback_latency = None
        accuracy_metric = None
        used_surrogate = False
        surrogate_name = None

        if model is not None:
            surrogate_name = model.__class__.__name__
            try:
                features = self._extract_features(params)
                start = time.perf_counter()
                raw_output = model(features)
                surrogate_latency = (time.perf_counter() - start) * 1000.0
                surrogate_output = self._normalise_output(raw_output)
                used_surrogate = True
                record_metadata["feature_source"] = "params"
            except Exception as exc:  # pragma: no cover - runtime guard
                self.logger.exception("Surrogate inference failed for %s: %s", command, exc)
                record_metadata["surrogate_error"] = repr(exc)
                used_surrogate = False

        should_validate = bool(params.get("validate_surrogate", self.validate_surrogates))
        require_fallback = not used_surrogate or should_validate or params.get("force_full_precision")

        if fallback is not None and require_fallback:
            start = time.perf_counter()
            fallback_output = fallback()
            fallback_latency = (time.perf_counter() - start) * 1000.0
            record_metadata["fallback_used"] = True

            if surrogate_output is not None and should_validate:
                accuracy_metric = self._compute_accuracy(surrogate_output, fallback_output)
                record_metadata["validation_performed"] = True
        elif fallback is None and not used_surrogate:
            self.logger.warning("No surrogate available for %s and no fallback provided", command)

        result = SurrogateExecutionResult(
            command=command,
            used_surrogate=used_surrogate,
            surrogate_name=surrogate_name,
            surrogate_latency_ms=surrogate_latency,
            fallback_latency_ms=fallback_latency,
            accuracy_metric=accuracy_metric,
            surrogate_output=surrogate_output,
            fallback_output=fallback_output,
            metadata=record_metadata,
        )

        self._benchmarks.append(
            SurrogateBenchmarkRecord(
                command=command,
                surrogate=surrogate_name,
                used_surrogate=used_surrogate,
                surrogate_latency_ms=surrogate_latency,
                fallback_latency_ms=fallback_latency,
                accuracy_metric=accuracy_metric,
                metadata=dict(record_metadata),
            )
        )
        return result

    def _extract_features(self, params: Mapping[str, Any]) -> Any:
        for key in ("surrogate_input", "features", "waveform_features"):
            if key in params:
                return params[key]
        raise KeyError("No surrogate input features found in command parameters")

    def _normalise_output(self, output: Any) -> Any:
        try:
            import numpy as np
        except Exception:  # pragma: no cover - numpy optional
            np = None  # type: ignore

        if hasattr(output, "detach"):
            tensor = output.detach()
            if hasattr(tensor, "cpu"):
                tensor = tensor.cpu()
            if hasattr(tensor, "numpy"):
                return tensor.numpy().tolist()
            return tensor
        if np is not None and isinstance(output, np.ndarray):
            return output.tolist()
        if isinstance(output, (list, tuple)):
            return list(output)
        return output

    def _compute_accuracy(self, surrogate_output: Any, fallback_output: Any) -> float:
        try:
            import numpy as np
        except Exception:  # pragma: no cover
            np = None  # type: ignore

        surrogate_arr = self._to_array(surrogate_output, np)
        fallback_arr = self._to_array(fallback_output, np)
        if surrogate_arr is None or fallback_arr is None:
            return 0.0
        diff = surrogate_arr - fallback_arr
        return float((abs(diff)).mean())

    def _to_array(self, value: Any, np_module: Any) -> Optional[Any]:
        if value is None:
            return None
        if np_module is not None and isinstance(value, np_module.ndarray):
            return value.astype(np_module.float32)
        if np_module is not None and isinstance(value, list):
            return np_module.asarray(value, dtype=np_module.float32)
        if hasattr(value, "detach") and hasattr(value, "cpu"):
            tensor = value.detach().cpu()
            if hasattr(tensor, "numpy"):
                return tensor.numpy()
        return None

    def flush_benchmarks(
        self,
        *,
        profiler: Optional["ProfilerSession"] = None,
        run_id: Optional[str] = None,
    ) -> Optional[Path]:
        """Persist benchmarking data and optionally emit profiler metadata."""

        if not self._benchmarks:
            return None

        if profiler is not None:
            for record in self._benchmarks:
                profiler.record_gpu_metrics(
                    name=f"surrogate::{record.command}",
                    utilisation=None,
                    memory_mb=None,
                    metadata={
                        "used_surrogate": record.used_surrogate,
                        "surrogate_latency_ms": record.surrogate_latency_ms,
                        "fallback_latency_ms": record.fallback_latency_ms,
                        "accuracy_metric": record.accuracy_metric,
                        **dict(record.metadata),
                    },
                )

        artifact_path = None
        if self.benchmark_dir is not None:
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            base_name = run_id or "surrogate-benchmark"
            artifact_path = self.benchmark_dir / f"{base_name}-{timestamp}.json"
            payload = {
                "run_id": run_id,
                "generated_at": datetime.utcnow().isoformat(),
                "records": [record.to_dict() for record in self._benchmarks],
            }
            artifact_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            self.logger.info("Surrogate benchmark summary written to %s", artifact_path)

        self._benchmarks.clear()
        return artifact_path


__all__ = ["SurrogateAdapter", "SurrogateExecutionResult"]
