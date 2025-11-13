"""
Scientific Validation Test: IGSOA Energy Conservation

Tests that the IGSOA engine conserves energy in isolated systems,
which is a fundamental requirement for physical correctness.

Test 2.1.1 from SCIENTIFIC_VALIDATION_CHECKLIST.md

Acceptance Criteria:
- Energy conserved to < 0.1% over 1000 steps
- No secular drift (monotonic increase/decrease)
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

try:
    # Try to import C++ bindings
    from engine.runtime import IGSOAEngine
    IGSOA_AVAILABLE = True
except ImportError:
    IGSOA_AVAILABLE = False


@pytest.mark.skipif(not IGSOA_AVAILABLE, reason="IGSOA engine not available")
class TestIGSOAEnergyConservation:
    """Test energy conservation in IGSOA engine."""

    def compute_total_energy_2d(self, psi, phi, h, dx, dy, kappa=1.0, gamma=0.1):
        """
        Compute total energy of 2D IGSOA system.

        E_total = ∫ [|∇ψ|² + |ψ|⁴ + κ|φ|² + γh²] dV

        Parameters
        ----------
        psi : complex ndarray, shape (N_x, N_y)
            Complex scalar field
        phi : complex ndarray, shape (N_x, N_y)
            Gauge field
        h : float ndarray, shape (N_x, N_y)
            Higgs field
        dx, dy : float
            Grid spacing
        kappa, gamma : float
            Coupling constants

        Returns
        -------
        float
            Total energy
        """
        # Gradient energy (finite differences)
        grad_x_real = np.gradient(psi.real, dx, axis=0)
        grad_x_imag = np.gradient(psi.imag, dx, axis=0)
        grad_y_real = np.gradient(psi.real, dy, axis=1)
        grad_y_imag = np.gradient(psi.imag, dy, axis=1)

        grad_energy = np.sum(
            grad_x_real**2 + grad_x_imag**2 + grad_y_real**2 + grad_y_imag**2
        )

        # Interaction energy (quartic)
        psi_magnitude_sq = psi.real**2 + psi.imag**2
        interaction_energy = np.sum(0.25 * psi_magnitude_sq**2)

        # Gauge field energy
        gauge_energy = 0.5 * kappa * np.sum(phi.real**2 + phi.imag**2)

        # Higgs field energy
        higgs_energy = 0.5 * gamma * np.sum(h**2)

        # Total energy (integrated over grid)
        total = (grad_energy + interaction_energy + gauge_energy + higgs_energy) * dx * dy

        return total

    def test_energy_conservation_free_evolution(self):
        """
        Test energy conservation for free field evolution (no sources).

        This is the most basic test: isolated system should conserve energy.
        """
        # Configuration
        N_x, N_y = 64, 64
        L_x, L_y = 10.0, 10.0
        dx, dy = L_x / N_x, L_y / N_y
        dt = 0.01
        num_steps = 1000
        kappa = 1.0
        gamma = 0.1

        # Initialize engine
        engine = IGSOAEngine(
            num_nodes=N_x * N_y,
            grid_shape=(N_x, N_y),
            R_c=1.0,
            kappa=kappa,
            gamma=gamma,
            dt=dt,
        )

        # Initialize with Gaussian wavepacket
        x = np.linspace(-L_x / 2, L_x / 2, N_x)
        y = np.linspace(-L_y / 2, L_y / 2, N_y)
        X, Y = np.meshgrid(x, y, indexing='ij')

        sigma = 2.0
        amplitude = 1.0
        psi_initial = amplitude * np.exp(-(X**2 + Y**2) / (2 * sigma**2))
        psi_initial = psi_initial.astype(complex)  # Convert to complex

        engine.set_field("psi", psi_initial)

        # Get initial state
        psi_0 = engine.get_field("psi")
        phi_0 = engine.get_field("phi")
        h_0 = engine.get_field("h")

        E_0 = self.compute_total_energy_2d(psi_0, phi_0, h_0, dx, dy, kappa, gamma)

        print(f"\nInitial energy: {E_0:.6f}")

        # Evolve system
        energies = [E_0]
        times = [0.0]

        for step in range(num_steps):
            engine.step()

            # Sample energy every 10 steps
            if step % 10 == 0:
                psi = engine.get_field("psi")
                phi = engine.get_field("phi")
                h = engine.get_field("h")

                E = self.compute_total_energy_2d(psi, phi, h, dx, dy, kappa, gamma)
                energies.append(E)
                times.append((step + 1) * dt)

        E_final = energies[-1]
        print(f"Final energy: {E_final:.6f}")

        # Energy conservation check
        energy_drift = E_final - E_0
        relative_drift = abs(energy_drift / E_0)

        print(f"Energy drift: {energy_drift:.6e} ({relative_drift*100:.4f}%)")

        # Acceptance criteria: < 0.1% drift over 1000 steps
        assert relative_drift < 0.001, (
            f"Energy drift {relative_drift*100:.4f}% exceeds 0.1% threshold"
        )

        # Check for secular drift (monotonic trend)
        energies_array = np.array(energies)
        energy_changes = np.diff(energies_array)

        # If all changes have the same sign, there's secular drift
        all_positive = np.all(energy_changes > 0)
        all_negative = np.all(energy_changes < 0)

        assert not (all_positive or all_negative), (
            "Detected secular energy drift (monotonic trend)"
        )

        print("✓ Energy conservation validated")

    def test_energy_conservation_colliding_wavepackets(self):
        """
        Test energy conservation during wavepacket collision.

        More stringent test: energy should be conserved even during
        nonlinear interactions.
        """
        # Configuration
        N_x, N_y = 64, 64
        L_x, L_y = 20.0, 20.0
        dx, dy = L_x / N_x, L_y / N_y
        dt = 0.01
        num_steps = 500
        kappa = 1.0
        gamma = 0.1

        # Initialize engine
        engine = IGSOAEngine(
            num_nodes=N_x * N_y,
            grid_shape=(N_x, N_y),
            R_c=1.0,
            kappa=kappa,
            gamma=gamma,
            dt=dt,
        )

        # Initialize with two Gaussian wavepackets moving toward each other
        x = np.linspace(-L_x / 2, L_x / 2, N_x)
        y = np.linspace(-L_y / 2, L_y / 2, N_y)
        X, Y = np.meshgrid(x, y, indexing='ij')

        sigma = 2.0
        amplitude = 0.5
        separation = 8.0

        # Wavepacket 1 (left)
        psi_1 = amplitude * np.exp(-((X + separation)**2 + Y**2) / (2 * sigma**2))

        # Wavepacket 2 (right)
        psi_2 = amplitude * np.exp(-((X - separation)**2 + Y**2) / (2 * sigma**2))

        # Superpose with velocities (complex phase gives momentum)
        k_x = 0.5  # Wave vector (momentum)
        psi_initial = (
            psi_1 * np.exp(1j * k_x * X) +
            psi_2 * np.exp(-1j * k_x * X)
        )

        engine.set_field("psi", psi_initial)

        # Get initial energy
        psi_0 = engine.get_field("psi")
        phi_0 = engine.get_field("phi")
        h_0 = engine.get_field("h")

        E_0 = self.compute_total_energy_2d(psi_0, phi_0, h_0, dx, dy, kappa, gamma)

        print(f"\nInitial energy: {E_0:.6f}")

        # Evolve through collision
        energies = [E_0]

        for step in range(num_steps):
            engine.step()

            if step % 10 == 0:
                psi = engine.get_field("psi")
                phi = engine.get_field("phi")
                h = engine.get_field("h")

                E = self.compute_total_energy_2d(psi, phi, h, dx, dy, kappa, gamma)
                energies.append(E)

        E_final = energies[-1]
        print(f"Final energy: {E_final:.6f}")

        # Energy conservation check (more lenient during collision: < 0.5%)
        relative_drift = abs((E_final - E_0) / E_0)
        print(f"Energy drift: {relative_drift*100:.4f}%")

        assert relative_drift < 0.005, (
            f"Energy drift {relative_drift*100:.4f}% exceeds 0.5% threshold"
        )

        print("✓ Energy conserved through collision")

    def test_energy_components_balance(self):
        """
        Test that energy is exchanged between components but total is conserved.

        Individual energy components (kinetic, potential, etc.) can change,
        but their sum should remain constant.
        """
        # Configuration
        N_x, N_y = 32, 32
        L_x, L_y = 10.0, 10.0
        dx, dy = L_x / N_x, L_y / N_y
        dt = 0.01
        num_steps = 200

        engine = IGSOAEngine(
            num_nodes=N_x * N_y,
            grid_shape=(N_x, N_y),
            R_c=1.0,
            kappa=1.0,
            gamma=0.1,
            dt=dt,
        )

        # Initialize with localized excitation
        x = np.linspace(-L_x / 2, L_x / 2, N_x)
        y = np.linspace(-L_y / 2, L_y / 2, N_y)
        X, Y = np.meshgrid(x, y, indexing='ij')

        psi_initial = np.exp(-(X**2 + Y**2) / 4.0).astype(complex)
        engine.set_field("psi", psi_initial)

        # Track energy components
        grad_energies = []
        interaction_energies = []
        total_energies = []

        for step in range(num_steps):
            psi = engine.get_field("psi")
            phi = engine.get_field("phi")
            h = engine.get_field("h")

            # Gradient energy
            grad_x_real = np.gradient(psi.real, dx, axis=0)
            grad_x_imag = np.gradient(psi.imag, dx, axis=0)
            grad_y_real = np.gradient(psi.real, dy, axis=1)
            grad_y_imag = np.gradient(psi.imag, dy, axis=1)

            E_grad = np.sum(
                grad_x_real**2 + grad_x_imag**2 + grad_y_real**2 + grad_y_imag**2
            ) * dx * dy

            # Interaction energy
            psi_mag_sq = psi.real**2 + psi.imag**2
            E_int = 0.25 * np.sum(psi_mag_sq**2) * dx * dy

            # Total (simplified, just psi contribution)
            E_total = E_grad + E_int

            grad_energies.append(E_grad)
            interaction_energies.append(E_int)
            total_energies.append(E_total)

            engine.step()

        # Check that total energy is conserved
        E_0 = total_energies[0]
        E_final = total_energies[-1]
        relative_change = abs((E_final - E_0) / E_0)

        print(f"\nInitial total energy: {E_0:.6f}")
        print(f"Final total energy: {E_final:.6f}")
        print(f"Relative change: {relative_change*100:.4f}%")

        # Check that components change (energy is exchanged)
        grad_change = abs(grad_energies[-1] - grad_energies[0]) / grad_energies[0]
        int_change = abs(interaction_energies[-1] - interaction_energies[0]) / interaction_energies[0]

        print(f"Gradient energy change: {grad_change*100:.2f}%")
        print(f"Interaction energy change: {int_change*100:.2f}%")

        # Components should change (> 1%)
        assert grad_change > 0.01 or int_change > 0.01, (
            "Energy components not exchanging (system may be static)"
        )

        # But total should be conserved (< 0.1%)
        assert relative_change < 0.001, (
            f"Total energy not conserved: {relative_change*100:.4f}%"
        )

        print("✓ Energy components balance correctly")

    @pytest.mark.parametrize("grid_size", [32, 64, 128])
    def test_energy_conservation_grid_independence(self, grid_size):
        """
        Test that energy conservation is independent of grid resolution.

        Energy conservation is a fundamental property and should hold
        regardless of numerical discretization.
        """
        N = grid_size
        L = 10.0
        dx = L / N
        dt = 0.01
        num_steps = 100

        engine = IGSOAEngine(
            num_nodes=N * N,
            grid_shape=(N, N),
            R_c=1.0,
            kappa=1.0,
            gamma=0.1,
            dt=dt,
        )

        # Same physical initial condition
        x = np.linspace(-L / 2, L / 2, N)
        y = np.linspace(-L / 2, L / 2, N)
        X, Y = np.meshgrid(x, y, indexing='ij')

        psi_initial = np.exp(-(X**2 + Y**2) / 4.0).astype(complex)
        engine.set_field("psi", psi_initial)

        # Initial energy
        psi_0 = engine.get_field("psi")
        phi_0 = engine.get_field("phi")
        h_0 = engine.get_field("h")

        E_0 = self.compute_total_energy_2d(psi_0, phi_0, h_0, dx, dx, 1.0, 0.1)

        # Evolve
        for _ in range(num_steps):
            engine.step()

        # Final energy
        psi_f = engine.get_field("psi")
        phi_f = engine.get_field("phi")
        h_f = engine.get_field("h")

        E_f = self.compute_total_energy_2d(psi_f, phi_f, h_f, dx, dx, 1.0, 0.1)

        relative_drift = abs((E_f - E_0) / E_0)

        print(f"Grid {N}x{N}: Energy drift = {relative_drift*100:.4f}%")

        # Should conserve energy regardless of grid size
        assert relative_drift < 0.002, (
            f"Grid {N}x{N}: Energy drift {relative_drift*100:.4f}% exceeds 0.2%"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
