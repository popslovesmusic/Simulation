#!/usr/bin/env python3
"""Unified governance CLI for DASE cache system.

This CLI provides a single interface for all governance operations:
- Health monitoring
- Benchmark validation
- Static analysis
- Automated maintenance

Usage:
    python dase_governance_cli.py health
    python dase_governance_cli.py benchmark
    python dase_governance_cli.py analyze
    python dase_governance_cli.py maintain
    python dase_governance_cli.py report
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache.governance_agent import CacheGovernanceAgent
from cache.benchmark_scheduler import BenchmarkScheduler
from cache.static_analysis import StaticAnalyzer


class GovernanceCLI:
    """Unified CLI for cache governance."""

    def __init__(self, cache_root: str = "./cache"):
        """Initialize governance CLI.

        Args:
            cache_root: Path to cache root directory
        """
        self.cache_root = cache_root
        self.agent = CacheGovernanceAgent(cache_root=cache_root)
        self.scheduler = BenchmarkScheduler(cache_root=cache_root)
        self.analyzer = StaticAnalyzer()

    def cmd_health(self, save: bool = False):
        """Show cache health status.

        Args:
            save: If True, save report to file
        """
        print("\n" + "="*70)
        print("CACHE HEALTH REPORT")
        print("="*70)

        report = self.agent.generate_health_report()

        # Summary
        print(f"\nTimestamp: {report.timestamp}")
        print(f"Cache Root: {report.cache_root}")
        print(f"\nOverall Statistics:")
        print(f"  Total entries:    {report.total_entries:6d}")
        print(f"  Total size:       {report.total_size_mb:6.2f} MB")
        print(f"  Overall hit rate: {report.overall_hit_rate:6.1%}")

        # Category details
        if report.categories:
            print(f"\nCategory Details:")
            print(f"  {'Category':<25s} {'Entries':>8s} {'Size (MB)':>10s} "
                  f"{'Hit Rate':>10s} {'Health':>12s}")
            print(f"  {'-'*25} {'-'*8} {'-'*10} {'-'*10} {'-'*12}")

            for cat, metrics in report.categories.items():
                health = "[OK] Healthy" if metrics.is_healthy() else "[!] Issues"
                print(f"  {cat:<25s} {metrics.total_entries:8d} "
                      f"{metrics.total_size_mb:10.2f} "
                      f"{metrics.hit_rate:9.1%} {health:>12s}")

        # Warnings
        if report.warnings:
            print(f"\n[!] Warnings ({len(report.warnings)}):")
            for i, warning in enumerate(report.warnings, 1):
                print(f"  {i}. {warning}")

        # Recommendations
        if report.recommendations:
            print(f"\n[*] Recommendations ({len(report.recommendations)}):")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print(f"\n[OK] No recommendations - system is healthy")

        # Growth prediction
        growth = self.agent.predict_growth(days_ahead=30)
        if "error" not in growth:
            print(f"\n[GROWTH] Prediction (30 days):")
            print(f"  Current:   {growth['current']['entries']:5d} entries, "
                  f"{growth['current']['size_mb']:6.2f} MB")
            print(f"  Predicted: {growth['predicted']['entries']:5d} entries, "
                  f"{growth['predicted']['size_mb']:6.2f} MB")

        if save:
            output_path = Path(self.cache_root) / "governance_report.json"
            report.save(output_path)
            print(f"\n[OK] Report saved to: {output_path}")

        print()

    def cmd_benchmark(
        self,
        set_baseline: bool = False,
        compare: bool = True
    ):
        """Run benchmark validation.

        Args:
            set_baseline: If True, save results as new baseline
            compare: If True, compare against baseline
        """
        print("\n" + "="*70)
        print("BENCHMARK VALIDATION")
        print("="*70)

        # Run benchmarks
        results = self.scheduler.run_benchmark_suite()

        # Summary
        num_passed = sum(1 for r in results if r.status == "success")
        num_failed = sum(1 for r in results if r.status == "error")

        print(f"\nResults: {num_passed}/{len(results)} passed")

        # Show details
        print(f"\nBenchmark Details:")
        print(f"  {'Benchmark':<25s} {'Status':>10s} {'Duration (ms)':>15s} {'Hit Rate':>10s}")
        print(f"  {'-'*25} {'-'*10} {'-'*15} {'-'*10}")

        for result in results:
            status = "[OK] Pass" if result.status == "success" else "[X] Fail"
            print(f"  {result.benchmark_name:<25s} {status:>10s} "
                  f"{result.duration_ms:15.1f} {result.hit_rate:9.1%}")

        # Compare to baseline
        if compare:
            comparisons = self.scheduler.compare_to_baseline(results)
            if comparisons:
                print(f"\n[BASELINE] Comparison:")

                regressions = [c for c in comparisons if c.is_regression]
                if regressions:
                    print(f"\n  [!] Regressions detected ({len(regressions)}):")
                    for comp in regressions:
                        print(f"    {comp.benchmark_name}:")
                        for reason in comp.regression_reasons:
                            print(f"      - {reason}")
                else:
                    print(f"  [OK] No regressions detected")
            else:
                print(f"\n  No baseline found for comparison")

        # Set baseline
        if set_baseline:
            self.scheduler.set_baseline(results)
            print(f"\n[OK] Baseline updated")

        print()

    def cmd_analyze(self, save: bool = False):
        """Run static code analysis.

        Args:
            save: If True, save report to file
        """
        print("\n" + "="*70)
        print("STATIC CODE ANALYSIS")
        print("="*70)

        report = self.analyzer.run_analysis()

        # Summary
        print(f"\nTimestamp: {report.timestamp}")
        print(f"\nOverall Statistics:")
        print(f"  Total files:             {report.total_files:6d}")
        print(f"  Total lines:             {report.total_lines:6d}")
        print(f"  Code lines:              {report.total_code_lines:6d}")
        print(f"  Functions:               {report.total_functions:6d}")
        print(f"  Classes:                 {report.total_classes:6d}")
        print(f"  Avg docstring coverage:  {report.avg_docstring_coverage:6.1%}")

        # Module details
        if report.modules:
            print(f"\nModule Details:")
            print(f"  {'Module':<40s} {'LOC':>6s} {'Funcs':>6s} {'Classes':>8s} {'Doc %':>8s}")
            print(f"  {'-'*40} {'-'*6} {'-'*6} {'-'*8} {'-'*8}")

            for module in report.modules:
                module_name = Path(module.module_path).name
                print(f"  {module_name:<40s} {module.code_lines:6d} "
                      f"{module.num_functions:6d} {module.num_classes:8d} "
                      f"{module.docstring_coverage:7.1%}")

        # Issues
        if report.issues:
            print(f"\n[!] Issues ({len(report.issues)}):")
            for i, issue in enumerate(report.issues[:10], 1):  # Show max 10
                print(f"  {i}. {issue}")
            if len(report.issues) > 10:
                print(f"  ... and {len(report.issues) - 10} more")

        # Recommendations
        if report.recommendations:
            print(f"\n[*] Recommendations ({len(report.recommendations)}):")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")

        if save:
            output_path = Path(self.cache_root) / "static_analysis_report.json"
            report.save(output_path)
            print(f"\n[OK] Report saved to: {output_path}")

        print()

    def cmd_maintain(
        self,
        cleanup: bool = True,
        warmup: bool = True
    ):
        """Run automated maintenance.

        Args:
            cleanup: If True, cleanup stale entries
            warmup: If True, run warmup if needed
        """
        print("\n" + "="*70)
        print("AUTOMATED MAINTENANCE")
        print("="*70)

        print("\nRunning maintenance tasks...")

        results = self.agent.run_maintenance(
            cleanup_stale=cleanup,
            warmup_if_needed=warmup
        )

        print(f"\nInitial State:")
        print(f"  Entries: {results['initial_state']['entries']}")
        print(f"  Size:    {results['initial_state']['size_mb']:.2f} MB")

        if results['actions_taken']:
            print(f"\nActions Taken ({len(results['actions_taken'])}):")
            for action in results['actions_taken']:
                action_name = action['action']
                result = action['result']

                if action_name == "cleanup_stale":
                    print(f"  [OK] Cleanup: Removed {result['removed_count']} stale entries, "
                          f"freed {result['freed_mb']:.2f} MB")
                elif action_name == "warmup":
                    if result['status'] == 'success':
                        print(f"  [OK] Warmup: Created {result['entries_created']} entries, "
                              f"{result['cache_size_mb']:.2f} MB")
                    else:
                        print(f"  [X] Warmup failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"\n[OK] No maintenance needed")

        print(f"\nFinal State:")
        print(f"  Entries: {results['final_state']['entries']}")
        print(f"  Size:    {results['final_state']['size_mb']:.2f} MB")

        print()

    def cmd_report(self, output: Optional[str] = None):
        """Generate comprehensive governance report.

        Args:
            output: Output file path (None = print to console)
        """
        print("\n" + "="*70)
        print("COMPREHENSIVE GOVERNANCE REPORT")
        print("="*70)

        # Collect all data
        health_report = self.agent.generate_health_report()
        benchmark_results = self.scheduler.run_benchmark_suite()
        analysis_report = self.analyzer.run_analysis()

        # Compile report
        report = {
            "timestamp": health_report.timestamp,
            "health": health_report.to_dict(),
            "benchmarks": [r.to_dict() for r in benchmark_results],
            "static_analysis": analysis_report.to_dict()
        }

        if output:
            import json
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n[OK] Comprehensive report saved to: {output_path}")
        else:
            # Print summary
            print(f"\n[SUMMARY] Overview:")
            print(f"  Cache entries:        {health_report.total_entries}")
            print(f"  Cache size:           {health_report.total_size_mb:.2f} MB")
            print(f"  Hit rate:             {health_report.overall_hit_rate:.1%}")
            print(f"  Benchmarks passed:    {sum(1 for r in benchmark_results if r.status == 'success')}/{len(benchmark_results)}")
            print(f"  Code files:           {analysis_report.total_files}")
            print(f"  Code lines:           {analysis_report.total_code_lines}")
            print(f"  Docstring coverage:   {analysis_report.avg_docstring_coverage:.1%}")

        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DASE Cache Governance CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--cache-root",
        default="./cache",
        help="Path to cache root directory (default: ./cache)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Health command
    health_parser = subparsers.add_parser("health", help="Show cache health status")
    health_parser.add_argument("--save", action="store_true", help="Save report to file")

    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run benchmark validation")
    bench_parser.add_argument("--set-baseline", action="store_true", help="Save as new baseline")
    bench_parser.add_argument("--no-compare", action="store_true", help="Skip baseline comparison")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run static code analysis")
    analyze_parser.add_argument("--save", action="store_true", help="Save report to file")

    # Maintain command
    maintain_parser = subparsers.add_parser("maintain", help="Run automated maintenance")
    maintain_parser.add_argument("--no-cleanup", action="store_true", help="Skip stale cleanup")
    maintain_parser.add_argument("--no-warmup", action="store_true", help="Skip warmup")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate comprehensive report")
    report_parser.add_argument("--output", "-o", help="Output file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize CLI
    cli = GovernanceCLI(cache_root=args.cache_root)

    # Dispatch command
    if args.command == "health":
        cli.cmd_health(save=args.save)

    elif args.command == "benchmark":
        cli.cmd_benchmark(
            set_baseline=args.set_baseline,
            compare=not args.no_compare
        )

    elif args.command == "analyze":
        cli.cmd_analyze(save=args.save)

    elif args.command == "maintain":
        cli.cmd_maintain(
            cleanup=not args.no_cleanup,
            warmup=not args.no_warmup
        )

    elif args.command == "report":
        cli.cmd_report(output=args.output)


if __name__ == "__main__":
    main()
