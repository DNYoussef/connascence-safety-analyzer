    private generateDashboardHTML(summary: any, charts: any): string {
        return `<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Connascence Dashboard</title>
            <style>
                body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); }
                .summary { padding: 20px; }
                .ai-chat-section { margin-top: 30px; padding: 20px; }
            </style>
        </head>
        <body>
            <div class="summary">
                <h1>Dashboard</h1>
                <p>Total Files: ${summary.totalFiles || 0}</p>
                <p>Total Violations: ${summary.totalViolations || 0}</p>
            </div>
            <div class="ai-chat-section">
                <h2>AI Assistant</h2>
                <div id="chatMessages"></div>
                <input id="chatInput" type="text" placeholder="Ask about your code quality...">
                <button id="sendButton">Send</button>
            </div>
            <script>
                const chatMessages = document.getElementById('chatMessages');
                const chatInput = document.getElementById('chatInput');
                const sendButton = document.getElementById('sendButton');
                
                function addMessage(message, isUser) {
                    const div = document.createElement('div');
                    div.textContent = (isUser ? 'You: ' : 'AI: ') + message;
                    chatMessages.appendChild(div);
                }
                
                sendButton.addEventListener('click', () => {
                    const message = chatInput.value.trim();
                    if (message) {
                        addMessage(message, true);
                        chatInput.value = '';
                    }
                });
            </script>
        </body>
        </html>`;
    }