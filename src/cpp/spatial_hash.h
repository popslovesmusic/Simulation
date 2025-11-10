/**
 * Spatial Hash Grid
 *
 * Quantum Walk-inspired spatial partitioning for O(1) neighbor queries
 * Instead of checking all N nodes, only check nodes in nearby cells
 *
 * Expected speedup: 5-20x for neighbor search
 */

#pragma once

#include <vector>
#include <unordered_map>
#include <cmath>
#include <algorithm>

namespace dase {
namespace igsoa {

/**
 * 1D Spatial Hash
 */
class SpatialHash1D {
private:
    std::unordered_map<int, std::vector<int>> cells_;
    int cell_size_;
    size_t N_;

public:
    explicit SpatialHash1D(size_t N, double R_c)
        : N_(N)
        , cell_size_(std::max(1, static_cast<int>(R_c)))
    {}

    void clear() {
        cells_.clear();
    }

    void insert(int node_id, int x) {
        int cell_x = x / cell_size_;
        cells_[cell_x].push_back(node_id);
    }

    std::vector<int> query(int x, int range) const {
        std::vector<int> result;
        int cell_x = x / cell_size_;
        int cell_range = (range + cell_size_ - 1) / cell_size_;

        for (int dx = -cell_range; dx <= cell_range; ++dx) {
            int key = cell_x + dx;
            auto it = cells_.find(key);
            if (it != cells_.end()) {
                result.insert(result.end(), it->second.begin(), it->second.end());
            }
        }

        return result;
    }
};

/**
 * 2D Spatial Hash
 */
class SpatialHash2D {
private:
    std::unordered_map<int64_t, std::vector<int>> cells_;
    int cell_size_;
    size_t N_x_, N_y_;

    // Hash function for 2D coordinates
    inline int64_t hash2D(int cx, int cy) const {
        return (static_cast<int64_t>(cx) << 32) | static_cast<int64_t>(cy);
    }

public:
    explicit SpatialHash2D(size_t N_x, size_t N_y, double R_c)
        : N_x_(N_x)
        , N_y_(N_y)
        , cell_size_(std::max(1, static_cast<int>(R_c)))
    {}

    void clear() {
        cells_.clear();
    }

    void insert(int node_id, int x, int y) {
        int cell_x = x / cell_size_;
        int cell_y = y / cell_size_;
        int64_t key = hash2D(cell_x, cell_y);
        cells_[key].push_back(node_id);
    }

    std::vector<int> query(int x, int y, int range) const {
        std::vector<int> result;
        result.reserve(100);  // Pre-allocate

        int cell_x = x / cell_size_;
        int cell_y = y / cell_size_;
        int cell_range = (range + cell_size_ - 1) / cell_size_;

        // Query 3x3 (or larger) cell neighborhood
        for (int dy = -cell_range; dy <= cell_range; ++dy) {
            for (int dx = -cell_range; dx <= cell_range; ++dx) {
                int64_t key = hash2D(cell_x + dx, cell_y + dy);
                auto it = cells_.find(key);
                if (it != cells_.end()) {
                    result.insert(result.end(), it->second.begin(), it->second.end());
                }
            }
        }

        return result;
    }

    size_t getMemoryUsage() const {
        size_t total = 0;
        for (const auto& pair : cells_) {
            total += pair.second.capacity() * sizeof(int);
        }
        return total + cells_.size() * (sizeof(int64_t) + sizeof(std::vector<int>));
    }
};

/**
 * 3D Spatial Hash
 */
class SpatialHash3D {
private:
    std::unordered_map<int64_t, std::vector<int>> cells_;
    int cell_size_;
    size_t N_x_, N_y_, N_z_;

    // Hash function for 3D coordinates (Morton code inspired)
    inline int64_t hash3D(int cx, int cy, int cz) const {
        // Pack into 64-bit: 21 bits each for x,y,z (supports up to 2M cells per dimension)
        int64_t hx = static_cast<int64_t>(cx) & 0x1FFFFF;
        int64_t hy = static_cast<int64_t>(cy) & 0x1FFFFF;
        int64_t hz = static_cast<int64_t>(cz) & 0x1FFFFF;
        return (hx << 42) | (hy << 21) | hz;
    }

public:
    explicit SpatialHash3D(size_t N_x, size_t N_y, size_t N_z, double R_c)
        : N_x_(N_x)
        , N_y_(N_y)
        , N_z_(N_z)
        , cell_size_(std::max(1, static_cast<int>(R_c)))
    {}

    void clear() {
        cells_.clear();
    }

    void insert(int node_id, int x, int y, int z) {
        int cell_x = x / cell_size_;
        int cell_y = y / cell_size_;
        int cell_z = z / cell_size_;
        int64_t key = hash3D(cell_x, cell_y, cell_z);
        cells_[key].push_back(node_id);
    }

    std::vector<int> query(int x, int y, int z, int range) const {
        std::vector<int> result;
        result.reserve(200);  // Pre-allocate for 3D

        int cell_x = x / cell_size_;
        int cell_y = y / cell_size_;
        int cell_z = z / cell_size_;
        int cell_range = (range + cell_size_ - 1) / cell_size_;

        // Query 3x3x3 (or larger) cell neighborhood
        for (int dz = -cell_range; dz <= cell_range; ++dz) {
            for (int dy = -cell_range; dy <= cell_range; ++dy) {
                for (int dx = -cell_range; dx <= cell_range; ++dx) {
                    int64_t key = hash3D(cell_x + dx, cell_y + dy, cell_z + dz);
                    auto it = cells_.find(key);
                    if (it != cells_.end()) {
                        result.insert(result.end(), it->second.begin(), it->second.end());
                    }
                }
            }
        }

        return result;
    }

    size_t getMemoryUsage() const {
        size_t total = 0;
        for (const auto& pair : cells_) {
            total += pair.second.capacity() * sizeof(int);
        }
        return total + cells_.size() * (sizeof(int64_t) + sizeof(std::vector<int>));
    }

    int getCellSize() const { return cell_size_; }
};

} // namespace igsoa
} // namespace dase
