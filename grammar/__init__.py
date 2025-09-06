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

from .ast_safe_refactoring import ASTSafeRefactoring
from .backends.tree_sitter_backend import TreeSitterBackend
from .constrained_generator import ConstrainedGenerator
from .overlay_manager import OverlayManager

__all__ = [
    "TreeSitterBackend",
    "OverlayManager",
    "ConstrainedGenerator",
    "ASTSafeRefactoring",
]
