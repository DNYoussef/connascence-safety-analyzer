"""
Base Clarity Detector Class

Provides abstract base class for all clarity linter detectors.
Defines common interface and shared functionality.

NASA Rule 4 Compliant: All functions under 60 lines
NASA Rule 5 Compliant: Input assertions
"""

import ast
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from analyzer.clarity_linter.models import ClarityViolation


class BaseClarityDetector(ABC):
    """
    Abstract base class for all clarity linter detectors.

    Provides common interface and shared utilities for:
    - ThinHelperDetector
    - UselessIndirectionDetector
    - CallChainDepthDetector
    - PoorNamingDetector
    - CommentIssuesDetector

    NASA Rule 4 Compliant: All methods under 60 lines
    NASA Rule 5 Compliant: Input assertions
    """

    # Subclasses must define these class attributes
    rule_id: str = ""  # e.g., "CLARITY_THIN_HELPER"
    rule_name: str = ""  # e.g., "Thin Helper Function"
    default_severity: str = "medium"  # "critical", "high", "medium", "low", "info"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize detector with configuration.

        NASA Rule 5: Input validation assertions

        Args:
            config: Optional configuration dictionary from clarity_linter.yaml
        """
        # NASA Rule 5: Input validation
        assert config is None or isinstance(config, dict), \
            "config must be None or dictionary"

        self.config = config or {}
        self.violations: List[ClarityViolation] = []

        # Load rule-specific configuration
        self.rule_config = self._load_rule_config()
        self.severity = self._get_severity()
        self.enabled = self._is_enabled()

        # NASA Rule 5: State validation
        assert isinstance(self.violations, list), "violations must be list"
        assert isinstance(self.severity, str), "severity must be string"
        assert isinstance(self.enabled, bool), "enabled must be boolean"

    def _load_rule_config(self) -> Dict[str, Any]:
        """
        Load rule-specific configuration.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Returns:
            Rule configuration dictionary
        """
        # NASA Rule 5: Input validation
        assert hasattr(self, 'rule_id'), "rule_id must be defined"
        assert isinstance(self.rule_id, str), "rule_id must be string"

        rules = self.config.get('rules', {})
        return rules.get(self.rule_id, {})

    def _get_severity(self) -> str:
        """
        Get severity level for this rule.

        NASA Rule 4: Function under 60 lines

        Returns:
            Severity level string
        """
        return self.rule_config.get('severity', self.default_severity)

    def _is_enabled(self) -> bool:
        """
        Check if rule is enabled in configuration.

        NASA Rule 4: Function under 60 lines

        Returns:
            True if enabled, False otherwise
        """
        return self.rule_config.get('enabled', True)

    def is_enabled(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Public method to check if detector is enabled.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            config: Optional config to check (uses self.config if None)

        Returns:
            True if detector is enabled
        """
        # NASA Rule 5: Input validation
        assert config is None or isinstance(config, dict), \
            "config must be None or dictionary"

        if config:
            rules = config.get('rules', {})
            rule_config = rules.get(self.rule_id, {})
            return rule_config.get('enabled', True)

        return self.enabled

    @abstractmethod
    def detect(
        self,
        tree: ast.Module,
        file_path: Path
    ) -> List[ClarityViolation]:
        """
        Detect violations in AST tree.

        Must be implemented by subclasses.

        NASA Rule 5: Input validation required in implementations

        Args:
            tree: Parsed AST tree to analyze
            file_path: Path to file being analyzed

        Returns:
            List of clarity violations found
        """
        pass

    def get_code_snippet(
        self,
        file_path: Path,
        line_number: int,
        context_lines: int = 2
    ) -> str:
        """
        Extract code snippet around specified line.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            file_path: Path to source file
            line_number: Line number to center on
            context_lines: Number of lines before/after to include

        Returns:
            Formatted code snippet with line numbers
        """
        # NASA Rule 5: Input validation
        assert file_path is not None, "file_path cannot be None"
        assert isinstance(file_path, (str, Path)), "file_path must be string or Path"
        assert isinstance(line_number, int), "line_number must be integer"
        assert line_number > 0, "line_number must be positive"
        assert isinstance(context_lines, int), "context_lines must be integer"
        assert context_lines >= 0, "context_lines must be non-negative"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)

            snippet_lines = []
            for i in range(start_line, end_line):
                marker = ">>>" if i == line_number - 1 else "   "
                snippet_lines.append(
                    f"{marker} {i+1:4d}: {lines[i].rstrip()}"
                )

            return "\n".join(snippet_lines)

        except Exception as e:
            return f"[Unable to extract snippet: {e}]"

    def create_violation(
        self,
        file_path: Path,
        line_number: int,
        description: str,
        recommendation: Optional[str] = None,
        code_snippet: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ClarityViolation:
        """
        Create a ClarityViolation object with proper defaults.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            file_path: Path to file with violation
            line_number: Line number of violation
            description: Description of violation
            recommendation: Optional fix recommendation
            code_snippet: Optional code snippet
            context: Optional additional context data

        Returns:
            ClarityViolation instance
        """
        # NASA Rule 5: Input validation
        assert file_path is not None, "file_path cannot be None"
        assert isinstance(line_number, int), "line_number must be integer"
        assert isinstance(description, str), "description must be string"

        return ClarityViolation(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            severity=self.severity,
            file_path=str(file_path),
            line_number=line_number,
            description=description,
            recommendation=recommendation or self._get_default_recommendation(),
            code_snippet=code_snippet,
            context=context or {}
        )

    def _get_default_recommendation(self) -> str:
        """
        Get default fix recommendation for this rule.

        NASA Rule 4: Function under 60 lines

        Returns:
            Default recommendation string
        """
        return self.rule_config.get(
            'fix_suggestion',
            "Refactor to improve code clarity"
        )

    def reset(self) -> None:
        """
        Reset detector state for reuse.

        NASA Rule 4: Function under 60 lines
        """
        self.violations = []

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get detector-specific metrics.

        NASA Rule 4: Function under 60 lines

        Returns:
            Dictionary with detector metrics
        """
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'severity': self.severity,
            'enabled': self.enabled,
            'violations_found': len(self.violations)
        }


__all__ = ['BaseClarityDetector']
