"""
Duplication Detection Module
===========================

This module provides MECE (Mutually Exclusive, Collectively Exhaustive) analysis
for detecting code duplication and functional overlap in codebases.

Components:
- MECEAnalyzer: Main analysis engine for detecting various types of duplication
- DuplicationCluster: Data structure for representing found duplications
- FunctionSignature: Detailed function metadata for comparison

Usage:
    from analyzer.dup_detection import MECEAnalyzer
    
    analyzer = MECEAnalyzer()
    results = analyzer.analyze_codebase("/path/to/code", ["*.py", "*.js"])
    
    print(f"Found {len(results['duplication_clusters'])} duplication clusters")
"""

from .mece_analyzer import MECEAnalyzer, DuplicationCluster, FunctionSignature

__all__ = ['MECEAnalyzer', 'DuplicationCluster', 'FunctionSignature']