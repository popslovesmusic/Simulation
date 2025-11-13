"""
Progress Tracking Utilities

Provides consistent progress indicators for long-running operations.
Uses rich library for beautiful terminal progress bars.

Usage:
    from utils.progress import ProgressTracker, progress_context

    # Method 1: Context manager
    with progress_context("Processing files", total=100) as progress:
        for i in range(100):
            # Do work
            progress.update(1)

    # Method 2: Manual tracking
    tracker = ProgressTracker("Training model")
    tracker.start()
    for epoch in range(10):
        tracker.update(1, description=f"Epoch {epoch+1}/10")
    tracker.finish()
"""

from typing import Optional, Callable, Any, Dict
import time
from contextlib import contextmanager
from dataclasses import dataclass

try:
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TimeRemainingColumn,
        TimeElapsedColumn,
        TaskProgressColumn,
    )
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich library not available. Progress bars will be text-only.")


@dataclass
class ProgressStats:
    """Statistics for a progress tracker."""
    total: int
    completed: int
    elapsed_time: float
    estimated_remaining: float
    percentage: float
    rate: float  # items per second


class ProgressTracker:
    """
    Track progress of long-running operations.

    Features:
    - Rich terminal progress bars (if rich is available)
    - Fallback to simple text output
    - Estimated time remaining
    - Rate calculation
    """

    def __init__(
        self,
        description: str,
        total: Optional[int] = None,
        unit: str = "items",
        show_percentage: bool = True,
        show_rate: bool = True,
        show_eta: bool = True,
    ):
        """
        Initialize progress tracker.

        Parameters
        ----------
        description : str
            Description of the operation
        total : int, optional
            Total number of items to process
        unit : str
            Unit name (e.g., "files", "epochs", "steps")
        show_percentage : bool
            Show percentage complete
        show_rate : bool
            Show processing rate
        show_eta : bool
            Show estimated time remaining
        """
        self.description = description
        self.total = total
        self.unit = unit
        self.show_percentage = show_percentage
        self.show_rate = show_rate
        self.show_eta = show_eta

        self.completed = 0
        self.start_time: Optional[float] = None
        self.last_update_time: Optional[float] = None

        # Rich progress bar (if available)
        self.progress: Optional[Any] = None
        self.task_id: Optional[Any] = None
        self.console: Optional[Console] = None

        # For text-only fallback
        self.last_print_time: float = 0.0
        self.print_interval: float = 0.5  # seconds

    def start(self) -> 'ProgressTracker':
        """Start tracking progress."""
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.completed = 0

        if RICH_AVAILABLE:
            # Create rich progress bar
            columns = [
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
            ]

            if self.total is not None:
                columns.extend([
                    BarColumn(),
                    TaskProgressColumn(),
                ])

                if self.show_eta:
                    columns.append(TimeRemainingColumn())

            columns.append(TimeElapsedColumn())

            self.progress = Progress(*columns)
            self.progress.start()
            self.task_id = self.progress.add_task(
                self.description,
                total=self.total,
            )
        else:
            # Fallback to simple text
            self._print_progress()

        return self

    def update(
        self,
        advance: int = 1,
        description: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Update progress.

        Parameters
        ----------
        advance : int
            Number of items completed
        description : str, optional
            Update description
        **kwargs
            Additional fields to update
        """
        if self.start_time is None:
            raise RuntimeError("Progress tracker not started. Call start() first.")

        self.completed += advance
        self.last_update_time = time.time()

        if RICH_AVAILABLE and self.progress is not None:
            # Update rich progress bar
            if description:
                self.progress.update(
                    self.task_id,
                    advance=advance,
                    description=description,
                    **kwargs
                )
            else:
                self.progress.update(self.task_id, advance=advance, **kwargs)
        else:
            # Fallback: print occasionally
            current_time = time.time()
            if current_time - self.last_print_time >= self.print_interval:
                self._print_progress(description)
                self.last_print_time = current_time

    def finish(self, message: Optional[str] = None) -> None:
        """
        Finish tracking progress.

        Parameters
        ----------
        message : str, optional
            Final completion message
        """
        if RICH_AVAILABLE and self.progress is not None:
            self.progress.stop()

        # Print completion message
        elapsed = time.time() - self.start_time if self.start_time else 0
        if message:
            print(f"✓ {message} (completed in {elapsed:.2f}s)")
        else:
            print(f"✓ {self.description} completed in {elapsed:.2f}s")

    def get_stats(self) -> ProgressStats:
        """Get current progress statistics."""
        if self.start_time is None:
            raise RuntimeError("Progress tracker not started.")

        elapsed = time.time() - self.start_time
        rate = self.completed / elapsed if elapsed > 0 else 0.0

        if self.total is not None and rate > 0:
            remaining_items = self.total - self.completed
            estimated_remaining = remaining_items / rate
            percentage = (self.completed / self.total) * 100
        else:
            estimated_remaining = 0.0
            percentage = 0.0

        return ProgressStats(
            total=self.total or 0,
            completed=self.completed,
            elapsed_time=elapsed,
            estimated_remaining=estimated_remaining,
            percentage=percentage,
            rate=rate,
        )

    def _print_progress(self, description: Optional[str] = None) -> None:
        """Print progress in text format (fallback)."""
        desc = description or self.description
        stats = self.get_stats()

        if self.total is not None:
            # Deterministic progress
            bar_width = 30
            filled = int((self.completed / self.total) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            print(
                f"\r{desc}: [{bar}] {self.completed}/{self.total} "
                f"({stats.percentage:.1f}%) "
                f"[{stats.rate:.1f} {self.unit}/s, "
                f"ETA: {stats.estimated_remaining:.1f}s]",
                end="",
                flush=True
            )
        else:
            # Indeterminate progress
            print(
                f"\r{desc}: {self.completed} {self.unit} "
                f"[{stats.rate:.1f} {self.unit}/s, {stats.elapsed_time:.1f}s elapsed]",
                end="",
                flush=True
            )

    def __enter__(self) -> 'ProgressTracker':
        """Context manager entry."""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.finish()
        else:
            # Error occurred
            if RICH_AVAILABLE and self.progress is not None:
                self.progress.stop()
            print(f"\n❌ {self.description} failed")
        return False


@contextmanager
def progress_context(
    description: str,
    total: Optional[int] = None,
    **kwargs
):
    """
    Context manager for progress tracking.

    Usage:
        with progress_context("Processing", total=100) as progress:
            for i in range(100):
                # do work
                progress.update(1)
    """
    tracker = ProgressTracker(description, total=total, **kwargs)
    yield tracker.start()
    tracker.finish()


class MultiProgressTracker:
    """
    Track multiple concurrent progress operations.

    Useful for pipelines or parallel tasks.
    """

    def __init__(self):
        self.trackers: Dict[str, ProgressTracker] = {}
        self.progress: Optional[Any] = None

        if RICH_AVAILABLE:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                TimeElapsedColumn(),
            )

    def add_task(
        self,
        name: str,
        description: str,
        total: Optional[int] = None,
    ) -> str:
        """
        Add a new task to track.

        Returns
        -------
        str
            Task name (for updating)
        """
        tracker = ProgressTracker(description, total=total)
        self.trackers[name] = tracker

        if RICH_AVAILABLE and self.progress is not None:
            # Add to shared progress display
            tracker.task_id = self.progress.add_task(description, total=total)

        return name

    def update(self, name: str, advance: int = 1, **kwargs) -> None:
        """Update a specific task."""
        if name not in self.trackers:
            raise KeyError(f"Task '{name}' not found")

        tracker = self.trackers[name]
        tracker.completed += advance

        if RICH_AVAILABLE and self.progress is not None:
            self.progress.update(tracker.task_id, advance=advance, **kwargs)

    def start(self) -> 'MultiProgressTracker':
        """Start all tracking."""
        if RICH_AVAILABLE and self.progress is not None:
            self.progress.start()

        for tracker in self.trackers.values():
            tracker.start_time = time.time()

        return self

    def finish(self) -> None:
        """Finish all tracking."""
        if RICH_AVAILABLE and self.progress is not None:
            self.progress.stop()

        print("✓ All tasks completed")

    def __enter__(self) -> 'MultiProgressTracker':
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()
        return False


def track_function(
    description: Optional[str] = None,
    unit: str = "calls",
):
    """
    Decorator to track function execution with progress.

    Usage:
        @track_function("Processing files")
        def process_file(file_path):
            # ... do work
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            func_desc = description or f"Executing {func.__name__}"

            with progress_context(func_desc, unit=unit) as progress:
                result = func(*args, **kwargs)
                progress.update(1)
                return result

        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    import random

    # Example 1: Simple progress bar
    print("Example 1: Simple progress bar")
    with progress_context("Processing files", total=50) as progress:
        for i in range(50):
            time.sleep(0.05)  # Simulate work
            progress.update(1)

    print("\n" + "=" * 70 + "\n")

    # Example 2: Indeterminate progress
    print("Example 2: Indeterminate progress")
    with progress_context("Searching for files") as progress:
        for i in range(30):
            time.sleep(0.05)
            progress.update(1)

    print("\n" + "=" * 70 + "\n")

    # Example 3: Multi-task progress
    print("Example 3: Multi-task progress")
    with MultiProgressTracker() as multi:
        multi.add_task("download", "Downloading data", total=100)
        multi.add_task("process", "Processing data", total=100)
        multi.add_task("save", "Saving results", total=100)

        for i in range(100):
            time.sleep(0.02)
            multi.update("download", advance=1)
            if i >= 20:
                multi.update("process", advance=1)
            if i >= 50:
                multi.update("save", advance=1)

    print("\n" + "=" * 70 + "\n")

    # Example 4: Function decorator
    @track_function("Processing batch")
    def process_batch(size):
        time.sleep(0.5)
        return f"Processed {size} items"

    result = process_batch(1000)
    print(result)
