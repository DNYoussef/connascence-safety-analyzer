"""
AST-based Static Analysis Engine

This module implements comprehensive AST analysis for detecting static
forms of connascence (CoN, CoT, CoM, CoP, CoA).
"""

from .core_analyzer import ConnascenceASTAnalyzer, Violation
from .visitors import (
    NameConnascenceVisitor,
    TypeConnascenceVisitor, 
    MeaningConnascenceVisitor,
    PositionConnascenceVisitor,
    AlgorithmConnascenceVisitor,
)

__all__ = [
    "ConnascenceASTAnalyzer",
    "Violation",
    "NameConnascenceVisitor",
    "TypeConnascenceVisitor", 
    "MeaningConnascenceVisitor",
    "PositionConnascenceVisitor",
    "AlgorithmConnascenceVisitor",
]