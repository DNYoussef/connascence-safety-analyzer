
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

# CoP Improvement - Pass 3: Parameter Objects
@dataclass
class ViolationCreationParams:
    """Parameter object for ConnascenceViolation creation (CoP Improvement - Pass 3)."""
    type_name: Optional[str] = None
    severity: Optional[str] = None
    file_path: Optional[str] = None
    line: Optional[int] = None
    description: Optional[str] = None
    id: Optional[str] = None
    rule_id: Optional[str] = None
    connascence_type: Optional[str] = None
    weight: float = 1.0
    
    def to_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs dictionary for backward compatibility."""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'connascence_type': self.connascence_type,
            'weight': self.weight
        }

@dataclass
class ConnascenceViolation:
    id: str = ''
    rule_id: str = ''
    connascence_type: str = ''
    severity: str = 'medium'
    description: str = ''
    file_path: str = ''
    line_number: int = 0
    weight: float = 1.0
    
    def __init__(self, type_name=None, severity=None, file_path=None, line=None, description=None, params: Optional[ViolationCreationParams] = None, **kwargs):
        # CoP Improvement - Pass 3: Support both parameter object and legacy signature
        if params is not None:
            # Use parameter object (preferred)
            self.id = params.id or kwargs.get('id', f'violation_{hash(str(kwargs))}')
            self.rule_id = params.rule_id or kwargs.get('rule_id', f'CON_{params.type_name or type_name or "Unknown"}')
            self.connascence_type = params.connascence_type or params.type_name or type_name or kwargs.get('connascence_type', 'Unknown')
            self.severity = params.severity or severity or 'medium'
            self.description = params.description or description or 'No description'
            self.file_path = params.file_path or file_path or ''
            self.line_number = params.line or line or 0
            self.weight = params.weight or kwargs.get('weight', 1.0)
        else:
            # Legacy parameter signature (backward compatibility)
            self.id = kwargs.get('id', f'violation_{hash(str(kwargs))}')
            self.rule_id = kwargs.get('rule_id', f'CON_{type_name or "Unknown"}')
            self.connascence_type = type_name or kwargs.get('connascence_type', 'Unknown')
            self.severity = severity or 'medium'
            self.description = description or 'No description'
            self.file_path = file_path or ''
            self.line_number = line or 0
            self.weight = kwargs.get('weight', 1.0)
        
    @classmethod
    def create_with_params(cls, params: ViolationCreationParams) -> 'ConnascenceViolation':
        """Factory method using parameter object (CoP Improvement - Pass 3)."""
        return cls(params=params)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.connascence_type,
            'severity': self.severity,
            'file': self.file_path,
            'line': self.line_number,
            'description': self.description
        }
