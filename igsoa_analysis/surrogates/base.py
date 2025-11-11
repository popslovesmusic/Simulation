"""Base classes and configuration helpers for surrogate modelling prototypes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, MutableMapping, Sequence


@dataclass
class SurrogateConfig:
    """Configuration describing the architecture and training hyperparameters."""

    input_dim: int
    output_dim: int
    hidden_layers: Sequence[int]
    learning_rate: float
    batch_size: int
    epochs: int
    seed: int | None = None
    device: str = "cpu"
    extra: MutableMapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SurrogateConfig":
        """Create a :class:`SurrogateConfig` from a dictionary payload."""

        required = {"input_dim", "output_dim", "hidden_layers", "learning_rate", "batch_size", "epochs"}
        missing = sorted(required.difference(payload))
        if missing:
            raise ValueError(f"Missing required config keys: {', '.join(missing)}")
        extra = {
            key: value
            for key, value in payload.items()
            if key not in {"input_dim", "output_dim", "hidden_layers", "learning_rate", "batch_size", "epochs", "seed", "device"}
        }
        return cls(
            input_dim=int(payload["input_dim"]),
            output_dim=int(payload["output_dim"]),
            hidden_layers=list(payload["hidden_layers"]),
            learning_rate=float(payload["learning_rate"]),
            batch_size=int(payload["batch_size"]),
            epochs=int(payload["epochs"]),
            seed=int(payload["seed"]) if payload.get("seed") is not None else None,
            device=str(payload.get("device", "cpu")),
            extra=extra,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the configuration for notebooks and manifests."""

        payload: Dict[str, Any] = {
            "input_dim": self.input_dim,
            "output_dim": self.output_dim,
            "hidden_layers": list(self.hidden_layers),
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "device": self.device,
        }
        if self.seed is not None:
            payload["seed"] = self.seed
        payload.update(self.extra)
        return payload


@dataclass
class SurrogateTrainingArtifact:
    """Captures training telemetry for governance and benchmarking."""

    dataset_name: str
    config: SurrogateConfig
    loss_history: Sequence[float]
    metrics: Mapping[str, float]

    def to_json(self) -> Dict[str, Any]:
        return {
            "dataset": self.dataset_name,
            "config": self.config.to_dict(),
            "loss_history": list(self.loss_history),
            "metrics": dict(self.metrics),
        }


class SurrogateModelBase(ABC):
    """Abstract base class implemented by surrogate model backends."""

    def __init__(self, config: SurrogateConfig) -> None:
        self.config = config

    @abstractmethod
    def __call__(self, inputs: Any) -> Any:  # pragma: no cover - interface definition
        """Run forward inference with the surrogate model."""

    @abstractmethod
    def train_on_arrays(self, features: Any, targets: Any, **kwargs: Any) -> Sequence[float]:
        """Train the surrogate using in-memory tensors/arrays."""

    @abstractmethod
    def save(self, path: str | None = None) -> str:
        """Persist the surrogate weights to ``path`` and return the resolved path."""

    @classmethod
    @abstractmethod
    def load(cls, path: str, config: SurrogateConfig | None = None) -> "SurrogateModelBase":
        """Load a saved surrogate from disk."""

    @classmethod
    def from_config(cls, config_like: Mapping[str, Any] | SurrogateConfig) -> "SurrogateModelBase":
        """Build a surrogate instance from a mapping or :class:`SurrogateConfig`."""

        config = config_like if isinstance(config_like, SurrogateConfig) else SurrogateConfig.from_mapping(config_like)
        return cls(config)


__all__ = ["SurrogateConfig", "SurrogateModelBase", "SurrogateTrainingArtifact"]
