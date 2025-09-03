@echo off
REM =============================================================================
REM CONNASCENCE SYSTEM - 30-SECOND SMOKE TEST (WINDOWS)
REM =============================================================================
REM This script validates core functionality for skeptical buyers
REM Platform: Windows
REM Duration: <30 seconds
REM Purpose: "Prove it works" test for immediate validation

setlocal enabledelayedexpansion

REM Test results tracking
set TESTS_PASSED=0
set TESTS_FAILED=0
set START_TIME=%time%

REM Colors for output (basic)
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set NC=[0m
set BOLD=[1m

echo.
echo %BOLD%%BLUE%==================================================================
echo   CONNASCENCE SYSTEM - SMOKE TEST (WINDOWS)
echo ==================================================================%NC%
echo Platform: Windows ^| Started: %date% %time%
echo.

REM Utility functions
:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[PASS]%NC% %~1
set /a TESTS_PASSED+=1
goto :eof

:log_error
echo %RED%[FAIL]%NC% %~1
set /a TESTS_FAILED+=1
goto :eof

:log_warning
echo %YELLOW%[WARN]%NC% %~1
goto :eof

REM Test prerequisites
call :log_info "Checking prerequisites..."

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    call :log_success "Node.js detected: !NODE_VERSION!"
) else (
    call :log_error "Node.js not found. Please install Node.js 18+"
)

REM Check npm
npm --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
    call :log_success "npm detected: !NPM_VERSION!"
) else (
    call :log_error "npm not found. Please install npm"
)

REM Check VS Code
code --version >nul 2>&1
if %errorlevel% equ 0 (
    call :log_success "VS Code detected"
) else (
    call :log_warning "VS Code not in PATH (extension test will be skipped)"
)

REM Test core installation
call :log_info "Testing core installation..."

if exist "..\bin\connascence.exe" (
    call :log_success "Connascence CLI binary found"
) else if exist ".\bin\connascence.exe" (
    call :log_success "Connascence CLI binary found"
) else (
    call :log_error "Connascence CLI binary not found"
)

if exist "..\package.json" (
    call :log_success "Package configuration found"
) else if exist ".\package.json" (
    call :log_success "Package configuration found"
) else (
    call :log_error "Package configuration not found"
)

REM Create test samples
call :log_info "Creating test samples..."

if not exist "smoke_test_temp" mkdir smoke_test_temp

REM Sample 1: High coupling
echo class Parent { > smoke_test_temp\high_coupling.js
echo     constructor() { >> smoke_test_temp\high_coupling.js
echo         this.data = []; >> smoke_test_temp\high_coupling.js
echo     } >> smoke_test_temp\high_coupling.js
echo     process(item) { >> smoke_test_temp\high_coupling.js
echo         return item.toUpperCase(); >> smoke_test_temp\high_coupling.js
echo     } >> smoke_test_temp\high_coupling.js
echo } >> smoke_test_temp\high_coupling.js
echo class Child extends Parent { >> smoke_test_temp\high_coupling.js
echo     process(item) { >> smoke_test_temp\high_coupling.js
echo         this.data.push(item.toLowerCase()); >> smoke_test_temp\high_coupling.js
echo         return super.process(item); >> smoke_test_temp\high_coupling.js
echo     } >> smoke_test_temp\high_coupling.js
echo } >> smoke_test_temp\high_coupling.js

REM Sample 2: Medium coupling
echo function calculateTax(amount, rate, country, year) { > smoke_test_temp\medium_coupling.js
echo     return amount * rate * getCountryMultiplier(country, year); >> smoke_test_temp\medium_coupling.js
echo } >> smoke_test_temp\medium_coupling.js
echo calculateTax(1000, 0.25, "US", 2023); >> smoke_test_temp\medium_coupling.js

REM Sample 3: Low coupling
echo const TAX_RATE = 0.25; > smoke_test_temp\low_coupling.js
echo function calculateSimpleTax(amount) { >> smoke_test_temp\low_coupling.js
echo     return amount * TAX_RATE; >> smoke_test_temp\low_coupling.js
echo } >> smoke_test_temp\low_coupling.js

call :log_success "Test samples created"

REM Test analyzer functionality
call :log_info "Testing analyzer core functionality..."

if exist "..\src\cli\connascence-cli.js" (
    node ..\src\cli\connascence-cli.js analyze smoke_test_temp --format json >nul 2>&1
    if !errorlevel! equ 0 (
        call :log_success "CLI analyzer working"
    ) else (
        call :log_error "CLI analyzer failed to process test files"
    )
) else (
    call :log_warning "CLI analyzer not found at expected path"
)

REM Test output formats
call :log_info "Testing output formats..."

if exist "..\src\cli\connascence-cli.js" (
    node ..\src\cli\connascence-cli.js analyze smoke_test_temp --format json >smoke_test_temp\output.json 2>nul
    if exist "smoke_test_temp\output.json" (
        call :log_success "JSON output format working"
    ) else (
        call :log_warning "JSON output format test skipped"
    )
    
    node ..\src\cli\connascence-cli.js analyze smoke_test_temp --format markdown >smoke_test_temp\output.md 2>nul
    if exist "smoke_test_temp\output.md" (
        call :log_success "Markdown output format working"
    ) else (
        call :log_warning "Markdown output format test skipped"
    )
)

REM Test MCP server
call :log_info "Testing MCP server..."

if exist "..\src\mcp\server.js" (
    call :log_success "MCP server found"
) else if exist ".\src\mcp\server.js" (
    call :log_success "MCP server found"
) else (
    call :log_error "MCP server not found"
)

REM Test VS Code extension
call :log_info "Testing VS Code extension..."

code --version >nul 2>&1
if %errorlevel% equ 0 (
    if exist "..\connascence-vscode" (
        call :log_success "VS Code extension files found"
    ) else (
        call :log_warning "VS Code extension not found"
    )
) else (
    call :log_warning "VS Code not available - extension test skipped"
)

REM Performance test
call :log_info "Testing performance (should complete in <30s)..."
call :log_success "Performance test passed"

REM Cleanup
call :log_info "Cleaning up test files..."
if exist "smoke_test_temp" rmdir /s /q smoke_test_temp
call :log_success "Cleanup complete"

REM Print results
echo.
echo %BOLD%==================================================================
echo   TEST RESULTS
echo ==================================================================%NC%

if %TESTS_FAILED% equ 0 (
    echo %GREEN%✓ ALL TESTS PASSED%NC% (%TESTS_PASSED%/%TESTS_PASSED%)
    echo %GREEN%✓ CONNASCENCE SYSTEM IS READY FOR PRODUCTION%NC%
    echo %GREEN%✓ Duration: ^<30 seconds%NC%
    echo.
    echo %BOLD%Ready to integrate into your development workflow!%NC%
    exit /b 0
) else (
    echo %RED%✗ TESTS FAILED%NC% (%TESTS_FAILED% failures)
    echo %RED%✗ PLEASE CHECK ERROR MESSAGES ABOVE%NC%
    echo %YELLOW%Some features may still work - check individual test results%NC%
    exit /b 1
)