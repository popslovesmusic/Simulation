"""Quick test for Prime-Gap Echo Templates.

Run with: python backend/cache/test_echo_templates.py
"""

import sys
from pathlib import Path
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache.echo_templates import PrimeGapGenerator, EchoTemplateGenerator, CachedEchoProvider


def test_prime_generation():
    """Test prime number generation."""
    print("\n" + "=" * 60)
    print("TEST: Prime Number Generation")
    print("=" * 60)

    # First 10 primes: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29
    primes = PrimeGapGenerator.sieve_of_eratosthenes(30)
    expected = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

    print(f"\nFirst 10 primes: {primes[:10]}")
    print(f"Expected:        {expected}")

    assert len(primes) == 10, f"Should find 10 primes, found {len(primes)}"
    assert np.array_equal(primes, expected), "Primes don't match expected"

    print("\n[OK] Prime generation working correctly")
    return True


def test_prime_gaps():
    """Test prime gap computation."""
    print("\n" + "=" * 60)
    print("TEST: Prime Gap Computation")
    print("=" * 60)

    # First 10 gaps: 1, 2, 2, 4, 2, 4, 2, 4, 6, ...
    gaps = PrimeGapGenerator.get_prime_gaps(10)
    expected = [1, 2, 2, 4, 2, 4, 2, 4, 6, 2]

    print(f"\nFirst 10 gaps: {gaps}")
    print(f"Expected:      {expected}")

    assert len(gaps) == 10, f"Should have 10 gaps, got {len(gaps)}"
    assert np.array_equal(gaps, expected), "Gaps don't match expected"

    print("\n[OK] Prime gaps working correctly")
    return True


def test_echo_timing():
    """Test echo timing generation."""
    print("\n" + "=" * 60)
    print("TEST: Echo Timing Generation")
    print("=" * 60)

    times = EchoTemplateGenerator.generate_echo_timings(
        tau0=0.1,
        num_echoes=50,
        alpha=1.8,
        scaling="linear"
    )

    print(f"\nGenerated {len(times)} echo times")
    print(f"  First 5: {times[:5]}")
    print(f"  Last 5:  {times[-5:]}")
    print(f"  Duration: {times[-1]:.3f}s")

    assert len(times) == 50, "Should have 50 echo times"
    assert times[0] > 0, "First echo should be positive"
    assert np.all(np.diff(times) > 0), "Times should be strictly increasing"

    print("\n[OK] Echo timing working correctly")
    return True


def test_echo_envelopes():
    """Test echo envelope generation."""
    print("\n" + "=" * 60)
    print("TEST: Echo Envelope Generation")
    print("=" * 60)

    times = np.linspace(0.1, 10.0, 100)

    # Test exponential decay
    env_exp = EchoTemplateGenerator.generate_echo_envelopes(
        times, alpha=1.8, decay_type="exponential"
    )

    print(f"\nExponential decay:")
    print(f"  First amplitude: {env_exp[0]:.4f}")
    print(f"  Last amplitude:  {env_exp[-1]:.4f}")
    print(f"  Max amplitude:   {np.max(env_exp):.4f}")

    assert np.max(env_exp) == 1.0, "Should be normalized to 1.0"
    assert env_exp[0] > env_exp[-1], "Should decay over time"

    # Test power-law decay
    env_pow = EchoTemplateGenerator.generate_echo_envelopes(
        times, alpha=2.0, decay_type="power_law"
    )

    print(f"\nPower-law decay:")
    print(f"  First amplitude: {env_pow[0]:.4f}")
    print(f"  Last amplitude:  {env_pow[-1]:.4f}")

    assert np.max(env_pow) == 1.0, "Should be normalized to 1.0"
    assert env_pow[0] > env_pow[-1], "Should decay over time"

    print("\n[OK] Echo envelopes working correctly")
    return True


def test_complete_template():
    """Test complete template generation."""
    print("\n" + "=" * 60)
    print("TEST: Complete Template Generation")
    print("=" * 60)

    template = EchoTemplateGenerator.generate_template(
        alpha=1.8,
        tau0=0.1,
        num_echoes=100
    )

    print(f"\nTemplate parameters:")
    print(f"  Alpha: {template['alpha']}")
    print(f"  Tau0: {template['tau0']}")
    print(f"  Num echoes: {template['num_echoes']}")

    print(f"\nMetadata:")
    print(f"  Total duration: {template['metadata']['total_duration']:.3f}s")
    print(f"  Mean gap: {template['metadata']['mean_gap']:.2f}")
    print(f"  Std gap: {template['metadata']['std_gap']:.2f}")
    print(f"  Mean amplitude: {template['metadata']['mean_amplitude']:.4f}")
    print(f"  Decay rate: {template['metadata']['decay_rate']:.4f}")

    assert len(template['echo_times']) == 100, "Should have 100 echo times"
    assert len(template['echo_amplitudes']) == 100, "Should have 100 amplitudes"
    assert len(template['prime_gaps']) == 100, "Should have 100 prime gaps"

    print("\n[OK] Complete template working correctly")
    return True


def test_caching():
    """Test template caching."""
    print("\n" + "=" * 60)
    print("TEST: Template Caching")
    print("=" * 60)

    provider = CachedEchoProvider()

    # First call: cache miss
    print("\nFirst call (cache miss):")
    template1 = provider.get_echo_template(alpha=1.5, tau0=0.05, num_echoes=50)
    stats1 = provider.get_stats()
    print(f"  Cache hits: {stats1['cache_hits']}")
    print(f"  Cache misses: {stats1['cache_misses']}")

    # Second call: cache hit
    print("\nSecond call (cache hit):")
    template2 = provider.get_echo_template(alpha=1.5, tau0=0.05, num_echoes=50)
    stats2 = provider.get_stats()
    print(f"  Cache hits: {stats2['cache_hits']}")
    print(f"  Cache misses: {stats2['cache_misses']}")

    assert stats2['cache_hits'] > stats1['cache_hits'], "Should have cache hit"

    # Verify identical
    assert np.array_equal(template1['echo_times'], template2['echo_times']), \
        "Cached times should be identical"
    assert np.array_equal(template1['echo_amplitudes'], template2['echo_amplitudes']), \
        "Cached amplitudes should be identical"

    print(f"\nFinal hit rate: {stats2['hit_rate'] * 100:.1f}%")
    print("\n[OK] Caching working correctly")
    return True


def test_parameter_sweep():
    """Test multiple template generation."""
    print("\n" + "=" * 60)
    print("TEST: Parameter Sweep")
    print("=" * 60)

    provider = CachedEchoProvider()

    alphas = [1.5, 1.8, 2.0]
    tau0s = [0.05, 0.1, 0.2]

    print(f"\nGenerating {len(alphas) * len(tau0s)} templates...")
    templates = provider.get_multiple_templates(alphas, tau0s, num_echoes=50)

    print(f"  Generated {len(templates)} templates")

    for (alpha, tau0), template in templates.items():
        duration = template['metadata']['total_duration']
        print(f"  (alpha={alpha}, tau0={tau0}): duration={duration:.3f}s")

    assert len(templates) == 9, "Should have 9 templates"

    print("\n[OK] Parameter sweep working correctly")
    return True


def main():
    """Run all echo template tests."""
    print("=" * 60)
    print("PRIME-GAP ECHO TEMPLATES - TEST SUITE")
    print("=" * 60)

    tests = [
        ("Prime Generation", test_prime_generation),
        ("Prime Gaps", test_prime_gaps),
        ("Echo Timing", test_echo_timing),
        ("Echo Envelopes", test_echo_envelopes),
        ("Complete Template", test_complete_template),
        ("Caching", test_caching),
        ("Parameter Sweep", test_parameter_sweep),
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
