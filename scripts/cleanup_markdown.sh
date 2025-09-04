#!/bin/bash
# Connascence Markdown Cleanup Script  
# Removes 1,859+ external/demo/system markdown files while preserving 79 core project files

echo "Starting markdown file cleanup..."
echo

echo "BEFORE cleanup:"
find . -name "*.md" | wc -l
echo "Total markdown files found"
echo

echo "Phase 1: Removing external dependencies (806 files)"
if [ -d "vscode-extension/node_modules" ]; then
    echo "Removing vscode-extension/node_modules markdown files..."
    find ./vscode-extension/node_modules -name "*.md" -delete
    echo "Phase 1 complete: External dependencies removed"
else
    echo "Phase 1 skipped: vscode-extension/node_modules not found"
fi
echo

echo "Phase 2: Removing demo repositories (912 files)"
if [ -d "sale/demos" ]; then
    echo "Removing sale/demos markdown files..."
    find ./sale/demos -name "*.md" -delete
    echo "Phase 2 complete: Demo repositories removed"
else
    echo "Phase 2 skipped: sale/demos not found"
fi
echo

echo "Phase 3: Removing Claude Flow system files (141 files)"
if [ -d ".claude" ]; then
    echo "Removing .claude system markdown files..."
    find ./.claude -name "*.md" -delete
    echo "Phase 3 complete: Claude Flow system files removed"
else
    echo "Phase 3 skipped: .claude directory not found"  
fi
echo

echo "Phase 4: Removing duplicate Express repository (12 files)"
if [ -d "express" ]; then
    echo "Removing express/ markdown files..."
    find ./express -name "*.md" -delete
    echo "Phase 4 complete: Duplicate Express repository removed"
else
    echo "Phase 4 skipped: express directory not found"
fi
echo

echo "AFTER cleanup:"
find . -name "*.md" | wc -l
echo "Total markdown files remaining (should be ~79)"
echo

echo "==============================================="
echo "CLEANUP SUMMARY"
echo "==============================================="
echo "Files preserved (should be ~79):"
echo "- README.md, CLAUDE.md, CHANGELOG.md (root)"
echo "- docs/*.md (5 files - enterprise documentation)"
echo "- analysis/self-analysis/*.md (5 files - analysis results)" 
echo "- data-room/**/*.md (66 files - buyer materials)"
echo "- .pytest_cache/README.md (1 file - testing)"
echo
echo "Files removed (~1,859):"
echo "- vscode-extension/node_modules/**/*.md (806 files)"
echo "- sale/demos/**/*.md (912 files)"
echo "- .claude/**/*.md (141 files)"
echo "- express/*.md (12 files)"
echo
echo "Cleanup completed successfully!"