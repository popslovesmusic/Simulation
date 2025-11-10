#!/usr/bin/env python3
"""
Compute autocorrelation function and extract correlation length
using multiple fitting methods.
"""

import json
import numpy as np
import sys
from scipy.optimize import curve_fit
from scipy.signal import correlate

def exponential_decay(x, xi):
    """Exponential decay: exp(-x/xi)"""
    return np.exp(-x / xi)

def power_law_decay(x, xi, alpha):
    """Power law decay: (1 + x/xi)^(-alpha)"""
    return (1 + x / xi)**(-alpha)

def compute_autocorrelation(psi_real, psi_imag):
    """Compute autocorrelation of |Ψ|^2"""
    F = psi_real**2 + psi_imag**2
    F = F - np.mean(F)  # Remove DC component

    # Compute autocorrelation using FFT
    autocorr = correlate(F, F, mode='same', method='fft')
    autocorr = autocorr / autocorr[len(autocorr)//2]  # Normalize to 1 at zero lag

    # Take positive lags only
    N = len(F)
    lags = np.arange(0, N//2)
    autocorr_positive = autocorr[N//2:]

    return lags, autocorr_positive

def fit_exponential(lags, autocorr, max_lag=100):
    """Fit exponential decay to extract xi"""
    # Use only first max_lag points
    mask = lags < max_lag
    x_fit = lags[mask]
    y_fit = autocorr[mask]

    # Remove non-positive values
    positive_mask = y_fit > 0
    x_fit = x_fit[positive_mask]
    y_fit = y_fit[positive_mask]

    if len(x_fit) < 10:
        return None, None

    try:
        # Fit exponential
        popt, _ = curve_fit(exponential_decay, x_fit, y_fit, p0=[10.0], maxfev=10000)
        xi = popt[0]

        # Compute R^2
        y_pred = exponential_decay(x_fit, xi)
        ss_res = np.sum((y_fit - y_pred)**2)
        ss_tot = np.sum((y_fit - np.mean(y_fit))**2)
        r_squared = 1 - (ss_res / ss_tot)

        return xi, r_squared
    except:
        return None, None

def fit_power_law(lags, autocorr, max_lag=100):
    """Fit power law decay to extract xi"""
    mask = lags < max_lag
    x_fit = lags[mask]
    y_fit = autocorr[mask]

    # Remove non-positive values
    positive_mask = y_fit > 0
    x_fit = x_fit[positive_mask]
    y_fit = y_fit[positive_mask]

    if len(x_fit) < 10:
        return None, None, None

    try:
        # Fit power law
        popt, _ = curve_fit(power_law_decay, x_fit, y_fit, p0=[10.0, 2.0], maxfev=10000)
        xi, alpha = popt

        # Compute R^2
        y_pred = power_law_decay(x_fit, xi, alpha)
        ss_res = np.sum((y_fit - y_pred)**2)
        ss_tot = np.sum((y_fit - np.mean(y_fit))**2)
        r_squared = 1 - (ss_res / ss_tot)

        return xi, alpha, r_squared
    except:
        return None, None, None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: compute_autocorrelation.py <input.json> <R_c>")
        sys.exit(1)

    input_file = sys.argv[1]
    R_c = float(sys.argv[2])

    # Load state
    with open(input_file, 'r') as f:
        lines = f.readlines()

    state = None
    for line in lines:
        try:
            data = json.loads(line)
            if data.get('command') == 'get_state' and data.get('status') == 'success':
                state = data['result']
                break
        except:
            continue

    if state is None:
        print("ERROR: No valid get_state response found")
        sys.exit(1)

    psi_real = np.array(state['psi_real'])
    psi_imag = np.array(state['psi_imag'])

    # Compute autocorrelation
    lags, autocorr = compute_autocorrelation(psi_real, psi_imag)

    # Fit exponential
    xi_exp, r2_exp = fit_exponential(lags, autocorr)

    # Fit power law
    xi_pow, alpha, r2_pow = fit_power_law(lags, autocorr)

    # Print results
    print(f"R_c = {R_c}")
    print(f"Exponential fit: xi = {xi_exp:.3f}, R^2 = {r2_exp:.4f}" if xi_exp else "Exponential fit: FAILED")
    print(f"Power law fit: xi = {xi_pow:.3f}, alpha = {alpha:.3f}, R^2 = {r2_pow:.4f}" if xi_pow else "Power law fit: FAILED")

    if xi_exp:
        print(f"xi/R_c (exponential) = {xi_exp/R_c:.3f}")
    if xi_pow:
        print(f"xi/R_c (power law) = {xi_pow/R_c:.3f}")
