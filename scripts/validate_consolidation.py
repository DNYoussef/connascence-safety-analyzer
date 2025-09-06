#!/usr/bin/env python3
"""
Consolidation Validation Script
Validates that critical content is preserved after file consolidation.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import sys


class ConsolidationValidator:
    def __init__(self, repo_root="."):
        self.repo_root = Path(repo_root).resolve()
        self.validation_report = {
            "validation_timestamp": datetime.now().isoformat(),
            "checks": {},
            "critical_files_status": {},
            "content_preservation": {},
            "warnings": [],
            "errors": []
        }

    def log_check(self, check_name, status, details=""):
        """Log validation check result"""
        self.validation_report["checks"][check_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        print(f"✓ {check_name}: {status}" + (f" - {details}" if details else ""))

    def add_warning(self, message):
        """Add warning to validation report"""
        self.validation_report["warnings"].append(message)
        print(f"⚠️  WARNING: {message}")

    def add_error(self, message):
        """Add error to validation report"""
        self.validation_report["errors"].append(message)
        print(f"❌ ERROR: {message}")

    def check_critical_files_exist(self):
        """Verify critical files are preserved"""
        critical_files = [
            "FULL_CODEBASE_ANALYSIS.json",
            "final_validation_nasa.json",
            "docs/CRITICAL_VIOLATIONS_ACTION_PLAN.json",
            "docs/VIOLATION_HEATMAPS.json",
            "docs/integration-analysis/implementation-roadmap.md",
            "docs/integration-analysis/architecture-diagram.md",
            "docs/integration-analysis/gap-analysis-report.md",
            "enterprise-package/validation/ACCURACY_REPORT.md"
        ]

        missing_files = []
        existing_files = []

        for file_rel in critical_files:
            file_path = self.repo_root / file_rel
            if file_path.exists():
                existing_files.append(file_rel)
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                self.validation_report["critical_files_status"][file_rel] = {
                    "exists": True,
                    "size_mb": round(size_mb, 2)
                }
            else:
                missing_files.append(file_rel)
                self.validation_report["critical_files_status"][file_rel] = {
                    "exists": False,
                    "size_mb": 0
                }

        if missing_files:
            for file_rel in missing_files:
                self.add_error(f"Critical file missing: {file_rel}")
            self.log_check("critical_files_exist", "FAILED", f"{len(missing_files)} missing files")
        else:
            self.log_check("critical_files_exist", "PASSED", f"All {len(critical_files)} critical files present")

        return len(missing_files) == 0

    def check_master_analysis_integrity(self):
        """Verify master analysis file contains expected data"""
        master_file = self.repo_root / "FULL_CODEBASE_ANALYSIS.json"

        if not master_file.exists():
            self.add_error("Master analysis file missing")
            self.log_check("master_analysis_integrity", "FAILED", "File not found")
            return False

        try:
            with open(master_file) as f:
                data = json.load(f)

            # Check required fields
            required_fields = ["metadata", "summary", "violations"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                self.add_error(f"Master analysis missing fields: {missing_fields}")
                self.log_check("master_analysis_integrity", "FAILED", f"Missing fields: {missing_fields}")
                return False

            # Check data quality
            total_violations = data["summary"].get("total_violations", 0)
            violations_count = len(data["violations"])

            if total_violations == 0 or violations_count == 0:
                self.add_warning("Master analysis appears to have no violations - verify this is correct")

            self.validation_report["content_preservation"]["master_analysis"] = {
                "total_violations": total_violations,
                "violations_in_data": violations_count,
                "critical_violations": data["summary"].get("critical_violations", 0),
                "quality_score": data["summary"].get("overall_quality_score", 0)
            }

            self.log_check("master_analysis_integrity", "PASSED",
                         f"Contains {total_violations} violations, quality score: {data['summary'].get('overall_quality_score', 0)}")
            return True

        except json.JSONDecodeError as e:
            self.add_error(f"Master analysis JSON is corrupted: {e}")
            self.log_check("master_analysis_integrity", "FAILED", "JSON decode error")
            return False
        except Exception as e:
            self.add_error(f"Error validating master analysis: {e}")
            self.log_check("master_analysis_integrity", "FAILED", str(e))
            return False

    def check_nasa_validation_integrity(self):
        """Verify NASA validation file contains expected data"""
        nasa_file = self.repo_root / "final_validation_nasa.json"

        if not nasa_file.exists():
            self.add_error("NASA validation file missing")
            self.log_check("nasa_validation_integrity", "FAILED", "File not found")
            return False

        try:
            with open(nasa_file) as f:
                data = json.load(f)

            # Check NASA-specific content
            if "metadata" in data and "nasa" in str(data).lower():
                self.validation_report["content_preservation"]["nasa_validation"] = {
                    "file_size_mb": round(os.path.getsize(nasa_file) / (1024 * 1024), 2),
                    "contains_nasa_content": True
                }
                self.log_check("nasa_validation_integrity", "PASSED", "NASA validation data preserved")
                return True
            else:
                self.add_warning("NASA validation file may not contain expected NASA-specific content")
                self.log_check("nasa_validation_integrity", "WARNING", "NASA content questionable")
                return True

        except json.JSONDecodeError as e:
            self.add_error(f"NASA validation JSON is corrupted: {e}")
            self.log_check("nasa_validation_integrity", "FAILED", "JSON decode error")
            return False
        except Exception as e:
            self.add_error(f"Error validating NASA file: {e}")
            self.log_check("nasa_validation_integrity", "FAILED", str(e))
            return False

    def check_documentation_structure(self):
        """Verify documentation structure is maintained"""
        required_docs = [
            "docs/integration-analysis",
            "docs/analysis",
            "docs/reports",
            "enterprise-package/validation"
        ]

        missing_dirs = []
        existing_dirs = []

        for dir_rel in required_docs:
            dir_path = self.repo_root / dir_rel
            if dir_path.exists() and dir_path.is_dir():
                existing_dirs.append(dir_rel)
                # Count files in directory
                file_count = sum(1 for f in dir_path.rglob("*") if f.is_file())
                self.validation_report["content_preservation"][f"dir_{dir_rel.replace('/', '_')}"] = {
                    "exists": True,
                    "file_count": file_count
                }
            else:
                missing_dirs.append(dir_rel)

        if missing_dirs:
            for dir_rel in missing_dirs:
                self.add_warning(f"Expected directory missing: {dir_rel}")
            self.log_check("documentation_structure", "WARNING", f"{len(missing_dirs)} directories missing")
        else:
            self.log_check("documentation_structure", "PASSED", "All required directories exist")

        return len(missing_dirs) == 0

    def check_duplicate_removal(self):
        """Verify duplicate files have been removed"""
        expected_removed_files = [
            "final_validation_full.json",
            "reports/final_test_report.json",
            "reports/consolidated_analysis_report.json",
            "enterprise-package/technical/architecture/vscode-extension-validation-report.md",
            "analysis/self-analysis/DOGFOODING_VALIDATION_REPORT.md",
            "vscode-extension-backup-20250905-142126",
            "temp-artifacts",
            "test_activation.py"
        ]

        still_exists = []
        properly_removed = []

        for item_rel in expected_removed_files:
            item_path = self.repo_root / item_rel
            if item_path.exists():
                still_exists.append(item_rel)
            else:
                properly_removed.append(item_rel)

        if still_exists:
            for item_rel in still_exists:
                self.add_warning(f"Expected removed file/directory still exists: {item_rel}")
            self.log_check("duplicate_removal", "WARNING", f"{len(still_exists)} items not removed")
        else:
            self.log_check("duplicate_removal", "PASSED", f"{len(properly_removed)} duplicates properly removed")

        return len(still_exists) == 0

    def check_storage_savings(self):
        """Calculate storage savings estimate"""
        current_analysis_files = []
        total_size = 0

        # Find remaining analysis JSON files
        for json_file in self.repo_root.rglob("*.json"):
            if any(keyword in str(json_file).lower() for keyword in ["analysis", "validation", "report"]):
                if json_file.is_file():
                    size_mb = os.path.getsize(json_file) / (1024 * 1024)
                    total_size += size_mb
                    current_analysis_files.append({
                        "file": str(json_file.relative_to(self.repo_root)),
                        "size_mb": round(size_mb, 2)
                    })

        self.validation_report["content_preservation"]["storage_analysis"] = {
            "remaining_analysis_files": len(current_analysis_files),
            "total_size_mb": round(total_size, 2),
            "files": current_analysis_files[:10]  # Top 10 by discovery order
        }

        if total_size < 100:  # Expected significant reduction
            self.log_check("storage_savings", "PASSED", f"Analysis files reduced to {total_size:.1f} MB")
        else:
            self.add_warning(f"Storage reduction may be less than expected: {total_size:.1f} MB remaining")
            self.log_check("storage_savings", "WARNING", "Less reduction than expected")

        return True

    def check_consolidation_artifacts(self):
        """Check for consolidation process artifacts"""
        expected_artifacts = [
            "docs/FILE_CONSOLIDATION_EXECUTION_PLAN.md",
            "docs/CONSOLIDATION_DECISION_MATRIX.md",
            "scripts/execute_consolidation.py",
            "scripts/validate_consolidation.py"
        ]

        missing_artifacts = []
        existing_artifacts = []

        for artifact_rel in expected_artifacts:
            artifact_path = self.repo_root / artifact_rel
            if artifact_path.exists():
                existing_artifacts.append(artifact_rel)
            else:
                missing_artifacts.append(artifact_rel)

        if missing_artifacts:
            for artifact_rel in missing_artifacts:
                self.add_warning(f"Consolidation artifact missing: {artifact_rel}")

        self.log_check("consolidation_artifacts", "INFO", f"{len(existing_artifacts)} artifacts present")
        return True

    def generate_validation_report(self):
        """Generate final validation report"""
        # Calculate overall status
        error_count = len(self.validation_report["errors"])
        warning_count = len(self.validation_report["warnings"])

        if error_count > 0:
            overall_status = "FAILED"
        elif warning_count > 0:
            overall_status = "PASSED_WITH_WARNINGS"
        else:
            overall_status = "PASSED"

        self.validation_report["overall_status"] = overall_status
        self.validation_report["summary"] = {
            "total_checks": len(self.validation_report["checks"]),
            "errors": error_count,
            "warnings": warning_count
        }

        # Save validation report
        report_path = self.repo_root / "docs" / "CONSOLIDATION_VALIDATION_REPORT.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(self.validation_report, f, indent=2)

        print(f"\n{'='*60}")
        print("CONSOLIDATION VALIDATION COMPLETE")
        print(f"Overall Status: {overall_status}")
        print(f"Errors: {error_count}, Warnings: {warning_count}")
        print(f"Validation report saved: {report_path.relative_to(self.repo_root)}")
        print(f"{'='*60}\n")

        return overall_status == "PASSED" or overall_status == "PASSED_WITH_WARNINGS"

    def run_full_validation(self):
        """Run complete validation suite"""
        print("Starting Consolidation Validation...")
        print(f"Repository: {self.repo_root}")
        print("-" * 60)

        # Run all validation checks
        checks = [
            self.check_critical_files_exist,
            self.check_master_analysis_integrity,
            self.check_nasa_validation_integrity,
            self.check_documentation_structure,
            self.check_duplicate_removal,
            self.check_storage_savings,
            self.check_consolidation_artifacts
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                self.add_error(f"Validation check failed: {check.__name__}: {e}")

        return self.generate_validation_report()

def main():
    """Main validation execution"""
    validator = ConsolidationValidator()
    success = validator.run_full_validation()

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
