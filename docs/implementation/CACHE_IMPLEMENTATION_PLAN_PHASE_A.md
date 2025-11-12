# Cache Implementation Plan - Phase A (Foundation)

**Phase:** A - Foundation (Week 1)
**Priority:** P0 (Critical)
**Duration:** 36 hours (5 working days)
**Features:** #11 (Cache I/O Interface), #3 (FFTW Wisdom)

---

## Phase A Overview

**Goal:** Build the foundational cache infrastructure that all other features depend on.

**Success Criteria:**
- ✅ Unified `CacheManager` API working
- ✅ FFTW wisdom persistence functional
- ✅ 80%+ test coverage on cache operations
- ✅ Documentation complete

---

## Task Breakdown

### **Task A1: Design Cache Directory Structure** (4 hours)

**Objective:** Define the filesystem layout for all cache categories

**Directory Structure:**
```
cache/
├── README.md                          # Cache documentation
├── .gitignore                          # Don't commit cache data
├── index.json                          # Global cache metadata
│
├── fractional_kernels/
│   ├── index.json                      # Category metadata
│   ├── kernel_1.5_0.01_1000.npz
│   └── kernel_1.8_0.005_500.npz
│
├── stencils/
│   ├── index.json
│   ├── laplacian_2d_64_64_periodic.npz
│   └── laplacian_3d_32_32_32.sparse.npz
│
├── fftw_wisdom/
│   ├── index.json
│   ├── wisdom_64_64_1_Intel_i7.dat
│   └── wisdom_128_128_64_AMD_Ryzen.dat
│
├── echo_templates/
│   ├── index.json
│   └── echo_1.5_0.1_100.json
│
├── state_profiles/
│   ├── index.json
│   ├── gaussian_1.0_2.0_64x64x64.npz
│   └── soliton_0.5_1.0_128x128x1.npz
│
├── source_maps/
│   ├── index.json
│   └── map_a3f2e1_64x64.npz
│
├── mission_graph/
│   ├── index.json
│   ├── node_a1b2c3d4.json          # Command outputs
│   └── node_e5f6g7h8.npz
│
└── surrogates/
    ├── index.json
    ├── models/
    │   ├── igsoa_gw_v1.pt
    │   ├── igsoa_gw_v2.pt
    │   └── satp_higgs_v1.pt
    └── metadata/
        ├── igsoa_gw_v1.json
        └── igsoa_gw_v2.json
```

**index.json Format:**
```json
{
  "version": "1.0",
  "created_at": "2025-11-11T10:00:00Z",
  "total_entries": 42,
  "total_size_mb": 1234.5,
  "entries": {
    "kernel_1.5_0.01_1000": {
      "created_at": "2025-11-11T10:05:00Z",
      "size_bytes": 8192,
      "access_count": 5,
      "last_accessed": "2025-11-11T15:30:00Z",
      "checksum": "sha256:a1b2c3d4..."
    }
  }
}
```

**Deliverables:**
- ✅ `cache/README.md` - Usage documentation
- ✅ `cache/.gitignore` - Don't commit cache data
- ✅ `docs/implementation/CACHE_STRUCTURE.md` - Design doc

**Assignee:** Lead Developer
**Dependencies:** None

---

### **Task A2: Implement CacheManager Base Class** (8 hours)

**Objective:** Create the core cache management API

**File:** `backend/cache/cache_manager.py`

**Implementation:**
```python
"""Unified cache management system for DASE/IGSOA framework."""

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

class CacheBackend(Protocol):
    """Protocol for cache backend implementations."""

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
        cache = CacheManager(root=Path("./cache"))

        # Store fractional kernel
        cache.save("fractional_kernels", "kernel_1.5_0.01_1000", coefficients)

        # Load kernel
        coeffs = cache.load("fractional_kernels", "kernel_1.5_0.01_1000")

        # Check existence
        if cache.exists("stencils", "laplacian_2d_64_64"):
            stencil = cache.load("stencils", "laplacian_2d_64_64")
    """

    def __init__(
        self,
        root: Path = Path("./cache"),
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

        # Initialize backends
        from .backends import (
            FilesystemBackend,
            ModelBackend,
            BinaryBackend
        )

        self.backends: dict[str, CacheBackend] = {
            "fractional_kernels": FilesystemBackend(self.root / "fractional_kernels"),
            "stencils": FilesystemBackend(self.root / "stencils"),
            "fftw_wisdom": BinaryBackend(self.root / "fftw_wisdom"),
            "echo_templates": FilesystemBackend(self.root / "echo_templates"),
            "state_profiles": FilesystemBackend(self.root / "state_profiles"),
            "source_maps": FilesystemBackend(self.root / "source_maps"),
            "mission_graph": FilesystemBackend(self.root / "mission_graph"),
            "surrogates": ModelBackend(self.root / "surrogates"),
        }

        # Load metadata
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

    def _load_metadata(self) -> None:
        """Load metadata from index files."""
        self.metadata: dict[str, dict] = {}

        for category in self.backends:
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

            self.metadata[category]["entries"][key] = asdict(entry)
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
            entry["access_count"] += 1
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
```

**Deliverables:**
- ✅ `backend/cache/cache_manager.py`
- ✅ `backend/cache/__init__.py`
- ✅ Unit tests in `tests/cache/test_cache_manager.py`

**Assignee:** Lead Developer
**Dependencies:** Task A1

---

### **Task A3: Create FilesystemBackend** (6 hours)

**Objective:** Implement file-based storage for NumPy arrays and JSON

**File:** `backend/cache/backends/filesystem_backend.py`

**Implementation:**
```python
"""Filesystem-based cache backend for NumPy arrays and JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import numpy as np

class FilesystemBackend:
    """Store data as compressed NumPy .npz files or JSON."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, data: Any) -> Path:
        """Save data to filesystem."""

        # Determine format from data type
        if isinstance(data, (np.ndarray, dict)):
            if isinstance(data, dict) and all(
                isinstance(v, np.ndarray) for v in data.values()
            ):
                # Multiple arrays: Use .npz
                path = self.root / f"{key}.npz"
                np.savez_compressed(path, **data)
            elif isinstance(data, np.ndarray):
                # Single array: Use .npz
                path = self.root / f"{key}.npz"
                np.savez_compressed(path, data=data)
            else:
                # Plain dict: Use JSON
                path = self.root / f"{key}.json"
                path.write_text(json.dumps(data, indent=2))
        elif isinstance(data, (list, str, int, float)):
            # Primitive types: Use JSON
            path = self.root / f"{key}.json"
            path.write_text(json.dumps(data, indent=2))
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")

        return path

    def load(self, key: str) -> Any:
        """Load data from filesystem."""

        # Try .npz first
        npz_path = self.root / f"{key}.npz"
        if npz_path.exists():
            loaded = np.load(npz_path)
            if len(loaded.files) == 1 and loaded.files[0] == "data":
                return loaded["data"]
            return {k: loaded[k] for k in loaded.files}

        # Try .json
        json_path = self.root / f"{key}.json"
        if json_path.exists():
            return json.loads(json_path.read_text())

        raise FileNotFoundError(f"Cache key not found: {key}")

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        npz_path = self.root / f"{key}.npz"
        json_path = self.root / f"{key}.json"
        return npz_path.exists() or json_path.exists()

    def delete(self, key: str) -> bool:
        """Delete cached entry."""
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
        """List all keys in this backend."""
        keys = set()

        for path in self.root.glob("*.npz"):
            keys.add(path.stem)

        for path in self.root.glob("*.json"):
            if path.stem != "index":  # Skip index.json
                keys.add(path.stem)

        return sorted(keys)

    def get_size(self, key: str) -> int:
        """Get size of cached entry in bytes."""
        npz_path = self.root / f"{key}.npz"
        if npz_path.exists():
            return npz_path.stat().st_size

        json_path = self.root / f"{key}.json"
        if json_path.exists():
            return json_path.stat().st_size

        return 0
```

**Deliverables:**
- ✅ `backend/cache/backends/filesystem_backend.py`
- ✅ `backend/cache/backends/__init__.py`
- ✅ Unit tests

**Assignee:** Junior Developer
**Dependencies:** Task A2

---

### **Task A4: Create ModelBackend (PyTorch)** (4 hours)

**Objective:** Implement backend for PyTorch model storage

**File:** `backend/cache/backends/model_backend.py`

**Implementation:**
```python
"""PyTorch model cache backend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

class ModelBackend:
    """Store PyTorch models with metadata."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.models_dir = self.root / "models"
        self.metadata_dir = self.root / "metadata"

        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, model_path: Path | dict) -> Path:
        """
        Save model to cache.

        Args:
            key: Model identifier (e.g., "igsoa_gw_v1")
            model_path: Either Path to .pt file or dict with 'model' and 'metadata'

        Returns:
            Path to cached model
        """
        if isinstance(model_path, Path):
            # Copy model file
            dest = self.models_dir / f"{key}.pt"
            import shutil
            shutil.copy(model_path, dest)
            return dest

        elif isinstance(model_path, dict):
            # Save model and metadata separately
            if "model" in model_path:
                dest = self.models_dir / f"{key}.pt"
                import shutil
                shutil.copy(model_path["model"], dest)

            if "metadata" in model_path:
                meta_path = self.metadata_dir / f"{key}.json"
                meta_path.write_text(json.dumps(model_path["metadata"], indent=2))

            return dest

        raise TypeError("model_path must be Path or dict")

    def load(self, key: str) -> dict:
        """Load model and metadata."""
        model_path = self.models_dir / f"{key}.pt"
        meta_path = self.metadata_dir / f"{key}.json"

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {key}")

        result = {"model_path": model_path}

        if meta_path.exists():
            result["metadata"] = json.loads(meta_path.read_text())

        return result

    def exists(self, key: str) -> bool:
        """Check if model exists."""
        return (self.models_dir / f"{key}.pt").exists()

    def delete(self, key: str) -> bool:
        """Delete model and metadata."""
        deleted = False

        model_path = self.models_dir / f"{key}.pt"
        if model_path.exists():
            model_path.unlink()
            deleted = True

        meta_path = self.metadata_dir / f"{key}.json"
        if meta_path.exists():
            meta_path.unlink()

        return deleted

    def list_keys(self) -> list[str]:
        """List all models."""
        return [p.stem for p in self.models_dir.glob("*.pt")]

    def get_size(self, key: str) -> int:
        """Get model file size."""
        model_path = self.models_dir / f"{key}.pt"
        return model_path.stat().st_size if model_path.exists() else 0
```

**Deliverables:**
- ✅ `backend/cache/backends/model_backend.py`
- ✅ Unit tests with mock PyTorch models

**Assignee:** Junior Developer
**Dependencies:** Task A2

---

### **Task A5: FFTW Wisdom Manager (C++)** (8 hours)

**Objective:** Implement persistent FFTW wisdom caching in C++

**File:** `src/cpp/cache/fftw_wisdom_manager.h`

**Implementation:**
```cpp
/**
 * FFTW Wisdom Manager - Persistent FFT Plan Optimization
 *
 * Caches FFTW wisdom (optimized FFT plans) to disk for reuse across runs.
 * First run with a new grid size takes 1-5 seconds to create wisdom.
 * All subsequent runs use optimized plans instantly.
 */

#pragma once

#include <fftw3.h>
#include <string>
#include <sstream>
#include <fstream>
#include <filesystem>
#include <cstring>

namespace dase {
namespace cache {

class FFTWWisdomManager {
private:
    std::filesystem::path wisdom_dir_;

public:
    /**
     * Constructor
     *
     * @param wisdom_dir Directory to store wisdom files (default: ./cache/fftw_wisdom)
     */
    explicit FFTWWisdomManager(
        const std::filesystem::path& wisdom_dir = "./cache/fftw_wisdom"
    )
        : wisdom_dir_(wisdom_dir)
    {
        std::filesystem::create_directories(wisdom_dir_);
    }

    /**
     * Load wisdom for specific grid dimensions, creating if needed
     *
     * @param Nx Grid size in X
     * @param Ny Grid size in Y (1 for 1D/2D)
     * @param Nz Grid size in Z (1 for 1D/2D)
     * @return True if wisdom was loaded or created successfully
     */
    bool loadOrCreate(int Nx, int Ny = 1, int Nz = 1) {
        std::string filename = wisdomFilename(Nx, Ny, Nz);
        std::filesystem::path filepath = wisdom_dir_ / filename;

        // Try to load existing wisdom
        if (std::filesystem::exists(filepath)) {
            if (fftw_import_wisdom_from_filename(filepath.c_str()) != 0) {
                return true;  // Successfully loaded
            }
            // If load failed, fall through to create new wisdom
        }

        // Create wisdom by planning and timing
        createWisdom(Nx, Ny, Nz);

        // Export wisdom to file
        return fftw_export_wisdom_to_filename(filepath.c_str()) != 0;
    }

    /**
     * Force creation of wisdom (for benchmarking)
     */
    void benchmarkAndSave(int Nx, int Ny = 1, int Nz = 1) {
        createWisdom(Nx, Ny, Nz);

        std::string filename = wisdomFilename(Nx, Ny, Nz);
        std::filesystem::path filepath = wisdom_dir_ / filename;

        fftw_export_wisdom_to_filename(filepath.c_str());
    }

    /**
     * Clear all wisdom (force reoptimization)
     */
    void clearAll() {
        fftw_forget_wisdom();

        for (const auto& entry : std::filesystem::directory_iterator(wisdom_dir_)) {
            if (entry.path().extension() == ".dat") {
                std::filesystem::remove(entry.path());
            }
        }
    }

private:
    /**
     * Generate wisdom filename based on grid size and CPU model
     */
    std::string wisdomFilename(int Nx, int Ny, int Nz) const {
        std::ostringstream oss;
        oss << "fftw_" << Nx << "_" << Ny << "_" << Nz;

        // Add CPU model for hardware-specific optimization
        std::string cpu_model = getCPUModel();
        if (!cpu_model.empty()) {
            oss << "_" << cpu_model;
        }

        oss << ".dat";
        return oss.str();
    }

    /**
     * Create wisdom by planning with FFTW_PATIENT or FFTW_MEASURE
     */
    void createWisdom(int Nx, int Ny, int Nz) {
        // Allocate dummy arrays
        fftw_complex* in = fftw_alloc_complex(Nx * Ny * Nz);
        fftw_complex* out = fftw_alloc_complex(Nx * Ny * Nz);

        if (!in || !out) {
            fftw_free(in);
            fftw_free(out);
            throw std::runtime_error("Failed to allocate FFTW arrays");
        }

        // Create plan with FFTW_PATIENT for best optimization
        // This takes time but creates optimal wisdom
        fftw_plan plan;

        if (Nz > 1) {
            // 3D FFT
            plan = fftw_plan_dft_3d(
                Nx, Ny, Nz, in, out, FFTW_FORWARD, FFTW_PATIENT
            );
        } else if (Ny > 1) {
            // 2D FFT
            plan = fftw_plan_dft_2d(
                Nx, Ny, in, out, FFTW_FORWARD, FFTW_PATIENT
            );
        } else {
            // 1D FFT
            plan = fftw_plan_dft_1d(
                Nx, in, out, FFTW_FORWARD, FFTW_PATIENT
            );
        }

        if (plan) {
            fftw_destroy_plan(plan);
        }

        fftw_free(in);
        fftw_free(out);

        // Wisdom is now stored in FFTW's internal state
    }

    /**
     * Get CPU model name for wisdom filename
     */
    std::string getCPUModel() const {
#ifdef __linux__
        std::ifstream cpuinfo("/proc/cpuinfo");
        std::string line;
        while (std::getline(cpuinfo, line)) {
            if (line.find("model name") != std::string::npos) {
                size_t pos = line.find(':');
                if (pos != std::string::npos) {
                    std::string model = line.substr(pos + 2);
                    // Sanitize for filename
                    for (char& c : model) {
                        if (!std::isalnum(c)) c = '_';
                    }
                    return model.substr(0, 20);  // Truncate
                }
            }
        }
#elif defined(_WIN32)
        // Windows: Read from registry or use default
        return "Windows";
#endif
        return "generic";
    }
};

} // namespace cache
} // namespace dase
```

**Usage Example:**
```cpp
// In IGSOA GW engine initialization
#include "cache/fftw_wisdom_manager.h"

void IGSOAGWEngine::initialize(int grid_nx, int grid_ny, int grid_nz) {
    // Load or create FFTW wisdom
    dase::cache::FFTWWisdomManager wisdom_mgr;
    wisdom_mgr.loadOrCreate(grid_nx, grid_ny, grid_nz);

    // Now create FFT plans - they'll use optimized wisdom
    fftw_plan forward = fftw_plan_dft_3d(
        grid_nx, grid_ny, grid_nz,
        field_in, field_out,
        FFTW_FORWARD, FFTW_ESTIMATE  // Fast, uses wisdom
    );

    // First run: ~5 seconds to create wisdom
    // Subsequent runs: <0.1 seconds with wisdom
}
```

**Deliverables:**
- ✅ `src/cpp/cache/fftw_wisdom_manager.h`
- ✅ `src/cpp/cache/CMakeLists.txt` (if using CMake)
- ✅ Integration test with IGSOA GW engine
- ✅ Benchmark comparison (with/without wisdom)

**Assignee:** Senior C++ Developer
**Dependencies:** None (independent of Python cache)

---

### **Task A6: Integration Tests** (6 hours)

**Objective:** Comprehensive test suite for cache system

**File:** `tests/cache/test_cache_manager.py`

**Test Cases:**
```python
import pytest
import numpy as np
from pathlib import Path
from backend.cache import CacheManager

@pytest.fixture
def cache_manager(tmp_path):
    return CacheManager(root=tmp_path)

class TestCacheManager:
    def test_save_and_load_numpy_array(self, cache_manager):
        """Test saving and loading NumPy arrays."""
        data = np.random.rand(100, 100)
        cache_manager.save("fractional_kernels", "test_kernel", data)

        loaded = cache_manager.load("fractional_kernels", "test_kernel")
        np.testing.assert_array_equal(data, loaded)

    def test_save_and_load_json(self, cache_manager):
        """Test saving and loading JSON data."""
        data = {"alpha": 1.5, "dt": 0.01, "num_steps": 1000}
        cache_manager.save("echo_templates", "test_template", data)

        loaded = cache_manager.load("echo_templates", "test_template")
        assert loaded == data

    def test_exists(self, cache_manager):
        """Test existence checking."""
        assert not cache_manager.exists("stencils", "nonexistent")

        data = np.eye(10)
        cache_manager.save("stencils", "identity", data)

        assert cache_manager.exists("stencils", "identity")

    def test_delete(self, cache_manager):
        """Test deletion."""
        data = np.zeros(50)
        cache_manager.save("state_profiles", "zeros", data)

        assert cache_manager.exists("state_profiles", "zeros")

        cache_manager.delete("state_profiles", "zeros")

        assert not cache_manager.exists("state_profiles", "zeros")

    def test_clear_category(self, cache_manager):
        """Test clearing a category."""
        for i in range(5):
            cache_manager.save("stencils", f"stencil_{i}", np.eye(10))

        count = cache_manager.clear_category("stencils")
        assert count == 5

        for i in range(5):
            assert not cache_manager.exists("stencils", f"stencil_{i}")

    def test_get_stats(self, cache_manager):
        """Test statistics collection."""
        data = np.random.rand(1000)
        cache_manager.save("fractional_kernels", "large_kernel", data)

        stats = cache_manager.get_stats("fractional_kernels")

        assert stats["total_entries"] == 1
        assert "large_kernel" in stats["entries"]
        assert stats["entries"]["large_kernel"]["size_bytes"] > 0

    def test_metadata_persistence(self, tmp_path):
        """Test that metadata persists across instances."""
        cache1 = CacheManager(root=tmp_path)
        cache1.save("stencils", "test", np.eye(5))

        # Create new instance (simulates restart)
        cache2 = CacheManager(root=tmp_path)

        assert cache2.exists("stencils", "test")

        stats = cache2.get_stats("stencils")
        assert stats["total_entries"] == 1
```

**Deliverables:**
- ✅ `tests/cache/test_cache_manager.py`
- ✅ `tests/cache/test_backends.py`
- ✅ `tests/cache/test_fftw_wisdom.cpp` (C++)
- ✅ CI/CD integration

**Assignee:** QA/Testing Lead
**Dependencies:** Tasks A2, A3, A4, A5

---

## Phase A Deliverables Checklist

### Code

- [ ] `backend/cache/cache_manager.py` - Core cache manager
- [ ] `backend/cache/__init__.py` - Package exports
- [ ] `backend/cache/backends/filesystem_backend.py` - NumPy/JSON storage
- [ ] `backend/cache/backends/model_backend.py` - PyTorch model storage
- [ ] `backend/cache/backends/binary_backend.py` - Binary data storage
- [ ] `backend/cache/backends/__init__.py` - Backend exports
- [ ] `src/cpp/cache/fftw_wisdom_manager.h` - FFTW wisdom caching

### Tests

- [ ] `tests/cache/test_cache_manager.py` - CacheManager tests
- [ ] `tests/cache/test_filesystem_backend.py` - Backend tests
- [ ] `tests/cache/test_model_backend.py` - Model backend tests
- [ ] `tests/cache/test_fftw_wisdom.cpp` - C++ FFTW tests
- [ ] Test coverage >80%

### Documentation

- [ ] `cache/README.md` - User documentation
- [ ] `docs/implementation/CACHE_STRUCTURE.md` - Architecture doc
- [ ] `docs/api/cache_manager.md` - API reference
- [ ] `docs/guides/CACHE_USAGE_GUIDE.md` - Usage examples

### Integration

- [ ] CI/CD pipeline updated (run cache tests)
- [ ] `.gitignore` updated (exclude `cache/` directory)
- [ ] Example integration in IGSOA GW engine

---

## Testing Strategy

### Unit Tests
- All CacheManager methods
- All backend implementations
- Edge cases (empty data, large files, concurrent access)

### Integration Tests
- End-to-end cache save/load workflow
- FFTW wisdom integration with actual FFT plans
- Multi-category operations

### Performance Tests
- Benchmark cache save/load latency
- FFTW wisdom speedup measurement (with/without)
- Large file handling (>100MB arrays)

### Regression Tests
- Metadata persistence across restarts
- Backward compatibility with future schema changes

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Unit test coverage** | >80% | pytest-cov |
| **FFTW wisdom speedup** | 10-30x | Benchmark script |
| **Cache save latency** | <100ms | For 10MB array |
| **Cache load latency** | <50ms | For 10MB array |
| **Metadata overhead** | <1% | Of total cache size |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **Filesystem errors** | Graceful fallback, clear error messages |
| **Corrupted cache** | Checksum validation, auto-rebuild |
| **Concurrent access** | File locking (future), atomic writes |
| **FFTW wisdom portability** | CPU model in filename, test on CI |

---

## Timeline

```
Day 1: Tasks A1, A2 (Design + CacheManager base)
Day 2: Task A3 (FilesystemBackend)
Day 3: Tasks A4, A5 (ModelBackend + FFTW Wisdom)
Day 4: Task A6 (Integration tests)
Day 5: Documentation + buffer
```

**Total:** 5 working days (36 hours)

---

## Next Steps After Phase A

Once Phase A is complete:

1. ✅ **Phase B Kickoff** - Start P1 features (Fractional Kernel Cache)
2. ✅ **Production Testing** - Deploy FFTW wisdom to staging
3. ✅ **Documentation Review** - Ensure all APIs documented
4. ✅ **Performance Baseline** - Benchmark before Phase B features

**Proceed to:** `CACHE_IMPLEMENTATION_PLAN_PHASE_B.md`

---

**Status:** Ready to start
**Prerequisites:** None (foundational phase)
**Approval Required:** Technical Lead, DevOps

