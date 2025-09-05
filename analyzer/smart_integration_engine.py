# SPDX-License-Identifier: MIT
# Smart integration engine for real connascence analysis

import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

class SmartIntegrationEngine:
    """Smart integration engine for real connascence analysis."""
    
    def __init__(self):
        self.violations = []
    
    def integrate(self, *args, **kwargs):
        return []
    
    def comprehensive_analysis(self, path: str, policy: str = "default") -> Dict[str, Any]:
        """Perform comprehensive analysis on real files."""
        path_obj = Path(path)
        violations = []
        
        if not path_obj.exists():
            return {
                'violations': [],
                'summary': {'total_violations': 0, 'critical_violations': 0},
                'nasa_compliance': {'score': 1.0, 'violations': [], 'passing': True}
            }
        
        # Analyze real files
        if path_obj.is_file() and path_obj.suffix == '.py':
            violations.extend(self._analyze_python_file(path_obj))
        elif path_obj.is_dir():
            # Recursively analyze Python files in directory
            for py_file in path_obj.rglob('*.py'):
                try:
                    violations.extend(self._analyze_python_file(py_file))
                except Exception as e:
                    print(f"Warning: Failed to analyze {py_file}: {e}")
        
        # Calculate summary
        critical_violations = len([v for v in violations if v.get('severity') == 'critical'])
        
        return {
            'violations': violations,
            'summary': {
                'total_violations': len(violations),
                'critical_violations': critical_violations
            },
            'nasa_compliance': {
                'score': 1.0 if critical_violations == 0 else 0.5,
                'violations': [],
                'passing': critical_violations == 0
            }
        }
    
    def _analyze_python_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze a single Python file for real violations."""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Parse AST
            tree = ast.parse(source)
            
            # Analyze for real violations
            for node in ast.walk(tree):
                # Check for God Objects (classes with too many methods)
                if isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    if len(methods) > 15:  # Threshold for God Object
                        violations.append({
                            'id': f'god_object_{node.name}',
                            'rule_id': 'god_object',
                            'type': 'god_object',
                            'severity': 'high',
                            'description': f'God Object detected: Class "{node.name}" has {len(methods)} methods (threshold: 15)',
                            'file_path': str(file_path),
                            'line_number': node.lineno,
                            'weight': 4.0
                        })
                
                # Check for long parameter lists (Connascence of Position)
                if isinstance(node, ast.FunctionDef):
                    param_count = len(node.args.args)
                    if param_count > 6:  # NASA Rule: max 6 parameters
                        violations.append({
                            'id': f'parameter_bomb_{node.name}',
                            'rule_id': 'connascence_of_position',
                            'type': 'CoP',
                            'severity': 'medium',
                            'description': f'Function "{node.name}" has {param_count} parameters (NASA limit: 6)',
                            'file_path': str(file_path),
                            'line_number': node.lineno,
                            'weight': 2.0
                        })
                
                # Check for magic literals (Connascence of Meaning)
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and node.value not in [0, 1, -1]:
                    violations.append({
                        'id': f'magic_literal_{node.lineno}',
                        'rule_id': 'connascence_of_meaning',
                        'type': 'CoM',
                        'severity': 'low',
                        'description': f'Magic literal "{node.value}" should be a named constant',
                        'file_path': str(file_path),
                        'line_number': node.lineno,
                        'weight': 1.0
                    })
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return violations

__all__ = ["SmartIntegrationEngine"]
