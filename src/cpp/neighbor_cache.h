/**
 * Quantum Walk-Inspired Neighbor Cache
 *
 * Pre-computes and caches neighbor lists with coupling weights
 * Combines:
 * - Spatial hashing for fast neighbor discovery
 * - Kernel cache for fast weight computation
 * - Amplitude amplification tiering
 *
 * Expected speedup: 5-20x over naive neighbor search
 */

#pragma once

#include "spatial_hash.h"
#include "kernel_cache.h"
#include "igsoa_complex_node.h"
#include <vector>
#include <complex>

namespace dase {
namespace igsoa {

/**
 * Neighbor information for a single node
 */
struct NeighborInfo {
    int node_id;           // Index of neighbor node
    double weight;         // Pre-computed coupling weight K(distance, R_c)
    double distance;       // Distance (for debugging/analysis)
};

/**
 * 2D Neighbor Cache
 */
class NeighborCache2D {
private:
    std::vector<std::vector<NeighborInfo>> neighbor_lists_;
    KernelCache kernel_cache_;
    SpatialHash2D spatial_hash_;

    size_t N_x_, N_y_;
    double R_c_;
    bool is_built_;

    // Distance computation (toroidal)
    inline double wrappedDistance(int x1, int y1, int x2, int y2) const {
        int dx = std::abs(x1 - x2);
        int dy = std::abs(y1 - y2);

        dx = std::min(dx, static_cast<int>(N_x_) - dx);
        dy = std::min(dy, static_cast<int>(N_y_) - dy);

        return std::sqrt(static_cast<double>(dx * dx + dy * dy));
    }

public:
    NeighborCache2D(size_t N_x, size_t N_y, double R_c)
        : neighbor_lists_(N_x * N_y)
        , kernel_cache_(R_c, 1024)
        , spatial_hash_(N_x, N_y, R_c)
        , N_x_(N_x)
        , N_y_(N_y)
        , R_c_(R_c)
        , is_built_(false)
    {}

    /**
     * Build neighbor lists and pre-compute weights
     * Call once at initialization or when R_c changes
     */
    void build() {
        const size_t N_total = N_x_ * N_y_;

        // Clear previous data
        spatial_hash_.clear();
        for (auto& list : neighbor_lists_) {
            list.clear();
        }

        // Step 1: Populate spatial hash
        for (size_t i = 0; i < N_total; ++i) {
            int x = static_cast<int>(i % N_x_);
            int y = static_cast<int>(i / N_x_);
            spatial_hash_.insert(static_cast<int>(i), x, y);
        }

        // Step 2: Build neighbor lists using spatial hash
        const int R_c_int = static_cast<int>(std::ceil(R_c_));

        for (size_t i = 0; i < N_total; ++i) {
            int x_i = static_cast<int>(i % N_x_);
            int y_i = static_cast<int>(i / N_x_);

            // Query spatial hash for candidates
            auto candidates = spatial_hash_.query(x_i, y_i, R_c_int);

            // Filter by actual distance and pre-compute weights
            for (int j : candidates) {
                if (j == static_cast<int>(i)) continue;  // Skip self

                int x_j = static_cast<int>(j % N_x_);
                int y_j = static_cast<int>(j / N_x_);

                double dist = wrappedDistance(x_i, y_i, x_j, y_j);

                if (dist <= R_c_) {
                    NeighborInfo info;
                    info.node_id = j;
                    info.distance = dist;
                    info.weight = kernel_cache_.evaluateTiered(dist);

                    neighbor_lists_[i].push_back(info);
                }
            }
        }

        is_built_ = true;
    }

    /**
     * Rebuild cache (e.g., when R_c changes)
     */
    void rebuild(double new_R_c) {
        if (std::abs(new_R_c - R_c_) < 1e-10) return;  // No change

        R_c_ = new_R_c;
        kernel_cache_.rebuild(new_R_c);
        spatial_hash_ = SpatialHash2D(N_x_, N_y_, R_c_);
        build();
    }

    /**
     * Compute non-local coupling for node i
     * Uses pre-computed neighbor list (O(neighbors) instead of O(N))
     */
    std::complex<double> computeCoupling(
        size_t i,
        const std::vector<IGSOAComplexNode>& nodes
    ) const {
        if (!is_built_) return std::complex<double>(0, 0);

        std::complex<double> sum(0, 0);
        const auto& neighbors = neighbor_lists_[i];
        const auto& node_i = nodes[i];

        // Vectorizable loop (fixed-length, sequential access)
        for (const auto& neighbor : neighbors) {
            sum += neighbor.weight * (nodes[neighbor.node_id].psi - node_i.psi);
        }

        return sum;
    }

    /**
     * Get neighbor count for node i
     */
    size_t getNeighborCount(size_t i) const {
        return neighbor_lists_[i].size();
    }

    /**
     * Get average neighbor count
     */
    double getAverageNeighborCount() const {
        size_t total = 0;
        for (const auto& list : neighbor_lists_) {
            total += list.size();
        }
        return static_cast<double>(total) / neighbor_lists_.size();
    }

    /**
     * Get memory usage (bytes)
     */
    size_t getMemoryUsage() const {
        size_t total = kernel_cache_.getMemoryUsage();
        total += spatial_hash_.getMemoryUsage();

        for (const auto& list : neighbor_lists_) {
            total += list.capacity() * sizeof(NeighborInfo);
        }

        return total;
    }

    bool isBuilt() const { return is_built_; }
};

/**
 * 3D Neighbor Cache
 */
class NeighborCache3D {
private:
    std::vector<std::vector<NeighborInfo>> neighbor_lists_;
    KernelCache kernel_cache_;
    SpatialHash3D spatial_hash_;

    size_t N_x_, N_y_, N_z_;
    double R_c_;
    bool is_built_;

    // Distance computation (toroidal)
    inline double wrappedDistance(int x1, int y1, int z1, int x2, int y2, int z2) const {
        int dx = std::abs(x1 - x2);
        int dy = std::abs(y1 - y2);
        int dz = std::abs(z1 - z2);

        dx = std::min(dx, static_cast<int>(N_x_) - dx);
        dy = std::min(dy, static_cast<int>(N_y_) - dy);
        dz = std::min(dz, static_cast<int>(N_z_) - dz);

        return std::sqrt(static_cast<double>(dx * dx + dy * dy + dz * dz));
    }

public:
    NeighborCache3D(size_t N_x, size_t N_y, size_t N_z, double R_c)
        : neighbor_lists_(N_x * N_y * N_z)
        , kernel_cache_(R_c, 1024)
        , spatial_hash_(N_x, N_y, N_z, R_c)
        , N_x_(N_x)
        , N_y_(N_y)
        , N_z_(N_z)
        , R_c_(R_c)
        , is_built_(false)
    {}

    /**
     * Build neighbor lists and pre-compute weights
     */
    void build() {
        const size_t N_total = N_x_ * N_y_ * N_z_;
        const size_t plane_size = N_x_ * N_y_;

        // Clear previous data
        spatial_hash_.clear();
        for (auto& list : neighbor_lists_) {
            list.clear();
        }

        // Step 1: Populate spatial hash
        for (size_t i = 0; i < N_total; ++i) {
            int x = static_cast<int>(i % N_x_);
            int y = static_cast<int>((i / N_x_) % N_y_);
            int z = static_cast<int>(i / plane_size);
            spatial_hash_.insert(static_cast<int>(i), x, y, z);
        }

        // Step 2: Build neighbor lists
        const int R_c_int = static_cast<int>(std::ceil(R_c_));

        for (size_t i = 0; i < N_total; ++i) {
            int x_i = static_cast<int>(i % N_x_);
            int y_i = static_cast<int>((i / N_x_) % N_y_);
            int z_i = static_cast<int>(i / plane_size);

            // Query spatial hash
            auto candidates = spatial_hash_.query(x_i, y_i, z_i, R_c_int);

            // Filter and compute weights
            for (int j : candidates) {
                if (j == static_cast<int>(i)) continue;

                int x_j = static_cast<int>(j % N_x_);
                int y_j = static_cast<int>((j / N_x_) % N_y_);
                int z_j = static_cast<int>(j / plane_size);

                double dist = wrappedDistance(x_i, y_i, z_i, x_j, y_j, z_j);

                if (dist <= R_c_) {
                    NeighborInfo info;
                    info.node_id = j;
                    info.distance = dist;
                    info.weight = kernel_cache_.evaluateTiered(dist);

                    neighbor_lists_[i].push_back(info);
                }
            }
        }

        is_built_ = true;
    }

    /**
     * Rebuild cache
     */
    void rebuild(double new_R_c) {
        if (std::abs(new_R_c - R_c_) < 1e-10) return;

        R_c_ = new_R_c;
        kernel_cache_.rebuild(new_R_c);
        spatial_hash_ = SpatialHash3D(N_x_, N_y_, N_z_, R_c_);
        build();
    }

    /**
     * Compute non-local coupling for node i
     */
    std::complex<double> computeCoupling(
        size_t i,
        const std::vector<IGSOAComplexNode>& nodes
    ) const {
        if (!is_built_) return std::complex<double>(0, 0);

        std::complex<double> sum(0, 0);
        const auto& neighbors = neighbor_lists_[i];
        const auto& node_i = nodes[i];

        for (const auto& neighbor : neighbors) {
            sum += neighbor.weight * (nodes[neighbor.node_id].psi - node_i.psi);
        }

        return sum;
    }

    size_t getNeighborCount(size_t i) const {
        return neighbor_lists_[i].size();
    }

    double getAverageNeighborCount() const {
        size_t total = 0;
        for (const auto& list : neighbor_lists_) {
            total += list.size();
        }
        return static_cast<double>(total) / neighbor_lists_.size();
    }

    size_t getMemoryUsage() const {
        size_t total = kernel_cache_.getMemoryUsage();
        total += spatial_hash_.getMemoryUsage();

        for (const auto& list : neighbor_lists_) {
            total += list.capacity() * sizeof(NeighborInfo);
        }

        return total;
    }

    bool isBuilt() const { return is_built_; }
};

} // namespace igsoa
} // namespace dase
