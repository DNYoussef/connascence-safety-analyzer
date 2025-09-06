# Self-Analysis Framework

## Overview

The Self-Analysis Framework enables the Connascence Safety Analyzer to analyze its own codebase, providing insights into code quality, architectural decisions, and identifying areas for improvement within the analysis system itself.

## Framework Components

### 1. Recursive Analysis Capability

The analyzer can analyze its own source code using the same engines that analyze external projects:

```bash
# Analyze the analyzer itself
python -m analyzer.core --path . --policy nasa_jpl_pot10 --include-mece-analysis
```

### 2. Bootstrap Analysis

**Purpose**: Verify the analyzer produces consistent results on known codebases.

**Process**:
1. Run analysis on analyzer source code
2. Compare results against expected patterns
3. Validate that critical analysis features work correctly
4. Ensure no regressions in core detection capabilities

### 3. Meta-Analysis Validation

**Capability**: The analyzer can verify its own analysis results for correctness:

```bash
# Self-validation cycle
python -m analyzer.core --path analyzer/ --policy strict-core --format json --output self_analysis.json
python -m analyzer.core --path . --policy default --include-mece-analysis --output full_self_analysis.json
```

## Self-Analysis Use Cases

### 1. Quality Assurance

**Dogfooding**: Using the tool on itself to ensure:
- All connascence types are properly detected
- NASA compliance rules work correctly  
- MECE duplication detection functions as expected
- Report formats are correctly generated

### 2. Regression Testing

**Continuous Validation**: 
- Run self-analysis as part of CI/CD pipeline
- Compare results against baseline to detect regressions
- Ensure new features don't break existing detection

### 3. Performance Benchmarking

**Self-Performance Analysis**:
- Measure analysis time on known codebase (itself)
- Track memory usage patterns
- Identify performance bottlenecks in analysis pipeline

### 4. Feature Validation

**New Feature Testing**:
- Test new connascence types on analyzer codebase
- Validate severity calculations
- Ensure new policies work correctly

## Expected Self-Analysis Results

### Typical Findings in Analyzer Codebase

Based on actual analysis of the analyzer source:

1. **Magic Literals (CoM)**: Configuration values, thresholds, constants
2. **Algorithm Duplications (CoA)**: Similar parsing patterns across engines  
3. **Parameter Coupling (CoP)**: Complex function signatures in analyzers
4. **Name Coupling (CoN)**: Import dependencies between modules

### Baseline Metrics

**Quality Expectations**:
- Overall Quality Score: >0.80 (good maintainability)
- NASA Compliance: >0.90 (safety-focused design)
- MECE Score: >0.75 (reasonable duplication levels)

**Violation Distribution**:
- CoM (Magic Literals): ~60-70% of violations (normal for analysis tools)
- CoA (Algorithm): ~15-20% (parsing similarities acceptable)
- CoP (Position): ~10-15% (complex analysis requires parameters)
- Other types: <10% each

## Self-Analysis Commands

### Basic Self-Analysis
```bash
# Quick self-check
python -m analyzer.core --path analyzer/ --format json

# NASA compliance self-check
python -m analyzer.core --path . --policy nasa_jpl_pot10 --nasa-validation
```

### Comprehensive Self-Analysis
```bash
# Full analysis with all features
python -m analyzer.core \
  --path . \
  --policy strict-core \
  --format sarif \
  --output self_analysis.sarif \
  --include-god-objects \
  --include-mece-analysis \
  --include-nasa-rules
```

### MECE Self-Analysis
```bash
# Focus on code duplication within analyzer
python -m analyzer.dup_detection.mece_analyzer \
  --path analyzer/ \
  --comprehensive \
  --threshold 0.7 \
  --output analyzer_duplications.json
```

### Exclusion-Based Analysis
```bash
# Exclude test files and focus on core logic
python -m analyzer.core \
  --path . \
  --exclude "tests/" "__pycache__/" ".git/" "docs/" \
  --policy default \
  --format json \
  --output core_analysis.json
```

## Interpreting Self-Analysis Results

### Expected Patterns

1. **High CoM Count**: Analysis tools contain many thresholds and configuration values
2. **Moderate CoA Count**: Similar parsing patterns across different analyzers
3. **Low God Objects**: Well-architected analysis system should have focused classes
4. **Good NASA Compliance**: Safety-focused tools should meet NASA standards

### Red Flags

1. **Critical Violations**: Should not exist in analysis tool itself
2. **Low Overall Quality**: <0.70 indicates tool needs refactoring
3. **God Objects in Core**: Single classes >500 lines or >20 methods
4. **High Parameter Coupling**: Functions with >6 parameters violate NASA rules

## Continuous Self-Analysis

### CI/CD Integration

Add self-analysis to continuous integration:

```yaml
# Example GitHub Actions step
- name: Self-Analysis Quality Check
  run: |
    python -m analyzer.core --path . --policy strict-core --format json --output ci_self_analysis.json
    # Parse results and fail if quality below threshold
```

### Trend Monitoring

**Track Quality Over Time**:
- Monitor self-analysis results over multiple versions
- Alert on quality regression
- Track improvement in self-compliance

### Self-Improvement Loop

1. **Analyze**: Run self-analysis to identify issues
2. **Prioritize**: Focus on violations that impact analyzer reliability
3. **Fix**: Improve code quality in analyzer itself
4. **Validate**: Re-run analysis to confirm improvements
5. **Repeat**: Continuous improvement cycle

## Framework Benefits

### 1. Reliability Assurance
- Ensures the analyzer works correctly on real code (itself)
- Catches regressions in analysis logic
- Validates new features against known codebase

### 2. Quality Leadership
- Demonstrates commitment to code quality
- Shows analyzer follows its own recommendations  
- Builds confidence in analysis results

### 3. Development Efficiency
- Quick validation of changes
- Automated quality checks
- Performance benchmarking on consistent codebase

## Limitations

### 1. Analysis Scope
- Self-analysis only covers Python code (full AST analysis)
- Cannot test multi-language analysis capabilities on itself
- Limited to analyzer's own architectural patterns

### 2. Baseline Drift
- Expected results may change as analyzer evolves
- Need to update baselines with intentional changes
- Distinguish between improvements and regressions

### 3. Circular Dependencies
- Cannot use self-analysis to validate fundamental analysis logic
- Requires external validation for core engine correctness
- Risk of self-confirming incorrect analysis

## Best Practices

### 1. Regular Self-Analysis
- Run self-analysis before each release
- Include in CI/CD pipeline
- Monitor trends over time

### 2. Baseline Management
- Maintain expected result baselines
- Update baselines only for intentional changes
- Document reasons for baseline changes

### 3. Result Validation
- Compare self-analysis with external code analysis tools
- Use self-analysis to validate new features
- Ensure consistency across different analysis modes

The Self-Analysis Framework provides confidence in the analyzer's reliability and demonstrates commitment to code quality by applying the same standards to itself that it applies to analyzed code.