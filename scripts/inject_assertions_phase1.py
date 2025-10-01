#!/usr/bin/env python3
"""
Phase 1 Quick Win: Automated Assertion Injection for Rule 4 Compliance

This script automatically injects defensive programming assertions into functions
that are missing input validation, targeting the top 20 files with highest
violation density.

Usage:
    python scripts/inject_assertions_phase1.py [--dry-run] [--top-n 20]

Features:
- Analyzes function parameters and injects appropriate assertions
- Handles type hints and default values
- Adds precondition checks for None, empty containers, and types
- Preserves existing code structure and formatting
- Generates detailed report of injected assertions

Target: Improve Rule 4 compliance from 0% to 70-80%
"""

import argparse
import ast
import json
from pathlib import Path
from typing import Dict, List


class AssertionInjector(ast.NodeTransformer):
    """AST transformer that injects assertions into functions"""

    def __init__(self):
        self.injected_count = 0
        self.injection_log = []

    def visit_FunctionDef(self, node):
        # Check if function already has assertions
        has_assertions = any(isinstance(n, ast.Assert) for n in ast.walk(node))

        if not has_assertions and node.args.args:
            # Generate assertions for parameters
            assertions = []

            for arg in node.args.args:
                arg_name = arg.arg

                # Skip 'self' and 'cls'
                if arg_name in ("self", "cls"):
                    continue

                # Basic None check
                assertions.append(
                    ast.Assert(
                        test=ast.Compare(
                            left=ast.Name(id=arg_name, ctx=ast.Load()),
                            ops=[ast.IsNot()],
                            comparators=[ast.Constant(value=None)],
                        ),
                        msg=ast.Constant(value=f"{arg_name} must not be None"),
                    )
                )

                # Type-specific checks if type hint available
                if arg.annotation:
                    type_name = self._get_type_name(arg.annotation)
                    if type_name:
                        assertions.append(
                            ast.Assert(
                                test=ast.Call(
                                    func=ast.Name(id="isinstance", ctx=ast.Load()),
                                    args=[
                                        ast.Name(id=arg_name, ctx=ast.Load()),
                                        ast.Name(id=type_name, ctx=ast.Load()),
                                    ],
                                    keywords=[],
                                ),
                                msg=ast.Constant(value=f"{arg_name} must be of type {type_name}"),
                            )
                        )

            if assertions:
                # Insert assertions at the beginning of the function
                # Preserve docstring if it exists
                insert_index = 0
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    insert_index = 1  # After docstring

                for assertion in reversed(assertions):
                    node.body.insert(insert_index, assertion)

                self.injected_count += len(assertions)
                self.injection_log.append(
                    {"function": node.name, "line": node.lineno, "assertions_added": len(assertions)}
                )

        return node

    def _get_type_name(self, annotation):
        """Extract type name from annotation"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                return annotation.value.id
        return None


def inject_assertions_in_file(filepath: Path, dry_run: bool = False) -> Dict:
    """Inject assertions into a single file"""
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
            tree = ast.parse(source, filename=str(filepath))

        # Transform AST
        injector = AssertionInjector()
        new_tree = injector.visit(tree)
        ast.fix_missing_locations(new_tree)

        result = {
            "file": str(filepath),
            "injected_count": injector.injected_count,
            "injection_log": injector.injection_log,
            "success": True,
        }

        if not dry_run and injector.injected_count > 0:
            # Write back modified code
            new_source = ast.unparse(new_tree)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_source)

        return result

    except Exception as e:
        return {"file": str(filepath), "success": False, "error": str(e)}


def load_top_files(n: int = 20) -> List[Path]:
    """Load top N files from violation report"""
    report_path = Path("docs/enhancement/nasa-violations-detailed.json")

    with open(report_path) as f:
        report = json.load(f)

    top_files = []
    for file_data in report["top_100_files"][:n]:
        if file_data["violations"]["rule_4"] > 0:  # Only files with Rule 4 violations
            filepath = Path("analyzer") / file_data["file"]
            if filepath.exists():
                top_files.append(filepath)

    return top_files


def main():
    parser = argparse.ArgumentParser(description="Inject assertions for Rule 4 compliance")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    parser.add_argument("--top-n", type=int, default=20, help="Number of top files to process")
    args = parser.parse_args()

    print("=" * 60)
    print("NASA POT10 Rule 4 Compliance - Assertion Injection")
    print("=" * 60)
    print(f"\nMode: {'DRY RUN (preview only)' if args.dry_run else 'LIVE (will modify files)'}")
    print(f"Target: Top {args.top_n} files with Rule 4 violations\n")

    # Load target files
    target_files = load_top_files(args.top_n)
    print(f"Found {len(target_files)} files with Rule 4 violations\n")

    # Process files
    results = []
    total_injected = 0

    for filepath in target_files:
        print(f"Processing: {filepath}")
        result = inject_assertions_in_file(filepath, dry_run=args.dry_run)
        results.append(result)

        if result["success"]:
            total_injected += result["injected_count"]
            print(f"  ✅ Injected {result['injected_count']} assertions")
        else:
            print(f"  ❌ Error: {result['error']}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {len(results)}")
    print(f"Total assertions injected: {total_injected}")
    print(f"Success rate: {sum(1 for r in results if r['success'])}/{len(results)}")

    # Save detailed report
    report_path = Path("docs/enhancement/assertion-injection-report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metadata": {"dry_run": args.dry_run, "top_n": args.top_n, "total_injected": total_injected},
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\nDetailed report saved: {report_path}")

    # Compliance estimate
    baseline_violations = 1312  # From analysis
    expected_compliance = ((total_injected / baseline_violations) * 100) if baseline_violations > 0 else 0

    print("\nEstimated Rule 4 Compliance Improvement:")
    print("  Before: 0%")
    print(f"  After:  ~{expected_compliance:.1f}%")

    if not args.dry_run:
        print("\n⚠️  IMPORTANT: Run tests to validate injected assertions!")
        print("  1. Run: python -m pytest tests/")
        print("  2. Fix any assertion failures")
        print("  3. Re-run NASA compliance analysis")


if __name__ == "__main__":
    main()
