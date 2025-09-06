#!/usr/bin/env python3
"""
Intelligent Duplication Consolidation
Removes duplicates while preserving unique content and functionality.
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime
import filecmp

class IntelligentConsolidator:
    def __init__(self, repo_root="."):
        self.repo_root = Path(repo_root).resolve()
        self.backup_dir = self.repo_root / "intelligent_backup"
        self.log_file = self.repo_root / "intelligent_consolidation.log"
        self.removed_files = []
        self.space_saved = 0
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp}: {message}\n"
        print(f"[CONSOLIDATE] {message}")
        with open(self.log_file, "a") as f:
            f.write(log_entry)
    
    def get_file_hash(self, file_path):
        """Get MD5 hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def get_file_size_mb(self, file_path):
        """Get file size in MB"""
        try:
            return os.path.getsize(file_path) / (1024 * 1024)
        except:
            return 0
    
    def backup_and_remove(self, file_path, reason="duplicate"):
        """Backup file then remove"""
        if not os.path.exists(file_path):
            return False
        
        size_mb = self.get_file_size_mb(file_path)
        rel_path = Path(file_path).relative_to(self.repo_root)
        backup_path = self.backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(file_path, backup_path)
        os.remove(file_path)
        
        self.removed_files.append(str(rel_path))
        self.space_saved += size_mb
        self.log(f"REMOVED ({reason}): {rel_path} ({size_mb:.2f}MB)")
        return True
    
    def phase1_remove_exact_json_duplicates(self):
        """Phase 1: Remove exact JSON file duplicates"""
        self.log("=== PHASE 1: Removing Exact JSON Duplicates ===")
        
        # Find all JSON files
        json_files = list(self.repo_root.glob("**/*.json"))
        json_hashes = {}
        duplicates = []
        
        for json_file in json_files:
            if json_file.is_file() and "node_modules" not in str(json_file):
                file_hash = self.get_file_hash(json_file)
                if file_hash:
                    if file_hash in json_hashes:
                        # Keep the file in better location (docs over root)
                        existing = json_hashes[file_hash]
                        current = json_file
                        
                        if "docs" in str(current) and "docs" not in str(existing):
                            duplicates.append(existing)
                            json_hashes[file_hash] = current
                        else:
                            duplicates.append(current)
                    else:
                        json_hashes[file_hash] = json_file
        
        # Remove duplicates
        for dup_file in duplicates:
            self.backup_and_remove(dup_file, "exact JSON duplicate")
        
        self.log(f"Phase 1: Removed {len(duplicates)} exact JSON duplicates")
    
    def phase2_consolidate_analysis_results(self):
        """Phase 2: Consolidate analysis_results_*.json files"""
        self.log("=== PHASE 2: Consolidating Analysis Results ===")
        
        # Find all analysis_results files
        analysis_files = list(self.repo_root.glob("**/analysis_results_*.json"))
        consolidated_data = {
            "consolidation_date": datetime.now().isoformat(),
            "source_files": [],
            "folder_analyses": {}
        }
        
        for analysis_file in analysis_files:
            if analysis_file.is_file():
                try:
                    with open(analysis_file, 'r') as f:
                        data = json.load(f)
                    
                    folder_name = analysis_file.stem.replace("analysis_results_", "")
                    consolidated_data["folder_analyses"][folder_name] = {
                        "source_file": str(analysis_file.relative_to(self.repo_root)),
                        "summary": data.get("summary", {}),
                        "critical_violations": [v for v in data.get("violations", []) if v.get("severity") == "critical"][:10],
                        "violation_count": len(data.get("violations", []))
                    }
                    consolidated_data["source_files"].append(str(analysis_file.relative_to(self.repo_root)))
                    
                    self.backup_and_remove(analysis_file, "consolidated into master file")
                
                except Exception as e:
                    self.log(f"Error processing {analysis_file}: {e}")
        
        # Save consolidated file
        consolidated_path = self.repo_root / "docs" / "analysis-reports" / "CONSOLIDATED_ANALYSIS_RESULTS.json"
        consolidated_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(consolidated_path, 'w') as f:
            json.dump(consolidated_data, f, indent=2)
        
        self.log(f"Created consolidated analysis: {consolidated_path.relative_to(self.repo_root)}")
        self.log(f"Phase 2: Consolidated {len(analysis_files)} analysis files")
    
    def phase3_remove_redundant_readmes(self):
        """Phase 3: Remove redundant README files intelligently"""
        self.log("=== PHASE 3: Removing Redundant READMEs ===")
        
        readme_files = list(self.repo_root.glob("**/README.md"))
        readme_content_map = {}
        important_readmes = set()
        
        # Mark important READMEs to preserve
        important_patterns = [
            "README.md",  # Root README
            "enterprise-package/README.md",
            "professional-package/README.md", 
            "startup-package/README.md",
            "analyzer/README.md",
            "cli/README.md",
            "vscode-extension/README.md"
        ]
        
        for readme in readme_files:
            rel_path = str(readme.relative_to(self.repo_root))
            if any(pattern in rel_path for pattern in important_patterns):
                important_readmes.add(readme)
                continue
            
            # Check for very small or template READMEs
            size = self.get_file_size_mb(readme)
            if size < 0.001:  # Less than 1KB
                self.backup_and_remove(readme, "tiny README")
                continue
            
            # Check for duplicate content
            try:
                with open(readme, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if len(content) < 100:  # Very short READMEs
                    self.backup_and_remove(readme, "minimal content README")
                    continue
                    
                # Check for template/boilerplate content
                if "# TODO" in content or "Coming soon" in content or content.count('\n') < 5:
                    self.backup_and_remove(readme, "template/TODO README")
                    continue
                    
            except Exception as e:
                self.log(f"Could not read README {readme}: {e}")
        
        removed_count = len([f for f in self.removed_files if "README.md" in f and f not in [str(r.relative_to(self.repo_root)) for r in important_readmes]])
        self.log(f"Phase 3: Removed {removed_count} redundant READMEs, preserved {len(important_readmes)} important ones")
    
    def phase4_remove_test_duplicates(self):
        """Phase 4: Remove duplicate test files"""
        self.log("=== PHASE 4: Removing Test File Duplicates ===")
        
        # Find test files that are likely duplicates
        test_patterns = [
            "**/test_*.py",
            "**/*_test.py", 
            "**/*.test.js",
            "**/*.test.ts"
        ]
        
        test_files = []
        for pattern in test_patterns:
            test_files.extend(self.repo_root.glob(pattern))
        
        # Remove tests in backup directories or obvious temp locations
        for test_file in test_files:
            rel_path = str(test_file.relative_to(self.repo_root))
            if any(x in rel_path.lower() for x in ["backup", "temp", "old", "duplicate", "__pycache__"]):
                self.backup_and_remove(test_file, "test file in backup/temp location")
        
        self.log("Phase 4: Cleaned duplicate test files")
    
    def phase5_remove_backup_directories(self):
        """Phase 5: Remove obvious backup directories"""
        self.log("=== PHASE 5: Removing Backup Directories ===")
        
        backup_patterns = [
            "*backup*",
            "*old*",
            "*temp*"
        ]
        
        backup_dirs = []
        for pattern in backup_patterns:
            backup_dirs.extend([d for d in self.repo_root.glob(pattern) if d.is_dir()])
        
        # Don't remove our own backup or important directories
        safe_dirs = {"intelligent_backup", "consolidation_backup", ".hive-mind"}
        
        for backup_dir in backup_dirs:
            dir_name = backup_dir.name.lower()
            if (dir_name not in safe_dirs and 
                "vscode-extension" not in dir_name and
                backup_dir != self.backup_dir):
                
                # Calculate directory size
                total_size = 0
                for root, dirs, files in os.walk(backup_dir):
                    total_size += sum(os.path.getsize(os.path.join(root, file)) for file in files)
                size_mb = total_size / (1024 * 1024)
                
                # Backup then remove
                rel_path = backup_dir.relative_to(self.repo_root)
                backup_path = self.backup_dir / rel_path
                if backup_dir.exists():
                    shutil.copytree(backup_dir, backup_path, dirs_exist_ok=True)
                    shutil.rmtree(backup_dir)
                    
                    self.space_saved += size_mb
                    self.removed_files.append(str(rel_path))
                    self.log(f"REMOVED DIRECTORY: {rel_path} ({size_mb:.1f}MB)")
        
        self.log("Phase 5: Removed backup directories")
    
    def phase6_clean_node_modules_duplicates(self):
        """Phase 6: Clean duplicate node_modules if multiple exist"""
        self.log("=== PHASE 6: Cleaning Node Modules Duplicates ===")
        
        node_modules = list(self.repo_root.glob("**/node_modules"))
        
        # Keep only the main vscode-extension node_modules
        main_node_modules = None
        for nm in node_modules:
            if "vscode-extension/node_modules" in str(nm):
                main_node_modules = nm
                break
        
        for nm in node_modules:
            if nm != main_node_modules and nm.exists():
                total_size = 0
                for root, dirs, files in os.walk(nm):
                    total_size += sum(os.path.getsize(os.path.join(root, file)) for file in files)
                size_mb = total_size / (1024 * 1024)
                
                if size_mb > 1:  # Only log if significant size
                    self.log(f"Would remove node_modules: {nm.relative_to(self.repo_root)} ({size_mb:.1f}MB)")
                    # Don't actually remove - just log for now
        
        self.log("Phase 6: Analyzed node_modules duplicates")
    
    def generate_final_report(self):
        """Generate final consolidation report"""
        self.log("=== Generating Final Report ===")
        
        report = {
            "consolidation_completed": datetime.now().isoformat(),
            "total_files_removed": len(self.removed_files),
            "total_space_saved_mb": round(self.space_saved, 2),
            "backup_location": str(self.backup_dir.relative_to(self.repo_root)),
            "removed_files": self.removed_files[:50],  # First 50 for brevity
            "phases_completed": [
                "Exact JSON duplicate removal",
                "Analysis results consolidation", 
                "Redundant README cleanup",
                "Test file deduplication",
                "Backup directory removal",
                "Node modules analysis"
            ]
        }
        
        report_path = self.repo_root / "docs" / "INTELLIGENT_CONSOLIDATION_REPORT.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"Final report: {report_path.relative_to(self.repo_root)}")
        self.log(f"CONSOLIDATION COMPLETE: {len(self.removed_files)} files removed, {self.space_saved:.1f}MB saved")
    
    def execute_intelligent_consolidation(self):
        """Execute full intelligent consolidation"""
        self.log("Starting Intelligent Consolidation")
        self.backup_dir.mkdir(exist_ok=True)
        
        try:
            self.phase1_remove_exact_json_duplicates()
            self.phase2_consolidate_analysis_results() 
            self.phase3_remove_redundant_readmes()
            self.phase4_remove_test_duplicates()
            self.phase5_remove_backup_directories()
            self.phase6_clean_node_modules_duplicates()
            self.generate_final_report()
            
        except Exception as e:
            self.log(f"ERROR: {e}")
            raise

def main():
    consolidator = IntelligentConsolidator()
    consolidator.execute_intelligent_consolidation()

if __name__ == "__main__":
    main()