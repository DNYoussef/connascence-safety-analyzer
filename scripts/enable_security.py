#!/usr/bin/env python3
"""
Script to enable GitHub Advanced Security and Code Scanning
"""

import subprocess


def run_command(command, capture_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=True, check=False)
        return result
    except subprocess.SubprocessError as e:
        print(f"Command failed: {e}")
        return None


def enable_advanced_security():
    """Enable GitHub Advanced Security features."""
    print("Enabling GitHub Advanced Security...")

    # Try to enable advanced security using different approaches
    commands = [
        'gh api --method PATCH repos/DNYoussef/connascence-safety-analyzer --field "security_and_analysis[advanced_security][status]"="enabled"',
        'gh api --method PATCH repos/DNYoussef/connascence-safety-analyzer --field "security_and_analysis[secret_scanning][status]"="enabled"',
        'gh api --method PATCH repos/DNYoussef/connascence-safety-analyzer --field "security_and_analysis[secret_scanning_push_protection][status]"="enabled"',
    ]

    for cmd in commands:
        print(f"Running: {cmd}")
        result = run_command(cmd)
        if result and result.returncode == 0:
            print("SUCCESS: Command completed")
        else:
            print(f"WARNING: Command may have failed: {result.stderr if result else 'Unknown error'}")


def main():
    """Main function to enable security features."""
    print("GitHub Advanced Security Setup Script")
    print("=" * 50)

    # Step 1: Enable Advanced Security
    enable_advanced_security()

    print("\nNext Steps:")
    print("1. The CodeQL workflow has been created at .github/workflows/codeql-analysis.yml")
    print("2. Commit and push the workflow to trigger the first scan")
    print("3. Once the workflow runs, code scanning will be enabled automatically")
    print("4. Your SARIF uploads in the connascence-analysis workflow should then work")

    print("\nManual Steps (if API calls failed):")
    print("1. Go to: https://github.com/DNYoussef/connascence-safety-analyzer/settings/security-analysis")
    print("2. Enable 'GitHub Advanced Security'")
    print("3. Enable 'Code scanning'")
    print("4. Enable 'Secret scanning'")
    print("5. Enable 'Push protection for secrets'")


if __name__ == "__main__":
    main()
