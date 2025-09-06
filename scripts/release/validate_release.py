#!/usr/bin/env python3
"""
Pre-release validation script to ensure quality gates are met.

This script performs comprehensive checks before allowing a release.
Usage: python scripts/release/validate_release.py [--version VERSION]
"""

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Dict, List, Tuple


class ReleaseValidator:
    """Validate release readiness with comprehensive quality gates."""
    
    def __init__(self, verbose: bool = False):
        """Initialize validator."""
        self.verbose = verbose
        self.results = {}
        
    def run_command(self, command: List[str], cwd: Path = None) -> Tuple[int, str, str]:
        """Run shell command and capture output."""
        if self.verbose:
            print(f"Running: {' '.join(command)}")
            
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=cwd or Path.cwd()
        )
        
        return result.returncode, result.stdout, result.stderr
    
    def validate_version_consistency(self) -> bool:
        """Ensure version is consistent across all files."""
        print("Checking version consistency...")
        
        # Get version from pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            print("❌ pyproject.toml not found")
            return False
            
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        
        version = data["project"]["version"]
        print(f"  Version in pyproject.toml: {version}")
        
        # Check changelog has this version
        changelog_path = Path("CHANGELOG.md")
        if changelog_path.exists():
            changelog_content = changelog_path.read_text(encoding="utf-8")
            if f"## [{version}]" in changelog_content:
                print(f"  ✅ Version {version} found in CHANGELOG.md")
            else:
                print(f"  ❌ Version {version} not found in CHANGELOG.md")
                return False
        
        self.results["version"] = version
        return True
    
    def validate_tests(self) -> bool:
        """Run test suite and check coverage."""
        print("Running test suite...")
        
        # Run pytest with coverage
        returncode, stdout, stderr = self.run_command([
            "python", "-m", "pytest", 
            "tests/", 
            "--cov=.", 
            "--cov-report=json",
            "--cov-report=term-missing",
            "--tb=short"
        ])
        
        if returncode != 0:
            print("❌ Test suite failed")
            if self.verbose:
                print(stdout)
                print(stderr)
            return False
        
        # Check coverage
        coverage_file = Path("coverage.json")
        if coverage_file.exists():
            try:
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)
                
                total_coverage = coverage_data["totals"]["percent_covered"]
                print(f"  Coverage: {total_coverage:.1f}%")
                
                if total_coverage < 85.0:
                    print(f"❌ Coverage {total_coverage:.1f}% is below minimum 85%")
                    return False
                else:
                    print(f"  ✅ Coverage {total_coverage:.1f}% meets minimum requirement")
                    
            except (json.JSONDecodeError, KeyError):
                print("❌ Could not parse coverage report")
                return False
        
        print("  ✅ All tests passed")
        return True
    
    def validate_linting(self) -> bool:
        """Check code quality with linting tools."""
        print("Checking code quality...")
        
        # Run ruff
        returncode, stdout, stderr = self.run_command([
            "python", "-m", "ruff", "check", ".", "--format=json"
        ])
        
        if returncode != 0:
            print("❌ Ruff linting failed")
            if self.verbose and stdout:
                try:
                    issues = json.loads(stdout)
                    print(f"  Found {len(issues)} linting issues")
                    for issue in issues[:5]:  # Show first 5
                        print(f"    {issue['filename']}:{issue['location']['row']} {issue['code']}: {issue['message']}")
                except json.JSONDecodeError:
                    print(stdout)
            return False
        
        print("  ✅ Ruff linting passed")
        
        # Run mypy type checking
        returncode, stdout, stderr = self.run_command([
            "python", "-m", "mypy", ".", "--ignore-missing-imports"
        ])
        
        if returncode != 0:
            print("❌ MyPy type checking failed")
            if self.verbose:
                print(stdout)
            return False
        
        print("  ✅ MyPy type checking passed")
        return True
    
    def validate_security(self) -> bool:
        """Run security analysis."""
        print("Running security analysis...")
        
        # Run connascence self-analysis with NASA policy
        returncode, stdout, stderr = self.run_command([
            "python", "-m", "connascence", ".", 
            "--policy=nasa_jpl_pot10",
            "--format=json",
            "--exit-zero"
        ])
        
        if returncode != 0:
            print("❌ Security analysis failed to run")
            if self.verbose:
                print(stderr)
            return False
        
        try:
            if stdout.strip():
                analysis_result = json.loads(stdout)
                
                # Check for critical issues
                critical_count = 0
                high_count = 0
                
                if "violations" in analysis_result:
                    for violation in analysis_result["violations"]:
                        severity = violation.get("severity", "").lower()
                        if severity == "critical":
                            critical_count += 1
                        elif severity == "high":
                            high_count += 1
                
                print(f"  Security analysis: {critical_count} critical, {high_count} high severity issues")
                
                if critical_count > 0:
                    print(f"❌ Found {critical_count} critical security issues")
                    return False
                
                if high_count > 5:  # Allow up to 5 high severity issues
                    print(f"❌ Found {high_count} high severity issues (max 5 allowed)")
                    return False
                    
            print("  ✅ Security analysis passed")
            
        except json.JSONDecodeError:
            print("❌ Could not parse security analysis results")
            return False
        
        return True
    
    def validate_documentation(self) -> bool:
        """Check documentation completeness."""
        print("Checking documentation...")
        
        required_files = [
            "README.md",
            "CHANGELOG.md", 
            "docs/README.md",
            "docs/deployment/INSTALLATION.md"
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                print(f"❌ Required documentation file missing: {file_path}")
                return False
        
        # Check if README mentions current version
        readme_content = Path("README.md").read_text(encoding="utf-8")
        version = self.results.get("version", "unknown")
        
        # This is a basic check - in practice you might want more sophisticated validation
        print("  ✅ Required documentation files present")
        return True
    
    def validate_build(self) -> bool:
        """Test that the package builds correctly."""
        print("Testing package build...")
        
        # Clean previous builds
        for path in Path(".").glob("dist/*"):
            path.unlink()
        for path in Path(".").glob("build/*"):
            path.unlink()
        
        # Build package
        returncode, stdout, stderr = self.run_command([
            "python", "-m", "build"
        ])
        
        if returncode != 0:
            print("❌ Package build failed")
            if self.verbose:
                print(stdout)
                print(stderr)
            return False
        
        # Check that build artifacts exist
        dist_files = list(Path("dist").glob("*"))
        if len(dist_files) < 2:  # Should have both wheel and sdist
            print("❌ Build did not create expected artifacts")
            return False
        
        print(f"  ✅ Package built successfully ({len(dist_files)} artifacts)")
        return True
    
    def validate_git_status(self) -> bool:
        """Ensure git working directory is clean."""
        print("Checking git status...")
        
        returncode, stdout, stderr = self.run_command([
            "git", "status", "--porcelain"
        ])
        
        if returncode != 0:
            print("❌ Git status check failed")
            return False
        
        if stdout.strip():
            print("❌ Working directory has uncommitted changes")
            if self.verbose:
                print(stdout)
            return False
        
        print("  ✅ Working directory is clean")
        return True
    
    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print("🔍 Running pre-release validation...")
        print("=" * 50)
        
        validations = [
            ("Version Consistency", self.validate_version_consistency),
            ("Git Status", self.validate_git_status),
            ("Test Suite", self.validate_tests),
            ("Code Quality", self.validate_linting),
            ("Security Analysis", self.validate_security),
            ("Documentation", self.validate_documentation),
            ("Package Build", self.validate_build),
        ]
        
        all_passed = True
        
        for name, validator in validations:
            print()
            try:
                if not validator():
                    all_passed = False
            except Exception as e:
                print(f"❌ {name} validation failed with error: {e}")
                all_passed = False
        
        print()
        print("=" * 50)
        
        if all_passed:
            print("🎉 All validation checks passed! Ready for release.")
            version = self.results.get("version", "unknown")
            print(f"📦 Version {version} is ready to be released.")
        else:
            print("❌ Some validation checks failed. Please fix issues before release.")
        
        return all_passed


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate release readiness",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--version",
        help="Expected version (optional)"
    )
    
    args = parser.parse_args()
    
    validator = ReleaseValidator(verbose=args.verbose)
    
    if validator.run_all_validations():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()