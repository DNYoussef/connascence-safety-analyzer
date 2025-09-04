"""
AST-based Static Analysis Engine

This module implements comprehensive AST analysis for detecting static
forms of connascence (CoN, CoT, CoM, CoP, CoA).
"""

from .core_analyzer import ConnascenceASTAnalyzer
from .violations import Violation, AnalysisResult

__all__ = [
    "ConnascenceASTAnalyzer",
    "Violation", 
    "AnalysisResult",
]