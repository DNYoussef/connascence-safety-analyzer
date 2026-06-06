"""Type definitions for analyzer utilities."""

from dataclasses import dataclass, field, InitVar
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ConnascenceViolation:
    """Represents a connascence violation found in code."""

    violation_id: str = ""
    type: str = ""
    severity: str = "medium"
    file_path: Path | str = ""
    line_number: int = 0
    column_number: Optional[int] = None
    column: InitVar[Optional[int]] = None  # Backwards compatibility alias
    message: str = ""
    recommendation: str = ""
    description: str = ""
    code_snippet: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    rule_id: Optional[str] = None
    connascence_type: Optional[str] = None
    weight: float = 1.0

    def __post_init__(self, column: Optional[int]):
        # Handle backwards compatibility: column -> column_number
        if column is not None and self.column_number is None:
            self.column_number = column

        if self.context is None:
            self.context = {}

        if self.id and not self.violation_id:
            self.violation_id = self.id
        elif self.violation_id and self.id is None:
            self.id = self.violation_id

        if self.connascence_type and not self.type:
            self.type = self.connascence_type
        elif self.type and not self.connascence_type:
            self.connascence_type = self.type

        if self.description and not self.message:
            self.message = self.description
        elif self.message and not self.description:
            self.description = self.message

        if self.weight == 1.0:
            severity_weights = {"critical": 10.0, "high": 5.0, "medium": 2.0, "low": 1.0}
            self.weight = severity_weights.get(self.severity, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "violation_id": self.violation_id,
            "rule_id": self.rule_id,
            "type": self.type,
            "connascence_type": self.connascence_type,
            "severity": self.severity,
            "weight": self.weight,
            "file_path": str(self.file_path),
            "line_number": self.line_number,
            "column": self.column_number or 0,
            "column_number": self.column_number,
            "message": self.message,
            "description": self.description,
            "recommendation": self.recommendation,
            "code_snippet": self.code_snippet,
            "context": self.context,
        }
