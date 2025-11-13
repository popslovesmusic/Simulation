"""
HelpfulError Exception System

Provides context-aware error messages with actionable suggestions for fixing issues.
Designed to improve user experience by making errors understandable and fixable.

Usage:
    from utils.helpful_errors import HelpfulError, ParameterError, FileError

    raise ParameterError(
        "num_nodes must be positive",
        parameter="num_nodes",
        got_value=-100,
        expected="positive integer",
        suggestion="Set num_nodes to a value like 1024, 4096, or 10000"
    )
"""

from typing import Optional, Dict, Any, List
import traceback
import sys


class HelpfulError(Exception):
    """
    Base class for context-aware errors with helpful suggestions.

    Attributes
    ----------
    message : str
        Main error message
    context : dict
        Additional context about the error
    suggestion : str or list of str
        Actionable suggestion(s) for fixing the error
    docs_link : str, optional
        Link to relevant documentation
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str | List[str]] = None,
        docs_link: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        self.message = message
        self.context = context or {}
        self.suggestion = suggestion if isinstance(suggestion, list) else ([suggestion] if suggestion else [])
        self.docs_link = docs_link
        self.cause = cause

        # Build full error message
        full_message = self._build_message()
        super().__init__(full_message)

    def _build_message(self) -> str:
        """Build formatted error message with context and suggestions."""
        lines = [
            "",
            "=" * 70,
            f"❌ {self.__class__.__name__}: {self.message}",
            "=" * 70,
        ]

        # Add context
        if self.context:
            lines.append("\n📋 Context:")
            for key, value in self.context.items():
                lines.append(f"  • {key}: {value}")

        # Add suggestions
        if self.suggestion:
            lines.append("\n💡 Suggested fix:")
            for i, sugg in enumerate(self.suggestion, 1):
                if len(self.suggestion) > 1:
                    lines.append(f"  {i}. {sugg}")
                else:
                    lines.append(f"  {sugg}")

        # Add documentation link
        if self.docs_link:
            lines.append(f"\n📚 Documentation: {self.docs_link}")

        # Add cause if available
        if self.cause:
            lines.append(f"\n⚠️  Caused by: {type(self.cause).__name__}: {str(self.cause)}")

        lines.append("=" * 70)
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary (useful for JSON serialization)."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "suggestions": self.suggestion,
            "docs_link": self.docs_link,
            "cause": str(self.cause) if self.cause else None,
        }


class ParameterError(HelpfulError):
    """Error for invalid parameters or configuration."""

    def __init__(
        self,
        message: str,
        parameter: Optional[str] = None,
        got_value: Any = None,
        expected: Optional[str] = None,
        suggestion: Optional[str | List[str]] = None,
        valid_range: Optional[str] = None,
        **kwargs
    ):
        context = {}
        if parameter:
            context["Parameter"] = parameter
        if got_value is not None:
            context["Got value"] = repr(got_value)
        if expected:
            context["Expected"] = expected
        if valid_range:
            context["Valid range"] = valid_range

        # Auto-generate suggestion if not provided
        if not suggestion and parameter and expected:
            suggestion = f"Set '{parameter}' to {expected}"

        super().__init__(
            message,
            context=context,
            suggestion=suggestion,
            docs_link="docs/user_guide/PARAMETERS.md",
            **kwargs
        )


class FileError(HelpfulError):
    """Error for file-related issues."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        suggestion: Optional[str | List[str]] = None,
        **kwargs
    ):
        context = {}
        if file_path:
            context["File path"] = file_path
        if operation:
            context["Operation"] = operation

        # Auto-generate suggestions
        if not suggestion:
            suggestions = []
            if operation == "read" and file_path:
                suggestions.append(f"Check that the file exists: {file_path}")
                suggestions.append("Verify you have read permissions")
            elif operation == "write" and file_path:
                suggestions.append(f"Check that the directory exists")
                suggestions.append("Verify you have write permissions")
                suggestions.append("Ensure disk space is available")
            suggestion = suggestions if suggestions else None

        super().__init__(
            message,
            context=context,
            suggestion=suggestion,
            docs_link="docs/user_guide/FILE_OPERATIONS.md",
            **kwargs
        )


class CacheError(HelpfulError):
    """Error for cache-related issues."""

    def __init__(
        self,
        message: str,
        cache_type: Optional[str] = None,
        cache_key: Optional[str] = None,
        suggestion: Optional[str | List[str]] = None,
        **kwargs
    ):
        context = {}
        if cache_type:
            context["Cache type"] = cache_type
        if cache_key:
            context["Cache key"] = cache_key

        # Auto-generate suggestions
        if not suggestion:
            suggestions = [
                "Try clearing the cache with --clear-cache flag",
                "Check cache directory permissions",
                "Verify disk space is available"
            ]
            suggestion = suggestions

        super().__init__(
            message,
            context=context,
            suggestion=suggestion,
            docs_link="docs/user_guide/CACHING.md",
            **kwargs
        )


class EngineError(HelpfulError):
    """Error for computation engine issues."""

    def __init__(
        self,
        message: str,
        engine_type: Optional[str] = None,
        operation: Optional[str] = None,
        suggestion: Optional[str | List[str]] = None,
        **kwargs
    ):
        context = {}
        if engine_type:
            context["Engine"] = engine_type
        if operation:
            context["Operation"] = operation

        super().__init__(
            message,
            context=context,
            suggestion=suggestion,
            docs_link="docs/technical/ENGINES.md",
            **kwargs
        )


class ValidationError(HelpfulError):
    """Error for validation failures."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        validator: Optional[str] = None,
        got_value: Any = None,
        suggestion: Optional[str | List[str]] = None,
        **kwargs
    ):
        context = {}
        if field:
            context["Field"] = field
        if validator:
            context["Validator"] = validator
        if got_value is not None:
            context["Got value"] = repr(got_value)

        super().__init__(
            message,
            context=context,
            suggestion=suggestion,
            docs_link="docs/user_guide/VALIDATION.md",
            **kwargs
        )


class MissionError(HelpfulError):
    """Error for mission planning/execution issues."""

    def __init__(
        self,
        message: str,
        mission_id: Optional[str] = None,
        phase: Optional[str] = None,
        suggestion: Optional[str | List[str]] = None,
        **kwargs
    ):
        context = {}
        if mission_id:
            context["Mission ID"] = mission_id
        if phase:
            context["Phase"] = phase

        super().__init__(
            message,
            context=context,
            suggestion=suggestion,
            docs_link="docs/user_guide/MISSIONS.md",
            **kwargs
        )


class DependencyError(HelpfulError):
    """Error for missing or incompatible dependencies."""

    def __init__(
        self,
        message: str,
        dependency: Optional[str] = None,
        required_version: Optional[str] = None,
        found_version: Optional[str] = None,
        suggestion: Optional[str | List[str]] = None,
        **kwargs
    ):
        context = {}
        if dependency:
            context["Dependency"] = dependency
        if required_version:
            context["Required version"] = required_version
        if found_version:
            context["Found version"] = found_version

        # Auto-generate suggestion
        if not suggestion and dependency:
            if not found_version:
                suggestion = f"Install the required package: pip install {dependency}"
            else:
                suggestion = f"Update the package: pip install --upgrade {dependency}"

        super().__init__(
            message,
            context=context,
            suggestion=suggestion,
            docs_link="docs/setup/INSTALLATION.md",
            **kwargs
        )


def format_exception_with_context(exc: Exception) -> str:
    """
    Format any exception with context and traceback.

    Useful for catching and re-formatting non-HelpfulError exceptions.
    """
    if isinstance(exc, HelpfulError):
        return str(exc)

    lines = [
        "",
        "=" * 70,
        f"❌ {type(exc).__name__}: {str(exc)}",
        "=" * 70,
        "\n📍 Traceback (most recent call last):",
    ]

    # Get traceback
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    lines.extend(["  " + line.rstrip() for line in tb_lines])

    lines.append("=" * 70)
    return "\n".join(lines)


def suggest_common_fixes(exc: Exception) -> List[str]:
    """
    Suggest common fixes based on exception type.

    Returns
    -------
    list of str
        Suggested fixes
    """
    suggestions = []

    if isinstance(exc, FileNotFoundError):
        suggestions.append("Check that the file path is correct")
        suggestions.append("Ensure the file exists before trying to read it")

    elif isinstance(exc, PermissionError):
        suggestions.append("Check file/directory permissions")
        suggestions.append("Try running with appropriate permissions")

    elif isinstance(exc, KeyError):
        suggestions.append("Check that the key exists in the dictionary")
        suggestions.append("Use .get() method with a default value")

    elif isinstance(exc, ValueError):
        suggestions.append("Verify input values are in the expected format")
        suggestions.append("Check parameter ranges and constraints")

    elif isinstance(exc, ImportError):
        suggestions.append("Install missing dependencies: pip install -r requirements.txt")
        suggestions.append("Check that the module name is spelled correctly")

    elif isinstance(exc, AttributeError):
        suggestions.append("Verify the object has the expected attribute")
        suggestions.append("Check for typos in attribute names")

    elif isinstance(exc, TypeError):
        suggestions.append("Check that arguments have the correct type")
        suggestions.append("Verify function signature matches the call")

    elif isinstance(exc, IndexError):
        suggestions.append("Check array/list bounds")
        suggestions.append("Ensure index is within valid range")

    elif isinstance(exc, ZeroDivisionError):
        suggestions.append("Add a check to avoid division by zero")
        suggestions.append("Ensure denominator is non-zero before dividing")

    return suggestions


class ErrorContext:
    """
    Context manager for adding helpful error context.

    Usage:
        with ErrorContext("Loading mission file", file_path="mission.json"):
            # ... code that might raise exceptions
    """

    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Wrap exception with helpful context
            if isinstance(exc_val, HelpfulError):
                # Already helpful, just re-raise
                return False

            # Create helpful error from generic exception
            suggestions = suggest_common_fixes(exc_val)

            helpful_exc = HelpfulError(
                f"Error during {self.operation}: {str(exc_val)}",
                context=self.context,
                suggestion=suggestions,
                cause=exc_val
            )

            # Replace exception with helpful version
            raise helpful_exc from exc_val

        return False


# Convenience function for CLI tools
def print_error(error: Exception, verbose: bool = False) -> None:
    """
    Print error in a user-friendly format.

    Parameters
    ----------
    error : Exception
        The error to print
    verbose : bool
        If True, include full traceback
    """
    if isinstance(error, HelpfulError):
        print(str(error), file=sys.stderr)
    else:
        print(format_exception_with_context(error), file=sys.stderr)

    if verbose and not isinstance(error, HelpfulError):
        print("\n📍 Full traceback:", file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


# Example usage
if __name__ == "__main__":
    # Example 1: Parameter error
    try:
        raise ParameterError(
            "num_nodes must be positive",
            parameter="num_nodes",
            got_value=-100,
            expected="positive integer",
            valid_range="1 to 1,000,000",
            suggestion="Try using num_nodes=1024 or num_nodes=4096"
        )
    except HelpfulError as e:
        print(e)

    print("\n" + "=" * 70 + "\n")

    # Example 2: File error
    try:
        raise FileError(
            "Could not read mission file",
            file_path="/path/to/mission.json",
            operation="read",
            cause=FileNotFoundError("No such file")
        )
    except HelpfulError as e:
        print(e)

    print("\n" + "=" * 70 + "\n")

    # Example 3: Using ErrorContext
    try:
        with ErrorContext("Loading configuration", config_file="config.yaml"):
            # Simulate an error
            raise ValueError("Invalid YAML format")
    except HelpfulError as e:
        print(e)
