"""Type definitions for analyzer utilities."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class ConnascenceViolation:
    """Represents a connascence violation found in code."""

    violation_id: str
    type: str
    severity: str
    file_path: Path
    line_number: int
    column_number: Optional[int] = None
    message: str = ""
    context: Dict[str, Any] = None
    recommendation: str = ""

    def __post_init__(self):
        if self.context is None:
            self.context = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "violation_id": self.violation_id,
            "type": self.type,
            "severity": self.severity,
            "file_path": str(self.file_path),
            "line_number": self.line_number,
            "column_number": self.column_number,
            "message": self.message,
            "context": self.context,
            "recommendation": self.recommendation
        }