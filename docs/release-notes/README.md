# Release Notes

This directory contains detailed release notes for each version of Connascence Analyzer.

## Current Release

* [1.0.0](1.0.0.md) - Enterprise-grade release with self-analysis capabilities

## Release Format

Our release notes follow the format of mature projects like [flake8](https://flake8.pycqa.org/en/latest/release-notes/) with:

- Clear version numbers and release dates
- Categorized changes (Added, Changed, Fixed, Security, etc.)
- Installation and upgrade instructions
- Links to PyPI and GitHub releases
- Comparison with previous versions
- Performance metrics where applicable

## Version History

| Version | Release Date | Type | Key Features |
|---------|--------------|------|--------------|
| [1.0.0](1.0.0.md) | 2024-09-03 | Major | NASA Power of Ten compliance, self-analysis |
| 0.9.0 | 2024-09-02 | Minor | Initial MCP server, policy framework |

## Automated Generation

Release notes are automatically generated from our [CHANGELOG.md](../../CHANGELOG.md) using:

```bash
python scripts/release/generate_release_notes.py <version>
```

## Release Process

1. **Version Bump**: Use `scripts/release/bump_version.py`
2. **Changelog Update**: Update the changelog with release notes
3. **Generate Notes**: Run the release notes generator
4. **Create Release**: Tag and push to GitHub
5. **Publish**: Deploy to PyPI

See our [Release Workflow Documentation](../deployment/RELEASE_WORKFLOW.md) for detailed instructions.