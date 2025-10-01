#!/usr/bin/env python3
"""
Rollback Script for AST-Damaged Files
Reverts files damaged by the assertion injector's AST unparsing.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class ASTDamageRollback:
    """Rollback files damaged by AST unparsing."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.damaged_files = []

    def find_damaged_files(self) -> List[str]:
        """Find files that were modified by the assertion injector."""
        print("Finding damaged files...")

        # Get list of modified files
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        damaged = []
        for line in result.stdout.strip().split('\n'):
            if line.startswith(' M '):
                file_path = line[3:].strip()

                # Check if file has the telltale signs of AST damage
                full_path = self.repo_path / file_path
                if full_path.suffix == '.py' and full_path.exists():
                    # Check for damaged imports
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        first_lines = f.read(500)

                    # AST damage indicators:
                    # 1. Single-quoted docstrings at file start
                    # 2. ProductionAssert import at beginning
                    if ('from fixes.phase0.production_safe_assertions import ProductionAssert' in first_lines or
                        (first_lines.startswith("'") and not first_lines.startswith('"""'))):
                        damaged.append(file_path)

        self.damaged_files = damaged
        return damaged

    def rollback_file(self, file_path: str) -> bool:
        """Rollback a single file to its last committed state."""
        try:
            # Use git checkout to restore file
            result = subprocess.run(
                ["git", "checkout", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"  [ERROR] Failed to rollback {file_path}: {e.stderr}")
            return False

    def rollback_all(self) -> Tuple[int, int]:
        """Rollback all damaged files."""
        print("\nRolling back damaged files...")
        print("-" * 40)

        success_count = 0
        fail_count = 0

        for file_path in self.damaged_files:
            print(f"Rolling back: {file_path}")
            if self.rollback_file(file_path):
                success_count += 1
                print(f"  [OK] Restored to last commit")
            else:
                fail_count += 1

        return success_count, fail_count

    def verify_rollback(self) -> bool:
        """Verify that rollback was successful."""
        print("\nVerifying rollback...")

        # Check git status again
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        remaining_modified = []
        for line in result.stdout.strip().split('\n'):
            if line.startswith(' M ') and line[3:].strip() in self.damaged_files:
                remaining_modified.append(line[3:].strip())

        if remaining_modified:
            print(f"  [WARNING] {len(remaining_modified)} files still modified:")
            for f in remaining_modified[:5]:
                print(f"    - {f}")
            return False
        else:
            print("  [OK] All damaged files restored")
            return True


def main():
    """Main rollback function."""
    print("AST Damage Rollback Script")
    print("=" * 70)
    print("This will restore files damaged by the assertion injector")

    # Get repository path
    repo_path = Path.cwd()

    # Initialize rollback
    rollback = ASTDamageRollback(repo_path)

    # Find damaged files
    damaged = rollback.find_damaged_files()

    if not damaged:
        print("\n✅ No damaged files found!")
        return

    print(f"\nFound {len(damaged)} potentially damaged files:")
    for f in damaged[:10]:
        print(f"  - {f}")
    if len(damaged) > 10:
        print(f"  ... and {len(damaged) - 10} more")

    # Ask for confirmation
    response = input("\nProceed with rollback? (y/n): ")
    if response.lower() != 'y':
        print("Rollback cancelled")
        return

    # Perform rollback
    success, failed = rollback.rollback_all()

    # Report results
    print("\n" + "=" * 70)
    print("ROLLBACK COMPLETE")
    print("=" * 70)
    print(f"Files restored: {success}")
    print(f"Files failed: {failed}")

    # Verify
    if rollback.verify_rollback():
        print("\n✅ Rollback successful! Files restored to last commit.")
        print("\nNext steps:")
        print("1. Create improved assertion injector that preserves formatting")
        print("2. Use regex-based insertion instead of AST manipulation")
        print("3. Target only critical functions")
    else:
        print("\n⚠️ Some files may still have issues. Check git status.")


if __name__ == "__main__":
    main()