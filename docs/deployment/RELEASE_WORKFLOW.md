# Release Workflow Documentation

This document outlines the complete release process for Connascence Analyzer, following industry best practices for mature software projects.

## Overview

Our release process follows semantic versioning and provides professional release notes similar to established tools like flake8. The process is partially automated to ensure consistency and reduce errors.

## Release Types

### Major Release (X.0.0)
- Breaking changes
- Significant new features
- Architecture changes
- API modifications

### Minor Release (X.Y.0)
- New features
- Enhancements to existing features
- Deprecations (with backward compatibility)

### Patch Release (X.Y.Z)
- Bug fixes
- Security patches
- Documentation updates
- Small improvements

## Pre-Release Checklist

Before starting a release:

- [ ] All planned features are complete and tested
- [ ] CI/CD pipeline is passing
- [ ] Documentation is updated
- [ ] Security scan is clean
- [ ] Performance benchmarks are acceptable
- [ ] Breaking changes are documented

## Release Process

### Step 1: Prepare the Release

1. **Check current state**:
   ```bash
   git status
   git log --oneline -10
   ```

2. **Run full test suite**:
   ```bash
   python -m pytest tests/ --cov=. --cov-report=term-missing
   ```

3. **Run security checks**:
   ```bash
   python -m connascence . --policy=nasa_jpl_pot10 --format=json
   ```

### Step 2: Version Bump

1. **Determine version bump type** based on changes:
   - Major: Breaking changes or significant new features
   - Minor: New features with backward compatibility
   - Patch: Bug fixes and small improvements

2. **Run version bump script**:
   ```bash
   # Dry run first to preview changes
   python scripts/release/bump_version.py patch --dry-run
   
   # Apply the version bump
   python scripts/release/bump_version.py patch
   ```

3. **Update changelog manually**:
   - Move items from "Unreleased" to the new version section
   - Categorize changes appropriately (Added, Changed, Fixed, etc.)
   - Add detailed descriptions for major features

### Step 3: Generate Release Notes

1. **Generate professional release notes**:
   ```bash
   python scripts/release/generate_release_notes.py 1.0.1 --output docs/release-notes/1.0.1.md
   ```

2. **Review generated notes**:
   - Verify all changes are captured
   - Check formatting and links
   - Ensure installation instructions are correct

### Step 4: Create Release

1. **Commit version changes**:
   ```bash
   git add .
   git commit -m "Bump version to 1.0.1"
   ```

2. **Create and push tag**:
   ```bash
   git tag v1.0.1
   git push origin main
   git push origin v1.0.1
   ```

3. **Create GitHub release**:
   - Go to GitHub releases page
   - Click "Create a new release"
   - Use tag v1.0.1
   - Copy content from generated release notes
   - Mark as "Latest release" if appropriate

### Step 5: Publish to PyPI

1. **Build distribution**:
   ```bash
   python -m build
   ```

2. **Test on TestPyPI first** (recommended):
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

3. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/*
   ```

### Step 6: Post-Release Tasks

1. **Update documentation**:
   - Verify installation instructions work with new version
   - Update any version-specific documentation
   - Refresh examples if needed

2. **Notify stakeholders**:
   - Update project README if needed
   - Notify enterprise customers of new features
   - Update integration guides

3. **Monitor for issues**:
   - Watch for installation problems
   - Monitor issue tracker for new bugs
   - Check PyPI download statistics

## Automated Scripts

### Version Bump Script
```bash
python scripts/release/bump_version.py <major|minor|patch> [--dry-run]
```

Features:
- Updates pyproject.toml version
- Updates CHANGELOG.md with new version and date
- Maintains semantic versioning compliance
- Dry-run option for safety

### Release Notes Generator
```bash
python scripts/release/generate_release_notes.py <version> [--output file.md]
```

Features:
- Extracts changes from CHANGELOG.md
- Formats in professional style (similar to flake8)
- Includes installation instructions
- Adds repository links
- Categorizes changes appropriately

## Quality Gates

Every release must pass these quality gates:

1. **Test Coverage**: Minimum 85% code coverage
2. **Security Scan**: No high or critical security issues
3. **Performance**: No significant performance regressions
4. **Documentation**: All new features documented
5. **Backward Compatibility**: Breaking changes properly versioned

## Emergency Releases

For critical security fixes or major bugs:

1. **Hotfix Branch**:
   ```bash
   git checkout -b hotfix/security-fix
   # Make fixes
   git commit -m "Security fix for CVE-YYYY-XXXX"
   ```

2. **Fast-Track Process**:
   - Skip minor process steps
   - Focus on fix verification
   - Expedited patch release

3. **Post-Emergency**:
   - Full retrospective
   - Process improvements
   - Update documentation

## Rollback Process

If a release has critical issues:

1. **Immediate Response**:
   - Document the issue
   - Assess impact and severity
   - Decide on rollback vs. hotfix

2. **PyPI Rollback** (if necessary):
   - Cannot delete releases, but can yank them
   - Communicate to users immediately

3. **Recovery**:
   - Fix the issue in a new release
   - Update documentation
   - Conduct post-mortem

## Version Support Policy

- **Latest Major**: Full support with new features and bug fixes
- **Previous Major**: Security fixes and critical bugs only
- **Older Versions**: End-of-life, no support

## Tools and Dependencies

Required tools for release management:

```bash
pip install build twine
```

Optional but recommended:
```bash
pip install gh  # GitHub CLI for release automation
```

## Example Release Timeline

For a typical minor release:

- **Week -2**: Feature freeze, testing begins
- **Week -1**: Documentation updates, release notes preparation
- **Day 0**: Version bump, tag creation, PyPI upload
- **Day +1**: Monitor for issues, stakeholder notifications
- **Week +1**: Post-release review and metrics analysis

This workflow ensures consistent, professional releases that maintain the high quality standards expected from enterprise software.