"""
Core analyzer classes and data structures.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class ConnascenceViolation:
    """Represents a connascence violation found in code."""
    
    # Core identification
    id: str = ''
    rule_id: str = ''
    connascence_type: str = ''
    
    # Severity and description
    severity: str = 'medium'
    description: str = ''
    
    # Location information
    file_path: str = ''
    line_number: int = 0
    
    # Analysis metadata
    weight: float = 1.0
    
    def __init__(self, type_name=None, severity=None, file_path=None, 
                 line=None, description=None, **kwargs):
        """Initialize with flexible parameter names for backward compatibility."""
        self.id = kwargs.get('id', f"violation_{hash(str(kwargs))}")
        self.rule_id = kwargs.get('rule_id', f"CON_{type_name or 'Unknown'}")
        self.connascence_type = type_name or kwargs.get('connascence_type', 'Unknown')
        
        self.severity = severity or kwargs.get('severity', 'medium')
        self.description = description or kwargs.get('description', 'No description')
        
        self.file_path = file_path or kwargs.get('file_path', '')
        self.line_number = line or kwargs.get('line_number', 0)
        
        self.weight = kwargs.get('weight', 1.0)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary format."""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'type': self.connascence_type,
            'severity': self.severity,
            'description': self.description,
            'file': self.file_path,
            'line': self.line_number,
            'weight': self.weight
        }
