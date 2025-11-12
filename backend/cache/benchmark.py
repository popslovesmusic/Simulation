"""Performance benchmarks for DASE cache system.

Measures:
- Fractional kernel computation speedup
- Laplacian stencil cache effectiveness
- FFTW wisdom load times
- Overall cache hit rates

Run with: python backend/cache/benchmark.py
"""

import sys
from pathlib import Path
import time
import numpy as np
import torch
import torch.nn as nn
from typing import List, Tuple

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import CacheManager
from cache.integrations import CachedFractionalKernelProvider


class CacheBenchmark:
    """Benchmark cache system performance."""

    def __init__(self):
        """Initialize benchmark."""
        self.cache = CacheManager(root="./cache")
        self.kernel_provider = CachedFractionalKernelProvider()

        # Clear stats
        self.kernel_provider.clear_stats()

    def benchmark_fractional_kernels(self, iterations: int = 10) -> dict:
        """Benchmark fractional kernel caching.

        Args:
            iterations: Number of repeated requests

        Returns:
            Benchmark results dict
        """
        print("\n" + "=" * 60)
        print("BENCHMARK: Fractional Kernel Caching")
        print("=" * 60)

        # Test configurations
        configs = [
            (1.5, 0.01, 1000),
            (1.8, 0.01, 1000),
            (1.9, 0.01, 5000),
        ]

        results = {
            "configs": [],
            "uncached_time_ms": [],
            "cached_time_ms": [],
            "speedup_factors": []
        }

        for alpha, dt, N in configs:
            config_str = f"alpha={alpha}, dt={dt}, N={N}"
            print(f"\nConfig: {config_str}")

            # Warm up: compute once to cache
            self.kernel_provider.get_kernel(alpha, dt, N)

            # Benchmark uncached (force recompute)
            uncached_times = []
            for _ in range(iterations):
                t0 = time.time()
                self.kernel_provider.get_kernel(alpha, dt, N, force_recompute=True)
                t1 = time.time()
                uncached_times.append((t1 - t0) * 1000)

            avg_uncached = np.mean(uncached_times)

            # Benchmark cached
            cached_times = []
            for _ in range(iterations):
                t0 = time.time()
                self.kernel_provider.get_kernel(alpha, dt, N)
                t1 = time.time()
                cached_times.append((t1 - t0) * 1000)

            avg_cached = np.mean(cached_times)

            speedup = avg_uncached / avg_cached if avg_cached > 0 else 0

            results["configs"].append(config_str)
            results["uncached_time_ms"].append(avg_uncached)
            results["cached_time_ms"].append(avg_cached)
            results["speedup_factors"].append(speedup)

            print(f"  Uncached: {avg_uncached:.2f} ms")
            print(f"  Cached:   {avg_cached:.2f} ms")
            print(f"  Speedup:  {speedup:.1f}x")

        # Overall statistics
        overall_speedup = np.mean(results["speedup_factors"])
        print(f"\n{'-' * 60}")
        print(f"Overall Average Speedup: {overall_speedup:.1f}x")

        return results

    def benchmark_stencil_caching(self, iterations: int = 100) -> dict:
        """Benchmark Laplacian stencil caching.

        Args:
            iterations: Number of repeated loads

        Returns:
            Benchmark results dict
        """
        print("\n" + "=" * 60)
        print("BENCHMARK: Laplacian Stencil Caching")
        print("=" * 60)

        # Ensure stencil exists
        key = "laplacian_2d_512x512"
        stencil_data = {
            "type": "laplacian_2d",
            "grid_size": [512, 512],
            "stencil": [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
        }

        if not self.cache.exists("stencils", key):
            self.cache.save("stencils", key, stencil_data)

        # Benchmark loads
        times = []
        for _ in range(iterations):
            t0 = time.time()
            self.cache.load("stencils", key)
            t1 = time.time()
            times.append((t1 - t0) * 1000)

        avg_time = np.mean(times)
        std_time = np.std(times)

        print(f"\nStencil: {key}")
        print(f"  Average load time: {avg_time:.3f} ms ± {std_time:.3f} ms")
        print(f"  Min: {np.min(times):.3f} ms")
        print(f"  Max: {np.max(times):.3f} ms")

        return {
            "key": key,
            "avg_time_ms": avg_time,
            "std_time_ms": std_time,
            "iterations": iterations
        }

    def benchmark_model_caching(self, iterations: int = 10) -> dict:
        """Benchmark PyTorch model caching.

        Args:
            iterations: Number of repeated save/load cycles

        Returns:
            Benchmark results dict
        """
        print("\n" + "=" * 60)
        print("BENCHMARK: PyTorch Model Caching")
        print("=" * 60)

        # Create test model
        model = nn.Sequential(
            nn.Linear(100, 500),
            nn.ReLU(),
            nn.Linear(500, 500),
            nn.ReLU(),
            nn.Linear(500, 100)
        )

        state_dict = model.state_dict()
        key = "benchmark_model"

        # Benchmark save
        save_times = []
        for i in range(iterations):
            t0 = time.time()
            self.cache.save("surrogates", f"{key}_{i}", state_dict)
            t1 = time.time()
            save_times.append((t1 - t0) * 1000)

        # Benchmark load
        load_times = []
        for i in range(iterations):
            t0 = time.time()
            self.cache.load("surrogates", f"{key}_{i}")
            t1 = time.time()
            load_times.append((t1 - t0) * 1000)

        # Clean up
        for i in range(iterations):
            self.cache.delete("surrogates", f"{key}_{i}")

        avg_save = np.mean(save_times)
        avg_load = np.mean(load_times)

        print(f"\nModel size: ~{len(state_dict)} parameters")
        print(f"  Average save time: {avg_save:.2f} ms")
        print(f"  Average load time: {avg_load:.2f} ms")
        print(f"  Save throughput:   {1000 / avg_save:.1f} models/sec")
        print(f"  Load throughput:   {1000 / avg_load:.1f} models/sec")

        return {
            "avg_save_ms": avg_save,
            "avg_load_ms": avg_load,
            "iterations": iterations
        }

    def benchmark_cache_overhead(self, iterations: int = 1000) -> dict:
        """Benchmark cache system overhead (metadata updates, etc).

        Args:
            iterations: Number of operations

        Returns:
            Benchmark results dict
        """
        print("\n" + "=" * 60)
        print("BENCHMARK: Cache System Overhead")
        print("=" * 60)

        # Small data to isolate overhead
        small_data = np.random.rand(10)

        # Benchmark exists() calls
        exists_times = []
        for _ in range(iterations):
            t0 = time.time()
            self.cache.exists("fractional_kernels", "nonexistent_key")
            t1 = time.time()
            exists_times.append((t1 - t0) * 1000)

        # Benchmark save/load cycle
        cycle_times = []
        for i in range(100):
            t0 = time.time()
            self.cache.save("fractional_kernels", f"overhead_test_{i}", small_data)
            self.cache.load("fractional_kernels", f"overhead_test_{i}")
            self.cache.delete("fractional_kernels", f"overhead_test_{i}")
            t1 = time.time()
            cycle_times.append((t1 - t0) * 1000)

        avg_exists = np.mean(exists_times)
        avg_cycle = np.mean(cycle_times)

        print(f"\nOverhead measurements:")
        print(f"  exists() call:      {avg_exists:.4f} ms")
        print(f"  save+load+delete:   {avg_cycle:.2f} ms")
        print(f"  Metadata per entry: ~200 bytes (JSON)")

        return {
            "avg_exists_ms": avg_exists,
            "avg_cycle_ms": avg_cycle
        }

    def benchmark_cache_hit_simulation(self, num_requests: int = 1000) -> dict:
        """Simulate realistic cache hit patterns.

        Args:
            num_requests: Number of simulated kernel requests

        Returns:
            Simulation results dict
        """
        print("\n" + "=" * 60)
        print("BENCHMARK: Cache Hit Rate Simulation")
        print("=" * 60)

        # Realistic distribution of kernel requests
        # (some configs used more frequently than others)
        kernel_pool = [
            (1.5, 0.01, 1000),   # Most common
            (1.5, 0.01, 1000),
            (1.5, 0.01, 1000),
            (1.8, 0.01, 1000),   # Moderately common
            (1.8, 0.01, 1000),
            (1.9, 0.01, 5000),   # Rare
        ]

        # Clear provider stats
        provider = CachedFractionalKernelProvider()
        provider.clear_stats()

        # Simulate requests
        t0 = time.time()
        for _ in range(num_requests):
            config = kernel_pool[np.random.randint(0, len(kernel_pool))]
            alpha, dt, N = config
            provider.get_kernel(alpha, dt, N)

        t1 = time.time()
        total_time = (t1 - t0) * 1000

        # Get stats
        stats = provider.get_stats()

        print(f"\nSimulation: {num_requests} requests")
        print(f"  Total time:     {total_time:.2f} ms")
        print(f"  Avg per request: {total_time / num_requests:.3f} ms")
        print(f"  Cache hits:     {stats['cache_hits']}")
        print(f"  Cache misses:   {stats['cache_misses']}")
        print(f"  Hit rate:       {stats['hit_rate'] * 100:.1f}%")
        print(f"  Speedup factor: {stats['speedup_factor']:.1f}x")

        return stats

    def run_all_benchmarks(self) -> dict:
        """Run all benchmarks and generate report.

        Returns:
            Complete benchmark results
        """
        print("\n" + "=" * 60)
        print("DASE CACHE SYSTEM - PERFORMANCE BENCHMARKS")
        print("=" * 60)

        results = {}

        results["fractional_kernels"] = self.benchmark_fractional_kernels()
        results["stencils"] = self.benchmark_stencil_caching()
        results["models"] = self.benchmark_model_caching()
        results["overhead"] = self.benchmark_cache_overhead()
        results["hit_simulation"] = self.benchmark_cache_hit_simulation()

        # Summary
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)

        kernel_speedup = np.mean(results["fractional_kernels"]["speedup_factors"])
        hit_rate = results["hit_simulation"]["hit_rate"]

        print(f"\nKey Findings:")
        print(f"  Fractional kernel speedup:  {kernel_speedup:.1f}x")
        print(f"  Stencil load time:          {results['stencils']['avg_time_ms']:.2f} ms")
        print(f"  Model save time:            {results['models']['avg_save_ms']:.2f} ms")
        print(f"  Model load time:            {results['models']['avg_load_ms']:.2f} ms")
        print(f"  Cache hit rate (sim):       {hit_rate * 100:.1f}%")
        print(f"  exists() overhead:          {results['overhead']['avg_exists_ms']:.4f} ms")

        print(f"\nRecommendation:")
        if kernel_speedup >= 10:
            print(f"  EXCELLENT - {kernel_speedup:.0f}x speedup justifies cache deployment")
        elif kernel_speedup >= 5:
            print(f"  GOOD - {kernel_speedup:.0f}x speedup recommended for production")
        elif kernel_speedup >= 2:
            print(f"  MODERATE - {kernel_speedup:.0f}x speedup, consider use case")
        else:
            print(f"  LOW - {kernel_speedup:.0f}x speedup, cache may not be beneficial")

        return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DASE Cache Performance Benchmarks"
    )

    parser.add_argument(
        '--benchmark',
        choices=['kernels', 'stencils', 'models', 'overhead', 'simulation', 'all'],
        default='all',
        help='Which benchmark to run (default: all)'
    )

    parser.add_argument(
        '--iterations',
        type=int,
        default=10,
        help='Number of iterations (default: 10)'
    )

    args = parser.parse_args()

    benchmark = CacheBenchmark()

    try:
        if args.benchmark == 'all':
            benchmark.run_all_benchmarks()

        elif args.benchmark == 'kernels':
            benchmark.benchmark_fractional_kernels(args.iterations)

        elif args.benchmark == 'stencils':
            benchmark.benchmark_stencil_caching(args.iterations)

        elif args.benchmark == 'models':
            benchmark.benchmark_model_caching(args.iterations)

        elif args.benchmark == 'overhead':
            benchmark.benchmark_cache_overhead(args.iterations)

        elif args.benchmark == 'simulation':
            benchmark.benchmark_cache_hit_simulation(args.iterations * 100)

        return 0

    except KeyboardInterrupt:
        print("\nBenchmark interrupted.")
        return 130
    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
