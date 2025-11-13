"""Tests for initial-state profile generators.

Run with: python backend/cache/test_profiles.py
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache.profile_generators import CachedProfileProvider, ProfileGenerator


def test_gaussian_profiles():
    """Test Gaussian profile generation in 1D, 2D, 3D."""
    print("\n" + "=" * 60)
    print("TEST: Gaussian Profiles")
    print("=" * 60)

    provider = CachedProfileProvider()

    # 1D Gaussian
    print("\n1D Gaussian:")
    psi_1d = provider.get_profile("gaussian", (256,), amplitude=1.0, sigma=1.0)
    print(f"  Shape: {psi_1d.shape}")
    print(f"  Max value: {np.max(psi_1d):.4f} (expected: 1.0)")
    print(f"  Min value: {np.min(psi_1d):.4f}")
    assert np.isclose(np.max(psi_1d), 1.0, rtol=0.01), "Peak should be 1.0"

    # 2D Gaussian
    print("\n2D Gaussian:")
    psi_2d = provider.get_profile("gaussian", (128, 128), amplitude=2.0, sigma=0.5)
    print(f"  Shape: {psi_2d.shape}")
    print(f"  Max value: {np.max(psi_2d):.4f} (expected: ~2.0)")
    assert np.max(psi_2d) > 1.9, "Peak should be close to 2.0"

    # 3D Gaussian
    print("\n3D Gaussian:")
    psi_3d = provider.get_profile("gaussian", (64, 64, 64), amplitude=1.5, sigma=1.5)
    print(f"  Shape: {psi_3d.shape}")
    print(f"  Max value: {np.max(psi_3d):.4f} (expected: ~1.5)")
    assert np.max(psi_3d) > 1.4, "Peak should be close to 1.5"

    print("\n[OK] Gaussian profiles working correctly")
    return True


def test_soliton_profiles():
    """Test soliton profile generation."""
    print("\n" + "=" * 60)
    print("TEST: Soliton Profiles")
    print("=" * 60)

    provider = CachedProfileProvider()

    # 1D Soliton (kink)
    print("\n1D Soliton (kink):")
    psi_1d = provider.get_profile("soliton", (256,), amplitude=1.0, width=1.0)
    print(f"  Shape: {psi_1d.shape}")
    print(f"  Max value: {np.max(psi_1d):.4f}")
    print(f"  Min value: {np.min(psi_1d):.4f}")
    assert np.max(psi_1d) > 0.9, "Should reach ~1.0"
    assert np.min(psi_1d) < -0.9, "Should reach ~-1.0"

    # 2D Soliton (radial)
    print("\n2D Soliton (radial):")
    psi_2d = provider.get_profile("soliton", (128, 128), amplitude=1.0, width=1.0)
    print(f"  Shape: {psi_2d.shape}")
    print(f"  Max value: {np.max(psi_2d):.4f}")
    assert np.max(psi_2d) > 0.95, "Peak should be close to 1.0"

    print("\n[OK] Soliton profiles working correctly")
    return True


def test_spherical_profiles():
    """Test spherical shell profiles."""
    print("\n" + "=" * 60)
    print("TEST: Spherical Shell Profiles")
    print("=" * 60)

    provider = CachedProfileProvider()

    # 3D Spherical shell
    print("\n3D Spherical shell:")
    psi_3d = provider.get_profile(
        "spherical",
        (64, 64, 64),
        amplitude=1.0,
        inner_radius=2.0,
        thickness=1.0
    )
    print(f"  Shape: {psi_3d.shape}")
    print(f"  Max value: {np.max(psi_3d):.4f}")
    print(f"  Center value: {psi_3d[32, 32, 32]:.4f} (should be ~0, inside shell)")
    assert psi_3d[32, 32, 32] < 0.1, "Center should be near zero (inside shell)"

    print("\n[OK] Spherical profiles working correctly")
    return True


def test_compact_support():
    """Test compact support profiles."""
    print("\n" + "=" * 60)
    print("TEST: Compact Support Profiles")
    print("=" * 60)

    provider = CachedProfileProvider()

    # 2D Compact support
    print("\n2D Compact support:")
    psi_2d = provider.get_profile(
        "compact",
        (128, 128),
        amplitude=1.0,
        radius=3.0,
        smoothing=0.1
    )
    print(f"  Shape: {psi_2d.shape}")
    print(f"  Max value: {np.max(psi_2d):.4f}")
    print(f"  Corner value: {psi_2d[0, 0]:.6f} (should be ~0, outside support)")
    assert psi_2d[0, 0] < 0.01, "Far corners should be near zero"

    print("\n[OK] Compact support profiles working correctly")
    return True


def test_field_triplet():
    """Test IGSOA field triplet generation."""
    print("\n" + "=" * 60)
    print("TEST: Field Triplet (psi, phi, h)")
    print("=" * 60)

    provider = CachedProfileProvider()

    psi, phi, h = provider.get_field_triplet(
        "gaussian",
        (64, 64, 64),
        amplitude=1.0,
        sigma=1.0
    )

    print(f"\npsi field:")
    print(f"  Shape: {psi.shape}")
    print(f"  Max: {np.max(psi):.4f}")

    print(f"\nphi field:")
    print(f"  Shape: {phi.shape}")
    print(f"  Max: {np.max(phi):.4f}")

    print(f"\nh field:")
    print(f"  Shape: {h.shape}")
    print(f"  Max: {np.max(h):.4f}")

    assert psi.shape == phi.shape == h.shape, "All fields should have same shape"
    assert np.max(psi) > np.max(phi) > np.max(h), "Amplitudes should be decreasing"

    print("\n[OK] Field triplet generation working correctly")
    return True


def test_caching():
    """Test profile caching functionality."""
    print("\n" + "=" * 60)
    print("TEST: Profile Caching")
    print("=" * 60)

    # Create a fresh provider with test cache directory
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    provider = CachedProfileProvider(cache_root=temp_dir)

    # Use a unique configuration not tested before
    # First call: cache miss
    print("\nFirst call (cache miss):")
    psi1 = provider.get_profile("gaussian", (100, 100), amplitude=3.14, sigma=2.5)
    stats1 = provider.get_stats()
    print(f"  Cache hits: {stats1['cache_hits']}")
    print(f"  Cache misses: {stats1['cache_misses']}")
    assert stats1['cache_misses'] >= 1, "Should have at least 1 miss"

    # Second call: cache hit (same parameters)
    print("\nSecond call (cache hit):")
    psi2 = provider.get_profile("gaussian", (100, 100), amplitude=3.14, sigma=2.5)
    stats2 = provider.get_stats()
    print(f"  Cache hits: {stats2['cache_hits']}")
    print(f"  Cache misses: {stats2['cache_misses']}")
    assert stats2['cache_hits'] > stats1['cache_hits'], "Should have cache hit"

    # Verify identical
    assert np.array_equal(psi1, psi2), "Cached profile should be identical"

    print(f"\nFinal hit rate: {stats2['hit_rate'] * 100:.1f}%")
    print("\n[OK] Caching working correctly")

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    return True


def test_visualization():
    """Generate visualization of profiles (saved to file)."""
    print("\n" + "=" * 60)
    print("TEST: Profile Visualization")
    print("=" * 60)

    provider = CachedProfileProvider()

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # 1D Gaussian
    x = np.linspace(-10, 10, 256)
    psi_1d = provider.get_profile("gaussian", (256,), amplitude=1.0, sigma=1.0, center=(0.0,), domain=(-10.0, 10.0))
    axes[0, 0].plot(x, psi_1d)
    axes[0, 0].set_title("1D Gaussian")
    axes[0, 0].set_xlabel("x")
    axes[0, 0].set_ylabel("psi")
    axes[0, 0].grid(True)

    # 2D Gaussian
    psi_2d = provider.get_profile("gaussian", (128, 128), amplitude=1.0, sigma=1.0)
    im = axes[0, 1].imshow(psi_2d, extent=[-10, 10, -10, 10], origin='lower', cmap='viridis')
    axes[0, 1].set_title("2D Gaussian")
    axes[0, 1].set_xlabel("x")
    axes[0, 1].set_ylabel("y")
    plt.colorbar(im, ax=axes[0, 1])

    # 2D Soliton
    psi_sol = provider.get_profile("soliton", (128, 128), amplitude=1.0, width=1.0)
    im = axes[0, 2].imshow(psi_sol, extent=[-10, 10, -10, 10], origin='lower', cmap='viridis')
    axes[0, 2].set_title("2D Soliton")
    axes[0, 2].set_xlabel("x")
    axes[0, 2].set_ylabel("y")
    plt.colorbar(im, ax=axes[0, 2])

    # 1D Soliton (kink)
    psi_kink = provider.get_profile("soliton", (256,), amplitude=1.0, width=1.0, center=(0.0,), domain=(-10.0, 10.0))
    axes[1, 0].plot(x, psi_kink)
    axes[1, 0].set_title("1D Soliton (kink)")
    axes[1, 0].set_xlabel("x")
    axes[1, 0].set_ylabel("psi")
    axes[1, 0].grid(True)

    # 2D Compact support
    psi_compact = provider.get_profile("compact", (128, 128), amplitude=1.0, radius=3.0)
    im = axes[1, 1].imshow(psi_compact, extent=[-10, 10, -10, 10], origin='lower', cmap='viridis')
    axes[1, 1].set_title("2D Compact Support")
    axes[1, 1].set_xlabel("x")
    axes[1, 1].set_ylabel("y")
    plt.colorbar(im, ax=axes[1, 1])

    # 3D Spherical shell (central slice)
    psi_sphere = provider.get_profile("spherical", (64, 64, 64), amplitude=1.0, inner_radius=2.0, thickness=1.0)
    im = axes[1, 2].imshow(psi_sphere[:, :, 32], extent=[-10, 10, -10, 10], origin='lower', cmap='viridis')
    axes[1, 2].set_title("3D Spherical Shell (z=0 slice)")
    axes[1, 2].set_xlabel("x")
    axes[1, 2].set_ylabel("y")
    plt.colorbar(im, ax=axes[1, 2])

    plt.tight_layout()

    output_path = Path("cache/profile_visualization.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    print(f"\n[OK] Visualization saved to: {output_path}")

    plt.close()
    return True


def main():
    """Run all profile tests."""
    print("=" * 60)
    print("INITIAL-STATE PROFILE GENERATORS - TEST SUITE")
    print("=" * 60)

    tests = [
        ("Gaussian Profiles", test_gaussian_profiles),
        ("Soliton Profiles", test_soliton_profiles),
        ("Spherical Profiles", test_spherical_profiles),
        ("Compact Support", test_compact_support),
        ("Field Triplet", test_field_triplet),
        ("Caching", test_caching),
        ("Visualization", test_visualization),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n[OK] ALL TESTS PASSED")
        return 0
    else:
        print(f"\n[FAIL] {failed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
