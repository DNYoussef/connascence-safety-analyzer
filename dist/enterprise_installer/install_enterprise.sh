#!/bin/bash
# Connascence Enterprise Installer v1.0.0

set -e

echo "Connascence Enterprise Installation v1.0.0"
echo "=============================================="

# Check Python version
python3 --version >/dev/null 2>&1 || {
    echo "Python 3.8+ is required"
    exit 1
}

# Install core packages
echo "📦 Installing core analysis engine..."
pip install connascence-analyzer-core-1.0.0.tar.gz

echo "Installing enterprise security features..."  
pip install connascence-analyzer-enterprise-1.0.0.tar.gz

# Setup security configuration
echo "Setting up enterprise security..."
mkdir -p /etc/connascence
cp security/enterprise_deployment.yml /etc/connascence/
cp security/rbac_config.yml /etc/connascence/

# Setup systemd service
echo "Installing system service..."
cp scripts/connascence.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable connascence

# Initialize security
echo "🔐 Initializing security framework..."
connascence init-security --mode=enterprise

# Setup VS Code extension (optional)
if command -v code &> /dev/null; then
    echo "💻 Installing VS Code extension..."
    code --install-extension connascence-vscode-extension-1.0.0.vsix
fi

echo "[DONE] Enterprise installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure SSO integration: connascence configure-auth --help"
echo "2. Start the service: systemctl start connascence"
echo "3. Access dashboard: http://localhost:8080"
echo ""
echo "Enterprise support: support@connascence.com"
