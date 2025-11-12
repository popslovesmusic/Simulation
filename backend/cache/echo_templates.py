"""Prime-Gap Echo Template Generator for IGSOA GW Engine.

This module generates echo schedules based on prime number gaps,
used for gravitational wave echo detection in IGSOA simulations.

The prime-gap structure provides:
- Non-uniform sampling to avoid aliasing
- Natural irregular spacing for echo detection
- Deterministic but pseudo-random intervals

Usage:
    from backend.cache.echo_templates import CachedEchoProvider

    provider = CachedEchoProvider()
    template = provider.get_echo_template(
        alpha=1.8,
        tau0=0.1,
        num_echoes=100
    )
"""

import sys
from pathlib import Path
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import hashlib

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import CacheManager


class PrimeGapGenerator:
    """Generate prime numbers and compute gaps."""

    @staticmethod
    def sieve_of_eratosthenes(limit: int) -> np.ndarray:
        """Generate primes up to limit using Sieve of Eratosthenes.

        Args:
            limit: Upper bound for prime search

        Returns:
            Array of prime numbers
        """
        if limit < 2:
            return np.array([], dtype=np.int32)

        # Create boolean array
        is_prime = np.ones(limit + 1, dtype=bool)
        is_prime[0:2] = False

        # Sieve
        for i in range(2, int(np.sqrt(limit)) + 1):
            if is_prime[i]:
                is_prime[i*i::i] = False

        return np.where(is_prime)[0].astype(np.int32)

    @staticmethod
    def get_prime_gaps(num_primes: int) -> np.ndarray:
        """Get first N prime gaps.

        Args:
            num_primes: Number of prime gaps to generate

        Returns:
            Array of prime gaps
        """
        # Estimate upper bound (prime number theorem)
        if num_primes < 10:
            limit = 100
        else:
            limit = int(num_primes * (np.log(num_primes) + np.log(np.log(num_primes)) + 2))

        # Generate primes
        primes = PrimeGapGenerator.sieve_of_eratosthenes(limit)

        while len(primes) < num_primes + 1:
            limit *= 2
            primes = PrimeGapGenerator.sieve_of_eratosthenes(limit)

        # Compute gaps
        gaps = np.diff(primes[:num_primes + 1])

        return gaps[:num_primes]


class EchoTemplateGenerator:
    """Generate echo templates with prime-gap timing."""

    @staticmethod
    def generate_echo_timings(
        tau0: float,
        num_echoes: int,
        alpha: float = 1.8,
        scaling: str = "linear"
    ) -> np.ndarray:
        """Generate echo timing schedule based on prime gaps.

        Args:
            tau0: Base echo delay time
            num_echoes: Number of echoes
            alpha: Fractional order parameter (affects amplitude decay)
            scaling: "linear", "logarithmic", or "power"

        Returns:
            Array of echo arrival times
        """
        # Get prime gaps
        gaps = PrimeGapGenerator.get_prime_gaps(num_echoes)

        # Normalize gaps
        gaps_norm = gaps.astype(np.float64) / np.mean(gaps)

        # Scale to base delay
        if scaling == "linear":
            delays = gaps_norm * tau0
        elif scaling == "logarithmic":
            delays = np.log1p(gaps_norm) * tau0
        elif scaling == "power":
            delays = (gaps_norm ** alpha) * tau0
        else:
            raise ValueError(f"Unknown scaling: {scaling}")

        # Compute cumulative timing
        echo_times = np.cumsum(delays)

        return echo_times

    @staticmethod
    def generate_echo_envelopes(
        echo_times: np.ndarray,
        alpha: float = 1.8,
        decay_type: str = "exponential"
    ) -> np.ndarray:
        """Generate normalized echo amplitude envelopes.

        Args:
            echo_times: Echo arrival times
            alpha: Fractional decay parameter
            decay_type: "exponential", "power_law", or "gaussian"

        Returns:
            Array of normalized echo amplitudes
        """
        t = echo_times
        t0 = t[0] if len(t) > 0 else 1.0

        if decay_type == "exponential":
            # Exponential decay: exp(-alpha * t / t0)
            envelopes = np.exp(-alpha * t / t0)

        elif decay_type == "power_law":
            # Power-law decay: (t0 / t)^alpha
            envelopes = (t0 / t) ** alpha

        elif decay_type == "gaussian":
            # Gaussian decay: exp(-(t/t0)^2 / (2*alpha))
            envelopes = np.exp(-(t / t0) ** 2 / (2 * alpha))

        else:
            raise ValueError(f"Unknown decay type: {decay_type}")

        # Normalize to [0, 1]
        envelopes /= np.max(envelopes)

        return envelopes

    @staticmethod
    def generate_template(
        alpha: float,
        tau0: float,
        num_echoes: int,
        scaling: str = "linear",
        decay_type: str = "exponential"
    ) -> Dict[str, Any]:
        """Generate complete echo template.

        Args:
            alpha: Fractional parameter
            tau0: Base delay time
            num_echoes: Number of echoes
            scaling: Time scaling method
            decay_type: Amplitude decay type

        Returns:
            Template dict with times, amplitudes, gaps, metadata
        """
        # Generate timing schedule
        echo_times = EchoTemplateGenerator.generate_echo_timings(
            tau0, num_echoes, alpha, scaling
        )

        # Generate amplitude envelopes
        echo_amplitudes = EchoTemplateGenerator.generate_echo_envelopes(
            echo_times, alpha, decay_type
        )

        # Get prime gaps
        prime_gaps = PrimeGapGenerator.get_prime_gaps(num_echoes)

        # Compute statistics
        template = {
            "alpha": alpha,
            "tau0": tau0,
            "num_echoes": num_echoes,
            "scaling": scaling,
            "decay_type": decay_type,
            "echo_times": echo_times,
            "echo_amplitudes": echo_amplitudes,
            "prime_gaps": prime_gaps,
            "metadata": {
                "total_duration": echo_times[-1] if len(echo_times) > 0 else 0.0,
                "mean_gap": np.mean(prime_gaps),
                "std_gap": np.std(prime_gaps),
                "mean_amplitude": np.mean(echo_amplitudes),
                "decay_rate": -np.log(echo_amplitudes[-1] / echo_amplitudes[0]) / echo_times[-1]
                    if len(echo_times) > 0 else 0.0
            }
        }

        return template


class CachedEchoProvider:
    """Provides echo templates with automatic caching.

    Example:
        >>> provider = CachedEchoProvider()
        >>>
        >>> # Get echo template (automatically cached)
        >>> template = provider.get_echo_template(
        ...     alpha=1.8,
        ...     tau0=0.1,
        ...     num_echoes=100
        ... )
        >>>
        >>> print(f"Total duration: {template['metadata']['total_duration']:.3f}s")
        >>> print(f"Mean gap: {template['metadata']['mean_gap']:.2f}")
    """

    def __init__(self, cache_root: str = "./cache", enable_cache: bool = True):
        """Initialize echo provider.

        Args:
            cache_root: Path to cache root directory
            enable_cache: If False, always recompute
        """
        self.enable_cache = enable_cache
        self.generator = EchoTemplateGenerator()

        if enable_cache:
            self.cache = CacheManager(root=cache_root)
        else:
            self.cache = None

        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0
        }

    def get_echo_template(
        self,
        alpha: float,
        tau0: float,
        num_echoes: int,
        scaling: str = "linear",
        decay_type: str = "exponential",
        force_recompute: bool = False
    ) -> Dict[str, Any]:
        """Get echo template (cached if available).

        Args:
            alpha: Fractional parameter
            tau0: Base delay time
            num_echoes: Number of echoes
            scaling: Time scaling method
            decay_type: Amplitude decay type
            force_recompute: If True, bypass cache

        Returns:
            Echo template dict
        """
        # Generate cache key
        key = self._generate_key(alpha, tau0, num_echoes, scaling, decay_type)

        # Try to load from cache
        if self.enable_cache and not force_recompute:
            try:
                # Load arrays
                cache_data = self.cache.load("echo_templates", key)

                # Load metadata
                meta_key = key + "_meta"
                metadata_full = self.cache.load("echo_templates", meta_key)

                # Reconstruct template
                template = {
                    "alpha": metadata_full["alpha"],
                    "tau0": metadata_full["tau0"],
                    "num_echoes": metadata_full["num_echoes"],
                    "scaling": metadata_full["scaling"],
                    "decay_type": metadata_full["decay_type"],
                    "echo_times": cache_data["echo_times"],
                    "echo_amplitudes": cache_data["echo_amplitudes"],
                    "prime_gaps": cache_data["prime_gaps"],
                    "metadata": {
                        "total_duration": metadata_full["total_duration"],
                        "mean_gap": metadata_full["mean_gap"],
                        "std_gap": metadata_full["std_gap"],
                        "mean_amplitude": metadata_full["mean_amplitude"],
                        "decay_rate": metadata_full["decay_rate"]
                    }
                }

                self.stats["cache_hits"] += 1
                return template
            except (FileNotFoundError, KeyError):
                pass

        # Generate template
        template = self.generator.generate_template(
            alpha, tau0, num_echoes, scaling, decay_type
        )

        # Cache result (convert to dict with multiple arrays)
        if self.enable_cache:
            try:
                # Convert template to cacheable format (dict of arrays)
                cache_data = {
                    "echo_times": template["echo_times"],
                    "echo_amplitudes": template["echo_amplitudes"],
                    "prime_gaps": template["prime_gaps"]
                }
                self.cache.save("echo_templates", key, cache_data)

                # Also save metadata separately as JSON
                meta_key = key + "_meta"
                metadata_full = {
                    "alpha": template["alpha"],
                    "tau0": template["tau0"],
                    "num_echoes": template["num_echoes"],
                    "scaling": template["scaling"],
                    "decay_type": template["decay_type"],
                    **template["metadata"]
                }
                self.cache.save("echo_templates", meta_key, metadata_full)
            except Exception as e:
                print(f"Warning: Failed to cache template: {e}")

        self.stats["cache_misses"] += 1
        return template

    def get_multiple_templates(
        self,
        alpha_values: List[float],
        tau0_values: List[float],
        num_echoes: int = 100
    ) -> Dict[Tuple[float, float], Dict[str, Any]]:
        """Get multiple templates for parameter sweep.

        Args:
            alpha_values: List of alpha values
            tau0_values: List of tau0 values
            num_echoes: Number of echoes per template

        Returns:
            Dict mapping (alpha, tau0) -> template
        """
        templates = {}

        for alpha in alpha_values:
            for tau0 in tau0_values:
                key = (alpha, tau0)
                templates[key] = self.get_echo_template(alpha, tau0, num_echoes)

        return templates

    def _generate_key(
        self,
        alpha: float,
        tau0: float,
        num_echoes: int,
        scaling: str,
        decay_type: str
    ) -> str:
        """Generate cache key for template parameters."""
        # Round floats
        alpha_str = f"{alpha:.6f}".rstrip('0').rstrip('.')
        tau0_str = f"{tau0:.9f}".rstrip('0').rstrip('.')

        return f"echo_{alpha_str}_{tau0_str}_{num_echoes}_{scaling}_{decay_type}"

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = self.stats["cache_hits"] / total if total > 0 else 0.0

        return {
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": hit_rate
        }

    def clear_stats(self):
        """Reset performance statistics."""
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0
        }


__all__ = [
    "PrimeGapGenerator",
    "EchoTemplateGenerator",
    "CachedEchoProvider"
]
