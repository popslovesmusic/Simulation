/**
 * IGSOA Gravitational Wave Engine - Symmetry Field Implementation
 */

#include "symmetry_field.h"
#include <cmath>
#include <algorithm>
#include <stdexcept>
#include <fstream>

namespace dase {
namespace igsoa {
namespace gw {

// ============================================================================
// Vector3D Implementation
// ============================================================================

double Vector3D::magnitude() const {
    return std::sqrt(x*x + y*y + z*z);
}

Vector3D Vector3D::normalized() const {
    double mag = magnitude();
    if (mag < 1e-15) return Vector3D(0, 0, 0);
    return Vector3D(x/mag, y/mag, z/mag);
}

Vector3D Vector3D::operator+(const Vector3D& other) const {
    return Vector3D(x + other.x, y + other.y, z + other.z);
}

Vector3D Vector3D::operator-(const Vector3D& other) const {
    return Vector3D(x - other.x, y - other.y, z - other.z);
}

Vector3D Vector3D::operator*(double scalar) const {
    return Vector3D(x * scalar, y * scalar, z * scalar);
}

double Vector3D::dot(const Vector3D& other) const {
    return x * other.x + y * other.y + z * other.z;
}

Vector3D Vector3D::cross(const Vector3D& other) const {
    return Vector3D(
        y * other.z - z * other.y,
        z * other.x - x * other.z,
        x * other.y - y * other.x
    );
}

// ============================================================================
// Tensor4x4 Implementation
// ============================================================================

Tensor4x4::Tensor4x4() {
    for (int mu = 0; mu < 4; mu++) {
        for (int nu = 0; nu < 4; nu++) {
            components[mu][nu] = 0.0;
        }
    }
}

double& Tensor4x4::operator()(int mu, int nu) {
    return components[mu][nu];
}

const double& Tensor4x4::operator()(int mu, int nu) const {
    return components[mu][nu];
}

double Tensor4x4::trace() const {
    return components[0][0] + components[1][1] + components[2][2] + components[3][3];
}

Tensor4x4 Tensor4x4::transpose() const {
    Tensor4x4 result;
    for (int mu = 0; mu < 4; mu++) {
        for (int nu = 0; nu < 4; nu++) {
            result(mu, nu) = components[nu][mu];
        }
    }
    return result;
}

// ============================================================================
// SymmetryFieldConfig Implementation
// ============================================================================

SymmetryFieldConfig::SymmetryFieldConfig()
    : nx(64), ny(64), nz(64)
    , dx(1000.0), dy(1000.0), dz(1000.0)  // 1 km grid spacing
    , R_c_default(0.5)
    , kappa(1.0)
    , lambda(0.1)
    , alpha_min(1.0)   // Maximum memory (near horizon)
    , alpha_max(2.0)   // No memory (flat spacetime)
    , dt(0.001)        // 1 ms timestep
{
}

// ============================================================================
// SymmetryField Implementation
// ============================================================================

SymmetryField::SymmetryField(const SymmetryFieldConfig& config)
    : config_(config)
    , current_time_(0.0)
{
    int total = config_.nx * config_.ny * config_.nz;

    // Allocate 3D grids (flattened)
    delta_phi_.resize(total, std::complex<double>(0.0, 0.0));
    alpha_.resize(total, config_.alpha_max);  // Start with no memory
    gradient_magnitude_.resize(total, 0.0);
    potential_.resize(total, 0.0);
}

SymmetryField::~SymmetryField() {
    // Vectors handle their own cleanup
}

// === Grid Access ===

std::complex<double> SymmetryField::getDeltaPhi(int i, int j, int k) const {
    if (!isValidIndex(i, j, k)) {
        throw std::out_of_range("Grid index out of bounds");
    }
    int idx = toFlatIndex(i, j, k);
    return delta_phi_[idx];
}

void SymmetryField::setDeltaPhi(int i, int j, int k, std::complex<double> value) {
    if (!isValidIndex(i, j, k)) {
        throw std::out_of_range("Grid index out of bounds");
    }
    int idx = toFlatIndex(i, j, k);
    delta_phi_[idx] = value;
}

std::complex<double> SymmetryField::getDeltaPhiAt(const Vector3D& position) const {
    return interpolateDeltaPhi(position);
}

double SymmetryField::getAlpha(int i, int j, int k) const {
    if (!isValidIndex(i, j, k)) {
        throw std::out_of_range("Grid index out of bounds");
    }
    int idx = toFlatIndex(i, j, k);
    return alpha_[idx];
}

void SymmetryField::setAlpha(int i, int j, int k, double alpha) {
    if (!isValidIndex(i, j, k)) {
        throw std::out_of_range("Grid index out of bounds");
    }
    if (alpha < config_.alpha_min || alpha > config_.alpha_max) {
        throw std::invalid_argument("Alpha out of valid range [alpha_min, alpha_max]");
    }
    int idx = toFlatIndex(i, j, k);
    alpha_[idx] = alpha;
}

double SymmetryField::getAlphaAt(const Vector3D& position) const {
    return interpolateAlpha(position);
}

const std::vector<std::complex<double>>& SymmetryField::getDeltaPhiFlat() const {
    return delta_phi_;
}

std::vector<double> SymmetryField::getAlphaValues() const {
    return alpha_;
}

// === Spatial Derivatives ===

Vector3D SymmetryField::computeGradient(int i, int j, int k) const {
    // Implement centered finite difference
    // ∇δΦ = (∂ₓδΦ, ∂ᵧδΦ, ∂_zδΦ)
    // Use second-order centered: ∂ₓf ≈ (f[i+1] - f[i-1]) / (2*dx)

    Vector3D grad(0, 0, 0);

    // Handle boundary conditions (use one-sided differences at edges)
    if (i == 0 || i == config_.nx - 1 ||
        j == 0 || j == config_.ny - 1 ||
        k == 0 || k == config_.nz - 1) {
        return grad;  // Zero gradient at boundaries
    }

    // X-direction derivative
    std::complex<double> phi_xp = getDeltaPhi(i+1, j, k);
    std::complex<double> phi_xm = getDeltaPhi(i-1, j, k);
    std::complex<double> dphidx = (phi_xp - phi_xm) / (2.0 * config_.dx);
    grad.x = std::abs(dphidx);

    // Y-direction derivative
    std::complex<double> phi_yp = getDeltaPhi(i, j+1, k);
    std::complex<double> phi_ym = getDeltaPhi(i, j-1, k);
    std::complex<double> dphidy = (phi_yp - phi_ym) / (2.0 * config_.dy);
    grad.y = std::abs(dphidy);

    // Z-direction derivative
    std::complex<double> phi_zp = getDeltaPhi(i, j, k+1);
    std::complex<double> phi_zm = getDeltaPhi(i, j, k-1);
    std::complex<double> dphidz = (phi_zp - phi_zm) / (2.0 * config_.dz);
    grad.z = std::abs(dphidz);

    return grad;
}

std::complex<double> SymmetryField::computeLaplacian(int i, int j, int k) const {
    // Implement 3D Laplacian
    // ∇²δΦ = ∂²ₓδΦ + ∂²ᵧδΦ + ∂²_zδΦ
    // Use second-order centered: ∂²ₓf ≈ (f[i+1] - 2f[i] + f[i-1]) / dx²

    std::complex<double> laplacian(0.0, 0.0);

    // Handle boundary conditions (zero Laplacian at edges)
    if (i == 0 || i == config_.nx - 1 ||
        j == 0 || j == config_.ny - 1 ||
        k == 0 || k == config_.nz - 1) {
        return laplacian;
    }

    std::complex<double> phi_center = getDeltaPhi(i, j, k);

    // X-direction second derivative
    std::complex<double> phi_xp = getDeltaPhi(i+1, j, k);
    std::complex<double> phi_xm = getDeltaPhi(i-1, j, k);
    std::complex<double> d2phidx2 = (phi_xp - 2.0*phi_center + phi_xm) / (config_.dx * config_.dx);

    // Y-direction second derivative
    std::complex<double> phi_yp = getDeltaPhi(i, j+1, k);
    std::complex<double> phi_ym = getDeltaPhi(i, j-1, k);
    std::complex<double> d2phidy2 = (phi_yp - 2.0*phi_center + phi_ym) / (config_.dy * config_.dy);

    // Z-direction second derivative
    std::complex<double> phi_zp = getDeltaPhi(i, j, k+1);
    std::complex<double> phi_zm = getDeltaPhi(i, j, k-1);
    std::complex<double> d2phidz2 = (phi_zp - 2.0*phi_center + phi_zm) / (config_.dz * config_.dz);

    // Sum to get Laplacian
    laplacian = d2phidx2 + d2phidy2 + d2phidz2;

    return laplacian;
}

double SymmetryField::getGradientMagnitude(int i, int j, int k) const {
    int idx = toFlatIndex(i, j, k);
    return gradient_magnitude_[idx];
}

void SymmetryField::updateGradientCache() {
    // TODO: Loop over all grid points and compute gradients
    for (int i = 1; i < config_.nx - 1; i++) {
        for (int j = 1; j < config_.ny - 1; j++) {
            for (int k = 1; k < config_.nz - 1; k++) {
                Vector3D grad = computeGradient(i, j, k);
                int idx = toFlatIndex(i, j, k);
                gradient_magnitude_[idx] = grad.magnitude();
            }
        }
    }
}

// === Effective Potential ===

double SymmetryField::computePotential(int i, int j, int k) const {
    // TODO: Implement asymmetry potential
    // V(δΦ) = λ |δΦ|² + κ |δΦ|⁴

    std::complex<double> phi = getDeltaPhi(i, j, k);
    double abs_phi_sq = std::norm(phi);  // |δΦ|²

    double V = config_.lambda * abs_phi_sq
             + config_.kappa * abs_phi_sq * abs_phi_sq;

    return V;
}

std::complex<double> SymmetryField::computePotentialDerivative(int i, int j, int k) const {
    // TODO: Implement ∂V/∂δΦ
    // For V = λ|δΦ|² + κ|δΦ|⁴
    // ∂V/∂δΦ* = λδΦ + 2κ|δΦ|²δΦ

    std::complex<double> phi = getDeltaPhi(i, j, k);
    double abs_phi_sq = std::norm(phi);

    std::complex<double> dV = config_.lambda * phi
                             + 2.0 * config_.kappa * abs_phi_sq * phi;

    return dV;
}

double SymmetryField::getPotential(int i, int j, int k) const {
    int idx = toFlatIndex(i, j, k);
    return potential_[idx];
}

void SymmetryField::updatePotentialCache() {
    // TODO: Loop over all grid points and compute potentials
    for (int i = 0; i < config_.nx; i++) {
        for (int j = 0; j < config_.ny; j++) {
            for (int k = 0; k < config_.nz; k++) {
                int idx = toFlatIndex(i, j, k);
                potential_[idx] = computePotential(i, j, k);
            }
        }
    }
}

// === Field Evolution ===

void SymmetryField::evolveStep(
    const std::vector<std::complex<double>>& fractional_derivatives,
    const std::vector<std::complex<double>>& source_terms)
{
    // Implement fractional wave equation evolution
    // ∂²ₓψ - ₀D^α_t ψ - V(δΦ)ψ = S
    //
    // Rearranged for time stepping:
    // ψ(t+dt) ≈ ψ(t) + dt * [∂²ₓψ - ₀D^α_t ψ - V(δΦ)ψ + S]
    //
    // Components:
    // - ∂²ₓψ = Laplacian (spatial part)
    // - ₀D^α_t ψ = fractional_derivatives (from FractionalSolver)
    // - V(δΦ)ψ = potential term
    // - S = source_terms (binary merger)

    int total = getTotalPoints();
    std::vector<std::complex<double>> new_field(total);

    // Evolve each grid point
    for (int i = 1; i < config_.nx - 1; i++) {
        for (int j = 1; j < config_.ny - 1; j++) {
            for (int k = 1; k < config_.nz - 1; k++) {
                int idx = toFlatIndex(i, j, k);

                // Get current field value
                std::complex<double> psi = getDeltaPhi(i, j, k);

                // Compute spatial derivatives (Laplacian)
                std::complex<double> laplacian = computeLaplacian(i, j, k);

                // Get fractional time derivative
                std::complex<double> frac_deriv = fractional_derivatives[idx];

                // Get potential
                double V = getPotential(i, j, k);

                // Get source term
                std::complex<double> source = source_terms[idx];

                // Fractional wave equation right-hand side:
                // RHS = ∂²ₓψ - ₀D^α_t ψ - V·ψ + S
                std::complex<double> rhs = laplacian - frac_deriv - V * psi + source;

                // Forward Euler step (simple first-order time integration)
                // For production, use RK4 or other higher-order method
                new_field[idx] = psi + config_.dt * rhs;
            }
        }
    }

    // Update field with new values (interior points only)
    for (int i = 1; i < config_.nx - 1; i++) {
        for (int j = 1; j < config_.ny - 1; j++) {
            for (int k = 1; k < config_.nz - 1; k++) {
                int idx = toFlatIndex(i, j, k);
                delta_phi_[idx] = new_field[idx];
            }
        }
    }

    // Boundary conditions: maintain current values at boundaries
    // (Zero-gradient boundary condition implicit)

    // Update gradient and potential caches
    updateGradientCache();
    updatePotentialCache();

    // Advance time
    current_time_ += config_.dt;
}

// === Grid Info ===

int SymmetryField::toFlatIndex(int i, int j, int k) const {
    return i + config_.nx * (j + config_.ny * k);
}

void SymmetryField::fromFlatIndex(int idx, int& i, int& j, int& k) const {
    k = idx / (config_.nx * config_.ny);
    int remainder = idx % (config_.nx * config_.ny);
    j = remainder / config_.nx;
    i = remainder % config_.nx;
}

Vector3D SymmetryField::toPosition(int i, int j, int k) const {
    return Vector3D(
        i * config_.dx,
        j * config_.dy,
        k * config_.dz
    );
}

void SymmetryField::toIndices(const Vector3D& pos, int& i, int& j, int& k) const {
    i = static_cast<int>(pos.x / config_.dx + 0.5);
    j = static_cast<int>(pos.y / config_.dy + 0.5);
    k = static_cast<int>(pos.z / config_.dz + 0.5);
}

// === Diagnostics ===

double SymmetryField::computeTotalEnergy() const {
    double energy = 0.0;
    double dV = config_.dx * config_.dy * config_.dz;

    for (const auto& phi : delta_phi_) {
        energy += std::norm(phi) * dV;
    }

    return energy;
}

double SymmetryField::computeMaxAmplitude() const {
    double max_amp = 0.0;

    for (const auto& phi : delta_phi_) {
        double amp = std::abs(phi);
        if (amp > max_amp) {
            max_amp = amp;
        }
    }

    return max_amp;
}

SymmetryField::FieldStats SymmetryField::getStatistics() const {
    FieldStats stats;

    stats.max_amplitude = 0.0;
    stats.total_energy = 0.0;
    double sum_amplitude = 0.0;
    double sum_gradient = 0.0;
    stats.max_gradient = 0.0;

    double dV = config_.dx * config_.dy * config_.dz;
    int total_points = getTotalPoints();

    // Compute all statistics in one pass
    for (int idx = 0; idx < total_points; idx++) {
        // Amplitude statistics
        double amp = std::abs(delta_phi_[idx]);
        sum_amplitude += amp;
        if (amp > stats.max_amplitude) {
            stats.max_amplitude = amp;
        }

        // Energy
        stats.total_energy += std::norm(delta_phi_[idx]) * dV;

        // Gradient statistics
        double grad = gradient_magnitude_[idx];
        sum_gradient += grad;
        if (grad > stats.max_gradient) {
            stats.max_gradient = grad;
        }
    }

    // Compute means
    stats.mean_amplitude = sum_amplitude / total_points;
    stats.mean_gradient = sum_gradient / total_points;

    return stats;
}

void SymmetryField::exportToFile(const std::string& filename) const {
    // TODO: Export to VTK or HDF5 for visualization
    std::ofstream file(filename);

    if (!file.is_open()) {
        throw std::runtime_error("Cannot open file for export");
    }

    // Placeholder - write simple text format
    file << "# SymmetryField Export\n";
    file << "# nx=" << config_.nx << " ny=" << config_.ny << " nz=" << config_.nz << "\n";
    file << "# time=" << current_time_ << "\n";

    // TODO: Write actual data

    file.close();
}

// === Private Helpers ===

bool SymmetryField::isValidIndex(int i, int j, int k) const {
    return (i >= 0 && i < config_.nx) &&
           (j >= 0 && j < config_.ny) &&
           (k >= 0 && k < config_.nz);
}

std::complex<double> SymmetryField::interpolateDeltaPhi(const Vector3D& pos) const {
    // Trilinear interpolation of δΦ at arbitrary position

    // Find grid cell containing position
    double fx = pos.x / config_.dx;
    double fy = pos.y / config_.dy;
    double fz = pos.z / config_.dz;

    int i0 = static_cast<int>(std::floor(fx));
    int j0 = static_cast<int>(std::floor(fy));
    int k0 = static_cast<int>(std::floor(fz));

    int i1 = i0 + 1;
    int j1 = j0 + 1;
    int k1 = k0 + 1;

    // Check bounds
    if (i0 < 0 || i1 >= config_.nx ||
        j0 < 0 || j1 >= config_.ny ||
        k0 < 0 || k1 >= config_.nz) {
        return std::complex<double>(0.0, 0.0);
    }

    // Interpolation weights
    double wx1 = fx - i0;
    double wy1 = fy - j0;
    double wz1 = fz - k0;
    double wx0 = 1.0 - wx1;
    double wy0 = 1.0 - wy1;
    double wz0 = 1.0 - wz1;

    // Get 8 corner values
    std::complex<double> c000 = getDeltaPhi(i0, j0, k0);
    std::complex<double> c001 = getDeltaPhi(i0, j0, k1);
    std::complex<double> c010 = getDeltaPhi(i0, j1, k0);
    std::complex<double> c011 = getDeltaPhi(i0, j1, k1);
    std::complex<double> c100 = getDeltaPhi(i1, j0, k0);
    std::complex<double> c101 = getDeltaPhi(i1, j0, k1);
    std::complex<double> c110 = getDeltaPhi(i1, j1, k0);
    std::complex<double> c111 = getDeltaPhi(i1, j1, k1);

    // Trilinear interpolation
    std::complex<double> result =
        c000 * wx0 * wy0 * wz0 +
        c001 * wx0 * wy0 * wz1 +
        c010 * wx0 * wy1 * wz0 +
        c011 * wx0 * wy1 * wz1 +
        c100 * wx1 * wy0 * wz0 +
        c101 * wx1 * wy0 * wz1 +
        c110 * wx1 * wy1 * wz0 +
        c111 * wx1 * wy1 * wz1;

    return result;
}

double SymmetryField::interpolateAlpha(const Vector3D& pos) const {
    // Trilinear interpolation of α at arbitrary position

    // Find grid cell containing position
    double fx = pos.x / config_.dx;
    double fy = pos.y / config_.dy;
    double fz = pos.z / config_.dz;

    int i0 = static_cast<int>(std::floor(fx));
    int j0 = static_cast<int>(std::floor(fy));
    int k0 = static_cast<int>(std::floor(fz));

    int i1 = i0 + 1;
    int j1 = j0 + 1;
    int k1 = k0 + 1;

    // Check bounds
    if (i0 < 0 || i1 >= config_.nx ||
        j0 < 0 || j1 >= config_.ny ||
        k0 < 0 || k1 >= config_.nz) {
        return config_.alpha_max;
    }

    // Interpolation weights
    double wx1 = fx - i0;
    double wy1 = fy - j0;
    double wz1 = fz - k0;
    double wx0 = 1.0 - wx1;
    double wy0 = 1.0 - wy1;
    double wz0 = 1.0 - wz1;

    // Get 8 corner values
    double a000 = getAlpha(i0, j0, k0);
    double a001 = getAlpha(i0, j0, k1);
    double a010 = getAlpha(i0, j1, k0);
    double a011 = getAlpha(i0, j1, k1);
    double a100 = getAlpha(i1, j0, k0);
    double a101 = getAlpha(i1, j0, k1);
    double a110 = getAlpha(i1, j1, k0);
    double a111 = getAlpha(i1, j1, k1);

    // Trilinear interpolation
    double result =
        a000 * wx0 * wy0 * wz0 +
        a001 * wx0 * wy0 * wz1 +
        a010 * wx0 * wy1 * wz0 +
        a011 * wx0 * wy1 * wz1 +
        a100 * wx1 * wy0 * wz0 +
        a101 * wx1 * wy0 * wz1 +
        a110 * wx1 * wy1 * wz0 +
        a111 * wx1 * wy1 * wz1;

    return result;
}

} // namespace gw
} // namespace igsoa
} // namespace dase
