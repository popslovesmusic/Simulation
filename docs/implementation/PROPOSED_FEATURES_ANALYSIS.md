# Proposed Features Analysis & Recommendations

**Date:** 2025-11-11
**Source:** `docs/proposed-features.txt`
**Status:** 📊 **ANALYSIS COMPLETE**

---

## Executive Summary

The proposed 12-feature cache & automation system represents a **comprehensive acceleration framework** that aligns well with **Phase 2 (ML Surrogate & Acceleration)** of the project roadmap.

**Key Findings:**
- ✅ **3 features already partially implemented** (runtime caching)
- ✅ **5 features ready for implementation** (infrastructure exists)
- ⚠️ **4 features require significant new infrastructure**
- 🎯 **Estimated 50-80% speedup** for repeated missions

**Recommendation:** Implement in **3 phases** over 6-8 weeks, prioritizing high-impact, low-risk features first.

---

## Feature Assessment Matrix

| # | Feature | Status | Impact | Effort | Risk | Priority |
|---|---------|--------|--------|--------|------|----------|
| 1 | Fractional Kernel Cache | 🟡 Partial | **HIGH** | Medium | Low | **P1** |
| 2 | Laplacian Stencil Cache | ⚪ New | High | Low | Low | **P1** |
| 3 | FFTW Wisdom Store | 🟢 Ready | **HIGH** | **Low** | Low | **P0** |
| 4 | Prime-Gap Echo Templates | ⚪ New | Medium | Medium | Low | P2 |
| 5 | Initial-State Profile Cache | ⚪ New | Medium | Low | Low | **P1** |
| 6 | Source Map Cache | ⚪ New | Low | Low | Low | P2 |
| 7 | Mission Graph Cache | ⚪ New | **HIGH** | **High** | **High** | P3 |
| 8 | Surrogate Response Library | 🟡 Partial | **HIGH** | Medium | Medium | **P1** |
| 9 | Validation Loop | ⚪ New | Medium | High | Medium | P3 |
| 10 | Governance Agent | ⚪ New | Low | **High** | High | P4 |
| 11 | Cache I/O Interface | ⚪ New | **HIGH** | Medium | Low | **P0** |
| 12 | Hybrid Mission Mode | ⚪ New | **HIGH** | High | Medium | P2 |

**Legend:**
- 🟢 Ready: Infrastructure exists, low effort
- 🟡 Partial: Some components exist, needs extension
- ⚪ New: Requires new infrastructure

---

## Current State Assessment

### ✅ Already Implemented (Runtime Only)

**Feature 1: Fractional Kernel Cache** (Partial)
- **Current:** `src/cpp/kernel_cache.h` - Runtime in-memory cache
- **Exists:** KernelCache, KernelCacheManager, tiered evaluation
- **Missing:** Persistent storage across missions
- **Code:**
  ```cpp
  class KernelCache {
      std::vector<double> cached_values_;  // 1024 bins
      double R_c_;
      inline double lookup(double distance) const;
  };
  ```

**Feature 2: Neighbor Cache** (Runtime)
- **Current:** `src/cpp/neighbor_cache.h` - Pre-computed neighbor lists
- **Exists:** NeighborCache2D, spatial hashing, weight pre-computation
- **Missing:** Persistent storage

**Feature 8: Surrogate Response Library** (Partial)
- **Current:** `backend/engine/surrogate_adapter.py`, `igsoa_analysis/surrogates/`
- **Exists:** SurrogateAdapter, FeedForwardSurrogate, benchmarking
- **Missing:** Production-trained models, library management
- **Status:** Infrastructure ready, awaiting training data (see GOOGLE_COLAB_TRAINING_PLAN.md)

---

## Detailed Feature Analysis

### 🔥 **P0: Critical Foundation (Week 1)**

#### Feature 11: Unified Cache I/O Interface ⭐

**Impact:** Enables all other cache features
**Effort:** 2-3 days
**Risk:** Low

**Design:**
```python
# cache_manager.py
class CacheManager:
    def __init__(self, root: Path = Path("./cache")):
        self.root = root
        self.backends = {
            "fractional_kernels": FilesystemBackend(root / "fractional_kernels"),
            "stencils": FilesystemBackend(root / "stencils"),
            "fftw_wisdom": BinaryBackend(root / "fftw_wisdom"),
            "surrogates": ModelBackend(root / "surrogates")
        }

    def save(self, category: str, key: str, data: Any) -> Path:
        """Store data with automatic serialization."""
        backend = self.backends[category]
        return backend.save(key, data)

    def load(self, category: str, key: str) -> Any:
        """Load and deserialize data."""
        backend = self.backends[category]
        return backend.load(key)

    def exists(self, category: str, key: str) -> bool:
        """Check if cached entry exists."""
        return self.backends[category].exists(key)
```

**Storage Backends:**
1. **FilesystemBackend** - JSON + NumPy arrays (default)
2. **LMDBBackend** - Fast key-value store (optional)
3. **ModelBackend** - PyTorch .pt files with metadata

**Directory Structure:**
```
cache/
├── fractional_kernels/
│   ├── kernel_1.5_0.01_1000.npz
│   ├── kernel_1.8_0.005_500.npz
│   └── index.json
├── stencils/
│   ├── laplacian_2d_64_64.npz
│   └── index.json
├── fftw_wisdom/
│   ├── wisdom_64_64_1.dat
│   └── index.json
└── surrogates/
    ├── waveform_v1.pt
    ├── waveform_v1_metadata.json
    └── index.json
```

---

#### Feature 3: FFTW Wisdom Store ⭐

**Impact:** HIGH (10-30% FFT speedup)
**Effort:** 1 day
**Risk:** Low
**Prerequisites:** Feature 11

**Current Status:**
- `fftw3.h` present in codebase
- FFTW already used in GW engines
- No wisdom persistence

**Implementation:**
```cpp
// fftw_wisdom_manager.h
namespace dase {
namespace fftw {

class WisdomManager {
private:
    std::string wisdom_dir_;

public:
    WisdomManager(const std::string& dir = "./cache/fftw_wisdom")
        : wisdom_dir_(dir) {}

    // Load wisdom file or create if missing
    bool loadOrCreate(int Nx, int Ny, int Nz) {
        std::string filename = wisdomFilename(Nx, Ny, Nz);

        if (std::ifstream(filename).good()) {
            // Load existing wisdom
            return fftw_import_wisdom_from_filename(filename.c_str()) != 0;
        } else {
            // Create wisdom by planning and timing
            createWisdom(Nx, Ny, Nz);
            return fftw_export_wisdom_to_filename(filename.c_str()) != 0;
        }
    }

private:
    std::string wisdomFilename(int Nx, int Ny, int Nz) const {
        char cpu_model[128];
        getCPUModel(cpu_model);  // Read from /proc/cpuinfo or CPUID

        std::ostringstream oss;
        oss << wisdom_dir_ << "/fftw_"
            << Nx << "_" << Ny << "_" << Nz
            << "_" << cpu_model << ".dat";
        return oss.str();
    }

    void createWisdom(int Nx, int Ny, int Nz) {
        // Allocate dummy arrays
        fftw_complex *in = fftw_alloc_complex(Nx * Ny * Nz);
        fftw_complex *out = fftw_alloc_complex(Nx * Ny * Nz);

        // Create plan with FFTW_PATIENT or FFTW_MEASURE
        fftw_plan plan = fftw_plan_dft_3d(
            Nx, Ny, Nz, in, out, FFTW_FORWARD, FFTW_PATIENT
        );

        // Wisdom is now stored in FFTW's internal state
        fftw_destroy_plan(plan);
        fftw_free(in);
        fftw_free(out);
    }
};

}} // namespace dase::fftw
```

**Integration Point:**
```cpp
// In IGSOA GW engine initialization
dase::fftw::WisdomManager wisdom_mgr;
wisdom_mgr.loadOrCreate(grid_nx, grid_ny, grid_nz);
// Now create FFT plans - they'll use optimized wisdom
```

**Benefit:** First run takes 1-5 seconds to create wisdom, all subsequent runs use optimized plans instantly.

---

### 🚀 **P1: High-Impact Cache Features (Weeks 2-3)**

#### Feature 1: Persistent Fractional Kernel Cache

**Impact:** HIGH (50-80% speedup for fractional engines)
**Effort:** 3-4 days
**Prerequisites:** Feature 11

**Current Code:** `src/cpp/kernel_cache.h` (runtime only)

**Enhancement:**
```cpp
// fractional_kernel_cache.h
namespace dase {
namespace cache {

struct FractionalKernelKey {
    double alpha;
    double dt;
    int num_steps;

    std::string to_string() const {
        std::ostringstream oss;
        oss << "fractional_kernel_"
            << alpha << "_" << dt << "_" << num_steps;
        return oss.str();
    }
};

class PersistentFractionalKernelCache {
private:
    std::string cache_dir_;
    std::map<std::string, std::vector<double>> memory_cache_;

public:
    // Try to load from disk, compute if missing
    std::vector<double> getOrCompute(const FractionalKernelKey& key) {
        std::string cache_key = key.to_string();

        // Check memory cache
        auto it = memory_cache_.find(cache_key);
        if (it != memory_cache_.end()) {
            return it->second;
        }

        // Check disk cache
        std::string filename = cache_dir_ + "/" + cache_key + ".npz";
        if (fileExists(filename)) {
            std::vector<double> coeffs = loadFromDisk(filename);
            memory_cache_[cache_key] = coeffs;
            return coeffs;
        }

        // Compute and cache
        std::vector<double> coeffs = computeSOECoefficients(
            key.alpha, key.dt, key.num_steps
        );
        saveToDisk(filename, coeffs);
        memory_cache_[cache_key] = coeffs;
        return coeffs;
    }

private:
    std::vector<double> computeSOECoefficients(
        double alpha, double dt, int num_steps
    ) {
        // Compute Caputo/SOE fractional derivative weights
        // This is the expensive operation we want to cache
        std::vector<double> weights(num_steps);

        // Caputo formula: w_k = (k^(1-α) - (k-1)^(1-α)) / Γ(2-α)
        double gamma_factor = 1.0 / std::tgamma(2.0 - alpha);

        for (int k = 0; k < num_steps; ++k) {
            double k_term = std::pow(k + 1.0, 1.0 - alpha);
            double k_prev = (k > 0) ? std::pow(k, 1.0 - alpha) : 0.0;
            weights[k] = (k_term - k_prev) * gamma_factor;
        }

        return weights;
    }

    void saveToDisk(const std::string& filename,
                    const std::vector<double>& data) {
        // Use NumPy .npz format or simple binary
        std::ofstream file(filename, std::ios::binary);
        size_t size = data.size();
        file.write(reinterpret_cast<const char*>(&size), sizeof(size));
        file.write(reinterpret_cast<const char*>(data.data()),
                   size * sizeof(double));
    }
};

}} // namespace dase::cache
```

**Python Bridge:**
```python
# cache_manager.py extension
class FractionalKernelBackend:
    def save(self, key: str, coeffs: np.ndarray) -> Path:
        path = self.root / f"{key}.npz"
        np.savez_compressed(path, coefficients=coeffs)
        return path

    def load(self, key: str) -> np.ndarray:
        path = self.root / f"{key}.npz"
        return np.load(path)['coefficients']
```

---

#### Feature 2: Laplacian Stencil Cache

**Impact:** High (zero recomputation for repeated grids)
**Effort:** 2 days
**Prerequisites:** Feature 11

**Implementation:**
```python
# stencil_cache.py
class LaplacianStencilCache:
    def __init__(self, cache_mgr: CacheManager):
        self.cache = cache_mgr

    def get_or_compute_2d(self, Nx: int, Ny: int,
                          boundary: str = "periodic") -> np.ndarray:
        key = f"laplacian_2d_{Nx}_{Ny}_{boundary}"

        if self.cache.exists("stencils", key):
            return self.cache.load("stencils", key)

        # Compute Laplacian stencil (sparse matrix or FFT kernel)
        if Nx * Ny < 10000:
            # Small grid: Use sparse matrix
            stencil = self._build_sparse_laplacian_2d(Nx, Ny, boundary)
        else:
            # Large grid: Use FFT-based approach
            stencil = self._build_fft_laplacian_2d(Nx, Ny)

        self.cache.save("stencils", key, stencil)
        return stencil

    def _build_sparse_laplacian_2d(self, Nx, Ny, boundary):
        from scipy.sparse import diags, kron

        # 1D Laplacian
        diag_1d = diags([-2, 1, 1], [0, -1, 1], shape=(Nx, Nx))

        if boundary == "periodic":
            diag_1d[0, -1] = 1
            diag_1d[-1, 0] = 1

        # 2D Laplacian via Kronecker product
        I = diags([1], [0], shape=(Ny, Ny))
        laplacian = kron(I, diag_1d) + kron(diag_1d, I)

        return laplacian
```

---

#### Feature 5: Initial-State Profile Cache

**Impact:** Medium-High (fast mission startup)
**Effort:** 1-2 days
**Prerequisites:** Feature 11

**Implementation:**
```cpp
// state_profile_cache.h
namespace dase {
namespace cache {

enum class ProfileType {
    GAUSSIAN,
    SOLITON,
    SPHERICAL_SHELL,
    PLANE_WAVE
};

struct ProfileKey {
    ProfileType type;
    double amplitude;
    double width;  // sigma for Gaussian
    int Nx, Ny, Nz;

    std::string to_string() const;
};

class StateProfileCache {
public:
    // Get cached profile or generate
    std::vector<std::complex<double>> getOrGenerate(const ProfileKey& key) {
        std::string cache_key = key.to_string();

        if (existsOnDisk(cache_key)) {
            return loadFromDisk(cache_key);
        }

        auto profile = generateProfile(key);
        saveToDisk(cache_key, profile);
        return profile;
    }

private:
    std::vector<std::complex<double>> generateProfile(const ProfileKey& key) {
        switch (key.type) {
            case ProfileType::GAUSSIAN:
                return generateGaussian(key);
            case ProfileType::SOLITON:
                return generateSoliton(key);
            // ... other types
        }
    }

    std::vector<std::complex<double>> generateGaussian(const ProfileKey& key) {
        std::vector<std::complex<double>> field(key.Nx * key.Ny * key.Nz);

        double center_x = key.Nx / 2.0;
        double center_y = key.Ny / 2.0;
        double center_z = key.Nz / 2.0;

        for (int i = 0; i < key.Nx; ++i) {
            for (int j = 0; j < key.Ny; ++j) {
                for (int k = 0; k < key.Nz; ++k) {
                    double r2 = std::pow(i - center_x, 2) +
                                std::pow(j - center_y, 2) +
                                std::pow(k - center_z, 2);

                    double value = key.amplitude *
                                   std::exp(-r2 / (2.0 * key.width * key.width));

                    int idx = i + key.Nx * (j + key.Ny * k);
                    field[idx] = std::complex<double>(value, 0.0);
                }
            }
        }

        return field;
    }
};

}} // namespace dase::cache
```

---

#### Feature 8: Surrogate Response Library (Extension)

**Impact:** HIGH (10-100x speedup in production)
**Effort:** 3-4 days (model management layer)
**Prerequisites:** Feature 11, trained models from Colab

**Current Status:**
- ✅ Infrastructure exists (`SurrogateAdapter`, `FeedForwardSurrogate`)
- ⚠️ No trained models yet
- ⚠️ No library management

**Enhancement:**
```python
# surrogate_library.py
class SurrogateLibrary:
    """Manages trained surrogate models with versioning and metadata."""

    def __init__(self, cache_mgr: CacheManager):
        self.cache = cache_mgr
        self.models = {}
        self._load_registry()

    def register_model(
        self,
        engine_type: str,
        model_path: Path,
        metadata: dict
    ) -> str:
        """Register a trained surrogate model."""

        model_id = f"{engine_type}_v{metadata.get('version', 1)}"

        # Copy model to cache
        cache_path = self.cache.save("surrogates", model_id, model_path)

        # Store metadata
        meta_key = f"{model_id}_metadata"
        self.cache.save("surrogates", meta_key, metadata)

        # Update registry
        self.models[model_id] = {
            "path": cache_path,
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat()
        }
        self._save_registry()

        return model_id

    def load_model(self, model_id: str) -> FeedForwardSurrogate:
        """Load a registered surrogate model."""

        if model_id not in self.models:
            raise KeyError(f"Model {model_id} not found in library")

        path = self.models[model_id]["path"]
        return FeedForwardSurrogate.load(str(path))

    def get_best_model(self, engine_type: str) -> tuple[str, FeedForwardSurrogate]:
        """Get highest-accuracy model for engine type."""

        candidates = [
            (mid, meta) for mid, meta in self.models.items()
            if mid.startswith(engine_type)
        ]

        if not candidates:
            raise ValueError(f"No models found for {engine_type}")

        # Sort by accuracy (lower MAE is better)
        best_id, best_meta = min(
            candidates,
            key=lambda x: x[1]["metadata"].get("mae", float('inf'))
        )

        return best_id, self.load_model(best_id)

    def list_models(self, engine_type: str = None) -> list[dict]:
        """List all registered models."""

        if engine_type:
            return [
                {"id": mid, **meta}
                for mid, meta in self.models.items()
                if mid.startswith(engine_type)
            ]

        return [{"id": mid, **meta} for mid, meta in self.models.items()]
```

**Usage Example:**
```python
# In production mission runtime
library = SurrogateLibrary(cache_mgr)
model_id, surrogate = library.get_best_model("igsoa_gw")

adapter = SurrogateAdapter()
adapter.register("run_mission", surrogate)

runtime = MissionRuntime(surrogate_adapter=adapter)
runtime.execute(mission_commands)  # Uses surrogate automatically
```

---

### 🔬 **P2: Medium-Impact Features (Weeks 4-5)**

#### Feature 4: Prime-Gap Echo Templates

**Impact:** Medium (constant-time echo generation)
**Effort:** 2-3 days
**Specific to:** IGSOA GW engine

**Implementation:**
```python
# echo_template_cache.py
class EchoTemplateCache:
    def get_or_compute(self, alpha: float, tau0: float, num_echoes: int):
        key = f"echo_template_{alpha}_{tau0}_{num_echoes}"

        if self.cache.exists("echo_templates", key):
            return self.cache.load("echo_templates", key)

        # Compute prime-gap sequence
        template = self._generate_prime_gap_echoes(alpha, tau0, num_echoes)
        self.cache.save("echo_templates", key, template)
        return template

    def _generate_prime_gap_echoes(self, alpha, tau0, num_echoes):
        """Generate echo timings based on prime gaps."""
        from sympy import prime

        echoes = []
        for i in range(num_echoes):
            # Use prime gaps to space echoes
            gap = prime(i + 2) - prime(i + 1)
            time = tau0 * (1.0 + alpha * gap)

            echoes.append({
                "time": time,
                "gap": gap,
                "envelope": self._normalized_envelope(time, tau0)
            })

        return echoes
```

---

#### Feature 6: Source Map Cache

**Impact:** Low-Medium (SATP multi-zone engines)
**Effort:** 1-2 days

**Implementation:**
```python
# source_map_cache.py
class SourceMapCache:
    def get_or_compute(self, zone_layout: dict, grid_shape: tuple):
        import hashlib
        layout_hash = hashlib.sha256(
            json.dumps(zone_layout, sort_keys=True).encode()
        ).hexdigest()[:16]

        key = f"source_map_{layout_hash}_{grid_shape[0]}x{grid_shape[1]}"

        if self.cache.exists("source_maps", key):
            return self.cache.load("source_maps", key)

        # Generate spatial masks for each zone
        masks = self._generate_zone_masks(zone_layout, grid_shape)
        self.cache.save("source_maps", key, masks)
        return masks
```

---

#### Feature 12: Hybrid Mission Mode

**Impact:** HIGH (adaptive computation)
**Effort:** 4-5 days
**Prerequisites:** Features 8, 11

**Implementation:**
```python
# hybrid_mission_runtime.py
class HybridMissionRuntime(MissionRuntime):
    def __init__(
        self,
        surrogate_adapter: SurrogateAdapter,
        cache_manager: CacheManager,
        novelty_threshold: float = 0.1
    ):
        super().__init__(surrogate_adapter=surrogate_adapter)
        self.cache = cache_manager
        self.threshold = novelty_threshold

    def execute(self, mission_commands: list) -> ProfilerSessionResult:
        """Execute mission with adaptive surrogate/full-solver switching."""

        for cmd in mission_commands:
            # Compute novelty score
            novelty = self._compute_novelty(cmd)

            if novelty < self.threshold:
                # Low novelty: Use surrogate
                self.logger.info(f"Using surrogate (novelty={novelty:.3f})")
                result = self.surrogate_adapter.execute(
                    cmd["command"],
                    cmd["params"],
                    fallback=None  # No fallback needed
                )
            else:
                # High novelty: Run full solver and update cache
                self.logger.info(f"Using full solver (novelty={novelty:.3f})")
                result = self._run_full_solver(cmd)

                # Update surrogate training data
                self._add_to_training_buffer(cmd, result)

        return super().execute(mission_commands)

    def _compute_novelty(self, cmd: dict) -> float:
        """Compute how novel this command is vs. cached data."""

        # Extract parameter vector
        params = self._extract_param_vector(cmd)

        # Find nearest cached mission
        nearest_key, nearest_params = self._find_nearest_cached(params)

        if nearest_key is None:
            return 1.0  # Completely novel

        # Compute L2 distance (normalized)
        novelty = np.linalg.norm(params - nearest_params) / np.linalg.norm(params)
        return novelty
```

---

### 🤖 **P3: Advanced Automation (Weeks 6-7)**

#### Feature 7: Mission Graph Cache

**Impact:** HIGH (DAG-level reuse)
**Effort:** 5-7 days
**Risk:** HIGH (complexity)

**Design:**
```python
# mission_graph_cache.py
class MissionGraphCache:
    """DAG-level caching using content-addressable storage."""

    def __init__(self, cache_mgr: CacheManager):
        self.cache = cache_mgr
        self.graph = nx.DiGraph()  # Dependency graph

    def execute_with_cache(self, mission_json: dict) -> dict:
        """Execute mission with DAG-level caching."""

        # Build dependency graph
        dag = self._build_dag(mission_json["commands"])

        results = {}
        for node in nx.topological_sort(dag):
            cmd = dag.nodes[node]["command"]

            # Compute content hash (SHA256 of params + dependencies)
            node_hash = self._compute_node_hash(cmd, results)

            if self.cache.exists("mission_graph", node_hash):
                # Cache hit: Load result
                results[node] = self.cache.load("mission_graph", node_hash)
            else:
                # Cache miss: Execute and store
                result = self._execute_command(cmd, results)
                self.cache.save("mission_graph", node_hash, result)
                results[node] = result

        return results

    def _compute_node_hash(self, cmd: dict, dependencies: dict) -> str:
        """Compute SHA256 hash of command + dependency outputs."""
        import hashlib

        # Serialize command params
        cmd_str = json.dumps(cmd["params"], sort_keys=True)

        # Include hashes of dependency outputs
        dep_hashes = [
            hashlib.sha256(str(dependencies[dep]).encode()).hexdigest()
            for dep in cmd.get("depends_on", [])
        ]

        combined = cmd_str + "".join(sorted(dep_hashes))
        return hashlib.sha256(combined.encode()).hexdigest()
```

**Benefit:** If you run a mission with commands A → B → C, then run A → B → D, commands A and B are cached and instant.

---

#### Feature 9: Validation & Re-Training Loop

**Impact:** Medium (surrogate fidelity)
**Effort:** 4-5 days
**Prerequisites:** Feature 8

**Implementation:**
```python
# surrogate_validator.py
class SurrogateValidator:
    def __init__(
        self,
        library: SurrogateLibrary,
        drift_threshold: float = 0.05
    ):
        self.library = library
        self.threshold = drift_threshold

    def validate_and_retrain(
        self,
        model_id: str,
        benchmark_missions: list
    ) -> dict:
        """Run validation and trigger retraining if needed."""

        surrogate = self.library.load_model(model_id)

        # Run benchmark missions
        errors = []
        for mission in benchmark_missions:
            # Run with surrogate
            surrogate_output = surrogate(mission["features"])

            # Run with full solver
            full_output = self._run_full_solver(mission)

            # Compute error
            mae = np.mean(np.abs(surrogate_output - full_output))
            errors.append(mae)

        avg_error = np.mean(errors)
        max_error = np.max(errors)

        # Check if retraining needed
        if avg_error > self.threshold:
            self.logger.warning(
                f"Surrogate drift detected: {avg_error:.4f} > {self.threshold}"
            )
            self._trigger_retraining(model_id, benchmark_missions)
            return {"status": "retrained", "error": avg_error}

        return {"status": "valid", "error": avg_error}

    def _trigger_retraining(self, model_id: str, missions: list):
        """Queue retraining job (could be async/Colab)."""

        # Export training data
        dataset_path = self._export_training_dataset(missions)

        # Create retraining job
        job = {
            "model_id": model_id,
            "dataset": dataset_path,
            "triggered_at": datetime.utcnow().isoformat(),
            "reason": "drift_threshold_exceeded"
        }

        # Queue for Colab or local training
        self._queue_training_job(job)
```

---

### 🚫 **P4: Deferred/Future (Post-Phase 2)**

#### Feature 10: Governance & Growth Agent

**Impact:** Low (automation nice-to-have)
**Effort:** 7-10 days
**Risk:** HIGH (scope creep)

**Recommendation:** **DEFER** until Phases 1-2 complete and manual processes are stable.

**Reasoning:**
- Requires mature validation processes
- Risk of over-automation before workflows stabilized
- Better to manually refine processes first

**Future Design:**
```python
# governance_agent.py (DEFERRED)
class GovernanceAgent:
    """Automated self-maintenance and validation orchestrator."""

    def run_nightly_cycle(self):
        # 1. Run benchmark suite
        # 2. Validate surrogates
        # 3. Check code metrics
        # 4. Generate reports
        # 5. Trigger retraining if needed
        # 6. Update documentation
        pass
```

---

## Implementation Roadmap

### **Phase A: Foundation (Week 1) - Priority P0**

**Goal:** Build unified cache infrastructure

| Task | Feature | Effort | Status |
|------|---------|--------|--------|
| A1 | Design cache directory structure | 4 hours | Planned |
| A2 | Implement CacheManager base class | 8 hours | Planned |
| A3 | Create FilesystemBackend | 6 hours | Planned |
| A4 | Create ModelBackend (PyTorch) | 4 hours | Planned |
| A5 | FFTW Wisdom Manager (C++) | 8 hours | Planned |
| A6 | Integration tests | 6 hours | Planned |

**Deliverables:**
- ✅ `backend/cache/cache_manager.py`
- ✅ `src/cpp/cache/fftw_wisdom_manager.h`
- ✅ `cache/` directory structure
- ✅ Unit tests for CacheManager

**Estimated Time:** 36 hours (1 week)

---

### **Phase B: High-Impact Caches (Weeks 2-3) - Priority P1**

**Goal:** Implement features with highest ROI

| Task | Feature | Effort | Status |
|------|---------|--------|--------|
| B1 | Persistent Fractional Kernel Cache | 24 hours | Planned |
| B2 | Laplacian Stencil Cache | 16 hours | Planned |
| B3 | Initial-State Profile Cache | 12 hours | Planned |
| B4 | Surrogate Library Management | 20 hours | Planned |
| B5 | CLI integration points | 8 hours | Planned |
| B6 | End-to-end tests | 10 hours | Planned |

**Deliverables:**
- ✅ `src/cpp/cache/fractional_kernel_cache.h`
- ✅ `backend/cache/stencil_cache.py`
- ✅ `backend/cache/surrogate_library.py`
- ✅ CLI `--use-cache` flag

**Estimated Time:** 90 hours (2-3 weeks)

---

### **Phase C: Advanced Features (Weeks 4-6) - Priority P2**

**Goal:** Adaptive computation and specialized caches

| Task | Feature | Effort | Status |
|------|---------|--------|--------|
| C1 | Prime-Gap Echo Templates | 16 hours | Planned |
| C2 | Source Map Cache | 12 hours | Planned |
| C3 | Hybrid Mission Mode | 32 hours | Planned |
| C4 | Mission Graph Cache (prototype) | 40 hours | Planned |
| C5 | Performance benchmarking | 12 hours | Planned |
| C6 | Documentation | 16 hours | Planned |

**Deliverables:**
- ✅ `backend/runtime/hybrid_mission_runtime.py`
- ✅ `backend/cache/mission_graph_cache.py` (prototype)
- ✅ Performance comparison report

**Estimated Time:** 128 hours (3-4 weeks)

---

### **Phase D: Validation & Polish (Week 7) - Priority P3**

**Goal:** Production readiness

| Task | Feature | Effort | Status |
|------|---------|--------|--------|
| D1 | Surrogate Validation Loop | 32 hours | Planned |
| D2 | Cache eviction policies | 8 hours | Planned |
| D3 | Monitoring & metrics | 12 hours | Planned |
| D4 | Production deployment guide | 8 hours | Planned |
| D5 | Security audit (cache access) | 8 hours | Planned |

**Deliverables:**
- ✅ `backend/validation/surrogate_validator.py`
- ✅ Cache monitoring dashboard
- ✅ Deployment documentation

**Estimated Time:** 68 hours (1-2 weeks)

---

## Total Implementation Estimate

| Phase | Duration | Features | Effort (hours) |
|-------|----------|----------|----------------|
| **Phase A** | 1 week | P0 (Foundation) | 36 |
| **Phase B** | 2-3 weeks | P1 (High-Impact) | 90 |
| **Phase C** | 3-4 weeks | P2 (Advanced) | 128 |
| **Phase D** | 1-2 weeks | P3 (Validation) | 68 |
| **Total** | **7-10 weeks** | **12 features** | **322 hours** |

**Team Size:** 1-2 developers
**Realistic Timeline:** 8-10 weeks with testing & iteration

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cache invalidation bugs | Medium | High | Implement strict versioning, hash-based keys |
| Disk I/O bottlenecks | Low | Medium | Use LMDB for hot paths, async I/O |
| Surrogate accuracy drift | Medium | High | Automated validation loop (Feature 9) |
| Graph cache complexity | High | Medium | Start with prototype, MVP first |
| FFTW wisdom portability | Low | Low | CPU model in cache key |

### Organizational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep (Feature 10) | High | Medium | Defer governance agent to Phase 3 |
| Incomplete training data | Medium | High | Run Phase 1 validation first |
| Cache storage growth | Low | Medium | Implement eviction policies |

---

## Success Metrics

### Performance Targets

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Fractional engine startup** | 5-10s | <1s | Cache hit rate |
| **FFT initialization** | 1-5s | <0.1s | Wisdom load time |
| **Repeated mission time** | 100% | 20-50% | With/without cache |
| **Surrogate inference** | 1-10s | <100ms | vs. full solver |
| **Cache hit rate** | 0% | >80% | After warm-up |

### Quality Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Cache correctness** | 100% | Hash collision rate |
| **Surrogate MAE** | <0.05 | Validation loop |
| **Test coverage** | >85% | Cache manager tests |
| **Documentation** | 100% | All features documented |

---

## Prerequisites

### Before Starting Phase A

- ✅ **Security fixes applied** (completed today)
- ✅ **Surrogate infrastructure reviewed** (already exists)
- ⚠️ **Phase 1 validation data** (needed for Feature 8)
- ⚠️ **Storage strategy decided** (LMDB vs. filesystem)

### Before Starting Phase B

- ✅ **Feature 11 (CacheManager) complete**
- ✅ **Feature 3 (FFTW Wisdom) tested**
- ⚠️ **Trained surrogate models available** (from Colab)

### Before Starting Phase C

- ✅ **Phase B features tested in production**
- ✅ **Performance benchmarks baseline**
- ⚠️ **DAG execution model designed**

---

## Integration Points

### Command Center Integration

**Dashboard View:**
```typescript
// Add cache status panel to Command Center
interface CacheStatus {
    hit_rate: number;
    total_size_mb: number;
    categories: {
        fractional_kernels: { count: number, size_mb: number },
        stencils: { count: number, size_mb: number },
        surrogates: { count: number, size_mb: number }
    }
}
```

**Cache Control Panel:**
- ✅ View cache statistics
- ✅ Clear cache by category
- ✅ Export/import cache bundles
- ✅ Force cache rebuild

### CLI Integration

**New Flags:**
```bash
# Enable all caching
./dase_cli --use-cache mission.json

# Clear cache before run
./dase_cli --clear-cache --use-cache mission.json

# Cache stats
./dase_cli --cache-stats

# Export cache for sharing
./dase_cli --export-cache cache_bundle.tar.gz
```

---

## Recommended Next Steps

### **Immediate (This Week)**

1. ✅ **Review this analysis** with team/stakeholders
2. ✅ **Approve Phase A scope** (Foundation)
3. ✅ **Decide storage backend** (Filesystem vs. LMDB)
4. ✅ **Allocate developer time** (1-2 devs for 8 weeks)

### **Week 1 (Phase A)**

1. ✅ Create `backend/cache/` directory structure
2. ✅ Implement `CacheManager` base class
3. ✅ Build FFTW wisdom manager
4. ✅ Write unit tests
5. ✅ Document cache API

### **Weeks 2-3 (Phase B)**

1. ✅ Implement persistent fractional kernel cache
2. ✅ Build Laplacian stencil cache
3. ✅ Create surrogate library management
4. ✅ Integrate with CLI
5. ✅ Run performance benchmarks

### **Deferred Until Phase 1 Complete**

- ⚠️ Feature 8 production deployment (awaits trained models)
- ⚠️ Feature 9 validation loop (awaits Phase 1 data)
- ⚠️ Feature 10 governance agent (awaits stable processes)

---

## Conclusion

The proposed 12-feature cache system is **architecturally sound and well-aligned with the Phase 2 roadmap**. The features build logically on each other with clear dependencies.

**Key Recommendations:**

1. ✅ **Implement in 4 phases** (Foundation → High-Impact → Advanced → Validation)
2. ✅ **Start with P0 features** (CacheManager, FFTW Wisdom)
3. ⚠️ **Defer governance agent** (Feature 10) to Phase 3
4. ⚠️ **Wait for Phase 1 data** before full surrogate deployment
5. ✅ **Allocate 8-10 weeks** with 1-2 developers

**Expected Outcome:**
- 50-80% speedup for repeated missions
- Near-instant startup for cached configurations
- Foundation for ML-accelerated workflows
- Self-optimizing simulation framework

**Ready to proceed:** Yes, pending approval and resource allocation.

---

**Next Document:** `CACHE_IMPLEMENTATION_PLAN_PHASE_A.md` (detailed Phase A tasks)

