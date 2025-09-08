"""
Minimal ConnascenceAnalyzer replacement for backward compatibility.

This file contains only the essential classes needed by external interfaces
while delegating the actual work to the new modular architecture.
"""

import argparse
import ast
from pathlib import Path
import sys
import time
from typing import List, Dict, Any

from utils.types import ConnascenceViolation
from .check_connascence import ConnascenceDetector


class ConnascenceAnalyzer:
    """
    Lightweight analyzer wrapper that delegates to the new modular architecture.
    
    REFACTORED: Now uses DetectorFactory and ConnascenceAnalyzer service
    while maintaining 100% backward compatibility.
    """

    def __init__(self, exclusions: List[str] = None):
        self.exclusions = exclusions or [
            "test_*", "tests/", "*_test.py", "conftest.py",
            "deprecated/", "archive/", "experimental/",
            "__pycache__/", ".git/", "build/", "dist/",
            "*.egg-info/", "venv*/", "*env*/",
        ]
        self.violations: List[ConnascenceViolation] = []
        self.file_stats: Dict[str, Dict] = {}

    def analyze_file(self, file_path: Path) -> List[ConnascenceViolation]:
        """Analyze a single Python file using the new modular architecture."""
        try:
            # Import the new service
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
            from services.connascence_analyzer import ConnascenceAnalyzer as AnalyzerService
            
            analyzer = AnalyzerService()
            return analyzer.analyze_file(file_path)
        except ImportError:
            # Fallback to legacy implementation if new services not available
            return self._analyze_python_file(file_path)

    def _analyze_python_file(self, file_path: Path) -> List[ConnascenceViolation]:
        """Fallback legacy implementation."""
        if not file_path.exists() or file_path.suffix != '.py':
            return []

        try:
            source_code = file_path.read_text(encoding='utf-8')
            source_lines = source_code.splitlines()
            
            tree = ast.parse(source_code, filename=str(file_path))
            detector = ConnascenceDetector(str(file_path), source_lines)
            detector.visit(tree)
            
            return detector.violations
        except Exception:
            return []

    def analyze_directory(self, target_path: Path) -> List[ConnascenceViolation]:
        """Analyze all Python files in a directory."""
        all_violations = []
        
        if target_path.is_file():
            return self.analyze_file(target_path)
        
        # Find all Python files
        for py_file in target_path.rglob('*.py'):
            # Skip excluded patterns
            if any(py_file.match(pattern) for pattern in self.exclusions):
                continue
                
            file_violations = self.analyze_file(py_file)
            all_violations.extend(file_violations)
            
            # Update stats
            self.file_stats[str(py_file)] = {
                'violations': len(file_violations),
                'types': list(set(v.type for v in file_violations))
            }
        
        self.violations = all_violations
        return all_violations


def main():
    """Main CLI entry point with minimal implementation."""
    parser = argparse.ArgumentParser(description="Detect connascence violations in Python code")
    parser.add_argument("path", help="Path to analyze (file or directory)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text")
    parser.add_argument("--severity", "-s", choices=["low", "medium", "high", "critical"])
    parser.add_argument("--exclude", "-e", help="Additional exclusion patterns")
    parser.add_argument("--verbose", "-v", action="store_true")
    
    args = parser.parse_args()
    
    target_path = Path(args.path).resolve()
    if not target_path.exists():
        print(f"Error: Path {target_path} does not exist")
        return 1
    
    start_time = time.time()
    analyzer = ConnascenceAnalyzer()
    violations = analyzer.analyze_directory(target_path)
    elapsed = time.time() - start_time
    
    # Filter by severity if specified
    if args.severity:
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_level = severity_order[args.severity]
        violations = [v for v in violations if severity_order.get(v.severity, 0) >= min_level]
    
    # Generate report
    if args.format == "json":
        import json
        report_data = [
            {
                "type": v.type,
                "severity": v.severity,
                "file_path": v.file_path,
                "line_number": v.line_number,
                "column": v.column,
                "description": v.description,
                "recommendation": v.recommendation,
                "context": v.context
            }
            for v in violations
        ]
        report = json.dumps(report_data, indent=2)
    else:
        # Text format
        report_lines = [f"Found {len(violations)} connascence violations:\n"]
        for v in violations:
            report_lines.append(f"{v.severity.upper()}: {v.description}")
            report_lines.append(f"  File: {v.file_path}:{v.line_number}")
            report_lines.append(f"  Fix: {v.recommendation}\n")
        report = "\n".join(report_lines)
    
    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
    else:
        print(report)
    
    if args.verbose:
        print(f"Analysis completed in {elapsed:.2f} seconds")
        print(f"Found {len(violations)} violations")
    
    # Exit with error code if critical violations found
    critical_count = sum(1 for v in violations if v.severity == "critical")
    return min(critical_count, 1)


if __name__ == "__main__":
    sys.exit(main())