"""Initial-State Profile Generators for DASE/IGSOA missions.

This module provides generators for common initial field profiles:
- Gaussian profiles (wave packets)
- Soliton profiles (kink/breather solutions)
- Spherical profiles (compact support)

All profiles are cacheable via CacheManager for fast mission initialization.

Usage:
    from backend.cache.profile_generators import CachedProfileProvider

    provider = CachedProfileProvider()
    psi, phi, h = provider.get_profile(
        profile_type="gaussian",
        amplitude=1.0,
        sigma=0.5,
        grid_shape=(128, 128)
    )
"""

import sys
from pathlib import Path
import numpy as np
from typing import Tuple, Optional, Dict, Any
import hashlib

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import CacheManager


class ProfileGenerator:
    """Generates initial field profiles for DASE/IGSOA simulations."""

    @staticmethod
    def gaussian_1d(
        x: np.ndarray,
        amplitude: float = 1.0,
        center: float = 0.0,
        sigma: float = 1.0
    ) -> np.ndarray:
        """Generate 1D Gaussian profile.

        Args:
            x: Spatial grid points
            amplitude: Peak amplitude
            center: Center position
            sigma: Width parameter

        Returns:
            Gaussian field values
        """
        return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))

    @staticmethod
    def gaussian_2d(
        grid_shape: Tuple[int, int],
        amplitude: float = 1.0,
        center: Tuple[float, float] = (0.0, 0.0),
        sigma: float = 1.0,
        domain: Tuple[float, float, float, float] = (-10.0, 10.0, -10.0, 10.0)
    ) -> np.ndarray:
        """Generate 2D Gaussian profile.

        Args:
            grid_shape: (nx, ny) grid dimensions
            amplitude: Peak amplitude
            center: (cx, cy) center position
            sigma: Width parameter
            domain: (xmin, xmax, ymin, ymax) spatial domain

        Returns:
            2D Gaussian field
        """
        nx, ny = grid_shape
        xmin, xmax, ymin, ymax = domain

        x = np.linspace(xmin, xmax, nx)
        y = np.linspace(ymin, ymax, ny)
        X, Y = np.meshgrid(x, y, indexing='ij')

        cx, cy = center
        r2 = (X - cx) ** 2 + (Y - cy) ** 2

        return amplitude * np.exp(-r2 / (2 * sigma ** 2))

    @staticmethod
    def gaussian_3d(
        grid_shape: Tuple[int, int, int],
        amplitude: float = 1.0,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        sigma: float = 1.0,
        domain: Tuple[float, float, float, float, float, float] =
            (-10.0, 10.0, -10.0, 10.0, -10.0, 10.0)
    ) -> np.ndarray:
        """Generate 3D Gaussian profile.

        Args:
            grid_shape: (nx, ny, nz) grid dimensions
            amplitude: Peak amplitude
            center: (cx, cy, cz) center position
            sigma: Width parameter
            domain: (xmin, xmax, ymin, ymax, zmin, zmax) spatial domain

        Returns:
            3D Gaussian field
        """
        nx, ny, nz = grid_shape
        xmin, xmax, ymin, ymax, zmin, zmax = domain

        x = np.linspace(xmin, xmax, nx)
        y = np.linspace(ymin, ymax, ny)
        z = np.linspace(zmin, zmax, nz)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

        cx, cy, cz = center
        r2 = (X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2

        return amplitude * np.exp(-r2 / (2 * sigma ** 2))

    @staticmethod
    def soliton_1d(
        x: np.ndarray,
        amplitude: float = 1.0,
        center: float = 0.0,
        width: float = 1.0,
        velocity: float = 0.0
    ) -> np.ndarray:
        """Generate 1D kink soliton profile.

        Uses tanh profile: A * tanh((x - x0) / w)

        Args:
            x: Spatial grid points
            amplitude: Soliton amplitude
            center: Center position
            width: Characteristic width
            velocity: Soliton velocity (for moving solitons)

        Returns:
            Soliton field values
        """
        xi = (x - center) / width
        return amplitude * np.tanh(xi)

    @staticmethod
    def soliton_2d(
        grid_shape: Tuple[int, int],
        amplitude: float = 1.0,
        center: Tuple[float, float] = (0.0, 0.0),
        width: float = 1.0,
        domain: Tuple[float, float, float, float] = (-10.0, 10.0, -10.0, 10.0)
    ) -> np.ndarray:
        """Generate 2D radial soliton profile.

        Uses sech^2 profile: A * sech^2(r / w)

        Args:
            grid_shape: (nx, ny) grid dimensions
            amplitude: Soliton amplitude
            center: (cx, cy) center position
            width: Characteristic width
            domain: (xmin, xmax, ymin, ymax) spatial domain

        Returns:
            2D soliton field
        """
        nx, ny = grid_shape
        xmin, xmax, ymin, ymax = domain

        x = np.linspace(xmin, xmax, nx)
        y = np.linspace(ymin, ymax, ny)
        X, Y = np.meshgrid(x, y, indexing='ij')

        cx, cy = center
        r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)

        return amplitude / np.cosh(r / width) ** 2

    @staticmethod
    def spherical_shell(
        grid_shape: Tuple[int, int, int],
        amplitude: float = 1.0,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        inner_radius: float = 1.0,
        thickness: float = 0.5,
        domain: Tuple[float, float, float, float, float, float] =
            (-10.0, 10.0, -10.0, 10.0, -10.0, 10.0)
    ) -> np.ndarray:
        """Generate 3D spherical shell profile.

        Args:
            grid_shape: (nx, ny, nz) grid dimensions
            amplitude: Shell amplitude
            center: (cx, cy, cz) center position
            inner_radius: Inner shell radius
            thickness: Shell thickness
            domain: (xmin, xmax, ymin, ymax, zmin, zmax) spatial domain

        Returns:
            3D spherical shell field
        """
        nx, ny, nz = grid_shape
        xmin, xmax, ymin, ymax, zmin, zmax = domain

        x = np.linspace(xmin, xmax, nx)
        y = np.linspace(ymin, ymax, ny)
        z = np.linspace(zmin, zmax, nz)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

        cx, cy, cz = center
        r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2)

        # Shell profile: smooth transition using tanh
        outer_radius = inner_radius + thickness
        profile = np.zeros_like(r)

        # Inner edge (rise)
        inner_transition = 0.1 * thickness
        profile += 0.5 * (1 + np.tanh((r - inner_radius) / inner_transition))

        # Outer edge (fall)
        outer_transition = 0.1 * thickness
        profile *= 0.5 * (1 - np.tanh((r - outer_radius) / outer_transition))

        return amplitude * profile

    @staticmethod
    def compact_support(
        grid_shape: Tuple[int, ...],
        amplitude: float = 1.0,
        center: Tuple[float, ...] = None,
        radius: float = 1.0,
        domain: Tuple[float, ...] = None,
        smoothing: float = 0.1
    ) -> np.ndarray:
        """Generate profile with compact support (zero outside radius).

        Args:
            grid_shape: Grid dimensions (1D, 2D, or 3D)
            amplitude: Field amplitude inside support
            center: Center position
            radius: Support radius
            domain: Spatial domain bounds
            smoothing: Edge smoothing width (as fraction of radius)

        Returns:
            Field with compact support
        """
        ndim = len(grid_shape)

        if center is None:
            center = tuple(0.0 for _ in range(ndim))

        if domain is None:
            domain = tuple(val for _ in range(ndim) for val in (-10.0, 10.0))

        # Create coordinate grids
        grids = []
        for i in range(ndim):
            n = grid_shape[i]
            xmin, xmax = domain[2 * i], domain[2 * i + 1]
            grids.append(np.linspace(xmin, xmax, n))

        coords = np.meshgrid(*grids, indexing='ij')

        # Calculate distance from center
        r2 = sum((coord - c) ** 2 for coord, c in zip(coords, center))
        r = np.sqrt(r2)

        # Smooth cutoff using tanh
        transition_width = smoothing * radius
        profile = amplitude * 0.5 * (1 - np.tanh((r - radius) / transition_width))

        return profile


class CachedProfileProvider:
    """Provides initial field profiles with automatic caching.

    Example:
        >>> provider = CachedProfileProvider()
        >>>
        >>> # Get 2D Gaussian profile (automatically cached)
        >>> profile = provider.get_profile(
        ...     profile_type="gaussian",
        ...     grid_shape=(128, 128),
        ...     amplitude=1.0,
        ...     sigma=0.5
        ... )
        >>>
        >>> # Get IGSOA field triplet (ψ, φ, h)
        >>> psi, phi, h = provider.get_field_triplet(
        ...     profile_type="soliton",
        ...     grid_shape=(64, 64, 64),
        ...     amplitude=2.0
        ... )
    """

    def __init__(self, cache_root: str = "./cache", enable_cache: bool = True):
        """Initialize profile provider.

        Args:
            cache_root: Path to cache root directory
            enable_cache: If False, always recompute
        """
        self.enable_cache = enable_cache
        self.generator = ProfileGenerator()

        if enable_cache:
            self.cache = CacheManager(root=cache_root)
        else:
            self.cache = None

        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0
        }

    def get_profile(
        self,
        profile_type: str,
        grid_shape: Tuple[int, ...],
        amplitude: float = 1.0,
        sigma: Optional[float] = None,
        center: Optional[Tuple[float, ...]] = None,
        domain: Optional[Tuple[float, ...]] = None,
        **kwargs
    ) -> np.ndarray:
        """Get field profile (cached if available).

        Args:
            profile_type: "gaussian", "soliton", "spherical", or "compact"
            grid_shape: Grid dimensions
            amplitude: Field amplitude
            sigma: Width parameter (for Gaussian)
            center: Center position
            domain: Spatial domain bounds
            **kwargs: Additional profile-specific parameters

        Returns:
            Field profile array
        """
        # Generate cache key
        key = self._generate_key(
            profile_type, grid_shape, amplitude, sigma, center, domain, **kwargs
        )

        # Try to load from cache
        if self.enable_cache:
            try:
                profile = self.cache.load("state_profiles", key)
                self.stats["cache_hits"] += 1
                return profile
            except (FileNotFoundError, KeyError):
                pass

        # Compute profile
        ndim = len(grid_shape)

        if profile_type == "gaussian":
            if ndim == 1:
                x = np.linspace(-10, 10, grid_shape[0]) if domain is None else \
                    np.linspace(domain[0], domain[1], grid_shape[0])
                profile = self.generator.gaussian_1d(
                    x, amplitude, center[0] if center else 0.0,
                    sigma if sigma else 1.0
                )
            elif ndim == 2:
                profile = self.generator.gaussian_2d(
                    grid_shape, amplitude,
                    center if center else (0.0, 0.0),
                    sigma if sigma else 1.0,
                    domain if domain else (-10, 10, -10, 10)
                )
            elif ndim == 3:
                profile = self.generator.gaussian_3d(
                    grid_shape, amplitude,
                    center if center else (0.0, 0.0, 0.0),
                    sigma if sigma else 1.0,
                    domain if domain else (-10, 10, -10, 10, -10, 10)
                )
            else:
                raise ValueError(f"Gaussian not supported for {ndim}D")

        elif profile_type == "soliton":
            if ndim == 1:
                x = np.linspace(-10, 10, grid_shape[0]) if domain is None else \
                    np.linspace(domain[0], domain[1], grid_shape[0])
                profile = self.generator.soliton_1d(
                    x, amplitude, center[0] if center else 0.0,
                    kwargs.get('width', 1.0), kwargs.get('velocity', 0.0)
                )
            elif ndim == 2:
                profile = self.generator.soliton_2d(
                    grid_shape, amplitude,
                    center if center else (0.0, 0.0),
                    kwargs.get('width', 1.0),
                    domain if domain else (-10, 10, -10, 10)
                )
            else:
                raise ValueError(f"Soliton not supported for {ndim}D")

        elif profile_type == "spherical":
            if ndim != 3:
                raise ValueError("Spherical shell requires 3D grid")
            profile = self.generator.spherical_shell(
                grid_shape, amplitude,
                center if center else (0.0, 0.0, 0.0),
                kwargs.get('inner_radius', 1.0),
                kwargs.get('thickness', 0.5),
                domain if domain else (-10, 10, -10, 10, -10, 10)
            )

        elif profile_type == "compact":
            profile = self.generator.compact_support(
                grid_shape, amplitude, center, kwargs.get('radius', 1.0),
                domain, kwargs.get('smoothing', 0.1)
            )

        else:
            raise ValueError(f"Unknown profile type: {profile_type}")

        # Cache result
        if self.enable_cache:
            self.cache.save("state_profiles", key, profile)

        self.stats["cache_misses"] += 1
        return profile

    def get_field_triplet(
        self,
        profile_type: str,
        grid_shape: Tuple[int, ...],
        amplitude: float = 1.0,
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get IGSOA field triplet (ψ, φ, h).

        Args:
            profile_type: Profile type
            grid_shape: Grid dimensions
            amplitude: Base amplitude
            **kwargs: Profile parameters

        Returns:
            (psi, phi, h) field arrays
        """
        # Generate primary field (ψ)
        psi = self.get_profile(profile_type, grid_shape, amplitude, **kwargs)

        # Generate conjugate field (φ) - typically same shape, can be zero or derived
        phi = self.get_profile(profile_type, grid_shape, amplitude * 0.5, **kwargs)

        # Generate metric perturbation (h) - typically smaller amplitude
        h = self.get_profile(profile_type, grid_shape, amplitude * 0.1, **kwargs)

        return psi, phi, h

    def _generate_key(
        self,
        profile_type: str,
        grid_shape: Tuple[int, ...],
        amplitude: float,
        sigma: Optional[float],
        center: Optional[Tuple[float, ...]],
        domain: Optional[Tuple[float, ...]],
        **kwargs
    ) -> str:
        """Generate cache key for profile parameters."""
        # Round floats to avoid precision issues
        amp_str = f"{amplitude:.6f}".rstrip('0').rstrip('.')
        sigma_str = f"{sigma:.6f}".rstrip('0').rstrip('.') if sigma else "none"

        grid_str = "x".join(str(n) for n in grid_shape)

        # Hash additional kwargs for compact key
        kwargs_str = str(sorted(kwargs.items()))
        kwargs_hash = hashlib.md5(kwargs_str.encode()).hexdigest()[:8]

        return f"state_{profile_type}_{amp_str}_{sigma_str}_{grid_str}_{kwargs_hash}"

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = self.stats["cache_hits"] / total if total > 0 else 0.0

        return {
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": hit_rate
        }


__all__ = ["ProfileGenerator", "CachedProfileProvider"]
