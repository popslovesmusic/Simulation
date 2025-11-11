/**
 * IGSOA Gravitational Wave Engine - Symmetry Field Module
 *
 * Manages the 3D spatial grid of the fundamental asymmetry field δΦ.
 * The field δΦ = Φ - Φ₀ represents broken causal symmetry from which
 * all gravitational phenomena emerge in IGSOA theory.
 *
 * Based on: IGSOA-QMM Framework Papers 01, 04, 05
 * Design: docs/implementation/IGSOA_GW_ENGINE_DESIGN.md
 */

#pragma once

#include <complex>
#include <vector>
#include <memory>

namespace dase {
namespace igsoa {
namespace gw {

/**
 * 3D Vector for spatial coordinates
 */
struct Vector3D {
    double x, y, z;

    Vector3D() : x(0), y(0), z(0) {}
    Vector3D(double x_, double y_, double z_) : x(x_), y(y_), z(z_) {}

    // Vector operations
    double magnitude() const;
    Vector3D normalized() const;
    Vector3D operator+(const Vector3D& other) const;
    Vector3D operator-(const Vector3D& other) const;
    Vector3D operator*(double scalar) const;
    double dot(const Vector3D& other) const;
    Vector3D cross(const Vector3D& other) const;
};

/**
 * 4x4 Tensor for stress-energy (O_μν projection)
 */
struct Tensor4x4 {
    double components[4][4];

    Tensor4x4();
    double& operator()(int mu, int nu);
    const double& operator()(int mu, int nu) const;

    // Tensor operations
    double trace() const;
    Tensor4x4 transpose() const;
};

/**
 * Configuration for symmetry field grid
 */
struct SymmetryFieldConfig {
    // Grid dimensions
    int nx, ny, nz;          // Number of grid points in each dimension
    double dx, dy, dz;       // Grid spacing in meters

    // Physical parameters
    double R_c_default;      // Default coupling constant
    double kappa;            // Asymmetry potential scale
    double lambda;           // Self-interaction strength

    // Fractional dynamics
    double alpha_min;        // Minimum memory order (near horizon)
    double alpha_max;        // Maximum memory order (flat spacetime)

    // Time evolution
    double dt;               // Timestep in seconds

    SymmetryFieldConfig();
};

/**
 * Main symmetry field class
 *
 * Represents the 3D grid of δΦ(x,y,z,t) - the broken symmetry field
 * from which gravitational waves emerge as propagating restoration modes.
 */
class SymmetryField {
public:
    /**
     * Constructor
     * @param config Field configuration
     */
    explicit SymmetryField(const SymmetryFieldConfig& config);

    /**
     * Destructor - clean up 3D arrays
     */
    ~SymmetryField();

    // Disable copy (large 3D arrays)
    SymmetryField(const SymmetryField&) = delete;
    SymmetryField& operator=(const SymmetryField&) = delete;

    // === Grid Access ===

    /**
     * Get δΦ at grid point (i,j,k)
     */
    std::complex<double> getDeltaPhi(int i, int j, int k) const;

    /**
     * Set δΦ at grid point (i,j,k)
     */
    void setDeltaPhi(int i, int j, int k, std::complex<double> value);

    /**
     * Get δΦ at physical position (interpolated)
     */
    std::complex<double> getDeltaPhiAt(const Vector3D& position) const;

    /**
     * Get fractional memory order α at grid point
     */
    double getAlpha(int i, int j, int k) const;

    /**
     * Set fractional memory order α at grid point
     */
    void setAlpha(int i, int j, int k, double alpha);

    /**
     * Get α at physical position (interpolated)
     */
    double getAlphaAt(const Vector3D& position) const;

    /**
     * Get flat array of all δΦ values (for FractionalSolver)
     * @return Reference to internal storage
     */
    const std::vector<std::complex<double>>& getDeltaPhiFlat() const;

    /**
     * Get flat array of all α values (for FractionalSolver)
     * @return Vector of alpha values at each grid point
     */
    std::vector<double> getAlphaValues() const;

    // === Spatial Derivatives ===

    /**
     * Compute gradient ∇δΦ at grid point
     */
    Vector3D computeGradient(int i, int j, int k) const;

    /**
     * Compute Laplacian ∇²δΦ at grid point
     */
    std::complex<double> computeLaplacian(int i, int j, int k) const;

    /**
     * Get gradient magnitude |∇δΦ| (cached)
     */
    double getGradientMagnitude(int i, int j, int k) const;

    /**
     * Update all gradient magnitude cache
     */
    void updateGradientCache();

    // === Effective Potential ===

    /**
     * Compute asymmetry potential V(δΦ) at grid point
     * V(δΦ) = λ |δΦ|² + κ |δΦ|⁴ + ...
     */
    double computePotential(int i, int j, int k) const;

    /**
     * Compute potential derivative ∂V/∂δΦ
     */
    std::complex<double> computePotentialDerivative(int i, int j, int k) const;

    /**
     * Get cached potential value
     */
    double getPotential(int i, int j, int k) const;

    /**
     * Update all potential cache
     */
    void updatePotentialCache();

    // === Field Evolution ===

    /**
     * Advance field by one timestep using fractional wave equation:
     * ∂²ₓ ψ - ₀D^α_t ψ - V(δΦ) ψ = S
     *
     * @param fractional_derivatives Computed by FractionalSolver
     * @param source_terms Source S(x,t) from binary system
     */
    void evolveStep(
        const std::vector<std::complex<double>>& fractional_derivatives,
        const std::vector<std::complex<double>>& source_terms
    );

    /**
     * Get current simulation time
     */
    double getCurrentTime() const { return current_time_; }

    /**
     * Set current simulation time
     */
    void setCurrentTime(double t) { current_time_ = t; }

    /**
     * Get timestep
     */
    double getTimestep() const { return config_.dt; }

    // === Grid Info ===

    const SymmetryFieldConfig& getConfig() const { return config_; }
    int getNx() const { return config_.nx; }
    int getNy() const { return config_.ny; }
    int getNz() const { return config_.nz; }
    double getDx() const { return config_.dx; }
    double getDy() const { return config_.dy; }
    double getDz() const { return config_.dz; }
    int getTotalPoints() const { return config_.nx * config_.ny * config_.nz; }

    /**
     * Convert (i,j,k) to flat index
     */
    int toFlatIndex(int i, int j, int k) const;

    /**
     * Convert flat index to (i,j,k)
     */
    void fromFlatIndex(int idx, int& i, int& j, int& k) const;

    /**
     * Convert grid indices to physical position
     */
    Vector3D toPosition(int i, int j, int k) const;

    /**
     * Convert physical position to grid indices (nearest)
     */
    void toIndices(const Vector3D& pos, int& i, int& j, int& k) const;

    // === Diagnostics ===

    /**
     * Compute total energy ∫ |δΦ|² dV
     */
    double computeTotalEnergy() const;

    /**
     * Compute maximum |δΦ| in grid
     */
    double computeMaxAmplitude() const;

    /**
     * Get field statistics
     */
    struct FieldStats {
        double mean_amplitude;
        double max_amplitude;
        double total_energy;
        double mean_gradient;
        double max_gradient;
    };
    FieldStats getStatistics() const;

    /**
     * Export field to file (for visualization)
     */
    void exportToFile(const std::string& filename) const;

private:
    SymmetryFieldConfig config_;

    // 3D grids (flattened storage: [nx * ny * nz])
    std::vector<std::complex<double>> delta_phi_;     // δΦ(x,y,z)
    std::vector<double> alpha_;                       // α(x,y,z) memory order
    std::vector<double> gradient_magnitude_;          // |∇δΦ| (cached)
    std::vector<double> potential_;                   // V(δΦ) (cached)

    double current_time_;

    // Helper: check if indices are valid
    bool isValidIndex(int i, int j, int k) const;

    // Helper: trilinear interpolation for field values
    std::complex<double> interpolateDeltaPhi(const Vector3D& pos) const;
    double interpolateAlpha(const Vector3D& pos) const;

    // Helper: validate configuration parameters
    void validateConfig() const;
};

} // namespace gw
} // namespace igsoa
} // namespace dase
