"""
Violation Factory

Provides factory methods for creating ConnascenceViolation objects with proper
defaults and validation. This module consolidates violation creation logic that
was previously duplicated across multiple detector implementations.

NASA Rule 4 Compliant: All functions under 60 lines
"""

from typing import Any, Dict, Optional

from fixes.phase0.production_safe_assertions import ProductionAssert


class ViolationFactory:
    """
    Factory class for creating ConnascenceViolation objects.

    Provides standardized violation creation with proper defaults, validation,
    and consistent formatting. Used by detectors in analyzer/detectors/ to
    ensure uniform violation structure.
    """

    @staticmethod
    def _validate_violation_inputs(
        violation_type: str, severity: str, location: Dict[str, Any], description: str
    ) -> None:
        """
        Validate inputs for violation creation.

        Args:
            violation_type: Type of connascence
            severity: Severity level
            location: Location dict
            description: Description text

        NASA Rule 4: Under 60 lines
        NASA Rule 5: Input assertions
        """
        ProductionAssert.not_none(violation_type, "violation_type")
        ProductionAssert.not_none(severity, "severity")
        ProductionAssert.not_none(location, "location")
        ProductionAssert.not_none(description, "description")

        # Validate severity
        valid_severities = {"low", "medium", "high", "critical"}
        assert severity in valid_severities, f"Invalid severity: {severity}"

        # Validate location has required fields
        assert "file" in location, "location must have 'file' field"
        assert "line" in location, "location must have 'line' field"

    @staticmethod
    def create_violation(
        violation_type: str,
        severity: str,
        location: Dict[str, Any],
        description: str,
        recommendation: Optional[str] = None,
        code_snippet: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized ConnascenceViolation object.

        Args:
            violation_type: Type of connascence (e.g., "CoP", "CoM", "CoT")
            severity: Severity level ("low", "medium", "high", "critical")
            location: Location dict with file, line, column
            description: Human-readable description of violation
            recommendation: Optional fix recommendation
            code_snippet: Optional code snippet showing violation
            context: Optional additional context data

        Returns:
            Dict representing a ConnascenceViolation with all fields

        NASA Rule 4: Under 60 lines
        NASA Rule 5: Input assertions
        """
        ViolationFactory._validate_violation_inputs(violation_type, severity, location, description)

        # Build violation object
        violation = {
            "type": violation_type,
            "severity": severity,
            "file_path": location["file"],
            "line_number": location["line"],
            "column": location.get("column", 0),
            "description": description,
        }

        # Add optional fields if provided
        if recommendation:
            violation["recommendation"] = recommendation
        if code_snippet:
            violation["code_snippet"] = code_snippet
        if context:
            violation["context"] = context

        # Add end location if available
        if "end_line" in location:
            violation["end_line"] = location["end_line"]
        if "end_column" in location:
            violation["end_column"] = location["end_column"]

        return violation

    @staticmethod
    def create_cop_violation(
        location: Dict[str, Any], function_name: str, param_count: int, threshold: int = 3
    ) -> Dict[str, Any]:
        """
        Create a Connascence of Position (CoP) violation.

        Args:
            location: Location dict with file, line, column
            function_name: Name of function with too many parameters
            param_count: Number of positional parameters
            threshold: Maximum allowed parameters (default: 3)

        Returns:
            Dict representing a CoP violation

        NASA Rule 4: Under 60 lines
        """
        ProductionAssert.not_none(location, "location")
        ProductionAssert.not_none(function_name, "function_name")

        description = f"Function '{function_name}' has {param_count} positional " f"parameters (threshold: {threshold})"

        recommendation = (
            "Consider using a parameter object, keyword arguments, or " "breaking the function into smaller pieces."
        )

        context = {"function_name": function_name, "param_count": param_count, "threshold": threshold}

        return ViolationFactory.create_violation(
            violation_type="CoP",
            severity="high" if param_count > threshold + 2 else "medium",
            location=location,
            description=description,
            recommendation=recommendation,
            context=context,
        )

    @staticmethod
    def create_com_violation(location: Dict[str, Any], literal_value: Any, literal_type: str) -> Dict[str, Any]:
        """
        Create a Connascence of Meaning (CoM) violation.

        Args:
            location: Location dict with file, line, column
            literal_value: The magic literal value
            literal_type: Type of literal (e.g., "number", "string")

        Returns:
            Dict representing a CoM violation

        NASA Rule 4: Under 60 lines
        """
        ProductionAssert.not_none(location, "location")
        ProductionAssert.not_none(literal_value, "literal_value")
        ProductionAssert.not_none(literal_type, "literal_type")

        description = f"Magic {literal_type} literal '{literal_value}' should be " f"extracted to a named constant"

        recommendation = "Extract this literal to a module-level constant with a " "descriptive name."

        context = {"literal_value": literal_value, "literal_type": literal_type}

        return ViolationFactory.create_violation(
            violation_type="CoM",
            severity="medium",
            location=location,
            description=description,
            recommendation=recommendation,
            context=context,
        )

    @staticmethod
    def create_cot_violation(location: Dict[str, Any], element_name: str, missing_types: str) -> Dict[str, Any]:
        """
        Create a Connascence of Type (CoT) violation.

        Args:
            location: Location dict with file, line, column
            element_name: Name of element missing type hints
            missing_types: Description of missing types

        Returns:
            Dict representing a CoT violation

        NASA Rule 4: Under 60 lines
        """
        ProductionAssert.not_none(location, "location")
        ProductionAssert.not_none(element_name, "element_name")
        ProductionAssert.not_none(missing_types, "missing_types")

        description = f"'{element_name}' is missing type hints: {missing_types}"

        recommendation = "Add explicit type hints for all parameters and return values."

        context = {"element_name": element_name, "missing_types": missing_types}

        return ViolationFactory.create_violation(
            violation_type="CoT",
            severity="medium",
            location=location,
            description=description,
            recommendation=recommendation,
            context=context,
        )
