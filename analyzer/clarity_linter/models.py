"""
Clarity Linter Violation Models

Defines data structures for representing clarity violations.

NASA Rule 4 Compliant: All functions under 60 lines
NASA Rule 5 Compliant: Input assertions
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ClarityViolation:
    """
    Represents a single clarity violation detected by the linter.

    Compatible with ConnascenceViolation structure for unified reporting.

    Attributes:
        rule_id: Unique rule identifier (e.g., "CLARITY001")
        rule_name: Human-readable rule name
        severity: Severity level ("critical", "high", "medium", "low", "info")
        file_path: Path to file with violation
        line_number: Line number where violation occurs
        description: Description of the violation
        recommendation: Suggested fix or improvement
        code_snippet: Optional code snippet showing violation
        context: Additional context data
    """

    rule_id: str
    rule_name: str
    severity: str
    file_path: str
    line_number: int
    description: str
    recommendation: str
    code_snippet: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    # Optional fields for enhanced reporting
    column: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert violation to dictionary format.

        NASA Rule 4: Function under 60 lines

        Returns:
            Dictionary representation of violation
        """
        result = {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'severity': self.severity,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'description': self.description,
            'recommendation': self.recommendation,
            'context': self.context,
        }

        # Add optional fields if present
        if self.code_snippet:
            result['code_snippet'] = self.code_snippet
        if self.column:
            result['column'] = self.column
        if self.end_line:
            result['end_line'] = self.end_line
        if self.end_column:
            result['end_column'] = self.end_column

        return result

    def to_connascence_violation(self) -> Dict[str, Any]:
        """
        Convert to ConnascenceViolation format for unified reporting.

        NASA Rule 4: Function under 60 lines

        Returns:
            Dictionary compatible with ConnascenceViolation
        """
        return {
            'type': self.rule_id,
            'severity': self.severity,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'column': self.column,
            'description': self.description,
            'recommendation': self.recommendation,
            'code_snippet': self.code_snippet,
            'context': {
                **self.context,
                'rule_name': self.rule_name,
                'clarity_violation': True
            }
        }

    def __str__(self) -> str:
        """
        String representation of violation.

        NASA Rule 4: Function under 60 lines

        Returns:
            Human-readable violation summary
        """
        return (
            f"{self.severity.upper()}: {self.rule_name} "
            f"({self.rule_id}) at {self.file_path}:{self.line_number}\n"
            f"  {self.description}\n"
            f"  Recommendation: {self.recommendation}"
        )

    def __repr__(self) -> str:
        """
        Developer representation of violation.

        NASA Rule 4: Function under 60 lines

        Returns:
            Detailed violation representation
        """
        return (
            f"ClarityViolation(rule_id='{self.rule_id}', "
            f"severity='{self.severity}', "
            f"file_path='{self.file_path}', "
            f"line_number={self.line_number})"
        )


@dataclass
class ClaritySummary:
    """
    Summary statistics for clarity analysis results.

    Attributes:
        total_files: Number of files analyzed
        total_violations: Total violations found
        violations_by_severity: Count by severity level
        violations_by_rule: Count by rule ID
        violations_by_file: Count by file path
    """

    total_files: int = 0
    total_violations: int = 0
    violations_by_severity: Dict[str, int] = field(default_factory=dict)
    violations_by_rule: Dict[str, int] = field(default_factory=dict)
    violations_by_file: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert summary to dictionary format.

        NASA Rule 4: Function under 60 lines

        Returns:
            Dictionary representation of summary
        """
        return {
            'total_files': self.total_files,
            'total_violations': self.total_violations,
            'violations_by_severity': self.violations_by_severity,
            'violations_by_rule': self.violations_by_rule,
            'violations_by_file': self.violations_by_file,
        }

    @classmethod
    def from_violations(
        cls,
        violations: list,
        total_files: int = 0
    ) -> 'ClaritySummary':
        """
        Create summary from list of violations.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            violations: List of ClarityViolation objects
            total_files: Total number of files analyzed

        Returns:
            ClaritySummary instance with computed statistics
        """
        # NASA Rule 5: Input validation
        assert isinstance(violations, list), "violations must be list"
        assert isinstance(total_files, int), "total_files must be integer"
        assert total_files >= 0, "total_files must be non-negative"

        summary = cls(
            total_files=total_files,
            total_violations=len(violations)
        )

        # Count by severity
        for violation in violations:
            severity = violation.severity
            summary.violations_by_severity[severity] = \
                summary.violations_by_severity.get(severity, 0) + 1

        # Count by rule
        for violation in violations:
            rule_id = violation.rule_id
            summary.violations_by_rule[rule_id] = \
                summary.violations_by_rule.get(rule_id, 0) + 1

        # Count by file
        for violation in violations:
            file_path = violation.file_path
            summary.violations_by_file[file_path] = \
                summary.violations_by_file.get(file_path, 0) + 1

        return summary


__all__ = ['ClarityViolation', 'ClaritySummary']
