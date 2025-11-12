"""Filesystem-based cache backend for NumPy arrays and JSON data.

This backend stores:
- NumPy arrays as compressed .npz files
- Dictionaries and primitives as .json files
- Automatic format detection on load
"""

from __future__ import annotations

import json
import numpy as np
from pathlib import Path
from typing import Any


class FilesystemBackend:
    """Store data as compressed NumPy .npz or JSON files.

    This backend automatically detects the data type and chooses
    the appropriate storage format:
    - NumPy arrays → .npz (compressed)
    - Dicts, lists, primitives → .json

    Example:
        >>> backend = FilesystemBackend(Path("./cache/fractional_kernels"))
        >>>
        >>> # Save NumPy array
        >>> import numpy as np
        >>> kernel = np.random.rand(1000)
        >>> backend.save("kernel_1.5_0.01", kernel)
        >>>
        >>> # Save JSON data
        >>> metadata = {"alpha": 1.5, "dt": 0.01, "size": 1000}
        >>> backend.save("kernel_1.5_0.01_meta", metadata)
        >>>
        >>> # Load (auto-detects format)
        >>> loaded_kernel = backend.load("kernel_1.5_0.01")
        >>> loaded_meta = backend.load("kernel_1.5_0.01_meta")
    """

    def __init__(self, root: Path):
        """Initialize filesystem backend.

        Args:
            root: Root directory for this cache category
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, data: Any) -> Path:
        """Save data to filesystem, auto-detecting format.

        Args:
            key: Cache key (filename without extension)
            data: Data to save (NumPy array or JSON-serializable)

        Returns:
            Path to saved file

        Raises:
            ValueError: If data type not supported
        """
        # NumPy arrays → .npz
        if isinstance(data, np.ndarray):
            path = self.root / f"{key}.npz"
            np.savez_compressed(path, data=data)
            return path

        # Multiple NumPy arrays → .npz
        elif isinstance(data, dict) and all(isinstance(v, np.ndarray) for v in data.values()):
            path = self.root / f"{key}.npz"
            np.savez_compressed(path, **data)
            return path

        # JSON-serializable data → .json
        elif self._is_json_serializable(data):
            path = self.root / f"{key}.json"
            path.write_text(json.dumps(data, indent=2))
            return path

        else:
            raise ValueError(
                f"Unsupported data type: {type(data)}. "
                "Expected NumPy array or JSON-serializable data."
            )

    def load(self, key: str) -> Any:
        """Load data from filesystem, auto-detecting format.

        Args:
            key: Cache key (filename without extension)

        Returns:
            Deserialized data

        Raises:
            FileNotFoundError: If key not found
        """
        # Try .npz first
        npz_path = self.root / f"{key}.npz"
        if npz_path.exists():
            loaded = np.load(npz_path)

            # Single array saved with 'data' key
            if 'data' in loaded:
                return loaded['data']

            # Multiple arrays saved as dict
            return {k: loaded[k] for k in loaded.files}

        # Try .json
        json_path = self.root / f"{key}.json"
        if json_path.exists():
            return json.loads(json_path.read_text())

        raise FileNotFoundError(f"Cache key not found: {key}")

    def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists in either .npz or .json format
        """
        npz_path = self.root / f"{key}.npz"
        json_path = self.root / f"{key}.json"
        return npz_path.exists() or json_path.exists()

    def delete(self, key: str) -> bool:
        """Delete cached entry.

        Args:
            key: Cache key

        Returns:
            True if file was deleted, False if not found
        """
        deleted = False

        npz_path = self.root / f"{key}.npz"
        if npz_path.exists():
            npz_path.unlink()
            deleted = True

        json_path = self.root / f"{key}.json"
        if json_path.exists():
            json_path.unlink()
            deleted = True

        return deleted

    def list_keys(self) -> list[str]:
        """List all cached keys (without extensions).

        Returns:
            List of cache keys
        """
        keys = set()

        # Add .npz keys
        for path in self.root.glob("*.npz"):
            keys.add(path.stem)

        # Add .json keys
        for path in self.root.glob("*.json"):
            if path.name != "index.json":  # Skip metadata index
                keys.add(path.stem)

        return sorted(keys)

    def get_size(self, key: str) -> int:
        """Get size of cached entry in bytes.

        Args:
            key: Cache key

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If key not found
        """
        npz_path = self.root / f"{key}.npz"
        if npz_path.exists():
            return npz_path.stat().st_size

        json_path = self.root / f"{key}.json"
        if json_path.exists():
            return json_path.stat().st_size

        raise FileNotFoundError(f"Cache key not found: {key}")

    def _is_json_serializable(self, data: Any) -> bool:
        """Check if data can be JSON serialized.

        Args:
            data: Data to check

        Returns:
            True if JSON-serializable
        """
        try:
            json.dumps(data)
            return True
        except (TypeError, ValueError):
            return False


__all__ = ["FilesystemBackend"]
