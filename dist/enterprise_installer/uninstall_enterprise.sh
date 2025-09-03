#!/bin/bash
# Connascence Enterprise Uninstaller

echo "Uninstalling Connascence Enterprise..."

# Stop and disable service
systemctl stop connascence 2>/dev/null || true
systemctl disable connascence 2>/dev/null || true
rm -f /etc/systemd/system/connascence.service

# Remove Python packages
pip uninstall -y connascence-analyzer-core connascence-analyzer-enterprise

# Remove configuration (ask user)
read -p "Remove configuration files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf /etc/connascence
    echo "Configuration files removed"
fi

echo "[DONE] Connascence Enterprise uninstalled"
