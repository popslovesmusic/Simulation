/**
 * Engine FFT Analysis - Expose internal FFTW3 for field analysis
 *
 * Provides FFT analysis capabilities using DASE's internal FFTW3:
 * - Power spectrum computation
 * - Frequency domain analysis
 * - Peak detection in k-space
 * - Radial averaging for 2D/3D
 */

#pragma once

#include <string>
#include <vector>
#include <complex>
#include "json.hpp"

namespace dase {
namespace analysis {

struct FFTResult {
    // Spectrum data
    std::vector<double> frequencies;      // Frequency bins
    std::vector<double> power_spectrum;   // |FFT|^2
    std::vector<double> magnitude;        // |FFT|
    std::vector<double> phase;            // arg(FFT)

    // Statistics
    double dc_component;
    double peak_frequency;
    double peak_magnitude;
    double total_power;

    // Radial profile (for 2D/3D)
    std::vector<double> radial_k;         // Radial frequency bins
    std::vector<double> radial_power;     // Azimuthally averaged power

    // Metadata
    size_t N;                             // Number of points
    size_t N_x, N_y, N_z;                // Dimensions (for 2D/3D)
    std::string field_name;               // Which field was analyzed
    double execution_time_ms;
};

class EngineFFTAnalysis {
public:
    /**
     * Compute 1D FFT of a field
     *
     * @param field_data Real or imaginary values
     * @param field_name Name of the field
     * @return FFT result with spectrum
     */
    static FFTResult compute1DFFT(
        const std::vector<double>& field_data,
        const std::string& field_name
    );

    /**
     * Compute 2D FFT with radial averaging
     *
     * @param field_data Flattened 2D array
     * @param N_x Width
     * @param N_y Height
     * @param field_name Name of the field
     * @return FFT result with 2D spectrum and radial profile
     */
    static FFTResult compute2DFFT(
        const std::vector<double>& field_data,
        size_t N_x,
        size_t N_y,
        const std::string& field_name
    );

    /**
     * Compute 3D FFT with radial averaging
     *
     * @param field_data Flattened 3D array
     * @param N_x, N_y, N_z Dimensions
     * @param field_name Name of the field
     * @return FFT result with 3D spectrum and radial profile
     */
    static FFTResult compute3DFFT(
        const std::vector<double>& field_data,
        size_t N_x,
        size_t N_y,
        size_t N_z,
        const std::string& field_name
    );

    /**
     * Find peaks in power spectrum
     *
     * @param result FFT result
     * @param n_peaks Number of peaks to find
     * @param threshold Minimum threshold (fraction of max)
     * @return Vector of (frequency, magnitude) pairs
     */
    static std::vector<std::pair<double, double>> findPeaks(
        const FFTResult& result,
        size_t n_peaks = 10,
        double threshold = 0.01
    );

    /**
     * Export FFT result to JSON
     *
     * @param result FFT result
     * @return JSON representation
     */
    static nlohmann::json toJSON(const FFTResult& result);

private:
    // Radial averaging helper for 2D
    static void computeRadialProfile2D(
        FFTResult& result,
        const std::vector<std::complex<double>>& fft_data,
        size_t N_x,
        size_t N_y
    );

    // Radial averaging helper for 3D
    static void computeRadialProfile3D(
        FFTResult& result,
        const std::vector<std::complex<double>>& fft_data,
        size_t N_x,
        size_t N_y,
        size_t N_z
    );
};

} // namespace analysis
} // namespace dase
