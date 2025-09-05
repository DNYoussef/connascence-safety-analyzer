"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConnascenceDashboardProvider = exports.DashboardItem = void 0;
const vscode = __importStar(require("vscode"));
class DashboardItem extends vscode.TreeItem {
    constructor(label, collapsibleState, value, contextValue, command) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.value = value;
        this.contextValue = contextValue;
        this.command = command;
        this.tooltip = value ? `${label}: ${value}` : label;
        this.description = value || '';
        this.contextValue = contextValue;
    }
}
exports.DashboardItem = DashboardItem;
class ConnascenceDashboardProvider {
    constructor(connascenceService) {
        this.connascenceService = connascenceService;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.qualityMetrics = null;
        this.analysisResults = null;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    updateData(qualityMetrics, analysisResults) {
        this.qualityMetrics = qualityMetrics;
        this.analysisResults = analysisResults;
        this.refresh();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            return Promise.resolve(this.getRootElements());
        }
        switch (element.contextValue) {
            case 'qualityOverview':
                return Promise.resolve(this.getQualityOverviewChildren());
            case 'recentAnalysis':
                return Promise.resolve(this.getRecentAnalysisChildren());
            case 'safetyCompliance':
                return Promise.resolve(this.getSafetyComplianceChildren());
            case 'quickActions':
                return Promise.resolve(this.getQuickActionsChildren());
            default:
                return Promise.resolve([]);
        }
    }
    getRootElements() {
        return [
            new DashboardItem('Quality Overview', vscode.TreeItemCollapsibleState.Expanded, undefined, 'qualityOverview'),
            new DashboardItem('Safety Compliance', vscode.TreeItemCollapsibleState.Expanded, undefined, 'safetyCompliance'),
            new DashboardItem('Recent Analysis', vscode.TreeItemCollapsibleState.Expanded, undefined, 'recentAnalysis'),
            new DashboardItem('Quick Actions', vscode.TreeItemCollapsibleState.Expanded, undefined, 'quickActions')
        ];
    }
    getQualityOverviewChildren() {
        if (!this.qualityMetrics) {
            return [
                new DashboardItem('No data available', vscode.TreeItemCollapsibleState.None, 'Run analysis first')
            ];
        }
        return [
            new DashboardItem('Overall Score', vscode.TreeItemCollapsibleState.None, `${this.qualityMetrics.overallScore || 0}/100`, 'metric'),
            new DashboardItem('Total Issues', vscode.TreeItemCollapsibleState.None, `${this.qualityMetrics.totalIssues || 0}`, 'metric'),
            new DashboardItem('Files Analyzed', vscode.TreeItemCollapsibleState.None, `${this.qualityMetrics.filesAnalyzed || 0}`, 'metric'),
            new DashboardItem('Critical Issues', vscode.TreeItemCollapsibleState.None, `${this.qualityMetrics.criticalIssues || 0}`, 'metric')
        ];
    }
    getSafetyComplianceChildren() {
        const config = vscode.workspace.getConfiguration('connascence');
        const safetyProfile = config.get('safetyProfile', 'modern_general');
        return [
            new DashboardItem('Current Profile', vscode.TreeItemCollapsibleState.None, safetyProfile, 'profile'),
            new DashboardItem('Compliance Status', vscode.TreeItemCollapsibleState.None, this.qualityMetrics?.compliant ? '✅ Compliant' : '❌ Non-Compliant', 'compliance'),
            new DashboardItem('Safety Violations', vscode.TreeItemCollapsibleState.None, `${this.qualityMetrics?.safetyViolations || 0}`, 'violations')
        ];
    }
    getRecentAnalysisChildren() {
        if (!this.analysisResults || !this.analysisResults.recentFiles) {
            return [
                new DashboardItem('No recent analysis', vscode.TreeItemCollapsibleState.None)
            ];
        }
        return this.analysisResults.recentFiles.slice(0, 5).map((file) => new DashboardItem(file.name, vscode.TreeItemCollapsibleState.None, `${file.issues} issues`, 'recentFile', {
            command: 'vscode.open',
            title: 'Open File',
            arguments: [vscode.Uri.file(file.path)]
        }));
    }
    getQuickActionsChildren() {
        return [
            new DashboardItem('Analyze Current File', vscode.TreeItemCollapsibleState.None, undefined, 'action', {
                command: 'connascence.analyzeFile',
                title: 'Analyze Current File'
            }),
            new DashboardItem('Analyze Workspace', vscode.TreeItemCollapsibleState.None, undefined, 'action', {
                command: 'connascence.analyzeWorkspace',
                title: 'Analyze Workspace'
            }),
            new DashboardItem('Generate Report', vscode.TreeItemCollapsibleState.None, undefined, 'action', {
                command: 'connascence.generateReport',
                title: 'Generate Report'
            }),
            new DashboardItem('Open Settings', vscode.TreeItemCollapsibleState.None, undefined, 'action', {
                command: 'connascence.openSettings',
                title: 'Open Settings'
            })
        ];
    }
}
exports.ConnascenceDashboardProvider = ConnascenceDashboardProvider;
//# sourceMappingURL=dashboardProvider.js.map