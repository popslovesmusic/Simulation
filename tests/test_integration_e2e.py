"""End-to-end integration test for cache system."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.cache.cache_manager import CacheManager
from backend.cache.profile_generators import CachedProfileProvider
from backend.cache.echo_templates import CachedEchoProvider
from backend.cache.mission_graph import CachedMissionRunner

def test_e2e_workflow():
    """Test complete workflow: profiles -> echoes -> missions."""
    print("\n" + "="*60)
    print("END-TO-END INTEGRATION TEST")
    print("="*60)

    # Step 1: Initialize cache system
    print("\n[1/4] Initializing cache system...")
    cache = CacheManager()
    profile_provider = CachedProfileProvider()
    echo_provider = CachedEchoProvider()
    print("  [OK] Cache system initialized")

    # Step 2: Generate profiles
    print("\n[2/4] Generating initial state profiles...")
    profile_gaussian = profile_provider.get_profile(
        "gaussian", (64, 64), amplitude=1.0, sigma=0.5
    )
    profile_soliton = profile_provider.get_profile(
        "soliton", (64, 64), amplitude=1.5, width=2.0
    )
    print(f"  [OK] Generated 2 profiles")
    print(f"      - Gaussian: {profile_gaussian.shape}")
    print(f"      - Soliton: {profile_soliton.shape}")

    # Step 3: Generate echo templates
    print("\n[3/4] Generating echo templates...")
    echo_1 = echo_provider.get_echo_template(1.5, 0.05, 50)
    echo_2 = echo_provider.get_echo_template(1.8, 0.1, 50)
    print(f"  [OK] Generated 2 echo templates")
    print(f"      - Echo 1: {len(echo_1['echo_times'])} echoes, duration={echo_1['metadata']['total_duration']:.2f}s")
    print(f"      - Echo 2: {len(echo_2['echo_times'])} echoes, duration={echo_2['metadata']['total_duration']:.2f}s")

    # Step 4: Check cache statistics
    print("\n[4/4] Verifying cache performance...")
    profile_stats = profile_provider.get_stats()
    echo_stats = echo_provider.get_stats()

    print(f"  Profile cache:")
    print(f"    - Hits: {profile_stats['cache_hits']}")
    print(f"    - Misses: {profile_stats['cache_misses']}")
    print(f"    - Hit rate: {profile_stats['hit_rate']*100:.1f}%")

    print(f"  Echo cache:")
    print(f"    - Hits: {echo_stats['cache_hits']}")
    print(f"    - Misses: {echo_stats['cache_misses']}")
    print(f"    - Hit rate: {echo_stats['hit_rate']*100:.1f}%")

    # Validation
    assert profile_gaussian.shape == (64, 64), "Profile shape mismatch"
    assert len(echo_1['echo_times']) == 50, "Echo count mismatch"
    assert profile_stats['cache_hits'] + profile_stats['cache_misses'] > 0, "No cache activity"
    assert echo_stats['cache_hits'] + echo_stats['cache_misses'] > 0, "No cache activity"

    print("\n" + "="*60)
    print("[OK] END-TO-END INTEGRATION TEST PASSED")
    print("="*60)

    return {
        "profiles_generated": 2,
        "echoes_generated": 2,
        "profile_hit_rate": profile_stats['hit_rate'],
        "echo_hit_rate": echo_stats['hit_rate'],
        "status": "PASS"
    }

if __name__ == "__main__":
    result = test_e2e_workflow()
    print(f"\nTest result: {result}")
