# Release Management Scripts

This directory contains automated tools for managing releases of Connascence Analyzer, following professional practices similar to mature projects like flake8.

## Overview

The release management system provides:

- **Automated version bumping** following semantic versioning
- **Professional release notes generation** in the style of established tools
- **Comprehensive pre-release validation** with quality gates
- **Standardized workflow documentation** and templates

## Scripts

### bump_version.py

Automates version bumping and changelog updates.

```bash
# Preview version bump
python scripts/release/bump_version.py patch --dry-run

# Perform version bump
python scripts/release/bump_version.py patch
python scripts/release/bump_version.py minor
python scripts/release/bump_version.py major
```

**Features:**
- Updates `pyproject.toml` version
- Updates `CHANGELOG.md` with new version and date
- Maintains semantic versioning compliance
- Safe dry-run mode

### generate_release_notes.py

Generates professional release notes from the changelog.

```bash
# Generate release notes for version 1.0.1
python scripts/release/generate_release_notes.py 1.0.1

# Save to file
python scripts/release/generate_release_notes.py 1.0.1 --output docs/release-notes/1.0.1.md
```

**Features:**
- Formats in professional style (similar to flake8)
- Includes installation instructions
- Adds repository and PyPI links
- Categorizes changes appropriately
- Provides comparison links

### validate_release.py

Comprehensive pre-release validation with quality gates.

```bash
# Run all validation checks
python scripts/release/validate_release.py

# Verbose output
python scripts/release/validate_release.py --verbose
```

**Quality Gates:**
- Version consistency across files
- Clean git working directory
- Test suite pass with 85%+ coverage
- Code quality (ruff, mypy)
- Security analysis (NASA Power of Ten compliance)
- Documentation completeness
- Successful package build

## Makefile

Convenient make targets for common operations.

```bash
# Show available commands
make help

# Run validation
make validate

# Version bumps
make bump-patch
make bump-minor  
make bump-major

# Preview version bumps
make bump-patch-dry
make bump-minor-dry
make bump-major-dry

# Generate release notes
make release-notes

# Full workflow
make full-release
```

## Release Workflow

### Standard Release Process

1. **Prepare release**:
   ```bash
   make prepare-release  # Runs validation, linting, tests, security
   ```

2. **Bump version**:
   ```bash
   make bump-patch  # or bump-minor, bump-major
   ```

3. **Update changelog**:
   - Move items from "Unreleased" to the new version section
   - Categorize changes (Added, Changed, Fixed, Security, etc.)
   - Add detailed descriptions

4. **Generate release notes**:
   ```bash
   make release-notes
   ```

5. **Create release**:
   ```bash
   make create-release VERSION=1.0.1
   ```

6. **Publish**:
   ```bash
   make publish  # or publish-test for TestPyPI
   ```

### Interactive Full Release

For a guided experience:

```bash
make full-release
```

This interactive workflow:
- Runs all validation checks
- Prompts for release type
- Generates version and release notes
- Provides step-by-step instructions

## Quality Standards

Every release must meet these quality gates:

- **Test Coverage**: Minimum 85%
- **Security**: No critical or high-severity issues
- **Code Quality**: Pass ruff and mypy checks
- **Documentation**: All required files present
- **Build**: Package builds without errors
- **Git**: Clean working directory

## Examples

### Patch Release (Bug Fixes)

```bash
# 1. Validate current state
make validate

# 2. Create patch release
make bump-patch

# 3. Update changelog manually
# 4. Generate release notes
make release-notes

# 5. Create and publish
make create-release VERSION=1.0.1
make publish
```

### Minor Release (New Features)

```bash
# 1. Full validation
make prepare-release

# 2. Create minor release  
make bump-minor

# 3. Update changelog with new features
# 4. Generate and review release notes
make release-notes

# 5. Create and publish
make create-release VERSION=1.1.0
make publish
```

### Major Release (Breaking Changes)

```bash
# 1. Comprehensive validation
make prepare-release

# 2. Create major release
make bump-major

# 3. Document breaking changes in changelog
# 4. Update migration documentation
# 5. Generate detailed release notes
make release-notes

# 6. Create and publish
make create-release VERSION=2.0.0
make publish
```

## File Structure

```
scripts/release/
├── README.md                 # This file
├── bump_version.py          # Version bumping automation
├── generate_release_notes.py # Release notes generation
├── validate_release.py      # Pre-release validation
├── Makefile                 # Convenient make targets
└── RELEASE_TEMPLATE.md      # Release checklist template
```

## Configuration

The scripts use configuration from:

- `pyproject.toml` - Version and project metadata
- `CHANGELOG.md` - Release history and notes
- GitHub repository settings - For release links

## Integration

These scripts integrate with:

- **GitHub**: Release creation and comparison links
- **PyPI**: Package publishing and download links
- **Git**: Version tagging and change tracking
- **CI/CD**: Quality gate enforcement

## Best Practices

1. **Always validate** before releasing
2. **Use dry-run** to preview changes
3. **Update changelog** before generating notes
4. **Test installation** on clean environment
5. **Monitor post-release** for issues

This release management system ensures consistent, professional releases that maintain the high quality standards expected from enterprise software.