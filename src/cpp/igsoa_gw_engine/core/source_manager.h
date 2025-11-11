/**
 * IGSOA Gravitational Wave Engine - Binary Merger Source Manager
 *
 * Manages binary black hole merger dynamics and generates source terms
 * for the IGSOA field evolution.
 *
 * Physics:
 * - Two massive objects in circular orbit
 * - Gaussian asymmetry concentrations at each BH location
 * - Source term S(x,t) = S₁(x,t) + S₂(x,t)
 * - Optional inspiral dynamics (GW radiation backreaction)
 *
 * Coordinate System:
 * - Center of mass at configurable position
 * - Orbital plane in xy-plane
 * - z-axis perpendicular to orbit
 */

#ifndef DASE_IGSOA_GW_SOURCE_MANAGER_H
#define DASE_IGSOA_GW_SOURCE_MANAGER_H

#include "symmetry_field.h"
#include <complex>
#include <vector>

namespace dase {
namespace igsoa {
namespace gw {

/**
 * Configuration for binary merger simulation
 */
struct BinaryMergerConfig {
    // Masses (in solar masses M☉)
    double mass1;
    double mass2;

    // Initial orbital parameters
    double initial_separation;      // meters
    double initial_orbital_phase;   // radians (default: 0)

    // Orbital center position
    Vector3D center;

    // Source amplitude parameters
    double gaussian_width;          // σ for asymmetry concentration (meters)
    double source_amplitude;        // Overall amplitude factor

    // Physics flags
    bool enable_inspiral;           // Enable GW radiation backreaction
    double merger_threshold;        // r_merge = merger_threshold × R_schwarzschild

    // Default constructor
    BinaryMergerConfig()
        : mass1(30.0)
        , mass2(30.0)
        , initial_separation(200e3)     // 200 km
        , initial_orbital_phase(0.0)
        , center(0, 0, 0)
        , gaussian_width(5e3)           // 5 km
        , source_amplitude(1.0)
        , enable_inspiral(false)        // Start with circular orbit
        , merger_threshold(3.0)         // Merge at 3 R_s
    {}
};

/**
 * Binary Merger Source Manager
 *
 * Handles:
 * - Orbital dynamics (position evolution)
 * - Source term generation (Gaussian concentrations)
 * - Merger detection
 * - Inspiral (optional)
 */
class BinaryMerger {
public:
    /**
     * Constructor
     * @param config Binary merger configuration
     */
    explicit BinaryMerger(const BinaryMergerConfig& config);

    /**
     * Destructor
     */
    ~BinaryMerger();

    // ========================================================================
    // Orbital Evolution
    // ========================================================================

    /**
     * Evolve orbital positions by one timestep
     * @param dt Timestep (seconds)
     */
    void evolveOrbit(double dt);

    /**
     * Reset to initial conditions
     */
    void reset();

    // ========================================================================
    // Source Term Generation
    // ========================================================================

    /**
     * Compute source terms for the IGSOA field
     *
     * S(x,t) = S₁(x,t) + S₂(x,t)
     * where: S_i(x,t) = A_i exp(-|x - x_i(t)|² / (2σ²))
     *
     * @param field Symmetry field (provides grid information)
     * @param t Current simulation time (seconds)
     * @return Vector of complex source terms (one per grid point)
     */
    std::vector<std::complex<double>> computeSourceTerms(
        const SymmetryField& field,
        double t) const;

    // ========================================================================
    // Query Methods
    // ========================================================================

    /**
     * Get position of first black hole
     * @return Position vector (meters)
     */
    Vector3D getPosition1() const;

    /**
     * Get position of second black hole
     * @return Position vector (meters)
     */
    Vector3D getPosition2() const;

    /**
     * Get current orbital separation
     * @return Distance between BHs (meters)
     */
    double getSeparation() const;

    /**
     * Get current orbital frequency
     * @return Angular frequency ω (rad/s)
     */
    double getOrbitalFrequency() const;

    /**
     * Get current orbital phase
     * @return Phase φ (radians)
     */
    double getOrbitalPhase() const;

    /**
     * Check if merger has occurred
     * @return True if r < r_merge
     */
    bool hasMerged() const;

    /**
     * Get time until merger (if inspiral enabled)
     * @return Estimated time to merger (seconds), or -1 if not applicable
     */
    double getTimeToMerger() const;

    /**
     * Get total system mass
     * @return M = m₁ + m₂ (solar masses)
     */
    double getTotalMass() const;

    /**
     * Get reduced mass
     * @return μ = m₁m₂/(m₁+m₂) (solar masses)
     */
    double getReducedMass() const;

    /**
     * Get Schwarzschild radius for total mass
     * @return R_s = 2GM/c² (meters)
     */
    double getSchwarzchildRadius() const;

    // ========================================================================
    // Diagnostics
    // ========================================================================

    /**
     * Get total energy radiated in GWs (if inspiral enabled)
     * @return Energy (Joules)
     */
    double getTotalEnergyRadiated() const;

    /**
     * Print current orbital state
     */
    void printState() const;

private:
    // Configuration
    BinaryMergerConfig config_;

    // Orbital state
    double current_separation_;     // Current r (meters)
    double current_phase_;          // Current φ (radians)
    double current_omega_;          // Current ω (rad/s)

    // Individual positions (relative to center)
    Vector3D position1_;
    Vector3D position2_;

    // Reduced orbital radii (from center of mass)
    double r1_;  // = m₂/(m₁+m₂) × r
    double r2_;  // = m₁/(m₁+m₂) × r

    // Derived quantities
    double total_mass_;             // M = m₁ + m₂ (kg)
    double reduced_mass_;           // μ = m₁m₂/M (kg)
    double schwarzschild_radius_;   // R_s = 2GM/c² (meters)
    double merger_radius_;          // r_merge (meters)

    // Inspiral tracking
    double total_energy_radiated_;  // E_GW (Joules)
    bool has_merged_;

    // Physical constants (CGS → SI conversions handled internally)
    static constexpr double G = 6.67430e-11;        // m³/(kg·s²)
    static constexpr double c = 299792458.0;        // m/s
    static constexpr double M_sun = 1.98847e30;     // kg

    // ========================================================================
    // Internal Methods
    // ========================================================================

    /**
     * Initialize derived quantities from configuration
     */
    void initialize();

    /**
     * Compute orbital frequency from separation
     * ω = √(GM/r³)
     * @param separation Orbital radius (meters)
     * @return Angular frequency (rad/s)
     */
    double computeOrbitalFrequency(double separation) const;

    /**
     * Compute inspiral rate dr/dt from GW luminosity
     * (Peters & Mathews 1963)
     * @return dr/dt (meters/second)
     */
    double computeInspiralRate() const;

    /**
     * Update individual positions from orbital parameters
     */
    void updatePositions();

    /**
     * Compute Gaussian source amplitude at a point
     * @param position Field point position
     * @param bh_position BH position
     * @param mass BH mass (for amplitude scaling)
     * @return Complex source amplitude
     */
    std::complex<double> computeGaussianSource(
        const Vector3D& position,
        const Vector3D& bh_position,
        double mass) const;
};

} // namespace gw
} // namespace igsoa
} // namespace dase

#endif // DASE_IGSOA_GW_SOURCE_MANAGER_H
