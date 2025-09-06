#!/usr/bin/env python3

"""
VS Code extension dependency analysis for the connascence analyzer repository.
Analyzes TypeScript/JavaScript files in the vscode-extension folder.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any

class VSCodeExtensionAnalyzer:
    """Analyzes VS Code extension architecture and dependencies."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.extension_path = self.root_path / "vscode-extension"
        self.import_graph = defaultdict(lambda: defaultdict(int))
        self.file_analysis = {}
        
    def extract_ts_js_imports(self, file_path: Path) -> List[Tuple[str, str]]:
        """Extract import statements from TypeScript/JavaScript files."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # TypeScript/JavaScript import patterns
            import_patterns = [
                # import { something } from 'module'
                r"import\s+\{[^}]*\}\s+from\s+['\"]([^'\"]+)['\"]",
                # import * as something from 'module'
                r"import\s+\*\s+as\s+\w+\s+from\s+['\"]([^'\"]+)['\"]",
                # import something from 'module'
                r"import\s+\w+\s+from\s+['\"]([^'\"]+)['\"]",
                # const something = require('module')
                r"(?:const|let|var)\s+.*?\s*=\s*require\(['\"]([^'\"]+)['\"]\)",
                # require('module')
                r"require\(['\"]([^'\"]+)['\"]\)"
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    imports.append(('import', match))
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return imports
    
    def categorize_import(self, import_name: str) -> str:
        """Categorize import by type."""
        if import_name.startswith('./') or import_name.startswith('../'):
            return 'internal'
        elif import_name.startswith('@types/'):
            return 'types'
        elif import_name in ['vscode', '@vscode/test-electron']:
            return 'vscode-api'
        elif import_name.startswith('@') or import_name in ['typescript', 'esbuild']:
            return 'external'
        else:
            return 'node-builtin' if import_name in ['fs', 'path', 'os', 'util'] else 'external'
    
    def get_module_category(self, file_path: Path) -> str:
        """Determine the module category for a file."""
        relative_path = file_path.relative_to(self.extension_path)
        parts = relative_path.parts
        
        if 'src' in parts:
            src_index = parts.index('src')
            if len(parts) > src_index + 1:
                return parts[src_index + 1]
        
        if parts[0] in ['test', 'tests']:
            return 'test'
        elif parts[0] in ['out', 'dist']:
            return 'build'
        elif file_path.name in ['webpack.config.js', 'tsconfig.json', 'package.json']:
            return 'config'
            
        return 'root'
    
    def analyze_extension_structure(self):
        """Analyze the VS Code extension structure."""
        print("Analyzing VS Code extension structure...")
        
        if not self.extension_path.exists():
            print(f"VS Code extension path not found: {self.extension_path}")
            return
        
        # Find TypeScript and JavaScript files
        for file_path in self.extension_path.rglob("*.ts"):
            if "node_modules" in str(file_path) or ".git" in str(file_path):
                continue
                
            relative_path = str(file_path.relative_to(self.extension_path))
            imports = self.extract_ts_js_imports(file_path)
            
            module_category = self.get_module_category(file_path)
            
            self.file_analysis[relative_path] = {
                'category': module_category,
                'imports': imports,
                'import_count': len(imports)
            }
            
            # Count category-to-category dependencies
            for import_type, import_name in imports:
                import_category = self.categorize_import(import_name)
                self.import_graph[module_category][import_category] += 1
        
        # Also analyze JavaScript files
        for file_path in self.extension_path.rglob("*.js"):
            if "node_modules" in str(file_path) or ".git" in str(file_path):
                continue
                
            relative_path = str(file_path.relative_to(self.extension_path))
            imports = self.extract_ts_js_imports(file_path)
            
            module_category = self.get_module_category(file_path)
            
            self.file_analysis[relative_path] = {
                'category': module_category,
                'imports': imports,
                'import_count': len(imports)
            }
    
    def analyze_package_json(self) -> Dict[str, Any]:
        """Analyze package.json for dependencies."""
        package_json_path = self.extension_path / "package.json"
        
        if not package_json_path.exists():
            return {}
            
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            
            return {
                'dependencies': dependencies,
                'devDependencies': dev_dependencies,
                'total_deps': len(dependencies) + len(dev_dependencies),
                'prod_deps': len(dependencies),
                'dev_deps': len(dev_dependencies)
            }
        except Exception as e:
            print(f"Error reading package.json: {e}")
            return {}
    
    def generate_extension_report(self) -> Dict[str, Any]:
        """Generate comprehensive extension analysis report."""
        package_info = self.analyze_package_json()
        
        # Calculate statistics
        total_files = len(self.file_analysis)
        categories = defaultdict(int)
        import_stats = defaultdict(int)
        
        for file_info in self.file_analysis.values():
            categories[file_info['category']] += 1
            for _, import_name in file_info['imports']:
                import_category = self.categorize_import(import_name)
                import_stats[import_category] += 1
        
        report = {
            'summary': {
                'total_files_analyzed': total_files,
                'file_categories': dict(categories),
                'import_statistics': dict(import_stats),
                'package_dependencies': package_info
            },
            'module_dependencies': dict(self.import_graph),
            'detailed_analysis': self.file_analysis
        }
        
        return report
    
    def generate_extension_coupling_matrix(self) -> str:
        """Generate coupling matrix for VS Code extension."""
        matrix = "VS CODE EXTENSION - MODULE COUPLING MATRIX\n"
        matrix += "=" * 50 + "\n"
        
        categories = sorted(set(cat for file_info in self.file_analysis.values() 
                               for cat in [file_info['category']]))
        
        if not categories:
            matrix += "No module categories found.\n"
            return matrix
        
        matrix += f"{'Source':>12} | "
        for cat in categories[:8]:  # Limit to avoid wide display
            matrix += f"{cat[:8]:>8} "
        matrix += "\n"
        matrix += "-" * (14 + len(categories[:8]) * 9) + "\n"
        
        for source in categories[:8]:
            matrix += f"{source:>12} | "
            for target in categories[:8]:
                count = self.import_graph[source].get('internal', 0) if source != target else 0
                if source == target:
                    matrix += f"{'--':>8} "
                elif count > 0:
                    matrix += f"{count:>8} "
                else:
                    matrix += f"{'':>8} "
            matrix += "\n"
        
        return matrix
    
    def generate_extension_summary(self) -> str:
        """Generate extension analysis summary."""
        report_data = self.generate_extension_report()
        summary = report_data['summary']
        
        summary_text = "VS CODE EXTENSION ANALYSIS SUMMARY\n"
        summary_text += "=" * 40 + "\n\n"
        
        summary_text += f"FILES ANALYZED: {summary['total_files_analyzed']}\n\n"
        
        summary_text += "FILE CATEGORIES:\n"
        summary_text += "-" * 16 + "\n"
        for category, count in summary['file_categories'].items():
            summary_text += f"- {category:>12}: {count} files\n"
        
        summary_text += "\nIMPORT ANALYSIS:\n"
        summary_text += "-" * 16 + "\n"
        for import_type, count in summary['import_statistics'].items():
            summary_text += f"- {import_type:>12}: {count} imports\n"
        
        if summary['package_dependencies']:
            pkg_info = summary['package_dependencies']
            summary_text += f"\nPACKAGE DEPENDENCIES:\n"
            summary_text += "-" * 20 + "\n"
            summary_text += f"- Production: {pkg_info.get('prod_deps', 0)} dependencies\n"
            summary_text += f"- Development: {pkg_info.get('dev_deps', 0)} dependencies\n"
            summary_text += f"- Total: {pkg_info.get('total_deps', 0)} dependencies\n"
        
        summary_text += "\n" + self.generate_extension_coupling_matrix()
        
        return summary_text

def main():
    """Analyze VS Code extension architecture."""
    root_path = Path(__file__).parent.parent
    analyzer = VSCodeExtensionAnalyzer(str(root_path))
    
    # Run analysis
    analyzer.analyze_extension_structure()
    report = analyzer.generate_extension_report()
    
    # Generate summary
    summary = analyzer.generate_extension_summary()
    print(summary)
    
    # Save detailed report
    output_dir = root_path / "analysis"
    output_dir.mkdir(exist_ok=True)
    
    report_file = output_dir / "vscode_extension_analysis.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    summary_file = output_dir / "vscode_extension_summary.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"\nDetailed report saved to: {report_file}")
    print(f"Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()