"""Source map and coupling zone cache for SATP multi-zone simulations.

This module generates spatial masks for multi-zone source configurations,
used in SATP (Spatially Asynchronous Temporal Processing) simulations.

Features:
- Multi-zone circular/rectangular masks
- Smooth transitions between zones
- Coupling strength maps
- Automatic caching

Usage:
    from backend.cache.source_maps import CachedSourceMapProvider

    provider = CachedSourceMapProvider()
    source_map = provider.get_source_map({
        "zones": [
            {"type": "circle", "center": [0, 0], "radius": 2.0, "amplitude": 1.0},
            {"type": "circle", "center": [5, 0], "radius": 1.5, "amplitude": 0.5}
        ],
        "grid_shape": [128, 128],
        "domain": [-10, 10, -10, 10]
    })
"""

import sys
from pathlib import Path
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import hashlib
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import CacheManager


class SourceMapGenerator:
    """Generate spatial source maps for multi-zone simulations."""

    @staticmethod
    def circular_zone(
        grid_shape: Tuple[int, ...],
        center: Tuple[float, ...],
        radius: float,
        amplitude: float = 1.0,
        domain: Tuple[float, ...] = None,
        smoothing: float = 0.1
    ) -> np.ndarray:
        """Generate circular zone mask.

        Args:
            grid_shape: Grid dimensions (2D or 3D)
            center: Zone center position
            radius: Zone radius
            amplitude: Source amplitude in zone
            domain: Spatial domain bounds
            smoothing: Edge smoothing width (as fraction of radius)

        Returns:
            Spatial mask array
        """
        ndim = len(grid_shape)

        if domain is None:
            domain = tuple(val for _ in range(ndim) for val in (-10.0, 10.0))

        # Create coordinate grids
        grids = []
        for i in range(ndim):
            n = grid_shape[i]
            xmin, xmax = domain[2*i], domain[2*i + 1]
            grids.append(np.linspace(xmin, xmax, n))

        coords = np.meshgrid(*grids, indexing='ij')

        # Calculate distance from center
        r2 = sum((coord - c)**2 for coord, c in zip(coords, center))
        r = np.sqrt(r2)

        # Smooth cutoff using tanh
        transition_width = smoothing * radius
        mask = amplitude * 0.5 * (1 - np.tanh((r - radius) / transition_width))

        return mask

    @staticmethod
    def rectangular_zone(
        grid_shape: Tuple[int, int],
        center: Tuple[float, float],
        width: float,
        height: float,
        amplitude: float = 1.0,
        domain: Tuple[float, float, float, float] = (-10, 10, -10, 10),
        smoothing: float = 0.1
    ) -> np.ndarray:
        """Generate rectangular zone mask.

        Args:
            grid_shape: Grid dimensions (2D only)
            center: Zone center (cx, cy)
            width: Zone width
            height: Zone height
            amplitude: Source amplitude
            domain: Spatial domain (xmin, xmax, ymin, ymax)
            smoothing: Edge smoothing width

        Returns:
            2D spatial mask
        """
        nx, ny = grid_shape
        xmin, xmax, ymin, ymax = domain

        x = np.linspace(xmin, xmax, nx)
        y = np.linspace(ymin, ymax, ny)
        X, Y = np.meshgrid(x, y, indexing='ij')

        cx, cy = center

        # Distance from edges
        dx = np.abs(X - cx) - width/2
        dy = np.abs(Y - cy) - height/2

        # Smooth transitions
        trans_w = smoothing * width
        trans_h = smoothing * height

        mask_x = 0.5 * (1 - np.tanh(dx / trans_w))
        mask_y = 0.5 * (1 - np.tanh(dy / trans_h))

        mask = amplitude * mask_x * mask_y

        return mask

    @staticmethod
    def gaussian_zone(
        grid_shape: Tuple[int, ...],
        center: Tuple[float, ...],
        sigma: float,
        amplitude: float = 1.0,
        domain: Tuple[float, ...] = None
    ) -> np.ndarray:
        """Generate Gaussian zone mask.

        Args:
            grid_shape: Grid dimensions
            center: Zone center
            sigma: Gaussian width
            amplitude: Peak amplitude
            domain: Spatial domain

        Returns:
            Spatial mask array
        """
        ndim = len(grid_shape)

        if domain is None:
            domain = tuple(val for _ in range(ndim) for val in (-10.0, 10.0))

        # Create coordinate grids
        grids = []
        for i in range(ndim):
            n = grid_shape[i]
            xmin, xmax = domain[2*i], domain[2*i + 1]
            grids.append(np.linspace(xmin, xmax, n))

        coords = np.meshgrid(*grids, indexing='ij')

        # Calculate distance from center
        r2 = sum((coord - c)**2 for coord, c in zip(coords, center))

        # Gaussian profile
        mask = amplitude * np.exp(-r2 / (2 * sigma**2))

        return mask

    @staticmethod
    def combine_zones(
        zones: List[np.ndarray],
        mode: str = "add"
    ) -> np.ndarray:
        """Combine multiple zone masks.

        Args:
            zones: List of zone mask arrays
            mode: Combination mode ("add", "max", "multiply")

        Returns:
            Combined mask
        """
        if not zones:
            raise ValueError("No zones provided")

        if mode == "add":
            return np.sum(zones, axis=0)
        elif mode == "max":
            return np.maximum.reduce(zones)
        elif mode == "multiply":
            result = zones[0].copy()
            for zone in zones[1:]:
                result *= zone
            return result
        else:
            raise ValueError(f"Unknown combination mode: {mode}")

    @staticmethod
    def generate_coupling_map(
        source_map: np.ndarray,
        coupling_strength: float = 1.0,
        coupling_type: str = "linear"
    ) -> np.ndarray:
        """Generate coupling strength map from source map.

        Args:
            source_map: Source spatial distribution
            coupling_strength: Global coupling strength
            coupling_type: "linear", "quadratic", or "threshold"

        Returns:
            Coupling strength map
        """
        if coupling_type == "linear":
            return coupling_strength * source_map

        elif coupling_type == "quadratic":
            return coupling_strength * source_map**2

        elif coupling_type == "threshold":
            threshold = 0.5 * np.max(source_map)
            return coupling_strength * (source_map > threshold).astype(float)

        else:
            raise ValueError(f"Unknown coupling type: {coupling_type}")


class CachedSourceMapProvider:
    """Provides source maps with automatic caching.

    Example:
        >>> provider = CachedSourceMapProvider()
        >>>
        >>> # Define multi-zone layout
        >>> layout = {
        ...     "zones": [
        ...         {"type": "circle", "center": [0, 0], "radius": 2.0, "amplitude": 1.0},
        ...         {"type": "circle", "center": [5, 0], "radius": 1.5, "amplitude": 0.5}
        ...     ],
        ...     "grid_shape": [128, 128],
        ...     "domain": [-10, 10, -10, 10],
        ...     "combine_mode": "add"
        ... }
        >>>
        >>> # Get source map (automatically cached)
        >>> source_map = provider.get_source_map(layout)
        >>>
        >>> # Get coupling map
        >>> coupling_map = provider.get_coupling_map(layout, coupling_strength=0.8)
    """

    def __init__(self, cache_root: str = "./cache", enable_cache: bool = True):
        """Initialize source map provider.

        Args:
            cache_root: Path to cache root directory
            enable_cache: If False, always recompute
        """
        self.enable_cache = enable_cache
        self.generator = SourceMapGenerator()

        if enable_cache:
            self.cache = CacheManager(root=cache_root)
        else:
            self.cache = None

        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0
        }

    def get_source_map(
        self,
        layout: Dict[str, Any],
        force_recompute: bool = False
    ) -> np.ndarray:
        """Get source map for given layout (cached if available).

        Args:
            layout: Zone layout specification
            force_recompute: If True, bypass cache

        Returns:
            Source map array

        Layout format:
            {
                "zones": [
                    {
                        "type": "circle" | "rectangle" | "gaussian",
                        "center": [x, y] or [x, y, z],
                        "radius": float (circle),
                        "width": float, "height": float (rectangle),
                        "sigma": float (gaussian),
                        "amplitude": float
                    },
                    ...
                ],
                "grid_shape": [nx, ny] or [nx, ny, nz],
                "domain": [xmin, xmax, ymin, ymax, ...],
                "combine_mode": "add" | "max" | "multiply"
            }
        """
        # Generate cache key
        key = self._generate_key(layout)

        # Try to load from cache
        if self.enable_cache and not force_recompute:
            try:
                source_map = self.cache.load("source_maps", key)
                self.stats["cache_hits"] += 1
                return source_map
            except (FileNotFoundError, KeyError):
                pass

        # Generate source map
        grid_shape = tuple(layout["grid_shape"])
        domain = tuple(layout.get("domain", []))
        combine_mode = layout.get("combine_mode", "add")

        # Generate individual zones
        zones = []
        for zone_spec in layout["zones"]:
            zone_type = zone_spec["type"]
            center = tuple(zone_spec["center"])
            amplitude = zone_spec.get("amplitude", 1.0)
            smoothing = zone_spec.get("smoothing", 0.1)

            if zone_type == "circle":
                radius = zone_spec["radius"]
                zone = self.generator.circular_zone(
                    grid_shape, center, radius, amplitude,
                    domain if domain else None, smoothing
                )

            elif zone_type == "rectangle":
                width = zone_spec["width"]
                height = zone_spec["height"]
                zone = self.generator.rectangular_zone(
                    grid_shape, center, width, height, amplitude,
                    domain if domain else (-10, 10, -10, 10), smoothing
                )

            elif zone_type == "gaussian":
                sigma = zone_spec["sigma"]
                zone = self.generator.gaussian_zone(
                    grid_shape, center, sigma, amplitude,
                    domain if domain else None
                )

            else:
                raise ValueError(f"Unknown zone type: {zone_type}")

            zones.append(zone)

        # Combine zones
        source_map = self.generator.combine_zones(zones, combine_mode)

        # Cache result
        if self.enable_cache:
            try:
                self.cache.save("source_maps", key, source_map)
            except Exception as e:
                print(f"Warning: Failed to cache source map: {e}")

        self.stats["cache_misses"] += 1
        return source_map

    def get_coupling_map(
        self,
        layout: Dict[str, Any],
        coupling_strength: float = 1.0,
        coupling_type: str = "linear"
    ) -> np.ndarray:
        """Get coupling strength map for given layout.

        Args:
            layout: Zone layout specification
            coupling_strength: Global coupling strength
            coupling_type: Coupling model

        Returns:
            Coupling map array
        """
        # Get source map (cached)
        source_map = self.get_source_map(layout)

        # Generate coupling map
        coupling_map = self.generator.generate_coupling_map(
            source_map, coupling_strength, coupling_type
        )

        return coupling_map

    def _generate_key(self, layout: Dict[str, Any]) -> str:
        """Generate cache key from layout specification."""
        # Create deterministic JSON representation
        layout_json = json.dumps(layout, sort_keys=True)

        # Hash for compact key
        layout_hash = hashlib.md5(layout_json.encode()).hexdigest()

        # Include grid shape for human readability
        grid_str = "x".join(str(n) for n in layout["grid_shape"])

        return f"source_map_{grid_str}_{layout_hash[:12]}"

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = self.stats["cache_hits"] / total if total > 0 else 0.0

        return {
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": hit_rate
        }


__all__ = ["SourceMapGenerator", "CachedSourceMapProvider"]
