"""Static analysis automation for cache system code quality.

This module automates code quality checks:
- Code metrics (LOC, complexity)
- Static analysis scanning
- Documentation coverage
- Technical debt tracking

Usage:
    from backend.cache.static_analysis import StaticAnalyzer

    analyzer = StaticAnalyzer()
    report = analyzer.run_analysis()
"""

import sys
from pathlib import Path
import json
import ast
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class CodeMetrics:
    """Code metrics for a module."""

    module_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    num_functions: int
    num_classes: int
    avg_function_length: float
    max_function_length: int
    docstring_coverage: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AnalysisReport:
    """Static analysis report."""

    timestamp: str
    total_files: int
    total_lines: int
    total_code_lines: int
    total_functions: int
    total_classes: int
    avg_docstring_coverage: float
    modules: List[CodeMetrics] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "total_code_lines": self.total_code_lines,
            "total_functions": self.total_functions,
            "total_classes": self.total_classes,
            "avg_docstring_coverage": self.avg_docstring_coverage,
            "modules": [m.to_dict() for m in self.modules],
            "issues": self.issues,
            "recommendations": self.recommendations
        }

    def save(self, output_path: Path):
        """Save report to JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class StaticAnalyzer:
    """Automates static analysis and code quality checks.

    Example:
        >>> analyzer = StaticAnalyzer()
        >>>
        >>> # Run full analysis
        >>> report = analyzer.run_analysis()
        >>>
        >>> # Check specific module
        >>> metrics = analyzer.analyze_module("backend/cache/cache_manager.py")
    """

    def __init__(
        self,
        project_root: str = ".",
        target_dirs: Optional[List[str]] = None
    ):
        """Initialize static analyzer.

        Args:
            project_root: Root directory of project
            target_dirs: Directories to analyze (None = cache modules only)
        """
        self.project_root = Path(project_root)

        if target_dirs:
            self.target_dirs = [Path(d) for d in target_dirs]
        else:
            self.target_dirs = [
                self.project_root / "backend" / "cache"
            ]

    def _count_lines(self, filepath: Path) -> Tuple[int, int, int, int]:
        """Count lines in file.

        Returns:
            (total_lines, code_lines, comment_lines, blank_lines)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            return (0, 0, 0, 0)

        total = len(lines)
        blank = 0
        comment = 0
        code = 0

        in_multiline_string = False
        multiline_quote = None

        for line in lines:
            stripped = line.strip()

            # Check for blank line
            if not stripped:
                blank += 1
                continue

            # Check for multiline string start/end
            if '"""' in line or "'''" in line:
                if '"""' in line:
                    quote = '"""'
                else:
                    quote = "'''"

                if not in_multiline_string:
                    in_multiline_string = True
                    multiline_quote = quote
                    comment += 1
                elif quote == multiline_quote:
                    in_multiline_string = False
                    multiline_quote = None
                    comment += 1
                continue

            # Inside multiline string
            if in_multiline_string:
                comment += 1
                continue

            # Single-line comment
            if stripped.startswith('#'):
                comment += 1
                continue

            # Code line
            code += 1

        return (total, code, comment, blank)

    def _analyze_ast(self, filepath: Path) -> Tuple[int, int, float, int]:
        """Analyze Python AST.

        Returns:
            (num_functions, num_classes, docstring_coverage, max_function_length)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception:
            return (0, 0, 0.0, 0)

        num_functions = 0
        num_classes = 0
        functions_with_docs = 0
        classes_with_docs = 0
        function_lengths = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                num_functions += 1

                # Check for docstring
                if (node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    functions_with_docs += 1

                # Get function length
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    length = node.end_lineno - node.lineno + 1
                    function_lengths.append(length)

            elif isinstance(node, ast.ClassDef):
                num_classes += 1

                # Check for docstring
                if (node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    classes_with_docs += 1

        # Calculate docstring coverage
        total_items = num_functions + num_classes
        documented_items = functions_with_docs + classes_with_docs
        docstring_coverage = documented_items / total_items if total_items > 0 else 1.0

        max_func_length = max(function_lengths) if function_lengths else 0

        return (num_functions, num_classes, docstring_coverage, max_func_length)

    def analyze_module(self, module_path: str) -> CodeMetrics:
        """Analyze single module.

        Args:
            module_path: Path to Python module

        Returns:
            Code metrics for module
        """
        filepath = Path(module_path)

        # Count lines
        total_lines, code_lines, comment_lines, blank_lines = self._count_lines(filepath)

        # Analyze AST
        num_functions, num_classes, docstring_coverage, max_func_length = self._analyze_ast(filepath)

        avg_func_length = code_lines / num_functions if num_functions > 0 else 0.0

        return CodeMetrics(
            module_path=str(filepath),
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            num_functions=num_functions,
            num_classes=num_classes,
            avg_function_length=avg_func_length,
            max_function_length=max_func_length,
            docstring_coverage=docstring_coverage
        )

    def run_analysis(self) -> AnalysisReport:
        """Run full static analysis.

        Returns:
            Analysis report
        """
        timestamp = datetime.utcnow().isoformat() + "Z"

        modules: List[CodeMetrics] = []
        issues: List[str] = []
        recommendations: List[str] = []

        # Find all Python files in target directories
        py_files = []
        for target_dir in self.target_dirs:
            if target_dir.exists():
                py_files.extend(target_dir.rglob("*.py"))

        # Analyze each file
        for py_file in py_files:
            # Skip test files for now (they have different standards)
            if "test_" in py_file.name:
                continue

            try:
                metrics = self.analyze_module(str(py_file))
                modules.append(metrics)

                # Check for issues
                if metrics.docstring_coverage < 0.5:
                    issues.append(f"{py_file.name}: Low docstring coverage ({metrics.docstring_coverage:.0%})")

                if metrics.max_function_length > 200:
                    issues.append(f"{py_file.name}: Very long function ({metrics.max_function_length} lines)")

                if metrics.code_lines > 1000:
                    recommendations.append(f"{py_file.name}: Large module ({metrics.code_lines} LOC) - consider splitting")

            except Exception as e:
                issues.append(f"{py_file.name}: Analysis failed - {e}")

        # Aggregate statistics
        total_files = len(modules)
        total_lines = sum(m.total_lines for m in modules)
        total_code_lines = sum(m.code_lines for m in modules)
        total_functions = sum(m.num_functions for m in modules)
        total_classes = sum(m.num_classes for m in modules)
        avg_docstring_coverage = (sum(m.docstring_coverage for m in modules) / total_files
                                 if total_files > 0 else 0.0)

        # Generate recommendations
        if avg_docstring_coverage < 0.7:
            recommendations.append("Overall docstring coverage is low - add more documentation")

        if total_code_lines > 10000:
            recommendations.append("Project is getting large - consider modularization")

        report = AnalysisReport(
            timestamp=timestamp,
            total_files=total_files,
            total_lines=total_lines,
            total_code_lines=total_code_lines,
            total_functions=total_functions,
            total_classes=total_classes,
            avg_docstring_coverage=avg_docstring_coverage,
            modules=modules,
            issues=issues,
            recommendations=recommendations
        )

        return report

    def generate_metrics_summary(self) -> Dict[str, Any]:
        """Generate quick metrics summary.

        Returns:
            Metrics summary dict
        """
        report = self.run_analysis()

        return {
            "total_files": report.total_files,
            "total_lines": report.total_lines,
            "total_code_lines": report.total_code_lines,
            "total_functions": report.total_functions,
            "total_classes": report.total_classes,
            "avg_docstring_coverage": f"{report.avg_docstring_coverage:.1%}",
            "num_issues": len(report.issues),
            "num_recommendations": len(report.recommendations)
        }


__all__ = ["StaticAnalyzer", "CodeMetrics", "AnalysisReport"]
