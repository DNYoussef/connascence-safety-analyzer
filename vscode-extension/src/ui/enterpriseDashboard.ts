/**
 * Enterprise Connascence Dashboard with Budget, Policy, and Trend Analysis
 */
export function generateEnterpriseDashboardHTML(summary: any, charts: any, enterpriseData?: any): string {
    const budgetData = enterpriseData?.budget || {};
    const baselineData = enterpriseData?.baseline || {};
    const driftData = enterpriseData?.drift || {};
    const waiverData = enterpriseData?.waivers || {};

    return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Connascence Enterprise Dashboard</title>
    <style>
        :root {
            --primary-color: var(--vscode-charts-blue);
            --success-color: var(--vscode-charts-green);
            --warning-color: var(--vscode-charts-orange);
            --error-color: var(--vscode-charts-red);
            --background-color: var(--vscode-editor-background);
            --border-color: var(--vscode-panel-border);
        }

        body { 
            font-family: var(--vscode-font-family); 
            color: var(--vscode-foreground); 
            background: var(--background-color);
            margin: 0; 
            padding: 0;
        }

        .dashboard-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .dashboard-header {
            background: var(--vscode-titleBar-activeBackground);
            padding: 15px 20px;
            border-bottom: 1px solid var(--border-color);
        }

        .dashboard-title {
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }

        .dashboard-subtitle {
            font-size: 14px;
            opacity: 0.8;
            margin: 5px 0 0 0;
        }

        .tab-container {
            display: flex;
            background: var(--vscode-tab-inactiveBackground);
            border-bottom: 1px solid var(--border-color);
        }

        .tab {
            padding: 12px 20px;
            cursor: pointer;
            border-right: 1px solid var(--border-color);
            background: var(--vscode-tab-inactiveBackground);
            color: var(--vscode-tab-inactiveForeground);
            transition: all 0.2s;
        }

        .tab:hover {
            background: var(--vscode-tab-hoverBackground);
        }

        .tab.active {
            background: var(--vscode-tab-activeBackground);
            color: var(--vscode-tab-activeForeground);
            border-bottom: 2px solid var(--primary-color);
        }

        .tab-content {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }

        .tab-pane {
            display: none;
        }

        .tab-pane.active {
            display: block;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .metric-card {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
        }

        .metric-title {
            font-size: 14px;
            font-weight: bold;
            color: var(--vscode-descriptionForeground);
            margin-bottom: 10px;
        }

        .metric-value {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .metric-subtitle {
            font-size: 12px;
            opacity: 0.7;
        }

        .budget-exceeded { color: var(--error-color); }
        .budget-warning { color: var(--warning-color); }
        .budget-ok { color: var(--success-color); }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--vscode-progressBar-background);
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }

        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
            border-radius: 4px;
        }

        .section {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .section-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }

        .status-success { background: var(--success-color); color: white; }
        .status-warning { background: var(--warning-color); color: white; }
        .status-error { background: var(--error-color); color: white; }

        .action-button {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            margin: 4px 8px 4px 0;
        }

        .action-button:hover {
            background: var(--vscode-button-hoverBackground);
        }

        .violation-list {
            max-height: 300px;
            overflow-y: auto;
        }

        .violation-item {
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: between;
            align-items: center;
        }

        .violation-item:last-child {
            border-bottom: none;
        }

        .violation-severity {
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            margin-right: 8px;
        }

        .severity-critical { background: var(--error-color); color: white; }
        .severity-major { background: var(--warning-color); color: white; }
        .severity-minor { background: var(--vscode-charts-blue); color: white; }
        .severity-info { background: var(--vscode-descriptionForeground); color: white; }

        .trend-chart {
            height: 200px;
            background: var(--vscode-input-background);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--vscode-descriptionForeground);
        }

        .ai-chat {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            background: var(--vscode-input-background);
        }

        .chat-messages {
            height: 300px;
            overflow-y: auto;
            margin-bottom: 10px;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
        }

        .message {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 6px;
        }

        .user-message {
            background: var(--primary-color);
            color: white;
            text-align: right;
        }

        .ai-message {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--border-color);
        }

        .chat-input-container {
            display: flex;
            gap: 8px;
        }

        .chat-input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
        }

        .chat-send {
            padding: 8px 16px;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }

        .icon {
            width: 16px;
            height: 16px;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="dashboard-header">
            <h1 class="dashboard-title">🔗 Connascence Enterprise Dashboard</h1>
            <p class="dashboard-subtitle">Real-time code quality monitoring with enterprise policy enforcement</p>
        </div>

        <div class="tab-container">
            <div class="tab active" data-tab="overview">📊 Overview</div>
            <div class="tab" data-tab="budget">💰 Budget</div>
            <div class="tab" data-tab="policy">🛡️ Policy</div>
            <div class="tab" data-tab="trends">📈 Trends</div>
            <div class="tab" data-tab="violations">⚠️ Violations</div>
            <div class="tab" data-tab="ai">🤖 AI Assistant</div>
        </div>

        <div class="tab-content">
            <!-- Overview Tab -->
            <div class="tab-pane active" id="overview">
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-title">Total Violations</div>
                        <div class="metric-value ${(summary.totalViolations || 0) > 0 ? 'budget-warning' : 'budget-ok'}">
                            ${summary.totalViolations || 0}
                        </div>
                        <div class="metric-subtitle">Across ${summary.totalFiles || 0} files</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-title">Critical Issues</div>
                        <div class="metric-value ${(summary.severityBreakdown?.critical || 0) > 0 ? 'budget-exceeded' : 'budget-ok'}">
                            ${summary.severityBreakdown?.critical || 0}
                        </div>
                        <div class="metric-subtitle">Immediate attention required</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-title">Quality Score</div>
                        <div class="metric-value ${(summary.averageScore || 100) < 80 ? 'budget-warning' : 'budget-ok'}">
                            ${Math.round(summary.averageScore || 100)}%
                        </div>
                        <div class="metric-subtitle">Overall code quality</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-title">Budget Status</div>
                        <div class="metric-value ${budgetData.exceeded ? 'budget-exceeded' : 'budget-ok'}">
                            ${budgetData.exceeded ? 'EXCEEDED' : 'OK'}
                        </div>
                        <div class="metric-subtitle">Budget compliance</div>
                    </div>
                </div>

                <div class="section">
                    <h3 class="section-title">
                        <span class="icon">📈</span>
                        Quick Actions
                    </h3>
                    <button class="action-button" onclick="createSnapshot()">📸 Create Snapshot</button>
                    <button class="action-button" onclick="checkBudget()">💰 Check Budget</button>
                    <button class="action-button" onclick="analyzeWorkspace()">🔍 Analyze Workspace</button>
                    <button class="action-button" onclick="showTrends()">📊 View Trends</button>
                </div>
            </div>

            <!-- Budget Tab -->
            <div class="tab-pane" id="budget">
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-title">Total Budget</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${Math.min((summary.totalViolations || 0) / 50 * 100, 100)}%; background: ${(summary.totalViolations || 0) > 50 ? 'var(--error-color)' : 'var(--success-color)'}"></div>
                        </div>
                        <div class="metric-value">${summary.totalViolations || 0}/50</div>
                        <div class="metric-subtitle">Total violations allowed</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-title">Critical Budget</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${(summary.severityBreakdown?.critical || 0) > 0 ? '100%' : '0%'}; background: var(--error-color)"></div>
                        </div>
                        <div class="metric-value">${summary.severityBreakdown?.critical || 0}/0</div>
                        <div class="metric-subtitle">Zero tolerance policy</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-title">High Severity Budget</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${Math.min((summary.severityBreakdown?.major || 0) / 5 * 100, 100)}%; background: ${(summary.severityBreakdown?.major || 0) > 5 ? 'var(--error-color)' : 'var(--warning-color)'}"></div>
                        </div>
                        <div class="metric-value">${summary.severityBreakdown?.major || 0}/5</div>
                        <div class="metric-subtitle">High severity limit</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-title">New Violations</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${Math.min((baselineData.newViolations || 0) / 3 * 100, 100)}%; background: ${(baselineData.newViolations || 0) > 3 ? 'var(--error-color)' : 'var(--success-color)'}"></div>
                        </div>
                        <div class="metric-value">${baselineData.newViolations || 0}/3</div>
                        <div class="metric-subtitle">Per PR limit</div>
                    </div>
                </div>

                <div class="section">
                    <h3 class="section-title">Budget Configuration</h3>
                    <button class="action-button" onclick="configureBudgets()">⚙️ Configure Limits</button>
                    <button class="action-button" onclick="generateBudgetReport()">📄 Generate Report</button>
                    <button class="action-button" onclick="validateForCI()">✅ Validate for CI</button>
                </div>
            </div>

            <!-- Policy Tab -->
            <div class="tab-pane" id="policy">
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-title">Active Waivers</div>
                        <div class="metric-value">${waiverData.activeCount || 0}</div>
                        <div class="metric-subtitle">Approved exceptions</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-title">Baseline Status</div>
                        <div class="metric-value">${baselineData.exists ? 'ACTIVE' : 'NONE'}</div>
                        <div class="metric-subtitle">Reference snapshot</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-title">Policy Mode</div>
                        <div class="metric-value">${budgetData.mode || 'BASELINE'}</div>
                        <div class="metric-subtitle">Enforcement strategy</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-title">Compliance</div>
                        <div class="metric-value ${budgetData.compliant ? 'budget-ok' : 'budget-exceeded'}">
                            ${budgetData.compliant ? 'PASS' : 'FAIL'}
                        </div>
                        <div class="metric-subtitle">Overall status</div>
                    </div>
                </div>

                <div class="section">
                    <h3 class="section-title">Policy Management</h3>
                    <button class="action-button" onclick="createBaseline()">📸 Create Baseline</button>
                    <button class="action-button" onclick="manageWaivers()">📝 Manage Waivers</button>
                    <button class="action-button" onclick="configurePolicies()">⚙️ Configure Policies</button>
                    <button class="action-button" onclick="auditCompliance()">🔍 Audit Compliance</button>
                </div>
            </div>

            <!-- Trends Tab -->
            <div class="tab-pane" id="trends">
                <div class="section">
                    <h3 class="section-title">
                        <span class="icon">📈</span>
                        Quality Trends
                    </h3>
                    <div class="trend-chart">
                        📊 Trend visualization would appear here
                        <br><small>(Integration with drift tracking system)</small>
                    </div>
                </div>

                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-title">Trend Direction</div>
                        <div class="metric-value">${driftData.direction || 'STABLE'}</div>
                        <div class="metric-subtitle">30-day analysis</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-title">Change Rate</div>
                        <div class="metric-value">${driftData.changeRate || '0.0'}/day</div>
                        <div class="metric-subtitle">Violations per day</div>
                    </div>
                </div>

                <div class="section">
                    <h3 class="section-title">Trend Actions</h3>
                    <button class="action-button" onclick="analyzeDrift()">📊 Analyze Drift</button>
                    <button class="action-button" onclick="recordMeasurement()">📝 Record Measurement</button>
                    <button class="action-button" onclick="exportHistory()">💾 Export History</button>
                </div>
            </div>

            <!-- Violations Tab -->
            <div class="tab-pane" id="violations">
                <div class="section">
                    <h3 class="section-title">
                        <span class="icon">⚠️</span>
                        Current Violations
                    </h3>
                    <div class="violation-list" id="violationsList">
                        <!-- Violations will be populated by JavaScript -->
                    </div>
                </div>
            </div>

            <!-- AI Assistant Tab -->
            <div class="tab-pane" id="ai">
                <div class="ai-chat">
                    <h3 class="section-title">
                        <span class="icon">🤖</span>
                        AI Assistant
                    </h3>
                    <div class="chat-messages" id="chatMessages">
                        <div class="message ai-message">
                            Hello! I'm your Connascence AI assistant. I can help you understand your code quality, suggest improvements, and guide you through enterprise policy management. Try asking:
                            <br><br>
                            • "What are my critical violations?"<br>
                            • "How can I improve my budget compliance?"<br>
                            • "Explain the baseline comparison"<br>
                            • "What's my drift analysis showing?"
                        </div>
                    </div>
                    <div class="chat-input-container">
                        <input type="text" id="chatInput" class="chat-input" placeholder="Ask about your code quality...">
                        <button id="sendButton" class="chat-send">Send</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and panes
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding pane
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab).classList.add('active');
            });
        });

        // Chat functionality
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        
        function addMessage(message, isUser) {
            const div = document.createElement('div');
            div.className = isUser ? 'message user-message' : 'message ai-message';
            div.innerHTML = (isUser ? 'You: ' : 'AI: ') + message;
            chatMessages.appendChild(div);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        sendButton.addEventListener('click', () => {
            const message = chatInput.value.trim();
            if (message) {
                addMessage(message, true);
                vscode.postMessage({
                    type: 'aiChat',
                    message: message,
                    context: {
                        violations: ${summary.totalViolations || 0},
                        criticalCount: ${summary.severityBreakdown?.critical || 0},
                        files: ${summary.totalFiles || 0},
                        budgetExceeded: ${budgetData.exceeded || false},
                        hasBaseline: ${baselineData.exists || false}
                    }
                });
                chatInput.value = '';
            }
        });
        
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendButton.click();
            }
        });

        // Action button handlers
        function createSnapshot() {
            vscode.postMessage({ type: 'createSnapshot' });
        }

        function checkBudget() {
            vscode.postMessage({ type: 'checkBudget' });
        }

        function analyzeWorkspace() {
            vscode.postMessage({ type: 'analyzeWorkspace' });
        }

        function showTrends() {
            document.querySelector('[data-tab="trends"]').click();
        }

        function configureBudgets() {
            vscode.postMessage({ type: 'configureBudgets' });
        }

        function generateBudgetReport() {
            vscode.postMessage({ type: 'generateBudgetReport' });
        }

        function validateForCI() {
            vscode.postMessage({ type: 'validateForCI' });
        }

        function createBaseline() {
            vscode.postMessage({ type: 'createBaseline' });
        }

        function manageWaivers() {
            vscode.postMessage({ type: 'manageWaivers' });
        }

        function configurePolicies() {
            vscode.postMessage({ type: 'configurePolicies' });
        }

        function auditCompliance() {
            vscode.postMessage({ type: 'auditCompliance' });
        }

        function analyzeDrift() {
            vscode.postMessage({ type: 'analyzeDrift' });
        }

        function recordMeasurement() {
            vscode.postMessage({ type: 'recordMeasurement' });
        }

        function exportHistory() {
            vscode.postMessage({ type: 'exportHistory' });
        }

        // Handle messages from VS Code
        window.addEventListener('message', event => {
            const message = event.data;
            if (message.type === 'aiResponse') {
                addMessage(message.response, false);
            }
        });

        // Initialize violations list (simplified)
        const violationsList = document.getElementById('violationsList');
        if (violationsList) {
            const severityBreakdown = ${JSON.stringify(summary.severityBreakdown || {})};
            let violationsHTML = '';
            
            Object.entries(severityBreakdown).forEach(([severity, count]) => {
                if (count > 0) {
                    violationsHTML += \`
                        <div class="violation-item">
                            <span class="violation-severity severity-\${severity}">\${severity.toUpperCase()}</span>
                            <span>\${count} violations</span>
                        </div>
                    \`;
                }
            });
            
            if (violationsHTML === '') {
                violationsHTML = '<div class="violation-item">No violations detected ✅</div>';
            }
            
            violationsList.innerHTML = violationsHTML;
        }
    </script>
</body>
</html>`;
}