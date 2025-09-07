# GitHub Advanced Security Configuration

This document explains the GitHub Advanced Security setup for the connascence-safety-analyzer repository.

## Overview

The repository has been configured with:

1. **CodeQL Analysis Workflow** - Automated code scanning for security vulnerabilities
2. **SARIF Upload Integration** - Connascence analysis results uploaded to GitHub Security tab
3. **Smart Fallback Handling** - Graceful handling when Advanced Security is not yet enabled

## Configuration Files

### `.github/workflows/codeql-analysis.yml`
- Runs CodeQL security analysis on Python and JavaScript code
- Triggered on pushes to main/develop branches and pull requests
- Uses security-extended and security-and-quality query suites

### `.github/workflows/connascence-analysis.yml` (Updated)
- Added code scanning status detection
- Conditional SARIF upload only when code scanning is enabled
- Clear status messages when Advanced Security is not available

## Enabling GitHub Advanced Security

### For Private Repositories (Requires GitHub Enterprise)

1. Go to repository Settings → Code security and analysis
2. Enable "GitHub Advanced Security" 
3. Enable "Code scanning"
4. Enable "Secret scanning"
5. Enable "Push protection for secrets"

### For Public Repositories (Free)

Code scanning is automatically available. Just run the CodeQL workflow.

## Current Status

The repository is configured but **GitHub Advanced Security is not yet purchased** for this private repository.

**Current behavior:**
- Connascence analysis runs successfully
- SARIF files are generated and saved as artifacts
- SARIF upload is skipped with clear messaging
- No workflow failures due to missing security features

**After enabling Advanced Security:**
- SARIF files will automatically upload to Security tab
- Code scanning alerts will appear in repository
- Security dashboard will show all vulnerabilities

## Manual Verification

Run this command to check if code scanning is enabled:

```bash
gh api repos/DNYoussef/connascence-safety-analyzer/code-scanning/alerts --jq 'length'
```

**Current result:** HTTP 403 - Code scanning not enabled
**After setup:** Returns number of alerts (0 or more)

## Workflow Features

### Smart Detection
- Automatically detects if code scanning is available
- Only uploads SARIF when scanning is enabled
- Provides clear status messages in workflow logs

### Security Permissions
```yaml
permissions:
  contents: read
  security-events: write  # Required for SARIF upload
  actions: read
  pull-requests: write
```

### SARIF Upload Step
```yaml
- name: Upload SARIF Results
  uses: github/codeql-action/upload-sarif@v3
  if: always() && steps.check-code-scanning.outputs.code_scanning_enabled == 'true'
  continue-on-error: true
  with:
    sarif_file: connascence_analysis.sarif
    category: connascence-analysis
```

## Next Steps

1. **Enable Advanced Security** (requires GitHub Enterprise license)
2. **Run CodeQL workflow** to initialize code scanning
3. **Verify SARIF uploads** in Security → Code scanning alerts
4. **Configure branch protection** rules with security checks

## Testing

The setup can be tested even without Advanced Security enabled:

```bash
# Run the workflow
gh workflow run "Connascence Safety Analysis"

# Check logs for status messages
gh run list --workflow="Connascence Safety Analysis" --limit=1
```

Expected output will include:
- "Code scanning is not enabled - SARIF upload will be skipped"
- SARIF files available in workflow artifacts
- All other analysis steps working normally

## Benefits

- **Zero Configuration** - Works with or without Advanced Security
- **No Failures** - Graceful fallback prevents CI/CD breakage
- **Future Ready** - Automatically enables when security features are purchased
- **Clear Status** - Always shows current security setup status