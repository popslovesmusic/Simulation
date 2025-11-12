#!/usr/bin/env python3
"""DASE Cache CLI - Command-line tool for cache management.

Commands:
    dase-cache ls [category]              List cache entries
    dase-cache stats [category]           Show cache statistics
    dase-cache info <category> <key>      Show entry details
    dase-cache clear <category> [key]     Clear cache entries
    dase-cache warmup                     Pre-populate cache with common data
    dase-cache validate                   Validate cache integrity

Examples:
    # List all entries
    python -m backend.cache.dase_cache_cli ls

    # List fractional kernels
    python -m backend.cache.dase_cache_cli ls fractional_kernels

    # Show overall statistics
    python -m backend.cache.dase_cache_cli stats

    # Show stats for specific category
    python -m backend.cache.dase_cache_cli stats surrogates

    # Show entry details
    python -m backend.cache.dase_cache_cli info fractional_kernels kernel_1.5_0.01

    # Clear specific entry
    python -m backend.cache.dase_cache_cli clear fractional_kernels kernel_1.5_0.01

    # Clear entire category
    python -m backend.cache.dase_cache_cli clear fractional_kernels

    # Warmup cache
    python -m backend.cache.dase_cache_cli warmup
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import CacheManager


class CacheCLI:
    """Command-line interface for DASE cache management."""

    def __init__(self, cache_root: str = "./cache"):
        """Initialize CLI with cache manager.

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

    def cmd_ls(self, category: str = None):
        """List cache entries.

        Args:
            category: Optional category to filter by
        """
        if category:
            # List specific category
            if category not in self.categories:
                print(f"Error: Unknown category '{category}'")
                print(f"Valid categories: {', '.join(self.categories)}")
                return 1

            keys = self.cache.backends[category].list_keys()

            if not keys:
                print(f"No entries in '{category}'")
                return 0

            print(f"\n{category}:")
            print("-" * 60)

            stats = self.cache.get_stats(category)
            entries = stats.get("entries", {})

            for key in keys:
                entry = entries.get(key, {})
                size_kb = entry.get("size_bytes", 0) / 1024
                access_count = entry.get("access_count", 0)

                print(f"  {key:40s} {size_kb:8.1f} KB  {access_count:4d} accesses")

            print(f"\nTotal: {len(keys)} entries")

        else:
            # List all categories
            print("\nCache Entries by Category")
            print("=" * 60)

            for cat in self.categories:
                keys = self.cache.backends[cat].list_keys()

                if keys:
                    print(f"\n{cat}: ({len(keys)} entries)")

                    stats = self.cache.get_stats(cat)
                    entries = stats.get("entries", {})

                    for key in keys[:5]:  # Show first 5
                        entry = entries.get(key, {})
                        size_kb = entry.get("size_bytes", 0) / 1024
                        print(f"  - {key:40s} {size_kb:8.1f} KB")

                    if len(keys) > 5:
                        print(f"  ... and {len(keys) - 5} more")

            # Overall summary
            all_stats = self.cache.get_stats()
            print(f"\n{'=' * 60}")
            print(f"Total: {sum(len(self.cache.backends[c].list_keys()) for c in self.categories)} entries")
            print(f"Total size: {all_stats['total_size_mb']:.2f} MB")

        return 0

    def cmd_stats(self, category: str = None):
        """Show cache statistics.

        Args:
            category: Optional category to show stats for
        """
        if category:
            # Stats for specific category
            if category not in self.categories:
                print(f"Error: Unknown category '{category}'")
                return 1

            stats = self.cache.get_stats(category)

            print(f"\nCache Statistics: {category}")
            print("=" * 60)
            print(f"Total entries:    {stats.get('total_entries', 0)}")
            print(f"Total size:       {stats.get('total_size_mb', 0):.2f} MB")
            print(f"Created at:       {stats.get('created_at', 'N/A')}")

            entries = stats.get("entries", {})
            if entries:
                # Calculate access statistics
                access_counts = [e.get("access_count", 0) for e in entries.values()]
                sizes = [e.get("size_bytes", 0) for e in entries.values()]

                print(f"\nAccess Statistics:")
                print(f"  Total accesses:  {sum(access_counts)}")
                print(f"  Avg per entry:   {sum(access_counts) / len(access_counts):.1f}")
                print(f"  Most accessed:   {max(access_counts)}")

                print(f"\nSize Statistics:")
                print(f"  Avg entry size:  {sum(sizes) / len(sizes) / 1024:.1f} KB")
                print(f"  Largest entry:   {max(sizes) / 1024:.1f} KB")
                print(f"  Smallest entry:  {min(sizes) / 1024:.1f} KB")

                # Most accessed entries
                sorted_entries = sorted(
                    entries.items(),
                    key=lambda x: x[1].get("access_count", 0),
                    reverse=True
                )[:5]

                if sorted_entries:
                    print(f"\nMost Accessed Entries:")
                    for key, entry in sorted_entries:
                        count = entry.get("access_count", 0)
                        last = entry.get("last_accessed", "Never")
                        print(f"  {key:40s} {count:4d} accesses (last: {last})")

        else:
            # Overall stats
            all_stats = self.cache.get_stats()

            print("\nOverall Cache Statistics")
            print("=" * 60)
            print(f"Total categories: {all_stats['total_categories']}")
            print(f"Total size:       {all_stats['total_size_mb']:.2f} MB")

            print("\nPer-Category Breakdown:")
            print(f"{'Category':<25s} {'Entries':>10s} {'Size (MB)':>12s} {'Accesses':>10s}")
            print("-" * 60)

            for cat in self.categories:
                cat_stats = all_stats['categories'].get(cat, {})
                entries_count = cat_stats.get('total_entries', 0)
                size_mb = cat_stats.get('total_size_mb', 0)

                # Calculate total accesses
                entries = cat_stats.get('entries', {})
                total_accesses = sum(e.get('access_count', 0) for e in entries.values())

                if entries_count > 0:
                    print(f"{cat:<25s} {entries_count:>10d} {size_mb:>12.2f} {total_accesses:>10d}")

        return 0

    def cmd_info(self, category: str, key: str):
        """Show detailed information about a cache entry.

        Args:
            category: Cache category
            key: Entry key
        """
        if category not in self.categories:
            print(f"Error: Unknown category '{category}'")
            return 1

        if not self.cache.exists(category, key):
            print(f"Error: Entry '{key}' not found in '{category}'")
            return 1

        stats = self.cache.get_stats(category)
        entry = stats['entries'].get(key)

        if not entry:
            print(f"Error: Metadata not found for '{key}'")
            return 1

        print(f"\nCache Entry: {category}/{key}")
        print("=" * 60)
        print(f"Key:           {entry['key']}")
        print(f"Created:       {entry.get('created_at', 'N/A')}")
        print(f"Last accessed: {entry.get('last_accessed', 'Never')}")
        print(f"Access count:  {entry.get('access_count', 0)}")
        print(f"Size:          {entry.get('size_bytes', 0) / 1024:.1f} KB")

        checksum = entry.get('checksum')
        if checksum:
            print(f"Checksum:      {checksum}")

        # Try to show data preview
        try:
            data = self.cache.load(category, key)

            print(f"\nData Preview:")
            print("-" * 60)

            if hasattr(data, 'shape'):  # NumPy array
                print(f"Type:  NumPy array")
                print(f"Shape: {data.shape}")
                print(f"Dtype: {data.dtype}")
                if data.size < 10:
                    print(f"Data:  {data}")
                else:
                    print(f"Data:  {data.flat[:5]} ... {data.flat[-5:]}")

            elif isinstance(data, dict):
                print(f"Type:  Dictionary")
                print(f"Keys:  {list(data.keys())[:10]}")
                if len(data) <= 5:
                    print(f"Data:  {json.dumps(data, indent=2)[:500]}")

            elif isinstance(data, bytes):
                print(f"Type:  Binary data")
                print(f"Size:  {len(data)} bytes")
                print(f"First bytes: {data[:20].hex()}")

            else:
                print(f"Type:  {type(data).__name__}")
                print(f"Data:  {str(data)[:500]}")

        except Exception as e:
            print(f"\nNote: Could not load data preview: {e}")

        return 0

    def cmd_clear(self, category: str, key: str = None):
        """Clear cache entries.

        Args:
            category: Cache category
            key: Optional specific key to clear (if None, clears entire category)
        """
        if category not in self.categories:
            print(f"Error: Unknown category '{category}'")
            return 1

        if key:
            # Clear specific entry
            if not self.cache.exists(category, key):
                print(f"Warning: Entry '{key}' not found in '{category}'")
                return 0

            # Confirm deletion
            print(f"Delete '{category}/{key}'? [y/N] ", end='')
            response = input().strip().lower()

            if response != 'y':
                print("Cancelled.")
                return 0

            success = self.cache.delete(category, key)
            if success:
                print(f"Deleted '{category}/{key}'")
                return 0
            else:
                print(f"Error: Failed to delete '{category}/{key}'")
                return 1

        else:
            # Clear entire category
            stats = self.cache.get_stats(category)
            count = stats.get('total_entries', 0)

            if count == 0:
                print(f"Category '{category}' is already empty.")
                return 0

            # Confirm deletion
            print(f"Delete all {count} entries in '{category}'? [y/N] ", end='')
            response = input().strip().lower()

            if response != 'y':
                print("Cancelled.")
                return 0

            deleted = self.cache.clear_category(category)
            print(f"Deleted {deleted} entries from '{category}'")
            return 0

    def cmd_validate(self):
        """Validate cache integrity (checksums)."""
        print("\nValidating cache integrity...")
        print("=" * 60)

        errors = []
        total_checked = 0

        for category in self.categories:
            stats = self.cache.get_stats(category)
            entries = stats.get("entries", {})

            if not entries:
                continue

            print(f"\nChecking {category}: {len(entries)} entries")

            for key, entry in entries.items():
                total_checked += 1
                stored_checksum = entry.get("checksum")

                if not stored_checksum:
                    continue

                # Load and recompute checksum
                try:
                    backend = self.cache.backends[category]

                    # Get file path
                    if category == "surrogates":
                        path = Path(self.cache.root) / category / f"{key}.pt"
                    elif category == "fftw_wisdom":
                        path = Path(self.cache.root) / category / f"{key}.dat"
                    else:
                        # Try .npz first, then .json
                        path = Path(self.cache.root) / category / f"{key}.npz"
                        if not path.exists():
                            path = Path(self.cache.root) / category / f"{key}.json"

                    if path.exists():
                        computed = self.cache._compute_checksum(path)

                        if computed != stored_checksum:
                            errors.append(f"{category}/{key}: checksum mismatch")
                            print(f"  [FAIL] {key}: checksum mismatch")
                        else:
                            print(f"  [OK] {key}")
                    else:
                        errors.append(f"{category}/{key}: file not found")
                        print(f"  [FAIL] {key}: file not found")

                except Exception as e:
                    errors.append(f"{category}/{key}: {e}")
                    print(f"  [FAIL] {key}: {e}")

        print(f"\n{'=' * 60}")
        print(f"Validation complete: {total_checked} entries checked")

        if errors:
            print(f"\n{len(errors)} errors found:")
            for err in errors:
                print(f"  - {err}")
            return 1
        else:
            print("\n[OK] All checksums valid!")
            return 0


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="DASE Cache Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--root',
        default='./cache',
        help='Cache root directory (default: ./cache)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # ls command
    parser_ls = subparsers.add_parser('ls', help='List cache entries')
    parser_ls.add_argument('category', nargs='?', help='Category to list')

    # stats command
    parser_stats = subparsers.add_parser('stats', help='Show cache statistics')
    parser_stats.add_argument('category', nargs='?', help='Category to show stats for')

    # info command
    parser_info = subparsers.add_parser('info', help='Show entry details')
    parser_info.add_argument('category', help='Cache category')
    parser_info.add_argument('key', help='Entry key')

    # clear command
    parser_clear = subparsers.add_parser('clear', help='Clear cache entries')
    parser_clear.add_argument('category', help='Cache category')
    parser_clear.add_argument('key', nargs='?', help='Entry key (optional, clears category if omitted)')

    # validate command
    parser_validate = subparsers.add_parser('validate', help='Validate cache integrity')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = CacheCLI(cache_root=args.root)

    # Execute command
    try:
        if args.command == 'ls':
            return cli.cmd_ls(args.category)
        elif args.command == 'stats':
            return cli.cmd_stats(args.category)
        elif args.command == 'info':
            return cli.cmd_info(args.category, args.key)
        elif args.command == 'clear':
            return cli.cmd_clear(args.category, args.key)
        elif args.command == 'validate':
            return cli.cmd_validate()
        else:
            print(f"Unknown command: {args.command}")
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
