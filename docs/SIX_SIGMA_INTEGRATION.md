# Six Sigma Integration for Connascence Analyzer

## Overview

The Six Sigma quality management system has been successfully integrated into the Connascence analyzer, providing enterprise-grade quality metrics and continuous improvement capabilities.

## Components

### 1. Core Modules

#### SixSigmaTelemetry (`telemetry.py`)
- Tracks Defects Per Million Opportunities (DPMO)
- Calculates Rolled Throughput Yield (RTY)
- Determines Sigma Level (1σ to 6σ)
- Records connascence violations with severity weighting
- Provides trend analysis over time

#### SixSigmaAnalyzer (`analyzer.py`)
- Analyzes connascence violations using Six Sigma methodology
- Generates DMAIC improvement plans
- Performs Pareto analysis (80/20 rule)
- Creates impact-effort matrices for prioritization
- Identifies root causes and quick wins

#### CTQCalculator (`calculator.py`)
- Calculates Critical To Quality metrics
- Evaluates maintainability, complexity, coupling, cohesion
- Provides weighted composite scoring
- Identifies improvement priorities

#### ProcessCapability (`calculator.py`)
- Calculates Cp, Cpk, Pp, Ppk indices
- Analyzes process centering and variation
- Predicts defect rates
- Generates capability recommendations

#### Integration Module (`integration.py`)
- Bridges connascence detection with Six Sigma metrics
- Provides quality gate decisions for CI/CD
- Generates executive reports
- Exports dashboard-ready data

## Features

### Quality Levels
- **Six Sigma (6σ)**: 3.4 DPMO - World Class
- **Five Sigma (5σ)**: 233 DPMO - Enterprise Excellence
- **Four Sigma (4σ)**: 6,210 DPMO - Industry Standard
- **Three Sigma (3σ)**: 66,807 DPMO - Baseline Acceptable

### Connascence-Specific Opportunities
Each connascence type has weighted opportunity values:
- **Timing**: 8 opportunities (highest impact)
- **Execution**: 7 opportunities
- **Algorithm**: 6 opportunities
- **Identity**: 5 opportunities
- **Meaning**: 4 opportunities
- **Type**: 4 opportunities
- **Position**: 3 opportunities
- **Values**: 3 opportunities
- **Convention**: 2 opportunities (lowest impact)

Critical violations receive 2x multiplier for opportunities.

### Quality Gates
Automated pass/fail decisions based on:
- Sigma Level threshold (default: 4.0σ)
- DPMO threshold (default: 6,210)
- RTY threshold (default: 80%)
- Critical violations (must be 0)

### DMAIC Improvement Plans
Structured improvement methodology:
1. **Define**: Problem statement and goals
2. **Measure**: Current state metrics
3. **Analyze**: Root cause analysis and Pareto charts
4. **Improve**: Quick wins and systematic improvements
5. **Control**: Monitoring and sustainability measures

## Usage

### Basic Analysis
```python
from analyzer.enterprise.sixsigma import SixSigmaAnalyzer

analyzer = SixSigmaAnalyzer(target_level="enterprise")
violations = [
    {'type': 'timing', 'severity': 'high'},
    {'type': 'algorithm', 'severity': 'critical'}
]
result = analyzer.analyze_violations(violations)
print(f"Sigma Level: {result.sigma_level}")
print(f"DPMO: {result.dpmo}")
```

### CI/CD Integration
```python
from analyzer.enterprise.sixsigma.integration import ConnascenceSixSigmaIntegration

integration = ConnascenceSixSigmaIntegration(target_sigma_level=5.0)
exit_code = integration.integrate_with_ci_cd(
    analysis_results,
    fail_on_quality_gate=True
)
```

### Executive Reporting
```python
report = integration.generate_executive_report(analysis_results)
print(report)
```

### Dashboard Export
```python
dashboard_data = integration.export_dashboard_data(
    analysis_results,
    Path('./six-sigma-metrics.json')
)
```

## Performance Impact

The Six Sigma integration maintains minimal overhead:
- **Target**: <1.2% performance impact
- **Memory**: ~2MB additional for telemetry history
- **Processing**: O(n) complexity for violation analysis

## Integration with Existing Connascence Analysis

The Six Sigma system enhances existing analysis by:
1. Adding quality metrics to violation reports
2. Providing trend analysis across analyses
3. Enabling quality gate enforcement
4. Supporting continuous improvement cycles
5. Facilitating executive-level reporting

## Testing

Comprehensive test suite available:
```bash
pytest tests/test_sixsigma_integration.py -v
```

Tests cover:
- Telemetry recording and metrics
- Analyzer calculations
- CTQ metrics
- Process capability
- Integration features
- Quality gates
- Executive reports
- Dashboard exports
- CI/CD integration

## Configuration

### Environment Variables
- `CONNASCENCE_SIGMA_TARGET`: Target sigma level (default: 5.0)
- `CONNASCENCE_DPMO_THRESHOLD`: Maximum acceptable DPMO (default: 233)
- `CONNASCENCE_QUALITY_GATE`: Enable/disable quality gates (default: true)

### Quality Profiles
- **world_class**: 6σ target, 3.4 DPMO
- **enterprise**: 5σ target, 233 DPMO
- **standard**: 4σ target, 6,210 DPMO
- **baseline**: 3σ target, 66,807 DPMO

## Benefits

1. **Quantifiable Quality**: Transform subjective code quality into objective metrics
2. **Continuous Improvement**: Track progress over time with trend analysis
3. **Executive Visibility**: Provide C-level metrics for software quality
4. **Automated Gates**: Enforce quality standards in CI/CD pipelines
5. **Prioritized Actions**: Focus on high-impact improvements first
6. **Industry Standards**: Apply proven Six Sigma methodology to software

## Next Steps

1. Configure quality gates in CI/CD pipeline
2. Set up dashboard for continuous monitoring
3. Establish baseline metrics for your codebase
4. Define improvement targets
5. Implement automated fixes for common violations
6. Schedule regular quality reviews

## Support

For issues or questions about Six Sigma integration:
- See test examples in `/tests/test_sixsigma_integration.py`
- Review module documentation in `/analyzer/enterprise/sixsigma/`
- Check integration patterns in `integration.py`

---

*Six Sigma integration successfully ported from SPEK template to Connascence analyzer.*
*Achieving enterprise-grade quality through data-driven improvement.*