"""Model cache backend for PyTorch models and checkpoints.

This backend stores:
- PyTorch model state_dicts as .pt files
- Full model checkpoints with optimizer state
- Metadata in companion .json files
"""

from __future__ import annotations

import json
import torch
from pathlib import Path
from typing import Any, Optional


class ModelBackend:
    """Store PyTorch models and training checkpoints.

    This backend handles:
    - Model state_dicts (weights and biases)
    - Full checkpoints (model + optimizer + epoch + loss)
    - Metadata (architecture, hyperparameters)

    Example:
        >>> backend = ModelBackend(Path("./cache/surrogates"))
        >>>
        >>> # Save model state_dict
        >>> model = torch.nn.Linear(10, 1)
        >>> backend.save("my_model_v1", model.state_dict())
        >>>
        >>> # Save full checkpoint
        >>> checkpoint = {
        ...     'model_state_dict': model.state_dict(),
        ...     'optimizer_state_dict': optimizer.state_dict(),
        ...     'epoch': 100,
        ...     'loss': 0.042
        ... }
        >>> backend.save("my_model_checkpoint", checkpoint)
        >>>
        >>> # Load model
        >>> loaded_state = backend.load("my_model_v1")
        >>> model.load_state_dict(loaded_state)
    """

    def __init__(self, root: Path):
        """Initialize model backend.

        Args:
            root: Root directory for this cache category
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, data: Any, metadata: Optional[dict] = None) -> Path:
        """Save PyTorch model or checkpoint.

        Args:
            key: Cache key (filename without extension)
            data: PyTorch state_dict or checkpoint dict
            metadata: Optional metadata (saved as companion .json)

        Returns:
            Path to saved .pt file

        Raises:
            ValueError: If data type not supported
        """
        if not isinstance(data, dict):
            raise ValueError(
                f"ModelBackend expects dict (state_dict or checkpoint), got {type(data)}"
            )

        # Save model as .pt
        path = self.root / f"{key}.pt"
        torch.save(data, path)

        # Save metadata if provided
        if metadata is not None:
            meta_path = self.root / f"{key}.meta.json"
            meta_path.write_text(json.dumps(metadata, indent=2))

        return path

    def load(self, key: str, map_location: Optional[str] = None) -> Any:
        """Load PyTorch model or checkpoint.

        Args:
            key: Cache key (filename without extension)
            map_location: Device to load tensors onto (e.g., 'cpu', 'cuda:0')
                         If None, uses default behavior

        Returns:
            Loaded state_dict or checkpoint dict

        Raises:
            FileNotFoundError: If key not found
        """
        path = self.root / f"{key}.pt"

        if not path.exists():
            raise FileNotFoundError(f"Cache key not found: {key}")

        # Load with specified device mapping
        if map_location is not None:
            return torch.load(path, map_location=map_location)
        else:
            return torch.load(path)

    def load_metadata(self, key: str) -> Optional[dict]:
        """Load metadata for a cached model.

        Args:
            key: Cache key

        Returns:
            Metadata dict or None if no metadata exists
        """
        meta_path = self.root / f"{key}.meta.json"

        if meta_path.exists():
            return json.loads(meta_path.read_text())

        return None

    def exists(self, key: str) -> bool:
        """Check if model exists in cache.

        Args:
            key: Cache key

        Returns:
            True if .pt file exists
        """
        path = self.root / f"{key}.pt"
        return path.exists()

    def delete(self, key: str) -> bool:
        """Delete cached model and metadata.

        Args:
            key: Cache key

        Returns:
            True if file was deleted, False if not found
        """
        deleted = False

        # Delete .pt file
        path = self.root / f"{key}.pt"
        if path.exists():
            path.unlink()
            deleted = True

        # Delete metadata if exists
        meta_path = self.root / f"{key}.meta.json"
        if meta_path.exists():
            meta_path.unlink()

        return deleted

    def list_keys(self) -> list[str]:
        """List all cached model keys.

        Returns:
            List of cache keys (without extensions)
        """
        keys = set()

        for path in self.root.glob("*.pt"):
            keys.add(path.stem)

        return sorted(keys)

    def get_size(self, key: str) -> int:
        """Get size of cached model in bytes.

        Args:
            key: Cache key

        Returns:
            File size in bytes (includes metadata if present)

        Raises:
            FileNotFoundError: If key not found
        """
        path = self.root / f"{key}.pt"

        if not path.exists():
            raise FileNotFoundError(f"Cache key not found: {key}")

        size = path.stat().st_size

        # Add metadata size if present
        meta_path = self.root / f"{key}.meta.json"
        if meta_path.exists():
            size += meta_path.stat().st_size

        return size


__all__ = ["ModelBackend"]
