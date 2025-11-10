#!/usr/bin/env python3
"""Utility script for inspecting IGSOA 2D simulation snapshots.

The script expects the JSON payload emitted by the `get_state` command of
`dase_cli`.  It reshapes the flattened arrays into a 2D lattice, computes the
informational density |Ψ|^2, evaluates center-of-mass drift, and optionally
produces a heatmap for quick visualization.

<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
=======
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
When NumPy is available the tool can also evaluate the complex spectrum and the
autocorrelation of the wavefunction.  Both diagnostics can be exported as JSON
summaries or rendered to heatmaps for quick inspection of high-frequency
content and lattice symmetry.

<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
Example usage
-------------
1. Capture state from CLI:

    dase_cli --command '{"command":"get_state","params":{"engine_id":"engine_002"}}' \
        > snapshot.json

2. Analyze and plot:

    python tools/analyze_igsoa_2d.py --state-json snapshot.json \
        --heatmap psi_density.png
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
from typing import List, Tuple
=======
from typing import Any, List, Tuple
>>>>>>> theirs
=======
from typing import Any, List, Tuple
>>>>>>> theirs
=======
from typing import Any, List, Tuple
>>>>>>> theirs
=======
from typing import Any, List, Tuple
>>>>>>> theirs

try:
    import numpy as _np  # type: ignore
except Exception:  # pragma: no cover - numpy is optional
    _np = None  # Fallback to pure Python implementations


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze IGSOA 2D state dumps.")
    parser.add_argument(
        "--state-json",
        type=Path,
        required=True,
        help="Path to JSON file produced by `get_state`.",
    )
    parser.add_argument(
        "--heatmap",
        type=Path,
        help=(
            "Optional output path for a heatmap image of |Psi|^2. Requires "
            "matplotlib."
        ),
    )
    parser.add_argument(
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
=======
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
        "--fft-json",
        type=Path,
        help=(
            "Optional path to dump FFT magnitude statistics as JSON. Requires "
            "NumPy."
        ),
    )
    parser.add_argument(
        "--fft-heatmap",
        type=Path,
        help=(
            "Optional output path for a heatmap of the FFT magnitude spectrum. "
            "Requires NumPy and matplotlib."
        ),
    )
    parser.add_argument(
        "--autocorr-heatmap",
        type=Path,
        help=(
            "Optional output path for a heatmap of the 2D autocorrelation. "
            "Requires NumPy and matplotlib."
        ),
    )
    parser.add_argument(
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
        "--expect-center",
        type=float,
        nargs=2,
        metavar=("X0", "Y0"),
        help="Expected center-of-mass coordinates for drift comparison.",
    )
    parser.add_argument(
        "--max-drift",
        type=float,
        default=0.5,
        help="Maximum acceptable drift radius (lattice units).",
    )
    return parser.parse_args()


def _reshape(values: List[float], dims: Tuple[int, int]) -> List[List[float]]:
    n_x, n_y = dims
    if len(values) != n_x * n_y:
        raise ValueError(
            f"Array length {len(values)} does not match lattice size {n_x}x{n_y}."
        )
    grid = [values[row * n_x : (row + 1) * n_x] for row in range(n_y)]
    return grid


def _compute_density(psi_real: List[float], psi_imag: List[float]) -> List[float]:
    if len(psi_real) != len(psi_imag):
        raise ValueError("psi_real and psi_imag must have identical lengths")
    return [r * r + i * i for r, i in zip(psi_real, psi_imag)]


def _center_of_mass(density: List[float], dims: Tuple[int, int]) -> Tuple[float, float]:
    n_x, n_y = dims
    total_mass = sum(density)
    if total_mass == 0.0:
        return 0.0, 0.0

    sum_x = 0.0
    sum_y = 0.0
    for index, value in enumerate(density):
        x = index % n_x
        y = index // n_x
        sum_x += x * value
        sum_y += y * value

    return sum_x / total_mass, sum_y / total_mass


def _standard_deviation(density: List[float]) -> float:
    if not density:
        return 0.0
    mean_val = statistics.mean(density)
    if mean_val == 0.0:
        return 0.0
    variance = statistics.mean((val - mean_val) ** 2 for val in density)
    return math.sqrt(variance)


def _save_heatmap(
    density: List[float], dims: Tuple[int, int], path: Path
) -> None:  # pragma: no cover - visualization helper
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Matplotlib is required for heatmap generation"
        ) from exc

    n_x, n_y = dims
    if _np is not None:
        array = _np.array(density).reshape((n_y, n_x))
    else:  # pragma: no cover - fallback
        array = _reshape(density, dims)

    plt.figure(figsize=(6, 5))
    plt.imshow(array, origin="lower", cmap="magma")
    plt.colorbar(label="|Psi|^2")
    plt.title("IGSOA 2D Informational Density")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
=======
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
def _require_numpy(feature: str) -> Any:
    if _np is None:
        raise RuntimeError(f"{feature} requires NumPy to be installed.")
    return _np


def _reshape_numpy(values: List[float], dims: Tuple[int, int]) -> "_np.ndarray":
    np_mod = _require_numpy("FFT support")
    n_x, n_y = dims
    return np_mod.array(values, dtype=float).reshape((n_y, n_x))


def _compute_fft_statistics(
    psi_real: List[float], psi_imag: List[float], dims: Tuple[int, int]
) -> Tuple[dict, "_np.ndarray", "_np.ndarray"]:
    np_mod = _require_numpy("FFT support")
    psi_r = _reshape_numpy(psi_real, dims)
    psi_i = _reshape_numpy(psi_imag, dims)
    psi_complex = psi_r + 1j * psi_i

    fft_vals = np_mod.fft.fft2(psi_complex)
    fft_shifted = np_mod.fft.fftshift(fft_vals)
    magnitude = np_mod.abs(fft_shifted)

    dc_component = float(np_mod.abs(fft_vals[0, 0]))
    peak_index = np_mod.unravel_index(np_mod.argmax(magnitude), magnitude.shape)

    center = (magnitude.shape[0] // 2, magnitude.shape[1] // 2)
    peak_offset = (
        int(peak_index[1] - center[1]),
        int(peak_index[0] - center[0]),
    )

    # Radial profile using integer distance bins from the center.
    y_indices, x_indices = np_mod.indices(magnitude.shape)
    radii = np_mod.sqrt(
        (x_indices - center[1]) ** 2 + (y_indices - center[0]) ** 2
    )
    radius_bins = radii.astype(int)
    max_radius = int(radius_bins.max())
    radial_sums = np_mod.bincount(radius_bins.ravel(), weights=magnitude.ravel())
    radial_counts = np_mod.bincount(radius_bins.ravel())
    radial_profile = []
    for radius in range(max_radius + 1):
        count = radial_counts[radius] if radius < len(radial_counts) else 0
        if count == 0:
            continue
        sum_val = radial_sums[radius] if radius < len(radial_sums) else 0.0
        avg_val = sum_val / count
        radial_profile.append({"radius": radius, "avg_magnitude": float(avg_val)})

    stats = {
        "dc_component": dc_component,
        "max_magnitude": float(magnitude.max()),
        "min_magnitude": float(magnitude.min()),
        "dominant_frequency_offset": {"kx": peak_offset[0], "ky": peak_offset[1]},
        "radial_profile": radial_profile,
    }

    return stats, magnitude, fft_vals


def _compute_autocorrelation(
    fft_vals: "_np.ndarray",
) -> Tuple[dict, "_np.ndarray"]:
    np_mod = _require_numpy("autocorrelation support")
    autocorr = np_mod.fft.ifft2(np_mod.abs(fft_vals) ** 2)
    autocorr_real = autocorr.real
    autocorr_shifted = np_mod.fft.fftshift(autocorr_real)

    max_val = float(autocorr_shifted.max())
    min_val = float(autocorr_shifted.min())
    zero_lag = float(autocorr_real[0, 0])

    peak_index = np_mod.unravel_index(
        np_mod.argmax(autocorr_shifted), autocorr_shifted.shape
    )
    center = (autocorr_shifted.shape[0] // 2, autocorr_shifted.shape[1] // 2)
    peak_offset = (
        int(peak_index[1] - center[1]),
        int(peak_index[0] - center[0]),
    )

    stats = {
        "zero_lag": zero_lag,
        "max_value": max_val,
        "min_value": min_val,
        "dominant_offset": {"dx": peak_offset[0], "dy": peak_offset[1]},
    }

    return stats, autocorr_shifted


def _save_fft_heatmap(
    magnitude: "_np.ndarray", path: Path
) -> None:  # pragma: no cover - visualization helper
    np_mod = _require_numpy("FFT visualization")
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Matplotlib is required for FFT heatmap generation"
        ) from exc

    with np_mod.errstate(divide="ignore"):
        log_magnitude = np_mod.log1p(magnitude)

    plt.figure(figsize=(6, 5))
    plt.imshow(log_magnitude, origin="lower", cmap="viridis")
    plt.colorbar(label="log(1 + |FFT|)")
    plt.title("IGSOA 2D FFT Magnitude")
    plt.xlabel("k_x index")
    plt.ylabel("k_y index")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _save_autocorr_heatmap(
    autocorr: "_np.ndarray", path: Path
) -> None:  # pragma: no cover - visualization helper
    _require_numpy("autocorrelation visualization")
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Matplotlib is required for autocorrelation heatmap generation"
        ) from exc

    plt.figure(figsize=(6, 5))
    plt.imshow(autocorr, origin="lower", cmap="cividis")
    plt.colorbar(label="Autocorrelation")
    plt.title("IGSOA 2D Autocorrelation")
    plt.xlabel("Δx index")
    plt.ylabel("Δy index")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
def main() -> None:
    args = _parse_args()
    state_data = json.loads(args.state_json.read_text(encoding="utf-8"))
    payload = state_data.get("result", state_data)

    psi_real = payload.get("psi_real")
    psi_imag = payload.get("psi_imag")
    dimensions = payload.get("dimensions")

    if psi_real is None or psi_imag is None:
        raise SystemExit("State JSON must contain 'psi_real' and 'psi_imag' arrays.")

    if dimensions:
        dims = (int(dimensions["N_x"]), int(dimensions["N_y"]))
    else:
        n_total = len(psi_real)
        sqrt_n = int(round(math.sqrt(n_total)))
        if sqrt_n * sqrt_n != n_total:
            raise SystemExit(
                "Lattice dimensions missing. Provide --state-json from updated CLI "
                "or specify dimensions explicitly in the file."
            )
        dims = (sqrt_n, sqrt_n)

    density = _compute_density(psi_real, psi_imag)
    com_x, com_y = _center_of_mass(density, dims)
    std_dev = _standard_deviation(density)

    report = {
        "dimensions": {"N_x": dims[0], "N_y": dims[1]},
        "center_of_mass": {"x": com_x, "y": com_y},
        "density_stddev": std_dev,
        "max_density": max(density) if density else 0.0,
    }

    if args.expect_center:
        ref_x, ref_y = args.expect_center
        drift = math.sqrt((com_x - ref_x) ** 2 + (com_y - ref_y) ** 2)
        report["expected_center"] = {"x": ref_x, "y": ref_y}
        report["drift"] = drift
        report["drift_ok"] = drift <= args.max_drift
    else:
        report["drift"] = None
        report["drift_ok"] = None

<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
=======
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
    fft_stats = None
    autocorr_stats = None
    fft_magnitude = None
    autocorr_shifted = None

    if _np is not None:
        fft_stats, fft_magnitude, fft_vals = _compute_fft_statistics(
            psi_real, psi_imag, dims
        )
        autocorr_stats, autocorr_shifted = _compute_autocorrelation(fft_vals)
        report["fft"] = fft_stats
        report["autocorrelation"] = autocorr_stats
    else:
        if args.fft_json or args.fft_heatmap or args.autocorr_heatmap:
            raise SystemExit("NumPy is required for FFT/autocorrelation outputs.")
        report["fft"] = None
        report["autocorrelation"] = None

<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
    print(json.dumps(report, indent=2))

    if args.heatmap:
        _save_heatmap(density, dims, args.heatmap)

<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
=======
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
    if args.fft_json:
        if fft_stats is None:
            raise SystemExit("Cannot export FFT stats without NumPy installed.")
        args.fft_json.write_text(json.dumps(fft_stats, indent=2), encoding="utf-8")

    if args.fft_heatmap:
        if fft_stats is None or fft_magnitude is None:
            raise SystemExit("Cannot export FFT heatmap without NumPy installed.")
        _save_fft_heatmap(fft_magnitude, args.fft_heatmap)

    if args.autocorr_heatmap:
        if autocorr_stats is None or autocorr_shifted is None:
            raise SystemExit(
                "Cannot export autocorrelation heatmap without NumPy installed."
            )
        _save_autocorr_heatmap(autocorr_shifted, args.autocorr_heatmap)

<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs

if __name__ == "__main__":
    main()
