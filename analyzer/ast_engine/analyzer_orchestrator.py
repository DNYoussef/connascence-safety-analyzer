# SPDX-License-Identifier: MIT
"""
AST-based analyzer orchestrator for god object detection and other complex analysis.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from mcp.server import ConnascenceViolation


class GodObjectAnalyzer:
    """Analyzer for detecting god objects (classes with too many methods/responsibilities)."""
    
    def __init__(self, threshold: int = 15):
        self.threshold = threshold
    
    def analyze_path(self, path: str) -> List[ConnascenceViolation]:
        """Analyze path for god objects using real file analysis."""
        violations = []
        path_obj = Path(path)
        
        if not path_obj.exists():
            return violations
        
        # Real analysis: scan actual Python files
        if path_obj.is_file() and path_obj.suffix == '.py':
            violations.extend(self._analyze_file(path_obj))
        elif path_obj.is_dir():
            # Recursively analyze Python files
            for py_file in path_obj.rglob('*.py'):
                try:
                    violations.extend(self._analyze_file(py_file))
                except Exception as e:
                    print(f"Warning: Failed to analyze {py_file}: {e}")
        
        return violations
    
    def _analyze_file(self, file_path: Path) -> List[ConnascenceViolation]:
        """Analyze a single Python file for god objects."""
        violations = []
        
        try:
            import ast
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Find classes with too many methods
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    if len(methods) > self.threshold:
                        violations.append(ConnascenceViolation(
                            id=f"god_object_{node.name}_{file_path.stem}",
                            rule_id="GOD_OBJECT_METHODS",
                            connascence_type="CoA",
                            severity="high",
                            description=f"God Object detected: Class '{node.name}' has {len(methods)} methods (threshold: {self.threshold})",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            weight=4.0
                        ))
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return violations


class AnalyzerOrchestrator:
    """Orchestrates various AST-based analyzers."""
    
    def __init__(self):
        self.analyzers = {
            'god_object': GodObjectAnalyzer
        }
    
    def analyze(self, *args, **kwargs):
        """Legacy analyze method for backward compatibility."""
        return []
    
    def orchestrate_analysis(self, *args, **kwargs):
        """Legacy orchestrate method for backward compatibility."""
        return []
    
    def analyze_directory(self, path: str, policy: str = "default") -> List[ConnascenceViolation]:
        """Analyze a directory using all available analyzers."""
        violations = []
        path_obj = Path(path)
        
        if not path_obj.exists():
            return violations
        
        # Run god object analysis
        try:
            god_object_analyzer = self.analyzers['god_object'](threshold=15)
            god_violations = god_object_analyzer.analyze_path(path)
            violations.extend(god_violations)
        except Exception as e:
            print(f"Warning: God object analysis failed: {e}")
        
        return violations
    
    def run_analyzer(self, analyzer_type: str, path: str, threshold: int = 15) -> List[ConnascenceViolation]:
        """Run a specific analyzer."""
        if analyzer_type not in self.analyzers:
            raise ValueError(f"Unknown analyzer type: {analyzer_type}")
        
        analyzer_class = self.analyzers[analyzer_type]
        analyzer = analyzer_class(threshold=threshold)
        return analyzer.analyze_path(path)


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(description="AST-based analyzer orchestrator")
    parser.add_argument('--path', required=True, help='Path to analyze')
    parser.add_argument('--analyzer', required=True, choices=['god_object'], help='Analyzer to run')
    parser.add_argument('--threshold', type=int, default=15, help='Analysis threshold')
    parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    try:
        orchestrator = AnalyzerOrchestrator()
        violations = orchestrator.run_analyzer(args.analyzer, args.path, args.threshold)
        
        result = {
            'success': True,
            'analyzer': args.analyzer,
            'path': args.path,
            'threshold': args.threshold,
            'violations': [
                {
                    'id': v.id,
                    'rule_id': v.rule_id,
                    'type': v.connascence_type,
                    'severity': v.severity,
                    'description': v.description,
                    'file_path': v.file_path,
                    'line_number': v.line_number,
                    'weight': v.weight
                }
                for v in violations
            ]
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())


__all__ = ["AnalyzerOrchestrator", "GodObjectAnalyzer"]
