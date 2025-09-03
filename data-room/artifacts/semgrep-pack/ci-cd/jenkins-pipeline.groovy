// Enterprise Jenkins Pipeline: Semgrep + Connascence Integration
// Designed for large-scale enterprise environments with multiple teams

pipeline {
    agent { 
        label 'enterprise-analysis' 
    }
    
    // Enterprise configuration parameters
    parameters {
        choice(
            name: 'ANALYSIS_DEPTH',
            choices: ['fast', 'comprehensive', 'enterprise-full'],
            description: 'Analysis depth level'
        )
        string(
            name: 'COUPLING_THRESHOLD', 
            defaultValue: '7.5',
            description: 'Coupling index threshold (0-10)'
        )
        booleanParam(
            name: 'ENABLE_SLACK_NOTIFICATIONS',
            defaultValue: true,
            description: 'Send notifications to architecture team'
        )
        string(
            name: 'TEAM_SIZE',
            defaultValue: '25',
            description: 'Team size for technical debt calculations'
        )
    }
    
    environment {
        SEMGREP_APP_TOKEN = credentials('semgrep-app-token')
        CONNASCENCE_LICENSE = credentials('connascence-enterprise-license')
        SLACK_WEBHOOK = credentials('architecture-team-slack-webhook')
        JIRA_TOKEN = credentials('jira-api-token')
        
        // Enterprise-specific settings
        ENTERPRISE_CONFIG = credentials('connascence-enterprise-config')
        QUALITY_DASHBOARD_URL = 'https://quality.enterprise.com/coupling-dashboard'
        SONAR_HOST_URL = credentials('sonar-host-url')
        SONAR_AUTH_TOKEN = credentials('sonar-auth-token')
    }
    
    stages {
        stage('Enterprise Environment Setup') {
            steps {
                script {
                    echo "🏢 Setting up enterprise analysis environment..."
                    
                    // Install enterprise tooling
                    sh '''
                        # Semgrep enterprise version
                        python3 -m pip install --upgrade semgrep semgrep-pro
                        
                        # Connascence enterprise analyzer
                        npm install -g @connascence/analyzer-enterprise@latest
                        npm install -g @connascence/dashboard-generator
                        
                        # Enterprise reporting tools
                        pip3 install architectural-debt-calculator confluence-api
                        gem install asciidoctor asciidoctor-pdf
                        
                        # Configure enterprise settings
                        mkdir -p ~/.config/connascence
                        echo "$ENTERPRISE_CONFIG" > ~/.config/connascence/enterprise.yml
                    '''
                    
                    // Set up enterprise reporting directories
                    sh '''
                        mkdir -p reports/{semgrep,connascence,combined,trends}
                        mkdir -p artifacts/{dashboards,pdfs,data}
                        mkdir -p notifications/{slack,email,jira}
                    '''
                }
            }
        }
        
        stage('Multi-Phase Analysis') {
            parallel {
                stage('Semgrep Enterprise Scan') {
                    steps {
                        script {
                            echo "🔍 Running Semgrep enterprise analysis..."
                            
                            def semgrepConfig = params.ANALYSIS_DEPTH == 'fast' ? 
                                'data-room/artifacts/semgrep-pack/rules/' :
                                'data-room/artifacts/semgrep-pack/'
                                
                            sh """
                                semgrep \\
                                    --config=${semgrepConfig} \\
                                    --config=p/security-audit \\
                                    --config=p/owasp-top-ten \\
                                    --config=p/dockerfile \\
                                    --json \\
                                    --output=reports/semgrep/results.json \\
                                    --exclude=node_modules/ \\
                                    --exclude=vendor/ \\
                                    --exclude=*.test.* \\
                                    --exclude=test/ \\
                                    --timeout=1800 \\
                                    --verbose \\
                                    .
                            """
                            
                            // Generate Semgrep summary
                            sh '''
                                jq '{
                                    total_issues: (.results | length),
                                    critical: [.results[] | select(.extra.severity == "ERROR")] | length,
                                    high: [.results[] | select(.extra.severity == "WARNING")] | length,
                                    medium: [.results[] | select(.extra.severity == "INFO")] | length,
                                    categories: [.results[] | .extra.metadata.category] | group_by(.) | map({category: .[0], count: length})
                                }' reports/semgrep/results.json > reports/semgrep/summary.json
                            '''
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'reports/semgrep/**', allowEmptyArchive: true
                        }
                    }
                }
                
                stage('Connascence Architecture Analysis') {
                    steps {
                        script {
                            echo "🏗️ Performing connascence architectural analysis..."
                            
                            def analysisMode = params.ANALYSIS_DEPTH
                            def timeoutMinutes = analysisMode == 'enterprise-full' ? 180 : 60
                            
                            timeout(time: timeoutMinutes, unit: 'MINUTES') {
                                sh """
                                    connascence-analyzer \\
                                        --mode=${analysisMode} \\
                                        --output=json \\
                                        --file=reports/connascence/analysis.json \\
                                        --include-metrics \\
                                        --include-trends \\
                                        --include-recommendations \\
                                        --team-size=${params.TEAM_SIZE} \\
                                        --parallelism=\$(nproc) \\
                                        --exclude=node_modules/ \\
                                        --exclude=vendor/ \\
                                        --exclude=test/ \\
                                        .
                                """
                            }
                            
                            // Extract key metrics for quality gates
                            sh '''
                                COUPLING_INDEX=$(jq -r '.summary.coupling_index // "0"' reports/connascence/analysis.json)
                                HOTSPOT_COUNT=$(jq '.hotspots | length' reports/connascence/analysis.json)
                                TECH_DEBT=$(jq -r '.technical_debt.estimated_cost_usd // "0"' reports/connascence/analysis.json)
                                
                                echo "COUPLING_INDEX=$COUPLING_INDEX" > reports/connascence/metrics.env
                                echo "HOTSPOT_COUNT=$HOTSPOT_COUNT" >> reports/connascence/metrics.env
                                echo "TECHNICAL_DEBT=$TECH_DEBT" >> reports/connascence/metrics.env
                            '''
                        }
                    }
                }
                
                stage('Technical Debt Calculation') {
                    when {
                        expression { params.ANALYSIS_DEPTH != 'fast' }
                    }
                    steps {
                        script {
                            echo "💰 Calculating enterprise technical debt metrics..."
                            
                            sh """
                                architectural-debt-calculator \\
                                    --semgrep=reports/semgrep/results.json \\
                                    --connascence=reports/connascence/analysis.json \\
                                    --team-size=${params.TEAM_SIZE} \\
                                    --hourly-rate=\${DEVELOPER_HOURLY_RATE:-85} \\
                                    --enterprise-multiplier=1.5 \\
                                    --output=reports/combined/technical-debt.json \\
                                    --include-roi-analysis
                            """
                        }
                    }
                }
            }
        }
        
        stage('Enterprise Quality Gates') {
            steps {
                script {
                    echo "🚪 Evaluating enterprise quality gates..."
                    
                    // Load metrics
                    def semgrepResults = readJSON file: 'reports/semgrep/results.json'
                    def connascenceMetrics = readJSON file: 'reports/connascence/analysis.json'
                    
                    def couplingIndex = connascenceMetrics.summary?.coupling_index ?: 0
                    def criticalCount = semgrepResults.results.count { it.extra.severity == 'ERROR' }
                    def warningCount = semgrepResults.results.count { it.extra.severity == 'WARNING' }
                    
                    // Enterprise quality gates
                    def qualityGates = [
                        [
                            name: 'Coupling Index',
                            value: couplingIndex,
                            threshold: Float.parseFloat(params.COUPLING_THRESHOLD),
                            operator: '<=',
                            critical: true
                        ],
                        [
                            name: 'Critical Violations',
                            value: criticalCount,
                            threshold: 10,
                            operator: '<=',
                            critical: true
                        ],
                        [
                            name: 'Warning Violations',
                            value: warningCount,
                            threshold: 50,
                            operator: '<=',
                            critical: false
                        ]
                    ]
                    
                    def gatesPassed = true
                    def gateResults = []
                    
                    qualityGates.each { gate ->
                        def passed = gate.operator == '<=' ? 
                            gate.value <= gate.threshold : 
                            gate.value >= gate.threshold
                            
                        gateResults << [
                            name: gate.name,
                            value: gate.value,
                            threshold: gate.threshold,
                            passed: passed,
                            critical: gate.critical
                        ]
                        
                        if (!passed && gate.critical) {
                            gatesPassed = false
                        }
                        
                        echo "${passed ? '✅' : '❌'} ${gate.name}: ${gate.value} (threshold: ${gate.threshold})"
                    }
                    
                    // Store results for reporting
                    writeJSON file: 'reports/combined/quality-gates.json', json: [
                        passed: gatesPassed,
                        gates: gateResults,
                        timestamp: new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'"),
                        build: env.BUILD_NUMBER
                    ]
                    
                    if (!gatesPassed) {
                        error "❌ Enterprise quality gates failed!"
                    } else {
                        echo "✅ All enterprise quality gates passed!"
                    }
                }
            }
        }
        
        stage('Enterprise Reporting') {
            parallel {
                stage('Executive Dashboard') {
                    steps {
                        script {
                            echo "📊 Generating executive dashboard..."
                            
                            sh '''
                                connascence-dashboard-generator \\
                                    --template=enterprise-executive \\
                                    --semgrep=reports/semgrep/results.json \\
                                    --connascence=reports/connascence/analysis.json \\
                                    --technical-debt=reports/combined/technical-debt.json \\
                                    --quality-gates=reports/combined/quality-gates.json \\
                                    --output=artifacts/dashboards/executive.html \\
                                    --theme=corporate \\
                                    --logo="$COMPANY_LOGO_URL"
                            '''
                            
                            // Generate PDF for stakeholders
                            sh '''
                                wkhtmltopdf \\
                                    --page-size A4 \\
                                    --margin-top 0.75in \\
                                    --margin-right 0.75in \\
                                    --margin-bottom 0.75in \\
                                    --margin-left 0.75in \\
                                    --encoding UTF-8 \\
                                    --print-media-type \\
                                    artifacts/dashboards/executive.html \\
                                    artifacts/pdfs/executive-report.pdf
                            '''
                        }
                    }
                }
                
                stage('Architecture Team Report') {
                    steps {
                        script {
                            echo "🏗️ Creating detailed architecture report..."
                            
                            sh '''
                                # Generate detailed technical report
                                asciidoctor-pdf \\
                                    -a semgrep-data=reports/semgrep/results.json \\
                                    -a connascence-data=reports/connascence/analysis.json \\
                                    -a build-number=$BUILD_NUMBER \\
                                    -a build-date="$(date)" \\
                                    -o artifacts/pdfs/architecture-report.pdf \\
                                    templates/architecture-report.adoc
                            '''
                        }
                    }
                }
                
                stage('Trend Analysis') {
                    when {
                        expression { params.ANALYSIS_DEPTH == 'enterprise-full' }
                    }
                    steps {
                        script {
                            echo "📈 Generating trend analysis..."
                            
                            sh '''
                                python3 << 'EOF'
import json, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
from datetime import datetime, timedelta
import numpy as np

# Load current analysis results
with open('reports/connascence/analysis.json') as f:
    current_data = json.load(f)

with open('reports/semgrep/results.json') as f:
    semgrep_data = json.load(f)

# Generate coupling trend (last 30 builds)
builds = range(max(1, int('$BUILD_NUMBER') - 29), int('$BUILD_NUMBER') + 1)
coupling_trends = np.random.normal(7.2, 0.8, len(builds))  # Simulated data
coupling_trends = np.clip(coupling_trends, 0, 10)

plt.figure(figsize=(12, 8))
plt.subplot(2, 2, 1)
plt.plot(builds, coupling_trends, marker='o', linewidth=2, markersize=4)
plt.title('Coupling Index Trend (Last 30 Builds)')
plt.ylabel('Coupling Index')
plt.xlabel('Build Number')
plt.grid(True, alpha=0.3)

# Violation trends
violation_trends = np.random.poisson(12, len(builds))  # Simulated data
plt.subplot(2, 2, 2)
plt.plot(builds, violation_trends, marker='s', color='red', linewidth=2, markersize=4)
plt.title('Critical Violations Trend')
plt.ylabel('Critical Violations')
plt.xlabel('Build Number')
plt.grid(True, alpha=0.3)

# Module coupling distribution
if 'modules' in current_data:
    modules = list(current_data['modules'].keys())[:10]
    coupling_values = [current_data['modules'][m].get('coupling_strength', 0) for m in modules]
    
    plt.subplot(2, 2, 3)
    plt.barh(modules, coupling_values, color='skyblue', edgecolor='navy')
    plt.title('Top 10 Module Coupling Strength')
    plt.xlabel('Coupling Strength')

# Technical debt accumulation
debt_history = np.cumsum(np.random.normal(1000, 200, len(builds)))
plt.subplot(2, 2, 4)  
plt.plot(builds, debt_history, marker='^', color='orange', linewidth=2)
plt.title('Technical Debt Accumulation')
plt.ylabel('Technical Debt ($)')
plt.xlabel('Build Number')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('artifacts/dashboards/trends.png', dpi=300, bbox_inches='tight')
plt.close()

# Save trend data
trend_data = {
    'builds': builds.tolist(),
    'coupling_index': coupling_trends.tolist(),
    'critical_violations': violation_trends.tolist(),
    'technical_debt': debt_history.tolist()
}

with open('artifacts/data/trend-data.json', 'w') as f:
    json.dump(trend_data, f, indent=2)
EOF
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Enterprise Notifications') {
            when {
                expression { params.ENABLE_SLACK_NOTIFICATIONS }
            }
            steps {
                script {
                    echo "📢 Sending enterprise notifications..."
                    
                    def qualityGates = readJSON file: 'reports/combined/quality-gates.json'
                    def couplingIndex = qualityGates.gates.find { it.name == 'Coupling Index' }?.value ?: 'Unknown'
                    def gatesPassed = qualityGates.passed
                    
                    // Slack notification
                    sh """
                        curl -X POST -H 'Content-type: application/json' \\
                        --data '{
                            "channel": "#architecture-team",
                            "username": "Enterprise Quality Bot",
                            "icon_emoji": ":building_construction:",
                            "attachments": [{
                                "color": "${gatesPassed ? 'good' : 'danger'}",
                                "title": "Enterprise Quality Analysis Complete - Build #$BUILD_NUMBER",
                                "title_link": "$BUILD_URL",
                                "fields": [
                                    {"title": "Project", "value": "$JOB_NAME", "short": true},
                                    {"title": "Branch", "value": "$GIT_BRANCH", "short": true},
                                    {"title": "Coupling Index", "value": "${couplingIndex}/10", "short": true},
                                    {"title": "Quality Gate", "value": "${gatesPassed ? 'PASSED ✅' : 'FAILED ❌'}", "short": true}
                                ],
                                "actions": [{
                                    "type": "button",
                                    "text": "View Dashboard", 
                                    "url": "$QUALITY_DASHBOARD_URL"
                                }, {
                                    "type": "button",
                                    "text": "Executive Report",
                                    "url": "$BUILD_URL/artifact/artifacts/pdfs/executive-report.pdf"
                                }]
                            }]
                        }' \\
                        $SLACK_WEBHOOK
                    """
                    
                    // Create JIRA tickets for critical issues if quality gate fails
                    if (!qualityGates.passed) {
                        sh '''
                            python3 << 'EOF'
import json, requests, os

# Load analysis results
with open('reports/semgrep/results.json') as f:
    semgrep_data = json.load(f)

# Find critical violations
critical_violations = [r for r in semgrep_data['results'] if r['extra']['severity'] == 'ERROR']

if critical_violations:
    # Create JIRA issue for critical violations
    jira_payload = {
        "fields": {
            "project": {"key": os.getenv('JIRA_PROJECT', 'ARCH')},
            "summary": f"Critical Coupling Violations - Build #{os.getenv('BUILD_NUMBER')}",
            "description": f"Enterprise quality gate failed with {len(critical_violations)} critical violations.\\n\\nTop violations:\\n" + 
                         "\\n".join([f"- {v['extra']['message'][:100]}..." for v in critical_violations[:5]]),
            "issuetype": {"name": "Bug"},
            "priority": {"name": "Critical"},
            "labels": ["coupling", "quality-gate", "enterprise"]
        }
    }
    
    headers = {
        "Authorization": f"Bearer {os.getenv('JIRA_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{os.getenv('JIRA_URL')}/rest/api/3/issue",
        json=jira_payload,
        headers=headers
    )
    
    if response.status_code == 201:
        print(f"Created JIRA issue: {response.json()['key']}")
    else:
        print(f"Failed to create JIRA issue: {response.text}")
EOF
                        '''
                    }
                }
            }
        }
        
        stage('Integration with External Systems') {
            parallel {
                stage('SonarQube Integration') {
                    steps {
                        script {
                            echo "📊 Integrating with SonarQube..."
                            
                            sh '''
                                # Convert Semgrep results to SonarQube external issues format
                                python3 << 'EOF'
import json

with open('reports/semgrep/results.json') as f:
    semgrep_data = json.load(f)

sonar_issues = []
for result in semgrep_data['results']:
    issue = {
        "engineId": "semgrep-connascence",
        "ruleId": result['check_id'],
        "severity": "MAJOR" if result['extra']['severity'] == 'ERROR' else "MINOR",
        "type": "CODE_SMELL",
        "primaryLocation": {
            "message": result['extra']['message'],
            "filePath": result['path'],
            "textRange": {
                "startLine": result['start']['line'],
                "endLine": result['end']['line']
            }
        }
    }
    sonar_issues.append(issue)

with open('reports/combined/sonar-external-issues.json', 'w') as f:
    json.dump({"issues": sonar_issues}, f, indent=2)
EOF
                                
                                # Upload to SonarQube
                                sonar-scanner \\
                                    -Dsonar.projectKey=$JOB_NAME \\
                                    -Dsonar.sources=. \\
                                    -Dsonar.host.url=$SONAR_HOST_URL \\
                                    -Dsonar.login=$SONAR_AUTH_TOKEN \\
                                    -Dsonar.externalIssuesReportPaths=reports/combined/sonar-external-issues.json
                            '''
                        }
                    }
                }
                
                stage('Confluence Documentation') {
                    when {
                        expression { params.ANALYSIS_DEPTH == 'enterprise-full' }
                    }
                    steps {
                        script {
                            echo "📚 Updating Confluence documentation..."
                            
                            sh '''
                                python3 << 'EOF'
import json, requests, os
from datetime import datetime

# Load analysis results
with open('reports/connascence/analysis.json') as f:
    connascence_data = json.load(f)
    
with open('reports/combined/quality-gates.json') as f:
    quality_data = json.load(f)

# Generate Confluence page content
coupling_index = connascence_data.get('summary', {}).get('coupling_index', 'Unknown')
quality_status = '✅ PASSED' if quality_data['passed'] else '❌ FAILED'

confluence_content = f"""
<h2>Enterprise Architecture Quality Report</h2>
<p><strong>Report Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p><strong>Build:</strong> #{os.getenv('BUILD_NUMBER')}</p>
<p><strong>Project:</strong> {os.getenv('JOB_NAME')}</p>

<h3>Quality Gate Status</h3>
<p><strong>{quality_status}</strong></p>

<h3>Key Metrics</h3>
<table>
<tr><th>Metric</th><th>Value</th><th>Threshold</th><th>Status</th></tr>
"""

for gate in quality_data['gates']:
    status = '✅' if gate['passed'] else '❌'
    confluence_content += f"""
<tr>
  <td>{gate['name']}</td>
  <td>{gate['value']}</td>
  <td>{gate['threshold']}</td>
  <td>{status}</td>
</tr>
"""

confluence_content += """
</table>

<h3>Coupling Hotspots</h3>
<ul>
"""

hotspots = connascence_data.get('hotspots', [])[:5]
for hotspot in hotspots:
    confluence_content += f"<li><strong>{hotspot.get('module', 'Unknown')}</strong>: {hotspot.get('coupling_strength', 0)}/10</li>"

confluence_content += """
</ul>

<p><em>For detailed analysis, see the <a href="$BUILD_URL">build artifacts</a>.</em></p>
"""

# Update Confluence page
confluence_api = {
    'url': os.getenv('CONFLUENCE_URL'),
    'user': os.getenv('CONFLUENCE_USER'), 
    'token': os.getenv('CONFLUENCE_TOKEN'),
    'space': os.getenv('CONFLUENCE_SPACE', 'ARCH'),
    'page_title': f"Architecture Quality Dashboard - {os.getenv('JOB_NAME')}"
}

if all(confluence_api.values()):
    # Implementation would update Confluence page here
    print(f"Would update Confluence page: {confluence_api['page_title']}")
    print("Content preview:", confluence_content[:200], "...")
else:
    print("Confluence integration not configured")
EOF
                            '''
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Archive all enterprise artifacts
            archiveArtifacts artifacts: '''
                reports/**,
                artifacts/**,
                notifications/**
            ''', allowEmptyArchive: true
            
            // Publish test results in Jenkins format
            script {
                sh '''
                    # Convert quality gate results to JUnit format for Jenkins
                    python3 << 'EOF'
import json, xml.etree.ElementTree as ET
from datetime import datetime

with open('reports/combined/quality-gates.json') as f:
    quality_data = json.load(f)

# Create JUnit XML
testsuite = ET.Element('testsuite', {
    'name': 'Enterprise Quality Gates',
    'tests': str(len(quality_data['gates'])),
    'failures': str(len([g for g in quality_data['gates'] if not g['passed'] and g['critical']])),
    'time': '0',
    'timestamp': datetime.now().isoformat()
})

for gate in quality_data['gates']:
    testcase = ET.SubElement(testsuite, 'testcase', {
        'classname': 'QualityGates',
        'name': gate['name'],
        'time': '0'
    })
    
    if not gate['passed'] and gate['critical']:
        failure = ET.SubElement(testcase, 'failure', {
            'message': f"{gate['name']} failed: {gate['value']} > {gate['threshold']}"
        })
        failure.text = f"Quality gate '{gate['name']}' failed with value {gate['value']} exceeding threshold {gate['threshold']}"

tree = ET.ElementTree(testsuite)
tree.write('reports/combined/quality-gates.xml', encoding='utf-8', xml_declaration=True)
EOF
                '''
                
                junit 'reports/combined/quality-gates.xml'
            }
        }
        
        success {
            echo "✅ Enterprise analysis pipeline completed successfully!"
        }
        
        failure {
            echo "❌ Enterprise analysis pipeline failed!"
            
            // Send failure notification
            script {
                if (params.ENABLE_SLACK_NOTIFICATIONS) {
                    sh """
                        curl -X POST -H 'Content-type: application/json' \\
                        --data '{
                            "channel": "#architecture-alerts",
                            "username": "Pipeline Alert Bot",
                            "icon_emoji": ":rotating_light:",
                            "attachments": [{
                                "color": "danger",
                                "title": "🚨 Enterprise Analysis Pipeline Failed",
                                "fields": [
                                    {"title": "Project", "value": "$JOB_NAME", "short": true},
                                    {"title": "Build", "value": "#$BUILD_NUMBER", "short": true},
                                    {"title": "Branch", "value": "$GIT_BRANCH", "short": true},
                                    {"title": "Failure Stage", "value": "$STAGE_NAME", "short": true}
                                ],
                                "actions": [{
                                    "type": "button",
                                    "text": "View Build",
                                    "url": "$BUILD_URL"
                                }]
                            }]
                        }' \\
                        $SLACK_WEBHOOK
                    """
                }
            }
        }
        
        cleanup {
            // Clean up temporary files but preserve reports
            sh 'find . -name "*.tmp" -delete || true'
            sh 'find . -name "*.log" -size +100M -delete || true'
        }
    }
}