#!/usr/bin/env python3
"""
Improved Assertion Injector - Regex-Based
Injects production-safe assertions without damaging file formatting.
"""

import json
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple


class ImprovedAssertionInjector:
    """Regex-based assertion injector that preserves formatting."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.baseline_file = self.project_path / "fixes" / "phase0" / "baseline" / "baseline_analysis.json"
        self.results = {"files_processed": 0, "assertions_injected": 0, "files_modified": [], "errors": []}

    def load_violation_data(self) -> List[Dict]:
        """Load Rule 5 violations from baseline."""
        with open(self.baseline_file) as f:
            data = json.load(f)

        # Filter for Rule 5 violations in project files (not test_packages)
        rule5_files = []
        for file_info in data["files_with_violations"]:
            # Skip test_packages
            if file_info["file"].startswith("test_packages"):
                continue

            rule5_violations = [v for v in file_info["violations"] if v["rule"] == "nasa_rule_5"]
            if rule5_violations:
                rule5_files.append(
                    {"file": file_info["file"], "violations": rule5_violations, "count": len(rule5_violations)}
                )

        # Sort by violation count
        return sorted(rule5_files, key=lambda x: x["count"], reverse=True)

    def find_function_signature(self, content: str, line_number: int) -> Optional[Tuple[str, List[str]]]:
        """Find function signature near the given line."""
        lines = content.split("\n")

        # Search backwards from line_number to find function def
        for i in range(max(0, line_number - 1), max(0, line_number - 20), -1):
            line = lines[i].strip()
            if line.startswith("def "):
                # Extract function name and parameters
                match = re.match(r"def\s+(\w+)\s*\((.*?)\):", line)
                if match:
                    func_name = match.group(1)
                    params = match.group(2).strip()

                    # Parse parameters
                    if params:
                        param_list = [p.split(":")[0].split("=")[0].strip() for p in params.split(",")]
                        # Filter out self, cls
                        param_list = [p for p in param_list if p and p not in ("self", "cls")]
                    else:
                        param_list = []

                    return (func_name, param_list)

        return None

    def create_assertion_code(self, func_name: str, params: List[str], indent: str) -> str:
        """Create assertion code for function parameters."""
        assertions = []

        # Add import if needed
        import_line = "from fixes.phase0.production_safe_assertions import ProductionAssert\n"

        # Create precondition assertions for each parameter
        for param in params:
            # Not-none check
            assertion = f"{indent}ProductionAssert.not_none({param}, '{param}')"
            assertions.append(assertion)

        return assertions

    def inject_assertions_regex(self, file_path: Path) -> int:
        """Inject assertions using regex pattern matching."""
        # Read file
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check if import already exists
        has_import = "from fixes.phase0.production_safe_assertions import ProductionAssert" in content

        # Count assertions injected
        injections = 0
        modified_content = content
        lines_to_add = {}

        # Find function definitions
        pattern = r"^(\s*)(def\s+(\w+)\s*\((.*?)\):)\s*$"
        for match in re.finditer(pattern, content, re.MULTILINE):
            indent = match.group(1)
            func_line = match.group(2)
            func_name = match.group(3)
            params_str = match.group(4)

            # Skip test functions and private methods
            if func_name.startswith(("test_", "_test")) or func_name.startswith("_"):
                continue

            # Parse parameters
            params = []
            if params_str.strip():
                for p in params_str.split(","):
                    param = p.split(":")[0].split("=")[0].strip()
                    if param and param not in ("self", "cls"):
                        params.append(param)

            # Only inject if function has parameters
            if not params:
                continue

            # Create assertions
            assertion_lines = []
            for param in params:
                assertion = f"{indent}    ProductionAssert.not_none({param}, '{param}')\n"
                assertion_lines.append(assertion)

            # Find where to insert (after function def and docstring)
            func_start_pos = match.end()

            # Check for docstring
            remaining = content[func_start_pos:]
            docstring_match = re.match(r'\s*(""".*?"""|\'\'\'.*?\'\'\')', remaining, re.DOTALL)

            if docstring_match:
                insert_pos = func_start_pos + docstring_match.end()
            else:
                # Insert right after function definition
                insert_pos = func_start_pos

            # Store position and assertions to add
            if insert_pos not in lines_to_add:
                lines_to_add[insert_pos] = []
            lines_to_add[insert_pos].extend(assertion_lines)
            injections += len(assertion_lines)

        # Apply insertions (in reverse order to maintain positions)
        if lines_to_add:
            sorted_positions = sorted(lines_to_add.keys(), reverse=True)
            for pos in sorted_positions:
                assertions_text = "".join(lines_to_add[pos])
                modified_content = modified_content[:pos] + "\n" + assertions_text + modified_content[pos:]

            # Add import at the top if not present
            if not has_import:
                # Find first import or beginning of file
                first_import = re.search(r"^import |^from ", modified_content, re.MULTILINE)
                if first_import:
                    insert_pos = first_import.start()
                else:
                    # After shebang/encoding if present
                    lines = modified_content.split("\n")
                    insert_line = 0
                    for i, line in enumerate(lines):
                        if line.startswith("#") or not line.strip():
                            insert_line = i + 1
                        else:
                            break
                    insert_pos = len("\n".join(lines[:insert_line]))

                modified_content = (
                    modified_content[:insert_pos]
                    + "from fixes.phase0.production_safe_assertions import ProductionAssert\n"
                    + modified_content[insert_pos:]
                )

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_content)

        return injections

    def process_files(self, max_files: int = 50):
        """Process files and inject assertions."""
        print("\nImproved Assertion Injection (Regex-Based)")
        print("=" * 70)

        # Load violations
        rule5_files = self.load_violation_data()
        print(f"Found {len(rule5_files)} project files with Rule 5 violations")
        print("(Excluding test_packages)")

        # Process top N files
        files_to_process = rule5_files[:max_files]
        print(f"\nProcessing top {len(files_to_process)} files...")
        print("-" * 40)

        for i, file_info in enumerate(files_to_process, 1):
            file_path = self.project_path / file_info["file"]

            if not file_path.exists():
                print(f"[{i}/{len(files_to_process)}] Skipping {file_info['file']} - not found")
                continue

            print(f"[{i}/{len(files_to_process)}] Processing {file_info['file']} ({file_info['count']} violations)")

            try:
                # Inject assertions
                injections = self.inject_assertions_regex(file_path)

                if injections > 0:
                    self.results["files_modified"].append(file_info["file"])
                    self.results["assertions_injected"] += injections
                    print(f"  [OK] Injected {injections} assertions")
                else:
                    print("  [SKIP] No suitable functions found")

                self.results["files_processed"] += 1

            except Exception as e:
                print(f"  [ERROR] {e}")
                self.results["errors"].append({"file": file_info["file"], "error": str(e)})

        return self.results

    def save_results(self):
        """Save injection results."""
        output_file = self.project_path / "fixes" / "phase3" / "improved_injection_results.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n[OK] Results saved to: {output_file}")

    def generate_report(self) -> str:
        """Generate injection report."""
        report = []
        report.append("\n" + "=" * 70)
        report.append("IMPROVED ASSERTION INJECTION REPORT")
        report.append("=" * 70)

        report.append(f"\nFiles Processed: {self.results['files_processed']}")
        report.append(f"Files Modified: {len(self.results['files_modified'])}")
        report.append(f"Assertions Injected: {self.results['assertions_injected']}")
        report.append(f"Errors: {len(self.results['errors'])}")

        if self.results["assertions_injected"] > 0:
            avg = self.results["assertions_injected"] / max(1, len(self.results["files_modified"]))
            report.append(f"\nAverage Assertions per File: {avg:.1f}")

        report.append("\n" + "=" * 70)
        return "\n".join(report)


def main():
    """Run improved assertion injection."""
    project_root = Path.cwd()

    print("Phase 3.1: Improved Assertion Injection")
    print("Using regex-based approach to preserve formatting")

    # Initialize injector
    injector = ImprovedAssertionInjector(project_root)

    # Process top 50 project files
    results = injector.process_files(max_files=50)

    # Generate report
    report = injector.generate_report()
    print(report)

    # Save results
    injector.save_results()

    print("\n[OK] Improved assertion injection complete!")
    print("Files are preserved with original formatting")


if __name__ == "__main__":
    main()
