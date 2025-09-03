# Connascence Enterprise Installer v1.0.0

## System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, RHEL 8+, CentOS 8+)
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB available space
- **Network**: Internet access for initial setup (air-gapped mode available)

## Quick Installation

```bash
sudo ./install_enterprise.sh
```

## Manual Installation

If you prefer manual installation:

1. Install core package:
   ```bash
   pip install connascence-analyzer-core-1.0.0.tar.gz
   ```

2. Install enterprise features:
   ```bash
   pip install connascence-analyzer-enterprise-1.0.0.tar.gz
   ```

3. Configure security:
   ```bash
   connascence init-security --mode=enterprise
   ```

## Air-Gapped Installation

For classified/sensitive environments:

1. Copy this entire installer package to target system
2. Run with air-gapped flag:
   ```bash
   sudo ./install_enterprise.sh --air-gapped
   ```

## Post-Installation Configuration

### 1. SSO Integration
```bash
# SAML
connascence configure-auth --provider=saml --config-file=saml.xml

# LDAP  
connascence configure-auth --provider=ldap --server=ldaps://ldap.company.com

# OIDC
connascence configure-auth --provider=oidc --issuer=https://auth.company.com
```

### 2. Start Services
```bash
sudo systemctl start connascence
sudo systemctl status connascence
```

### 3. Access Dashboard
Navigate to: http://localhost:8080

Default admin credentials:
- Username: admin
- Password: (generated during installation, check logs)

## Enterprise Features Included

### Security
- [DONE] Role-Based Access Control (6 roles)
- [DONE] Multi-Factor Authentication
- [DONE] Tamper-resistant audit logging
- [DONE] Data encryption (AES-256)
- [DONE] Air-gapped deployment mode

### Compliance
- [DONE] SOC 2 Type II controls
- [DONE] ISO 27001 alignment
- [DONE] General Safety Standards profiles
- [DONE] NIST framework mapping

### Integration
- [DONE] Enterprise SSO (SAML, LDAP, OIDC)
- [DONE] SIEM integration (Splunk, ELK)
- [DONE] CI/CD pipelines (Jenkins, GitHub Actions)
- [DONE] VS Code extension

## Support

- **Enterprise Support**: support@connascence.com
- **Sales**: sales@connascence.com  
- **Documentation**: https://docs.connascence.com/enterprise
- **Status Page**: https://status.connascence.com

## License

This software is licensed under the Connascence Enterprise License.
See LICENSE.txt for full terms.

Copyright © 2024 Connascence Systems. All rights reserved.
