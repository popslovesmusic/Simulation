"""Quick smoke test for cache system.

This script performs a quick validation of all cache backends
without requiring pytest. Useful for rapid verification during development.

Run with: python backend/cache/smoke_test.py
"""

import sys
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn

# Add backend directory to path for proper imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from cache import CacheManager


def test_numpy_caching():
    """Test NumPy array caching."""
    print("\n1. Testing NumPy array caching...")

    cache = CacheManager(root="./cache")

    # Save fractional kernel
    kernel = np.random.rand(1000)
    print(f"   - Saving kernel shape {kernel.shape}")
    cache.save("fractional_kernels", "test_kernel_1.5", kernel)

    # Load and verify
    loaded = cache.load("fractional_kernels", "test_kernel_1.5")
    assert np.allclose(kernel, loaded), "Kernel mismatch!"
    print("   [OK] NumPy caching works")

    # Check metadata
    stats = cache.get_stats("fractional_kernels")
    assert stats["total_entries"] >= 1
    print(f"   [OK] Metadata tracked: {stats['total_entries']} entries, {stats['total_size_mb']:.2f} MB")


def test_json_caching():
    """Test JSON caching."""
    print("\n2. Testing JSON caching...")

    cache = CacheManager(root="./cache")

    # Save stencil metadata
    stencil_info = {
        "type": "laplacian_2d",
        "grid_size": [64, 64],
        "boundary": "neumann",
        "order": 2
    }
    cache.save("stencils", "laplacian_64x64_meta", stencil_info)

    # Load and verify
    loaded = cache.load("stencils", "laplacian_64x64_meta")
    assert loaded == stencil_info, "JSON mismatch!"
    print("   [OK] JSON caching works")


def test_model_caching():
    """Test PyTorch model caching."""
    print("\n3. Testing PyTorch model caching...")

    cache = CacheManager(root="./cache")

    # Create and save model
    model = nn.Sequential(
        nn.Linear(10, 20),
        nn.ReLU(),
        nn.Linear(20, 1)
    )
    state_dict = model.state_dict()
    print(f"   - Saving model with {len(state_dict)} parameters")
    cache.save("surrogates", "test_surrogate_v1", state_dict)

    # Load and verify
    loaded = cache.load("surrogates", "test_surrogate_v1")
    assert set(loaded.keys()) == set(state_dict.keys()), "Model keys mismatch!"
    print("   [OK] PyTorch model caching works")


def test_binary_caching():
    """Test binary data caching."""
    print("\n4. Testing binary data caching...")

    cache = CacheManager(root="./cache")

    # Save simulated FFTW wisdom
    wisdom_data = b"\x00\x01\x02\x03FFTW_WISDOM_DATA"
    cache.save("fftw_wisdom", "fft_2d_512x512", wisdom_data)

    # Load and verify
    loaded = cache.load("fftw_wisdom", "fft_2d_512x512")
    assert loaded == wisdom_data, "Binary data mismatch!"
    print("   [OK] Binary caching works")


def test_access_tracking():
    """Test access statistics."""
    print("\n5. Testing access statistics...")

    cache = CacheManager(root="./cache")

    # Save test data
    data = np.random.rand(50)
    cache.save("fractional_kernels", "access_test", data)

    # Load multiple times
    for _ in range(3):
        cache.load("fractional_kernels", "access_test")

    # Check access count
    stats = cache.get_stats("fractional_kernels")
    entry = stats["entries"]["access_test"]
    assert entry["access_count"] == 3, f"Expected 3 accesses, got {entry['access_count']}"
    print(f"   [OK] Access tracking works: {entry['access_count']} accesses recorded")


def test_cache_operations():
    """Test cache operations (exists, delete, clear)."""
    print("\n6. Testing cache operations...")

    cache = CacheManager(root="./cache")

    # Test exists
    key = "operation_test"
    assert not cache.exists("fractional_kernels", key), "Key shouldn't exist yet"

    # Save and check
    cache.save("fractional_kernels", key, np.random.rand(10))
    assert cache.exists("fractional_kernels", key), "Key should exist now"
    print("   [OK] exists() works")

    # Test delete
    cache.delete("fractional_kernels", key)
    assert not cache.exists("fractional_kernels", key), "Key should be deleted"
    print("   [OK] delete() works")


def print_cache_stats():
    """Print overall cache statistics."""
    print("\n" + "="*60)
    print("CACHE STATISTICS")
    print("="*60)

    cache = CacheManager(root="./cache")
    stats = cache.get_stats()

    print(f"\nTotal Categories: {stats['total_categories']}")
    print(f"Total Size: {stats['total_size_mb']:.2f} MB")

    print("\nPer-Category Stats:")
    for category, cat_stats in stats['categories'].items():
        entries = cat_stats.get('total_entries', 0)
        size_mb = cat_stats.get('total_size_mb', 0)
        if entries > 0:
            print(f"  {category:20s}: {entries:3d} entries, {size_mb:6.2f} MB")


def main():
    """Run all smoke tests."""
    print("="*60)
    print("DASE CACHE SYSTEM - SMOKE TEST")
    print("="*60)

    try:
        test_numpy_caching()
        test_json_caching()
        test_model_caching()
        test_binary_caching()
        test_access_tracking()
        test_cache_operations()

        print_cache_stats()

        print("\n" + "="*60)
        print("[OK] ALL SMOKE TESTS PASSED")
        print("="*60)
        print("\nCache system is working correctly!")
        print("Run full test suite with: python -m pytest backend/cache/test_cache.py -v")

        return 0

    except Exception as e:
        print(f"\n[FAIL] SMOKE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
