"""
Severity Calculator - Extracted from MagicLiteralHandler
=========================================================

Handles severity determination for magic literal violations.
Part of Phase 1.5 to further decompose god objects.
"""

from typing import Any, Dict


class SeverityCalculator:
    """
    Calculates severity levels for magic literal violations.

    Extracted from MagicLiteralHandler to reduce class size.
    """

    def determine_severity(self, value: Any, context_info: Dict) -> str:
        """
        Determine the appropriate severity level for a magic literal violation.

        Severity levels:
        - critical: Never used (reserved for system-breaking issues)
        - high: Magic literals in conditionals, unclear large numbers
        - medium: Most magic literals with clear intent
        - low: Small numbers in appropriate contexts
        - informational: Very low impact cases
        """
        if context_info.get("in_conditional", False):
            base_severity = "high"
        else:
            base_severity = "medium"

        # Apply context-based modifications
        if context_info.get("severity_modifier") == "lower":
            if base_severity == "high":
                return "medium"
            elif base_severity == "medium":
                return "low"
            else:
                return "informational"

        if context_info.get("context_type"):
            return "medium"

        # String-specific severity adjustment
        if isinstance(value, str):
            if context_info.get("likely_structured", False):
                return "low" if base_severity != "high" else "medium"
            if len(str(value)) > 50:
                return "medium"

        # Numeric-specific severity adjustment
        if isinstance(value, (int, float)):
            abs_value = abs(float(value))
            if abs_value > 10000:
                return "high" if base_severity != "low" else "medium"
            elif abs_value > 1000:
                return base_severity
            elif context_info.get("detected_context"):
                return "low" if base_severity != "high" else "medium"

        return base_severity

    def calculate_formal_severity(self, severity_score: float) -> str:
        """Determine severity from formal grammar score."""
        if severity_score < 2.0:
            return "skip"  # Don't create violation
        elif severity_score > 8.0:
            return "high"
        elif severity_score > 5.0:
            return "medium"
        else:
            return "low"

    def get_severity_description(self, severity_score: float) -> str:
        """Get human-readable severity description."""
        if severity_score > 7.0:
            return "high-priority"
        elif severity_score > 4.0:
            return "medium-priority"
        else:
            return "low-priority"
