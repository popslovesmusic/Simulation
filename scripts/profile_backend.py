"""
Backend Performance Profiling Script

Profiles Python backend performance to establish baselines and identify bottlenecks.
Generates comprehensive performance report with recommendations.

Usage:
    python scripts/profile_backend.py
    python scripts/profile_backend.py --output-dir reports/
    python scripts/profile_backend.py --quick  # Fast profiling for CI
"""

import sys
import time
import json
import cProfile
import pstats
from pathlib import Path
from datetime import datetime
from io import StringIO
import tracemalloc
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    import numpy as np
    from cache.cache_manager import CacheManager
    from cache.profile_generators import CachedProfileProvider
    from cache.echo_templates import CachedEchoProvider
    from cache.benchmark_scheduler import BenchmarkScheduler
    from cache.governance_agent import CacheGovernanceAgent
except ImportError as e:
    print(f"Warning: Could not import backend modules: {e}")
    print("Some profiling tests will be skipped")


class BackendProfiler:
    """Comprehensive backend profiler."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("reports/profiling")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        self.timestamp = datetime.utcnow().isoformat()

    def profile_cache_operations(self) -> Dict[str, Any]:
        """Profile cache read/write operations."""
        print("\n=== Profiling Cache Operations ===")

        try:
            cache = CacheManager(root=Path("cache"))
            results = {}

            # Profile: Save operation
            print("  Profiling save operation...")
            data = np.random.rand(1000, 1000)  # 8 MB array

            start = time.perf_counter()
            cache.save("fractional_kernels", "profile_test_key", data)
            save_duration = time.perf_counter() - start

            results['save_time_ms'] = save_duration * 1000
            results['save_throughput_mbps'] = (data.nbytes / 1e6) / save_duration

            # Profile: Load operation
            print("  Profiling load operation...")
            start = time.perf_counter()
            loaded = cache.load("fractional_kernels", "profile_test_key")
            load_duration = time.perf_counter() - start

            results['load_time_ms'] = load_duration * 1000
            results['load_throughput_mbps'] = (data.nbytes / 1e6) / load_duration

            # Profile: Metadata query
            print("  Profiling metadata operations...")
            start = time.perf_counter()
            stats = cache.get_stats("fractional_kernels")
            metadata_duration = time.perf_counter() - start

            results['metadata_time_ms'] = metadata_duration * 1000

            # Cleanup
            cache.delete("fractional_kernels", "profile_test_key")

            print(f"    Save: {results['save_time_ms']:.2f} ms ({results['save_throughput_mbps']:.1f} MB/s)")
            print(f"    Load: {results['load_time_ms']:.2f} ms ({results['load_throughput_mbps']:.1f} MB/s)")
            print(f"    Metadata: {results['metadata_time_ms']:.2f} ms")

            return results

        except Exception as e:
            print(f"  ERROR: {e}")
            return {'error': str(e)}

    def profile_profile_generation(self) -> Dict[str, Any]:
        """Profile initial state profile generation."""
        print("\n=== Profiling Profile Generation ===")

        try:
            provider = CachedProfileProvider()
            results = {}

            # Profile: Gaussian 2D generation
            print("  Profiling 2D Gaussian generation...")
            start = time.perf_counter()
            psi_2d = provider.get_profile("gaussian", (256, 256), amplitude=1.0, sigma=1.0)
            duration_2d = time.perf_counter() - start

            results['gaussian_2d_time_ms'] = duration_2d * 1000
            results['gaussian_2d_shape'] = psi_2d.shape

            # Profile: Gaussian 3D generation
            print("  Profiling 3D Gaussian generation...")
            start = time.perf_counter()
            psi_3d = provider.get_profile("gaussian", (64, 64, 64), amplitude=1.0, sigma=1.0)
            duration_3d = time.perf_counter() - start

            results['gaussian_3d_time_ms'] = duration_3d * 1000
            results['gaussian_3d_shape'] = psi_3d.shape

            # Profile: Field triplet generation
            print("  Profiling field triplet generation...")
            start = time.perf_counter()
            psi, phi, h = provider.get_field_triplet("gaussian", (64, 64, 64), amplitude=1.0, sigma=1.0)
            duration_triplet = time.perf_counter() - start

            results['field_triplet_time_ms'] = duration_triplet * 1000

            # Get cache statistics
            stats = provider.get_stats()
            results['cache_hit_rate'] = stats['hit_rate']
            results['cache_hits'] = stats['cache_hits']
            results['cache_misses'] = stats['cache_misses']

            print(f"    2D Gaussian: {results['gaussian_2d_time_ms']:.2f} ms")
            print(f"    3D Gaussian: {results['gaussian_3d_time_ms']:.2f} ms")
            print(f"    Field triplet: {results['field_triplet_time_ms']:.2f} ms")
            print(f"    Cache hit rate: {results['cache_hit_rate']*100:.1f}%")

            return results

        except Exception as e:
            print(f"  ERROR: {e}")
            return {'error': str(e)}

    def profile_echo_templates(self) -> Dict[str, Any]:
        """Profile echo template generation."""
        print("\n=== Profiling Echo Template Generation ===")

        try:
            provider = CachedEchoProvider()
            results = {}

            # Profile: Single template generation
            print("  Profiling single template generation...")
            start = time.perf_counter()
            template = provider.get_echo_template(alpha=1.8, tau0=0.1, num_echoes=100)
            duration_single = time.perf_counter() - start

            results['single_template_time_ms'] = duration_single * 1000
            results['num_echoes'] = len(template['echo_times'])

            # Profile: Parameter sweep
            print("  Profiling parameter sweep...")
            alphas = [1.5, 1.8, 2.0]
            tau0s = [0.05, 0.1, 0.2]

            start = time.perf_counter()
            templates = provider.get_multiple_templates(alphas, tau0s, num_echoes=50)
            duration_sweep = time.perf_counter() - start

            results['parameter_sweep_time_ms'] = duration_sweep * 1000
            results['templates_generated'] = len(templates)
            results['time_per_template_ms'] = duration_sweep * 1000 / len(templates)

            # Get cache statistics
            stats = provider.get_stats()
            results['cache_hit_rate'] = stats['hit_rate']

            print(f"    Single template: {results['single_template_time_ms']:.2f} ms")
            print(f"    Parameter sweep: {results['parameter_sweep_time_ms']:.2f} ms ({results['templates_generated']} templates)")
            print(f"    Time per template: {results['time_per_template_ms']:.2f} ms")
            print(f"    Cache hit rate: {results['cache_hit_rate']*100:.1f}%")

            return results

        except Exception as e:
            print(f"  ERROR: {e}")
            return {'error': str(e)}

    def profile_memory_usage(self) -> Dict[str, Any]:
        """Profile memory usage of key operations."""
        print("\n=== Profiling Memory Usage ===")

        results = {}

        try:
            # Start memory tracking
            tracemalloc.start()

            # Memory: Large array creation
            print("  Profiling large array creation...")
            snapshot_before = tracemalloc.take_snapshot()

            large_array = np.random.rand(1000, 1000, 10)  # ~80 MB

            snapshot_after = tracemalloc.take_snapshot()
            top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')

            memory_used = sum(stat.size_diff for stat in top_stats)
            results['array_creation_mb'] = memory_used / 1e6

            # Memory: Cache operations
            print("  Profiling cache memory usage...")
            try:
                snapshot_before = tracemalloc.take_snapshot()

                cache = CacheManager(root=Path("cache"))
                data = np.random.rand(500, 500)
                cache.save("fractional_kernels", "memory_test", data)
                loaded = cache.load("fractional_kernels", "memory_test")

                snapshot_after = tracemalloc.take_snapshot()
                top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')

                memory_used = sum(stat.size_diff for stat in top_stats)
                results['cache_ops_mb'] = memory_used / 1e6

                cache.delete("fractional_kernels", "memory_test")

            except Exception as e:
                results['cache_ops_error'] = str(e)

            # Get current memory usage
            current, peak = tracemalloc.get_traced_memory()
            results['current_memory_mb'] = current / 1e6
            results['peak_memory_mb'] = peak / 1e6

            tracemalloc.stop()

            print(f"    Array creation: {results['array_creation_mb']:.2f} MB")
            if 'cache_ops_mb' in results:
                print(f"    Cache operations: {results['cache_ops_mb']:.2f} MB")
            print(f"    Peak memory: {results['peak_memory_mb']:.2f} MB")

            return results

        except Exception as e:
            tracemalloc.stop()
            print(f"  ERROR: {e}")
            return {'error': str(e)}

    def profile_with_cprofile(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Profile function with cProfile and extract statistics."""
        profiler = cProfile.Profile()
        profiler.enable()

        result = func(*args, **kwargs)

        profiler.disable()

        # Get statistics
        stream = StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions

        return {
            'profile_output': stream.getvalue(),
            'total_calls': stats.total_calls,
            'primitive_calls': stats.prim_calls,
        }

    def run_all_profiles(self, quick: bool = False):
        """Run all profiling tests."""
        print("="*60)
        print("BACKEND PERFORMANCE PROFILING")
        print("="*60)
        print(f"Timestamp: {self.timestamp}")
        print(f"Output directory: {self.output_dir}")
        print(f"Quick mode: {quick}")
        print()

        # Cache operations
        self.results['cache_operations'] = self.profile_cache_operations()

        # Profile generation
        self.results['profile_generation'] = self.profile_profile_generation()

        # Echo templates
        self.results['echo_templates'] = self.profile_echo_templates()

        # Memory usage
        if not quick:
            self.results['memory_usage'] = self.profile_memory_usage()

        # Add metadata
        self.results['metadata'] = {
            'timestamp': self.timestamp,
            'python_version': sys.version,
            'numpy_version': np.__version__,
            'quick_mode': quick,
        }

        print("\n" + "="*60)
        print("PROFILING COMPLETE")
        print("="*60)

    def generate_report(self) -> str:
        """Generate markdown report."""
        lines = ["# Backend Performance Profiling Report"]
        lines.append(f"\n**Date**: {self.timestamp}")
        lines.append(f"**Python**: {sys.version.split()[0]}")
        lines.append(f"**NumPy**: {np.__version__}")
        lines.append("\n---\n")

        lines.append("## Summary\n")

        # Cache operations summary
        if 'cache_operations' in self.results and 'error' not in self.results['cache_operations']:
            cache_ops = self.results['cache_operations']
            lines.append("### Cache Operations\n")
            lines.append(f"- **Save**: {cache_ops['save_time_ms']:.2f} ms ({cache_ops['save_throughput_mbps']:.1f} MB/s)")
            lines.append(f"- **Load**: {cache_ops['load_time_ms']:.2f} ms ({cache_ops['load_throughput_mbps']:.1f} MB/s)")
            lines.append(f"- **Metadata**: {cache_ops['metadata_time_ms']:.2f} ms")
            lines.append("")

        # Profile generation summary
        if 'profile_generation' in self.results and 'error' not in self.results['profile_generation']:
            prof_gen = self.results['profile_generation']
            lines.append("### Profile Generation\n")
            lines.append(f"- **2D Gaussian**: {prof_gen['gaussian_2d_time_ms']:.2f} ms")
            lines.append(f"- **3D Gaussian**: {prof_gen['gaussian_3d_time_ms']:.2f} ms")
            lines.append(f"- **Field Triplet**: {prof_gen['field_triplet_time_ms']:.2f} ms")
            lines.append(f"- **Cache Hit Rate**: {prof_gen['cache_hit_rate']*100:.1f}%")
            lines.append("")

        # Echo templates summary
        if 'echo_templates' in self.results and 'error' not in self.results['echo_templates']:
            echo = self.results['echo_templates']
            lines.append("### Echo Templates\n")
            lines.append(f"- **Single Template**: {echo['single_template_time_ms']:.2f} ms")
            lines.append(f"- **Parameter Sweep**: {echo['parameter_sweep_time_ms']:.2f} ms ({echo['templates_generated']} templates)")
            lines.append(f"- **Time per Template**: {echo['time_per_template_ms']:.2f} ms")
            lines.append("")

        # Memory usage summary
        if 'memory_usage' in self.results and 'error' not in self.results['memory_usage']:
            mem = self.results['memory_usage']
            lines.append("### Memory Usage\n")
            lines.append(f"- **Array Creation**: {mem['array_creation_mb']:.2f} MB")
            if 'cache_ops_mb' in mem:
                lines.append(f"- **Cache Operations**: {mem['cache_ops_mb']:.2f} MB")
            lines.append(f"- **Peak Memory**: {mem['peak_memory_mb']:.2f} MB")
            lines.append("")

        lines.append("\n---\n")
        lines.append("## Bottleneck Analysis\n")
        lines.append("*To be added based on detailed profiling*\n")

        lines.append("\n---\n")
        lines.append("## Recommendations\n")
        lines.append("*To be added based on analysis*\n")

        return "\n".join(lines)

    def save_results(self):
        """Save profiling results to files."""
        # Save JSON
        json_path = self.output_dir / f"backend_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\nResults saved to: {json_path}")

        # Save markdown report
        md_path = self.output_dir / f"backend_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md_path, 'w') as f:
            f.write(self.generate_report())
        print(f"Report saved to: {md_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Profile backend performance")
    parser.add_argument('--output-dir', type=Path, help="Output directory for reports")
    parser.add_argument('--quick', action='store_true', help="Quick profiling (skip memory tests)")

    args = parser.parse_args()

    profiler = BackendProfiler(output_dir=args.output_dir)
    profiler.run_all_profiles(quick=args.quick)
    profiler.save_results()


if __name__ == "__main__":
    main()
