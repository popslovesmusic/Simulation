"""Governance & Growth Agent for DASE cache system.

This module automates self-maintenance of the cache infrastructure:
- Cache health monitoring and alerting
- Automated warmup scheduling
- Benchmark validation runs
- Growth predictions and recommendations

Features:
- Track cache sizes, hit rates, staleness
- Detect invalidation needs
- Schedule periodic maintenance
- Generate governance reports

Usage:
    from backend.cache.governance_agent import CacheGovernanceAgent

    agent = CacheGovernanceAgent()
    report = agent.generate_health_report()
    agent.run_maintenance()
"""

import sys
from pathlib import Path
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import CacheManager


@dataclass
class CacheHealthMetrics:
    """Health metrics for a cache category."""

    category: str
    total_entries: int
    total_size_mb: float
    avg_entry_size_kb: float
    hit_rate: float
    total_hits: int
    total_misses: int
    oldest_entry_age_days: float
    newest_entry_age_days: float
    stale_entries: int
    stale_threshold_days: int = 30
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def is_healthy(self) -> bool:
        """Check if cache category is healthy."""
        # Health criteria
        if self.total_entries == 0:
            return True  # Empty is fine

        issues = []

        # Check hit rate (should be > 10% if entries exist)
        if self.hit_rate < 0.1 and self.total_hits + self.total_misses > 10:
            issues.append("Low hit rate")

        # Check staleness (> 50% stale is concerning)
        if self.total_entries > 0 and self.stale_entries / self.total_entries > 0.5:
            issues.append("High staleness")

        # Check size (> 1GB per category might need attention)
        if self.total_size_mb > 1024:
            issues.append("Large size")

        return len(issues) == 0


@dataclass
class GovernanceReport:
    """Overall governance report."""

    timestamp: str
    cache_root: str
    categories: Dict[str, CacheHealthMetrics]
    total_size_mb: float
    total_entries: int
    overall_hit_rate: float
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "cache_root": self.cache_root,
            "categories": {cat: metrics.to_dict() for cat, metrics in self.categories.items()},
            "total_size_mb": self.total_size_mb,
            "total_entries": self.total_entries,
            "overall_hit_rate": self.overall_hit_rate,
            "recommendations": self.recommendations,
            "warnings": self.warnings
        }

    def save(self, output_path: Path):
        """Save report to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class CacheGovernanceAgent:
    """Automates cache system governance and maintenance.

    Example:
        >>> agent = CacheGovernanceAgent()
        >>>
        >>> # Generate health report
        >>> report = agent.generate_health_report()
        >>> print(f"Total cache size: {report.total_size_mb:.2f} MB")
        >>> print(f"Overall hit rate: {report.overall_hit_rate:.1%}")
        >>>
        >>> # Run maintenance
        >>> actions = agent.run_maintenance()
        >>>
        >>> # Check if warmup needed
        >>> if agent.needs_warmup():
        ...     agent.run_warmup()
    """

    def __init__(
        self,
        cache_root: str = "./cache",
        stale_threshold_days: int = 30,
        size_warning_mb: float = 500.0,
        min_hit_rate: float = 0.1
    ):
        """Initialize governance agent.

        Args:
            cache_root: Path to cache root directory
            stale_threshold_days: Days before entry considered stale
            size_warning_mb: Size threshold for warnings (MB)
            min_hit_rate: Minimum acceptable hit rate
        """
        self.cache_root = Path(cache_root)
        self.cache = CacheManager(root=cache_root)
        self.stale_threshold_days = stale_threshold_days
        self.size_warning_mb = size_warning_mb
        self.min_hit_rate = min_hit_rate

        # Track maintenance history
        self.history_path = self.cache_root / "governance_history.json"
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load governance history."""
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        """Save governance history."""
        try:
            with open(self.history_path, 'w') as f:
                json.dump(self.history[-100:], f, indent=2)  # Keep last 100 entries
        except Exception as e:
            print(f"Warning: Failed to save governance history: {e}")

    def _compute_category_metrics(
        self,
        category: str
    ) -> Optional[CacheHealthMetrics]:
        """Compute health metrics for a category.

        Args:
            category: Cache category name

        Returns:
            Health metrics or None if category doesn't exist
        """
        category_path = self.cache_root / category
        if not category_path.exists():
            return None

        # Load metadata
        metadata_path = category_path / ".metadata.json"
        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except Exception:
            return None

        entries = metadata.get("entries", {})
        if not entries:
            return CacheHealthMetrics(
                category=category,
                total_entries=0,
                total_size_mb=0.0,
                avg_entry_size_kb=0.0,
                hit_rate=0.0,
                total_hits=0,
                total_misses=0,
                oldest_entry_age_days=0.0,
                newest_entry_age_days=0.0,
                stale_entries=0,
                stale_threshold_days=self.stale_threshold_days
            )

        # Compute metrics
        total_size = sum(entry.get("size_bytes", 0) for entry in entries.values())
        total_hits = sum(entry.get("access_count", 0) for entry in entries.values())
        total_misses = metadata.get("stats", {}).get("misses", 0)

        hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0.0

        # Compute age statistics
        now = datetime.utcnow()
        ages = []
        stale_count = 0

        for entry in entries.values():
            created = datetime.fromisoformat(entry.get("created", now.isoformat()).replace("Z", ""))
            age_days = (now - created).total_seconds() / 86400
            ages.append(age_days)

            if age_days > self.stale_threshold_days:
                stale_count += 1

        return CacheHealthMetrics(
            category=category,
            total_entries=len(entries),
            total_size_mb=total_size / (1024 * 1024),
            avg_entry_size_kb=(total_size / len(entries)) / 1024 if entries else 0.0,
            hit_rate=hit_rate,
            total_hits=total_hits,
            total_misses=total_misses,
            oldest_entry_age_days=max(ages) if ages else 0.0,
            newest_entry_age_days=min(ages) if ages else 0.0,
            stale_entries=stale_count,
            stale_threshold_days=self.stale_threshold_days
        )

    def generate_health_report(self) -> GovernanceReport:
        """Generate comprehensive health report.

        Returns:
            Governance report with metrics and recommendations
        """
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Get all categories
        categories = {}
        total_size = 0.0
        total_entries = 0
        total_hits = 0
        total_misses = 0

        for category_path in self.cache_root.iterdir():
            if category_path.is_dir() and not category_path.name.startswith('.'):
                category = category_path.name
                metrics = self._compute_category_metrics(category)

                if metrics:
                    categories[category] = metrics
                    total_size += metrics.total_size_mb
                    total_entries += metrics.total_entries
                    total_hits += metrics.total_hits
                    total_misses += metrics.total_misses

        overall_hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0.0

        # Generate recommendations and warnings
        recommendations = []
        warnings = []

        # Check overall size
        if total_size > self.size_warning_mb:
            warnings.append(f"Total cache size ({total_size:.1f} MB) exceeds threshold ({self.size_warning_mb} MB)")
            recommendations.append("Consider clearing stale entries or archiving old data")

        # Check overall hit rate
        if overall_hit_rate < self.min_hit_rate and (total_hits + total_misses) > 20:
            warnings.append(f"Low overall hit rate: {overall_hit_rate:.1%}")
            recommendations.append("Run warmup to populate cache with commonly used data")

        # Check individual categories
        for category, metrics in categories.items():
            if not metrics.is_healthy():
                warnings.append(f"Category '{category}' has health issues")

                if metrics.hit_rate < self.min_hit_rate and metrics.total_hits + metrics.total_misses > 10:
                    recommendations.append(f"Low hit rate in '{category}' - consider warmup")

                if metrics.stale_entries > metrics.total_entries * 0.5:
                    recommendations.append(f"High staleness in '{category}' - consider cleanup")

        # Check if warmup needed
        if total_entries == 0:
            recommendations.append("Cache is empty - run initial warmup")

        report = GovernanceReport(
            timestamp=timestamp,
            cache_root=str(self.cache_root),
            categories=categories,
            total_size_mb=total_size,
            total_entries=total_entries,
            overall_hit_rate=overall_hit_rate,
            recommendations=recommendations,
            warnings=warnings
        )

        # Add to history
        self.history.append({
            "timestamp": timestamp,
            "total_size_mb": total_size,
            "total_entries": total_entries,
            "hit_rate": overall_hit_rate,
            "num_warnings": len(warnings)
        })
        self._save_history()

        return report

    def needs_warmup(self) -> bool:
        """Check if cache needs warmup.

        Returns:
            True if warmup recommended
        """
        report = self.generate_health_report()

        # Warmup needed if:
        # 1. Cache is empty
        # 2. Hit rate is very low
        # 3. Very few entries

        if report.total_entries == 0:
            return True

        if report.overall_hit_rate < 0.05 and (report.total_entries < 20):
            return True

        return False

    def run_warmup(self) -> Dict[str, Any]:
        """Run cache warmup process.

        Returns:
            Warmup results
        """
        print("Running cache warmup...")

        from backend.cache.warmup import main as warmup_main

        try:
            # Run warmup
            warmup_main()

            # Generate post-warmup report
            report = self.generate_health_report()

            return {
                "status": "success",
                "entries_created": report.total_entries,
                "cache_size_mb": report.total_size_mb,
                "timestamp": report.timestamp
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

    def cleanup_stale_entries(
        self,
        category: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Remove stale cache entries.

        Args:
            category: Specific category to clean (None = all)
            dry_run: If True, only report what would be deleted

        Returns:
            Cleanup results
        """
        report = self.generate_health_report()

        categories_to_clean = [category] if category else report.categories.keys()

        removed_count = 0
        freed_mb = 0.0

        for cat in categories_to_clean:
            metrics = report.categories.get(cat)
            if not metrics or metrics.stale_entries == 0:
                continue

            # Load metadata
            metadata_path = self.cache_root / cat / ".metadata.json"
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except Exception:
                continue

            entries = metadata.get("entries", {})
            now = datetime.utcnow()

            # Find stale entries
            stale_keys = []
            for key, entry in entries.items():
                created = datetime.fromisoformat(entry.get("created", now.isoformat()).replace("Z", ""))
                age_days = (now - created).total_seconds() / 86400

                if age_days > self.stale_threshold_days:
                    stale_keys.append(key)
                    freed_mb += entry.get("size_bytes", 0) / (1024 * 1024)

            # Remove entries
            if not dry_run:
                for key in stale_keys:
                    try:
                        self.cache.delete(cat, key)
                        removed_count += 1
                    except Exception as e:
                        print(f"Warning: Failed to delete {cat}/{key}: {e}")

        return {
            "removed_count": removed_count,
            "freed_mb": freed_mb,
            "dry_run": dry_run,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def run_maintenance(
        self,
        cleanup_stale: bool = True,
        warmup_if_needed: bool = True
    ) -> Dict[str, Any]:
        """Run automated maintenance tasks.

        Args:
            cleanup_stale: If True, remove stale entries
            warmup_if_needed: If True, run warmup if needed

        Returns:
            Maintenance results
        """
        results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actions_taken": []
        }

        # Generate initial report
        report = self.generate_health_report()
        results["initial_state"] = {
            "entries": report.total_entries,
            "size_mb": report.total_size_mb,
            "hit_rate": report.overall_hit_rate
        }

        # Cleanup stale entries
        if cleanup_stale:
            any_stale = any(m.stale_entries > 0 for m in report.categories.values())
            if any_stale:
                cleanup_result = self.cleanup_stale_entries()
                results["actions_taken"].append({
                    "action": "cleanup_stale",
                    "result": cleanup_result
                })

        # Warmup if needed
        if warmup_if_needed and self.needs_warmup():
            warmup_result = self.run_warmup()
            results["actions_taken"].append({
                "action": "warmup",
                "result": warmup_result
            })

        # Generate final report
        final_report = self.generate_health_report()
        results["final_state"] = {
            "entries": final_report.total_entries,
            "size_mb": final_report.total_size_mb,
            "hit_rate": final_report.overall_hit_rate
        }

        return results

    def predict_growth(
        self,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """Predict cache growth based on history.

        Args:
            days_ahead: Number of days to predict

        Returns:
            Growth predictions
        """
        if len(self.history) < 2:
            return {
                "error": "Insufficient history for prediction",
                "min_history_needed": 2,
                "current_history": len(self.history)
            }

        # Extract time series
        timestamps = [datetime.fromisoformat(h["timestamp"].replace("Z", "")) for h in self.history]
        sizes = [h["total_size_mb"] for h in self.history]
        entries = [h["total_entries"] for h in self.history]

        # Simple linear regression
        x = np.array([(t - timestamps[0]).total_seconds() / 86400 for t in timestamps])
        y_size = np.array(sizes)
        y_entries = np.array(entries)

        # Fit linear model
        size_slope = np.polyfit(x, y_size, 1)[0] if len(x) > 1 else 0.0
        entry_slope = np.polyfit(x, y_entries, 1)[0] if len(x) > 1 else 0.0

        # Predict
        current_size = sizes[-1]
        current_entries = entries[-1]

        predicted_size = current_size + size_slope * days_ahead
        predicted_entries = int(current_entries + entry_slope * days_ahead)

        return {
            "current": {
                "size_mb": current_size,
                "entries": current_entries
            },
            "predicted": {
                "size_mb": max(0, predicted_size),
                "entries": max(0, predicted_entries),
                "days_ahead": days_ahead
            },
            "growth_rate": {
                "size_mb_per_day": size_slope,
                "entries_per_day": entry_slope
            }
        }


__all__ = ["CacheGovernanceAgent", "GovernanceReport", "CacheHealthMetrics"]
