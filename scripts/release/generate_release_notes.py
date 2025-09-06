#!/usr/bin/env python3
"""
Generate release notes from CHANGELOG.md in the style of mature projects like flake8.

Usage: python scripts/release/generate_release_notes.py <version>
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ReleaseNotesGenerator:
    """Generate professional release notes from changelog."""
    
    def __init__(self, changelog_path: Path = None):
        """Initialize with changelog path."""
        self.changelog_path = changelog_path or Path("CHANGELOG.md")
        
    def extract_version_content(self, version: str) -> Optional[Dict[str, any]]:
        """Extract content for a specific version from changelog."""
        if not self.changelog_path.exists():
            raise FileNotFoundError(f"Changelog not found: {self.changelog_path}")
        
        content = self.changelog_path.read_text(encoding="utf-8")
        
        # Find the version section
        version_pattern = rf"## \[{re.escape(version)}\] - (\d{{4}}-\d{{2}}-\d{{2}})"
        match = re.search(version_pattern, content)
        
        if not match:
            return None
        
        release_date = match.group(1)
        start_pos = match.end()
        
        # Find the next version section or end of file
        next_version_match = re.search(r"\n## \[", content[start_pos:])
        if next_version_match:
            end_pos = start_pos + next_version_match.start()
            version_content = content[start_pos:end_pos]
        else:
            version_content = content[start_pos:]
        
        return {
            "version": version,
            "date": release_date,
            "content": version_content.strip()
        }
    
    def parse_sections(self, content: str) -> Dict[str, List[str]]:
        """Parse changelog sections into categories."""
        sections = {}
        current_section = None
        
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            if line.startswith("### "):
                current_section = line[4:].strip()
                sections[current_section] = []
            elif line.startswith("- ") and current_section:
                # Remove markdown formatting from items
                item = line[2:].strip()
                # Remove **bold** formatting
                item = re.sub(r'\*\*(.*?)\*\*', r'\1', item)
                sections[current_section].append(item)
        
        return sections
    
    def format_release_notes(self, version_data: Dict[str, any]) -> str:
        """Format release notes in professional style similar to flake8."""
        version = version_data["version"]
        date = version_data["date"]
        content = version_data["content"]
        
        # Parse sections
        sections = self.parse_sections(content)
        
        # Generate release notes
        notes = []
        notes.append(f"# Connascence Analyzer {version}")
        notes.append("")
        notes.append(f"Released on {date}")
        notes.append("")
        
        # Add repository links
        repo_url = "https://github.com/connascence/connascence-analyzer"
        notes.append(f"* [Download from PyPI]({self._get_pypi_url()})")
        notes.append(f"* [View on GitHub]({repo_url}/releases/tag/v{version})")
        notes.append(f"* [Compare with previous version]({repo_url}/compare/v{self._get_previous_version(version)}...v{version})")
        notes.append("")
        
        # Add sections in order of importance
        section_order = [
            ("Added", "New Features"),
            ("Changed", "Changes"),
            ("Fixed", "Bug Fixes"),
            ("Security", "Security Improvements"), 
            ("Deprecated", "Deprecations"),
            ("Removed", "Removals")
        ]
        
        for section_key, section_title in section_order:
            if section_key in sections and sections[section_key]:
                notes.append(f"## {section_title}")
                notes.append("")
                for item in sections[section_key]:
                    notes.append(f"* {item}")
                notes.append("")
        
        # Add installation instructions
        notes.append("## Installation")
        notes.append("")
        notes.append("You can install Connascence Analyzer via pip:")
        notes.append("")
        notes.append("```bash")
        notes.append("pip install connascence-analyzer")
        notes.append("```")
        notes.append("")
        
        # Add upgrade instructions
        notes.append("Or upgrade from a previous version:")
        notes.append("")
        notes.append("```bash")
        notes.append("pip install --upgrade connascence-analyzer")
        notes.append("```")
        notes.append("")
        
        return "\n".join(notes)
    
    def _get_pypi_url(self) -> str:
        """Get PyPI URL for the package."""
        return "https://pypi.org/project/connascence-analyzer/"
    
    def _get_previous_version(self, current_version: str) -> str:
        """Get the previous version from changelog."""
        # This is a simplified approach - in practice you'd parse the changelog
        # to find the actual previous version
        parts = current_version.split(".")
        if len(parts) >= 3:
            patch = int(parts[2])
            if patch > 0:
                return f"{parts[0]}.{parts[1]}.{patch - 1}"
            else:
                minor = int(parts[1])
                if minor > 0:
                    return f"{parts[0]}.{minor - 1}.0"
                else:
                    major = int(parts[0])
                    if major > 0:
                        return f"{major - 1}.0.0"
        return "0.9.0"  # fallback
    
    def generate(self, version: str, output_file: Optional[Path] = None) -> str:
        """Generate release notes for a version."""
        version_data = self.extract_version_content(version)
        if not version_data:
            raise ValueError(f"Version {version} not found in changelog")
        
        release_notes = self.format_release_notes(version_data)
        
        if output_file:
            output_file.write_text(release_notes, encoding="utf-8")
            print(f"Release notes written to {output_file}")
        
        return release_notes


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate release notes from changelog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/release/generate_release_notes.py 1.0.0
  python scripts/release/generate_release_notes.py 1.0.0 --output docs/release-notes/1.0.0.md
        """
    )
    parser.add_argument("version", help="Version to generate release notes for")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file for release notes (default: print to stdout)"
    )
    
    args = parser.parse_args()
    
    try:
        generator = ReleaseNotesGenerator()
        release_notes = generator.generate(args.version, args.output)
        
        if not args.output:
            print(release_notes)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()