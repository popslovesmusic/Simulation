"""DASE Cache System - Unified caching for computational artifacts.

This module provides a centralized cache manager for:
- Fractional kernel coefficients
- Laplacian stencils
- FFTW wisdom files
- Echo templates
- State profiles
- Source maps
- Mission graph results
- Surrogate ML models

Expected speedup: 50-80% for repeated missions.

Example:
    >>> from backend.cache import CacheManager
    >>> cache = CacheManager(root="./cache")
    >>>
    >>> # Save fractional kernel
    >>> import numpy as np
    >>> kernel = np.random.rand(1000)
    >>> cache.save("fractional_kernels", "kernel_1.5_0.01", kernel)
    >>>
    >>> # Load kernel
    >>> loaded = cache.load("fractional_kernels", "kernel_1.5_0.01")
"""

from .cache_manager import CacheManager, CacheBackend, CacheEntry

__all__ = ["CacheManager", "CacheBackend", "CacheEntry"]
