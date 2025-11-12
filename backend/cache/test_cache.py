"""Integration tests for DASE cache system.

Tests all cache backends and CacheManager functionality:
- FilesystemBackend (NumPy arrays and JSON)
- ModelBackend (PyTorch models)
- BinaryBackend (FFTW wisdom)
- Metadata tracking and statistics
- Cache clearing and deletion

Run with: python -m pytest backend/cache/test_cache.py -v
"""

import json
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
import tempfile
import shutil

from cache_manager import CacheManager
from backends import FilesystemBackend, ModelBackend, BinaryBackend


class TestFilesystemBackend:
    """Test FilesystemBackend for NumPy and JSON storage."""

    def setup_method(self):
        """Create temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backend = FilesystemBackend(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_save_load_numpy_array(self):
        """Test saving and loading NumPy arrays."""
        # Create test data
        data = np.random.rand(100, 50)

        # Save
        path = self.backend.save("test_array", data)
        assert path.exists()
        assert path.suffix == ".npz"

        # Load
        loaded = self.backend.load("test_array")
        assert isinstance(loaded, np.ndarray)
        np.testing.assert_array_equal(data, loaded)

    def test_save_load_json(self):
        """Test saving and loading JSON data."""
        # Create test data
        data = {
            "alpha": 1.5,
            "dt": 0.01,
            "size": 1000,
            "enabled": True,
            "tags": ["fractional", "kernel"]
        }

        # Save
        path = self.backend.save("test_json", data)
        assert path.exists()
        assert path.suffix == ".json"

        # Load
        loaded = self.backend.load("test_json")
        assert loaded == data

    def test_save_load_multiple_arrays(self):
        """Test saving multiple NumPy arrays in one key."""
        data = {
            "coeffs": np.random.rand(100),
            "weights": np.random.rand(100),
            "biases": np.random.rand(10)
        }

        # Save
        path = self.backend.save("multi_array", data)
        assert path.suffix == ".npz"

        # Load
        loaded = self.backend.load("multi_array")
        assert isinstance(loaded, dict)
        assert set(loaded.keys()) == {"coeffs", "weights", "biases"}
        np.testing.assert_array_equal(data["coeffs"], loaded["coeffs"])

    def test_exists(self):
        """Test exists() method."""
        data = np.random.rand(50)

        assert not self.backend.exists("nonexistent")

        self.backend.save("test_key", data)
        assert self.backend.exists("test_key")

    def test_delete(self):
        """Test delete() method."""
        data = np.random.rand(50)
        self.backend.save("test_key", data)

        assert self.backend.exists("test_key")
        assert self.backend.delete("test_key")
        assert not self.backend.exists("test_key")

        # Delete non-existent key
        assert not self.backend.delete("nonexistent")

    def test_list_keys(self):
        """Test list_keys() method."""
        # Save multiple entries
        self.backend.save("array1", np.random.rand(10))
        self.backend.save("array2", np.random.rand(20))
        self.backend.save("json1", {"value": 42})

        keys = self.backend.list_keys()
        assert set(keys) == {"array1", "array2", "json1"}
        assert keys == sorted(keys)  # Should be sorted

    def test_get_size(self):
        """Test get_size() method."""
        data = np.random.rand(1000)
        self.backend.save("test_key", data)

        size = self.backend.get_size("test_key")
        assert size > 0
        assert isinstance(size, int)


class TestModelBackend:
    """Test ModelBackend for PyTorch models."""

    def setup_method(self):
        """Create temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backend = ModelBackend(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_save_load_state_dict(self):
        """Test saving and loading model state_dict."""
        # Create simple model
        model = nn.Sequential(
            nn.Linear(10, 20),
            nn.ReLU(),
            nn.Linear(20, 1)
        )
        state_dict = model.state_dict()

        # Save
        path = self.backend.save("test_model", state_dict)
        assert path.exists()
        assert path.suffix == ".pt"

        # Load
        loaded = self.backend.load("test_model")
        assert isinstance(loaded, dict)

        # Verify all keys match
        assert set(loaded.keys()) == set(state_dict.keys())

        # Verify tensors match
        for key in state_dict:
            torch.testing.assert_close(loaded[key], state_dict[key])

    def test_save_load_checkpoint(self):
        """Test saving and loading full checkpoint."""
        # Create checkpoint
        checkpoint = {
            'model_state_dict': torch.nn.Linear(5, 2).state_dict(),
            'optimizer_state_dict': {'param_groups': [{'lr': 0.001}]},
            'epoch': 42,
            'loss': 0.123
        }

        # Save
        path = self.backend.save("checkpoint_v1", checkpoint)

        # Load
        loaded = self.backend.load("checkpoint_v1")
        assert loaded['epoch'] == 42
        assert loaded['loss'] == 0.123

    def test_save_load_with_metadata(self):
        """Test saving model with metadata."""
        state_dict = torch.nn.Linear(10, 1).state_dict()
        metadata = {
            "architecture": "FeedForward",
            "input_dim": 10,
            "hidden_dims": [20, 10],
            "output_dim": 1,
            "trained_epochs": 100
        }

        # Save with metadata
        self.backend.save("model_with_meta", state_dict, metadata=metadata)

        # Load model
        loaded = self.backend.load("model_with_meta")
        assert isinstance(loaded, dict)

        # Load metadata
        loaded_meta = self.backend.load_metadata("model_with_meta")
        assert loaded_meta == metadata

    def test_map_location(self):
        """Test loading model with device mapping."""
        state_dict = torch.nn.Linear(5, 2).state_dict()
        self.backend.save("test_model", state_dict)

        # Load to CPU explicitly
        loaded = self.backend.load("test_model", map_location="cpu")
        for tensor in loaded.values():
            assert tensor.device.type == "cpu"

    def test_exists_delete(self):
        """Test exists() and delete() methods."""
        state_dict = torch.nn.Linear(5, 2).state_dict()

        assert not self.backend.exists("test_model")

        self.backend.save("test_model", state_dict)
        assert self.backend.exists("test_model")

        self.backend.delete("test_model")
        assert not self.backend.exists("test_model")


class TestBinaryBackend:
    """Test BinaryBackend for FFTW wisdom and binary data."""

    def setup_method(self):
        """Create temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backend = BinaryBackend(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_save_load_binary(self):
        """Test saving and loading binary data."""
        # Create test binary data (simulated FFTW wisdom)
        data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

        # Save
        path = self.backend.save("fftw_wisdom", data)
        assert path.exists()
        assert path.suffix == ".dat"

        # Load
        loaded = self.backend.load("fftw_wisdom")
        assert loaded == data

    def test_save_load_with_metadata(self):
        """Test saving binary data with metadata."""
        data = b"\x00\x01\x02\x03\x04\x05"
        metadata = {
            "dimensions": [512, 512],
            "planner": "FFTW_MEASURE",
            "created_at": "2025-11-11T10:00:00Z"
        }

        # Save with metadata
        self.backend.save("fftw_2d_512", data, metadata=metadata)

        # Load binary
        loaded = self.backend.load("fftw_2d_512")
        assert loaded == data

        # Load metadata
        loaded_meta = self.backend.load_metadata("fftw_2d_512")
        assert loaded_meta == metadata

    def test_invalid_data_type(self):
        """Test that non-bytes data raises error."""
        try:
            self.backend.save("invalid", "string data")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "expects bytes" in str(e)


class TestCacheManager:
    """Test unified CacheManager with all backends."""

    def setup_method(self):
        """Create temporary cache directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = CacheManager(root=self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test CacheManager creates proper directory structure."""
        expected_categories = [
            "fractional_kernels",
            "stencils",
            "fftw_wisdom",
            "echo_templates",
            "state_profiles",
            "source_maps",
            "mission_graph",
            "surrogates"
        ]

        for category in expected_categories:
            category_path = self.temp_dir / category
            assert category_path.exists()
            assert (category_path / "index.json").exists()

    def test_save_load_numpy(self):
        """Test saving and loading NumPy arrays through CacheManager."""
        # Create fractional kernel
        kernel = np.random.rand(1000)

        # Save
        path = self.cache.save("fractional_kernels", "kernel_1.5_0.01_1000", kernel)
        assert path.exists()

        # Load
        loaded = self.cache.load("fractional_kernels", "kernel_1.5_0.01_1000")
        np.testing.assert_array_equal(kernel, loaded)

    def test_save_load_model(self):
        """Test saving and loading PyTorch models."""
        model = nn.Linear(10, 1)
        state_dict = model.state_dict()

        # Save
        path = self.cache.save("surrogates", "test_surrogate_v1", state_dict)

        # Load
        loaded = self.cache.load("surrogates", "test_surrogate_v1")

        # Verify
        for key in state_dict:
            torch.testing.assert_close(loaded[key], state_dict[key])

    def test_metadata_tracking(self):
        """Test that metadata is tracked correctly."""
        data = np.random.rand(100)

        # Save data
        self.cache.save("fractional_kernels", "test_key", data)

        # Check metadata
        stats = self.cache.get_stats("fractional_kernels")
        assert stats["total_entries"] == 1
        assert "test_key" in stats["entries"]

        entry = stats["entries"]["test_key"]
        assert entry["key"] == "test_key"
        assert entry["size_bytes"] > 0
        assert "created_at" in entry
        assert entry["access_count"] == 0

    def test_access_statistics(self):
        """Test that access counts are tracked."""
        data = np.random.rand(50)

        # Save
        self.cache.save("fractional_kernels", "test_key", data)

        # Load multiple times
        for _ in range(5):
            self.cache.load("fractional_kernels", "test_key")

        # Check access count
        stats = self.cache.get_stats("fractional_kernels")
        entry = stats["entries"]["test_key"]
        assert entry["access_count"] == 5
        assert "last_accessed" in entry

    def test_exists(self):
        """Test exists() method."""
        assert not self.cache.exists("fractional_kernels", "nonexistent")

        data = np.random.rand(50)
        self.cache.save("fractional_kernels", "test_key", data)

        assert self.cache.exists("fractional_kernels", "test_key")

    def test_delete(self):
        """Test delete() method and metadata updates."""
        data = np.random.rand(50)
        self.cache.save("fractional_kernels", "test_key", data)

        # Verify exists
        assert self.cache.exists("fractional_kernels", "test_key")

        # Delete
        success = self.cache.delete("fractional_kernels", "test_key")
        assert success
        assert not self.cache.exists("fractional_kernels", "test_key")

        # Check metadata removed
        stats = self.cache.get_stats("fractional_kernels")
        assert "test_key" not in stats["entries"]
        assert stats["total_entries"] == 0

    def test_clear_category(self):
        """Test clearing entire category."""
        # Add multiple entries
        for i in range(5):
            data = np.random.rand(10)
            self.cache.save("fractional_kernels", f"key_{i}", data)

        # Verify entries exist
        stats = self.cache.get_stats("fractional_kernels")
        assert stats["total_entries"] == 5

        # Clear category
        count = self.cache.clear_category("fractional_kernels")
        assert count == 5

        # Verify all cleared
        stats = self.cache.get_stats("fractional_kernels")
        assert stats["total_entries"] == 0

    def test_clear_all(self):
        """Test clearing all categories."""
        # Add entries to multiple categories
        self.cache.save("fractional_kernels", "key1", np.random.rand(10))
        self.cache.save("stencils", "key2", np.random.rand(20))
        self.cache.save("surrogates", "key3", nn.Linear(5, 1).state_dict())

        # Clear all
        results = self.cache.clear_all()

        assert results["fractional_kernels"] >= 1
        assert results["stencils"] >= 1
        assert results["surrogates"] >= 1

        # Verify all cleared
        for category in ["fractional_kernels", "stencils", "surrogates"]:
            stats = self.cache.get_stats(category)
            assert stats["total_entries"] == 0

    def test_get_stats_all(self):
        """Test getting statistics for all categories."""
        # Add data to multiple categories
        self.cache.save("fractional_kernels", "key1", np.random.rand(100))
        self.cache.save("stencils", "key2", np.random.rand(200))

        # Get all stats
        stats = self.cache.get_stats()

        assert "total_categories" in stats
        assert "categories" in stats
        assert "total_size_mb" in stats

        assert stats["total_categories"] == 8
        assert stats["total_size_mb"] > 0

    def test_checksum_validation(self):
        """Test that checksums are computed correctly."""
        data = np.random.rand(100)

        # Save with checksums enabled
        self.cache.save("fractional_kernels", "test_key", data)

        # Check checksum exists
        stats = self.cache.get_stats("fractional_kernels")
        entry = stats["entries"]["test_key"]
        assert "checksum" in entry
        assert entry["checksum"].startswith("sha256:")

    def test_invalid_category(self):
        """Test that invalid categories raise errors."""
        try:
            self.cache.save("invalid_category", "key", np.random.rand(10))
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert "Unknown cache category" in str(e)


if __name__ == "__main__":
    print("Run tests with: python -m pytest backend/cache/test_cache.py -v")
    print("\nOr run specific test class:")
    print("  python -m pytest backend/cache/test_cache.py::TestCacheManager -v")
