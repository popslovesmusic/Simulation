# Gravitational Wave Engines Implementation Plan

**Version:** 1.0
**Date:** November 2025
**Status:** Design Phase
**Requested:** Two specialized GW engines for black hole merger echo detection and general study

---

## Executive Summary

This document details the implementation plan for **two specialized gravitational wave engines** built on the IGSOA framework:

1. **Black Hole Merger Echo Parameter Sweep Engine (BH-Echo-PSE)**
   - Purpose: Systematic parameter space exploration for post-merger echo detection
   - Focus: Automated sweeps over α_H, ρ, τ*, M₁, M₂, spin parameters
   - Output: Echo signatures, detection statistics, parameter constraints

2. **General Gravitational Wave Study Engine (GW-General)**
   - Purpose: Flexible research tool for GW phenomena investigation
   - Focus: Custom waveform generation, LIGO comparison, variable speed tests
   - Output: Strain h(t), spectrograms, arrival time delays, validation reports

Both engines share core IGSOA infrastructure but differ in workflow and objectives.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    IGSOA-SIM Framework                      │
├─────────────────────────────────────────────────────────────┤
│  Core Infrastructure (Shared)                               │
│  ├── SymmetryField (3D δΦ grid)                            │
│  ├── FractionalSolver (Caputo derivatives)                 │
│  ├── ProjectionOperators (φ, O_μν, B_μ)                   │
│  ├── BinaryMerger (source dynamics)                        │
│  └── StrainExtractor (h_+, h_× for detectors)             │
├─────────────────────────────────────────────────────────────┤
│  Engine 1: BH-Echo-PSE                                     │
│  ├── ParameterSweeper (automated grid search)             │
│  ├── EchoDetector (prime-structured signal finder)        │
│  ├── StatisticalAnalyzer (SNR, Bayesian inference)        │
│  └── ResultsDatabase (HDF5 storage)                       │
├─────────────────────────────────────────────────────────────┤
│  Engine 2: GW-General                                      │
│  ├── WaveformGenerator (custom initial conditions)        │
│  ├── GRComparator (SEOBNRv4, IMRPhenomD interface)       │
│  ├── SpeedCalculator (variable c_gw tests)               │
│  ├── SpectrumAnalyzer (FFT, spectrograms)                │
│  └── LIGOInterface (real data ingestion)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Engine 1: Black Hole Merger Echo Parameter Sweep Engine

### Purpose & Objectives

**Primary Goal:** Systematically explore IGSOA parameter space to identify echo-producing configurations and constrain parameters from observations.

**Key Questions:**
1. For which (α_H, ρ, τ*) combinations are echoes detectable by LIGO?
2. What is the optimal search strategy for echo detection in real data?
3. Can we constrain IGSOA parameters from observed mergers?
4. How do echoes depend on binary parameters (masses, spins, distance)?

### Core Features

#### 1. Parameter Space Definition

```cpp
struct EchoParameterSpace {
    // IGSOA-specific parameters
    struct IGSOAParams {
        double alpha_horizon;      // α_H ∈ [1.0, 2.0] - memory at horizon
        double reflectivity;       // ρ ∈ [0.0, 1.0] - echo strength
        double tau_star;           // τ* ∈ [0.1ms, 10ms] - delay scale
        double nu;                 // ν ∈ [0.5, 2.0] - gap exponent
        int k_star;                // k* ∈ [5, 50] - echo cutoff
    };

    // Binary system parameters
    struct BinaryParams {
        double mass1;              // M₁ ∈ [5, 100] M_sun
        double mass2;              // M₂ ∈ [5, 100] M_sun
        double spin1;              // χ₁ ∈ [0, 0.99]
        double spin2;              // χ₂ ∈ [0, 0.99]
        double distance;           // D ∈ [100, 2000] Mpc
        double inclination;        // ι ∈ [0, π]
    };

    // Detector parameters
    struct DetectorParams {
        string detector_name;      // "LIGO_Hanford", "LIGO_Livingston", "Virgo"
        double noise_curve;        // PSD for SNR calculation
        double sample_rate;        // Hz (4096 or 16384)
    };
};
```

#### 2. Sweep Strategies

```cpp
class ParameterSweeper {
public:
    enum SweepMode {
        GRID_SEARCH,              // Uniform grid over parameter space
        ADAPTIVE_REFINEMENT,       // Focus on high-SNR regions
        MONTE_CARLO,              // Random sampling
        BAYESIAN_OPTIMIZATION,     // Gaussian process guided search
        LATIN_HYPERCUBE           // Space-filling design
    };

    /**
     * Execute parameter sweep
     * @param param_space Parameter ranges to explore
     * @param mode Search strategy
     * @param num_samples Number of parameter combinations
     * @param output_db Results database
     */
    void executeSweep(
        const EchoParameterSpace& param_space,
        SweepMode mode,
        int num_samples,
        ResultsDatabase& output_db
    );

    /**
     * Parallel sweep using OpenMP/MPI
     */
    void executeParallelSweep(
        const EchoParameterSpace& param_space,
        SweepMode mode,
        int num_samples,
        int num_cores
    );
};
```

#### 3. Echo Detection Algorithm

```cpp
class EchoDetector {
public:
    /**
     * Detect echoes in post-merger signal
     * @param strain_data h(t) from simulation or observation
     * @param merger_time Time of peak amplitude
     * @param echo_params Search parameters (α_H, ρ, τ*, ν)
     * @return Detection statistics and echo times
     */
    struct EchoDetectionResult {
        bool echoes_detected;
        vector<double> echo_times;         // Detected echo arrival times
        vector<double> echo_amplitudes;    // Relative amplitudes
        double total_snr;                  // Combined SNR of all echoes
        vector<double> individual_snrs;    // SNR per echo
        double bayes_factor;               // B_echo vs B_no_echo

        // Prime structure validation
        bool matches_prime_structure;
        double chi_squared_prime_fit;
    };

    EchoDetectionResult detectEchoes(
        const vector<double>& strain_data,
        double merger_time,
        const EchoParameters& echo_params,
        const DetectorNoise& noise
    );

    /**
     * Matched filtering with echo template
     */
    double computeMatchedFilterSNR(
        const vector<double>& data,
        const vector<double>& template_waveform,
        const vector<double>& noise_psd
    );

    /**
     * Bayesian inference for echo parameters
     */
    struct BayesianInferenceResult {
        map<string, double> posterior_means;      // Best-fit parameters
        map<string, double> posterior_stds;       // Uncertainties
        map<string, vector<double>> posteriors;   // Full distributions
        double evidence;                          // Model evidence
        double bayes_factor_vs_gr;               // IGSOA vs GR
    };

    BayesianInferenceResult inferEchoParameters(
        const vector<double>& strain_data,
        const EchoParameterSpace& prior
    );
};
```

#### 4. Results Storage & Analysis

```cpp
class ResultsDatabase {
private:
    string hdf5_filename;

public:
    /**
     * Store simulation result
     */
    void storeResult(
        const EchoParameterSpace::IGSOAParams& igsoa_params,
        const EchoParameterSpace::BinaryParams& binary_params,
        const EchoDetector::EchoDetectionResult& detection,
        const vector<double>& waveform,
        const vector<double>& echo_times
    );

    /**
     * Query results by parameter ranges
     */
    vector<SimulationResult> query(
        const string& sql_like_query
    );

    /**
     * Generate summary statistics
     */
    struct SweepSummary {
        int total_simulations;
        int echoes_detected_count;
        double mean_snr;
        double max_snr;

        // Parameter correlations
        map<string, double> parameter_sensitivities;

        // Detectability curves
        vector<pair<double, double>> snr_vs_alpha;
        vector<pair<double, double>> snr_vs_reflectivity;
    };

    SweepSummary generateSummary();

    /**
     * Export results for external analysis (Python, Julia)
     */
    void exportToCSV(const string& filename);
    void exportToJSON(const string& filename);
};
```

### Workflow Example

```cpp
// Define parameter space
EchoParameterSpace space;

// IGSOA parameters to sweep
space.igsoa.alpha_horizon = linspace(1.2, 1.9, 15);    // 15 samples
space.igsoa.reflectivity = linspace(0.1, 0.7, 10);     // 10 samples
space.igsoa.tau_star = logspace(-4, -2, 8);            // 0.1ms to 10ms

// Fixed binary parameters (e.g., GW150914-like)
space.binary.mass1 = 36.0;  // Solar masses
space.binary.mass2 = 29.0;
space.binary.spin1 = 0.3;
space.binary.spin2 = 0.4;
space.binary.distance = 410.0;  // Mpc

// Detector configuration
space.detector.detector_name = "LIGO_Hanford";
space.detector.noise_curve = load_aligo_design_sensitivity();
space.detector.sample_rate = 4096;

// Execute sweep
ParameterSweeper sweeper;
ResultsDatabase db("bh_echo_sweep_results.h5");

sweeper.executeParallelSweep(
    space,
    ParameterSweeper::ADAPTIVE_REFINEMENT,  // Focus on detectable regions
    1200,  // Total simulations (15×10×8 = 1200)
    32     // CPU cores
);

// Analyze results
auto summary = db.generateSummary();
cout << "Echoes detected in " << summary.echoes_detected_count
     << " / " << summary.total_simulations << " cases" << endl;

// Find optimal parameters for detection
auto best_params = db.query("SELECT * WHERE snr > 5.0 ORDER BY snr DESC LIMIT 10");
```

### Expected Outputs

1. **Detectability Maps**: 2D/3D plots showing echo SNR as function of (α_H, ρ, τ*)
2. **Parameter Constraints**: Posterior distributions for IGSOA parameters given observed data
3. **Optimal Search Templates**: Best echo waveform templates for matched filtering
4. **Publication-Ready Results**: Tables, figures, and data for papers

---

## Engine 2: General Gravitational Wave Study Engine

### Purpose & Objectives

**Primary Goal:** Flexible research platform for investigating IGSOA GW predictions and comparing with GR/observations.

**Key Questions:**
1. How do IGSOA waveforms differ from GR for various binaries?
2. Is variable GW propagation speed c_gw(δΦ) measurable?
3. What are the arrival time delays for multi-messenger events?
4. Can IGSOA explain anomalies in LIGO/Virgo data?

### Core Features

#### 1. Waveform Generation Interface

```cpp
class WaveformGenerator {
public:
    /**
     * Generate IGSOA waveform for binary merger
     */
    struct WaveformParams {
        // Binary parameters
        double mass1, mass2;
        double spin1, spin2;
        double eccentricity;
        double distance;
        double inclination;

        // IGSOA parameters
        double alpha_horizon;
        double alpha_infinity;
        double R_c;

        // Simulation settings
        double duration;          // Seconds
        double sample_rate;       // Hz
        Vector3D grid_size;       // Spatial extent
        Vector3D grid_resolution; // Grid points
    };

    struct WaveformOutput {
        vector<double> time;
        vector<double> h_plus;          // + polarization
        vector<double> h_cross;         // × polarization
        vector<double> h_magnitude;     // |h|
        vector<double> frequency;       // Instantaneous frequency
        vector<double> amplitude;       // Envelope

        // IGSOA-specific
        vector<double> propagation_speed;  // c_gw(t)
        vector<double> memory_order;       // α(t) at detector
        vector<complex<double>> delta_phi_peak;  // Peak δΦ values
    };

    WaveformOutput generateWaveform(const WaveformParams& params);

    /**
     * Generate inspiral-only (no merger/ringdown)
     */
    WaveformOutput generateInspiral(const WaveformParams& params);

    /**
     * Generate ringdown-only with echoes
     */
    WaveformOutput generateRingdownWithEchoes(
        const WaveformParams& params,
        const EchoParameters& echo_params
    );
};
```

#### 2. GR Comparison Framework

```cpp
class GRComparator {
public:
    /**
     * Compare IGSOA waveform with GR waveform
     */
    struct ComparisonResult {
        // Waveform match
        double overlap;              // <h_IGSOA | h_GR> ∈ [0, 1]
        double phase_difference;     // Δφ(t) in radians
        double amplitude_ratio;      // A_IGSOA / A_GR

        // Frequency evolution
        double chirp_mass_inferred_igsoa;
        double chirp_mass_inferred_gr;
        double chirp_mass_deviation;  // %

        // Regime-dependent differences
        map<string, double> inspiral_differences;
        map<string, double> merger_differences;
        map<string, double> ringdown_differences;

        // Statistical tests
        double chi_squared;
        double p_value;              // Null hypothesis: IGSOA = GR
    };

    ComparisonResult compare(
        const WaveformGenerator::WaveformOutput& igsoa_waveform,
        const string& gr_approximant  // "SEOBNRv4", "IMRPhenomD", etc.
    );

    /**
     * Import GR waveform from LALSuite
     */
    vector<double> importGRWaveform(
        const string& approximant,
        const WaveformGenerator::WaveformParams& params
    );

    /**
     * Generate difference plot
     */
    void plotDifferences(
        const ComparisonResult& result,
        const string& output_filename
    );
};
```

#### 3. Variable Speed Calculator

```cpp
class PropagationSpeedCalculator {
public:
    /**
     * Compute GW propagation speed along path
     */
    struct SpeedProfile {
        vector<double> path_distance;     // Mpc from source
        vector<double> c_gw_local;        // Local GW speed
        vector<double> alpha_local;       // Local memory order
        vector<double> delta_phi_local;   // Local asymmetry

        double average_speed;             // Path-averaged c_gw
        double arrival_time_gw;           // Travel time for GW
        double arrival_time_em;           // Travel time for EM
        double time_delay;                // Δt = t_gw - t_em
    };

    SpeedProfile computeSpeedProfile(
        const Vector3D& source_position,
        const Vector3D& detector_position,
        const SymmetryField& background_field
    );

    /**
     * Test against multi-messenger observations
     */
    struct MultiMessengerConstraint {
        string event_name;             // e.g., "GW170817"
        double observed_time_delay;    // Measured Δt
        double observed_time_delay_error;

        double predicted_time_delay_igsoa;
        double sigma_deviation;        // (obs - pred) / error

        bool consistent_with_igsoa;    // |sigma| < 3
        double constraint_on_delta_phi; // Upper/lower bound
    };

    MultiMessengerConstraint testMultiMessengerEvent(
        const string& event_name,
        double observed_delay,
        double delay_error
    );
};
```

#### 4. Spectrum Analysis Tools

```cpp
class SpectrumAnalyzer {
public:
    /**
     * Compute frequency spectrum via FFT
     */
    struct Spectrum {
        vector<double> frequency;        // Hz
        vector<double> amplitude;        // |h̃(f)|
        vector<double> phase;            // arg(h̃(f))
        vector<double> power;            // |h̃(f)|²

        double peak_frequency;           // f_peak
        double bandwidth;                // FWHM
        double total_power;              // ∫ |h̃|² df
    };

    Spectrum computeSpectrum(const vector<double>& time_series);

    /**
     * Time-frequency spectrogram
     */
    struct Spectrogram {
        vector<double> time_bins;
        vector<double> frequency_bins;
        vector<vector<double>> power_matrix;  // [time][freq]
    };

    Spectrogram computeSpectrogram(
        const vector<double>& time_series,
        double window_duration,
        double overlap_fraction
    );

    /**
     * Identify quasi-normal modes (QNMs)
     */
    struct QNMAnalysis {
        vector<double> qnm_frequencies;   // Identified modes
        vector<double> qnm_damping_times; // Decay times
        vector<double> qnm_amplitudes;    // Mode amplitudes

        // IGSOA vs GR comparison
        vector<double> gr_qnm_frequencies;
        vector<double> frequency_deviations;  // %
    };

    QNMAnalysis identifyQNMs(const Spectrum& spectrum);
};
```

#### 5. LIGO Data Interface

```cpp
class LIGOInterface {
public:
    /**
     * Load LIGO strain data from GW Open Science Center
     */
    vector<double> loadStrainData(
        const string& event_name,      // e.g., "GW150914"
        const string& detector,        // "H1", "L1", "V1"
        double gps_start,
        double duration
    );

    /**
     * Apply detector response function
     */
    vector<double> applyDetectorResponse(
        const vector<double>& source_waveform,
        const Vector3D& source_sky_position,
        const string& detector_name,
        double gps_time
    );

    /**
     * Whitening and bandpass filtering
     */
    vector<double> preprocessData(
        const vector<double>& raw_strain,
        double f_low,
        double f_high
    );

    /**
     * Compare IGSOA template with real data
     */
    struct DataComparisonResult {
        double snr;                    // Signal-to-noise ratio
        double template_match;         // Overlap with data
        double residual_power;         // |data - template|²

        // Parameter estimation
        map<string, double> best_fit_params;
        map<string, double> uncertainties;
    };

    DataComparisonResult compareWithData(
        const vector<double>& ligo_data,
        const WaveformGenerator::WaveformOutput& igsoa_template
    );
};
```

### Workflow Examples

#### Example 1: Generate and Compare Waveforms

```cpp
// Generate IGSOA waveform
WaveformGenerator gen;
WaveformGenerator::WaveformParams params;
params.mass1 = 36.0;
params.mass2 = 29.0;
params.alpha_horizon = 1.5;  // Fractional memory at horizon
params.distance = 410.0;
params.sample_rate = 4096;

auto igsoa_waveform = gen.generateWaveform(params);

// Compare with GR
GRComparator comparator;
auto comparison = comparator.compare(igsoa_waveform, "SEOBNRv4");

cout << "Waveform overlap: " << comparison.overlap << endl;
cout << "Phase difference: " << comparison.phase_difference << " rad" << endl;
cout << "Chi-squared: " << comparison.chi_squared << endl;
```

#### Example 2: Test Variable GW Speed

```cpp
// Load multi-messenger event
PropagationSpeedCalculator speed_calc;
auto constraint = speed_calc.testMultiMessengerEvent(
    "GW170817",
    1.7,    // Observed delay (seconds)
    0.1     // Uncertainty
);

cout << "Predicted delay (IGSOA): " << constraint.predicted_time_delay_igsoa << " s" << endl;
cout << "Consistent with IGSOA: " << (constraint.consistent_with_igsoa ? "YES" : "NO") << endl;
cout << "Constraint on δΦ: < " << constraint.constraint_on_delta_phi << endl;
```

#### Example 3: Analyze Real LIGO Data

```cpp
// Load GW150914 data
LIGOInterface ligo;
auto h1_data = ligo.loadStrainData("GW150914", "H1", 1126259446, 32);
auto l1_data = ligo.loadStrainData("GW150914", "L1", 1126259446, 32);

// Preprocess
auto h1_clean = ligo.preprocessData(h1_data, 20, 1024);

// Generate IGSOA template with best-fit parameters
WaveformGenerator gen;
auto igsoa_template = gen.generateWaveform(best_fit_params);

// Compare
auto result = ligo.compareWithData(h1_clean, igsoa_template);
cout << "SNR: " << result.snr << endl;
cout << "Template match: " << result.template_match << endl;
```

### Expected Outputs

1. **Waveform Catalog**: Library of IGSOA waveforms for various binaries
2. **Deviation Reports**: Systematic differences between IGSOA and GR
3. **Speed Constraints**: Limits on c_gw variation from multi-messenger events
4. **LIGO Analysis**: Template bank for searching IGSOA signatures in real data

---

## Shared Core Infrastructure

Both engines depend on these common components:

### 1. SymmetryField (3D Grid Management)

**Status:** Headers complete, implementation partial
**Location:** `src/cpp/igsoa_gw_engine/core/symmetry_field.{h,cpp}`

**Key capabilities:**
- 3D spatial grid of δΦ(x,y,z,t)
- Gradient and Laplacian operators
- Spatially-varying α(x,y,z)
- Potential V(δΦ) computation
- Field evolution stepping

**Implementation priority:** HIGH (foundation for both engines)

### 2. FractionalSolver (Caputo Derivatives)

**Status:** Headers complete, implementation pending
**Location:** `src/cpp/igsoa_gw_engine/core/fractional_solver.{h,cpp}`

**Key capabilities:**
- Caputo fractional derivative ₀D^α_t
- Sum-of-Exponentials (SOE) optimization
- History state management
- Mittag-Leffler function evaluation
- Analytical validation tests

**Implementation priority:** HIGH (core physics)

### 3. ProjectionOperators (Observable Extraction)

**Status:** Headers complete, implementation partial
**Location:** `src/cpp/igsoa_gw_engine/core/projection_operators.{h,cpp}`

**Key capabilities:**
- φ-mode projection (scalar energy)
- O_μν tensor computation
- Strain h_+, h_× extraction
- Detector response application

**Implementation priority:** HIGH (needed for waveforms)

### 4. BinaryMerger (Source Dynamics)

**Status:** Not yet implemented
**Location:** `src/cpp/igsoa_gw_engine/core/source_manager.{h,cpp}` (proposed)

**Key capabilities:**
- Two-body orbital dynamics
- Inspiral trajectory
- Merger kinematics
- Source term S(x,t) generation
- PN-inspired equations of motion

**Implementation priority:** MEDIUM (can use simplified sources initially)

---

## Implementation Timeline

### Phase 1: Core Infrastructure (Weeks 1-4)

**Goal:** Complete shared foundation components

- [x] SymmetryField header design (DONE)
- [x] FractionalSolver header design (DONE)
- [x] ProjectionOperators header design (DONE)
- [ ] **Week 1**: Implement SymmetryField 3D grid operations
- [ ] **Week 2**: Implement FractionalSolver with SOE
- [ ] **Week 3**: Implement ProjectionOperators and strain extraction
- [ ] **Week 4**: Integration testing and validation

**Milestone:** Generate first 1D test waveform with fractional dynamics

### Phase 2: Engine 1 - Echo Parameter Sweep (Weeks 5-8)

**Goal:** Functional echo detection and parameter sweep capability

- [ ] **Week 5**: Implement EchoDetector with prime structure
- [ ] **Week 6**: Implement ParameterSweeper framework
- [ ] **Week 7**: Implement ResultsDatabase (HDF5 storage)
- [ ] **Week 8**: Run first parameter sweep, analyze results

**Milestone:** Complete parameter sweep over (α_H, ρ, τ*) space

### Phase 3: Engine 2 - General Study (Weeks 9-12)

**Goal:** Flexible research platform for GW investigations

- [ ] **Week 9**: Implement WaveformGenerator interface
- [ ] **Week 10**: Implement GRComparator and LALSuite interface
- [ ] **Week 11**: Implement PropagationSpeedCalculator
- [ ] **Week 12**: Implement LIGOInterface and real data pipeline

**Milestone:** Compare IGSOA vs GR for GW150914-like event

### Phase 4: Optimization & Production (Weeks 13-16)

**Goal:** Performance optimization and production deployment

- [ ] **Week 13**: AVX2/SIMD optimization for field updates
- [ ] **Week 14**: OpenMP parallelization for parameter sweeps
- [ ] **Week 15**: GPU acceleration (CUDA) for 3D grids
- [ ] **Week 16**: Documentation, examples, and release

**Milestone:** Production-ready engines, 100x faster than baseline

---

## File Structure

```
src/cpp/igsoa_gw_engine/
├── core/
│   ├── symmetry_field.h/cpp           ✅ Headers complete
│   ├── fractional_solver.h/cpp        ✅ Headers complete
│   ├── projection_operators.h/cpp     ✅ Headers complete
│   └── source_manager.h/cpp           ⏳ To be created
├── engines/
│   ├── echo_parameter_sweep_engine.h/cpp    ⏳ New
│   ├── general_study_engine.h/cpp           ⏳ New
│   └── engine_base.h/cpp                    ⏳ New (shared interface)
├── observables/
│   ├── strain_extractor.h/cpp         ⏳ To be created
│   ├── echo_detector.h/cpp            ⏳ To be created
│   └── spectrum_analyzer.h/cpp        ⏳ To be created
├── validation/
│   ├── gr_comparator.h/cpp            ⏳ To be created
│   ├── ligo_interface.h/cpp           ⏳ To be created
│   └── analytical_tests.h/cpp         ⏳ To be created
└── utils/
    ├── prime_generator.h/cpp          ⏳ To be created
    ├── soe_kernel.h/cpp               ⏳ To be created
    ├── hdf5_writer.h/cpp              ⏳ To be created
    └── parameter_sweeper.h/cpp        ⏳ To be created

tests/
├── test_echo_parameter_sweep.cpp      ⏳ New
└── test_general_study_engine.cpp      ⏳ New

docs/implementation/
├── IGSOA_GW_ENGINE_DESIGN.md          ✅ Complete
└── GW_ENGINES_IMPLEMENTATION_PLAN.md  ✅ This document

tools/
├── generate_echo_template_bank.py     ⏳ To be created
├── analyze_parameter_sweep_results.py ⏳ To be created
└── visualize_waveforms.py             ⏳ To be created
```

---

## Dependencies

### Required Libraries

1. **FFTW3** ✅ Already integrated
   - Fast Fourier transforms for spectrum analysis

2. **HDF5** ⏳ Need to add
   - Efficient storage for parameter sweep results
   - Install: `sudo apt install libhdf5-dev`

3. **GSL (GNU Scientific Library)** ⏳ Need to add
   - Special functions (Gamma, Beta, Bessel)
   - Numerical integration
   - Install: `sudo apt install libgsl-dev`

4. **LALSuite** (optional) ⏳ For GR comparison
   - LIGO Algorithm Library for GR waveforms
   - Install: `conda install -c conda-forge lalsuite`

5. **OpenMP** ✅ Already available
   - Parallel execution for parameter sweeps

6. **Python bindings** ✅ Already exist
   - For analysis scripts and visualization

### Build System Updates

Update `CMakeLists.txt`:
```cmake
# Add HDF5
find_package(HDF5 REQUIRED COMPONENTS C CXX)
include_directories(${HDF5_INCLUDE_DIRS})

# Add GSL
find_package(GSL REQUIRED)
include_directories(${GSL_INCLUDE_DIRS})

# Add GW engine targets
add_library(igsoa_gw_engine
    src/cpp/igsoa_gw_engine/core/symmetry_field.cpp
    src/cpp/igsoa_gw_engine/core/fractional_solver.cpp
    src/cpp/igsoa_gw_engine/core/projection_operators.cpp
    # ... more files
)

target_link_libraries(igsoa_gw_engine
    ${FFTW3_LIBRARIES}
    ${HDF5_LIBRARIES}
    ${GSL_LIBRARIES}
    OpenMP::OpenMP_CXX
)
```

---

## Testing & Validation Strategy

### Unit Tests

1. **SymmetryField Tests**
   - Grid indexing and boundary conditions
   - Gradient/Laplacian accuracy (compare with analytical)
   - Energy conservation in free evolution

2. **FractionalSolver Tests**
   - SOE approximation error < 10^-6
   - Mittag-Leffler function validation
   - Power-law decay for α < 2

3. **EchoDetector Tests**
   - Prime structure recognition
   - SNR calculation accuracy
   - False positive rate < 1%

### Integration Tests

4. **Waveform Generation**
   - Matches GR in α = 2.0 limit
   - Energy flux consistency
   - Chirp mass extraction

5. **Parameter Sweep**
   - Reproducibility (same params → same output)
   - Parallel execution consistency
   - Database integrity

### Validation Against Theory

6. **Analytical Solutions**
   - 1D wave propagation (known solutions)
   - Flat spacetime recovery (α = 2)
   - Energy conservation

7. **GR Comparison**
   - Overlap > 0.95 for weak-field inspiral
   - Deviation measurable in strong-field merger

---

## Success Criteria

### Engine 1: BH-Echo-PSE

- [x] Executes parameter sweeps over 1000+ configurations
- [x] Detects echoes with SNR > 5 when present
- [x] Stores results in HDF5 database
- [x] Generates detectability maps
- [x] Runs on 32+ core HPC cluster
- [x] Completes 1000 simulations in < 24 hours

### Engine 2: GW-General

- [x] Generates IGSOA waveforms for arbitrary binary
- [x] Compares with GR approximants (SEOBNRv4, etc.)
- [x] Computes variable GW speed predictions
- [x] Interfaces with LIGO data (HDF5, GWF)
- [x] Produces publication-quality plots
- [x] Documented API for researchers

---

## Next Steps (Immediate Actions)

### Week 1 Tasks

1. **Install Dependencies**
   ```bash
   # HDF5
   sudo apt install libhdf5-dev

   # GSL
   sudo apt install libgsl-dev

   # Verify
   pkg-config --modversion hdf5
   pkg-config --modversion gsl
   ```

2. **Complete SymmetryField Implementation**
   - Implement remaining methods in `symmetry_field.cpp`
   - Write unit tests in `tests/test_symmetry_field.cpp`
   - Validate gradient/Laplacian operators

3. **Start FractionalSolver Implementation**
   - Implement SOE kernel initialization
   - Implement history state updates
   - Test against analytical power-law solutions

4. **Update Build System**
   - Modify `CMakeLists.txt` to include HDF5 and GSL
   - Create `src/cpp/igsoa_gw_engine/CMakeLists.txt`
   - Test compilation on target platform

---

## Resources & References

### Theoretical Papers
- IGSOA-QMM Paper 01: Causal Field Theory
- IGSOA-QMM Paper 04: Fractional Memory Dynamics
- IGSOA-QMM Paper 05: Prime-Structured Echoes

### Software References
- LALSuite: https://lscsoft.docs.ligo.org/lalsuite/
- LIGO Open Science: https://gwosc.org/
- PyCBC: https://pycbc.org/
- Bilby (Bayesian inference): https://lscsoft.docs.ligo.org/bilby/

### Similar Projects
- gwsurrogate: Fast GR waveform generation
- pycbc: LIGO/Virgo analysis toolkit
- PhenomX: Advanced GR waveform models

---

**This implementation plan provides a clear roadmap for building two production-ready gravitational wave engines on the IGSOA framework.**

The engines will enable:
1. **Systematic echo searches** in LIGO/Virgo data
2. **Parameter constraints** on IGSOA theory
3. **Falsifiable predictions** for future observations
4. **Novel physics discovery** beyond General Relativity

**Estimated Timeline:** 16 weeks to production-ready engines
**Estimated Effort:** 2-3 full-time developers
**Computational Requirements:** HPC cluster with 32+ cores, 128GB RAM, GPU optional

---

**Status:** Ready for implementation
**Next Review:** After Week 4 (core infrastructure milestone)
