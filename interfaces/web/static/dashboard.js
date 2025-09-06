// Connascence Dashboard JavaScript
class ConnascenceDashboard {
    constructor() {
        this.socket = io();
        this.scanResults = null;
        this.charts = {};
        
        this.initializeEventHandlers();
        this.initializeWebSocket();
        this.initializeCharts();
    }
    
    initializeEventHandlers() {
        // Tab navigation
        document.querySelectorAll('[data-tab]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Scan button
        document.getElementById('scanButton').addEventListener('click', () => {
            this.startScan();
        });
        
        // Refresh button
        document.getElementById('refreshButton').addEventListener('click', () => {
            this.refreshData();
        });
        
        // Export button
        document.getElementById('exportButton').addEventListener('click', () => {
            this.showExportMenu();
        });
        
        // Violation filters
        document.getElementById('severityFilter').addEventListener('change', () => {
            this.filterViolations();
        });
        
        document.getElementById('typeFilter').addEventListener('change', () => {
            this.filterViolations();
        });
        
        // Autofix buttons
        document.getElementById('previewAllFixes').addEventListener('click', () => {
            this.previewAllFixes();
        });
        
        // Settings
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });
    }
    
    initializeWebSocket() {
        this.socket.on('connect', () => {
            this.updateConnectionStatus('connected');
        });
        
        this.socket.on('disconnect', () => {
            this.updateConnectionStatus('disconnected');
        });
        
        this.socket.on('scan_started', (data) => {
            this.handleScanStarted(data);
        });
        
        this.socket.on('scan_complete', (data) => {
            this.handleScanComplete(data);
        });
        
        this.socket.on('scan_error', (data) => {
            this.handleScanError(data);
        });
        
        this.socket.on('file_scan_complete', (data) => {
            this.handleFileScanComplete(data);
        });
    }
    
    initializeCharts() {
        // Severity distribution chart
        const severityCtx = document.getElementById('severityChart').getContext('2d');
        this.charts.severity = new Chart(severityCtx, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#ef4444', // Critical - red
                        '#f59e0b', // High - orange
                        '#3b82f6', // Medium - blue
                        '#10b981'  // Low - green
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        // Types chart
        const typesCtx = document.getElementById('typesChart').getContext('2d');
        this.charts.types = new Chart(typesCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Violations',
                    data: [],
                    backgroundColor: '#3b82f6',
                    borderColor: '#1d4ed8',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Trends chart
        const trendsCtx = document.getElementById('trendsChart').getContext('2d');
        this.charts.trends = new Chart(trendsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Connascence Index',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    switchTab(tabName) {
        // Update nav links
        document.querySelectorAll('[data-tab]').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('d-none');
        });
        document.getElementById(`${tabName}-tab`).classList.remove('d-none');
        
        // Load tab-specific data
        this.loadTabData(tabName);
    }
    
    loadTabData(tabName) {
        switch (tabName) {
            case 'trends':
                this.loadTrendsData();
                break;
            case 'autofix':
                this.loadAutofixSuggestions();
                break;
        }
    }
    
    startScan() {
        const projectPath = document.getElementById('projectPathInput').value || '.';
        const policyPreset = document.getElementById('policySelect').value;
        
        // Disable scan button
        const scanButton = document.getElementById('scanButton');
        scanButton.disabled = true;
        scanButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Scanning...';
        
        // Send scan request
        fetch('/api/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: projectPath,
                policy_preset: policyPreset
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'started') {
                this.handleScanError({error: data.message});
            }
        })
        .catch(error => {
            this.handleScanError({error: error.message});
        });
    }
    
    handleScanStarted(data) {
        document.getElementById('scanStatus').textContent = `Scanning ${data.project_path}...`;
        document.getElementById('scanProgress').style.width = '20%';
        
        // Update project path display
        document.getElementById('projectPath').textContent = data.project_path;
    }
    
    handleScanComplete(data) {
        this.scanResults = data;
        
        // Reset scan button
        const scanButton = document.getElementById('scanButton');
        scanButton.disabled = false;
        scanButton.innerHTML = '<i class="fas fa-search me-2"></i>Scan';
        
        // Update progress
        document.getElementById('scanProgress').style.width = '100%';
        document.getElementById('scanStatus').textContent = 'Scan complete';
        
        // Update last scan time
        const timestamp = new Date(data.timestamp).toLocaleString();
        document.getElementById('lastScanTime').textContent = `Last scan: ${timestamp}`;
        
        // Update metrics
        this.updateMetrics(data.summary);
        
        // Update charts
        this.updateCharts(data);
        
        // Update violations list
        this.updateViolationsList(data.violations);
        
        // Reset progress after delay
        setTimeout(() => {
            document.getElementById('scanProgress').style.width = '0%';
            document.getElementById('scanStatus').textContent = 'Ready to scan';
        }, 2000);
    }
    
    handleScanError(data) {
        // Reset scan button
        const scanButton = document.getElementById('scanButton');
        scanButton.disabled = false;
        scanButton.innerHTML = '<i class="fas fa-search me-2"></i>Scan';
        
        // Show error
        document.getElementById('scanStatus').textContent = `Error: ${data.error}`;
        document.getElementById('scanProgress').style.width = '0%';
        
        // Show toast notification
        this.showNotification('Scan failed: ' + data.error, 'error');
    }
    
    handleFileScanComplete(data) {
        // Update progress incrementally
        const currentWidth = parseFloat(document.getElementById('scanProgress').style.width) || 0;
        document.getElementById('scanProgress').style.width = Math.min(currentWidth + 5, 95) + '%';
    }
    
    updateMetrics(summary) {
        document.getElementById('totalViolations').textContent = summary.total_violations || 0;
        document.getElementById('criticalCount').textContent = summary.critical_count || 0;
        document.getElementById('highCount').textContent = summary.high_count || 0;
        document.getElementById('mediumCount').textContent = summary.medium_count || 0;
        document.getElementById('lowCount').textContent = summary.low_count || 0;
        document.getElementById('connascenceIndex').textContent = (summary.connascence_index || 0).toFixed(1);
    }
    
    updateCharts(data) {
        const summary = data.summary;
        
        // Update severity chart
        this.charts.severity.data.datasets[0].data = [
            summary.critical_count || 0,
            summary.high_count || 0,
            summary.medium_count || 0,
            summary.low_count || 0
        ];
        this.charts.severity.update();
        
        // Update types chart
        const violationsByType = summary.violations_by_type || {};
        this.charts.types.data.labels = Object.keys(violationsByType);
        this.charts.types.data.datasets[0].data = Object.values(violationsByType);
        this.charts.types.update();
    }
    
    updateViolationsList(violations) {
        const container = document.getElementById('violationsList');
        
        if (!violations || violations.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center text-muted py-4">
                    <i class="fas fa-check-circle fa-2x mb-2 text-success"></i>
                    <p>No violations found</p>
                </div>
            `;
            return;
        }
        
        // Show top 10 violations
        const topViolations = violations.slice(0, 10);
        
        container.innerHTML = topViolations.map(violation => `
            <div class="col-12">
                <div class="violation-card ${violation.severity} p-3 mb-2">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-1">
                                <span class="badge bg-${this.getSeverityColor(violation.severity)} me-2">
                                    ${violation.severity.toUpperCase()}
                                </span>
                                <strong>${violation.connascence_type}</strong>
                            </div>
                            <p class="mb-1">${violation.description}</p>
                            <small class="text-muted">
                                <i class="fas fa-file me-1"></i>
                                ${this.getFileName(violation.file_path)}:${violation.line_number}
                            </small>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-primary btn-sm" 
                                    onclick="dashboard.previewAutofix('${violation.id}')">
                                <i class="fas fa-magic me-1"></i>
                                Fix
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Update violations table
        this.updateViolationsTable(violations);
    }
    
    updateViolationsTable(violations) {
        const tbody = document.getElementById('violationsTableBody');
        
        if (!violations || violations.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">
                        No violations to display
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = violations.map(violation => `
            <tr>
                <td>
                    <span class="badge bg-${this.getSeverityColor(violation.severity)}">
                        ${violation.severity}
                    </span>
                </td>
                <td><code>${violation.connascence_type}</code></td>
                <td>
                    <span class="text-truncate d-inline-block" style="max-width: 200px;" 
                          title="${violation.file_path}">
                        ${this.getFileName(violation.file_path)}
                    </span>
                </td>
                <td>${violation.line_number}</td>
                <td class="text-truncate" style="max-width: 300px;" title="${violation.description}">
                    ${violation.description}
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-outline-primary" 
                            onclick="dashboard.previewAutofix('${violation.id}')">
                        <i class="fas fa-magic"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    filterViolations() {
        const severityFilter = document.getElementById('severityFilter').value;
        const typeFilter = document.getElementById('typeFilter').value;
        
        if (!this.scanResults || !this.scanResults.violations) return;
        
        let filteredViolations = this.scanResults.violations;
        
        if (severityFilter) {
            filteredViolations = filteredViolations.filter(v => v.severity === severityFilter);
        }
        
        if (typeFilter) {
            filteredViolations = filteredViolations.filter(v => v.connascence_type === typeFilter);
        }
        
        this.updateViolationsTable(filteredViolations);
    }
    
    previewAutofix(violationId) {
        if (!this.scanResults) return;
        
        const violation = this.scanResults.violations.find(v => v.id === violationId);
        if (!violation) return;
        
        // Show loading state
        this.showNotification('Generating autofix preview...', 'info');
        
        fetch('/api/autofix/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: violation.file_path,
                violations: [violation]
            })
        })
        .then(response => response.json())
        .then(data => {
            this.showAutofixPreview(data);
        })
        .catch(error => {
            this.showNotification('Failed to generate autofix: ' + error.message, 'error');
        });
    }
    
    previewAllFixes() {
        if (!this.scanResults || !this.scanResults.violations.length) return;
        
        this.showNotification('Generating autofix previews...', 'info');
        
        // Group violations by file
        const violationsByFile = {};
        this.scanResults.violations.forEach(violation => {
            if (!violationsByFile[violation.file_path]) {
                violationsByFile[violation.file_path] = [];
            }
            violationsByFile[violation.file_path].push(violation);
        });
        
        // Preview fixes for each file
        Object.entries(violationsByFile).forEach(([filePath, violations]) => {
            fetch('/api/autofix/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    file_path: filePath,
                    violations: violations
                })
            })
            .then(response => response.json())
            .then(data => {
                this.addAutofixSuggestion(filePath, data);
            })
            .catch(error => {
                console.error('Autofix preview failed for', filePath, error);
            });
        });
    }
    
    showAutofixPreview(data) {
        // Create modal or expand section to show preview
        const modalHtml = `
            <div class="modal fade" id="autofixModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Autofix Preview</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <h6>File: ${data.file_path}</h6>
                            <p>Total patches: ${data.total_patches}</p>
                            
                            ${data.patches.map(patch => `
                                <div class="card mb-3">
                                    <div class="card-header d-flex justify-content-between">
                                        <span>${patch.description}</span>
                                        <div>
                                            <span class="badge bg-info">Confidence: ${(patch.confidence * 100).toFixed(0)}%</span>
                                            <span class="badge bg-${patch.safety === 'safe' ? 'success' : 'warning'}">${patch.safety}</span>
                                        </div>
                                    </div>
                                    <div class="card-body">
                                        <pre><code>${patch.diff}</code></pre>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary">Apply Fixes</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.getElementById('autofixModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('autofixModal'));
        modal.show();
    }
    
    loadTrendsData() {
        fetch('/api/metrics/trends')
        .then(response => response.json())
        .then(data => {
            this.updateTrendsChart(data);
        })
        .catch(error => {
            console.error('Failed to load trends data:', error);
        });
    }
    
    updateTrendsChart(data) {
        if (!data.trends || data.trends.length === 0) return;
        
        const labels = data.trends.map(t => new Date(t.timestamp).toLocaleDateString());
        const indexValues = data.trends.map(t => t.connascence_index);
        
        this.charts.trends.data.labels = labels;
        this.charts.trends.data.datasets[0].data = indexValues;
        this.charts.trends.update();
    }
    
    updateConnectionStatus(status) {
        const indicator = document.getElementById('connectionStatus');
        const text = document.getElementById('connectionText');
        
        indicator.className = `status-indicator ${status}`;
        text.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    }
    
    getSeverityColor(severity) {
        const colors = {
            'critical': 'danger',
            'high': 'warning', 
            'medium': 'info',
            'low': 'success'
        };
        return colors[severity] || 'secondary';
    }
    
    getFileName(filePath) {
        return filePath.split('/').pop() || filePath.split('\\').pop() || filePath;
    }
    
    showNotification(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
    
    refreshData() {
        this.socket.emit('request_live_update');
    }
    
    saveSettings() {
        const settings = {
            defaultPolicy: document.getElementById('defaultPolicySelect').value,
            refreshInterval: document.getElementById('refreshInterval').value
        };
        
        localStorage.setItem('connascenceSettings', JSON.stringify(settings));
        this.showNotification('Settings saved', 'success');
    }
    
    loadSettings() {
        const settings = JSON.parse(localStorage.getItem('connascenceSettings') || '{}');
        
        if (settings.defaultPolicy) {
            document.getElementById('defaultPolicySelect').value = settings.defaultPolicy;
            document.getElementById('policySelect').value = settings.defaultPolicy;
        }
        
        if (settings.refreshInterval) {
            document.getElementById('refreshInterval').value = settings.refreshInterval;
        }
    }
}

// Export functions
function exportData(format) {
    window.open(`/api/export/${format}`, '_blank');
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', function() {
    dashboard = new ConnascenceDashboard();
    dashboard.loadSettings();
});