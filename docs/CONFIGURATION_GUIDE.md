# Connascence Safety Analyzer - Configuration Guide

## Overview

The Connascence Safety Analyzer provides comprehensive configuration options to customize analysis behavior, safety compliance levels, and performance settings. This guide covers all available configuration options and how to use them effectively.

## Configuration Sources

Configuration can be set through:
1. **VS Code Settings UI** - User-friendly interface
2. **Advanced Settings Panel** - Comprehensive configuration webview
3. **settings.json** - Direct JSON configuration
4. **Configuration Import/Export** - Share configurations across teams

## Configuration Categories

### 1. Safety & Framework Profiles

#### Safety Profile (`connascence.safetyProfile`)
Controls the strictness level of safety compliance checks.

- `none` - No safety enforcement
- `modern_general` - Balanced approach for modern development (default)
- `general_safety_strict` - Strict safety rules for general applications
- `safety_level_1` - Highest safety level (critical systems)
- `safety_level_3` - High safety level (important systems)

**Example:**
```json
{
  "connascence.safetyProfile": "safety_level_1"
}
```

#### Framework Profile (`connascence.frameworkProfile`)
Enables framework-specific analysis patterns.

- `generic` - Universal patterns (default)
- `django` - Django-specific patterns (models, views, migrations)
- `fastapi` - FastAPI patterns (dependency injection, async, schemas)
- `react` - React patterns (components, hooks, state management)

**Example:**
```json
{
  "connascence.frameworkProfile": "django"
}
```

### 2. Analysis Configuration

#### Analysis Depth (`connascence.analysisDepth`)
Controls thoroughness vs performance tradeoff.

- `surface` - Fast, surface-level analysis
- `standard` - Balanced analysis (default)
- `deep` - Thorough analysis (slower)
- `comprehensive` - Most thorough analysis (slowest)

#### Confidence Threshold (`connascence.confidenceThreshold`)
Minimum confidence level for analysis suggestions (0.0-1.0).

- Lower values: More suggestions, potentially more false positives
- Higher values: Fewer suggestions, higher accuracy
- Default: `0.8`

**Example:**
```json
{
  "connascence.analysisDepth": "deep",
  "connascence.confidenceThreshold": 0.9
}
```

#### NASA Compliance Threshold (`connascence.nasaComplianceThreshold`)
Threshold for NASA safety standard compliance (0.0-1.0).

- Default: `0.95`
- Used when safety profiles with NASA compliance are active
- Higher values enforce stricter compliance

#### MECE Quality Threshold (`connascence.meceQualityThreshold`)
Mutually Exclusive, Collectively Exhaustive quality threshold (0.0-1.0).

- Default: `0.85`
- Ensures code organization follows MECE principles
- Higher values enforce stricter organization

### 3. File Filtering

#### Include Patterns (`connascence.includePatterns`)
File patterns to include in analysis.

**Default:**
```json
{
  "connascence.includePatterns": [
    "**/*.py",
    "**/*.c",
    "**/*.cpp",
    "**/*.js",
    "**/*.ts"
  ]
}
```

#### Exclude Patterns (`connascence.excludePatterns`)
File patterns to exclude from analysis.

**Default:**
```json
{
  "connascence.excludePatterns": [
    "**/node_modules/**",
    "**/venv/**",
    "**/env/**",
    "**/__pycache__/**",
    "**/dist/**",
    "**/build/**",
    "**/.git/**"
  ]
}
```

### 4. Performance Settings

#### Performance Analysis Configuration (`connascence.performanceAnalysis`)

```json
{
  "connascence.performanceAnalysis": {
    "enableProfiling": true,
    "maxAnalysisTime": 30000,
    "memoryThreshold": 512,
    "enableCaching": true,
    "cacheSize": 1000
  }
}
```

**Options:**
- `enableProfiling` - Track performance metrics during analysis
- `maxAnalysisTime` - Maximum time per file in milliseconds (default: 30000)
- `memoryThreshold` - Memory usage threshold in MB for warnings (default: 512)
- `enableCaching` - Enable result caching for better performance
- `cacheSize` - Maximum number of cached results (default: 1000)

### 5. Advanced Filtering

#### Advanced Filtering Configuration (`connascence.advancedFiltering`)

```json
{
  "connascence.advancedFiltering": {
    "enableGitIgnore": true,
    "enableCustomIgnore": true,
    "minFileSize": 10,
    "maxFileSize": 10485760,
    "excludeBinaryFiles": true
  }
}
```

**Options:**
- `enableGitIgnore` - Respect .gitignore patterns
- `enableCustomIgnore` - Enable .connascence-ignore file
- `minFileSize` - Skip files smaller than this size in bytes (default: 10)
- `maxFileSize` - Skip files larger than this size in bytes (default: 10MB)
- `excludeBinaryFiles` - Automatically exclude binary files

### 6. Custom Analysis Rules

#### Custom Rules (`connascence.customRules`)
Define custom patterns to detect in your code.

```json
{
  "connascence.customRules": [
    {
      "name": "Avoid Global Variables",
      "pattern": "^\\s*global\\s+\\w+",
      "severity": "warning",
      "message": "Global variables should be avoided for better code maintainability"
    },
    {
      "name": "TODO Comments",
      "pattern": "(?i)todo|fixme|hack",
      "severity": "info",
      "message": "TODO comment found - consider creating a proper issue"
    }
  ]
}
```

**Rule Properties:**
- `name` - Human-readable name for the rule
- `pattern` - Regular expression pattern to match
- `severity` - `error`, `warning`, `info`, or `hint`
- `message` - Message displayed when pattern is found

### 7. Experimental Features

#### Enable Experimental Features (`connascence.enableExperimentalFeatures`)
Enable features that may be unstable or change in future versions.

- Default: `false`
- Use with caution in production environments
- May include AI-powered suggestions, advanced refactoring, etc.

## Safety Profile Details

### Safety Level 1 (Highest)
- **Max Complexity**: 5
- **Max Nested Loops**: 1  
- **Max Function Parameters**: 3
- **Max Line Length**: 80
- **Requires**: Docstrings, type hints
- **Prohibits**: Recursion, dynamic allocation
- **NASA Compliance**: Enabled

### Safety Level 3 (High)
- **Max Complexity**: 15
- **Max Nested Loops**: 3
- **Max Function Parameters**: 6
- **Max Line Length**: 120
- **Requires**: Docstrings, type hints
- **NASA Compliance**: Enabled

### General Safety Strict
- **Max Complexity**: 10
- **Max Nested Loops**: 2
- **Max Function Parameters**: 4
- **Max Line Length**: 80
- **Requires**: Docstrings, type hints
- **NASA Compliance**: Enabled

### Modern General (Default)
- **Max Complexity**: 20
- **Max Nested Loops**: 4
- **Max Function Parameters**: 8
- **Max Line Length**: 120
- **Requirements**: Flexible approach
- **NASA Compliance**: Disabled

## Framework Profile Details

### Django Profile
**Additional checks:**
- Model validation (relationships, field types)
- View complexity analysis
- Migration safety checks
- Settings validation
- ORM pattern detection
- Security pattern analysis
- Middleware complexity

### FastAPI Profile
**Additional checks:**
- Dependency injection patterns
- Schema validation (Pydantic)
- Route complexity analysis
- Async/await pattern validation
- Swagger/OpenAPI compliance
- Authentication patterns

### React Profile
**Additional checks:**
- Component complexity analysis
- Hook usage validation
- State management patterns
- Prop validation
- JSX pattern analysis
- Performance patterns (memo, callback)
- Accessibility checks

## Configuration Management

### Export Configuration
```typescript
// Via Settings Panel
settingsPanel.exportConfiguration();

// Via Command Palette
> Connascence: Export Analysis Report
```

### Import Configuration
```typescript
// Via Settings Panel
settingsPanel.importConfiguration();

// Programmatic import
configService.importConfiguration(configData);
```

### Reset to Defaults
```typescript
// Via Settings Panel
settingsPanel.resetConfiguration();

// Programmatic reset
configService.resetToDefaults();
```

## Best Practices

### 1. Team Configuration
- Use workspace settings for team consistency
- Export/import configurations for onboarding
- Document custom rules with clear rationale

### 2. Performance Optimization
- Start with `surface` analysis depth for large codebases
- Adjust `maxAnalysisTime` based on typical file sizes
- Enable caching for better interactive performance
- Use exclude patterns to skip generated/vendor code

### 3. Safety Compliance
- Choose appropriate safety profile for your domain
- Gradually increase safety level as codebase matures
- Use custom rules to enforce organization-specific patterns

### 4. Framework Integration
- Select framework profile matching your tech stack
- Combine with appropriate safety profile
- Adjust confidence thresholds based on framework complexity

## Validation and Debugging

### Configuration Validation
The extension automatically validates configuration changes and provides feedback:

- Invalid safety profiles are rejected
- Confidence thresholds must be between 0.0 and 1.0
- Custom rule patterns are validated for regex syntax
- File size limits are enforced

### Debug Configuration
To debug configuration issues:

1. Check VS Code Developer Console for errors
2. Use "Connascence: Generate Quality Report" to see active settings
3. Export configuration to verify current values
4. Reset to defaults if configuration becomes corrupted

## Migration Guide

### From Version 1.x to 2.x
- `exclude` renamed to `excludePatterns`
- `include` renamed to `includePatterns`
- `debounceDelay` renamed to `debounceMs`
- New advanced configuration options added
- Safety profile names updated for clarity

### Configuration Migration
The extension automatically migrates old configuration keys to new format. No manual action required for most settings.

## Examples

### High-Security Environment
```json
{
  "connascence.safetyProfile": "safety_level_1",
  "connascence.analysisDepth": "comprehensive",
  "connascence.confidenceThreshold": 0.95,
  "connascence.nasaComplianceThreshold": 0.98,
  "connascence.enableExperimentalFeatures": false,
  "connascence.performanceAnalysis": {
    "enableProfiling": true,
    "maxAnalysisTime": 60000,
    "enableCaching": false
  }
}
```

### Fast Development Environment
```json
{
  "connascence.safetyProfile": "modern_general",
  "connascence.analysisDepth": "surface",
  "connascence.confidenceThreshold": 0.7,
  "connascence.performanceAnalysis": {
    "enableProfiling": false,
    "maxAnalysisTime": 10000,
    "enableCaching": true,
    "cacheSize": 2000
  }
}
```

### Django Project
```json
{
  "connascence.safetyProfile": "general_safety_strict",
  "connascence.frameworkProfile": "django",
  "connascence.analysisDepth": "standard",
  "connascence.customRules": [
    {
      "name": "Django Model Field Ordering",
      "pattern": "class.*Model.*:\\s*[^\\n]*\\n(?:\\s*[^\\n]*\\n)*\\s*created_at.*\\n(?:\\s*[^\\n]*\\n)*\\s*updated_at",
      "severity": "hint",
      "message": "Consider placing timestamp fields at the end of model definition"
    }
  ]
}
```

## Support and Troubleshooting

For configuration issues:
1. Check the VS Code Developer Console
2. Verify JSON syntax in settings.json
3. Use the Settings Panel for guided configuration
4. Reset to defaults and reconfigure incrementally
5. Report issues with configuration export attached

## API Reference

### ConfigurationService Methods
- `getSafetyProfile()` - Get current safety profile
- `getFrameworkProfile()` - Get current framework profile
- `getConfidenceThreshold()` - Get confidence threshold
- `exportConfiguration()` - Export all settings
- `importConfiguration(data)` - Import settings
- `resetToDefaults()` - Reset all settings
- `validateCustomRule(rule)` - Validate custom rule