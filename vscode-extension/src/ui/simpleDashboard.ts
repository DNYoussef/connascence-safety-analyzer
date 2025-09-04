export function generateSimpleDashboardHTML(summary: any, charts: any): string {
    return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Connascence Dashboard</title>
    <style>
        body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); padding: 20px; }
        .summary { margin-bottom: 30px; }
        .ai-chat { border: 1px solid var(--vscode-panel-border); border-radius: 8px; padding: 15px; }
        .message { margin-bottom: 10px; }
        .user-message { color: var(--vscode-charts-blue); }
        .ai-message { color: var(--vscode-charts-green); }
        input, button { padding: 8px; margin: 5px; }
    </style>
</head>
<body>
    <div class="summary">
        <h1>Connascence Dashboard</h1>
        <p>Total Files: ${summary.totalFiles || 0}</p>
        <p>Total Violations: ${summary.totalViolations || 0}</p>
        <p>Critical Issues: ${(summary.severityBreakdown && summary.severityBreakdown.critical) || 0}</p>
    </div>
    
    <div class="ai-chat">
        <h2>AI Assistant</h2>
        <div id="chatMessages"></div>
        <input id="chatInput" type="text" placeholder="Ask about your code quality...">
        <button id="sendButton">Send</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        
        function addMessage(message, isUser) {
            const div = document.createElement('div');
            div.className = isUser ? 'message user-message' : 'message ai-message';
            div.textContent = (isUser ? 'You: ' : 'AI: ') + message;
            chatMessages.appendChild(div);
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
                        criticalCount: ${(summary.severityBreakdown && summary.severityBreakdown.critical) || 0},
                        files: ${summary.totalFiles || 0}
                    }
                });
                chatInput.value = '';
            }
        });
        
        window.addEventListener('message', event => {
            const message = event.data;
            if (message.type === 'aiChatResponse') {
                addMessage(message.response, false);
            }
        });
        
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendButton.click();
            }
        });
    </script>
</body>
</html>`;
}