
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

@dataclass 
class PatchSuggestion:
    violation_id: str
    confidence: float
    description: str
    old_code: str
    new_code: str
    file_path: str
    line_range: Tuple[int, int]
    safety_level: str = 'moderate'
    rollback_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.rollback_info is None:
            self.rollback_info = {}


# Import the real implementations from core module
from .core import PatchGenerator, AutofixEngine, SafeAutofixer
