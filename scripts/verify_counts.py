#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Connascence Safety Analyzer - Verification Script
=================================================

Automatically validates README numbers match demo artifacts using:
- Memory coordination for validation results tracking
- Sequential thinking for comprehensive checking
- CI/CD integration with proper exit codes

Key Requirements Validation:
- README total: 5,743 violations
- Individual counts: Celery=4,630, curl=1,061, Express=52
- File existence: all referenced artifacts present
- JSON validity: all artifact files parse correctly
"""

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Exit codes for CI/CD integration
EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILED = 1
EXIT_CONFIG_ERROR = 2
EXIT_RUNTIME_ERROR = 3

@dataclass
class ValidationResult:
    """Stores validation result for memory coordination"""
    test_name: str
    status: str  # 'PASS', 'FAIL', 'ERROR'
    expected: Any
    actual: Any
    message: str
    error_details: Optional[str] = None

@dataclass
class MemoryCoordination:
    """Memory coordination system for validation tracking"""
    session_id: str
    validation_results: List[ValidationResult]
    sequential_steps: Dict[str, str]
    memory_storage: Dict[str, Any]

    def store_result(self, result: ValidationResult):
        """Store validation result in memory"""
        self.validation_results.append(result)
        self.memory_storage[f"result_{result.test_name}"] = {
            "status": result.status,
            "expected": result.expected,
            "actual": result.actual,
            "message": result.message,
            "timestamp": datetime.now().isoformat()
        }

    def get_summary(self) -> Dict[str, int]:
        """Get validation summary statistics"""
        summary = {"PASS": 0, "FAIL": 0, "ERROR": 0}
        for result in self.validation_results:
            summary[result.status] += 1
        return summary

class SequentialThinkingValidator:
    """
    Sequential thinking implementation for systematic verification:
    1. Parse README.md for violation counts
    2. Parse DEMO_ARTIFACTS/index.json for expected counts
    3. Validate individual artifact files exist and parse correctly
    4. Cross-reference all counts for consistency
    5. Generate comprehensive validation report
    6. Store results in memory for CI coordination
    """

    def __init__(self, base_path: Path, verbose: bool = False):
        self.base_path = base_path
        self.verbose = verbose
        self.memory = MemoryCoordination(
            session_id=f"verification-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            validation_results=[],
            sequential_steps={
                "step_1": "Parse README.md for violation counts",
                "step_2": "Parse DEMO_ARTIFACTS/index.json for expected counts",
                "step_3": "Validate individual artifact files exist and parse correctly",
                "step_4": "Cross-reference all counts for consistency",
                "step_5": "Generate comprehensive validation report",
                "step_6": "Store results in memory for CI coordination"
            },
            memory_storage={}
        )

        # Expected counts from requirements - ENTERPRISE VERIFIED
        self.expected_counts = {
            "celery": 4630,
            "curl": 1061,
            "express": 52,
            "total": 5743
        }

    def log(self, message: str, level: str = "INFO"):
        """Logging with memory coordination"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Replace Unicode emojis with ASCII equivalents for Windows compatibility
        message_clean = (message.replace("🔍", "[SEARCH]")
                              .replace("✅", "[PASS]")
                              .replace("❌", "[FAIL]")
                              .replace("🚀", "[START]")
                              .replace("📄", "[REPORT]")
                              .replace("💾", "[MEMORY]")
                              .replace("🎯", "[TARGET]")
                              .replace("📊", "[STATS]")
                              .replace("💥", "[ERROR]")
                              .replace("🛑", "[STOP]"))

        log_entry = f"[{timestamp}] [{level}] {message_clean}"
        if self.verbose or level in ["ERROR", "FAIL"]:
            try:
                print(log_entry)
            except UnicodeEncodeError:
                # Fallback to ASCII-only logging
                print(log_entry.encode('ascii', errors='replace').decode('ascii'))

        # Store in memory
        if "logs" not in self.memory.memory_storage:
            self.memory.memory_storage["logs"] = []
        self.memory.memory_storage["logs"].append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })

    def step_1_parse_readme(self) -> Dict[str, int]:
        """
        Sequential Step 1: Parse README.md for violation counts
        Extracts: Celery=4,630, curl=1,061, Express=52, Total=5,743
        """
        self.log("[SEARCH] STEP 1: Parsing README.md for violation counts")

        readme_path = self.base_path / "README.md"
        if not readme_path.exists():
            result = ValidationResult(
                test_name="readme_exists",
                status="FAIL",
                expected="README.md exists",
                actual="File not found",
                message="README.md file not found"
            )
            self.memory.store_result(result)
            return {}

        try:
            with open(readme_path, encoding='utf-8') as f:
                content = f.read()

            # Parse violation counts using regex patterns
            counts = {}

            # Pattern 1: "4,630 violations detected" in complete Celery codebase
            celery_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+violations.*?Celery', content, re.IGNORECASE)
            if celery_match:
                counts['celery'] = int(celery_match.group(1).replace(',', ''))

            # Pattern 2: "1,061 violations in curl"
            curl_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+violations.*?curl', content, re.IGNORECASE)
            if curl_match:
                counts['curl'] = int(curl_match.group(1).replace(',', ''))

            # Pattern 3: "52 violations in Express.js"
            express_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+violations.*?Express', content, re.IGNORECASE)
            if express_match:
                counts['express'] = int(express_match.group(1).replace(',', ''))

            # Pattern 4: "5,743 violations" total
            total_match = re.search(r'Successfully detected \*\*(\d{1,3}(?:,\d{3})*) violations\*\*', content)
            if total_match:
                counts['total'] = int(total_match.group(1).replace(',', ''))

            self.memory.memory_storage["readme_parsed_counts"] = counts
            self.log(f"[PASS] STEP 1 COMPLETE: Parsed README counts: {counts}")

            result = ValidationResult(
                test_name="readme_parsing",
                status="PASS",
                expected="Parse violation counts from README",
                actual=counts,
                message=f"Successfully parsed {len(counts)} counts from README"
            )
            self.memory.store_result(result)

            return counts

        except Exception as e:
            result = ValidationResult(
                test_name="readme_parsing",
                status="ERROR",
                expected="Parse README successfully",
                actual=str(e),
                message="Failed to parse README.md",
                error_details=str(e)
            )
            self.memory.store_result(result)
            return {}

    def step_2_parse_index_json(self) -> Dict[str, Any]:
        """
        Sequential Step 2: Parse DEMO_ARTIFACTS/index.json for expected counts
        """
        self.log("[SEARCH] STEP 2: Parsing DEMO_ARTIFACTS/index.json for expected counts")

        index_path = self.base_path / "DEMO_ARTIFACTS" / "index.json"
        if not index_path.exists():
            result = ValidationResult(
                test_name="index_json_exists",
                status="FAIL",
                expected="index.json exists",
                actual="File not found",
                message="DEMO_ARTIFACTS/index.json not found"
            )
            self.memory.store_result(result)
            return {}

        try:
            with open(index_path, encoding='utf-8') as f:
                index_data = json.load(f)

            # Extract counts from index.json structure
            validation_results = index_data.get('validation_results', {})
            totals = index_data.get('totals', {})

            counts = {
                'celery': validation_results.get('celery', {}).get('violations', 0),
                'curl': validation_results.get('curl', {}).get('violations', 0),
                'express': validation_results.get('express', {}).get('violations', 0),
                'total': totals.get('violations', 0)
            }

            self.memory.memory_storage["index_json_counts"] = counts
            self.memory.memory_storage["index_json_data"] = index_data

            self.log(f"[PASS] STEP 2 COMPLETE: Parsed index.json counts: {counts}")

            result = ValidationResult(
                test_name="index_json_parsing",
                status="PASS",
                expected="Parse index.json successfully",
                actual=counts,
                message=f"Successfully parsed index.json with {len(counts)} counts"
            )
            self.memory.store_result(result)

            return index_data

        except Exception as e:
            result = ValidationResult(
                test_name="index_json_parsing",
                status="ERROR",
                expected="Parse index.json successfully",
                actual=str(e),
                message="Failed to parse index.json",
                error_details=str(e)
            )
            self.memory.store_result(result)
            return {}

    def step_3_validate_artifact_files(self, index_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Sequential Step 3: Validate individual artifact files exist and parse correctly
        """
        self.log("[SEARCH] STEP 3: Validating individual artifact files exist and parse correctly")

        artifacts_dir = self.base_path / "DEMO_ARTIFACTS"
        artifact_files = index_data.get('artifacts', [])
        validation_status = {}

        for artifact_file in artifact_files:
            file_path = artifacts_dir / artifact_file

            # Check file existence
            if not file_path.exists():
                result = ValidationResult(
                    test_name=f"artifact_exists_{artifact_file}",
                    status="FAIL",
                    expected=f"{artifact_file} exists",
                    actual="File not found",
                    message=f"Artifact file {artifact_file} not found"
                )
                self.memory.store_result(result)
                validation_status[artifact_file] = False
                continue

            # Validate JSON parsing
            try:
                with open(file_path, encoding='utf-8') as f:
                    artifact_data = json.load(f)

                # Store artifact data in memory
                self.memory.memory_storage[f"artifact_data_{artifact_file}"] = artifact_data

                # Validate required fields
                required_fields = ['tool_version', 'timestamp', 'repository', 'analysis']
                missing_fields = [field for field in required_fields if field not in artifact_data]

                if missing_fields:
                    result = ValidationResult(
                        test_name=f"artifact_structure_{artifact_file}",
                        status="FAIL",
                        expected=f"Required fields: {required_fields}",
                        actual=f"Missing fields: {missing_fields}",
                        message=f"Artifact {artifact_file} missing required fields"
                    )
                    self.memory.store_result(result)
                    validation_status[artifact_file] = False
                else:
                    result = ValidationResult(
                        test_name=f"artifact_valid_{artifact_file}",
                        status="PASS",
                        expected="Valid JSON with required fields",
                        actual="All fields present",
                        message=f"Artifact {artifact_file} is valid"
                    )
                    self.memory.store_result(result)
                    validation_status[artifact_file] = True

            except Exception as e:
                result = ValidationResult(
                    test_name=f"artifact_parsing_{artifact_file}",
                    status="ERROR",
                    expected="Valid JSON file",
                    actual=str(e),
                    message=f"Failed to parse {artifact_file}",
                    error_details=str(e)
                )
                self.memory.store_result(result)
                validation_status[artifact_file] = False

        self.memory.memory_storage["artifact_validation"] = validation_status
        self.log(f"[PASS] STEP 3 COMPLETE: Validated {len(artifact_files)} artifact files")

        return validation_status

    def step_4_cross_reference_counts(self) -> Dict[str, bool]:
        """
        Sequential Step 4: Cross-reference all counts for consistency
        """
        self.log("[SEARCH] STEP 4: Cross-referencing all counts for consistency")

        readme_counts = self.memory.memory_storage.get("readme_parsed_counts", {})
        index_counts = self.memory.memory_storage.get("index_json_counts", {})

        consistency_check = {}

        # Check each expected count
        for key, expected_value in self.expected_counts.items():
            readme_value = readme_counts.get(key, 0)
            index_value = index_counts.get(key, 0)

            # Check README vs Expected
            if readme_value == expected_value:
                result = ValidationResult(
                    test_name=f"readme_count_{key}",
                    status="PASS",
                    expected=expected_value,
                    actual=readme_value,
                    message=f"README {key} count matches expected value"
                )
                consistency_check[f"readme_{key}"] = True
            else:
                result = ValidationResult(
                    test_name=f"readme_count_{key}",
                    status="FAIL",
                    expected=expected_value,
                    actual=readme_value,
                    message=f"README {key} count mismatch"
                )
                consistency_check[f"readme_{key}"] = False
            self.memory.store_result(result)

            # Check Index vs Expected
            if index_value == expected_value:
                result = ValidationResult(
                    test_name=f"index_count_{key}",
                    status="PASS",
                    expected=expected_value,
                    actual=index_value,
                    message=f"Index.json {key} count matches expected value"
                )
                consistency_check[f"index_{key}"] = True
            else:
                result = ValidationResult(
                    test_name=f"index_count_{key}",
                    status="FAIL",
                    expected=expected_value,
                    actual=index_value,
                    message=f"Index.json {key} count mismatch"
                )
                consistency_check[f"index_{key}"] = False
            self.memory.store_result(result)

            # Check README vs Index consistency
            if readme_value == index_value:
                result = ValidationResult(
                    test_name=f"consistency_{key}",
                    status="PASS",
                    expected="README and index counts match",
                    actual=f"Both show {readme_value}",
                    message=f"{key} counts are consistent between sources"
                )
                consistency_check[f"consistency_{key}"] = True
            else:
                result = ValidationResult(
                    test_name=f"consistency_{key}",
                    status="FAIL",
                    expected="README and index counts match",
                    actual=f"README: {readme_value}, Index: {index_value}",
                    message=f"{key} counts are inconsistent between sources"
                )
                consistency_check[f"consistency_{key}"] = False
            self.memory.store_result(result)

        self.memory.memory_storage["consistency_check"] = consistency_check
        self.log(f"[PASS] STEP 4 COMPLETE: Cross-referenced {len(self.expected_counts)} count types")

        return consistency_check

    def step_5_generate_report(self) -> Dict[str, Any]:
        """
        Sequential Step 5: Generate comprehensive validation report
        """
        self.log("[SEARCH] STEP 5: Generating comprehensive validation report")

        summary = self.memory.get_summary()
        total_tests = len(self.memory.validation_results)

        report = {
            "validation_session": {
                "session_id": self.memory.session_id,
                "timestamp": datetime.now().isoformat(),
                "base_path": str(self.base_path)
            },
            "summary": {
                "total_tests": total_tests,
                "passed": summary["PASS"],
                "failed": summary["FAIL"],
                "errors": summary["ERROR"],
                "success_rate": round((summary["PASS"] / total_tests * 100), 2) if total_tests > 0 else 0
            },
            "expected_counts": self.expected_counts,
            "actual_counts": {
                "readme": self.memory.memory_storage.get("readme_parsed_counts", {}),
                "index_json": self.memory.memory_storage.get("index_json_counts", {})
            },
            "sequential_steps": self.memory.sequential_steps,
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "expected": r.expected,
                    "actual": r.actual,
                    "message": r.message,
                    "error_details": r.error_details
                }
                for r in self.memory.validation_results
            ],
            "memory_storage": self.memory.memory_storage
        }

        # Write report to file
        report_path = self.base_path / "DEMO_ARTIFACTS" / "validation_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.log(f"[REPORT] Validation report written to {report_path}")
        except Exception as e:
            self.log(f"[FAIL] Failed to write report: {e}", "ERROR")

        self.memory.memory_storage["validation_report"] = report
        self.log(f"[PASS] STEP 5 COMPLETE: Generated validation report with {total_tests} tests")

        return report

    def step_6_store_memory_coordination(self) -> bool:
        """
        Sequential Step 6: Store results in memory for CI coordination
        """
        self.log("[SEARCH] STEP 6: Storing results in memory for CI coordination")

        memory_path = self.base_path / "DEMO_ARTIFACTS" / "memory_coordination.json"

        try:
            # Update memory coordination file
            memory_data = {
                "coordination_system": "flow-nexus-memory",
                "version": "2.0.0",
                "validation_session": {
                    "session_id": self.memory.session_id,
                    "start_time": datetime.now().isoformat(),
                    "memory_keys": list(self.memory.memory_storage.keys())
                },
                "sequential_thinking": self.memory.sequential_steps,
                "memory_storage": self.memory.memory_storage,
                "validation_summary": self.memory.get_summary()
            }

            # Remove circular references before JSON serialization
            clean_memory_storage = {}
            for key, value in self.memory.memory_storage.items():
                if key != "validation_report":  # Skip circular reference
                    try:
                        json.dumps(value)  # Test serialization
                        clean_memory_storage[key] = value
                    except (TypeError, ValueError):
                        clean_memory_storage[key] = str(value)  # Convert to string if not serializable

            memory_data["memory_storage"] = clean_memory_storage

            with open(memory_path, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)

            self.log(f"[MEMORY] Memory coordination data stored to {memory_path}")
            self.log("[PASS] STEP 6 COMPLETE: Memory coordination storage successful")

            return True

        except Exception as e:
            self.log(f"[FAIL] Failed to store memory coordination: {e}", "ERROR")
            return False

    def run_validation(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute complete sequential thinking validation process
        Returns: (success, report)
        """
        self.log("[START] Starting Sequential Thinking Validation Process")
        self.log("=" * 60)

        try:
            # Execute sequential steps
            self.step_1_parse_readme()
            index_data = self.step_2_parse_index_json()
            self.step_3_validate_artifact_files(index_data)
            self.step_4_cross_reference_counts()
            report = self.step_5_generate_report()
            self.step_6_store_memory_coordination()

            # Determine overall success
            summary = self.memory.get_summary()
            success = summary["FAIL"] == 0 and summary["ERROR"] == 0

            self.log("=" * 60)
            self.log(f"[TARGET] VALIDATION COMPLETE - SUCCESS: {success}")
            self.log(f"[STATS] Results: {summary['PASS']} PASS, {summary['FAIL']} FAIL, {summary['ERROR']} ERROR")

            return success, report

        except Exception as e:
            self.log(f"[ERROR] CRITICAL ERROR in validation process: {e}", "ERROR")
            result = ValidationResult(
                test_name="validation_process",
                status="ERROR",
                expected="Complete validation successfully",
                actual=str(e),
                message="Critical error in validation process",
                error_details=str(e)
            )
            self.memory.store_result(result)

            return False, {"error": str(e)}

def main():
    """Main entry point for CI/CD integration"""
    parser = argparse.ArgumentParser(
        description="Connascence Safety Analyzer - Verification Script"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path.cwd(),
        help="Base path for the project (default: current directory)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report without validation (for testing)"
    )
    parser.add_argument(
        "--generate-validation-report",
        action="store_true",
        help="Generate detailed validation report (alias for --report-only with enhanced output)"
    )

    args = parser.parse_args()

    # Initialize validator
    validator = SequentialThinkingValidator(
        base_path=args.base_path,
        verbose=args.verbose
    )

    try:
        if args.report_only or args.generate_validation_report:
            mode = "validation-report" if args.generate_validation_report else "report-only"
            validator.log(f"[REPORT] Running in {mode} mode")
            # Generate enhanced report for validation-report mode
            report = validator.step_5_generate_report()
            if args.generate_validation_report:
                # Add enhanced validation metadata for CI/CD
                report["validation_metadata"] = {
                    "mode": "validation-report",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": validator.memory.session_id,
                    "enhanced_output": True
                }
            print(json.dumps(report, indent=2))
            sys.exit(EXIT_SUCCESS)
        else:
            # Run full validation
            success, report = validator.run_validation()

            # Print summary for CI/CD
            summary = validator.memory.get_summary()
            print("\n[TARGET] VALIDATION SUMMARY:")
            print(f"   Total Tests: {sum(summary.values())}")
            print(f"   Passed: {summary['PASS']}")
            print(f"   Failed: {summary['FAIL']}")
            print(f"   Errors: {summary['ERROR']}")
            print(f"   Success: {success}")

            # Exit with appropriate code for CI/CD
            if success:
                print("[PASS] All validations passed!")
                sys.exit(EXIT_SUCCESS)
            else:
                print("[FAIL] Validation failed!")
                sys.exit(EXIT_VALIDATION_FAILED)

    except KeyboardInterrupt:
        validator.log("[STOP] Validation interrupted by user", "ERROR")
        sys.exit(EXIT_RUNTIME_ERROR)
    except Exception as e:
        validator.log(f"[ERROR] Unexpected error: {e}", "ERROR")
        sys.exit(EXIT_RUNTIME_ERROR)

if __name__ == "__main__":
    main()
