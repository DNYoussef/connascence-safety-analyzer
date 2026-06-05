# Install Connascence Quality Gate Pre-Commit Hook
# Part of WIRE-002: Wire Connascence Bridge to All Code Projects
# Usage: .\install-pre-commit-hook.ps1 -ProjectPath "D:\Projects\my-project"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath,

    [Parameter(Mandatory=$false)]
    [switch]$Strict,

    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$CONNASCENCE_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $CONNASCENCE_ROOT) {
    $CONNASCENCE_ROOT = "D:\Projects\connascence"
}

$ProjectPath = (Resolve-Path $ProjectPath -ErrorAction SilentlyContinue).Path
if (-not $ProjectPath) {
    Write-Error "Project path not found"
    exit 1
}

$GitHooksPath = Join-Path $ProjectPath ".git\hooks"
if (-not (Test-Path $GitHooksPath)) {
    Write-Error "Not a git repository: $ProjectPath"
    exit 1
}

$PreCommitPath = Join-Path $GitHooksPath "pre-commit"

if ((Test-Path $PreCommitPath) -and -not $Force) {
    Write-Warning "pre-commit hook already exists. Use -Force to overwrite."
    exit 1
}

$StrictFlag = if ($Strict) { "--strict" } else { "" }

$HookContent = @"
#!/bin/bash
# Connascence Quality Gate Pre-Commit Hook
# Installed: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# Part of WIRE-002: Wire Connascence Bridge to All Code Projects

echo "Running 7-Analyzer Quality Gate..."

# Find Python
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "Error: Python not found"
    exit 1
fi

# Run quality gate
QUALITY_GATE="$CONNASCENCE_ROOT/scripts/quality-gate.py"

if [ -f "`$QUALITY_GATE" ]; then
    `$PYTHON "`$QUALITY_GATE" . $StrictFlag
    EXIT_CODE=`$?

    if [ `$EXIT_CODE -ne 0 ]; then
        echo ""
        echo "Quality gate FAILED. Commit blocked."
        echo "Fix violations and try again."
        exit 1
    fi
else
    echo "Warning: Quality gate script not found at `$QUALITY_GATE"
    echo "Skipping quality check."
fi

exit 0
"@

# Write the hook file
$HookContent | Out-File -FilePath $PreCommitPath -Encoding ASCII -NoNewline

# Make executable on Unix systems (no-op on Windows but good for WSL)
if (Get-Command chmod -ErrorAction SilentlyContinue) {
    chmod +x $PreCommitPath
}

Write-Host "Pre-commit hook installed at: $PreCommitPath" -ForegroundColor Green
Write-Host "Strict mode: $Strict" -ForegroundColor Cyan
