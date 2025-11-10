/**
 * IGSOA GW Engine - Projection Operators
 *
 * Projects the fundamental δΦ field onto observable modes:
 * - φ-mode: Scalar mass/energy projection
 * - O_μν-mode: Tensor curvature/GW projection
 * - B_μ-mode: Causal exchange flow
 *
 * The gravitational wave strain h(t) is extracted from O_μν.
 */

#pragma once

#include "symmetry_field.h"
#include <complex>

namespace dase {
namespace igsoa {
namespace gw {

/**
 * Projection mode configuration
 */
struct ProjectionConfig {
    // Observer position and orientation
    Vector3D observer_position;
    Vector3D detector_normal;     // Direction to detector
    double detector_distance;      // Distance from source (m)

    // Gauge choice for h extraction
    enum class Gauge {
        TransverseTraceless,  // TT gauge (standard for GW)
        Harmonic,             // Harmonic gauge
        Lorenz                // Lorenz gauge
    };
    Gauge gauge;

    ProjectionConfig();
};

/**
 * Projection operators class
 */
class ProjectionOperators {
public:
    explicit ProjectionOperators(const ProjectionConfig& config);

    // === φ-mode: Scalar Projection ===

    /**
     * Extract scalar mass/energy component from δΦ
     */
    double compute_phi_mode(std::complex<double> delta_phi) const;

    /**
     * Compute φ-mode over entire field
     */
    std::vector<double> compute_phi_mode_field(const SymmetryField& field) const;

    // === O_μν-mode: Tensor Projection ===

    /**
     * Compute stress-energy tensor O_μν from δΦ gradients
     *
     * O_μν ~ ∇_μ δΦ ∇_ν δΦ - g_μν L(δΦ)
     */
    Tensor4x4 compute_stress_energy_tensor(
        const SymmetryField& field,
        int i, int j, int k
    ) const;

    /**
     * Extract GW strain components in TT gauge
     * h_+ = O_xx - O_yy
     * h_× = 2 O_xy
     */
    struct StrainComponents {
        double h_plus;
        double h_cross;
        double amplitude;  // sqrt(h_+^2 + h_×^2)
        double phase;      // atan2(h_×, h_+)
    };
    StrainComponents compute_strain(
        const Tensor4x4& stress_tensor,
        const Vector3D& detector_direction
    ) const;

    /**
     * Compute strain at specific observer location
     */
    StrainComponents compute_strain_at_observer(
        const SymmetryField& field
    ) const;

    // === B_μ-mode: Causal Exchange ===

    /**
     * Compute causal exchange vector B_μ
     * (Direction of information flow)
     */
    struct CausalFlowVector {
        double B0, B1, B2, B3;  // 4-vector components
        double magnitude;
    };
    CausalFlowVector compute_causal_flow(
        const SymmetryField& field,
        int i, int j, int k
    ) const;

    // === Combined Projection ===

    /**
     * Full projection of δΦ → (φ, O_μν, B_μ)
     */
    struct FullProjection {
        double phi_mode;
        Tensor4x4 O_tensor;
        CausalFlowVector B_vector;
        StrainComponents strain;
    };
    FullProjection compute_full_projection(
        const SymmetryField& field,
        int i, int j, int k
    ) const;

    // === Gauge Transformations ===

    /**
     * Transform strain to specified gauge
     */
    StrainComponents transform_gauge(
        const StrainComponents& strain,
        ProjectionConfig::Gauge target_gauge
    ) const;

    /**
     * Apply TT projection operator to tensor
     */
    Tensor4x4 apply_TT_projection(const Tensor4x4& tensor) const;

private:
    ProjectionConfig config_;

    // Helper: metric tensor g_μν (Minkowski for now)
    double metric(int mu, int nu) const;
};

} // namespace gw
} // namespace igsoa
} // namespace dase
