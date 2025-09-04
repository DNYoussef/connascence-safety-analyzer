@echo off
echo === MARKDOWN CLEANUP SCRIPT FOR WINDOWS ===
echo.
echo This script will delete 1859 unnecessary markdown files (96% reduction)
echo Preserving only critical project documentation (79 files)
echo.
echo Categories being removed:
echo - VSCode extension node_modules (806 files)
echo - Demo repositories (912 files)  
echo - Claude Flow system files (141 files)
echo.
pause

echo.
echo === STEP 1: Remove VSCode Extension Dependencies ===
if exist "vscode-extension\node_modules" (
    echo Deleting all .md files from vscode-extension/node_modules...
    for /r "vscode-extension\node_modules" %%f in (*.md) do (
        del "%%f" 2>nul
    )
    echo VSCode extension .md files removed.
) else (
    echo No vscode-extension/node_modules directory found.
)

echo.
echo === STEP 2: Remove Demo Repository Files ===
if exist "sale\demos" (
    echo Deleting all .md files from sale/demos...
    for /r "sale\demos" %%f in (*.md) do (
        del "%%f" 2>nul
    )
    echo Demo repository .md files removed.
) else (
    echo No sale/demos directory found.
)

echo.
echo === STEP 3: Remove Claude Flow System Files ===
if exist ".claude" (
    echo Deleting all .md files from .claude directory...
    for /r ".claude" %%f in (*.md) do (
        del "%%f" 2>nul
    )
    echo Claude Flow system .md files removed.
) else (
    echo No .claude directory found.
)

echo.
echo === STEP 4: Remove Duplicate Express Directory ===
if exist "express" (
    echo Deleting all .md files from express directory...
    for /r "express" %%f in (*.md) do (
        del "%%f" 2>nul
    )
    echo Express duplicate .md files removed.
) else (
    echo No express directory found.
)

echo.
echo === STEP 5: Remove pytest cache README ===
if exist ".pytest_cache\README.md" del ".pytest_cache\README.md" 2>nul
if exist "tests\.pytest_cache\README.md" del "tests\.pytest_cache\README.md" 2>nul

echo.
echo === CLEANUP COMPLETE ===
echo.
echo PRESERVED FILES (should remain):
echo - README.md (main)
echo - CLAUDE.md 
echo - CHANGELOG.md
echo - docs/ directory (5 files)
echo - analysis/ directory (5 files)
echo - data-room/ directory (66 files)
echo.
echo Verifying preserved files exist...
if exist "README.md" echo ✅ README.md preserved
if exist "CLAUDE.md" echo ✅ CLAUDE.md preserved  
if exist "CHANGELOG.md" echo ✅ CHANGELOG.md preserved
if exist "docs" echo ✅ docs/ directory preserved
if exist "analysis" echo ✅ analysis/ directory preserved
if exist "data-room" echo ✅ data-room/ directory preserved

echo.
echo Final count of .md files:
dir *.md /s /b | find /c ".md"

echo.
echo === CLEANUP COMPLETED SUCCESSFULLY ===
pause