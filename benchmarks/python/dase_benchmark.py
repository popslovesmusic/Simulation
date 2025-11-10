# dase_benchmark.py
# Drop-in benchmark for DASE / DVSL AVX2 backend.
# - Detects AVX2 & FMA via dase_engine.CPUFeatures
# - Uses AnalogCellularEngineAVX2 and AnalogUniversalNodeAVX2
# - Falls back to simulation only if import fails
# - Writes JSON results to dase_benchmark_results_YYYYMMDD_HHMMSS.json

from __future__ import annotations
import json
import math
import os
import platform
import sys
import time
from datetime import datetime
from typing import Any, Dict

REPORT_PREFIX = "dase_benchmark_results"

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
        print("Engine module loaded but required classes are missing.")
except Exception as e:
    print("Engine import failed:", e)
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
            print("Engine not available — running simulation mode.")
            return False
        try:
            caps = {
                "avx2": bool(de.CPUFeatures.has_avx2()),
                "fma": bool(de.CPUFeatures.has_fma())
            }
            self.results["cpu_caps"] = caps
            print(f"CPU Features: AVX2={caps['avx2']}, FMA={caps['fma']}")
            if not caps["avx2"]:
                print("⚠️  AVX2 not detected — performance may be limited.")

            self.engine = de.AnalogCellularEngineAVX2(num_nodes)
            print(f"✅ Engine initialized: AnalogCellularEngineAVX2({num_nodes})")
            return True
        except Exception as e:
            print("Engine initialization failed:", e)
            return False

            # ----------------------- basic ops benchmark -----------------------------
    def test_basic_ops(self) -> None:
        print("\n=== Basic Operations Benchmark ===")
        tests = {}
        import time, numpy as np

        try:
            node = de.AnalogUniversalNodeAVX2() if ENGINE_AVAILABLE else None
            node_ok = node is not None
            if node_ok:
                print("✅ AnalogUniversalNodeAVX2 initialized.")
            else:
                print("⚠️  Using simulated node (engine unavailable).")
        except Exception as e:
            print(f"⚠️  Node init failed: {e}")
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
            print(f"  amplifier : {status}")
        except Exception as e:
            tests["amplifier"] = {"status": "error", "error": str(e)}
            print(f"  amplifier : error ({e})")

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
            print(f"  integrator: {status}")
        except Exception as e:
            tests["integrator"] = {"status": "error", "error": str(e)}
            print(f"  integrator: error ({e})")

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
            print(f"  oscillator: {status}")
        except Exception as e:
            tests["oscillator"] = {"status": "error", "error": str(e)}
            print(f"  oscillator: error ({e})")

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
            print(f"  filter    : {status}")
        except Exception as e:
            tests["filter"] = {"status": "error", "error": str(e)}
            print(f"  filter    : error ({e})")

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
            print(f"  feedback  : {status}")
        except Exception as e:
            tests["feedback"] = {"status": "error", "error": str(e)}
            print(f"  feedback  : error ({e})")

        # --- Save results ----------------------------------------------------
        self.results["basic_ops"] = tests



    # ----------------------- performance scaling ------------------------------
    def test_performance(self, cycles: int = 2000) -> None:
        print("\n=== Performance Scaling Benchmark ===")
        perf = {"mode": "simulation"}
        if self.engine:
            mode = "native"
            t0 = time.perf_counter()
            try:
                self.engine.run_mission(cycles)
                elapsed = time.perf_counter() - t0
                m = self.engine.get_metrics()
                perf = {
                    "mode": mode,
                    "elapsed_s": elapsed,
                    "current_ops_per_second": getattr(m, "current_ops_per_second", None),
                    "speedup_factor": getattr(m, "speedup_factor", None),
                    "total_operations": getattr(m, "total_operations", None),
                }
                print(f"  run_mission({cycles}) elapsed: {elapsed:.4f}s")
                if perf["current_ops_per_second"] is not None:
                    print(f"  ops/s: {perf['current_ops_per_second']:.2f}  speedup: x{perf['speedup_factor']}")
            except Exception as e:
                perf = {"mode": "error", "error": str(e)}
        else:
            # Simulated placeholder
            time.sleep(0.01)
            perf["mode"] = "simulated"
            perf["elapsed_s"] = 0.01
            perf["current_ops_per_second"] = 435.0
            perf["speedup_factor"] = 1.0
            perf["total_operations"] = 1000
            print("  (simulation placeholder)")

        self.results["performance"] = perf

        # ----------------------- accuracy (light checks) --------------------------
    def test_accuracy(self) -> None:
        print("\n=== Numerical Accuracy Benchmark ===")
        acc = {}

        # Helper for tiered tolerance
        def check_accuracy(label, err, strict=1e-3, relaxed=1.5e-3):
            """Tiered accuracy check: passes, warns, or fails based on error size."""
            if err < strict:
                return "passed"
            elif err < relaxed:
                print(f"⚠️  {label}: borderline precision ({err:.6f}) within AVX2 tolerance")
                return "warning"
            else:
                print(f"❌ {label}: precision error too high ({err:.6f})")
                return "failed"

        try:
            import numpy as np
        except ImportError:
            print("NumPy not installed — skipping accuracy tests.")
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
            print(f"  {k:16}: {v['status']:8} (max error: {v.get('error', 0):.6f})")

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
            "performance_mode": perf.get("mode")
        }
        self.results["summary"] = summary

        print("\n" + "="*60)
        print("BENCHMARK SUMMARY REPORT")
        print("="*60)
        print(f"Engine Status: {summary['engine_status']}")
        print(f"Basic Operations: {summary['basic_ops_passed']}")
        print(f"Accuracy Tests: {summary['accuracy_passed']}")
        if perf.get("mode") == "native":
            print(f"Throughput: {perf.get('current_ops_per_second')} ops/s, Speedup x{perf.get('speedup_factor')}")
        print()

    def save(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"{REPORT_PREFIX}_{ts}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        print(f"Detailed results saved to: {fname}")
        return fname

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    print("DASE Analog Engine Comprehensive Benchmark")
    print("="*50)
    print(f"System: {platform.system()}-{platform.release()} ({platform.version()})")
    print(f"Python: {platform.python_version()}")

    bench = DASEBenchmark()
    bench.initialize_engine(num_nodes=1024)

    bench.test_basic_ops()
    bench.test_performance(cycles=3000)
    bench.test_accuracy()
    bench.summarize()
    bench.save()

if __name__ == "__main__":
    main()
