/**
 * Engine FFT Analysis Implementation
 */

#include "engine_fft_analysis.h"
#include <cmath>
#include <algorithm>
#include <chrono>

#ifdef USE_FFTW3
#include <fftw3.h>
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace dase {
namespace analysis {

FFTResult EngineFFTAnalysis::compute1DFFT(
    const std::vector<double>& field_data,
    const std::string& field_name
) {
    auto start_time = std::chrono::high_resolution_clock::now();

#ifndef USE_FFTW3
    // Return error if FFTW3 not available
    FFTResult result;
    result.N = field_data.size();
    result.field_name = field_name;
    result.N_x = result.N;
    result.N_y = 1;
    result.N_z = 1;

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
    result.execution_time_ms = duration.count() / 1000.0;

    throw std::runtime_error("FFTW3 not available - FFT analysis disabled");
    return result;
#else

    FFTResult result;
    result.N = field_data.size();
    result.N_x = result.N;
    result.N_y = 1;
    result.N_z = 1;
    result.field_name = field_name;

    // Allocate FFTW arrays
    double* in = fftw_alloc_real(result.N);
    fftw_complex* out = fftw_alloc_complex(result.N / 2 + 1);

    // Copy input data
    for (size_t i = 0; i < result.N; ++i) {
        in[i] = field_data[i];
    }

    // Create plan and execute
    fftw_plan plan = fftw_plan_dft_r2c_1d(static_cast<int>(result.N), in, out, FFTW_ESTIMATE);
    fftw_execute(plan);

    // Process results
    size_t half_N = result.N / 2 + 1;
    result.frequencies.resize(half_N);
    result.power_spectrum.resize(half_N);
    result.magnitude.resize(half_N);
    result.phase.resize(half_N);

    result.total_power = 0.0;
    result.peak_magnitude = 0.0;
    result.peak_frequency = 0.0;

    for (size_t i = 0; i < half_N; ++i) {
        double re = out[i][0];
        double im = out[i][1];

        result.magnitude[i] = std::sqrt(re * re + im * im);
        result.power_spectrum[i] = result.magnitude[i] * result.magnitude[i];
        result.phase[i] = std::atan2(im, re);
        result.frequencies[i] = static_cast<double>(i) / static_cast<double>(result.N);

        result.total_power += result.power_spectrum[i];

        if (i > 0 && result.magnitude[i] > result.peak_magnitude) {
            result.peak_magnitude = result.magnitude[i];
            result.peak_frequency = result.frequencies[i];
        }
    }

    result.dc_component = result.magnitude[0];

    // Cleanup
    fftw_destroy_plan(plan);
    fftw_free(in);
    fftw_free(out);

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    result.execution_time_ms = duration.count();

    return result;
#endif // USE_FFTW3
}

FFTResult EngineFFTAnalysis::compute2DFFT(
    const std::vector<double>& field_data,
    size_t N_x,
    size_t N_y,
    const std::string& field_name
) {
    auto start_time = std::chrono::high_resolution_clock::now();

#ifndef USE_FFTW3
    // Return error if FFTW3 not available
    FFTResult result;
    result.N = N_x * N_y;
    result.N_x = N_x;
    result.N_y = N_y;
    result.N_z = 1;
    result.field_name = field_name;

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
    result.execution_time_ms = duration.count() / 1000.0;

    throw std::runtime_error("FFTW3 not available - FFT analysis disabled");
    return result;
#else

    FFTResult result;
    result.N = N_x * N_y;
    result.N_x = N_x;
    result.N_y = N_y;
    result.N_z = 1;
    result.field_name = field_name;

    // Allocate FFTW arrays
    double* in = fftw_alloc_real(result.N);
    fftw_complex* out = fftw_alloc_complex(N_x * (N_y / 2 + 1));

    // Copy input data
    for (size_t i = 0; i < result.N; ++i) {
        in[i] = field_data[i];
    }

    // Create plan and execute
    fftw_plan plan = fftw_plan_dft_r2c_2d(
        static_cast<int>(N_y),
        static_cast<int>(N_x),
        in,
        out,
        FFTW_ESTIMATE
    );
    fftw_execute(plan);

    // Process results - store full spectrum
    std::vector<std::complex<double>> fft_complex;
    size_t out_size = N_x * (N_y / 2 + 1);
    fft_complex.reserve(out_size);

    result.total_power = 0.0;
    result.peak_magnitude = 0.0;
    result.peak_frequency = 0.0;

    for (size_t i = 0; i < out_size; ++i) {
        std::complex<double> val(out[i][0], out[i][1]);
        fft_complex.push_back(val);

        double mag = std::abs(val);
        if (i > 0 && mag > result.peak_magnitude) {
            result.peak_magnitude = mag;
            // Compute k_x, k_y for peak
            size_t ix = i % N_x;
            size_t iy = i / N_x;
            double kx = static_cast<double>(ix) / static_cast<double>(N_x);
            double ky = static_cast<double>(iy) / static_cast<double>(N_y);
            result.peak_frequency = std::sqrt(kx * kx + ky * ky);
        }

        result.total_power += mag * mag;
    }

    result.dc_component = std::abs(fft_complex[0]);

    // Compute radial profile
    computeRadialProfile2D(result, fft_complex, N_x, N_y);

    // Cleanup
    fftw_destroy_plan(plan);
    fftw_free(in);
    fftw_free(out);

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    result.execution_time_ms = duration.count();

    return result;
#endif // USE_FFTW3
}

FFTResult EngineFFTAnalysis::compute3DFFT(
    const std::vector<double>& field_data,
    size_t N_x,
    size_t N_y,
    size_t N_z,
    const std::string& field_name
) {
    auto start_time = std::chrono::high_resolution_clock::now();

#ifndef USE_FFTW3
    // Return error if FFTW3 not available
    FFTResult result;
    result.N = N_x * N_y * N_z;
    result.N_x = N_x;
    result.N_y = N_y;
    result.N_z = N_z;
    result.field_name = field_name;

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
    result.execution_time_ms = duration.count() / 1000.0;

    throw std::runtime_error("FFTW3 not available - FFT analysis disabled");
    return result;
#else

    FFTResult result;
    result.N = N_x * N_y * N_z;
    result.N_x = N_x;
    result.N_y = N_y;
    result.N_z = N_z;
    result.field_name = field_name;

    // Allocate FFTW arrays
    double* in = fftw_alloc_real(result.N);
    fftw_complex* out = fftw_alloc_complex(N_x * N_y * (N_z / 2 + 1));

    // Copy input data
    for (size_t i = 0; i < result.N; ++i) {
        in[i] = field_data[i];
    }

    // Create plan and execute
    fftw_plan plan = fftw_plan_dft_r2c_3d(
        static_cast<int>(N_z),
        static_cast<int>(N_y),
        static_cast<int>(N_x),
        in,
        out,
        FFTW_ESTIMATE
    );
    fftw_execute(plan);

    // Process results
    std::vector<std::complex<double>> fft_complex;
    size_t out_size = N_x * N_y * (N_z / 2 + 1);
    fft_complex.reserve(out_size);

    result.total_power = 0.0;
    result.peak_magnitude = 0.0;
    result.peak_frequency = 0.0;

    for (size_t i = 0; i < out_size; ++i) {
        std::complex<double> val(out[i][0], out[i][1]);
        fft_complex.push_back(val);

        double mag = std::abs(val);
        if (i > 0 && mag > result.peak_magnitude) {
            result.peak_magnitude = mag;
        }

        result.total_power += mag * mag;
    }

    result.dc_component = std::abs(fft_complex[0]);

    // Compute radial profile
    computeRadialProfile3D(result, fft_complex, N_x, N_y, N_z);

    // Cleanup
    fftw_destroy_plan(plan);
    fftw_free(in);
    fftw_free(out);

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    result.execution_time_ms = duration.count();

    return result;
#endif // USE_FFTW3
}

#ifdef USE_FFTW3
void EngineFFTAnalysis::computeRadialProfile2D(
    FFTResult& result,
    const std::vector<std::complex<double>>& fft_data,
    size_t N_x,
    size_t N_y
) {
    // Compute maximum radius
    size_t max_radius = static_cast<size_t>(
        std::sqrt(static_cast<double>(N_x * N_x + N_y * N_y)) / 2.0
    ) + 1;

    std::vector<double> radial_sum(max_radius, 0.0);
    std::vector<size_t> radial_count(max_radius, 0);

    // Bin by radius
    for (size_t iy = 0; iy < N_y / 2 + 1; ++iy) {
        for (size_t ix = 0; ix < N_x; ++ix) {
            size_t idx = iy * N_x + ix;
            if (idx >= fft_data.size()) continue;

            // Compute radius
            double kx = static_cast<double>(ix);
            double ky = static_cast<double>(iy);
            if (ix > N_x / 2) kx = static_cast<double>(ix) - static_cast<double>(N_x);

            double k_radius = std::sqrt(kx * kx + ky * ky);
            size_t bin = static_cast<size_t>(k_radius);

            if (bin < max_radius) {
                double power = std::abs(fft_data[idx]) * std::abs(fft_data[idx]);
                radial_sum[bin] += power;
                radial_count[bin]++;
            }
        }
    }

    // Average and store
    for (size_t i = 0; i < max_radius; ++i) {
        if (radial_count[i] > 0) {
            result.radial_k.push_back(static_cast<double>(i) / std::max(N_x, N_y));
            result.radial_power.push_back(radial_sum[i] / radial_count[i]);
        }
    }
}

void EngineFFTAnalysis::computeRadialProfile3D(
    FFTResult& result,
    const std::vector<std::complex<double>>& fft_data,
    size_t N_x,
    size_t N_y,
    size_t N_z
) {
    // Similar to 2D but with 3D radius
    size_t max_radius = static_cast<size_t>(
        std::sqrt(static_cast<double>(N_x * N_x + N_y * N_y + N_z * N_z)) / 2.0
    ) + 1;

    std::vector<double> radial_sum(max_radius, 0.0);
    std::vector<size_t> radial_count(max_radius, 0);

    // Simplified binning (full implementation would iterate over all 3D indices)
    // For now, just compute from available data
    size_t max_N = std::max({N_x, N_y, N_z});
    for (size_t i = 0; i < fft_data.size() && i < max_radius; ++i) {
        double power = std::abs(fft_data[i]) * std::abs(fft_data[i]);
        radial_sum[i] += power;
        radial_count[i]++;
    }

    for (size_t i = 0; i < max_radius; ++i) {
        if (radial_count[i] > 0) {
            result.radial_k.push_back(static_cast<double>(i) / max_N);
            result.radial_power.push_back(radial_sum[i] / radial_count[i]);
        }
    }
}
#endif // USE_FFTW3

std::vector<std::pair<double, double>> EngineFFTAnalysis::findPeaks(
    const FFTResult& result,
    size_t n_peaks,
    double threshold
) {
    std::vector<std::pair<double, double>> peaks;

    if (result.magnitude.empty()) {
        return peaks;
    }

    double max_mag = result.peak_magnitude;
    double min_threshold = max_mag * threshold;

    // Create pairs of (frequency, magnitude)
    std::vector<std::pair<double, double>> all_peaks;
    for (size_t i = 1; i < result.magnitude.size(); ++i) {
        if (result.magnitude[i] > min_threshold) {
            all_peaks.push_back({result.frequencies[i], result.magnitude[i]});
        }
    }

    // Sort by magnitude (descending)
    std::sort(all_peaks.begin(), all_peaks.end(),
        [](const auto& a, const auto& b) { return a.second > b.second; });

    // Take top n_peaks
    size_t count = (std::min)(n_peaks, all_peaks.size());
    peaks.insert(peaks.end(), all_peaks.begin(), all_peaks.begin() + count);

    return peaks;
}

nlohmann::json EngineFFTAnalysis::toJSON(const FFTResult& result) {
    nlohmann::json j;

    j["field_name"] = result.field_name;
    j["N"] = result.N;
    j["dimensions"] = {
        {"N_x", result.N_x},
        {"N_y", result.N_y},
        {"N_z", result.N_z}
    };

    j["dc_component"] = result.dc_component;
    j["peak_frequency"] = result.peak_frequency;
    j["peak_magnitude"] = result.peak_magnitude;
    j["total_power"] = result.total_power;
    j["execution_time_ms"] = result.execution_time_ms;

    // Include radial profile if available
    if (!result.radial_k.empty()) {
        j["radial_profile"] = nlohmann::json::array();
        for (size_t i = 0; i < result.radial_k.size(); ++i) {
            j["radial_profile"].push_back({
                {"k", result.radial_k[i]},
                {"power", result.radial_power[i]}
            });
        }
    }

    // Find and include peaks
    auto peaks = findPeaks(result, 10, 0.01);
    j["peaks"] = nlohmann::json::array();
    for (const auto& [freq, mag] : peaks) {
        j["peaks"].push_back({
            {"frequency", freq},
            {"magnitude", mag}
        });
    }

    return j;
}

} // namespace analysis
} // namespace dase
