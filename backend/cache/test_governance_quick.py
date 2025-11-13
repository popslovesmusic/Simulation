"""Quick test for Governance Agent."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cache.governance_agent import CacheGovernanceAgent

def test_governance_agent():
    """Test governance agent basic functionality."""
    print("\n" + "="*60)
    print("GOVERNANCE AGENT - QUICK TEST")
    print("="*60)

    # Initialize agent
    print("\n1. Initializing governance agent...")
    agent = CacheGovernanceAgent(cache_root="./cache")
    print("   OK - Agent initialized")

    # Generate health report
    print("\n2. Generating health report...")
    report = agent.generate_health_report()
    print(f"   OK - Report generated")
    print(f"   Total entries: {report.total_entries}")
    print(f"   Total size: {report.total_size_mb:.2f} MB")
    print(f"   Overall hit rate: {report.overall_hit_rate:.1%}")
    print(f"   Categories: {len(report.categories)}")

    # Show category details
    print("\n3. Category health:")
    for cat, metrics in report.categories.items():
        health = "healthy" if metrics.is_healthy() else "needs attention"
        print(f"   {cat:25s} | {metrics.total_entries:4d} entries | "
              f"{metrics.total_size_mb:6.2f} MB | "
              f"{metrics.hit_rate:5.1%} hit rate | {health}")

    # Show recommendations
    if report.recommendations:
        print("\n4. Recommendations:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("\n4. Recommendations: None (system healthy)")

    # Show warnings
    if report.warnings:
        print("\n5. Warnings:")
        for i, warn in enumerate(report.warnings, 1):
            print(f"   {i}. {warn}")
    else:
        print("\n5. Warnings: None")

    # Check if warmup needed
    print("\n6. Warmup check:")
    needs_warmup = agent.needs_warmup()
    print(f"   Warmup needed: {needs_warmup}")

    # Growth prediction
    print("\n7. Growth prediction:")
    growth = agent.predict_growth(days_ahead=30)
    if "error" in growth:
        print(f"   {growth['error']}")
    else:
        print(f"   Current: {growth['current']['entries']} entries, "
              f"{growth['current']['size_mb']:.2f} MB")
        print(f"   Predicted (30 days): {growth['predicted']['entries']} entries, "
              f"{growth['predicted']['size_mb']:.2f} MB")

    # Save report
    print("\n8. Saving report...")
    report_path = Path("./cache/governance_report.json")
    report.save(report_path)
    print(f"   OK - Report saved to: {report_path}")

    print("\n" + "="*60)
    print("ALL TESTS PASSED")
    print("="*60)


if __name__ == "__main__":
    test_governance_agent()
