#!/usr/bin/env python3
"""
Version bump automation script for connascence-analyzer.

This script handles semantic versioning and updates all relevant files.
Usage: python scripts/release/bump_version.py <major|minor|patch> [--dry-run]
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

import tomllib


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    
    return data["project"]["version"]


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse version string into major, minor, patch components."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-.*)?$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(current: str, bump_type: str) -> str:
    """Bump version according to semantic versioning rules."""
    major, minor, patch = parse_version(current)
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def update_pyproject_toml(new_version: str, dry_run: bool = False) -> None:
    """Update version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding="utf-8")
    
    # Update version line
    new_content = re.sub(
        r'^version = "[^"]+"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    
    if dry_run:
        print(f"Would update pyproject.toml version to {new_version}")
    else:
        pyproject_path.write_text(new_content, encoding="utf-8")
        print(f"Updated pyproject.toml version to {new_version}")


def update_changelog(new_version: str, dry_run: bool = False) -> None:
    """Update CHANGELOG.md with new version and date."""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        print("CHANGELOG.md not found, skipping")
        return
    
    content = changelog_path.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Replace [Unreleased] with new version
    new_content = re.sub(
        r"## \[Unreleased\]",
        f"## [Unreleased]\n\n### Added\n### Changed\n### Fixed\n### Removed\n\n## [{new_version}] - {today}",
        content,
        count=1
    )
    
    # Update comparison links
    repo_url = "https://github.com/connascence/connascence-analyzer"
    
    # Add new comparison link
    if "[Unreleased]:" in new_content:
        new_content = re.sub(
            r"\[Unreleased\]: .+",
            f"[Unreleased]: {repo_url}/compare/v{new_version}...HEAD",
            new_content
        )
        
        # Add version comparison link before the last line
        lines = new_content.split("\n")
        last_line = lines[-1]
        lines[-1] = f"[{new_version}]: {repo_url}/compare/v{{previous_version}}...v{new_version}"
        lines.append(last_line)
        new_content = "\n".join(lines)
    
    if dry_run:
        print(f"Would update CHANGELOG.md with version {new_version}")
    else:
        changelog_path.write_text(new_content, encoding="utf-8")
        print(f"Updated CHANGELOG.md with version {new_version}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Bump version for connascence-analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/release/bump_version.py patch
  python scripts/release/bump_version.py minor --dry-run
  python scripts/release/bump_version.py major
        """
    )
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump to perform"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    
    args = parser.parse_args()
    
    try:
        current_version = get_current_version()
        new_version = bump_version(current_version, args.bump_type)
        
        print(f"Current version: {current_version}")
        print(f"New version: {new_version}")
        print()
        
        update_pyproject_toml(new_version, args.dry_run)
        update_changelog(new_version, args.dry_run)
        
        if not args.dry_run:
            print()
            print("Next steps:")
            print("1. Update the changelog entries for this version")
            print("2. Commit the version bump: git add . && git commit -m 'Bump version to {}'".format(new_version))
            print("3. Create a tag: git tag v{}".format(new_version))
            print("4. Push: git push && git push --tags")
            print("5. Generate release notes: python scripts/release/generate_release_notes.py v{}".format(new_version))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()