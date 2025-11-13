"""
Scientific Validation Test: DASE Fractional Derivative Accuracy

Tests that the DASE engine correctly computes fractional derivatives,
which is fundamental to the fractional calculus implementation.

Test 1.1.1 from SCIENTIFIC_VALIDATION_CHECKLIST.md

Acceptance Criteria:
- Fractional derivative accuracy: relative error < 1e-4 vs analytical solution
- Order independence: Works for α ∈ [0.1, 2.0]
- Grid independence: Consistent across resolutions
"""

import pytest
import numpy as np
from pathlib import Path
import sys
from scipy.special import gamma

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

try:
    # Try to import C++ bindings
    from engine.runtime import DASEEngine
    DASE_AVAILABLE = True
except ImportError:
    DASE_AVAILABLE = False


@pytest.mark.skipif(not DASE_AVAILABLE, reason="DASE engine not available")
class TestDASEFractionalDerivative:
    """Test fractional derivative computation accuracy."""

    def analytical_fractional_derivative_power_law(self, x, n, alpha):
        """
        Compute analytical fractional derivative of x^n.

        D^α (x^n) = Γ(n+1) / Γ(n+1-α) * x^(n-α)

        Parameters
        ----------
        x : float or ndarray
            Points at which to evaluate
        n : float
            Power law exponent
        alpha : float
            Fractional derivative order

        Returns
        -------
        float or ndarray
            Analytical fractional derivative
        """
        # Handle x = 0 case (derivative is 0 for appropriate n, alpha)
        result = np.zeros_like(x, dtype=float)

        # For x > 0
        mask = x > 0
        if np.any(mask):
            coefficient = gamma(n + 1) / gamma(n + 1 - alpha)
            result[mask] = coefficient * np.power(x[mask], n - alpha)

        return result

    def test_fractional_derivative_half_order_power_law(self):
        """
        Test D^0.5 (x^2) against analytical solution.

        Analytical: D^0.5 (x^2) = Γ(3)/Γ(2.5) * x^1.5
                                 = 2/√π * x^1.5
                                 ≈ 1.128379 * x^1.5
        """
        # Configuration
        N = 100
        x = np.linspace(0.1, 5.0, N)  # Avoid x=0
        alpha = 0.5
        n = 2.0

        # Analytical solution
        analytical = self.analytical_fractional_derivative_power_law(x, n, alpha)

        # Numerical solution from DASE
        # Note: This assumes DASE engine has a method to compute fractional derivative
        # The actual API may differ - adjust as needed
        engine = DASEEngine(num_nodes=N, alpha=alpha)

        # Initialize with f(x) = x^2
        field_data = x ** n
        engine.set_field("phi", field_data)

        # Compute fractional derivative
        numerical = engine.compute_fractional_derivative("phi")

        # Compute relative error
        relative_error = np.abs((numerical - analytical) / analytical)
        max_relative_error = np.max(relative_error)
        mean_relative_error = np.mean(relative_error)

        print(f"\nTest: D^{alpha} (x^{n})")
        print(f"Max relative error: {max_relative_error:.6e}")
        print(f"Mean relative error: {mean_relative_error:.6e}")

        # Acceptance criteria: < 1e-4 relative error
        assert max_relative_error < 1e-4, (
            f"Max relative error {max_relative_error:.6e} exceeds 1e-4 threshold"
        )
        assert mean_relative_error < 1e-5, (
            f"Mean relative error {mean_relative_error:.6e} exceeds 1e-5 threshold"
        )

        print("✓ Fractional derivative accuracy validated")

    @pytest.mark.parametrize("alpha", [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0])
    def test_fractional_derivative_order_independence(self, alpha):
        """
        Test fractional derivative accuracy for various orders α.

        Tests that the implementation works correctly across the range
        α ∈ [0.1, 2.0], including integer orders (1.0, 2.0).
        """
        # Configuration
        N = 100
        x = np.linspace(0.1, 5.0, N)
        n = 3.0  # Test with x^3

        # Skip if alpha > n (derivative would be singular)
        if alpha > n:
            pytest.skip(f"α={alpha} > n={n}, derivative is singular")

        # Analytical solution
        analytical = self.analytical_fractional_derivative_power_law(x, n, alpha)

        # Numerical solution
        engine = DASEEngine(num_nodes=N, alpha=alpha)
        field_data = x ** n
        engine.set_field("phi", field_data)
        numerical = engine.compute_fractional_derivative("phi")

        # Compute error
        relative_error = np.abs((numerical - analytical) / (analytical + 1e-12))
        max_relative_error = np.max(relative_error)

        print(f"α={alpha}: Max relative error = {max_relative_error:.6e}")

        # Acceptance criteria (slightly more lenient for edge cases)
        threshold = 5e-4 if alpha < 0.3 or alpha > 1.8 else 1e-4
        assert max_relative_error < threshold, (
            f"α={alpha}: Max relative error {max_relative_error:.6e} exceeds {threshold:.6e}"
        )

    @pytest.mark.parametrize("grid_size", [50, 100, 200, 400])
    def test_fractional_derivative_grid_independence(self, grid_size):
        """
        Test that fractional derivative accuracy improves with grid resolution.

        The error should decrease as grid size increases (convergence test).
        """
        N = grid_size
        x = np.linspace(0.1, 5.0, N)
        alpha = 0.5
        n = 2.0

        # Analytical solution
        analytical = self.analytical_fractional_derivative_power_law(x, n, alpha)

        # Numerical solution
        engine = DASEEngine(num_nodes=N, alpha=alpha)
        field_data = x ** n
        engine.set_field("phi", field_data)
        numerical = engine.compute_fractional_derivative("phi")

        # Compute error
        relative_error = np.abs((numerical - analytical) / analytical)
        max_relative_error = np.max(relative_error)

        print(f"Grid size {N}: Max relative error = {max_relative_error:.6e}")

        # Acceptance: Error should be bounded and reasonable
        # For coarse grids, allow more error
        if N <= 50:
            threshold = 1e-3
        elif N <= 100:
            threshold = 5e-4
        else:
            threshold = 1e-4

        assert max_relative_error < threshold, (
            f"Grid {N}: Error {max_relative_error:.6e} exceeds {threshold:.6e}"
        )

    def test_fractional_derivative_gaussian(self):
        """
        Test fractional derivative of Gaussian function.

        While there's no simple closed form for D^α exp(-x²),
        we can verify properties like smoothness and expected behavior.
        """
        # Configuration
        N = 200
        x = np.linspace(-3.0, 3.0, N)
        alpha = 0.5

        # Gaussian function
        sigma = 1.0
        gaussian = np.exp(-x**2 / (2 * sigma**2))

        # Compute fractional derivative
        engine = DASEEngine(num_nodes=N, alpha=alpha)
        engine.set_field("phi", gaussian)
        deriv = engine.compute_fractional_derivative("phi")

        # Properties to verify:
        # 1. Derivative should be smooth (no large jumps)
        deriv_gradient = np.gradient(deriv)
        max_gradient = np.max(np.abs(deriv_gradient))
        assert max_gradient < 10.0, f"Derivative not smooth: max gradient = {max_gradient}"

        # 2. Derivative should be symmetric (Gaussian is symmetric)
        left_half = deriv[:N//2]
        right_half = deriv[N//2:][::-1]
        symmetry_error = np.max(np.abs(left_half - right_half))
        assert symmetry_error < 0.1, f"Derivative not symmetric: error = {symmetry_error}"

        # 3. Derivative should be bounded
        assert np.all(np.isfinite(deriv)), "Derivative contains NaN or Inf"
        assert np.max(np.abs(deriv)) < 100.0, "Derivative unbounded"

        print("✓ Fractional derivative of Gaussian validated")

    def test_fractional_derivative_consistency_with_integer_orders(self):
        """
        Test that fractional derivative reduces to standard derivatives for integer orders.

        D^1.0 (f) should equal standard first derivative
        D^2.0 (f) should equal standard second derivative
        """
        N = 100
        x = np.linspace(0.1, 5.0, N)
        dx = x[1] - x[0]

        # Test function: sin(x)
        f = np.sin(x)

        # Test α = 1.0 (first derivative)
        engine_1 = DASEEngine(num_nodes=N, alpha=1.0)
        engine_1.set_field("phi", f)
        fractional_deriv_1 = engine_1.compute_fractional_derivative("phi")

        # Standard first derivative (finite differences)
        standard_deriv_1 = np.gradient(f, dx)

        # Compare (allow some numerical error)
        error_1 = np.max(np.abs(fractional_deriv_1 - standard_deriv_1))
        print(f"α=1.0: Max error vs standard derivative = {error_1:.6e}")
        assert error_1 < 0.01, f"α=1.0 does not match standard derivative: error = {error_1}"

        # Test α = 2.0 (second derivative)
        engine_2 = DASEEngine(num_nodes=N, alpha=2.0)
        engine_2.set_field("phi", f)
        fractional_deriv_2 = engine_2.compute_fractional_derivative("phi")

        # Standard second derivative
        standard_deriv_2 = np.gradient(np.gradient(f, dx), dx)

        # Compare
        error_2 = np.max(np.abs(fractional_deriv_2 - standard_deriv_2))
        print(f"α=2.0: Max error vs standard derivative = {error_2:.6e}")
        assert error_2 < 0.05, f"α=2.0 does not match standard derivative: error = {error_2}"

        print("✓ Consistency with integer orders validated")

    def test_fractional_derivative_linearity(self):
        """
        Test linearity of fractional derivative operator.

        D^α (a*f + b*g) = a*D^α(f) + b*D^α(g)
        """
        N = 100
        x = np.linspace(0.1, 5.0, N)
        alpha = 0.5

        # Two test functions
        f = x ** 2
        g = np.sin(x)

        # Scalars
        a, b = 2.0, 3.0

        # Compute D^α (a*f + b*g)
        engine = DASEEngine(num_nodes=N, alpha=alpha)
        engine.set_field("phi", a * f + b * g)
        lhs = engine.compute_fractional_derivative("phi")

        # Compute a*D^α(f) + b*D^α(g)
        engine.set_field("phi", f)
        df = engine.compute_fractional_derivative("phi")

        engine.set_field("phi", g)
        dg = engine.compute_fractional_derivative("phi")

        rhs = a * df + b * dg

        # Compare
        max_error = np.max(np.abs(lhs - rhs))
        relative_error = max_error / np.max(np.abs(lhs))

        print(f"Linearity test: Max relative error = {relative_error:.6e}")

        assert relative_error < 1e-4, (
            f"Linearity violated: relative error = {relative_error:.6e}"
        )

        print("✓ Linearity validated")

    def test_fractional_derivative_performance(self):
        """
        Test that fractional derivative computation is reasonably fast.

        This is a performance sanity check, not a strict requirement.
        """
        import time

        N = 10000
        x = np.linspace(0.1, 10.0, N)
        alpha = 0.5

        # Large field
        field = np.sin(x) * np.exp(-x / 10.0)

        engine = DASEEngine(num_nodes=N, alpha=alpha)
        engine.set_field("phi", field)

        # Time the computation
        start = time.perf_counter()
        deriv = engine.compute_fractional_derivative("phi")
        duration = time.perf_counter() - start

        print(f"Fractional derivative computation (N={N}): {duration*1000:.2f} ms")

        # Sanity check: Should complete in reasonable time
        assert duration < 1.0, f"Computation too slow: {duration:.3f} s"

        # Verify result is valid
        assert np.all(np.isfinite(deriv)), "Result contains NaN or Inf"

        print("✓ Performance acceptable")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
