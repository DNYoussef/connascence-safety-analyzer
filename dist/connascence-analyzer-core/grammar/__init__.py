"""
Grammar Layer for Connascence Analysis

Provides formal grammar support for constrained code generation,
AST-safe refactoring, and safety profile enforcement.

Key Components:
- TreeSitterBackend: Tree-sitter parser integration
- GrammarOverlay: Safety subset enforcement  
- ConstrainedGenerator: Ensures generated code stays parseable
- ASTSafeRefactoring: Guarantees syntactic validity
"""

from .backends.tree_sitter_backend import TreeSitterBackend
from .overlay_manager import OverlayManager
from .constrained_generator import ConstrainedGenerator
from .ast_safe_refactoring import ASTSafeRefactoring

__all__ = [
    "TreeSitterBackend",
    "OverlayManager", 
    "ConstrainedGenerator",
    "ASTSafeRefactoring",
]