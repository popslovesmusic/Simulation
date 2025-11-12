#!/usr/bin/env python3
"""DASE Cache Maintenance Script.

Provides utilities for:
- Cache health monitoring
- Automatic cleanup of old entries
- Cache size management
- Integrity checking
- Performance reporting

Usage:
    python scripts/cache_maintenance.py --check
    python scripts/cache_maintenance.py --cleanup --max-size-mb 1000
    python scripts/cache_maintenance.py --report
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime, timedelta
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from cache import CacheManager


class CacheMaintenance:
    """Cache maintenance and monitoring utilities."""

    def __init__(self, cache_root: str = "./cache"):
        """Initialize maintenance utility.

        Args:
            cache_root: Path to cache root directory
        """
        self.cache = CacheManager(root=cache_root)
        self.categories = [
            "fractional_kernels",
            "stencils",
            "fftw_wisdom",
            "echo_templates",
            "state_profiles",
            "source_maps",
            "mission_graph",
            "surrogates"
        ]

    def health_check(self) -> dict:
        """Perform cache health check.

        Returns:
            Health check results
        """
        print("\n" + "=" * 60)
        print("CACHE HEALTH CHECK")
        print("=" * 60)

        issues = []
        stats = self.cache.get_stats()

        # Check total size
        total_size_mb = stats["total_size_mb"]
        if total_size_mb > 1000:
            issues.append(f"Cache size ({total_size_mb:.1f} MB) exceeds 1 GB")

        # Check each category
        for category in self.categories:
            cat_stats = stats["categories"].get(category, {})
            entries = cat_stats.get("entries", {})

            # Check for very old entries (>30 days)
            for key, entry in entries.items():
                created_str = entry.get("created_at")
                if created_str:
                    try:
                        created = datetime.fromisoformat(created_str.rstrip('Z'))
                        age_days = (datetime.utcnow() - created).days

                        if age_days > 30:
                            issues.append(
                                f"{category}/{key} is {age_days} days old"
                            )
                    except Exception:
                        pass

            # Check for never-accessed entries
            never_accessed = [
                key for key, entry in entries.items()
                if entry.get("access_count", 0) == 0
            ]

            if never_accessed:
                issues.append(
                    f"{category}: {len(never_accessed)} entries never accessed"
                )

        # Report
        print(f"\nTotal entries: {sum(c.get('total_entries', 0) for c in stats['categories'].values())}")
        print(f"Total size: {total_size_mb:.2f} MB")

        if issues:
            print(f"\nIssues found: {len(issues)}")
            for issue in issues[:10]:  # Show first 10
                print(f"  - {issue}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")

            return {"status": "warning", "issues": issues}
        else:
            print("\n[OK] No issues found")
            return {"status": "healthy", "issues": []}

    def cleanup_old_entries(
        self,
        max_age_days: int = 30,
        dry_run: bool = True
    ) -> int:
        """Remove entries older than specified age.

        Args:
            max_age_days: Maximum age in days
            dry_run: If True, only report what would be deleted

        Returns:
            Number of entries deleted (or would be deleted)
        """
        print("\n" + "=" * 60)
        print(f"CLEANUP: Entries older than {max_age_days} days")
        if dry_run:
            print("(DRY RUN - no changes will be made)")
        print("=" * 60)

        to_delete = []
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)

        for category in self.categories:
            stats = self.cache.get_stats(category)
            entries = stats.get("entries", {})

            for key, entry in entries.items():
                created_str = entry.get("created_at")
                if created_str:
                    try:
                        created = datetime.fromisoformat(created_str.rstrip('Z'))

                        if created < cutoff:
                            to_delete.append((category, key, created))
                    except Exception:
                        pass

        if not to_delete:
            print("\nNo old entries found.")
            return 0

        print(f"\nFound {len(to_delete)} old entries:")
        for category, key, created in to_delete[:10]:
            age_days = (datetime.utcnow() - created).days
            print(f"  - {category}/{key} ({age_days} days old)")

        if len(to_delete) > 10:
            print(f"  ... and {len(to_delete) - 10} more")

        if not dry_run:
            print("\nDeleting...")
            for category, key, _ in to_delete:
                self.cache.delete(category, key)
            print(f"[OK] Deleted {len(to_delete)} entries")

        return len(to_delete)

    def cleanup_unused_entries(self, dry_run: bool = True) -> int:
        """Remove entries that have never been accessed.

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            Number of entries deleted (or would be deleted)
        """
        print("\n" + "=" * 60)
        print("CLEANUP: Never-accessed entries")
        if dry_run:
            print("(DRY RUN - no changes will be made)")
        print("=" * 60)

        to_delete = []

        for category in self.categories:
            stats = self.cache.get_stats(category)
            entries = stats.get("entries", {})

            for key, entry in entries.items():
                if entry.get("access_count", 0) == 0:
                    to_delete.append((category, key))

        if not to_delete:
            print("\nNo unused entries found.")
            return 0

        print(f"\nFound {len(to_delete)} unused entries:")
        for category, key in to_delete[:10]:
            print(f"  - {category}/{key}")

        if len(to_delete) > 10:
            print(f"  ... and {len(to_delete) - 10} more")

        if not dry_run:
            print("\nDeleting...")
            for category, key in to_delete:
                self.cache.delete(category, key)
            print(f"[OK] Deleted {len(to_delete)} entries")

        return len(to_delete)

    def enforce_size_limit(
        self,
        max_size_mb: float,
        dry_run: bool = True
    ) -> int:
        """Enforce maximum cache size by removing least-recently-used entries.

        Args:
            max_size_mb: Maximum cache size in MB
            dry_run: If True, only report what would be deleted

        Returns:
            Number of entries deleted (or would be deleted)
        """
        print("\n" + "=" * 60)
        print(f"CLEANUP: Enforce {max_size_mb:.1f} MB size limit")
        if dry_run:
            print("(DRY RUN - no changes will be made)")
        print("=" * 60)

        stats = self.cache.get_stats()
        current_size_mb = stats["total_size_mb"]

        if current_size_mb <= max_size_mb:
            print(f"\nCurrent size ({current_size_mb:.2f} MB) is within limit.")
            return 0

        print(f"\nCurrent size: {current_size_mb:.2f} MB")
        print(f"Target size:  {max_size_mb:.2f} MB")
        print(f"Need to free: {current_size_mb - max_size_mb:.2f} MB")

        # Collect all entries with access times
        all_entries = []
        for category in self.categories:
            cat_stats = stats["categories"].get(category, {})
            entries = cat_stats.get("entries", {})

            for key, entry in entries.items():
                last_accessed = entry.get("last_accessed")
                size_mb = entry.get("size_bytes", 0) / (1024 * 1024)

                # Parse last accessed time
                if last_accessed:
                    try:
                        accessed = datetime.fromisoformat(last_accessed.rstrip('Z'))
                    except Exception:
                        accessed = datetime.min
                else:
                    accessed = datetime.min

                all_entries.append((category, key, accessed, size_mb))

        # Sort by access time (oldest first)
        all_entries.sort(key=lambda x: x[2])

        # Delete until size limit met
        to_delete = []
        freed_mb = 0.0

        for category, key, accessed, size_mb in all_entries:
            to_delete.append((category, key, size_mb))
            freed_mb += size_mb

            if current_size_mb - freed_mb <= max_size_mb:
                break

        print(f"\nWill delete {len(to_delete)} entries ({freed_mb:.2f} MB):")
        for category, key, size_mb in to_delete[:10]:
            print(f"  - {category}/{key} ({size_mb:.2f} MB)")

        if len(to_delete) > 10:
            print(f"  ... and {len(to_delete) - 10} more")

        if not dry_run:
            print("\nDeleting...")
            for category, key, _ in to_delete:
                self.cache.delete(category, key)
            print(f"[OK] Deleted {len(to_delete)} entries, freed {freed_mb:.2f} MB")

        return len(to_delete)

    def generate_report(self, output_file: str = None) -> dict:
        """Generate detailed cache usage report.

        Args:
            output_file: Optional path to save JSON report

        Returns:
            Report data dict
        """
        print("\n" + "=" * 60)
        print("CACHE USAGE REPORT")
        print("=" * 60)

        stats = self.cache.get_stats()
        report = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_size_mb": stats["total_size_mb"],
            "total_entries": 0,
            "total_accesses": 0,
            "categories": {}
        }

        # Per-category analysis
        for category in self.categories:
            cat_stats = stats["categories"].get(category, {})
            entries = cat_stats.get("entries", {})

            if not entries:
                continue

            # Calculate statistics
            access_counts = [e.get("access_count", 0) for e in entries.values()]
            sizes_mb = [e.get("size_bytes", 0) / (1024 * 1024) for e in entries.values()]

            category_report = {
                "total_entries": len(entries),
                "total_size_mb": sum(sizes_mb),
                "total_accesses": sum(access_counts),
                "avg_accesses_per_entry": sum(access_counts) / len(access_counts) if access_counts else 0,
                "avg_size_mb": sum(sizes_mb) / len(sizes_mb) if sizes_mb else 0,
                "most_accessed": None,
                "largest_entry": None
            }

            # Find most accessed
            if access_counts:
                max_accesses = max(access_counts)
                for key, entry in entries.items():
                    if entry.get("access_count", 0) == max_accesses:
                        category_report["most_accessed"] = {
                            "key": key,
                            "accesses": max_accesses
                        }
                        break

            # Find largest
            if sizes_mb:
                max_size = max(sizes_mb)
                for key, entry in entries.items():
                    if entry.get("size_bytes", 0) / (1024 * 1024) == max_size:
                        category_report["largest_entry"] = {
                            "key": key,
                            "size_mb": max_size
                        }
                        break

            report["categories"][category] = category_report
            report["total_entries"] += len(entries)
            report["total_accesses"] += sum(access_counts)

            # Print summary
            print(f"\n{category}:")
            print(f"  Entries:     {len(entries)}")
            print(f"  Size:        {sum(sizes_mb):.2f} MB")
            print(f"  Accesses:    {sum(access_counts)}")
            if category_report["most_accessed"]:
                ma = category_report["most_accessed"]
                print(f"  Most used:   {ma['key']} ({ma['accesses']} accesses)")

        # Overall summary
        print(f"\n{'=' * 60}")
        print(f"Total entries: {report['total_entries']}")
        print(f"Total size:    {report['total_size_mb']:.2f} MB")
        print(f"Total accesses: {report['total_accesses']}")

        # Save to file if requested
        if output_file:
            Path(output_file).write_text(json.dumps(report, indent=2))
            print(f"\nReport saved to: {output_file}")

        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DASE Cache Maintenance Utility"
    )

    parser.add_argument(
        '--root',
        default='./cache',
        help='Cache root directory (default: ./cache)'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Perform health check'
    )

    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Cleanup old/unused entries'
    )

    parser.add_argument(
        '--max-age-days',
        type=int,
        default=30,
        help='Maximum age for entries (default: 30 days)'
    )

    parser.add_argument(
        '--max-size-mb',
        type=float,
        help='Maximum cache size in MB'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate usage report'
    )

    parser.add_argument(
        '--output',
        help='Output file for report (JSON)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    maintenance = CacheMaintenance(cache_root=args.root)

    try:
        if args.check:
            result = maintenance.health_check()
            return 0 if result["status"] == "healthy" else 1

        elif args.cleanup:
            count = maintenance.cleanup_old_entries(
                max_age_days=args.max_age_days,
                dry_run=args.dry_run
            )

            count += maintenance.cleanup_unused_entries(dry_run=args.dry_run)

            if args.max_size_mb:
                count += maintenance.enforce_size_limit(
                    max_size_mb=args.max_size_mb,
                    dry_run=args.dry_run
                )

            return 0

        elif args.report:
            maintenance.generate_report(output_file=args.output)
            return 0

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
