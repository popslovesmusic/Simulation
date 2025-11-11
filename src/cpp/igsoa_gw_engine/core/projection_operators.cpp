/**
 * IGSOA GW Engine - Projection Operators Implementation
 */

#include "projection_operators.h"
#include <cmath>
#include <algorithm>
#include <iostream>

namespace dase {
namespace igsoa {
namespace gw {

ProjectionConfig::ProjectionConfig()
    : observer_position(0, 0, 1e6)  // 1000 km away
    , detector_normal(0, 0, -1)      // Looking toward source
    , detector_distance(1e6)
    , gauge(Gauge::TransverseTraceless)
{
}

ProjectionOperators::ProjectionOperators(const ProjectionConfig& config)
    : config_(config)
{
}

double ProjectionOperators::compute_phi_mode(std::complex<double> delta_phi) const {
    return std::abs(delta_phi);
}

std::vector<double> ProjectionOperators::compute_phi_mode_field(const SymmetryField& field) const {
    int total = field.getTotalPoints();
    std::vector<double> phi_field(total);

    for (int i = 0; i < field.getNx(); i++) {
        for (int j = 0; j < field.getNy(); j++) {
            for (int k = 0; k < field.getNz(); k++) {
                int idx = field.toFlatIndex(i, j, k);
                std::complex<double> phi = field.getDeltaPhi(i, j, k);
                phi_field[idx] = compute_phi_mode(phi);
            }
        }
    }

    return phi_field;
}

Tensor4x4 ProjectionOperators::compute_stress_energy_tensor(
    const SymmetryField& field, int i, int j, int k) const
{
    Tensor4x4 O_tensor;

    // Get field value and gradients
    std::complex<double> phi = field.getDeltaPhi(i, j, k);
    Vector3D grad_phi = field.computeGradient(i, j, k);

    // Compute Lagrangian density
    // L(δΦ) = |∇δΦ|² - V(δΦ)
    double grad_sq = grad_phi.dot(grad_phi);
    double potential = field.getPotential(i, j, k);
    double lagrangian = grad_sq - potential;

    // Stress-energy tensor in IGSOA:
    // O_μν = ∂_μ δΦ* ∂_ν δΦ + ∂_μ δΦ ∂_ν δΦ* - g_μν L(δΦ)
    //
    // Simplified heuristic (spatial part dominates for GW):
    // O_ij ≈ ∂_i |δΦ| ∂_j |δΦ| - δ_ij L(δΦ)

    // Spatial components (i,j = 1,2,3)
    for (int mu = 1; mu <= 3; mu++) {
        for (int nu = 1; nu <= 3; nu++) {
            double grad_mu = 0.0, grad_nu = 0.0;

            if (mu == 1) grad_mu = grad_phi.x;
            else if (mu == 2) grad_mu = grad_phi.y;
            else if (mu == 3) grad_mu = grad_phi.z;

            if (nu == 1) grad_nu = grad_phi.x;
            else if (nu == 2) grad_nu = grad_phi.y;
            else if (nu == 3) grad_nu = grad_phi.z;

            O_tensor(mu, nu) = grad_mu * grad_nu;

            // Subtract trace part
            if (mu == nu) {
                O_tensor(mu, nu) -= lagrangian / 3.0;
            }
        }
    }

    // Time components (simplified: O_00 = energy density)
    O_tensor(0, 0) = std::norm(phi) + grad_sq + potential;

    // Mixed time-space (O_0i = momentum flux)
    for (int idx = 1; idx <= 3; idx++) {
        O_tensor(0, idx) = 0.0;  // Simplified: no momentum flux
        O_tensor(idx, 0) = 0.0;
    }

    return O_tensor;
}

ProjectionOperators::StrainComponents ProjectionOperators::compute_strain(
    const Tensor4x4& stress_tensor, const Vector3D& detector_direction) const
{
    StrainComponents strain;
    // TODO: Extract h_+, h_× from O_μν in TT gauge
    strain.h_plus = stress_tensor(1, 1) - stress_tensor(2, 2);
    strain.h_cross = 2.0 * stress_tensor(1, 2);
    strain.amplitude = std::sqrt(strain.h_plus * strain.h_plus + strain.h_cross * strain.h_cross);
    strain.phase = std::atan2(strain.h_cross, strain.h_plus);
    return strain;
}

ProjectionOperators::StrainComponents ProjectionOperators::compute_strain_at_observer(
    const SymmetryField& field) const
{
    // Get observer position
    Vector3D obs_pos = config_.observer_position;

    // Find nearest grid point (or interpolate in future)
    int i, j, k;
    field.toIndices(obs_pos, i, j, k);

    // Clamp to valid range
    i = std::max(0, std::min(i, field.getNx() - 1));
    j = std::max(0, std::min(j, field.getNy() - 1));
    k = std::max(0, std::min(k, field.getNz() - 1));

    // Compute stress tensor at observer
    Tensor4x4 O_tensor = compute_stress_energy_tensor(field, i, j, k);

    // Extract strain
    StrainComponents result = compute_strain(O_tensor, config_.detector_normal);

    return result;
}

ProjectionOperators::CausalFlowVector ProjectionOperators::compute_causal_flow(
    const SymmetryField& field, int i, int j, int k) const
{
    CausalFlowVector B_vec;

    // Causal exchange vector B_μ represents direction of information flow
    // In IGSOA, this is related to phase gradients of δΦ
    //
    // B_i ~ Im(δΦ* ∂_i δΦ) / |δΦ|²
    //
    // Simplified implementation: use phase gradient

    std::complex<double> phi = field.getDeltaPhi(i, j, k);
    Vector3D grad_phi = field.computeGradient(i, j, k);

    double phi_norm_sq = std::norm(phi);

    if (phi_norm_sq > 1e-20) {
        // Spatial components
        B_vec.B1 = grad_phi.x / std::sqrt(phi_norm_sq);
        B_vec.B2 = grad_phi.y / std::sqrt(phi_norm_sq);
        B_vec.B3 = grad_phi.z / std::sqrt(phi_norm_sq);

        // Time component (simplified)
        B_vec.B0 = 1.0;  // Unit time flow
    } else {
        B_vec.B0 = 1.0;
        B_vec.B1 = 0.0;
        B_vec.B2 = 0.0;
        B_vec.B3 = 0.0;
    }

    // Magnitude (3-vector part)
    B_vec.magnitude = std::sqrt(B_vec.B1*B_vec.B1 +
                                 B_vec.B2*B_vec.B2 +
                                 B_vec.B3*B_vec.B3);

    return B_vec;
}

ProjectionOperators::FullProjection ProjectionOperators::compute_full_projection(
    const SymmetryField& field, int i, int j, int k) const
{
    FullProjection proj;
    proj.phi_mode = compute_phi_mode(field.getDeltaPhi(i, j, k));
    proj.O_tensor = compute_stress_energy_tensor(field, i, j, k);
    proj.B_vector = compute_causal_flow(field, i, j, k);
    proj.strain = compute_strain(proj.O_tensor, config_.detector_normal);
    return proj;
}

ProjectionOperators::StrainComponents ProjectionOperators::transform_gauge(
    const StrainComponents& strain, ProjectionConfig::Gauge target_gauge) const
{
    // TODO: Implement gauge transformation
    return strain;
}

Tensor4x4 ProjectionOperators::apply_TT_projection(const Tensor4x4& tensor) const {
    Tensor4x4 TT_tensor;

    // TT projection operator:
    // h^TT_ij = (P_ik P_jl - 1/2 P_ij P_kl) h_kl
    //
    // where P_ij = δ_ij - n_i n_j is the transverse projector
    // and n is the propagation direction

    // For now, simple traceless-symmetric extraction
    // (Full TT projection requires Fourier methods)

    // Copy spatial part
    for (int i = 1; i <= 3; i++) {
        for (int j = 1; j <= 3; j++) {
            TT_tensor(i, j) = tensor(i, j);
        }
    }

    // Make traceless
    double trace = TT_tensor(1,1) + TT_tensor(2,2) + TT_tensor(3,3);
    TT_tensor(1, 1) -= trace / 3.0;
    TT_tensor(2, 2) -= trace / 3.0;
    TT_tensor(3, 3) -= trace / 3.0;

    // Zero out time components
    for (int i = 0; i <= 3; i++) {
        TT_tensor(0, i) = 0.0;
        TT_tensor(i, 0) = 0.0;
    }

    return TT_tensor;
}

double ProjectionOperators::metric(int mu, int nu) const {
    // Minkowski metric: η_μν = diag(-1, 1, 1, 1)
    if (mu == nu) {
        return (mu == 0) ? -1.0 : 1.0;
    }
    return 0.0;
}

} // namespace gw
} // namespace igsoa
} // namespace dase
