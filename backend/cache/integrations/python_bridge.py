"""Python bridge integration for cached fractional kernels.

This module provides a drop-in replacement for fractional kernel computation
that automatically uses cached values when available, falling back to
computation when necessary.

Usage in bridge_server_improved.py:
    from backend.cache.integrations import CachedFractionalKernelProvider

    kernel_provider = CachedFractionalKernelProvider()
    coeffs = kernel_provider.get_kernel(alpha=1.5, dt=0.01, N=1000)
"""

import sys
from pathlib import Path
import numpy as np
from typing import Optional
import hashlib

# Add backend to path for cache imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cache import CacheManager


class CachedFractionalKernelProvider:
    """Provides fractional derivative kernels with automatic caching.

    This class transparently caches Grünwald-Letnikov coefficients,
    providing significant speedup for repeated computations.

    Example:
        >>> provider = CachedFractionalKernelProvider()
        >>>
        >>> # First call: compute and cache
        >>> coeffs1 = provider.get_kernel(alpha=1.5, dt=0.01, N=1000)
        >>> # Took 50ms, cached
        >>>
        >>> # Second call: load from cache
        >>> coeffs2 = provider.get_kernel(alpha=1.5, dt=0.01, N=1000)
        >>> # Took 1ms, loaded from cache
    """

    def __init__(self, cache_root: str = "./cache", enable_cache: bool = True):
        """Initialize kernel provider.

        Args:
            cache_root: Path to cache root directory
            enable_cache: If False, always recompute (useful for testing)
        """
        self.enable_cache = enable_cache

        if enable_cache:
            self.cache = CacheManager(root=cache_root)
        else:
            self.cache = None

        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_compute_time_ms": 0.0,
            "total_load_time_ms": 0.0
        }

    def get_kernel(
        self,
        alpha: float,
        dt: float,
        N: int,
        force_recompute: bool = False
    ) -> np.ndarray:
        """Get fractional derivative kernel coefficients.

        Args:
            alpha: Fractional order (typically 1.5-2.0)
            dt: Time step size
            N: Number of coefficients
            force_recompute: If True, bypass cache and recompute

        Returns:
            NumPy array of Grünwald-Letnikov coefficients
        """
        import time

        # Generate cache key
        key = self._generate_key(alpha, dt, N)

        # Try to load from cache
        if self.enable_cache and not force_recompute:
            try:
                t0 = time.time()
                coeffs = self.cache.load("fractional_kernels", key)
                t1 = time.time()

                self.stats["cache_hits"] += 1
                self.stats["total_load_time_ms"] += (t1 - t0) * 1000

                return coeffs

            except (FileNotFoundError, KeyError):
                # Not in cache, will compute below
                pass

        # Compute kernel
        t0 = time.time()
        coeffs = self._compute_kernel(alpha, dt, N)
        t1 = time.time()

        self.stats["cache_misses"] += 1
        self.stats["total_compute_time_ms"] += (t1 - t0) * 1000

        # Save to cache
        if self.enable_cache:
            try:
                self.cache.save("fractional_kernels", key, coeffs)
            except Exception as e:
                # Don't fail if cache save fails
                print(f"Warning: Failed to cache kernel: {e}")

        return coeffs

    def _generate_key(self, alpha: float, dt: float, N: int) -> str:
        """Generate cache key for kernel parameters.

        Args:
            alpha: Fractional order
            dt: Time step
            N: Number of coefficients

        Returns:
            Cache key string
        """
        # Round to avoid floating point precision issues
        alpha_str = f"{alpha:.6f}".rstrip('0').rstrip('.')
        dt_str = f"{dt:.9f}".rstrip('0').rstrip('.')

        return f"kernel_{alpha_str}_{dt_str}_{N}"

    def _compute_kernel(self, alpha: float, dt: float, N: int) -> np.ndarray:
        """Compute Grünwald-Letnikov coefficients.

        Uses the recurrence relation:
            c_0 = 1
            c_k = c_{k-1} * (k - 1 - α) / k

        Then scales by dt^α.

        Args:
            alpha: Fractional order
            dt: Time step
            N: Number of coefficients

        Returns:
            NumPy array of coefficients
        """
        coeffs = np.zeros(N, dtype=np.float64)
        coeffs[0] = 1.0

        for k in range(1, N):
            coeffs[k] = coeffs[k - 1] * (k - 1 - alpha) / k

        # Scale by dt^α
        coeffs *= dt ** alpha

        return coeffs

    def preload_common_kernels(self) -> int:
        """Preload commonly used kernels into memory cache.

        Returns:
            Number of kernels preloaded
        """
        if not self.enable_cache:
            return 0

        # Common configurations
        configs = [
            (1.5, 0.001, 1000),
            (1.5, 0.01, 1000),
            (1.5, 0.1, 1000),
            (1.8, 0.001, 1000),
            (1.8, 0.01, 1000),
            (1.8, 0.1, 1000),
            (1.9, 0.001, 1000),
            (1.9, 0.01, 1000),
            (1.9, 0.1, 1000),
        ]

        count = 0
        for alpha, dt, N in configs:
            try:
                # This will load from cache if available
                self.get_kernel(alpha, dt, N)
                count += 1
            except Exception:
                pass

        return count

    def get_stats(self) -> dict:
        """Get cache performance statistics.

        Returns:
            Dict with hit rate, miss rate, and timing info
        """
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]

        if total_requests == 0:
            hit_rate = 0.0
        else:
            hit_rate = self.stats["cache_hits"] / total_requests

        avg_load_time = (
            self.stats["total_load_time_ms"] / self.stats["cache_hits"]
            if self.stats["cache_hits"] > 0 else 0.0
        )

        avg_compute_time = (
            self.stats["total_compute_time_ms"] / self.stats["cache_misses"]
            if self.stats["cache_misses"] > 0 else 0.0
        )

        return {
            "total_requests": total_requests,
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": hit_rate,
            "avg_load_time_ms": avg_load_time,
            "avg_compute_time_ms": avg_compute_time,
            "speedup_factor": avg_compute_time / avg_load_time if avg_load_time > 0 else 0.0
        }

    def clear_stats(self):
        """Reset performance statistics."""
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_compute_time_ms": 0.0,
            "total_load_time_ms": 0.0
        }


# Example integration with bridge server
def create_fractional_kernel_endpoint(app, kernel_provider: CachedFractionalKernelProvider):
    """Add fractional kernel endpoint to Flask app.

    Usage in bridge_server_improved.py:
        kernel_provider = CachedFractionalKernelProvider()
        create_fractional_kernel_endpoint(app, kernel_provider)

    Then clients can request:
        GET /api/fractional_kernel?alpha=1.5&dt=0.01&N=1000
    """
    from flask import jsonify, request

    @app.route("/api/fractional_kernel")
    def get_fractional_kernel():
        """Get fractional derivative kernel coefficients."""
        try:
            # Parse parameters
            alpha = float(request.args.get('alpha', 1.5))
            dt = float(request.args.get('dt', 0.01))
            N = int(request.args.get('N', 1000))

            # Validate
            if not (1.0 <= alpha <= 2.0):
                return jsonify({"error": "alpha must be between 1.0 and 2.0"}), 400

            if not (1e-6 <= dt <= 1.0):
                return jsonify({"error": "dt must be between 1e-6 and 1.0"}), 400

            if not (1 <= N <= 10000):
                return jsonify({"error": "N must be between 1 and 10000"}), 400

            # Get kernel
            coeffs = kernel_provider.get_kernel(alpha, dt, N)

            return jsonify({
                "alpha": alpha,
                "dt": dt,
                "N": N,
                "coefficients": coeffs.tolist(),
                "cache_stats": kernel_provider.get_stats()
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/fractional_kernel/stats")
    def get_kernel_stats():
        """Get kernel cache statistics."""
        return jsonify(kernel_provider.get_stats())


__all__ = ["CachedFractionalKernelProvider", "create_fractional_kernel_endpoint"]
