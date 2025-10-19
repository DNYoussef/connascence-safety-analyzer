"""
Detector Result Data Structures

Provides dataclasses and types for detector results, analysis context, and
metadata. This module consolidates result structures that were previously
duplicated across multiple detector implementations.

NASA Rule 4 Compliant: All functions under 60 lines
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from fixes.phase0.production_safe_assertions import ProductionAssert


@dataclass
class DetectorResult:
    """
    Result of running a connascence detector on a file.

    Contains violations found, metadata about the analysis, and optional
    performance metrics.
    """

    file_path: str
    violations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate required fields."""
        ProductionAssert.not_none(self.file_path, 'file_path')

        # Ensure violations is a list
        if not isinstance(self.violations, list):
            raise TypeError("violations must be a list")

    @property
    def violation_count(self) -> int:
        """Get total number of violations."""
        return len(self.violations)

    @property
    def has_errors(self) -> bool:
        """Check if analysis had errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if analysis had warnings."""
        return len(self.warnings) > 0

    def add_violation(self, violation: Dict[str, Any]) -> None:
        """
        Add a violation to the result.

        Args:
            violation: Violation dict from ViolationFactory

        NASA Rule 5: Input assertion
        """
        ProductionAssert.not_none(violation, 'violation')

        self.violations.append(violation)

    def add_error(self, error: str) -> None:
        """
        Add an error message to the result.

        Args:
            error: Error message

        NASA Rule 5: Input assertion
        """
        ProductionAssert.not_none(error, 'error')

        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """
        Add a warning message to the result.

        Args:
            warning: Warning message

        NASA Rule 5: Input assertion
        """
        ProductionAssert.not_none(warning, 'warning')

        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary.

        Returns:
            Dict representation of DetectorResult
        """
        return {
            "file_path": self.file_path,
            "violations": self.violations,
            "violation_count": self.violation_count,
            "metadata": self.metadata,
            "errors": self.errors,
            "warnings": self.warnings,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings
        }


@dataclass
class AnalysisContext:
    """
    Context information for detector analysis.

    Provides file path, source lines, and optional configuration to detectors
    during analysis.
    """

    file_path: str
    source_lines: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields."""
        ProductionAssert.not_none(self.file_path, 'file_path')

        # Ensure source_lines is a list
        if not isinstance(self.source_lines, list):
            raise TypeError("source_lines must be a list")

    @property
    def line_count(self) -> int:
        """Get total number of source lines."""
        return len(self.source_lines)

    def get_line(self, line_number: int) -> Optional[str]:
        """
        Get a specific line from source code (1-indexed).

        Args:
            line_number: Line number (1-indexed)

        Returns:
            Line content or None if out of range

        NASA Rule 4: Under 60 lines
        """
        if line_number < 1 or line_number > len(self.source_lines):
            return None

        return self.source_lines[line_number - 1]

    def get_lines(self, start_line: int, end_line: int) -> List[str]:
        """
        Get a range of lines from source code (1-indexed, inclusive).

        Args:
            start_line: Start line number (1-indexed)
            end_line: End line number (1-indexed, inclusive)

        Returns:
            List of lines in the range

        NASA Rule 4: Under 60 lines
        """
        if start_line < 1 or end_line > len(self.source_lines):
            return []

        if start_line > end_line:
            return []

        # Convert to 0-indexed for slicing
        return self.source_lines[start_line - 1:end_line]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary.

        Returns:
            Dict representation of AnalysisContext
        """
        return {
            "file_path": self.file_path,
            "line_count": self.line_count,
            "config": self.config
        }
