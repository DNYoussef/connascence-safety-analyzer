# Connascence Enterprise Distribution Manifest

**Version**: 1.0.0  
**Build Date**: 20250903  
**Build Timestamp**: 2025-09-03 00:16:57

## Packages Included

### connascence-analyzer-core
- **Description**: Core Connascence Analysis Engine
- **Target**: python  
- **Components**: analyzer/, policy/, integrations/, cli/, autofix/, reporting/, grammar/, mcp/

### connascence-analyzer-enterprise
- **Description**: Enterprise Security and Compliance Features
- **Target**: python  
- **Components**: security/, demo/, dashboard/

### connascence-vscode-extension
- **Description**: VS Code Integration Extension
- **Target**: vscode  
- **Components**: vscode-extension/

### connascence-sales-demo
- **Description**: Sales Demo and Proof Points
- **Target**: demo  
- **Components**: sales/

## Enterprise Features

- [DONE] Role-Based Access Control (RBAC)
- [DONE] Multi-Factor Authentication
- [DONE] Tamper-resistant audit logging
- [DONE] Data encryption (AES-256)
- [DONE] Air-gapped deployment mode
- [DONE] Enterprise SSO integration
- [DONE] SIEM integration
- [DONE] SOC 2 compliance controls
- [DONE] General Safety safety profiles

## Validated Proof Points

- **False Positive Rate**: <5% (validated on Celery, curl, Express)
- **Autofix Acceptance**: >=60% (production-safe transformations)  
- **General Safety Compliance**: Power of Ten rules automated
- **Enterprise Security**: Full RBAC, audit, air-gap ready

## Supported Platforms

- Linux (Ubuntu 20.04+)
- Linux (RHEL 8+)
- Linux (CentOS 8+)
- macOS (via Docker)
- Windows (via WSL2)

## Installation

For enterprise deployment:
```bash
sudo ./enterprise_installer/install_enterprise.sh
```

For sales demos:
```bash
python sale/run_all_demos.py
```

## Support

- **Enterprise Support**: support@connascence.com
- **Sales Inquiries**: sales@connascence.com
- **Documentation**: https://docs.connascence.com

---

*Connascence Enterprise - Where Architecture Meets Safety*  
*Copyright � 2024 Connascence Systems. All rights reserved.*
