# Release Template

Use this template when preparing a new release of Connascence Analyzer.

## Release Information

- **Version**: X.Y.Z
- **Release Date**: YYYY-MM-DD
- **Release Type**: Major | Minor | Patch
- **Release Manager**: [Name]

## Pre-Release Checklist

### Planning
- [ ] Release scope defined and communicated
- [ ] All planned features completed
- [ ] Breaking changes documented
- [ ] Migration guide prepared (if needed)

### Quality Assurance
- [ ] All tests passing
- [ ] Code coverage >= 85%
- [ ] Security scan clean (no critical/high issues)
- [ ] Performance benchmarks acceptable
- [ ] Documentation updated
- [ ] Examples verified

### Preparation
- [ ] Version bumped in pyproject.toml
- [ ] CHANGELOG.md updated with release notes
- [ ] Release notes generated
- [ ] Git working directory clean
- [ ] All changes committed

## Release Execution

### Build and Test
- [ ] `python scripts/release/validate_release.py` passes
- [ ] Package builds successfully
- [ ] Installation test on clean environment
- [ ] Basic smoke tests pass

### Git Operations
- [ ] Version commit created: `git commit -m "Bump version to X.Y.Z"`
- [ ] Git tag created: `git tag vX.Y.Z`
- [ ] Changes pushed to main branch
- [ ] Tag pushed to origin

### Publication
- [ ] GitHub release created with release notes
- [ ] Package uploaded to PyPI
- [ ] PyPI package verified (installation test)
- [ ] Documentation deployed

## Post-Release Tasks

### Communication
- [ ] Release announcement prepared
- [ ] Stakeholders notified
- [ ] Social media posts (if applicable)
- [ ] Community forums updated

### Monitoring
- [ ] PyPI download metrics monitored
- [ ] Issue tracker watched for problems
- [ ] User feedback collected
- [ ] Performance metrics tracked

### Documentation
- [ ] Installation instructions tested
- [ ] API documentation verified
- [ ] Tutorial examples updated
- [ ] Integration guides refreshed

## Release Notes Template

```markdown
# Connascence Analyzer X.Y.Z

Released on YYYY-MM-DD

* [Download from PyPI](https://pypi.org/project/connascence-analyzer/)
* [View on GitHub](https://github.com/connascence/connascence-analyzer/releases/tag/vX.Y.Z)
* [Compare with previous version](https://github.com/connascence/connascence-analyzer/compare/vA.B.C...vX.Y.Z)

## New Features

* Feature 1: Description
* Feature 2: Description

## Changes

* Change 1: Description
* Change 2: Description

## Bug Fixes

* Fix 1: Description
* Fix 2: Description

## Security Improvements

* Security improvement 1: Description

## Installation

You can install Connascence Analyzer via pip:

```bash
pip install connascence-analyzer
```

Or upgrade from a previous version:

```bash
pip install --upgrade connascence-analyzer
```

## Breaking Changes (if any)

* Breaking change 1: Description and migration path
* Breaking change 2: Description and migration path

## Deprecations (if any)

* Deprecated feature 1: Will be removed in version X.Y.Z
* Deprecated feature 2: Will be removed in version X.Y.Z
```

## Rollback Plan

If critical issues are discovered post-release:

1. **Immediate Assessment**
   - [ ] Severity evaluation
   - [ ] Impact analysis
   - [ ] User communication plan

2. **Decision Point**
   - [ ] Hotfix release planned
   - [ ] OR Package yanking considered
   - [ ] OR Full rollback required

3. **Execution**
   - [ ] Fix implemented and tested
   - [ ] Emergency release process initiated
   - [ ] Users notified of fix

## Success Criteria

- [ ] Package installs without errors
- [ ] Core functionality works in clean environment
- [ ] No critical bugs reported within 24 hours
- [ ] Documentation is accessible and accurate
- [ ] Download metrics show expected adoption

## Notes

Add any specific notes for this release:

- Special considerations
- Known issues
- Future plans
- Acknowledgments

## Release Sign-off

- [ ] Development Team Lead: _________________ Date: _______
- [ ] QA Lead: _________________ Date: _______
- [ ] Product Owner: _________________ Date: _______
- [ ] Release Manager: _________________ Date: _______

---

**Template Version**: 1.0
**Last Updated**: 2024-09-03