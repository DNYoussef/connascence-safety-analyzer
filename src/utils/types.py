"""
Type definitions for connascence analysis.

Copied from utils.types for the new modular architecture.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ConnascenceViolation:
    """Represents a single connascence violation detected in code."""
    
    type: str
    severity: str 
    file_path: str
    line_number: int
    column: int
    description: str
    recommendation: str
    code_snippet: str
    context: Dict[str, Any]