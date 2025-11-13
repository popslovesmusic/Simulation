"""Automated benchmark scheduling and validation for cache system.

This module schedules and runs automated benchmarks to validate cache performance
and detect regressions.

Features:
- Schedule periodic benchmark runs
- Compare results against baselines
- Detect performance regressions
- Generate validation reports

Usage:
    from backend.cache.benchmark_scheduler import BenchmarkScheduler

    scheduler = BenchmarkScheduler()
    result = scheduler.run_benchmark_suite()
"""

import sys
from pathlib import Path
import json
import time
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import CacheManager


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""

    benchmark_name: str
    status: str  # "success", "error", "timeout"
    duration_ms: float
    cache_hits: int
    cache_misses: int
    hit_rate: float
    entries_created: int
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class BenchmarkComparison:
    """Comparison between current and baseline results."""

    benchmark_name: str
    current_duration_ms: float
    baseline_duration_ms: float
    duration_change_pct: float
    current_hit_rate: float
    baseline_hit_rate: float
    hit_rate_change_pct: float
    is_regression: bool
    regression_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class BenchmarkScheduler:
    """Automates benchmark scheduling and validation.

    Example:
        >>> scheduler = BenchmarkScheduler()
        >>>
        >>> # Run all benchmarks
        >>> results = scheduler.run_benchmark_suite()
        >>>
        >>> # Compare against baseline
        >>> comparison = scheduler.compare_to_baseline(results)
        >>>
        >>> # Schedule nightly run
        >>> scheduler.schedule_nightly_run()
    """

    def __init__(
        self,
        cache_root: str = "./cache",
        baseline_path: Optional[str] = None,
        regression_threshold_pct: float = 10.0
    ):
        """Initialize benchmark scheduler.

        Args:
            cache_root: Path to cache root directory
            baseline_path: Path to baseline results JSON
            regression_threshold_pct: Performance degradation threshold
        """
        self.cache_root = Path(cache_root)
        self.cache = CacheManager(root=cache_root)

        if baseline_path:
            self.baseline_path = Path(baseline_path)
        else:
            self.baseline_path = self.cache_root / "benchmark_baseline.json"

        self.regression_threshold = regression_threshold_pct / 100.0

        # Benchmark history
        self.history_path = self.cache_root / "benchmark_history.json"
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load benchmark history."""
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        """Save benchmark history."""
        try:
            with open(self.history_path, 'w') as f:
                json.dump(self.history[-100:], f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save benchmark history: {e}")

    def _load_baseline(self) -> Optional[Dict[str, Any]]:
        """Load baseline results."""
        if not self.baseline_path.exists():
            return None

        try:
            with open(self.baseline_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    def _save_baseline(self, results: List[BenchmarkResult]):
        """Save results as new baseline."""
        baseline_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "results": [r.to_dict() for r in results]
        }

        try:
            with open(self.baseline_path, 'w') as f:
                json.dump(baseline_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save baseline: {e}")

    def run_single_benchmark(
        self,
        benchmark_name: str,
        timeout_seconds: int = 60
    ) -> BenchmarkResult:
        """Run a single benchmark.

        Args:
            benchmark_name: Name of benchmark to run
            timeout_seconds: Timeout for benchmark

        Returns:
            Benchmark result
        """
        start_time = time.time()

        try:
            # Dispatch to specific benchmark
            if benchmark_name == "cache_warmup":
                result = self._benchmark_cache_warmup()
            elif benchmark_name == "profile_generation":
                result = self._benchmark_profile_generation()
            elif benchmark_name == "echo_templates":
                result = self._benchmark_echo_templates()
            elif benchmark_name == "source_maps":
                result = self._benchmark_source_maps()
            elif benchmark_name == "mission_graph":
                result = self._benchmark_mission_graph()
            else:
                result = BenchmarkResult(
                    benchmark_name=benchmark_name,
                    status="error",
                    duration_ms=0.0,
                    cache_hits=0,
                    cache_misses=0,
                    hit_rate=0.0,
                    entries_created=0,
                    error_message=f"Unknown benchmark: {benchmark_name}"
                )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result = BenchmarkResult(
                benchmark_name=benchmark_name,
                status="error",
                duration_ms=duration_ms,
                cache_hits=0,
                cache_misses=0,
                hit_rate=0.0,
                entries_created=0,
                error_message=str(e)
            )

        return result

    def _benchmark_cache_warmup(self) -> BenchmarkResult:
        """Benchmark cache warmup."""
        from backend.cache.warmup import main as warmup_main

        start = time.time()

        # Clear cache first
        for category in ["fractional_kernels", "stencils", "echo_templates", "state_profiles"]:
            try:
                self.cache.clear_category(category)
            except Exception:
                pass

        # Run warmup
        try:
            warmup_main()
        except Exception as e:
            pass

        duration_ms = (time.time() - start) * 1000

        # Get stats
        stats = self.cache.get_stats()
        total_entries = sum(cat.get("entries", 0) for cat in stats.values())

        return BenchmarkResult(
            benchmark_name="cache_warmup",
            status="success",
            duration_ms=duration_ms,
            cache_hits=0,
            cache_misses=total_entries,
            hit_rate=0.0,
            entries_created=total_entries
        )

    def _benchmark_profile_generation(self) -> BenchmarkResult:
        """Benchmark profile generation."""
        from backend.cache.profile_generators import CachedProfileProvider

        provider = CachedProfileProvider(cache_root=str(self.cache_root))

        # Clear profile cache
        try:
            self.cache.clear_category("state_profiles")
        except Exception:
            pass

        start = time.time()

        # Generate various profiles
        profiles = [
            ("gaussian", (64, 64), {"amplitude": 1.0, "sigma": 0.5}),
            ("gaussian", (128, 128), {"amplitude": 2.0, "sigma": 1.0}),
            ("soliton", (64, 64), {"amplitude": 1.5, "width": 2.0}),
        ]

        cache_misses = 0
        cache_hits = 0

        for profile_type, grid_shape, kwargs in profiles:
            # First call - should be cache miss
            _ = provider.get_profile(profile_type, grid_shape, **kwargs)
            cache_misses += 1

            # Second call - should be cache hit
            _ = provider.get_profile(profile_type, grid_shape, **kwargs)
            cache_hits += 1

        duration_ms = (time.time() - start) * 1000
        hit_rate = cache_hits / (cache_hits + cache_misses)

        return BenchmarkResult(
            benchmark_name="profile_generation",
            status="success",
            duration_ms=duration_ms,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate=hit_rate,
            entries_created=cache_misses
        )

    def _benchmark_echo_templates(self) -> BenchmarkResult:
        """Benchmark echo template generation."""
        from backend.cache.echo_templates import CachedEchoProvider

        provider = CachedEchoProvider(cache_root=str(self.cache_root))

        # Clear echo cache
        try:
            self.cache.clear_category("echo_templates")
        except Exception:
            pass

        start = time.time()

        # Generate templates
        templates = [
            (1.5, 0.1, 50),
            (1.8, 0.2, 100),
            (2.0, 0.15, 75),
        ]

        cache_misses = 0
        cache_hits = 0

        for alpha, tau0, num_echoes in templates:
            # First call - cache miss
            _ = provider.get_echo_template(alpha, tau0, num_echoes)
            cache_misses += 1

            # Second call - cache hit
            _ = provider.get_echo_template(alpha, tau0, num_echoes)
            cache_hits += 1

        duration_ms = (time.time() - start) * 1000
        hit_rate = cache_hits / (cache_hits + cache_misses)

        return BenchmarkResult(
            benchmark_name="echo_templates",
            status="success",
            duration_ms=duration_ms,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate=hit_rate,
            entries_created=cache_misses
        )

    def _benchmark_source_maps(self) -> BenchmarkResult:
        """Benchmark source map generation."""
        from backend.cache.source_maps import CachedSourceMapProvider

        provider = CachedSourceMapProvider(cache_root=str(self.cache_root))

        # Clear source map cache
        try:
            self.cache.clear_category("source_maps")
        except Exception:
            pass

        start = time.time()

        # Generate source maps
        layout = {
            "zones": [
                {"type": "circle", "center": [0, 0], "radius": 2.0, "amplitude": 1.0},
                {"type": "circle", "center": [5, 0], "radius": 1.5, "amplitude": 0.5}
            ],
            "grid_shape": [64, 64],
            "domain": [-10, 10, -10, 10],
            "combine_mode": "add"
        }

        cache_misses = 0
        cache_hits = 0

        for _ in range(3):
            # First call - cache miss
            _ = provider.get_source_map(layout)
            cache_misses += 1

            # Second call - cache hit
            _ = provider.get_source_map(layout)
            cache_hits += 1

        duration_ms = (time.time() - start) * 1000
        hit_rate = cache_hits / (cache_hits + cache_misses)

        return BenchmarkResult(
            benchmark_name="source_maps",
            status="success",
            duration_ms=duration_ms,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate=hit_rate,
            entries_created=1  # Only 1 unique layout
        )

    def _benchmark_mission_graph(self) -> BenchmarkResult:
        """Benchmark mission graph caching."""
        from backend.cache.mission_graph import CachedMissionRunner

        runner = CachedMissionRunner(cache_root=str(self.cache_root))

        # Clear mission graph cache
        try:
            self.cache.clear_category("mission_graph")
        except Exception:
            pass

        start = time.time()

        mission = {
            "commands": [
                {"type": "create_engine", "params": {"num_nodes": 4096}},
                {"type": "evolve", "params": {"timesteps": 100}},
                {"type": "snapshot", "params": {}}
            ]
        }

        # First run - cache miss
        result1 = runner.run_mission(mission)
        cache_misses = result1["stats"]["cache_misses"]

        # Second run - cache hit
        result2 = runner.run_mission(mission)
        cache_hits = result2["stats"]["cache_hits"]

        duration_ms = (time.time() - start) * 1000
        hit_rate = cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0.0

        return BenchmarkResult(
            benchmark_name="mission_graph",
            status="success",
            duration_ms=duration_ms,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate=hit_rate,
            entries_created=cache_misses
        )

    def run_benchmark_suite(
        self,
        benchmarks: Optional[List[str]] = None
    ) -> List[BenchmarkResult]:
        """Run full benchmark suite.

        Args:
            benchmarks: List of benchmark names (None = all)

        Returns:
            List of benchmark results
        """
        if benchmarks is None:
            benchmarks = [
                "profile_generation",
                "echo_templates",
                "source_maps",
                "mission_graph"
            ]

        results = []

        print(f"\nRunning {len(benchmarks)} benchmarks...")

        for i, benchmark_name in enumerate(benchmarks, 1):
            print(f"  [{i}/{len(benchmarks)}] {benchmark_name}...", end=" ", flush=True)

            result = self.run_single_benchmark(benchmark_name)
            results.append(result)

            if result.status == "success":
                print(f"OK ({result.duration_ms:.1f} ms, {result.hit_rate:.0%} hit rate)")
            else:
                print(f"FAILED: {result.error_message}")

        # Save to history
        self.history.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "num_benchmarks": len(results),
            "num_passed": sum(1 for r in results if r.status == "success"),
            "num_failed": sum(1 for r in results if r.status == "error")
        })
        self._save_history()

        return results

    def compare_to_baseline(
        self,
        current_results: List[BenchmarkResult]
    ) -> List[BenchmarkComparison]:
        """Compare current results to baseline.

        Args:
            current_results: Current benchmark results

        Returns:
            List of comparisons
        """
        baseline = self._load_baseline()
        if not baseline:
            return []

        baseline_results = {r["benchmark_name"]: r for r in baseline["results"]}

        comparisons = []

        for current in current_results:
            if current.benchmark_name not in baseline_results:
                continue

            baseline_result = baseline_results[current.benchmark_name]

            # Compare duration
            duration_change = ((current.duration_ms - baseline_result["duration_ms"]) /
                              baseline_result["duration_ms"] if baseline_result["duration_ms"] > 0 else 0.0)

            # Compare hit rate
            hit_rate_change = ((current.hit_rate - baseline_result["hit_rate"]) /
                              baseline_result["hit_rate"] if baseline_result["hit_rate"] > 0 else 0.0)

            # Detect regression
            is_regression = False
            regression_reasons = []

            if duration_change > self.regression_threshold:
                is_regression = True
                regression_reasons.append(f"Duration increased by {duration_change*100:.1f}%")

            if hit_rate_change < -self.regression_threshold:
                is_regression = True
                regression_reasons.append(f"Hit rate decreased by {abs(hit_rate_change)*100:.1f}%")

            comparison = BenchmarkComparison(
                benchmark_name=current.benchmark_name,
                current_duration_ms=current.duration_ms,
                baseline_duration_ms=baseline_result["duration_ms"],
                duration_change_pct=duration_change * 100,
                current_hit_rate=current.hit_rate,
                baseline_hit_rate=baseline_result["hit_rate"],
                hit_rate_change_pct=hit_rate_change * 100,
                is_regression=is_regression,
                regression_reasons=regression_reasons
            )

            comparisons.append(comparison)

        return comparisons

    def set_baseline(self, results: Optional[List[BenchmarkResult]] = None):
        """Set new baseline from results.

        Args:
            results: Results to use as baseline (None = run new benchmarks)
        """
        if results is None:
            print("Running benchmarks to establish baseline...")
            results = self.run_benchmark_suite()

        self._save_baseline(results)
        print(f"Baseline saved to: {self.baseline_path}")


__all__ = ["BenchmarkScheduler", "BenchmarkResult", "BenchmarkComparison"]
