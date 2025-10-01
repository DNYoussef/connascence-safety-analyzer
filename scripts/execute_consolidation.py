#!/usr/bin/env python3
"""
File Consolidation Execution Script
Safely consolidates duplicate files and cleans repository structure.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import shutil


class ConsolidationExecutor:
    def __init__(self, repo_root="."):
        self.repo_root = Path(repo_root).resolve()
        self.backup_dir = self.repo_root / "consolidation_backup"
        self.log_file = self.repo_root / "consolidation_log.txt"

    def log(self, message):
        """Log operation with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp}: {message}\n"
        print(f"[{timestamp}] {message}")

        with open(self.log_file, "a") as f:
            f.write(log_entry)

    def backup_file(self, file_path):
        """Create backup of file before deletion"""
        rel_path = Path(file_path).relative_to(self.repo_root)
        backup_path = self.backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        self.log(f"Backed up: {rel_path}")

    def safe_delete(self, file_path):
        """Safely delete file with backup"""
        if not os.path.exists(file_path):
            self.log(f"File not found: {file_path}")
            return False

        self.backup_file(file_path)
        os.remove(file_path)
        self.log(f"Deleted: {Path(file_path).relative_to(self.repo_root)}")
        return True

    def safe_delete_directory(self, dir_path):
        """Safely delete directory with backup"""
        if not os.path.exists(dir_path):
            self.log(f"Directory not found: {dir_path}")
            return False

        # Backup entire directory
        rel_path = Path(dir_path).relative_to(self.repo_root)
        backup_path = self.backup_dir / rel_path
        shutil.copytree(dir_path, backup_path, dirs_exist_ok=True)
        self.log(f"Backed up directory: {rel_path}")

        shutil.rmtree(dir_path)
        self.log(f"Deleted directory: {rel_path}")
        return True

    def get_file_size(self, file_path):
        """Get file size in MB"""
        try:
            return os.path.getsize(file_path) / (1024 * 1024)
        except:
            return 0

    def phase1_remove_large_duplicates(self):
        """Phase 1: Remove large duplicate JSON files"""
        self.log("=== PHASE 1: Removing Large Duplicate JSON Files ===")

        large_duplicates = [
            "final_validation_full.json",
            "reports/final_test_report.json",
            "reports/final_nasa_test.json",
            "reports/validation_analysis_report.json",
            "reports/consolidated_analysis_report.json",
            "reports/nasa_compliance_report.json",
            "reports/connascence_analysis_report.json",
            "reports/complete_analysis_report.json",
        ]

        total_saved = 0
        for file_rel in large_duplicates:
            file_path = self.repo_root / file_rel
            if file_path.exists():
                size_mb = self.get_file_size(file_path)
                total_saved += size_mb
                self.safe_delete(file_path)
            else:
                self.log(f"File not found: {file_rel}")

        self.log(f"Phase 1 completed. Storage saved: {total_saved:.1f} MB")

    def phase2_remove_small_duplicates(self):
        """Phase 2: Remove small test and duplicate files"""
        self.log("=== PHASE 2: Removing Small Duplicates and Test Files ===")

        small_duplicates = [
            "reports/single_file_test.json",
            "reports/fixed_single_file_test.json",
            "reports/full_analysis_report.json",
            "reports/final_mece_test.json",
            "reports/post_consolidation_mece_report.json",
            "reports/mece_duplication_report.json",
            "reports/final_consolidation_mece_report.json",
            "analysis_results_tests.json",
            "analysis_results_experimental.json",
        ]

        total_saved = 0
        for file_rel in small_duplicates:
            file_path = self.repo_root / file_rel
            if file_path.exists():
                size_mb = self.get_file_size(file_path)
                total_saved += size_mb
                self.safe_delete(file_path)

        self.log(f"Phase 2 completed. Storage saved: {total_saved:.1f} MB")

    def phase3_remove_exact_duplicates(self):
        """Phase 3: Remove exact duplicate documentation"""
        self.log("=== PHASE 3: Removing Exact Documentation Duplicates ===")

        exact_duplicates = [
            "enterprise-package/technical/architecture/vscode-extension-validation-report.md",
            "analysis/self-analysis/DOGFOODING_VALIDATION_REPORT.md",
        ]

        for file_rel in exact_duplicates:
            file_path = self.repo_root / file_rel
            if file_path.exists():
                self.safe_delete(file_path)

        self.log("Phase 3 completed. Exact duplicates removed.")

    def phase4_remove_backup_temp(self):
        """Phase 4: Remove backup and temporary files"""
        self.log("=== PHASE 4: Removing Backup and Temporary Files ===")

        temp_directories = ["vscode-extension-backup-20250905-142126", "temp-artifacts"]

        temp_files = ["test_activation.py"]

        total_saved = 0

        # Remove directories
        for dir_rel in temp_directories:
            dir_path = self.repo_root / dir_rel
            if dir_path.exists():
                # Calculate directory size
                for root, dirs, files in os.walk(dir_path):
                    total_saved += sum(os.path.getsize(os.path.join(root, file)) for file in files) / (1024 * 1024)
                self.safe_delete_directory(dir_path)

        # Remove files
        for file_rel in temp_files:
            file_path = self.repo_root / file_rel
            if file_path.exists():
                total_saved += self.get_file_size(file_path)
                self.safe_delete(file_path)

        self.log(f"Phase 4 completed. Storage saved: {total_saved:.1f} MB")

    def phase5_consolidate_folder_analysis(self):
        """Phase 5: Consolidate folder-specific analysis files"""
        self.log("=== PHASE 5: Consolidating Folder Analysis Files ===")

        analysis_files = [
            "analysis_results_analyzer.json",
            "analysis_results_integrations.json",
            "analysis_results_policy.json",
            "analysis_results_mcp.json",
            "analysis_results_security.json",
            "analysis_results_cli.json",
            "analysis_results_config.json",
            "analysis_results_utils.json",
        ]

        # Create consolidated insights document
        consolidated_insights = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": "folder_analysis_consolidation",
                "description": "Consolidated insights from individual folder analyses",
            },
            "folder_insights": {},
        }

        total_saved = 0

        for file_rel in analysis_files:
            file_path = self.repo_root / file_rel
            if file_path.exists():
                try:
                    with open(file_path) as f:
                        data = json.load(f)

                    # Extract key insights
                    folder_name = file_rel.replace("analysis_results_", "").replace(".json", "")
                    insights = self.extract_key_insights(data, folder_name)
                    consolidated_insights["folder_insights"][folder_name] = insights

                    total_saved += self.get_file_size(file_path)
                    self.safe_delete(file_path)

                except Exception as e:
                    self.log(f"Error processing {file_rel}: {e}")

        # Save consolidated insights
        output_path = self.repo_root / "docs" / "CONSOLIDATED_FOLDER_ANALYSIS.json"
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(consolidated_insights, f, indent=2)

        self.log(f"Created consolidated analysis: {output_path.relative_to(self.repo_root)}")
        self.log(f"Phase 5 completed. Storage saved: {total_saved:.1f} MB")

    def extract_key_insights(self, data, folder_name):
        """Extract key insights from analysis data"""
        insights = {"folder": folder_name, "summary": {}}

        # Extract summary information
        if "summary" in data:
            insights["summary"] = data["summary"]

        # Extract critical violations (top 10)
        if "violations" in data:
            critical_violations = [v for v in data["violations"] if v.get("severity") == "critical"][:10]
            insights["critical_violations"] = critical_violations

        # Extract high-severity violations (top 20)
        if "violations" in data:
            high_violations = [v for v in data["violations"] if v.get("severity") == "high"][:20]
            insights["high_severity_violations"] = high_violations

        return insights

    def phase6_clean_summary_reports(self):
        """Phase 6: Clean redundant summary reports"""
        self.log("=== PHASE 6: Cleaning Redundant Summary Reports ===")

        redundant_summaries = [
            "reports/EXECUTIVE_DUPLICATION_SUMMARY.md",
            "reports/COMPREHENSIVE_SENSOR_ANALYSIS_AIVILLAGE.md",
            "reports/ANALYSIS_COMMANDS_AND_FILES.md",
        ]

        for file_rel in redundant_summaries:
            file_path = self.repo_root / file_rel
            if file_path.exists():
                self.safe_delete(file_path)

        self.log("Phase 6 completed. Redundant summaries removed.")

    def generate_consolidation_report(self):
        """Generate final consolidation report"""
        self.log("=== Generating Final Consolidation Report ===")

        report = {
            "consolidation_completed": datetime.now().isoformat(),
            "backup_location": str(self.backup_dir.relative_to(self.repo_root)),
            "log_location": str(self.log_file.relative_to(self.repo_root)),
            "phases_completed": [
                "Phase 1: Large duplicate JSON files removed",
                "Phase 2: Small duplicates and test files removed",
                "Phase 3: Exact documentation duplicates removed",
                "Phase 4: Backup and temporary files removed",
                "Phase 5: Folder analysis files consolidated",
                "Phase 6: Redundant summary reports cleaned",
            ],
            "key_files_preserved": [
                "FULL_CODEBASE_ANALYSIS.json",
                "final_validation_nasa.json",
                "docs/CRITICAL_VIOLATIONS_ACTION_PLAN.json",
                "docs/VIOLATION_HEATMAPS.json",
                "docs/integration-analysis/",
                "enterprise-package/validation/",
            ],
        }

        report_path = self.repo_root / "docs" / "CONSOLIDATION_COMPLETION_REPORT.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.log(f"Consolidation report generated: {report_path.relative_to(self.repo_root)}")

    def execute_full_consolidation(self):
        """Execute complete consolidation process"""
        self.log("Starting File Consolidation Process")
        self.log(f"Repository root: {self.repo_root}")
        self.log(f"Backup directory: {self.backup_dir}")

        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)

        try:
            self.phase1_remove_large_duplicates()
            self.phase2_remove_small_duplicates()
            self.phase3_remove_exact_duplicates()
            self.phase4_remove_backup_temp()
            self.phase5_consolidate_folder_analysis()
            self.phase6_clean_summary_reports()
            self.generate_consolidation_report()

            self.log("=== CONSOLIDATION COMPLETED SUCCESSFULLY ===")
            self.log("Review the consolidation log and backup directory before committing changes")

        except Exception as e:
            self.log(f"ERROR during consolidation: {e}")
            self.log("Check backup directory for recovery if needed")
            raise


def main():
    """Main execution function"""
    consolidator = ConsolidationExecutor()
    consolidator.execute_full_consolidation()


if __name__ == "__main__":
    main()
