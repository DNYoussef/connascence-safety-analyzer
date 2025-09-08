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

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


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

class PatchGenerator:
    """Mock patch generator for backward compatibility."""
    
    def generate_patch(self, violation):
        return None


class AutofixEngine:
    """Mock autofix engine for backward compatibility."""
    
    def __init__(self):
        pass
        
    def fix_violations(self, violations):
        return []


class SafeAutofixer:
    """Mock safe autofixer for backward compatibility."""
    
    def __init__(self):
        pass
        
    def apply_fixes(self, fixes):
        return []
