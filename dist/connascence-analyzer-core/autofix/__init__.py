"""Intelligent autofixer for connascence violations.

This module provides automated refactoring suggestions and patches for
common connascence violations, following the principle of safe transformations.

Safety Features:
- Read-only analysis by default
- Explicit patch generation (no auto-apply)
- Confidence scoring for suggestions
- Rollback mechanisms
"""

from .patch_api import PatchGenerator, AutofixEngine
from .magic_literals import MagicLiteralFixer
from .param_bombs import ParameterBombFixer
from .class_splits import ClassSplitFixer
from .type_hints import TypeHintFixer

__all__ = [
    'PatchGenerator',
    'AutofixEngine', 
    'MagicLiteralFixer',
    'ParameterBombFixer',
    'ClassSplitFixer',
    'TypeHintFixer'
]