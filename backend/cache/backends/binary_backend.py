"""Binary cache backend for FFTW wisdom and raw binary data.

This backend stores:
- FFTW wisdom files (.dat)
- Raw binary data with metadata
- Optimized for read-heavy workloads
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


class BinaryBackend:
    """Store binary data with optional metadata.

    This backend is optimized for:
    - FFTW wisdom files (FFT plan optimization)
    - Raw binary artifacts
    - Read-heavy access patterns

    Example:
        >>> backend = BinaryBackend(Path("./cache/fftw_wisdom"))
        >>>
        >>> # Save FFTW wisdom
        >>> wisdom_data = b"\\x89\\x50\\x4e\\x47..."  # Binary wisdom
        >>> backend.save("fftw_2d_512x512", wisdom_data)
        >>>
        >>> # Load wisdom
        >>> loaded = backend.load("fftw_2d_512x512")
        >>>
        >>> # Save with metadata
        >>> backend.save(
        ...     "fftw_3d_128x128x128",
        ...     wisdom_data,
        ...     metadata={"dimensions": [128, 128, 128], "planner": "FFTW_MEASURE"}
        ... )
    """

    def __init__(self, root: Path):
        """Initialize binary backend.

        Args:
            root: Root directory for this cache category
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, data: bytes, metadata: Optional[dict] = None) -> Path:
        """Save binary data.

        Args:
            key: Cache key (filename without extension)
            data: Binary data to save
            metadata: Optional metadata (saved as companion .json)

        Returns:
            Path to saved .dat file

        Raises:
            ValueError: If data is not bytes
        """
        if not isinstance(data, bytes):
            raise ValueError(f"BinaryBackend expects bytes, got {type(data)}")

        # Save binary data as .dat
        path = self.root / f"{key}.dat"
        path.write_bytes(data)

        # Save metadata if provided
        if metadata is not None:
            meta_path = self.root / f"{key}.meta.json"
            meta_path.write_text(json.dumps(metadata, indent=2))

        return path

    def load(self, key: str) -> bytes:
        """Load binary data.

        Args:
            key: Cache key (filename without extension)

        Returns:
            Binary data

        Raises:
            FileNotFoundError: If key not found
        """
        path = self.root / f"{key}.dat"

        if not path.exists():
            raise FileNotFoundError(f"Cache key not found: {key}")

        return path.read_bytes()

    def load_metadata(self, key: str) -> Optional[dict]:
        """Load metadata for cached binary data.

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
        """Check if binary data exists in cache.

        Args:
            key: Cache key

        Returns:
            True if .dat file exists
        """
        path = self.root / f"{key}.dat"
        return path.exists()

    def delete(self, key: str) -> bool:
        """Delete cached binary data and metadata.

        Args:
            key: Cache key

        Returns:
            True if file was deleted, False if not found
        """
        deleted = False

        # Delete .dat file
        path = self.root / f"{key}.dat"
        if path.exists():
            path.unlink()
            deleted = True

        # Delete metadata if exists
        meta_path = self.root / f"{key}.meta.json"
        if meta_path.exists():
            meta_path.unlink()

        return deleted

    def list_keys(self) -> list[str]:
        """List all cached binary keys.

        Returns:
            List of cache keys (without extensions)
        """
        keys = set()

        for path in self.root.glob("*.dat"):
            keys.add(path.stem)

        return sorted(keys)

    def get_size(self, key: str) -> int:
        """Get size of cached binary data in bytes.

        Args:
            key: Cache key

        Returns:
            File size in bytes (includes metadata if present)

        Raises:
            FileNotFoundError: If key not found
        """
        path = self.root / f"{key}.dat"

        if not path.exists():
            raise FileNotFoundError(f"Cache key not found: {key}")

        size = path.stat().st_size

        # Add metadata size if present
        meta_path = self.root / f"{key}.meta.json"
        if meta_path.exists():
            size += meta_path.stat().st_size

        return size


__all__ = ["BinaryBackend"]
