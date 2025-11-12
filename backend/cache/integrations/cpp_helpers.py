"""C++ engine integration helpers for FFTW wisdom caching.

This module provides Python utilities to export/import FFTW wisdom
for the C++ engine. The actual wisdom generation happens in C++,
but this module handles the caching.

C++ Integration Guide:
    See docs/implementation/CPP_CACHE_INTEGRATION.md for full details.

Python Usage:
    from backend.cache.integrations import FFTWWisdomHelper

    helper = FFTWWisdomHelper()

    # Export wisdom from C++ engine (after planning)
    helper.save_wisdom("fft_2d_512x512", wisdom_bytes)

    # Load wisdom before planning
    wisdom_bytes = helper.load_wisdom("fft_2d_512x512")
"""

import sys
from pathlib import Path
from typing import Optional
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cache import CacheManager


class FFTWWisdomHelper:
    """Helper for FFTW wisdom caching.

    FFTW wisdom contains optimized FFT plans that are expensive to compute
    (can take seconds) but extremely fast to load (milliseconds).

    Caching wisdom provides 100-1000x speedup for FFT initialization.
    """

    def __init__(self, cache_root: str = "./cache"):
        """Initialize FFTW wisdom helper.

        Args:
            cache_root: Path to cache root directory
        """
        self.cache = CacheManager(root=cache_root)

    def save_wisdom(
        self,
        key: str,
        wisdom_data: bytes,
        metadata: Optional[dict] = None
    ) -> Path:
        """Save FFTW wisdom to cache.

        Args:
            key: Unique identifier (e.g., "fft_2d_512x512")
            wisdom_data: Binary wisdom data from fftw_export_wisdom_to_string()
            metadata: Optional metadata (dimensions, planner flags, etc.)

        Returns:
            Path to cached wisdom file

        Example:
            >>> # In C++: wisdom_str = fftw_export_wisdom_to_string()
            >>> # Pass to Python: wisdom_bytes = wisdom_str.encode()
            >>> helper.save_wisdom("fft_2d_512x512", wisdom_bytes, {
            ...     "dimensions": [512, 512],
            ...     "planner": "FFTW_MEASURE"
            ... })
        """
        if not isinstance(wisdom_data, bytes):
            raise ValueError(f"wisdom_data must be bytes, got {type(wisdom_data)}")

        # Save via BinaryBackend
        backend = self.cache.backends["fftw_wisdom"]
        path = backend.save(key, wisdom_data, metadata=metadata)

        # Update cache manager metadata
        from datetime import datetime
        entry = {
            "key": key,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "size_bytes": len(wisdom_data),
            "access_count": 0
        }

        cat_metadata = self.cache.metadata.get("fftw_wisdom", {"entries": {}})
        cat_metadata["entries"][key] = entry
        self.cache._save_metadata("fftw_wisdom")

        return path

    def load_wisdom(self, key: str) -> Optional[bytes]:
        """Load FFTW wisdom from cache.

        Args:
            key: Wisdom identifier

        Returns:
            Binary wisdom data or None if not found

        Example:
            >>> wisdom_bytes = helper.load_wisdom("fft_2d_512x512")
            >>> if wisdom_bytes:
            ...     # In C++: fftw_import_wisdom_from_string(wisdom_bytes)
            ...     pass
        """
        try:
            return self.cache.load("fftw_wisdom", key)
        except (FileNotFoundError, KeyError):
            return None

    def get_wisdom_key(
        self,
        dimensions: list[int],
        transform_type: str = "fft"
    ) -> str:
        """Generate standardized wisdom key from FFT parameters.

        Args:
            dimensions: FFT dimensions (e.g., [512, 512] for 2D)
            transform_type: Type of transform ("fft", "rfft", "dct", etc.)

        Returns:
            Standardized key string

        Example:
            >>> helper.get_wisdom_key([512, 512], "fft")
            'fft_2d_512x512'
            >>> helper.get_wisdom_key([128, 128, 128], "rfft")
            'rfft_3d_128x128x128'
        """
        ndim = len(dimensions)

        if ndim == 1:
            return f"{transform_type}_1d_{dimensions[0]}"
        elif ndim == 2:
            return f"{transform_type}_2d_{dimensions[0]}x{dimensions[1]}"
        elif ndim == 3:
            return f"{transform_type}_3d_{dimensions[0]}x{dimensions[1]}x{dimensions[2]}"
        else:
            # Fallback for higher dimensions
            dims_str = "x".join(str(d) for d in dimensions)
            return f"{transform_type}_{ndim}d_{dims_str}"

    def list_wisdom(self) -> list[dict]:
        """List all cached wisdom entries with metadata.

        Returns:
            List of dicts with key, size, dimensions, etc.

        Example:
            >>> for entry in helper.list_wisdom():
            ...     print(f"{entry['key']}: {entry['size_kb']:.1f} KB")
        """
        backend = self.cache.backends["fftw_wisdom"]
        keys = backend.list_keys()

        entries = []
        for key in keys:
            # Get size
            size_bytes = backend.get_size(key)

            # Try to load metadata
            metadata = backend.load_metadata(key)

            entry = {
                "key": key,
                "size_bytes": size_bytes,
                "size_kb": size_bytes / 1024
            }

            if metadata:
                entry.update(metadata)

            entries.append(entry)

        return entries

    def export_wisdom_to_file(self, key: str, output_path: Path) -> bool:
        """Export wisdom to standalone file (for C++ loading).

        Args:
            key: Wisdom identifier
            output_path: Path to output file

        Returns:
            True if successful

        Example:
            >>> # Export for C++ engine
            >>> helper.export_wisdom_to_file(
            ...     "fft_2d_512x512",
            ...     Path("./config/fftw_wisdom.dat")
            ... )
        """
        wisdom = self.load_wisdom(key)

        if wisdom is None:
            return False

        output_path.write_bytes(wisdom)
        return True

    def import_wisdom_from_file(
        self,
        key: str,
        input_path: Path,
        metadata: Optional[dict] = None
    ) -> bool:
        """Import wisdom from standalone file into cache.

        Args:
            key: Wisdom identifier
            input_path: Path to wisdom file
            metadata: Optional metadata

        Returns:
            True if successful

        Example:
            >>> # Import wisdom generated by C++ engine
            >>> helper.import_wisdom_from_file(
            ...     "fft_2d_512x512",
            ...     Path("./fftw_wisdom_512.dat"),
            ...     {"dimensions": [512, 512]}
            ... )
        """
        if not input_path.exists():
            return False

        wisdom_data = input_path.read_bytes()
        self.save_wisdom(key, wisdom_data, metadata)
        return True


def create_cpp_integration_template():
    """Generate C++ code template for FFTW wisdom integration.

    Returns:
        C++ code as string

    This is useful for documenting how to integrate the cache
    with the C++ engine.
    """
    return """
// FFTW Wisdom Cache Integration for C++
// Add this to your dase_engine or IGSOA physics engine

#include <fftw3.h>
#include <fstream>
#include <string>

class FFTWWisdomCache {
public:
    // Load wisdom from cache before planning
    static bool load_wisdom(const std::string& cache_path) {
        std::ifstream file(cache_path, std::ios::binary);
        if (!file) return false;

        // Read wisdom data
        std::string wisdom_data(
            (std::istreambuf_iterator<char>(file)),
            std::istreambuf_iterator<char>()
        );

        // Import into FFTW
        int success = fftw_import_wisdom_from_string(wisdom_data.c_str());
        return success != 0;
    }

    // Save wisdom to cache after planning
    static bool save_wisdom(const std::string& cache_path) {
        char* wisdom_str = fftw_export_wisdom_to_string();
        if (!wisdom_str) return false;

        std::ofstream file(cache_path, std::ios::binary);
        if (!file) {
            fftw_free(wisdom_str);
            return false;
        }

        file << wisdom_str;
        fftw_free(wisdom_str);
        return true;
    }

    // Try to load wisdom, fall back to planning if not found
    static fftw_plan create_plan_with_cache(
        int n0, int n1,
        fftw_complex* in, fftw_complex* out,
        const std::string& cache_key
    ) {
        // Construct cache path
        std::string cache_path = "./cache/fftw_wisdom/" + cache_key + ".dat";

        // Try to load wisdom
        bool loaded = load_wisdom(cache_path);

        fftw_plan plan;
        if (loaded) {
            // Use FFTW_WISDOM_ONLY to avoid re-planning
            plan = fftw_plan_dft_2d(n0, n1, in, out, FFTW_FORWARD, FFTW_WISDOM_ONLY);

            if (plan) {
                return plan;  // Success!
            }
        }

        // Wisdom not found or didn't work, do full planning
        plan = fftw_plan_dft_2d(n0, n1, in, out, FFTW_FORWARD, FFTW_MEASURE);

        // Save wisdom for next time
        if (plan) {
            save_wisdom(cache_path);
        }

        return plan;
    }
};

// Example usage in DASE engine
void setup_fft_for_grid(int nx, int ny) {
    fftw_complex* data = fftw_alloc_complex(nx * ny);

    // Use cached wisdom
    std::string key = "fft_2d_" + std::to_string(nx) + "x" + std::to_string(ny);
    fftw_plan plan = FFTWWisdomCache::create_plan_with_cache(
        nx, ny, data, data, key
    );

    // Use plan...
    fftw_execute(plan);

    fftw_destroy_plan(plan);
    fftw_free(data);
}
"""


__all__ = ["FFTWWisdomHelper", "create_cpp_integration_template"]
