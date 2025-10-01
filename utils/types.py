# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Canonical type definitions for the Connascence Safety Analyzer.

This module provides the single source of truth for all data types used
across the analyzer, eliminating duplicate class definitions and ensuring
consistency across all modules.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ConnascenceViolation:
    """
    Canonical connascence violation representation across all modules.

    This is the single source of truth for ConnascenceViolation objects,
    replacing 8 duplicate definitions throughout the codebase.

    Attributes:
        id: Unique identifier for the violation (optional)
        rule_id: Rule identifier (e.g., 'connascence_of_position')
        type: Violation type (primary field)
        connascence_type: Alias for type (backward compatibility)
        severity: Severity level ('critical', 'high', 'medium', 'low')
        weight: Numeric weight for scoring (default: 1.0)
        file_path: Path to the file containing the violation
        line_number: Line number where violation occurs (0-based)
        column: Column number where violation occurs (0-based)
        description: Human-readable description of the violation
        recommendation: Suggested fix or improvement
        code_snippet: Relevant code excerpt
        context: Additional contextual information
    """

    # Core identification
    id: Optional[str] = None
    rule_id: Optional[str] = None
    type: str = ""
    connascence_type: Optional[str] = None  # Backward compatibility alias

    # Severity and classification
    severity: str = "medium"  # 'critical', 'high', 'medium', 'low'
    weight: float = 1.0

    # Location information
    file_path: str = ""
    line_number: int = 0
    column: int = 0

    # Content and context
    description: str = ""
    recommendation: str = ""
    code_snippet: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure backward compatibility aliases are properly set."""
        # Maintain bidirectional compatibility between type and connascence_type
        if self.connascence_type and not self.type:
            self.type = self.connascence_type
        elif self.type and not self.connascence_type:
            self.connascence_type = self.type

        # Ensure weight is set based on severity if not provided
        if self.weight == 1.0:  # Default value, calculate from severity
            severity_weights = {"critical": 10.0, "high": 5.0, "medium": 2.0, "low": 1.0}
            self.weight = severity_weights.get(self.severity, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary representation."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "type": self.type,
            "connascence_type": self.connascence_type,
            "severity": self.severity,
            "weight": self.weight,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "description": self.description,
            "recommendation": self.recommendation,
            "code_snippet": self.code_snippet,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnascenceViolation":
        """Create violation from dictionary representation."""
        return cls(
            id=data.get("id"),
            rule_id=data.get("rule_id"),
            type=data.get("type", ""),
            connascence_type=data.get("connascence_type"),
            severity=data.get("severity", "medium"),
            weight=data.get("weight", 1.0),
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
            column=data.get("column", 0),
            description=data.get("description", ""),
            recommendation=data.get("recommendation", ""),
            code_snippet=data.get("code_snippet", ""),
            context=data.get("context", {}),
        )


# Legacy compatibility function for modules that expect init-style construction
def create_violation(**kwargs) -> ConnascenceViolation:
    """
    Legacy compatibility function for creating violations with keyword arguments.

    This provides backward compatibility for modules that used init-style
    ConnascenceViolation construction with arbitrary keyword arguments.
    """
    return ConnascenceViolation(**kwargs)


# Type aliases for common use patterns
Violation = ConnascenceViolation  # Short alias
ViolationDict = Dict[str, Any]  # Dictionary representation


__all__ = ["ConnascenceViolation", "Violation", "ViolationDict", "create_violation"]
