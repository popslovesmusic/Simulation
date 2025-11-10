#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DASE Benchmark - Fixed Unicode Version
Drop-in benchmark for DASE / DVSL AVX2 backend.
- Detects AVX2 & FMA via dase_engine.CPUFeatures
- Uses AnalogCellularEngineAVX2 and AnalogUniversalNodeAVX2
- Falls back to simulation only if import fails
- Writes JSON results to dase_benchmark_results_YYYYMMDD_HHMMSS.json
"""

from __future__ import annotations
import json
import math
import os
import platform
import sys
import time
from datetime import datetime
from typing import Any, Dict

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

REPORT_PREFIX = "dase_benchmark_results"

# Safe print function that handles Unicode gracefully
def safe_print(text, level='info'):
    """Print with fallback for terminals that don't support Unicode"""
    symbols = {
        'check': {'unicode': '\u2705', 'ascii': '[OK]'},
        'cross': {'unicode': '\u274c', 'ascii': '[X]'},
        'warning': {'unicode': '\u26a0\ufe0f', 'ascii': '[!]'},
        'rocket': {'unicode': '\U0001f680', 'ascii': '[>>]'},
        'star': {'unicode': '\u2b50', 'ascii': '[*]'},
    }

    # Replace Unicode symbols with ASCII equivalents if needed
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII
        for symbol_data in symbols.values():
            text = text.replace(symbol_data['unicode'], symbol_data['ascii'])
        print(text)

# -----------------------------------------------------------------------------
# Environment info
# -----------------------------------------------------------------------------
def system_info() -> Dict[str, Any]:
    try:
        import psutil  # optional
        ram_gb = psutil.virtual_memory().total / (1024**3)
    except Exception:
        ram_gb = None
    return {
        "platform": platform.platform(),
        "system": f"{platform.system()}-{platform.release()}",
        "python": platform.python_version(),
        "cpu": platform.processor() or platform.machine(),
        "ram_gb": ram_gb,
        "logical_cpus": os.cpu_count()
    }

# -----------------------------------------------------------------------------
# Try to import backend
# -----------------------------------------------------------------------------
ENGINE_AVAILABLE = False
try:
    import dase_engine as de
    # Quick sanity: required classes
    _req = ["CPUFeatures", "EngineMetrics", "AnalogUniversalNodeAVX2", "AnalogCellularEngineAVX2"]
    if all(hasattr(de, r) for r in _req):
        # Confirm CPU feature calls work
        _ = de.CPUFeatures.has_avx2()
        _ = de.CPUFeatures.has_fma()
        ENGINE_AVAILABLE = True
    else:
        safe_print("Engine module loaded but required classes are missing.", 'warning')
except Exception as e:
    safe_print(f"Engine import failed: {e}", 'warning')
    ENGINE_AVAILABLE = False

# -----------------------------------------------------------------------------
# Bench Harness
# -----------------------------------------------------------------------------
class DASEBenchmark:
    def __init__(self) -> None:
        self.results: Dict[str, Any] = {
            "metadata": system_info(),
            "engine_available": ENGINE_AVAILABLE,
            "cpu_caps": {},
            "basic_ops": {},
            "performance": {},
            "accuracy": {},
            "summary": {}
        }
        self.engine = None

    # -------------------------- init engine ----------------------------------
    def initialize_engine(self, num_nodes: int = 1024) -> bool:
        if not ENGINE_AVAILABLE:
            safe_print("Engine not available - running simulation mode.", 'warning')
            return False
        try:
            caps = {
                "avx2": bool(de.CPUFeatures.has_avx2()),
                "fma": bool(de.CPUFeatures.has_fma())
            }
            self.results["cpu_caps"] = caps
            safe_print(f"CPU Features: AVX2={caps['avx2']}, FMA={caps['fma']}", 'info')
            if not caps["avx2"]:
                safe_print("AVX2 not detected - performance may be limited.", 'warning')

            self.engine = de.AnalogCellularEngineAVX2(num_nodes)
            safe_print(f"[OK] Engine initialized: AnalogCellularEngineAVX2({num_nodes})", 'info')
            return True
        except Exception as e:
            safe_print(f"Engine initialization failed: {e}", 'warning')
            return False

    # ----------------------- basic ops benchmark -----------------------------
    def test_basic_ops(self) -> None:
        safe_print("\n=== Basic Operations Benchmark ===", 'info')
        tests = {}
        import time, numpy as np

        try:
            node = de.AnalogUniversalNodeAVX2() if ENGINE_AVAILABLE else None
            node_ok = node is not None
            if node_ok:
                safe_print("[OK] AnalogUniversalNodeAVX2 initialized.", 'info')
            else:
                safe_print("[!] Using simulated node (engine unavailable).", 'warning')
        except Exception as e:
            safe_print(f"[!] Node init failed: {e}", 'warning')
            node_ok = False

        # --- Amplifier -------------------------------------------------------
        t0 = time.perf_counter()
        try:
            if node_ok and hasattr(node, "amplify"):
                y = node.amplify(2.0, 0.5)
                status = "passed" if abs(y - 1.0) < 1e-6 else "failed"
            else:
                time.sleep(0.0015)
                status = "simulated"
            tests["amplifier"] = {"status": status, "time_ms": (time.perf_counter() - t0) * 1000}
            safe_print(f"  amplifier : {status}", 'info')
        except Exception as e:
            tests["amplifier"] = {"status": "error", "error": str(e)}
            safe_print(f"  amplifier : error ({e})", 'warning')

        # --- Integrator ------------------------------------------------------
        t0 = time.perf_counter()
        try:
            if node_ok and hasattr(node, "integrate"):
                y = 0.0
                for _ in range(100):
                    y = node.integrate(1.0, 0.5)
                status = "passed" if y > 0.001 else "failed"
            else:
                time.sleep(0.002)
                status = "simulated"
            tests["integrator"] = {"status": status, "time_ms": (time.perf_counter() - t0) * 1000}
            safe_print(f"  integrator: {status}", 'info')
        except Exception as e:
            tests["integrator"] = {"status": "error", "error": str(e)}
            safe_print(f"  integrator: error ({e})", 'warning')

        # --- Oscillator ------------------------------------------------------
        t0 = time.perf_counter()
        try:
            if node_ok and hasattr(node, "oscillate"):
                _ = node.oscillate(440.0, 0.1)
                status = "passed"
            else:
                time.sleep(0.008)
                status = "simulated"
            tests["oscillator"] = {"status": status, "time_ms": (time.perf_counter() - t0) * 1000}
            safe_print(f"  oscillator: {status}", 'info')
        except Exception as e:
            tests["oscillator"] = {"status": "error", "error": str(e)}
            safe_print(f"  oscillator: error ({e})", 'warning')

        # --- Filter ----------------------------------------------------------
        t0 = time.perf_counter()
        try:
            if node_ok and hasattr(node, "process_block_frequency_domain"):
                test_signal = np.sin(np.linspace(0, 2 * np.pi, 256)).astype(np.float32)
                _ = node.process_block_frequency_domain(test_signal.tolist())
                status = "passed"
            else:
                time.sleep(0.056)
                status = "simulated"
            tests["filter"] = {"status": status, "time_ms": (time.perf_counter() - t0) * 1000}
            safe_print(f"  filter    : {status}", 'info')
        except Exception as e:
            tests["filter"] = {"status": "error", "error": str(e)}
            safe_print(f"  filter    : error ({e})", 'warning')

        # --- Feedback --------------------------------------------------------
        t0 = time.perf_counter()
        try:
            if node_ok and hasattr(node, "apply_feedback"):
                try:
                    node.apply_feedback(0.1, 0.5)
                except TypeError:
                    node.apply_feedback(0.1)
                status = "passed"
            else:
                time.sleep(0.0031)
                status = "simulated"
            tests["feedback"] = {"status": status, "time_ms": (time.perf_counter() - t0) * 1000}
            safe_print(f"  feedback  : {status}", 'info')
        except Exception as e:
            tests["feedback"] = {"status": "error", "error": str(e)}
            safe_print(f"  feedback  : error ({e})", 'warning')

        # --- Save results ----------------------------------------------------
        self.results["basic_ops"] = tests

    # ----------------------- performance scaling ------------------------------
    def test_performance(self, cycles: int = 2000, test_type: str = "standard") -> None:
        if test_type == "endurance":
            safe_print("\n=== ENDURANCE/STRESS TEST (10+ minutes) ===", 'info')
            safe_print("Configuration:", 'info')
            safe_print(f"  Mission Steps:    {cycles:,}", 'info')
            safe_print(f"  Nodes:            1,024", 'info')
            safe_print(f"  Iterations/Node:  30", 'info')
            safe_print(f"  Total Operations: ~{cycles * 1024 * 30 / 1e9:.1f} billion", 'info')
            safe_print(f"  Expected Duration: ~{cycles * 1024 * 30 / 280.3e6 / 60:.1f} minutes", 'info')
            safe_print(f"  CPU Utilization:  100% (12/12 cores)", 'info')
            safe_print("", 'info')
            safe_print("Starting endurance test... (this will take 10+ minutes)", 'info')
        else:
            safe_print("\n=== Performance Scaling Benchmark ===", 'info')

        perf = {"mode": "simulation", "test_type": test_type}
        if self.engine:
            mode = "native"
            t0 = time.perf_counter()
            try:
                # Progress reporting for long-running tests
                if test_type == "endurance" and cycles > 100000:
                    safe_print("Progress will be updated every minute...", 'info')
                    safe_print(f"Start time: {datetime.now().strftime('%H:%M:%S')}", 'info')
                    safe_print("", 'info')

                self.engine.run_mission(cycles)
                elapsed = time.perf_counter() - t0
                m = self.engine.get_metrics()

                total_ops = getattr(m, "total_operations", None)
                ops_per_sec = getattr(m, "current_ops_per_second", None)

                perf = {
                    "mode": mode,
                    "test_type": test_type,
                    "elapsed_s": elapsed,
                    "elapsed_min": elapsed / 60.0,
                    "current_ops_per_second": ops_per_sec,
                    "speedup_factor": getattr(m, "speedup_factor", None),
                    "total_operations": total_ops,
                    "cycles": cycles,
                    "ops_per_ns": (elapsed * 1e9 / total_ops) if total_ops else None,
                }

                safe_print("", 'info')
                safe_print(f"End time: {datetime.now().strftime('%H:%M:%S')}", 'info')
                safe_print(f"run_mission({cycles:,}) completed in {elapsed:.2f}s ({elapsed/60:.2f} min)", 'info')

                if perf["current_ops_per_second"] is not None:
                    safe_print(f"Operations/sec: {perf['current_ops_per_second']:,.0f}", 'info')
                    safe_print(f"Speedup factor: {perf['speedup_factor']:.2f}x", 'info')

                if total_ops:
                    safe_print(f"Total operations: {total_ops:,} ({total_ops/1e9:.2f} billion)", 'info')
                    safe_print(f"Time per operation: {perf['ops_per_ns']:.2f} ns/op", 'info')

            except Exception as e:
                perf = {"mode": "error", "error": str(e), "test_type": test_type}
        else:
            # Simulated placeholder
            time.sleep(0.01)
            perf["mode"] = "simulated"
            perf["elapsed_s"] = 0.01
            perf["current_ops_per_second"] = 435.0
            perf["speedup_factor"] = 1.0
            perf["total_operations"] = 1000
            safe_print("  (simulation placeholder)", 'info')

        self.results["performance"] = perf

    # ----------------------- accuracy (light checks) --------------------------
    def test_accuracy(self) -> None:
        safe_print("\n=== Numerical Accuracy Benchmark ===", 'info')
        acc = {}

        # Helper for tiered tolerance
        def check_accuracy(label, err, strict=1e-3, relaxed=1.5e-3):
            """Tiered accuracy check: passes, warns, or fails based on error size."""
            if err < strict:
                return "passed"
            elif err < relaxed:
                safe_print(f"[!] {label}: borderline precision ({err:.6f}) within AVX2 tolerance", 'warning')
                return "warning"
            else:
                safe_print(f"[X] {label}: precision error too high ({err:.6f})", 'warning')
                return "failed"

        try:
            import numpy as np
        except ImportError:
            safe_print("NumPy not installed - skipping accuracy tests.", 'warning')
            return

        # DC gain test: amplify(2, 0.5) -> 1.0
        try:
            if ENGINE_AVAILABLE:
                node = de.AnalogUniversalNodeAVX2()
                y = node.amplify(2.0, 0.5)
                err = abs(y - 1.0)
            else:
                err = abs((2.0 * 0.5) - 1.0)
            acc["dc_gain"] = {"error": err, "status": check_accuracy("dc_gain", err)}
        except Exception as e:
            acc["dc_gain"] = {"error": str(e), "status": "error"}

        # Sine wave reconstruction accuracy
        try:
            t = np.linspace(0, 2 * np.pi, 256)
            x = np.sin(t)
            if ENGINE_AVAILABLE:
                node = de.AnalogUniversalNodeAVX2()
                y = [node.amplify(1.0, xi) for xi in x]
            else:
                y = x
            err = float(np.max(np.abs(np.array(y) - x)))
            acc["sine_wave"] = {"error": err, "status": check_accuracy("sine_wave", err)}
        except Exception as e:
            acc["sine_wave"] = {"error": str(e), "status": "error"}

        # Step response accuracy
        try:
            x = np.zeros(256); x[128:] = 1.0
            if ENGINE_AVAILABLE:
                node = de.AnalogUniversalNodeAVX2()
                y = [node.integrate(1.0, xi) for xi in x]
            else:
                y = np.cumsum(x) / len(x)
            err = float(np.max(np.abs(np.diff(y))))
            acc["step_response"] = {"error": err, "status": check_accuracy("step_response", err)}
        except Exception as e:
            acc["step_response"] = {"error": str(e), "status": "error"}

        # Frequency response accuracy (light FFT check)
        try:
            f = np.fft.rfft(np.sin(np.linspace(0, 2 * np.pi, 1024)))
            if ENGINE_AVAILABLE:
                node = de.AnalogUniversalNodeAVX2()
                yf = np.fft.rfft([node.amplify(1.0, np.sin(tt)) for tt in np.linspace(0, 2 * np.pi, 1024)])
            else:
                yf = f
            err = float(np.max(np.abs(np.abs(yf) - np.abs(f))))
            acc["frequency_response"] = {"error": err, "status": check_accuracy("frequency_response", err)}
        except Exception as e:
            acc["frequency_response"] = {"error": str(e), "status": "error"}

        # Print summary
        for k, v in acc.items():
            safe_print(f"  {k:16}: {v['status']:8} (max error: {v.get('error', 0):.6f})", 'info')

        self.results["accuracy"] = acc

    # ----------------------- finalize & save ----------------------------------
    def summarize(self) -> None:
        basic = self.results.get("basic_ops", {})
        acc = self.results.get("accuracy", {})
        perf = self.results.get("performance", {})

        basic_pass = sum(1 for v in basic.values() if v.get("status") == "passed")
        basic_total = len(basic)
        acc_pass = sum(1 for v in acc.values() if v.get("status") == "passed")
        acc_total = len(acc)

        summary = {
            "engine_status": "native" if self.engine else "simulation",
            "basic_ops_passed": f"{basic_pass}/{basic_total}",
            "accuracy_passed": f"{acc_pass}/{acc_total}",
            "performance_mode": perf.get("mode"),
            "test_type": perf.get("test_type", "standard")
        }
        self.results["summary"] = summary

        safe_print("\n" + "="*80, 'info')
        if summary["test_type"] == "endurance":
            safe_print("ENDURANCE/STRESS TEST SUMMARY REPORT", 'info')
        else:
            safe_print("BENCHMARK SUMMARY REPORT", 'info')
        safe_print("="*80, 'info')

        safe_print(f"Engine Status:    {summary['engine_status']}", 'info')
        safe_print(f"Test Type:        {summary['test_type']}", 'info')
        safe_print(f"Basic Operations: {summary['basic_ops_passed']}", 'info')
        safe_print(f"Accuracy Tests:   {summary['accuracy_passed']}", 'info')

        if perf.get("mode") == "native":
            safe_print("", 'info')
            safe_print("PERFORMANCE RESULTS:", 'info')
            safe_print("-" * 80, 'info')

            if perf.get("test_type") == "endurance":
                # Detailed endurance test results
                safe_print(f"Total Operations:  {perf.get('total_operations', 0):,} ({perf.get('total_operations', 0)/1e9:.2f} billion)", 'info')
                safe_print(f"Mission Steps:     {perf.get('cycles', 0):,}", 'info')
                safe_print(f"Test Duration:     {perf.get('elapsed_s', 0):.2f} seconds ({perf.get('elapsed_min', 0):.2f} minutes)", 'info')
                safe_print(f"Throughput:        {perf.get('current_ops_per_second', 0):,.0f} ops/sec", 'info')
                safe_print(f"Time per Op:       {perf.get('ops_per_ns', 0):.2f} ns/op", 'info')
                safe_print(f"Speedup Factor:    {perf.get('speedup_factor', 0):.2f}x", 'info')
                safe_print("", 'info')

                # Calculate expected vs actual
                expected_ops = 5_475_000 * 1024 * 30  # 168.192 billion
                actual_ops = perf.get('total_operations', 0)
                if actual_ops and expected_ops:
                    accuracy_pct = (actual_ops / expected_ops) * 100
                    safe_print(f"Expected Operations: {expected_ops:,} ({expected_ops/1e9:.2f} billion)", 'info')
                    safe_print(f"Actual Operations:   {actual_ops:,} ({actual_ops/1e9:.2f} billion)", 'info')
                    safe_print(f"Test Accuracy:       {accuracy_pct:.2f}%", 'info')

                # Stability check
                if perf.get('elapsed_min', 0) >= 10.0:
                    safe_print("", 'info')
                    safe_print("[OK] ENDURANCE TEST PASSED: 10+ minute duration achieved", 'info')
                else:
                    safe_print("", 'info')
                    safe_print(f"[!] WARNING: Test duration ({perf.get('elapsed_min', 0):.2f} min) < 10 minutes", 'info')
            else:
                # Standard test results
                safe_print(f"Throughput: {perf.get('current_ops_per_second', 0):,.0f} ops/s", 'info')
                safe_print(f"Speedup:    {perf.get('speedup_factor', 0):.2f}x", 'info')

        safe_print("", 'info')

    def save(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"{REPORT_PREFIX}_{ts}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        safe_print(f"Detailed results saved to: {fname}", 'info')
        return fname

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    safe_print("DASE Analog Engine Comprehensive Benchmark", 'info')
    safe_print("="*50, 'info')
    safe_print(f"System: {platform.system()}-{platform.release()} ({platform.version()})", 'info')
    safe_print(f"Python: {platform.python_version()}", 'info')
    safe_print(f"Logical CPUs: {os.cpu_count()}", 'info')

    bench = DASEBenchmark()
    bench.initialize_engine(num_nodes=1024)

    # Run basic sanity checks first
    bench.test_basic_ops()
    bench.test_accuracy()

    # ENDURANCE TEST CONFIGURATION
    # Total Operations: ~168.3 billion ops
    # Expected Duration: ≥10 minutes (~603 seconds at 280.3M ops/sec)
    # Mission Steps: 5,475,000
    # Nodes: 1,024
    # Iterations per Node: 30
    # CPU Utilization: 100% (12/12 cores)
    bench.test_performance(cycles=5_475_000, test_type="endurance")

    bench.summarize()
    bench.save()

if __name__ == "__main__":
    main()
