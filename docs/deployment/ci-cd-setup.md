# CI/CD Setup Guide - Connascence Safety Analyzer

## Overview

This guide consolidates CI/CD integration patterns from across the system, including GitHub Actions, pre-commit hooks, and enterprise pipeline integration.

## 🚀 **Quick Setup for This Repository**

### **1. Enable NASA Compliance Workflow**

The workflow already exists at `.github/workflows/nasa-compliance-check.yml`:

```yaml
name: NASA Power of Ten Compliance Check
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  nasa-compliance:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run NASA Compliance Analysis
      run: |
        python -m analyzer.core --path . --policy nasa_jpl_pot10 --format sarif
        python -m policy.presets.general_safety_rules --validate --strict
    
    - name: Upload SARIF results
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: analysis_results.sarif
```

### **2. Self-Analysis Dashboard Integration**

Enable continuous self-monitoring:

```bash
# Add to .github/workflows/self-analysis.yml
name: Self Analysis
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  self-analysis:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Self Analysis
      run: |
        python -m analyzer.core --path . --policy strict-core --export-dashboard
        python scripts/verify_counts.py --verbose
    
    - name: Update Analysis Dashboard
      run: |
        python -m dashboard.ci_integration --update-dashboard
        python -m dashboard.metrics --generate-trends
```

## 🔧 **Pre-commit Integration**

### **Setup Pre-commit Hooks**

Based on `examples/pre_commit_integration.py`:

```python
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: connascence-analysis
        name: Connascence Safety Analysis
        entry: python -m analyzer.core
        args: ['--path', '.', '--policy', 'nasa_jpl_pot10', '--fail-on-critical']
        language: python
        files: \.(py|js|ts|c|cpp|h)$
        
      - id: nasa-compliance
        name: NASA Power of Ten Rules
        entry: python -m policy.presets.general_safety_rules
        args: ['--validate', '--fail-on-violation']
        language: python
        files: \.(py|c|cpp|h)$
        
      - id: mece-analysis
        name: MECE Duplication Check
        entry: python -m analyzer.dup_detection.mece_analyzer
        args: ['--path', '.', '--threshold', '0.8']
        language: python
        pass_filenames: false
```

### **Install Pre-commit**

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files (first time)
pre-commit run --all-files
```

## 🏢 **Enterprise CI/CD Integration**

### **GitHub Actions Enterprise**

Complete workflow from `examples/ci_integration.yaml`:

```yaml
name: Enterprise Connascence Analysis
on:
  push:
    branches: [main, develop, release/*]
  pull_request:
    branches: [main, develop]

jobs:
  security-analysis:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Full history for trend analysis
    
    - name: Security Scan
      run: |
        python -m integrations.bandit_integration --security-focused
        python -m policy.presets.general_safety_rules --security-rules
    
    - name: Upload Security Results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: security_analysis.sarif

  quality-analysis:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Enhanced Tool Coordination
      run: |
        # Run all 6 integrated tools
        python -m integrations.enhanced_tool_coordinator --run-all
        
        # Cross-tool correlation analysis
        python -m integrations.enhanced_tool_coordinator --correlate --confidence-threshold 0.8
    
    - name: MECE Analysis
      run: |
        python -m analyzer.dup_detection.mece_analyzer --comprehensive
        python -m analyzer.dup_detection.mece_analyzer --export-recommendations

  performance-analysis:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Performance Benchmarks
      run: |
        python -m analyzer.performance_benchmarks --run-suite
        python scripts/reproduce_enterprise_demo.py --validate-performance
    
    - name: Trend Analysis
      run: |
        python -m dashboard.metrics --calculate-trends
        python -m dashboard.ci_integration --update-metrics

  report-generation:
    needs: [security-analysis, quality-analysis, performance-analysis]
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Generate Comprehensive Report
      run: |
        python -m dashboard.ci_integration --generate-comprehensive-report
        python scripts/verify_counts.py --generate-validation-report
    
    - name: Upload Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: analysis-reports
        path: |
          analysis_results.sarif
          dashboard_data.json
          comprehensive_report.html
          validation_report.json
```

### **Jenkins Integration**

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.12'
        CONNASCENCE_POLICY = 'nasa_jpl_pot10'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    python -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('NASA Compliance') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m analyzer.core --path . --policy $CONNASCENCE_POLICY --format sarif
                    python -m policy.presets.general_safety_rules --validate --jenkins-output
                '''
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'nasa_compliance_report.html',
                        reportName: 'NASA Compliance Report'
                    ])
                }
            }
        }
        
        stage('MECE Analysis') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m analyzer.dup_detection.mece_analyzer --comprehensive --jenkins
                '''
            }
        }
        
        stage('Tool Integration') {
            parallel {
                stage('Ruff Analysis') {
                    steps {
                        sh '. venv/bin/activate && python -m integrations.ruff_integration'
                    }
                }
                stage('MyPy Analysis') {
                    steps {
                        sh '. venv/bin/activate && python -m integrations.mypy_integration'
                    }
                }
                stage('Radon Analysis') {
                    steps {
                        sh '. venv/bin/activate && python -m integrations.radon_integration'
                    }
                }
                stage('Bandit Analysis') {
                    steps {
                        sh '. venv/bin/activate && python -m integrations.bandit_integration'
                    }
                }
                stage('Black Analysis') {
                    steps {
                        sh '. venv/bin/activate && python -m integrations.black_integration'
                    }
                }
                stage('Build Flags Analysis') {
                    steps {
                        sh '. venv/bin/activate && python -m integrations.build_flags_integration'
                    }
                }
            }
        }
        
        stage('Cross-Tool Correlation') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m integrations.enhanced_tool_coordinator --correlate --confidence-threshold 0.8
                '''
            }
        }
        
        stage('Report Generation') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m dashboard.ci_integration --generate-jenkins-report
                '''
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '*.sarif, *.json, *.html', allowEmptyArchive: true
            
            script {
                // Parse SARIF results for Jenkins
                def sarifResults = readJSON file: 'analysis_results.sarif'
                currentBuild.description = "Violations: ${sarifResults.runs[0].results.size()}"
            }
        }
        
        failure {
            emailext (
                subject: "Connascence Analysis Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "The connascence analysis pipeline failed. Check the build logs for details.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
```

### **Azure DevOps Pipeline**

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
    - main
    - develop
    - release/*

pr:
  branches:
    include:
    - main
    - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  PYTHON_VERSION: '3.12'
  CONNASCENCE_POLICY: 'nasa_jpl_pot10'

stages:
- stage: Analysis
  displayName: 'Connascence Analysis'
  jobs:
  - job: NASACompliance
    displayName: 'NASA Power of Ten Compliance'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: $(PYTHON_VERSION)
    
    - script: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
      displayName: 'Install dependencies'
    
    - script: |
        python -m analyzer.core --path . --policy $(CONNASCENCE_POLICY) --format sarif
        python -m policy.presets.general_safety_rules --validate --azure-devops
      displayName: 'NASA Compliance Check'
    
    - task: PublishTestResults@2
      inputs:
        testResultsFormat: 'JUnit'
        testResultsFiles: 'nasa_compliance_results.xml'
      condition: always()

  - job: MECEAnalysis  
    displayName: 'MECE Duplication Analysis'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: $(PYTHON_VERSION)
    
    - script: |
        pip install -r requirements.txt
        python -m analyzer.dup_detection.mece_analyzer --comprehensive --azure-devops
      displayName: 'MECE Analysis'

  - job: ToolIntegration
    displayName: 'Enhanced Tool Coordination'  
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: $(PYTHON_VERSION)
    
    - script: |
        pip install -r requirements.txt
        python -m integrations.enhanced_tool_coordinator --run-all --azure-devops
      displayName: 'Tool Coordination'

- stage: Reporting
  displayName: 'Generate Reports'
  dependsOn: Analysis
  jobs:
  - job: ComprehensiveReport
    displayName: 'Comprehensive Reporting'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: $(PYTHON_VERSION)
    
    - script: |
        pip install -r requirements.txt
        python -m dashboard.ci_integration --generate-azure-report
      displayName: 'Generate Reports'
    
    - task: PublishHtmlReport@1
      inputs:
        reportDir: '.'
        tabName: 'Connascence Analysis'
```

## ⚙️ **Configuration Management**

### **Policy Presets**

Available in `policy/presets/general_safety_rules.py`:

```python
POLICY_PRESETS = {
    'nasa_jpl_pot10': {
        'max_parameters': 3,
        'max_function_lines': 60,
        'max_cyclomatic_complexity': 10,
        'require_assertions': True,
        'disallow_recursion': True,
        'max_pointer_levels': 1
    },
    
    'strict-core': {
        'max_parameters': 2,
        'max_function_lines': 40,
        'max_cyclomatic_complexity': 8,
        'max_god_object_methods': 10,
        'mece_threshold': 0.9
    },
    
    'enterprise-standard': {
        'max_parameters': 5,
        'max_function_lines': 100,
        'max_cyclomatic_complexity': 15,
        'enable_cross_tool_correlation': True,
        'confidence_threshold': 0.8
    }
}
```

### **Tool Configuration**

Enhanced tool coordinator settings in `integrations/enhanced_tool_coordinator.py`:

```python
TOOL_CONFIGS = {
    'ruff': {
        'enabled': True,
        'config_file': 'policy/enhanced-ruff-config.toml',
        'confidence': 0.95,
        'correlates_with': ['meaning', 'position']
    },
    
    'mypy': {
        'enabled': True,
        'strict_mode': True,
        'confidence': 0.95,
        'correlates_with': ['type', 'meaning']
    },
    
    'radon': {
        'enabled': True,
        'complexity_threshold': 10,
        'confidence': 0.85,
        'correlates_with': ['god_object', 'complexity']
    }
}
```

## 📊 **Quality Gates**

### **GitHub Status Checks**

```python
# dashboard/ci_integration.py
def set_github_status(violations: List[Violation], policy: str) -> None:
    """Set GitHub commit status based on analysis results"""
    
    critical_count = len([v for v in violations if v.severity == 'critical'])
    
    if critical_count == 0:
        status = 'success'
        description = 'No critical violations found'
    elif critical_count <= POLICY_THRESHOLDS[policy]['max_critical']:
        status = 'success' 
        description = f'{critical_count} critical violations (within threshold)'
    else:
        status = 'failure'
        description = f'{critical_count} critical violations exceed threshold'
    
    # Set GitHub status via API
    github_api.set_status(status, description, 'connascence-analysis')
```

### **Fail Conditions**

```python
# Configurable failure thresholds per policy
FAIL_CONDITIONS = {
    'nasa_jpl_pot10': {
        'max_critical_violations': 0,
        'max_nasa_rule_violations': 0,
        'min_compliance_score': 1.0
    },
    
    'strict-core': {
        'max_critical_violations': 5,
        'max_god_objects': 0,
        'min_mece_score': 0.9
    },
    
    'enterprise-standard': {
        'max_critical_violations': 20,
        'max_high_violations': 100,
        'min_overall_quality_score': 0.7
    }
}
```

## 🔍 **Troubleshooting**

### **Common CI/CD Issues**

1. **Python Version Conflicts**
```bash
# Ensure consistent Python version
python --version  # Should be 3.9+
pip install --upgrade pip setuptools wheel
```

2. **Missing Dependencies**
```bash
# Install all requirements including dev dependencies  
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Permission Issues**
```bash
# Ensure proper permissions for analysis scripts
chmod +x scripts/*.py
chmod +x scripts/*.sh
```

4. **Memory Issues on Large Codebases**
```bash
# Increase memory limits for CI runners
export PYTHONHASHSEED=0
export MALLOC_TRIM_THRESHOLD_=100000
```

### **Performance Optimization**

1. **Parallel Analysis**
```python
# Enable parallel processing in CI
python -m analyzer.core --parallel --max-workers 4
```

2. **Incremental Analysis**
```bash
# Analyze only changed files in PR
git diff --name-only HEAD^ | python -m analyzer.core --stdin --incremental
```

3. **Caching**
```yaml
# GitHub Actions caching
- name: Cache Analysis Results
  uses: actions/cache@v3
  with:
    path: |
      .connascence-cache/
      ~/.cache/pip
    key: connascence-${{ hashFiles('**/*.py') }}
```

## 📈 **Monitoring & Metrics**

### **Dashboard Integration**

Real-time monitoring via `dashboard/ci_integration.py`:

```python
def update_ci_metrics(build_id: str, analysis_result: AnalysisResult) -> None:
    """Update CI dashboard with latest metrics"""
    
    metrics = {
        'build_id': build_id,
        'timestamp': datetime.now().isoformat(),
        'total_violations': len(analysis_result.violations),
        'by_severity': analysis_result.severity_breakdown,
        'nasa_compliance_score': analysis_result.nasa_compliance.score,
        'mece_score': analysis_result.mece_analysis.score,
        'tool_correlations': analysis_result.tool_correlations
    }
    
    # Store in dashboard database
    dashboard_db.store_ci_metrics(metrics)
    
    # Send to monitoring systems
    if MONITORING_WEBHOOK:
        send_webhook(MONITORING_WEBHOOK, metrics)
```

### **Trend Analysis**

Historical tracking in `dashboard/metrics.py`:

```python
def calculate_quality_trends(days: int = 30) -> TrendAnalysis:
    """Calculate quality trends over time"""
    
    historical_data = dashboard_db.get_metrics_since(days_ago=days)
    
    trends = {
        'violation_trend': calculate_trend([d['total_violations'] for d in historical_data]),
        'compliance_trend': calculate_trend([d['nasa_compliance_score'] for d in historical_data]),
        'mece_trend': calculate_trend([d['mece_score'] for d in historical_data])
    }
    
    return TrendAnalysis(trends, historical_data)
```

---

**This CI/CD setup enables:**
- ✅ **Automated Quality Gates** - Block PRs with critical violations
- ✅ **Multi-Platform Support** - GitHub, Jenkins, Azure DevOps
- ✅ **Comprehensive Analysis** - NASA compliance + MECE + tool correlation
- ✅ **Real-time Monitoring** - Dashboard integration with trend analysis
- ✅ **Enterprise Scale** - Performance optimized for large codebases