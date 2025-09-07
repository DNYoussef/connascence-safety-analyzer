"""
Connascence Analyzer Service - Main analysis orchestrator.

Extracted from the monolithic check_connascence.py to follow Single Responsibility Principle.
This service orchestrates the analysis pipeline using specialized detectors.
"""
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..detectors.detector_factory import DetectorFactory
from utils.types import ConnascenceViolation


class ConnascenceAnalyzer:
    """
    Main analyzer service that orchestrates connascence detection.
    
    REFACTORED: Now uses DetectorFactory for modular detection instead of
    monolithic ConnascenceDetector. Provides the same interface for 
    backward compatibility.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def analyze_file(self, file_path: Path) -> List[ConnascenceViolation]:
        """
        Analyze a single Python file for connascence violations.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            List of ConnascenceViolation objects found in the file
        """
        if not file_path.exists():
            return []
            
        if not file_path.suffix == '.py':
            return []
            
        try:
            # Read source code
            source_code = file_path.read_text(encoding='utf-8')
            source_lines = source_code.splitlines()
            
            # Parse AST
            tree = ast.parse(source_code, filename=str(file_path))
            
            # Use DetectorFactory for analysis
            detector_factory = DetectorFactory(str(file_path), source_lines)
            violations = detector_factory.detect_all(tree)
            
            return violations
            
        except Exception as e:
            # Log error but don't fail the entire analysis
            print(f"Warning: Error analyzing {file_path}: {e}")
            return []
    
    def analyze_directory(self, directory_path: Path, 
                         exclude_patterns: List[str] = None) -> List[ConnascenceViolation]:
        """
        Recursively analyze all Python files in a directory.
        
        Args:
            directory_path: Path to directory to analyze
            exclude_patterns: List of glob patterns to exclude
            
        Returns:
            List of all ConnascenceViolation objects found
        """
        all_violations = []
        exclude_patterns = exclude_patterns or []
        
        # Find all Python files
        python_files = directory_path.rglob('*.py')
        
        for file_path in python_files:
            # Skip excluded patterns
            if any(file_path.match(pattern) for pattern in exclude_patterns):
                continue
                
            file_violations = self.analyze_file(file_path)
            all_violations.extend(file_violations)
        
        return all_violations
    
    def get_statistics(self, violations: List[ConnascenceViolation]) -> Dict[str, Any]:
        """
        Generate analysis statistics from violations.
        
        Args:
            violations: List of violations to analyze
            
        Returns:
            Dictionary containing analysis statistics
        """
        if not violations:
            return {
                'total_violations': 0,
                'by_severity': {},
                'by_type': {},
                'files_analyzed': 0
            }
        
        # Count by severity
        by_severity = {}
        for violation in violations:
            severity = violation.severity
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Count by type
        by_type = {}
        for violation in violations:
            vtype = violation.type
            by_type[vtype] = by_type.get(vtype, 0) + 1
        
        # Count unique files
        unique_files = len(set(v.file_path for v in violations))
        
        return {
            'total_violations': len(violations),
            'by_severity': by_severity,
            'by_type': by_type,
            'files_analyzed': unique_files
        }