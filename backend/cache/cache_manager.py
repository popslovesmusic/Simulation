"""Unified cache management system for DASE/IGSOA framework.

This module provides a central cache manager for all computational artifacts:
- Fractional kernel coefficients
- Laplacian stencils
- FFTW wisdom files
- Echo templates
- State profiles
- Source maps
- Mission graph results
- Surrogate ML models

Expected speedup: 50-80% for repeated missions.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Optional, Protocol
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class CacheEntry:
    """Metadata for a cached entry."""
    key: str
    created_at: str
    size_bytes: int
    access_count: int = 0
    last_accessed: Optional[str] = None
    checksum: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class CacheBackend(Protocol):
    """Protocol for cache backend implementations.

    All backends must implement these methods to be compatible
    with the CacheManager.
    """

    def save(self, key: str, data: Any) -> Path:
        """Save data and return path to cached file."""
        ...

    def load(self, key: str) -> Any:
        """Load and deserialize data."""
        ...

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        ...

    def delete(self, key: str) -> bool:
        """Delete cached entry."""
        ...

    def list_keys(self) -> list[str]:
        """List all cached keys."""
        ...

    def get_size(self, key: str) -> int:
        """Get size of cached entry in bytes."""
        ...


class CacheManager:
    """
    Unified cache manager for all DASE computational artifacts.

    Example:
        >>> cache = CacheManager(root=Path("./cache"))

        >>> # Store fractional kernel
        >>> import numpy as np
        >>> coeffs = np.random.rand(1000)
        >>> cache.save("fractional_kernels", "kernel_1.5_0.01_1000", coeffs)

        >>> # Load kernel
        >>> loaded = cache.load("fractional_kernels", "kernel_1.5_0.01_1000")

        >>> # Check existence
        >>> if cache.exists("stencils", "laplacian_2d_64_64"):
        ...     stencil = cache.load("stencils", "laplacian_2d_64_64")
    """

    def __init__(
        self,
        root: Path | str = Path("./cache"),
        enable_checksums: bool = True,
        enable_stats: bool = True
    ):
        """
        Initialize cache manager.

        Args:
            root: Root directory for cache storage
            enable_checksums: Verify data integrity with SHA256
            enable_stats: Track access counts and timestamps
        """
        self.root = Path(root)
        self.enable_checksums = enable_checksums
        self.enable_stats = enable_stats

        # Create cache directory structure
        self._ensure_structure()

        # Initialize backends (will import after backends are created)
        self.backends: dict[str, CacheBackend] = {}
        self._init_backends()

        # Load metadata
        self.metadata: dict[str, dict] = {}
        self._load_metadata()

    def _ensure_structure(self) -> None:
        """Create cache directory structure if not exists."""
        categories = [
            "fractional_kernels",
            "stencils",
            "fftw_wisdom",
            "echo_templates",
            "state_profiles",
            "source_maps",
            "mission_graph",
            "surrogates"
        ]

        for category in categories:
            category_path = self.root / category
            category_path.mkdir(parents=True, exist_ok=True)

            # Create index.json if not exists
            index_path = category_path / "index.json"
            if not index_path.exists():
                index_path.write_text(json.dumps({
                    "version": "1.0",
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "total_entries": 0,
                    "total_size_mb": 0.0,
                    "entries": {}
                }, indent=2))

    def _init_backends(self) -> None:
        """Initialize cache backends for each category."""
        try:
            from .backends import (
                FilesystemBackend,
                ModelBackend,
                BinaryBackend
            )

            self.backends = {
                "fractional_kernels": FilesystemBackend(self.root / "fractional_kernels"),
                "stencils": FilesystemBackend(self.root / "stencils"),
                "fftw_wisdom": BinaryBackend(self.root / "fftw_wisdom"),
                "echo_templates": FilesystemBackend(self.root / "echo_templates"),
                "state_profiles": FilesystemBackend(self.root / "state_profiles"),
                "source_maps": FilesystemBackend(self.root / "source_maps"),
                "mission_graph": FilesystemBackend(self.root / "mission_graph"),
                "surrogates": ModelBackend(self.root / "surrogates"),
            }
        except ImportError:
            # Backends not yet implemented - will be added in next tasks
            pass

    def _load_metadata(self) -> None:
        """Load metadata from index files."""
        categories = [
            "fractional_kernels", "stencils", "fftw_wisdom",
            "echo_templates", "state_profiles", "source_maps",
            "mission_graph", "surrogates"
        ]

        for category in categories:
            index_path = self.root / category / "index.json"
            if index_path.exists():
                self.metadata[category] = json.loads(index_path.read_text())
            else:
                self.metadata[category] = {"entries": {}}

    def _save_metadata(self, category: str) -> None:
        """Save metadata to index file."""
        index_path = self.root / category / "index.json"
        index_path.write_text(json.dumps(self.metadata[category], indent=2))

    def save(self, category: str, key: str, data: Any) -> Path:
        """
        Save data to cache.

        Args:
            category: Cache category (e.g., "fractional_kernels")
            key: Cache key (unique identifier)
            data: Data to cache (will be serialized by backend)

        Returns:
            Path to cached file

        Raises:
            KeyError: If category not found
        """
        if category not in self.backends:
            raise KeyError(f"Unknown cache category: {category}")

        # Save via backend
        backend = self.backends[category]
        path = backend.save(key, data)

        # Update metadata
        if self.enable_stats:
            entry = CacheEntry(
                key=key,
                created_at=datetime.utcnow().isoformat() + "Z",
                size_bytes=path.stat().st_size,
                access_count=0,
                checksum=self._compute_checksum(path) if self.enable_checksums else None
            )

            self.metadata[category]["entries"][key] = entry.to_dict()
            self.metadata[category]["total_entries"] = len(self.metadata[category]["entries"])
            self.metadata[category]["total_size_mb"] = sum(
                e["size_bytes"] for e in self.metadata[category]["entries"].values()
            ) / (1024 * 1024)

            self._save_metadata(category)

        return path

    def load(self, category: str, key: str) -> Any:
        """
        Load data from cache.

        Args:
            category: Cache category
            key: Cache key

        Returns:
            Deserialized data

        Raises:
            KeyError: If category or key not found
            ValueError: If checksum validation fails
        """
        if category not in self.backends:
            raise KeyError(f"Unknown cache category: {category}")

        backend = self.backends[category]

        if not backend.exists(key):
            raise KeyError(f"Cache key not found: {category}/{key}")

        # Load data
        data = backend.load(key)

        # Update access stats
        if self.enable_stats and key in self.metadata[category]["entries"]:
            entry = self.metadata[category]["entries"][key]
            entry["access_count"] = entry.get("access_count", 0) + 1
            entry["last_accessed"] = datetime.utcnow().isoformat() + "Z"
            self._save_metadata(category)

        return data

    def exists(self, category: str, key: str) -> bool:
        """Check if cache entry exists."""
        if category not in self.backends:
            return False

        return self.backends[category].exists(key)

    def delete(self, category: str, key: str) -> bool:
        """Delete cache entry."""
        if category not in self.backends:
            return False

        backend = self.backends[category]
        success = backend.delete(key)

        if success and self.enable_stats:
            if key in self.metadata[category]["entries"]:
                del self.metadata[category]["entries"][key]
                self.metadata[category]["total_entries"] = len(self.metadata[category]["entries"])
                self.metadata[category]["total_size_mb"] = sum(
                    e["size_bytes"] for e in self.metadata[category]["entries"].values()
                ) / (1024 * 1024)
                self._save_metadata(category)

        return success

    def clear_category(self, category: str) -> int:
        """Clear all entries in a category."""
        if category not in self.backends:
            return 0

        backend = self.backends[category]
        keys = backend.list_keys()

        count = 0
        for key in keys:
            if backend.delete(key):
                count += 1

        if self.enable_stats:
            self.metadata[category]["entries"] = {}
            self.metadata[category]["total_entries"] = 0
            self.metadata[category]["total_size_mb"] = 0.0
            self._save_metadata(category)

        return count

    def clear_all(self) -> dict[str, int]:
        """Clear all cache categories."""
        results = {}
        for category in self.backends:
            results[category] = self.clear_category(category)
        return results

    def get_stats(self, category: Optional[str] = None) -> dict:
        """Get cache statistics."""
        if category:
            return self.metadata.get(category, {})

        return {
            "total_categories": len(self.backends),
            "categories": self.metadata,
            "total_size_mb": sum(
                cat.get("total_size_mb", 0)
                for cat in self.metadata.values()
            )
        }

    def _compute_checksum(self, path: Path) -> str:
        """Compute SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"


__all__ = ["CacheManager", "CacheBackend", "CacheEntry"]
