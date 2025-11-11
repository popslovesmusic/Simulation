/**
 * IGSOA Gravitational Wave Engine - Binary Merger Source Manager Implementation
 */

#define _USE_MATH_DEFINES  // Enable M_PI on MSVC
#include <cmath>
#include "source_manager.h"
#include <iostream>
#include <iomanip>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace dase {
namespace igsoa {
namespace gw {

// ============================================================================
// Constructor and Initialization
// ============================================================================

BinaryMerger::BinaryMerger(const BinaryMergerConfig& config)
    : config_(config)
    , current_separation_(config.initial_separation)
    , current_phase_(config.initial_orbital_phase)
    , current_omega_(0.0)
    , position1_(0, 0, 0)
    , position2_(0, 0, 0)
    , r1_(0.0)
    , r2_(0.0)
    , total_mass_(0.0)
    , reduced_mass_(0.0)
    , schwarzschild_radius_(0.0)
    , merger_radius_(0.0)
    , total_energy_radiated_(0.0)
    , has_merged_(false)
{
    initialize();
}

BinaryMerger::~BinaryMerger() {
    // Nothing to clean up
}

void BinaryMerger::initialize() {
    // Convert masses to kg
    total_mass_ = (config_.mass1 + config_.mass2) * M_sun;
    reduced_mass_ = (config_.mass1 * config_.mass2) / (config_.mass1 + config_.mass2) * M_sun;

    // Compute Schwarzschild radius
    schwarzschild_radius_ = 2.0 * G * total_mass_ / (c * c);

    // Merger radius
    merger_radius_ = config_.merger_threshold * schwarzschild_radius_;

    // Reduced orbital radii (from center of mass)
    double mass_ratio = config_.mass2 / (config_.mass1 + config_.mass2);
    r1_ = mass_ratio * current_separation_;
    r2_ = (1.0 - mass_ratio) * current_separation_;

    // Initial orbital frequency
    current_omega_ = computeOrbitalFrequency(current_separation_);

    // Initial positions
    updatePositions();

    // Reset state
    total_energy_radiated_ = 0.0;
    has_merged_ = false;
}

// ============================================================================
// Orbital Evolution
// ============================================================================

void BinaryMerger::evolveOrbit(double dt) {
    // Check if already merged
    if (has_merged_) {
        return;
    }

    // Update phase (always happens)
    current_phase_ += current_omega_ * dt;

    // Wrap phase to [0, 2π)
    while (current_phase_ >= 2.0 * M_PI) {
        current_phase_ -= 2.0 * M_PI;
    }

    // If inspiral enabled, evolve separation
    if (config_.enable_inspiral) {
        double drdt = computeInspiralRate();
        current_separation_ += drdt * dt;

        // Update reduced radii
        double mass_ratio = config_.mass2 / (config_.mass1 + config_.mass2);
        r1_ = mass_ratio * current_separation_;
        r2_ = (1.0 - mass_ratio) * current_separation_;

        // Update orbital frequency
        current_omega_ = computeOrbitalFrequency(current_separation_);

        // Check for merger
        if (current_separation_ <= merger_radius_) {
            has_merged_ = true;
            std::cout << "MERGER OCCURRED at t = " << dt << " s, r = "
                      << current_separation_ / 1e3 << " km" << std::endl;
        }

        // Track energy radiated (approximate)
        // L_GW = (32/5) G⁴/c⁵ (m₁m₂)²(m₁+m₂)/r⁵
        double m1_kg = config_.mass1 * M_sun;
        double m2_kg = config_.mass2 * M_sun;
        double r5 = std::pow(current_separation_, 5);

        double L_GW = (32.0/5.0) * std::pow(G, 4) / std::pow(c, 5)
                    * std::pow(m1_kg * m2_kg, 2) * total_mass_ / r5;

        total_energy_radiated_ += L_GW * dt;
    }

    // Update positions
    updatePositions();
}

void BinaryMerger::reset() {
    current_separation_ = config_.initial_separation;
    current_phase_ = config_.initial_orbital_phase;
    total_energy_radiated_ = 0.0;
    has_merged_ = false;
    initialize();
}

// ============================================================================
// Source Term Generation
// ============================================================================

std::vector<std::complex<double>> BinaryMerger::computeSourceTerms(
    const SymmetryField& field,
    double t) const
{
    int total_points = field.getTotalPoints();
    std::vector<std::complex<double>> sources(total_points, std::complex<double>(0.0, 0.0));

    // If merged, no more source terms
    if (has_merged_) {
        return sources;
    }

    // Get grid configuration
    const SymmetryFieldConfig& grid_config = field.getConfig();

    // Compute sources for each grid point
    for (int i = 0; i < grid_config.nx; i++) {
        for (int j = 0; j < grid_config.ny; j++) {
            for (int k = 0; k < grid_config.nz; k++) {
                // Get position of this grid point
                Vector3D pos = field.toPosition(i, j, k);

                // Compute contribution from BH 1
                std::complex<double> S1 = computeGaussianSource(
                    pos, position1_, config_.mass1);

                // Compute contribution from BH 2
                std::complex<double> S2 = computeGaussianSource(
                    pos, position2_, config_.mass2);

                // Total source
                int idx = field.toFlatIndex(i, j, k);
                sources[idx] = (S1 + S2) * config_.source_amplitude;
            }
        }
    }

    return sources;
}

// ============================================================================
// Query Methods
// ============================================================================

Vector3D BinaryMerger::getPosition1() const {
    return position1_;
}

Vector3D BinaryMerger::getPosition2() const {
    return position2_;
}

double BinaryMerger::getSeparation() const {
    return current_separation_;
}

double BinaryMerger::getOrbitalFrequency() const {
    return current_omega_;
}

double BinaryMerger::getOrbitalPhase() const {
    return current_phase_;
}

bool BinaryMerger::hasMerged() const {
    return has_merged_;
}

double BinaryMerger::getTimeToMerger() const {
    if (!config_.enable_inspiral || has_merged_) {
        return -1.0;
    }

    // Approximate time to merger using Peters & Mathews (1963)
    // τ = (5/256) c⁵r⁴ / (G³m₁m₂(m₁+m₂))
    double m1_kg = config_.mass1 * M_sun;
    double m2_kg = config_.mass2 * M_sun;

    double numerator = (5.0/256.0) * std::pow(c, 5) * std::pow(current_separation_, 4);
    double denominator = std::pow(G, 3) * m1_kg * m2_kg * total_mass_;

    return numerator / denominator;
}

double BinaryMerger::getTotalMass() const {
    return config_.mass1 + config_.mass2;
}

double BinaryMerger::getReducedMass() const {
    return (config_.mass1 * config_.mass2) / (config_.mass1 + config_.mass2);
}

double BinaryMerger::getSchwarzchildRadius() const {
    return schwarzschild_radius_;
}

double BinaryMerger::getTotalEnergyRadiated() const {
    return total_energy_radiated_;
}

void BinaryMerger::printState() const {
    std::cout << std::fixed << std::setprecision(3);
    std::cout << "Binary Merger State:" << std::endl;
    std::cout << "  Separation: " << current_separation_ / 1e3 << " km" << std::endl;
    std::cout << "  Phase: " << current_phase_ << " rad" << std::endl;
    std::cout << "  Frequency: " << current_omega_ << " rad/s ("
              << current_omega_ / (2.0 * M_PI) << " Hz)" << std::endl;
    std::cout << "  BH1 position: (" << position1_.x / 1e3 << ", "
              << position1_.y / 1e3 << ", " << position1_.z / 1e3 << ") km" << std::endl;
    std::cout << "  BH2 position: (" << position2_.x / 1e3 << ", "
              << position2_.y / 1e3 << ", " << position2_.z / 1e3 << ") km" << std::endl;
    std::cout << "  Merged: " << (has_merged_ ? "YES" : "NO") << std::endl;

    if (config_.enable_inspiral && !has_merged_) {
        std::cout << "  Time to merger: " << getTimeToMerger() << " s" << std::endl;
        std::cout << "  Energy radiated: " << total_energy_radiated_ << " J" << std::endl;
    }
}

// ============================================================================
// Internal Methods
// ============================================================================

double BinaryMerger::computeOrbitalFrequency(double separation) const {
    // Kepler's third law: ω² = GM/r³
    double omega_squared = G * total_mass_ / std::pow(separation, 3);
    return std::sqrt(omega_squared);
}

double BinaryMerger::computeInspiralRate() const {
    // Peters & Mathews (1963) inspiral equation:
    // dr/dt = -(64/5) G³m₁m₂(m₁+m₂) / (c⁵r³)

    double m1_kg = config_.mass1 * M_sun;
    double m2_kg = config_.mass2 * M_sun;
    double r3 = std::pow(current_separation_, 3);

    double drdt = -(64.0/5.0) * std::pow(G, 3) * m1_kg * m2_kg * total_mass_
                / (std::pow(c, 5) * r3);

    return drdt;
}

void BinaryMerger::updatePositions() {
    // Circular orbit in xy-plane
    // BH1 at (r₁ cos φ, r₁ sin φ, 0)
    // BH2 at (-r₂ cos φ, -r₂ sin φ, 0)

    double cos_phi = std::cos(current_phase_);
    double sin_phi = std::sin(current_phase_);

    position1_.x = config_.center.x + r1_ * cos_phi;
    position1_.y = config_.center.y + r1_ * sin_phi;
    position1_.z = config_.center.z;

    position2_.x = config_.center.x - r2_ * cos_phi;
    position2_.y = config_.center.y - r2_ * sin_phi;
    position2_.z = config_.center.z;
}

std::complex<double> BinaryMerger::computeGaussianSource(
    const Vector3D& position,
    const Vector3D& bh_position,
    double mass) const
{
    // Compute distance squared
    double dx = position.x - bh_position.x;
    double dy = position.y - bh_position.y;
    double dz = position.z - bh_position.z;
    double r_squared = dx*dx + dy*dy + dz*dz;

    // Gaussian profile: A exp(-r²/(2σ²))
    // Amplitude scales with mass
    double sigma_squared = config_.gaussian_width * config_.gaussian_width;
    double amplitude = mass / config_.mass1;  // Normalize to mass1

    double gaussian = amplitude * std::exp(-r_squared / (2.0 * sigma_squared));

    // Return as complex (real part only for now)
    // Could add phase based on orbital motion for more realism
    return std::complex<double>(gaussian, 0.0);
}

} // namespace gw
} // namespace igsoa
} // namespace dase
