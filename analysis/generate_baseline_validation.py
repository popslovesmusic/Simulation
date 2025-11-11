"""Generate a baseline validation report for Phase 0."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_PATH = ROOT / "verification_results_20251023_054706.json"
WAVEFORM_PATH = ROOT / "gw_waveform_alpha_1.500000.csv"
REPORT_PATH = ROOT / "analysis" / "baseline_validation_report.md"


@dataclass
class CheckResult:
    name: str
    metric: str
    measured: float
    expected: float
    tolerance: float
    comparison: str = "abs"  # one of {"abs", "max", "min"}

    @property
    def delta(self) -> float:
        return self.measured - self.expected

    @property
    def within_tolerance(self) -> bool:
        if self.comparison == "abs":
            return abs(self.delta) <= self.tolerance
        if self.comparison == "max":
            return self.measured <= self.expected + self.tolerance
        if self.comparison == "min":
            return self.measured >= self.expected - self.tolerance
        raise ValueError(f"Unknown comparison mode: {self.comparison}")


@dataclass
class FlaggedItem:
    name: str
    message: str


def load_verification() -> Dict[str, dict]:
    return json.loads(VERIFICATION_PATH.read_text())["tests"]


def gather_waveform_metrics() -> Dict[str, float]:
    with WAVEFORM_PATH.open(newline="") as handle:
        reader = csv.DictReader(handle)
        amplitudes = [float(row["amplitude"]) for row in reader]
    return {
        "samples": float(len(amplitudes)),
        "peak": max(amplitudes),
        "mean": sum(amplitudes) / len(amplitudes),
    }


def evaluate() -> tuple[List[CheckResult], List[FlaggedItem]]:
    verification = load_verification()
    waveform = gather_waveform_metrics()

    checks: List[CheckResult] = []
    flags: List[FlaggedItem] = []

    # Oscillator benchmarks (pure tones)
    for label, target in {
        "oscillator_100.0hz": 100.0,
        "oscillator_440.0hz": 440.0,
        "oscillator_1000.0hz": 1000.0,
    }.items():
        measured = float(verification[label]["frequency_hz"])
        checks.append(
            CheckResult(
                name=label,
                metric="frequency_hz",
                measured=measured,
                expected=target,
                tolerance=1e-6,
            )
        )

    # Filter attenuation ratio (theoretical 9/34)
    target_ratio = 9 / 34
    for samples in (64, 128, 256, 512, 1024):
        label = f"filter_{samples}samples"
        measured = float(verification[label]["energy_ratio"])
        checks.append(
            CheckResult(
                name=label,
                metric="energy_ratio",
                measured=measured,
                expected=target_ratio,
                tolerance=5e-8,
            )
        )

    # Engine performance gating (ns/op <= 100, speedup >= 150)
    perf = verification["engine_integration"]
    ns_per_op = float(perf["ns_per_op"])
    speedup = float(perf["speedup"])
    checks.append(
        CheckResult(
            name="engine_integration",
            metric="ns_per_op",
            measured=ns_per_op,
            expected=100.0,
            tolerance=0.0,
            comparison="max",
        )
    )
    if ns_per_op > 100.0:
        flags.append(
            FlaggedItem(
                name="engine_integration",
                message=f"ns_per_op regressed to {ns_per_op:.2f} (> 100 target)",
            )
        )

    checks.append(
        CheckResult(
            name="engine_integration",
            metric="speedup",
            measured=speedup,
            expected=150.0,
            tolerance=0.0,
            comparison="min",
        )
    )
    if speedup < 150.0:
        flags.append(
            FlaggedItem(
                name="engine_integration",
                message=f"speedup dropped to {speedup:.2f} (< 150 target)",
            )
        )

    # Waveform amplitude scaling (alpha^2 law)
    alpha = 1.5
    analytic_base = 1.9515021322657777e-19
    expected_peak = analytic_base * alpha ** 2
    peak = waveform["peak"]
    tolerance = expected_peak * 0.02
    checks.append(
        CheckResult(
            name="gw_waveform_alpha_1.500000",
            metric="peak_amplitude",
            measured=peak,
            expected=expected_peak,
            tolerance=tolerance,
        )
    )
    if abs(peak - expected_peak) > tolerance:
        flags.append(
            FlaggedItem(
                name="gw_waveform_alpha_1.500000",
                message=(
                    "Waveform peak amplitude deviates more than 2% from the "
                    "quadrupole scaling expectation."
                ),
            )
        )

    # Mean amplitude sanity check
    mean_expected = expected_peak * 0.45  # empirical envelope from prior runs
    mean_tol = mean_expected * 0.1
    checks.append(
        CheckResult(
            name="gw_waveform_alpha_1.500000",
            metric="mean_amplitude",
            measured=waveform["mean"],
            expected=mean_expected,
            tolerance=mean_tol,
        )
    )
    if abs(waveform["mean"] - mean_expected) > mean_tol:
        flags.append(
            FlaggedItem(
                name="gw_waveform_alpha_1.500000",
                message="Waveform mean amplitude drifted outside the 10% stability band.",
            )
        )

    return checks, flags


def render_markdown(checks: Iterable[CheckResult], flags: Iterable[FlaggedItem]) -> str:
    checks = list(checks)
    flags = list(flags)

    def status_icon(check: CheckResult) -> str:
        return "✅" if check.within_tolerance else "⚠️"

    lines: List[str] = []
    lines.append("# Phase 0 Baseline Validation Report")
    lines.append("")
    lines.append("This report captures automated comparisons between the current artifact set")
    lines.append("and the analytical benchmarks established for Phase 0 mobilization.")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    pass_count = sum(1 for check in checks if check.within_tolerance)
    total = len(checks)
    lines.append(f"- Checks within tolerance: {pass_count} / {total}")
    lines.append(f"- Flagged follow-ups: {len(flags)}")
    lines.append("")

    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| Status | Artifact | Metric | Measured | Benchmark | Rule | Δ |")
    lines.append("|--------|----------|--------|----------|-----------|------|---|")
    for check in checks:
        if check.comparison == "abs":
            rule = f"±{check.tolerance:.2e}"
        elif check.comparison == "max":
            rule = f"≤{(check.expected + check.tolerance):.2e}"
        elif check.comparison == "min":
            rule = f"≥{(check.expected - check.tolerance):.2e}"
        else:
            rule = "?"
        lines.append(
            "| {status} | {name} | {metric} | {measured:.6e} | {expected:.6e} | "
            "{rule} | {delta:.2e} |".format(
                status=status_icon(check),
                name=check.name,
                metric=check.metric,
                measured=check.measured,
                expected=check.expected,
                rule=rule,
                delta=check.delta,
            )
        )
    lines.append("")

    lines.append("## Flags")
    lines.append("")
    if flags:
        for flag in flags:
            lines.append(f"- **{flag.name}** — {flag.message}")
    else:
        lines.append("- None; all metrics are within the configured tolerances.")
    lines.append("")

    lines.append("## Data Sources")
    lines.append("")
    lines.append(f"- Verification log: `{VERIFICATION_PATH.name}`")
    lines.append(f"- Waveform sample: `{WAVEFORM_PATH.name}`")

    return "\n".join(lines)


def main() -> None:
    checks, flags = evaluate()
    markdown = render_markdown(checks, flags)
    REPORT_PATH.write_text(markdown)


if __name__ == "__main__":
    main()
