#!/usr/bin/env python3

"""
Cross-folder dependency and coupling analysis for connascence analyzer repository.
Generates comprehensive architectural assessment including dependency matrices and coupling analysis.
"""

import ast
import json
import os
import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

class DependencyAnalyzer:
    """Analyzes import dependencies and coupling across repository folders."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.folders_to_analyze = [
            'analyzer', 'cli', 'mcp', 'config', 'policy', 'utils', 
            'integrations', 'security', 'tests', 'experimental',
            'core', 'reporting', 'dashboard', 'autofix'
        ]
        
        # Dependency tracking
        self.import_graph: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.file_imports: Dict[str, List[Tuple[str, str]]] = {}
        self.circular_dependencies: List[List[str]] = []
        self.interface_analysis: Dict[str, Dict[str, Any]] = {}
        
        # Coupling metrics
        self.coupling_matrix: Dict[str, Dict[str, float]] = {}
        self.fan_in: Dict[str, int] = defaultdict(int)
        self.fan_out: Dict[str, int] = defaultdict(int)
        
    def extract_imports_from_file(self, file_path: Path) -> List[Tuple[str, str]]:
        """Extract import statements from a Python file."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to extract imports
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(('import', alias.name))
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ''
                        for alias in node.names:
                            imports.append(('from', f"{module}.{alias.name}" if module else alias.name))
            except SyntaxError:
                # Fallback to regex parsing for problematic files
                import_patterns = [
                    r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
                    r'^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+([a-zA-Z_][a-zA-Z0-9_.*,\s]*)'
                ]
                
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('import '):
                        match = re.match(import_patterns[0], line)
                        if match:
                            imports.append(('import', match.group(1)))
                    elif line.startswith('from '):
                        match = re.match(import_patterns[1], line)
                        if match:
                            imports.append(('from', f"{match.group(1)}.{match.group(2)}"))
                            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return imports
    
    def get_folder_from_import(self, import_name: str) -> Optional[str]:
        """Determine which folder an import refers to."""
        # Handle relative imports
        if import_name.startswith('.'):
            return None
            
        # Check if import refers to one of our analyzed folders
        first_part = import_name.split('.')[0]
        
        # Direct folder references
        if first_part in self.folders_to_analyze:
            return first_part
            
        # Handle special cases
        if first_part in ['mcp', 'analyzer', 'cli']:
            return first_part
        if import_name.startswith('utils.'):
            return 'utils'
        if import_name.startswith('config.'):
            return 'config'
        if import_name.startswith('core.'):
            return 'core'
            
        return None
    
    def analyze_all_files(self):
        """Analyze all Python files for import dependencies."""
        print("Analyzing import dependencies across all folders...")
        
        for folder in self.folders_to_analyze:
            folder_path = self.root_path / folder
            if not folder_path.exists():
                continue
                
            # Find all Python files in folder
            for py_file in folder_path.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                    
                relative_path = str(py_file.relative_to(self.root_path))
                imports = self.extract_imports_from_file(py_file)
                self.file_imports[relative_path] = imports
                
                # Count folder-to-folder dependencies
                source_folder = folder
                for import_type, import_name in imports:
                    target_folder = self.get_folder_from_import(import_name)
                    if target_folder and target_folder != source_folder:
                        self.import_graph[source_folder][target_folder] += 1
                        self.fan_out[source_folder] += 1
                        self.fan_in[target_folder] += 1
    
    def calculate_coupling_metrics(self):
        """Calculate coupling strength between folders."""
        print("Calculating coupling metrics...")
        
        all_folders = set(self.folders_to_analyze)
        
        for source in all_folders:
            self.coupling_matrix[source] = {}
            for target in all_folders:
                if source == target:
                    self.coupling_matrix[source][target] = 0.0
                else:
                    # Calculate coupling strength based on import count and fan-out
                    import_count = self.import_graph[source][target]
                    total_imports = sum(self.import_graph[source].values()) or 1
                    coupling_strength = import_count / total_imports
                    self.coupling_matrix[source][target] = coupling_strength
    
    def detect_circular_dependencies(self):
        """Detect circular dependencies between folders."""
        print("Detecting circular dependencies...")
        
        # Use DFS to detect cycles in the dependency graph
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                if len(cycle) > 2:  # Only report non-trivial cycles
                    self.circular_dependencies.append(cycle)
                return
                
            if node in visited:
                return
                
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.import_graph[node]:
                if self.import_graph[node][neighbor] > 0:
                    dfs(neighbor, path + [neighbor])
            
            rec_stack.remove(node)
        
        for folder in self.folders_to_analyze:
            if folder not in visited:
                dfs(folder, [folder])
    
    def analyze_interfaces(self):
        """Analyze public interfaces and communication patterns between folders."""
        print("Analyzing interfaces and communication patterns...")
        
        for source_folder in self.folders_to_analyze:
            self.interface_analysis[source_folder] = {
                'exports_to': list(self.import_graph[source_folder].keys()),
                'imports_from': [],
                'shared_modules': [],
                'coupling_strength': self.fan_out.get(source_folder, 0)
            }
            
            # Find what imports from this folder
            for other_folder in self.folders_to_analyze:
                if self.import_graph[other_folder][source_folder] > 0:
                    self.interface_analysis[source_folder]['imports_from'].append(other_folder)
    
    def identify_architectural_violations(self) -> List[Dict[str, Any]]:
        """Identify potential architectural violations."""
        violations = []
        
        # High coupling violations
        for source, targets in self.coupling_matrix.items():
            for target, strength in targets.items():
                if strength > 0.3:  # High coupling threshold
                    violations.append({
                        'type': 'high_coupling',
                        'source': source,
                        'target': target,
                        'strength': strength,
                        'description': f"High coupling between {source} and {target} ({strength:.2%})"
                    })
        
        # Circular dependency violations
        for cycle in self.circular_dependencies:
            violations.append({
                'type': 'circular_dependency',
                'cycle': cycle,
                'description': f"Circular dependency detected: {' -> '.join(cycle)}"
            })
        
        # Architectural layering violations
        layering_rules = {
            'cli': ['analyzer', 'mcp', 'utils', 'config'],
            'mcp': ['analyzer', 'utils', 'config'],
            'analyzer': ['utils', 'config', 'core'],
            'tests': ['analyzer', 'cli', 'mcp', 'utils', 'config'],
        }
        
        for source, allowed_deps in layering_rules.items():
            if source in self.import_graph:
                for target in self.import_graph[source]:
                    if target not in allowed_deps and self.import_graph[source][target] > 0:
                        violations.append({
                            'type': 'layering_violation',
                            'source': source,
                            'target': target,
                            'description': f"Layering violation: {source} should not depend on {target}"
                        })
        
        return violations
    
    def generate_dependency_matrix(self) -> str:
        """Generate a visual dependency matrix."""
        folders = sorted(self.folders_to_analyze)
        
        # Header
        matrix = "DEPENDENCY MATRIX (source -> target):\n"
        matrix += "=" * 50 + "\n"
        matrix += f"{'Source':>12} | "
        for folder in folders:
            matrix += f"{folder[:8]:>8} "
        matrix += "\n"
        matrix += "-" * (14 + len(folders) * 9) + "\n"
        
        # Rows
        for source in folders:
            matrix += f"{source:>12} | "
            for target in folders:
                count = self.import_graph[source][target]
                if source == target:
                    matrix += f"{'--':>8} "
                elif count > 0:
                    matrix += f"{count:>8} "
                else:
                    matrix += f"{'':>8} "
            matrix += "\n"
        
        return matrix
    
    def generate_coupling_analysis(self) -> str:
        """Generate coupling strength analysis."""
        analysis = "\nCOUPLING ANALYSIS:\n"
        analysis += "=" * 30 + "\n"
        
        # High coupling pairs
        high_coupling = []
        for source, targets in self.coupling_matrix.items():
            for target, strength in targets.items():
                if strength > 0.1:  # Significant coupling threshold
                    high_coupling.append((source, target, strength))
        
        high_coupling.sort(key=lambda x: x[2], reverse=True)
        
        analysis += "\nHigh Coupling Pairs (>10%):\n"
        for source, target, strength in high_coupling[:10]:
            analysis += f"  {source:>12} -> {target:<12} ({strength:>6.2%})\n"
        
        # Fan-in/Fan-out analysis
        analysis += f"\nFan-In Analysis (most depended upon):\n"
        for folder, count in sorted(self.fan_in.items(), key=lambda x: x[1], reverse=True)[:8]:
            analysis += f"  {folder:>12}: {count} dependencies\n"
        
        analysis += f"\nFan-Out Analysis (most dependent):\n"
        for folder, count in sorted(self.fan_out.items(), key=lambda x: x[1], reverse=True)[:8]:
            analysis += f"  {folder:>12}: {count} outgoing dependencies\n"
        
        return analysis
    
    def generate_recommendations(self, violations: List[Dict[str, Any]]) -> str:
        """Generate refactoring recommendations."""
        recommendations = "\nREFACTORING RECOMMENDATIONS:\n"
        recommendations += "=" * 40 + "\n"
        
        # Group violations by type
        violation_groups = defaultdict(list)
        for violation in violations:
            violation_groups[violation['type']].append(violation)
        
        priority = 1
        
        # High coupling recommendations
        if 'high_coupling' in violation_groups:
            recommendations += f"\n{priority}. HIGH PRIORITY - Reduce Coupling:\n"
            for violation in violation_groups['high_coupling'][:5]:
                recommendations += f"   - Decouple {violation['source']} from {violation['target']} "
                recommendations += f"(current: {violation['strength']:.2%})\n"
            priority += 1
        
        # Circular dependency recommendations
        if 'circular_dependency' in violation_groups:
            recommendations += f"\n{priority}. CRITICAL - Break Circular Dependencies:\n"
            for violation in violation_groups['circular_dependency']:
                cycle = ' -> '.join(violation['cycle'])
                recommendations += f"   - Break cycle: {cycle}\n"
            priority += 1
        
        # Layering violation recommendations
        if 'layering_violation' in violation_groups:
            recommendations += f"\n{priority}. MEDIUM - Fix Layering Violations:\n"
            for violation in violation_groups['layering_violation'][:5]:
                recommendations += f"   - Move dependency from {violation['source']} to {violation['target']} "
                recommendations += f"through proper abstraction layer\n"
            priority += 1
        
        # General architectural improvements
        recommendations += f"\n{priority}. ARCHITECTURAL IMPROVEMENTS:\n"
        recommendations += "   - Extract common interfaces for high fan-in modules\n"
        recommendations += "   - Consider dependency injection for tightly coupled components\n"
        recommendations += "   - Implement facade patterns for complex subsystem interactions\n"
        recommendations += "   - Create abstract base classes for shared behaviors\n"
        
        return recommendations
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete dependency and coupling analysis."""
        print("Starting comprehensive cross-folder dependency analysis...")
        
        # Step 1: Analyze all files
        self.analyze_all_files()
        
        # Step 2: Calculate metrics
        self.calculate_coupling_metrics()
        
        # Step 3: Detect issues
        self.detect_circular_dependencies()
        self.analyze_interfaces()
        violations = self.identify_architectural_violations()
        
        # Step 4: Generate reports
        dependency_matrix = self.generate_dependency_matrix()
        coupling_analysis = self.generate_coupling_analysis()
        recommendations = self.generate_recommendations(violations)
        
        # Create summary report
        report = {
            'summary': {
                'total_folders_analyzed': len(self.folders_to_analyze),
                'total_files_analyzed': len(self.file_imports),
                'total_dependencies': sum(sum(targets.values()) for targets in self.import_graph.values()),
                'circular_dependencies_found': len(self.circular_dependencies),
                'total_violations': len(violations)
            },
            'dependency_matrix': dependency_matrix,
            'coupling_analysis': coupling_analysis,
            'circular_dependencies': self.circular_dependencies,
            'violations': violations,
            'recommendations': recommendations,
            'detailed_metrics': {
                'import_graph': dict(self.import_graph),
                'coupling_matrix': self.coupling_matrix,
                'fan_in': dict(self.fan_in),
                'fan_out': dict(self.fan_out),
                'interface_analysis': self.interface_analysis
            }
        }
        
        return report

def main():
    """Main entry point for dependency analysis."""
    root_path = Path(__file__).parent.parent
    analyzer = DependencyAnalyzer(str(root_path))
    
    # Run full analysis
    report = analyzer.run_full_analysis()
    
    # Print console report
    print("\n" + "=" * 80)
    print("CROSS-FOLDER DEPENDENCY AND COUPLING ANALYSIS")
    print("=" * 80)
    print(f"\nSUMMARY:")
    print(f"- Folders analyzed: {report['summary']['total_folders_analyzed']}")
    print(f"- Files analyzed: {report['summary']['total_files_analyzed']}")
    print(f"- Total dependencies: {report['summary']['total_dependencies']}")
    print(f"- Circular dependencies: {report['summary']['circular_dependencies_found']}")
    print(f"- Total violations: {report['summary']['total_violations']}")
    
    print(report['dependency_matrix'])
    print(report['coupling_analysis'])
    print(report['recommendations'])
    
    # Save detailed report
    output_file = root_path / "analysis" / "dependency_analysis_report.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nDetailed analysis saved to: {output_file}")
    
    return report

if __name__ == "__main__":
    main()