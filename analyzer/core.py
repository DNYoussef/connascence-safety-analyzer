
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

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
    
    def __init__(self, type_name=None, severity=None, file_path=None, line=None, description=None, **kwargs):
        self.id = kwargs.get('id', f'violation_{hash(str(kwargs))}')
        self.rule_id = kwargs.get('rule_id', f'CON_{type_name or "Unknown"}')
        self.connascence_type = type_name or kwargs.get('connascence_type', 'Unknown')
        self.severity = severity or 'medium'
        self.description = description or 'No description'
        self.file_path = file_path or ''
        self.line_number = line or 0
        self.weight = kwargs.get('weight', 1.0)
        
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.connascence_type,
            'severity': self.severity,
            'file': self.file_path,
            'line': self.line_number,
            'description': self.description
        }
