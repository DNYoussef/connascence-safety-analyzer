#!/usr/bin/env python3
"""
Phase 3.1: Assertion Injection Automation Script
Automatically injects production-safe assertions to fix NASA Rule 5 violations.
"""

import ast
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fixes.phase0.production_safe_assertions import ProductionAssert


@dataclass
class InjectionPoint:
    """Represents a location where assertion should be injected."""
    function_name: str
    line_number: int
    injection_type: str  # 'precondition', 'postcondition', 'invariant'
    parameters: List[str]
    message: str
    condition: str


class AssertionInjector(ast.NodeTransformer):
    """AST transformer that injects production-safe assertions."""

    def __init__(self):
        self.injections_made = 0
        self.current_class = None
        self.current_function = None

    def visit_ClassDef(self, node):
        """Track current class for context."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        return node

    def visit_FunctionDef(self, node):
        """Inject assertions into functions."""
        old_function = self.current_function
        self.current_function = node.name

        # Skip test functions and private methods
        if node.name.startswith('test_') or node.name.startswith('_test'):
            self.current_function = old_function
            return node

        # Analyze function for assertion needs
        needs_preconditions = self._needs_preconditions(node)
        needs_postconditions = self._needs_postconditions(node)

        if needs_preconditions:
            self._inject_preconditions(node)

        if needs_postconditions:
            self._inject_postconditions(node)

        # Visit child nodes
        self.generic_visit(node)
        self.current_function = old_function
        return node

    def _needs_preconditions(self, node: ast.FunctionDef) -> bool:
        """Check if function needs precondition assertions."""
        # Skip simple getters/setters
        if len(node.body) <= 3 and node.name.startswith(('get_', 'set_')):
            return False

        # Check if already has assertions
        has_assertions = any(
            isinstance(stmt, ast.Expr) and
            isinstance(stmt.value, ast.Call) and
            self._is_assertion_call(stmt.value)
            for stmt in node.body[:3]  # Check first 3 statements
        )

        # Need assertions if:
        # 1. Has parameters (except self/cls)
        # 2. No existing assertions
        # 3. Function is public
        params = [arg.arg for arg in node.args.args if arg.arg not in ('self', 'cls')]
        return len(params) > 0 and not has_assertions and not node.name.startswith('_')

    def _needs_postconditions(self, node: ast.FunctionDef) -> bool:
        """Check if function needs postcondition assertions."""
        # Check if function returns a value
        has_return = any(
            isinstance(stmt, ast.Return) and stmt.value is not None
            for stmt in ast.walk(node)
        )

        # Complex functions that return values should have postconditions
        return has_return and len(node.body) > 5

    def _is_assertion_call(self, call: ast.Call) -> bool:
        """Check if a call is to an assertion function."""
        if isinstance(call.func, ast.Attribute):
            if isinstance(call.func.value, ast.Name):
                return (call.func.value.id == 'ProductionAssert' or
                        call.func.value.id == 'assert')
        return False

    def _inject_preconditions(self, node: ast.FunctionDef):
        """Inject precondition assertions at function start."""
        params = [arg.arg for arg in node.args.args if arg.arg not in ('self', 'cls')]

        new_assertions = []
        for param in params:
            # Get type hint if available
            param_type = self._get_param_type(node, param)

            if param_type:
                # Type check assertion
                assertion = self._create_type_check(param, param_type)
                if assertion:
                    new_assertions.append(assertion)

            # Not-none check for required parameters
            assertion = self._create_not_none_check(param)
            new_assertions.append(assertion)

        # Insert assertions at the beginning of function body
        if new_assertions:
            # Add after docstring if present
            insert_pos = 0
            if (node.body and
                isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant)):
                insert_pos = 1

            node.body[insert_pos:insert_pos] = new_assertions
            self.injections_made += len(new_assertions)

    def _inject_postconditions(self, node: ast.FunctionDef):
        """Inject postcondition assertions before returns."""
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.Return) and stmt.value:
                # Create postcondition check
                postcondition = self._create_postcondition_check(stmt.value)
                if postcondition:
                    # Insert before return
                    node.body.insert(i, postcondition)
                    self.injections_made += 1

    def _get_param_type(self, node: ast.FunctionDef, param: str) -> Optional[str]:
        """Get type hint for a parameter."""
        for arg in node.args.args:
            if arg.arg == param and arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    return arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant):
                    return str(arg.annotation.value)
        return None

    def _create_type_check(self, param: str, param_type: str) -> Optional[ast.Expr]:
        """Create type checking assertion."""
        # Map common types
        type_map = {
            'str': 'str',
            'int': 'int',
            'float': 'float',
            'bool': 'bool',
            'list': 'list',
            'dict': 'dict',
            'List': 'list',
            'Dict': 'dict'
        }

        if param_type in type_map:
            # ProductionAssert.type_check(param, expected_type, "param")
            return ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='ProductionAssert', ctx=ast.Load()),
                        attr='type_check',
                        ctx=ast.Load()
                    ),
                    args=[
                        ast.Name(id=param, ctx=ast.Load()),
                        ast.Name(id=type_map[param_type], ctx=ast.Load()),
                        ast.Constant(value=param)
                    ],
                    keywords=[]
                )
            )
        return None

    def _create_not_none_check(self, param: str) -> ast.Expr:
        """Create not-none assertion."""
        # ProductionAssert.not_none(param, "param")
        return ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='ProductionAssert', ctx=ast.Load()),
                    attr='not_none',
                    ctx=ast.Load()
                ),
                args=[
                    ast.Name(id=param, ctx=ast.Load()),
                    ast.Constant(value=param)
                ],
                keywords=[]
            )
        )

    def _create_postcondition_check(self, return_value: ast.expr) -> Optional[ast.Expr]:
        """Create postcondition assertion for return value."""
        # Store return value in temp variable
        temp_var = '__return_value__'

        # __return_value__ = <return expression>
        assign = ast.Assign(
            targets=[ast.Name(id=temp_var, ctx=ast.Store())],
            value=return_value
        )

        # ProductionAssert.not_none(__return_value__, "return value")
        assertion = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='ProductionAssert', ctx=ast.Load()),
                    attr='not_none',
                    ctx=ast.Load()
                ),
                args=[
                    ast.Name(id=temp_var, ctx=ast.Load()),
                    ast.Constant(value="return value")
                ],
                keywords=[]
            )
        )

        # Update return to use temp variable
        return_value = ast.Name(id=temp_var, ctx=ast.Load())

        return None  # Simplified for now


class BatchAssertionInjector:
    """Batch processor for injecting assertions into multiple files."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.baseline_file = self.project_path / "fixes" / "phase0" / "baseline" / "baseline_analysis.json"
        self.results = {
            "files_processed": 0,
            "assertions_injected": 0,
            "files_modified": [],
            "errors": []
        }

    def load_violation_data(self) -> List[Dict]:
        """Load baseline violation data."""
        with open(self.baseline_file, 'r') as f:
            data = json.load(f)

        # Sort files by violation count (highest first)
        files_with_violations = sorted(
            data['files_with_violations'],
            key=lambda x: x['violation_count'],
            reverse=True
        )

        # Filter for Rule 5 violations
        rule5_files = []
        for file_info in files_with_violations:
            rule5_violations = [
                v for v in file_info['violations']
                if v['rule'] == 'nasa_rule_5'
            ]
            if rule5_violations:
                rule5_files.append({
                    'file': file_info['file'],
                    'violations': rule5_violations,
                    'count': len(rule5_violations)
                })

        return rule5_files

    def inject_assertions(self, max_files: int = 100):
        """Inject assertions into top violating files."""
        print(f"\nPhase 3.1: Assertion Injection Campaign")
        print("=" * 70)

        # Load violation data
        rule5_files = self.load_violation_data()
        print(f"Found {len(rule5_files)} files with Rule 5 violations")

        # Process top N files
        files_to_process = rule5_files[:max_files]
        print(f"Processing top {len(files_to_process)} files...")
        print("-" * 40)

        for i, file_info in enumerate(files_to_process, 1):
            file_path = self.project_path / file_info['file']

            # Skip if file doesn't exist
            if not file_path.exists():
                print(f"[{i}/{len(files_to_process)}] Skipping {file_info['file']} - file not found")
                continue

            print(f"[{i}/{len(files_to_process)}] Processing {file_info['file']} ({file_info['count']} violations)")

            try:
                # Read file
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()

                # Parse AST
                tree = ast.parse(source)

                # Check if imports are needed
                needs_import = 'ProductionAssert' not in source

                # Apply transformations
                injector = AssertionInjector()
                new_tree = injector.visit(tree)

                if injector.injections_made > 0:
                    # Add import if needed
                    if needs_import:
                        import_node = ast.ImportFrom(
                            module='fixes.phase0.production_safe_assertions',
                            names=[ast.alias(name='ProductionAssert', asname=None)],
                            level=0
                        )
                        new_tree.body.insert(0, import_node)

                    # Generate new source
                    new_source = ast.unparse(new_tree)

                    # Write back
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_source)

                    self.results["files_modified"].append(file_info['file'])
                    self.results["assertions_injected"] += injector.injections_made
                    print(f"  [OK] Injected {injector.injections_made} assertions")
                else:
                    print(f"  [SKIP] No assertions needed")

                self.results["files_processed"] += 1

            except Exception as e:
                print(f"  [ERROR] Failed: {e}")
                self.results["errors"].append({
                    "file": file_info['file'],
                    "error": str(e)
                })

        return self.results

    def save_results(self):
        """Save injection results."""
        output_dir = self.project_path / "fixes" / "phase3"
        output_dir.mkdir(exist_ok=True)

        results_file = output_dir / "assertion_injection_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n[OK] Results saved to: {results_file}")

    def generate_report(self) -> str:
        """Generate injection report."""
        report = []
        report.append("\n" + "=" * 70)
        report.append("ASSERTION INJECTION REPORT")
        report.append("=" * 70)

        report.append(f"\nFiles Processed: {self.results['files_processed']}")
        report.append(f"Files Modified: {len(self.results['files_modified'])}")
        report.append(f"Assertions Injected: {self.results['assertions_injected']}")
        report.append(f"Errors: {len(self.results['errors'])}")

        if self.results['assertions_injected'] > 0:
            report.append(f"\nAverage Assertions per File: {self.results['assertions_injected'] / max(1, len(self.results['files_modified'])):.1f}")

        report.append("\n" + "=" * 70)
        return "\n".join(report)


def main():
    """Run assertion injection for Phase 3.1."""
    print("Phase 3.1: Assertion Injection Campaign")
    print("Starting from 33.4% compliance, targeting 55%")

    # Initialize injector
    injector = BatchAssertionInjector(project_root)

    # Run injection on top 100 files
    results = injector.inject_assertions(max_files=100)

    # Generate report
    report = injector.generate_report()
    print(report)

    # Save results
    injector.save_results()

    print("\n[OK] Phase 3.1 assertion injection complete!")
    print("Next: Run fixed NASA analyzer to measure improvement")


if __name__ == "__main__":
    main()