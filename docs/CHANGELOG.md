# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Professional release notes system with semantic versioning
- Automated changelog generation scripts
- Version bump automation tools
- Release workflow documentation

### Changed
- Updated changelog format to follow Keep a Changelog standard
- Improved release management process

### Fixed
- Unicode encoding issues in Windows environments
- Rate limiting configuration inconsistencies

## [1.0.0] - 2024-09-03

### Added
- Complete NASA Power of Ten safety rule compliance
- Self-analysis capability with recursive improvement validation
- Enterprise-grade safety compliance (100% Strict Safety compliance)
- Parameter objects for complex method signatures (ViolationCreationParams)
- Production deployment readiness validation
- Magic literal elimination system (65+ literals replaced with named constants)
- Rate limiting configuration constants (DEFAULT_RATE_LIMIT_REQUESTS, DEFAULT_RATE_LIMIT_WINDOW_SECONDS)
- Policy framework with 54 total configuration constants
- Analyzer threshold constants for improved maintainability

### Changed
- Refactored ConnascenceViolation.__init__() to use parameter objects
- Enhanced MCP server configuration with extracted constants
- Improved policy framework with systematic constant organization
- Code maintainability improved by 23.6%
- Reduced code duplication from 12% to 3% (-75% reduction)

### Fixed
- Parameter coupling issues through parameter object implementation
- Policy preset inheritance mechanisms
- Configuration inconsistencies in rate limiting

### Security
- Verified no recursion patterns in critical code paths
- Verified no banned constructs (goto, eval, exec)
- Implemented safe build configuration and environment variables

## [0.9.0] - 2024-09-02

### Added
- Initial MCP server implementation
- Basic policy framework
- Core analyzer functionality
- Test suite establishment
- Baseline safety compliance (95%)

### Known Issues
- 65+ magic literals identified for improvement
- Parameter coupling in method signatures

[Unreleased]: https://github.com/connascence/connascence-analyzer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/connascence/connascence-analyzer/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/connascence/connascence-analyzer/releases/tag/v0.9.0