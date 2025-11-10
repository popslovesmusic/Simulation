# IGSOA GW Engine - Week 2 Next Steps

**Created:** November 10, 2025
**Session Status:** Week 1 Complete (90% achieved)
**Ready to Start:** BinaryMerger Implementation

---

## 🎯 **Primary Goal for Week 2**

**Generate the first IGSOA gravitational waveform from a binary merger simulation**

This will be the first-ever simulation of gravitational waves with:
- Fractional memory dynamics (α ≠ 2)
- Prime-structured echo potential
- IGSOA field projection to observable strain

---

## 📋 **Task 1: Implement BinaryMerger/SourceManager**

**Priority:** HIGHEST - This is the only remaining Week 1 component
**Estimated Time:** 2-3 hours
**Status:** Not started

### Files to Create

1. **`src/cpp/igsoa_gw_engine/core/source_manager.h`**
2. **`src/cpp/igsoa_gw_engine/core/source_manager.cpp`**

### Required Components

```cpp
class BinaryMerger {
public:
    // Configuration
    struct Config {
        double mass1;           // First BH mass (M☉)
        double mass2;           // Second BH mass (M☉)
        double initial_separation;  // Initial orbital radius (m)
        double orbital_frequency;   // Initial ω (rad/s)
        Vector3D center;        // Orbit center position
        double gaussian_width;  // σ for asymmetry concentration
    };

    // Constructor
    BinaryMerger(const Config& config);

    // Core methods
    void evolveOrbit(double dt);
    std::vector<std::complex<double>> computeSourceTerms(
        const SymmetryField& field,
        double t) const;

    // Query methods
    Vector3D getPosition1() const;
    Vector3D getPosition2() const;
    double getSeparation() const;
    bool hasMerged() const;

private:
    Config config_;
    double current_phase_;
    double current_separation_;
    double t_merger_;
};
```

### Physics to Implement

1. **Circular Orbit Kinematics**
   ```
   v = √(G M_total / r)
   ω = v / r

   x₁(t) = r₁ cos(ωt + φ₀)
   y₁(t) = r₁ sin(ωt + φ₀)

   x₂(t) = -r₂ cos(ωt + φ₀)
   y₂(t) = -r₂ sin(ωt + φ₀)

   where: r₁ = m₂/(m₁+m₂) × r
          r₂ = m₁/(m₁+m₂) × r
   ```

2. **Gaussian Asymmetry Concentrations**
   ```
   S(x,t) = S₁(x,t) + S₂(x,t)

   S_i(x,t) = A_i · exp(-|x - x_i(t)|² / (2σ²))

   where: A_i ∝ m_i (mass-dependent amplitude)
   ```

3. **Inspiral (Optional for v1, but nice to have)**
   ```
   dr/dt = -64/5 · G³m₁m₂(m₁+m₂) / (c⁵ r³)

   Merger condition: r < 2·R_s where R_s = 2GM/c²
   ```

### Implementation Steps

1. Create header with Config struct and class declaration
2. Implement constructor and initialization
3. Implement `evolveOrbit()` - update positions each timestep
4. Implement `computeSourceTerms()` - generate Gaussian sources
5. Add merger detection logic
6. Update CMakeLists.txt to include source_manager.cpp

### Testing

Create simple test:
```cpp
// In tests/test_source_manager.cpp
BinaryMerger::Config config;
config.mass1 = 30.0;  // 30 M☉
config.mass2 = 30.0;
config.initial_separation = 100e3;  // 100 km
BinaryMerger merger(config);

for (int i = 0; i < 100; i++) {
    merger.evolveOrbit(0.001);  // 1 ms steps
    std::cout << "Separation: " << merger.getSeparation() << " m" << std::endl;
}
```

---

## 📋 **Task 2: Integration Test - Couple All Modules**

**Priority:** HIGH
**Estimated Time:** 1 hour
**Status:** Waiting on Task 1

### File to Create

**`tests/test_gw_waveform_generation.cpp`**

### What to Implement

```cpp
int main() {
    // 1. Create field
    SymmetryFieldConfig field_config;
    field_config.nx = 64;
    field_config.ny = 64;
    field_config.nz = 64;
    field_config.dx = 1000.0;  // 1 km resolution
    field_config.dt = 0.001;   // 1 ms timestep
    SymmetryField field(field_config);

    // 2. Create fractional solver
    FractionalSolverConfig frac_config;
    frac_config.alpha_min = 1.5;
    frac_config.alpha_max = 1.5;  // Fixed α for now
    FractionalSolver solver(frac_config, field.getTotalPoints());

    // 3. Create binary merger
    BinaryMerger::Config merger_config;
    merger_config.mass1 = 30.0;
    merger_config.mass2 = 30.0;
    merger_config.initial_separation = 200e3;  // 200 km
    BinaryMerger merger(merger_config);

    // 4. Create projection operators
    ProjectionOperators projector(field_config);

    // 5. Time evolution loop
    std::vector<double> time_array;
    std::vector<double> h_plus_array;
    std::vector<double> h_cross_array;

    for (int step = 0; step < 1000; step++) {
        // Get source terms
        auto sources = merger.computeSourceTerms(field, step * field_config.dt);

        // Compute fractional derivatives
        auto frac_derivs = solver.computeDerivatives(field.getAlphaValues());

        // Evolve field
        field.evolveStep(frac_derivs, sources);

        // Update fractional solver history
        auto second_derivs = computeSecondTimeDerivatives(field);  // TODO
        solver.updateHistory(field.getDeltaPhiFlat(), second_derivs,
                           field.getAlphaValues(), field_config.dt);

        // Evolve orbit
        merger.evolveOrbit(field_config.dt);

        // Extract strain every 10 steps
        if (step % 10 == 0) {
            auto strain = projector.compute_strain_at_observer(field);
            time_array.push_back(step * field_config.dt);
            h_plus_array.push_back(strain.h_plus);
            h_cross_array.push_back(strain.h_cross);
        }

        if (step % 100 == 0) {
            std::cout << "Step " << step << ": h_+ = " << strain.h_plus << std::endl;
        }
    }

    // 6. Export results
    exportToCSV("gw_waveform_alpha_1.5.csv", time_array, h_plus_array, h_cross_array);

    std::cout << "SUCCESS: Generated IGSOA waveform!" << std::endl;
    return 0;
}
```

### Expected Output

```
Step 0: h_+ = 0
Step 100: h_+ = 1.23e-21
Step 200: h_+ = 3.45e-21
...
Step 900: h_+ = 8.76e-20
SUCCESS: Generated IGSOA waveform!
```

### Files Created

- `gw_waveform_alpha_1.5.csv` with columns: time, h_plus, h_cross

---

## 📋 **Task 3: Generate First Waveform and Visualize**

**Priority:** HIGH
**Estimated Time:** 1 hour
**Status:** Waiting on Task 2

### Python Plotting Script

Create **`scripts/plot_gw_waveform.py`**:

```python
import numpy as np
import matplotlib.pyplot as plt

# Load data
data = np.loadtxt('gw_waveform_alpha_1.5.csv', delimiter=',', skiprows=1)
time = data[:, 0]
h_plus = data[:, 1]
h_cross = data[:, 2]

# Compute amplitude
amplitude = np.sqrt(h_plus**2 + h_cross**2)

# Create figure
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# Plot h_+
axes[0].plot(time * 1000, h_plus, 'b-', linewidth=1.5)
axes[0].set_ylabel('h_+ strain')
axes[0].set_title('IGSOA Gravitational Waveform (α = 1.5)')
axes[0].grid(True, alpha=0.3)

# Plot h_×
axes[1].plot(time * 1000, h_cross, 'r-', linewidth=1.5)
axes[1].set_ylabel('h_× strain')
axes[1].grid(True, alpha=0.3)

# Plot amplitude
axes[2].plot(time * 1000, amplitude, 'k-', linewidth=2)
axes[2].set_xlabel('Time (ms)')
axes[2].set_ylabel('Total amplitude')
axes[2].set_yscale('log')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('gw_waveform_alpha_1.5.png', dpi=300)
plt.show()

print(f"Peak strain: {np.max(amplitude):.3e}")
print(f"Duration: {time[-1] * 1000:.1f} ms")
```

### Expected Result

A PNG image showing:
- Clear inspiral signal (increasing amplitude)
- Merger peak (maximum amplitude)
- Possible ringdown (if α ≠ 2, memory effects appear)

---

## 📋 **Task 4: Parameter Sweep - Varying Alpha**

**Priority:** MEDIUM
**Estimated Time:** 1-2 hours
**Status:** Waiting on Task 3

### Create Sweep Script

**`scripts/run_alpha_sweep.sh`** (Windows: `.bat`):

```bash
#!/bin/bash

for alpha in 1.0 1.2 1.5 1.8 2.0; do
    echo "Running with alpha = $alpha"
    ./build/test_gw_waveform --alpha $alpha --output "waveform_alpha_${alpha}.csv"
done

echo "All runs complete"
python scripts/compare_alpha_waveforms.py
```

### Comparison Script

**`scripts/compare_alpha_waveforms.py`**:

```python
import numpy as np
import matplotlib.pyplot as plt

alphas = [1.0, 1.2, 1.5, 1.8, 2.0]
colors = plt.cm.viridis(np.linspace(0, 1, len(alphas)))

fig, ax = plt.subplots(figsize=(12, 6))

for alpha, color in zip(alphas, colors):
    data = np.loadtxt(f'waveform_alpha_{alpha:.1f}.csv', delimiter=',', skiprows=1)
    time = data[:, 0] * 1000  # Convert to ms
    h_plus = data[:, 1]

    ax.plot(time, h_plus, color=color, linewidth=1.5,
            label=f'α = {alpha:.1f}', alpha=0.8)

ax.set_xlabel('Time (ms)', fontsize=12)
ax.set_ylabel('GW Strain h_+', fontsize=12)
ax.set_title('IGSOA Waveforms: Effect of Fractional Memory (α)', fontsize=14)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('alpha_comparison.png', dpi=300)
plt.show()
```

### Expected Findings

- **α = 2.0**: Standard wave equation (no memory)
- **α = 1.5**: Moderate memory → phase shift, amplitude modulation
- **α = 1.0**: Maximum memory → strongest modifications, possible oscillations

---

## 📋 **Task 5: Begin EchoGenerator (Week 2-3)**

**Priority:** LOW (Week 3 focus)
**Estimated Time:** 3-4 hours
**Status:** Planning only

### Concept

Post-merger, the IGSOA field can support delayed echoes due to:
1. Memory effects at the horizon (α < 2)
2. Prime number gap structure in asymmetry distribution
3. Effective "cavity" resonances

### Files to Create

- `src/cpp/igsoa_gw_engine/analysis/echo_generator.h`
- `src/cpp/igsoa_gw_engine/analysis/echo_generator.cpp`

### Core Functionality

```cpp
class EchoGenerator {
public:
    struct EchoConfig {
        std::vector<int> prime_gaps;      // [2, 4, 6, 10, 12, ...]
        double base_delay;                // t₀ (ms)
        double amplitude_decay;           // Exponential decay factor
        double memory_factor;             // From α
    };

    std::vector<double> generateEchoSignal(
        const std::vector<double>& original_signal,
        double dt,
        const EchoConfig& config) const;
};
```

### Implementation Strategy

1. Compute prime number gaps up to N = 1000
2. Convert gaps → time delays: Δt_n = t₀ · gap_n
3. For each echo: h_echo(t) = A_n · h_original(t - Δt_n)
4. Decay: A_n = A₀ · exp(-n/τ)
5. Sum all contributions

**Deferred to Week 3** - Focus on waveform generation first!

---

## 🚀 **Quick Start Commands**

When resuming, run these in order:

```bash
# 1. Verify build is still working
cd D:\igsoa-sim
cmake --build build --config Release

# 2. Run existing tests to confirm nothing broke
./build/Release/test_gw_engine_basic.exe

# 3. Start implementing BinaryMerger
# Create: src/cpp/igsoa_gw_engine/core/source_manager.h
# Create: src/cpp/igsoa_gw_engine/core/source_manager.cpp

# 4. Update CMakeLists.txt
# Add source_manager.cpp to igsoa_gw_core target

# 5. Compile and test
cmake --build build --config Release
./build/Release/test_source_manager.exe

# 6. Create waveform test
# Create: tests/test_gw_waveform_generation.cpp

# 7. Run full simulation
./build/Release/test_gw_waveform_generation.exe

# 8. Plot results
python scripts/plot_gw_waveform.py
```

---

## 📊 **Success Metrics for Week 2**

- ✅ BinaryMerger class compiles and runs
- ✅ Integration test completes without errors
- ✅ First waveform CSV file generated
- ✅ Waveform plot shows expected inspiral-merger-ringdown structure
- ✅ Parameter sweep reveals α-dependence
- ✅ Documentation updated with waveform results

---

## 💡 **Tips for Implementation**

1. **Start Simple**: Use circular orbits, no inspiral (constant separation)
2. **Test Incrementally**: Each component tested before integration
3. **Use Small Grids**: 32³ or 64³ for fast iteration
4. **Energy Conservation**: Monitor total field energy each step
5. **Visualization**: Plot field snapshots to debug source placement

---

## 📚 **Reference Equations**

### Gravitational Wave Strain
```
h_+ = O_xx - O_yy
h_× = 2 O_xy

where: O_μν = ∇_μ δΦ* ∇_ν δΦ - g_μν L(δΦ)
```

### Fractional Wave Equation
```
∂²ₓψ - ₀D^α_t ψ - V(δΦ)ψ = S(x,t)
```

### Caputo Fractional Derivative
```
₀D^α_t f(t) = 1/Γ(1-α) ∫₀ᵗ (t-τ)^(-α) f'(τ) dτ
```

### SOE Approximation
```
₀D^α_t f(t) ≈ Σᵣ zᵣ(t)
where: dzᵣ/dt = -sᵣ zᵣ + wᵣ f'(t)
```

---

## 🎯 **Estimated Timeline**

| Task | Time | Cumulative |
|------|------|------------|
| BinaryMerger implementation | 2-3 hrs | 3 hrs |
| Integration test | 1 hr | 4 hrs |
| First waveform generation | 1 hr | 5 hrs |
| Parameter sweep (5 alphas) | 1-2 hrs | 7 hrs |
| Analysis and plotting | 1 hr | 8 hrs |
| Documentation | 1 hr | **9 hrs** |

**Total Week 2 Estimated Effort: 8-10 hours**

---

## ✅ **Completion Checklist**

**Before Starting Week 2:**
- [x] Week 1 implementation complete
- [x] All tests passing (5/5)
- [x] Build system working
- [x] Documentation updated

**Week 2 Goals:**
- [ ] BinaryMerger class implemented
- [ ] Source terms generating correctly
- [ ] Integration test passing
- [ ] First waveform CSV generated
- [ ] Waveform plot created
- [ ] Parameter sweep complete
- [ ] Results documented

**Week 3 Prep:**
- [ ] EchoGenerator design complete
- [ ] Prime number utilities implemented
- [ ] Post-merger analysis framework ready

---

**Document Status:** Planning (Pre-Week 2)
**Last Updated:** November 10, 2025
**Next Review:** After BinaryMerger implementation

---

## 📞 **Quick Reference**

**Current Directory:** `D:\igsoa-sim`
**Build Directory:** `build/`
**Test Executable:** `build/Release/test_gw_engine_basic.exe`

**Key Files:**
- SymmetryField: `src/cpp/igsoa_gw_engine/core/symmetry_field.{h,cpp}`
- FractionalSolver: `src/cpp/igsoa_gw_engine/core/fractional_solver.{h,cpp}`
- ProjectionOperators: `src/cpp/igsoa_gw_engine/core/projection_operators.{h,cpp}`
- Tests: `tests/test_gw_engine_basic.cpp`

**Next File to Create:** `src/cpp/igsoa_gw_engine/core/source_manager.h`

**Git Status:** Not a git repo (consider initializing!)

---

**Ready to generate the first IGSOA gravitational waveform!** 🌊
