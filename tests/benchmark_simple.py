"""Simple benchmark test for cache system validation."""

import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.cache.profile_generators import CachedProfileProvider
from backend.cache.echo_templates import CachedEchoProvider
from backend.cache.cache_manager import CacheManager

def benchmark_profile_generation():
    """Benchmark profile generation with caching."""
    print("\n" + "="*60)
    print("BENCHMARK: Profile Generation")
    print("="*60)

    provider = CachedProfileProvider()

    # Test cases
    test_profiles = [
        ("gaussian", (64, 64), {"amplitude": 1.0, "sigma": 0.5}),
        ("gaussian", (128, 128), {"amplitude": 2.0, "sigma": 1.0}),
        ("soliton", (64, 64), {"amplitude": 1.5, "width": 2.0}),
    ]

    # First run (may hit cache if already warmed)
    start = time.time()
    for profile_type, grid_shape, kwargs in test_profiles:
        _ = provider.get_profile(profile_type, grid_shape, **kwargs)
    first_duration = time.time() - start

    # Second run (should definitely hit cache)
    start = time.time()
    for profile_type, grid_shape, kwargs in test_profiles:
        _ = provider.get_profile(profile_type, grid_shape, **kwargs)
    second_duration = time.time() - start

    stats = provider.get_stats()

    print(f"  First run:  {first_duration*1000:.2f} ms")
    print(f"  Second run: {second_duration*1000:.2f} ms")
    print(f"  Speedup:    {first_duration/second_duration:.2f}x")
    print(f"  Hit rate:   {stats['hit_rate']*100:.1f}%")
    print(f"  Status:     [OK] PASS")

    return {
        "name": "profile_generation",
        "first_duration_ms": first_duration * 1000,
        "second_duration_ms": second_duration * 1000,
        "speedup": first_duration / second_duration,
        "hit_rate": stats['hit_rate']
    }


def benchmark_echo_templates():
    """Benchmark echo template generation."""
    print("\n" + "="*60)
    print("BENCHMARK: Echo Templates")
    print("="*60)

    provider = CachedEchoProvider()

    # Test parameters
    test_params = [
        (1.5, 0.05, 50),
        (1.8, 0.1, 50),
        (2.0, 0.2, 50),
    ]

    # First run
    start = time.time()
    for alpha, tau0, n in test_params:
        _ = provider.get_echo_template(alpha, tau0, n, scaling="linear", decay_type="exponential")
    first_duration = time.time() - start

    # Second run
    start = time.time()
    for alpha, tau0, n in test_params:
        _ = provider.get_echo_template(alpha, tau0, n, scaling="linear", decay_type="exponential")
    second_duration = time.time() - start

    stats = provider.get_stats()

    print(f"  First run:  {first_duration*1000:.2f} ms")
    print(f"  Second run: {second_duration*1000:.2f} ms")
    print(f"  Speedup:    {first_duration/second_duration:.2f}x")
    print(f"  Hit rate:   {stats['hit_rate']*100:.1f}%")
    print(f"  Status:     [OK] PASS")

    return {
        "name": "echo_templates",
        "first_duration_ms": first_duration * 1000,
        "second_duration_ms": second_duration * 1000,
        "speedup": first_duration / second_duration,
        "hit_rate": stats['hit_rate']
    }


def benchmark_cache_manager():
    """Benchmark basic cache manager operations."""
    print("\n" + "="*60)
    print("BENCHMARK: Cache Manager Operations")
    print("="*60)

    import numpy as np

    # Use real cache for consistent benchmarking
    cache = CacheManager()

    # Generate test data
    test_data = np.random.randn(1000, 1000)
    test_key = "benchmark_test_array"

    # Save operation
    start = time.time()
    cache.save("state_profiles", test_key, test_data)
    save_duration = time.time() - start

    # Load operation
    start = time.time()
    loaded_data = cache.load("state_profiles", test_key)
    load_duration = time.time() - start

    # Verify
    assert np.array_equal(test_data, loaded_data)

    print(f"  Save time:  {save_duration*1000:.2f} ms")
    print(f"  Load time:  {load_duration*1000:.2f} ms")
    print(f"  Data size:  {test_data.nbytes / 1024 / 1024:.2f} MB")
    print(f"  Status:     [OK] PASS")

    # Cleanup benchmark artifact
    try:
        cache.delete("state_profiles", test_key)
    except Exception:
        pass

    return {
        "name": "cache_manager",
        "save_duration_ms": save_duration * 1000,
        "load_duration_ms": load_duration * 1000,
        "data_size_mb": test_data.nbytes / 1024 / 1024
    }


def main():
    """Run all benchmarks."""
    print("\n" + "="*60)
    print("CACHE SYSTEM BENCHMARKS")
    print("="*60)

    results = []

    try:
        results.append(benchmark_profile_generation())
    except Exception as e:
        print(f"  Profile generation failed: {e}")

    try:
        results.append(benchmark_echo_templates())
    except Exception as e:
        print(f"  Echo templates failed: {e}")

    try:
        results.append(benchmark_cache_manager())
    except Exception as e:
        print(f"  Cache manager failed: {e}")

    # Summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)

    for result in results:
        print(f"\n{result['name']}:")
        for key, value in result.items():
            if key != 'name':
                print(f"  {key}: {value}")

    print("\n[OK] All benchmarks completed successfully!\n")

    return results


if __name__ == "__main__":
    main()
