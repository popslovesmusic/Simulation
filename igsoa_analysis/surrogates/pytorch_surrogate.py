"""PyTorch-based surrogate model prototypes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from .base import SurrogateConfig, SurrogateModelBase

try:  # pragma: no cover - optional dependency during CI
    import torch
    from torch import nn
except Exception as exc:  # pragma: no cover - gracefully degrade when torch is missing
    torch = None  # type: ignore
    nn = None  # type: ignore
    _TORCH_IMPORT_ERROR = exc
else:  # pragma: no cover - executed when torch present
    _TORCH_IMPORT_ERROR = None


class FeedForwardSurrogate(SurrogateModelBase):
    """Simple fully-connected network for waveform emulation."""

    def __init__(self, config: SurrogateConfig) -> None:
        if torch is None or nn is None:  # pragma: no cover - environment guard
            raise RuntimeError(
                "PyTorch is required to instantiate FeedForwardSurrogate."
            ) from _TORCH_IMPORT_ERROR
        super().__init__(config)
        layers: list[nn.Module] = []
        in_dim = config.input_dim
        for hidden in config.hidden_layers:
            layers.append(nn.Linear(in_dim, hidden))
            layers.append(nn.ReLU())
            in_dim = hidden
        layers.append(nn.Linear(in_dim, config.output_dim))
        self.model = nn.Sequential(*layers)
        self.device = torch.device(config.device)
        self.model.to(self.device)
        self._loss = nn.MSELoss()

    def __call__(self, inputs: Any) -> Any:
        tensor = self._ensure_tensor(inputs)
        self.model.eval()
        with torch.no_grad():
            return self.model(tensor.to(self.device))

    def _ensure_tensor(self, value: Any) -> "torch.Tensor":
        if torch is None:  # pragma: no cover - import guard
            raise RuntimeError("PyTorch is unavailable in this environment")
        if isinstance(value, torch.Tensor):
            return value
        if isinstance(value, np.ndarray):
            return torch.from_numpy(value.astype(np.float32))
        if isinstance(value, Iterable):
            return torch.tensor(list(value), dtype=torch.float32)
        raise TypeError(f"Unsupported input type for surrogate inference: {type(value)!r}")

    def train_on_arrays(
        self,
        features: Any,
        targets: Any,
        *,
        epochs: int | None = None,
        learning_rate: float | None = None,
        batch_size: int | None = None,
    ) -> Sequence[float]:
        if torch is None:  # pragma: no cover
            raise RuntimeError("PyTorch is unavailable in this environment")

        epochs = epochs or self.config.epochs
        learning_rate = learning_rate or self.config.learning_rate
        batch_size = batch_size or self.config.batch_size

        features_tensor = self._ensure_tensor(features).to(self.device)
        targets_tensor = self._ensure_tensor(targets).to(self.device)

        optimiser = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        loss_history: list[float] = []

        self.model.train()
        num_samples = features_tensor.shape[0]
        for epoch in range(epochs):
            permutation = torch.randperm(num_samples, device=self.device)
            epoch_loss = 0.0
            batches = 0
            for start in range(0, num_samples, batch_size):
                indices = permutation[start : start + batch_size]
                batch_features = features_tensor.index_select(0, indices)
                batch_targets = targets_tensor.index_select(0, indices)

                optimiser.zero_grad()
                predictions = self.model(batch_features)
                loss = self._loss(predictions, batch_targets)
                loss.backward()
                optimiser.step()

                epoch_loss += float(loss.detach().cpu().item())
                batches += 1

            loss_history.append(epoch_loss / max(1, batches))
        return loss_history

    def save(self, path: str | None = None) -> str:
        if torch is None:  # pragma: no cover
            raise RuntimeError("PyTorch is unavailable in this environment")

        resolved = Path(path or f"surrogate-{self.config.input_dim}x{self.config.output_dim}.pt")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.model.state_dict(),
                "config": self.config.to_dict(),
            },
            resolved,
        )
        return str(resolved)

    @classmethod
    def load(cls, path: str, config: SurrogateConfig | None = None) -> "FeedForwardSurrogate":
        if torch is None:  # pragma: no cover
            raise RuntimeError("PyTorch is unavailable in this environment")

        payload = torch.load(path, map_location="cpu")
        config_dict = payload.get("config", {})
        merged_config = config.to_dict() if config else {}
        merged_config.update(config_dict)
        instance = cls(SurrogateConfig.from_mapping(merged_config))
        instance.model.load_state_dict(payload["state_dict"])
        return instance


__all__ = ["FeedForwardSurrogate"]
