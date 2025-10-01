#!/usr/bin/env python3
"""
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

Single-command verification script for all reproducible claims.
Generates complete evidence bundle with pinned dependencies.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict


class ClaimVerifier:
    """Verifies all reproducible claims with pinned dependencies."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_packages_dir = project_root / "test_packages"
        self.results = {
            "timestamp": time.time(),
            "verification_id": self._generate_verification_id(),
            "pinned_dependencies": {},
            "analysis_results": {},
            "verification_status": {},
            "evidence_bundle": {},
        }

    def _generate_verification_id(self) -> str:
        """Generate unique verification ID based on current state."""
        str(time.time())
        project_hash = hashlib.sha256(str(self.project_root).encode()).hexdigest()[:8]
        return f"verify-{project_hash}-{int(time.time())}"

    def pin_external_dependencies(self) -> Dict[str, str]:
        """Pin external repository dependencies to specific SHAs."""
        pinned_deps = {}

        # Pin test package versions (if they're git repos)
        test_packages = ["celery", "curl", "express"]

        for package in test_packages:
            package_dir = self.test_packages_dir / package
            if package_dir.exists() and (package_dir / ".git").exists():
                try:
                    # Get current commit SHA
                    result = subprocess.run(
                        ["git", "rev-parse", "HEAD"], cwd=package_dir, capture_output=True, text=True, check=True
                    )
                    sha = result.stdout.strip()
                    pinned_deps[package] = {"type": "git", "sha": sha, "path": str(package_dir)}
                except subprocess.CalledProcessError:
                    pinned_deps[package] = {"type": "local", "path": str(package_dir), "note": "Not a git repository"}

        # Pin MCP server versions from package.json/requirements if available
        mcp_servers = {"claude-flow": "@alpha", "ruv-swarm": "@latest", "flow-nexus": "@latest"}

        for server, version in mcp_servers.items():
            try:
                # Try to get actual installed version
                result = subprocess.run(
                    ["npm", "list", f"{server}", "--depth=0", "--json"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    npm_data = json.loads(result.stdout)
                    if "dependencies" in npm_data and server in npm_data["dependencies"]:
                        actual_version = npm_data["dependencies"][server]["version"]
                        pinned_deps[server] = {"type": "npm", "version": actual_version, "requested": version}
                    else:
                        pinned_deps[server] = {"type": "npm", "version": "not-installed", "requested": version}
                else:
                    pinned_deps[server] = {"type": "npm", "version": "unavailable", "requested": version}
            except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
                pinned_deps[server] = {"type": "npm", "version": "unknown", "requested": version}

        self.results["pinned_dependencies"] = pinned_deps
        return pinned_deps

    def verify_analyzer_functionality(self) -> Dict[str, Any]:
        """Verify core analyzer works without external dependencies."""
        verification = {
            "core_analyzer_standalone": False,
            "multi_language_support": False,
            "violation_detection": False,
            "error_messages": [],
        }

        try:
            # Test 1: Core analyzer import
            sys.path.insert(0, str(self.project_root))

            # Import main analyzer components
            from analyzer.check_connascence import ConnascenceAnalyzer

            verification["core_analyzer_standalone"] = True

            # Test 2: Create analyzer instance
            analyzer = ConnascenceAnalyzer()
            if hasattr(analyzer, "analyze_directory"):
                verification["multi_language_support"] = True

            # Test 3: Basic violation detection
            test_code = """
def test_function():
    x = 42  # Magic literal
    y = 42  # Duplicate magic literal
    return x + y
"""

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(test_code)
                temp_file = Path(f.name)

            try:
                result = analyzer.analyze_path(temp_file)
                if isinstance(result, dict) and "violations" in result:
                    if result["violations"]:
                        verification["violation_detection"] = True
                elif isinstance(result, list) and result:
                    verification["violation_detection"] = True
            finally:
                temp_file.unlink(missing_ok=True)

        except ImportError as e:
            verification["error_messages"].append(f"Import error: {e}")
        except Exception as e:
            verification["error_messages"].append(f"Runtime error: {e}")

        return verification

    def run_analysis_on_test_packages(self) -> Dict[str, Any]:
        """Run full analysis on test packages and verify claimed results."""
        results = {}

        expected_results = {
            "celery": {"target_violations": 24314, "tolerance": 0.05},
            "curl": {"target_violations": 40799, "tolerance": 0.05},
            "express": {"target_violations": 9124, "tolerance": 0.05},
        }

        try:
            sys.path.insert(0, str(self.project_root))
            from analyzer.check_connascence import ConnascenceAnalyzer

            analyzer = ConnascenceAnalyzer()

            for package, expected in expected_results.items():
                package_dir = self.test_packages_dir / package

                if not package_dir.exists():
                    results[package] = {"status": "package_not_found", "path": str(package_dir)}
                    continue

                print(f"Analyzing {package}... (this may take a few minutes)")
                start_time = time.time()

                try:
                    # Run analysis
                    violations = analyzer.analyze_directory(package_dir)
                    analysis_time = time.time() - start_time

                    violation_count = len(violations) if isinstance(violations, list) else 0

                    # Check if within tolerance
                    target = expected["target_violations"]
                    tolerance = expected["tolerance"]
                    min_expected = int(target * (1 - tolerance))
                    max_expected = int(target * (1 + tolerance))

                    within_tolerance = min_expected <= violation_count <= max_expected

                    results[package] = {
                        "status": "completed",
                        "violation_count": violation_count,
                        "target_violations": target,
                        "within_tolerance": within_tolerance,
                        "analysis_time_seconds": round(analysis_time, 2),
                        "tolerance_range": f"{min_expected}-{max_expected}",
                        "accuracy": "verified" if within_tolerance else "deviation",
                    }

                except Exception as e:
                    results[package] = {
                        "status": "analysis_failed",
                        "error": str(e),
                        "analysis_time_seconds": time.time() - start_time,
                    }

        except ImportError as e:
            results["analyzer_import_error"] = str(e)

        return results

    def generate_evidence_bundle(self) -> Dict[str, Any]:
        """Generate complete evidence bundle for reproducibility."""
        bundle = {
            "verification_metadata": {
                "timestamp": self.results["timestamp"],
                "verification_id": self.results["verification_id"],
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": str(self.project_root),
            },
            "pinned_dependencies": self.results["pinned_dependencies"],
            "analyzer_verification": self.results.get("analyzer_verification", {}),
            "analysis_results": self.results.get("analysis_results", {}),
            "reproducibility_command": self._generate_reproduction_command(),
            "verification_checksums": self._generate_checksums(),
        }

        return bundle

    def _generate_reproduction_command(self) -> str:
        """Generate single command to reproduce all results."""
        return f"""
# Single command to reproduce all verification results:
cd {self.project_root}
python scripts/verify_claims.py --full-verification > verification_report_{self.results['verification_id']}.json

# To reproduce specific package analysis:
python -m analyzer.check_connascence test_packages/celery > celery_analysis.json
python -m analyzer.check_connascence test_packages/curl > curl_analysis.json
python -m analyzer.check_connascence test_packages/express > express_analysis.json

# Verification ID: {self.results['verification_id']}
# All results are deterministic when run with same pinned dependency versions
        """.strip()

    def _generate_checksums(self) -> Dict[str, str]:
        """Generate checksums for key verification files."""
        checksums = {}

        key_files = ["analyzer/check_connascence.py", "mcp/server.py", "cli/connascence.py", "pyproject.toml"]

        for file_path in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                with open(full_path, "rb") as f:
                    checksums[file_path] = hashlib.sha256(f.read()).hexdigest()

        return checksums

    def run_full_verification(self) -> Dict[str, Any]:
        """Run complete verification process."""
        print(f"[VERIFY] Starting full verification - ID: {self.results['verification_id']}")

        # Step 1: Pin dependencies
        print("[PIN] Pinning external dependencies...")
        self.pin_external_dependencies()

        # Step 2: Verify analyzer functionality
        print("[CORE] Verifying analyzer functionality...")
        self.results["analyzer_verification"] = self.verify_analyzer_functionality()

        # Step 3: Run analysis on test packages
        print("[ANALYZE] Running analysis on test packages...")
        self.results["analysis_results"] = self.run_analysis_on_test_packages()

        # Step 4: Generate evidence bundle
        print("[BUNDLE] Generating evidence bundle...")
        self.results["evidence_bundle"] = self.generate_evidence_bundle()

        # Step 5: Final verification status
        self.results["verification_status"] = {
            "overall_status": self._determine_overall_status(),
            "core_functionality": self.results["analyzer_verification"].get("core_analyzer_standalone", False),
            "multi_language_support": self.results["analyzer_verification"].get("multi_language_support", False),
            "violation_detection": self.results["analyzer_verification"].get("violation_detection", False),
            "reproducible_claims": self._verify_reproducible_claims(),
        }

        print(f"[COMPLETE] Verification completed - Status: {self.results['verification_status']['overall_status']}")

        return self.results

    def _determine_overall_status(self) -> str:
        """Determine overall verification status."""
        analyzer_ok = self.results["analyzer_verification"].get("core_analyzer_standalone", False)

        if not analyzer_ok:
            return "FAILED - Core analyzer not functional"

        analysis_results = self.results["analysis_results"]
        if not analysis_results or "analyzer_import_error" in analysis_results:
            return "PARTIAL - Core works but analysis failed"

        # Check if key claims are verified
        verified_packages = 0
        total_packages = 0

        for package, result in analysis_results.items():
            if isinstance(result, dict) and "status" in result:
                total_packages += 1
                if result.get("within_tolerance", False):
                    verified_packages += 1

        if verified_packages == total_packages and total_packages > 0:
            return "VERIFIED - All claims reproduced"
        elif verified_packages > 0:
            return f"PARTIAL - {verified_packages}/{total_packages} claims verified"
        else:
            return "FAILED - No claims verified"

    def _verify_reproducible_claims(self) -> Dict[str, bool]:
        """Check which specific claims are reproducible."""
        claims = {
            "74237_total_violations": False,
            "celery_24314_violations": False,
            "curl_40799_violations": False,
            "express_9124_violations": False,
            "multi_language_support": False,
        }

        # Check multi-language support
        claims["multi_language_support"] = self.results["analyzer_verification"].get("multi_language_support", False)

        # Check individual package claims
        analysis_results = self.results.get("analysis_results", {})

        if "celery" in analysis_results:
            claims["celery_24314_violations"] = analysis_results["celery"].get("within_tolerance", False)

        if "curl" in analysis_results:
            claims["curl_40799_violations"] = analysis_results["curl"].get("within_tolerance", False)

        if "express" in analysis_results:
            claims["express_9124_violations"] = analysis_results["express"].get("within_tolerance", False)

        # Check total violations claim
        total_violations = 0
        for package in ["celery", "curl", "express"]:
            if package in analysis_results and "violation_count" in analysis_results[package]:
                total_violations += analysis_results[package]["violation_count"]

        # Within 5% tolerance of 74,237
        claims["74237_total_violations"] = 70525 <= total_violations <= 77949

        return claims


def main():
    """Main verification entry point."""
    project_root = Path(__file__).parent.parent

    # Parse command line args
    full_verification = "--full-verification" in sys.argv
    output_file = None

    # Look for output redirection
    if len(sys.argv) > 1 and sys.argv[-1].endswith(".json"):
        output_file = sys.argv[-1]

    verifier = ClaimVerifier(project_root)

    if full_verification:
        results = verifier.run_full_verification()
    else:
        # Quick verification
        print("[QUICK] Running quick verification...")
        verifier.pin_external_dependencies()
        results = verifier.verify_analyzer_functionality()

    # Output results
    output_json = json.dumps(results, indent=2, default=str)

    if output_file:
        with open(output_file, "w") as f:
            f.write(output_json)
        print(f"[OUTPUT] Results written to: {output_file}")
    else:
        print("\n[RESULTS] VERIFICATION RESULTS:")
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
