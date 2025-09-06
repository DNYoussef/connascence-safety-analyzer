import * as vscode from 'vscode';
import * as path from 'path';

export class BrokenChainLogoManager {
    private static instance: BrokenChainLogoManager;
    private statusBarItem: vscode.StatusBarItem;
    private webviewPanel: vscode.WebviewPanel | undefined;

    private constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
        this.setupStatusBarLogo();
    }

    public static getInstance(): BrokenChainLogoManager {
        if (!BrokenChainLogoManager.instance) {
            BrokenChainLogoManager.instance = new BrokenChainLogoManager();
        }
        return BrokenChainLogoManager.instance;
    }

    private setupStatusBarLogo(): void {
        const logoPath = path.join(__dirname, '..', '..', 'images', 'broken-chain-logo.png');
        this.statusBarItem.text = '$(link-external) Connascence';
        this.statusBarItem.tooltip = 'Break the chains of tight coupling! Click to view dashboard';
        this.statusBarItem.command = 'connascence.showDashboard';
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        this.statusBarItem.show();
    }

    public updateStatus(metrics: {
        totalIssues: number,
        criticalIssues: number,
        qualityScore: number,
        isAnalyzing?: boolean,
        qualityGateStatus?: 'passed' | 'warning' | 'failed',
        connascenceIndex?: number
    }): void {
        if (metrics.isAnalyzing) {
            this.statusBarItem.text = '$(sync~spin) Breaking chains...';
            this.statusBarItem.tooltip = 'Quality analysis in progress...';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
            return;
        }

        const chainIcon = this.getChainStatusIcon(metrics.qualityScore, metrics.criticalIssues, metrics.qualityGateStatus);
        const statusColor = this.getStatusColor(metrics.qualityScore, metrics.criticalIssues, metrics.qualityGateStatus);
        const gateStatusText = this.getGateStatusText(metrics.qualityGateStatus);
        
        this.statusBarItem.text = `${chainIcon} ${gateStatusText}`;
        this.statusBarItem.tooltip = this.buildTooltip(metrics);
        this.statusBarItem.backgroundColor = statusColor;
    }

    private getChainStatusIcon(qualityScore: number, criticalIssues: number, gateStatus?: string): string {
        // Priority: Gate status overrides individual metrics
        if (gateStatus === 'failed' || criticalIssues > 0) {
            return '$(error)'; // Gates failed or critical issues
        } else if (gateStatus === 'warning') {
            return '$(warning)'; // Gates warning
        } else if (gateStatus === 'passed' && qualityScore >= 90) {
            return '$(check)'; // All gates passed, excellent quality
        } else if (qualityScore >= 75) {
            return '$(link)'; // Good progress
        } else if (qualityScore >= 50) {
            return '$(warning)'; // Needs work
        } else {
            return '$(link-external)'; // Poor quality - broken chain
        }
    }

    private getStatusColor(qualityScore: number, criticalIssues: number, gateStatus?: string): vscode.ThemeColor {
        // Priority: Gate status overrides individual metrics
        if (gateStatus === 'failed' || criticalIssues > 0) {
            return new vscode.ThemeColor('statusBarItem.errorBackground');
        } else if (gateStatus === 'warning') {
            return new vscode.ThemeColor('statusBarItem.warningBackground');
        } else if (gateStatus === 'passed' && qualityScore >= 75) {
            return new vscode.ThemeColor('statusBarItem.prominentBackground');
        } else if (qualityScore >= 50) {
            return new vscode.ThemeColor('statusBarItem.warningBackground');
        } else {
            return new vscode.ThemeColor('statusBarItem.errorBackground');
        }
    }

    private getGateStatusText(gateStatus?: string): string {
        switch (gateStatus) {
            case 'passed':
                return 'Gates Passed';
            case 'warning':
                return 'Gates Warning';
            case 'failed':
                return 'Gates Failed';
            default:
                return 'Quality Check';
        }
    }

    private buildTooltip(metrics: {
        totalIssues: number,
        criticalIssues: number,
        qualityScore: number,
        qualityGateStatus?: string,
        connascenceIndex?: number
    }): string {
        let tooltip = `$(link-external) Connascence Quality Gates\n\n`;
        
        // Quality Gates Status
        if (metrics.qualityGateStatus) {
            const statusIcon = metrics.qualityGateStatus === 'passed' ? '✅' : 
                             metrics.qualityGateStatus === 'warning' ? '⚠️' : '❌';
            tooltip += `Quality Gates: ${statusIcon} ${metrics.qualityGateStatus.toUpperCase()}\n`;
        }
        
        tooltip += `Quality Score: ${metrics.qualityScore}/100\n`;
        if (metrics.connascenceIndex !== undefined) {
            tooltip += `Connascence Index: ${metrics.connascenceIndex.toFixed(1)}\n`;
        }
        tooltip += `Total Issues: ${metrics.totalIssues}\n`;
        
        if (metrics.criticalIssues > 0) {
            tooltip += `Critical Issues: ${metrics.criticalIssues} 🚨\n`;
        }
        
        // Status-specific messages
        if (metrics.qualityGateStatus === 'failed') {
            tooltip += `\n🚫 Quality gates are blocking progress`;
            tooltip += `\n🔧 Fix critical issues to pass gates`;
        } else if (metrics.qualityGateStatus === 'warning') {
            tooltip += `\n⚠️ Quality gates show warnings`;
            tooltip += `\n📊 Review quality metrics`;
        } else if (metrics.qualityGateStatus === 'passed') {
            tooltip += `\n🎉 All quality gates passed!`;
            tooltip += `\n✨ Great code quality`;
        }
        
        tooltip += `\n\n💡 Break the chains of tight coupling!`;
        tooltip += `\nClick to view quality dashboard`;
        
        return tooltip;
    }

    public showBrokenChainAnimation(): void {
        if (this.webviewPanel) {
            this.webviewPanel.reveal();
            return;
        }

        this.webviewPanel = vscode.window.createWebviewPanel(
            'brokenChainAnimation',
            '$(link-external) Breaking Chains Animation',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.webviewPanel.webview.html = this.getBrokenChainAnimationHTML();

        this.webviewPanel.onDidDispose(() => {
            this.webviewPanel = undefined;
        });
    }

    private getBrokenChainAnimationHTML(): string {
        return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Breaking Chains - Connascence Analyzer</title>
    <style>
        body {
            background: linear-gradient(135deg, #1e1e1e 0%, #2d2d30 100%);
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #ffffff;
            overflow: hidden;
        }
        
        .container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            text-align: center;
        }
        
        .logo {
            width: 120px;
            height: 120px;
            margin-bottom: 2rem;
            animation: breakChain 3s infinite;
            background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M8 7a1.5 1.5 0 0 0-1.5 1.5v1A1.5 1.5 0 0 0 8 11h1a1.5 1.5 0 0 0 1.5-1.5v-1A1.5 1.5 0 0 0 9 7H8zM15 7a1.5 1.5 0 0 0-1.5 1.5v1A1.5 1.5 0 0 0 15 11h1a1.5 1.5 0 0 0 1.5-1.5v-1A1.5 1.5 0 0 0 16 7h-1z"/><path d="M8 13a1.5 1.5 0 0 0-1.5 1.5v1A1.5 1.5 0 0 0 8 17h1a1.5 1.5 0 0 0 1.5-1.5v-1A1.5 1.5 0 0 0 9 13H8zM12.5 9.5v1c0 .28.22.5.5.5h1c.28 0 .5-.22.5-.5v-1c0-.28-.22-.5-.5-.5h-1c-.28 0-.5.22-.5.5z"/></svg>');
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
        }
        
        @keyframes breakChain {
            0% { 
                transform: scale(1) rotate(0deg);
                filter: hue-rotate(0deg);
            }
            25% { 
                transform: scale(1.1) rotate(-5deg);
                filter: hue-rotate(90deg);
            }
            50% { 
                transform: scale(1.2) rotate(5deg);
                filter: hue-rotate(180deg);
            }
            75% { 
                transform: scale(1.1) rotate(-2deg);
                filter: hue-rotate(270deg);
            }
            100% { 
                transform: scale(1) rotate(0deg);
                filter: hue-rotate(360deg);
            }
        }
        
        .title {
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 1rem;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
            background-size: 400% 400%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradientShift 4s ease infinite;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .subtitle {
            font-size: 1.5rem;
            margin-bottom: 3rem;
            color: #cccccc;
        }
        
        .chain-visualization {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 2rem 0;
        }
        
        .chain-link {
            font-size: 2rem;
            margin: 0 0.5rem;
            animation: linkBreak 2s infinite;
        }
        
        .chain-link:nth-child(1) { animation-delay: 0s; }
        .chain-link:nth-child(2) { animation-delay: 0.2s; }
        .chain-link:nth-child(3) { animation-delay: 0.4s; }
        .chain-link:nth-child(4) { animation-delay: 0.6s; }
        .chain-link:nth-child(5) { animation-delay: 0.8s; }
        
        @keyframes linkBreak {
            0%, 80% { 
                transform: scale(1) rotate(0deg);
                opacity: 1;
            }
            90% { 
                transform: scale(1.3) rotate(180deg);
                opacity: 0.7;
            }
            100% { 
                transform: scale(1) rotate(360deg);
                opacity: 1;
            }
        }
        
        .mission-statement {
            max-width: 800px;
            font-size: 1.2rem;
            line-height: 1.8;
            color: #e0e0e0;
            margin: 2rem auto;
            padding: 2rem;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
        }
        
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 2rem 0;
            flex-wrap: wrap;
        }
        
        .stat {
            text-align: center;
            padding: 1rem;
            margin: 0.5rem;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            min-width: 150px;
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #4ecdc4;
        }
        
        .stat-label {
            font-size: 1rem;
            color: #cccccc;
        }
        
        .floating-icons {
            position: absolute;
            width: 100%;
            height: 100%;
            overflow: hidden;
            pointer-events: none;
        }
        
        .floating-icon {
            position: absolute;
            font-size: 2rem;
            opacity: 0.3;
            animation: float 10s infinite;
        }
        
        @keyframes float {
            0% { 
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            10% { opacity: 0.3; }
            90% { opacity: 0.3; }
            100% { 
                transform: translateY(-100px) rotate(360deg);
                opacity: 0;
            }
        }
    </style>
</head>
<body>
    <div class="floating-icons" id="floatingIcons"></div>
    
    <div class="container">
        <div class="logo"></div>
        
        <div class="title">Break the Chains!</div>
        
        <div class="subtitle">Enterprise-grade Connascence Analysis</div>
        
        <div class="chain-visualization">
            <span class="chain-link">🔗</span>
            <span class="chain-link">⛓️</span>
            <span class="chain-link">💥</span>
            <span class="chain-link">✂️</span>
            <span class="chain-link">🔓</span>
        </div>
        
        <div class="mission-statement">
            <strong>🎯 Our Mission:</strong> Transform tightly coupled code into loosely coupled, maintainable architecture. 
            We detect 9 types of connascence violations, 10 NASA Power of Ten safety rules, and god object anti-patterns 
            to help you build better, safer, more maintainable software.
            
            <br><br>
            
            <strong>💪 Break the chains of:</strong><br>
            🔗 Name coupling • Type coupling • Position coupling<br>
            ⏰ Timing coupling • 🔐 Magic values • ⚙️ Algorithm coupling<br>
            👑 God objects • 🚀 NASA violations • And more!
        </div>
        
        <div class="stats" id="stats">
            <div class="stat">
                <div class="stat-number">9</div>
                <div class="stat-label">Connascence Types</div>
            </div>
            <div class="stat">
                <div class="stat-number">10</div>
                <div class="stat-label">NASA Safety Rules</div>
            </div>
            <div class="stat">
                <div class="stat-number">5</div>
                <div class="stat-label">God Object Patterns</div>
            </div>
            <div class="stat">
                <div class="stat-number">∞</div>
                <div class="stat-label">Chains Broken</div>
            </div>
        </div>
    </div>

    <script>
        // Create floating chain icons
        const icons = ['⛓', '🔗', '💔', '✂', '🔓', '💥', '⚡', '✨'];
        const container = document.getElementById('floatingIcons');
        
        function createFloatingIcon() {
            const icon = document.createElement('div');
            icon.className = 'floating-icon';
            icon.textContent = icons[Math.floor(Math.random() * icons.length)];
            icon.style.left = Math.random() * 100 + '%';
            icon.style.animationDuration = (5 + Math.random() * 10) + 's';
            icon.style.animationDelay = Math.random() * 2 + 's';
            container.appendChild(icon);
            
            setTimeout(() => {
                if (container.contains(icon)) {
                    container.removeChild(icon);
                }
            }, 15000);
        }
        
        // Create floating icons periodically
        setInterval(createFloatingIcon, 1000);
        
        // Initial batch of icons
        for (let i = 0; i < 5; i++) {
            setTimeout(createFloatingIcon, i * 200);
        }
    </script>
</body>
</html>`;
    }

    public hide(): void {
        this.statusBarItem.hide();
    }

    public show(): void {
        this.statusBarItem.show();
    }

    public dispose(): void {
        this.statusBarItem.dispose();
        if (this.webviewPanel) {
            this.webviewPanel.dispose();
        }
    }
}