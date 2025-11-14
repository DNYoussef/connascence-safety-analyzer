#!/bin/bash
# Cleanup Scaffolding Script
# Moves valuable content to docs/ and removes development scaffolding
# Run after project reaches production maturity

set -e

echo "==================================="
echo "Cleanup Scaffolding Script"
echo "==================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo -e "${YELLOW}Project root: $PROJECT_ROOT${NC}"
echo ""

# Create docs/archive directory if it doesn't exist
mkdir -p docs/archive
mkdir -p docs/development

echo -e "${GREEN}Step 1: Moving valuable .claude content to docs/${NC}"
echo "--------------------------------------"

# Move valuable .claude files to docs
if [ -d ".claude" ]; then
    echo "Processing .claude directory..."

    # Move agents documentation
    if [ -d ".claude/agents" ]; then
        echo "  - Moving agents/ to docs/development/agents/"
        mkdir -p docs/development/agents
        cp -r .claude/agents/* docs/development/agents/ 2>/dev/null || true
    fi

    # Move skills documentation
    if [ -d ".claude/skills" ]; then
        echo "  - Moving skills/ to docs/development/skills/"
        mkdir -p docs/development/skills
        cp -r .claude/skills/* docs/development/skills/ 2>/dev/null || true
    fi

    # Move CLAUDE.md if exists
    if [ -f ".claude/CLAUDE.md" ]; then
        echo "  - Moving CLAUDE.md to docs/archive/CLAUDE_INSTRUCTIONS.md"
        cp .claude/CLAUDE.md docs/archive/CLAUDE_INSTRUCTIONS.md
    fi

    # Move hooks documentation
    if [ -d ".claude/hooks" ]; then
        echo "  - Moving hooks/ to docs/development/hooks/"
        mkdir -p docs/development/hooks
        cp -r .claude/hooks/* docs/development/hooks/ 2>/dev/null || true
    fi

    echo -e "${GREEN}  Done moving .claude content${NC}"
else
    echo -e "${YELLOW}  No .claude directory found${NC}"
fi

echo ""
echo -e "${GREEN}Step 2: Moving valuable .claude-flow content to docs/${NC}"
echo "--------------------------------------"

# Move valuable .claude-flow files to docs
if [ -d ".claude-flow" ]; then
    echo "Processing .claude-flow directory..."

    # Move swarm configurations
    if [ -d ".claude-flow/swarms" ]; then
        echo "  - Moving swarms/ to docs/development/swarms/"
        mkdir -p docs/development/swarms
        cp -r .claude-flow/swarms/* docs/development/swarms/ 2>/dev/null || true
    fi

    # Move workflow configurations
    if [ -d ".claude-flow/workflows" ]; then
        echo "  - Moving workflows/ to docs/development/workflows/"
        mkdir -p docs/development/workflows
        cp -r .claude-flow/workflows/* docs/development/workflows/ 2>/dev/null || true
    fi

    # Move memory configurations
    if [ -d ".claude-flow/memory" ]; then
        echo "  - Moving memory/ to docs/development/memory/"
        mkdir -p docs/development/memory
        cp -r .claude-flow/memory/* docs/development/memory/ 2>/dev/null || true
    fi

    echo -e "${GREEN}  Done moving .claude-flow content${NC}"
else
    echo -e "${YELLOW}  No .claude-flow directory found${NC}"
fi

echo ""
echo -e "${GREEN}Step 3: Creating archive of scaffolding directories${NC}"
echo "--------------------------------------"

# Create timestamp for archive
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_NAME="scaffolding_archive_$TIMESTAMP.tar.gz"

echo "Creating archive: $ARCHIVE_NAME"

# Create archive of scaffolding directories
tar -czf "docs/archive/$ARCHIVE_NAME" \
    .claude \
    .claude-flow \
    2>/dev/null || true

if [ -f "docs/archive/$ARCHIVE_NAME" ]; then
    echo -e "${GREEN}  Archive created successfully: docs/archive/$ARCHIVE_NAME${NC}"
else
    echo -e "${YELLOW}  Warning: Archive creation failed or no directories to archive${NC}"
fi

echo ""
echo -e "${GREEN}Step 4: Removing scaffolding directories${NC}"
echo "--------------------------------------"

# Confirm before deletion
echo -e "${YELLOW}This will DELETE the following directories:${NC}"
echo "  - .claude"
echo "  - .claude-flow"
echo ""
echo -e "${YELLOW}Content has been backed up to docs/archive/$ARCHIVE_NAME${NC}"
echo ""
read -p "Continue with deletion? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Remove .claude directory
    if [ -d ".claude" ]; then
        echo "  - Removing .claude/"
        rm -rf .claude
        echo -e "${GREEN}    Removed${NC}"
    fi

    # Remove .claude-flow directory
    if [ -d ".claude-flow" ]; then
        echo "  - Removing .claude-flow/"
        rm -rf .claude-flow
        echo -e "${GREEN}    Removed${NC}"
    fi

    echo -e "${GREEN}  Scaffolding directories removed${NC}"
else
    echo -e "${YELLOW}  Deletion cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Step 5: Updating .gitignore${NC}"
echo "--------------------------------------"

# Update .gitignore to remove .claude and .claude-flow entries
if [ -f ".gitignore" ]; then
    echo "Updating .gitignore..."

    # Backup .gitignore
    cp .gitignore .gitignore.backup

    # Remove .claude and .claude-flow entries
    grep -v "^.claude$" .gitignore | grep -v "^.claude-flow$" > .gitignore.tmp
    mv .gitignore.tmp .gitignore

    # Add docs/archive to .gitignore if not already present
    if ! grep -q "^docs/archive" .gitignore; then
        echo "" >> .gitignore
        echo "# Archived scaffolding" >> .gitignore
        echo "docs/archive/scaffolding_archive_*.tar.gz" >> .gitignore
    fi

    echo -e "${GREEN}  .gitignore updated${NC}"
    echo -e "${YELLOW}  Backup saved as .gitignore.backup${NC}"
else
    echo -e "${YELLOW}  No .gitignore found${NC}"
fi

echo ""
echo -e "${GREEN}Step 6: Creating cleanup documentation${NC}"
echo "--------------------------------------"

# Create cleanup documentation
cat > docs/archive/CLEANUP_SUMMARY.md << EOF
# Scaffolding Cleanup Summary

**Date:** $(date +"%Y-%m-%d %H:%M:%S")
**Archive:** $ARCHIVE_NAME

## Directories Removed

- \`.claude/\` - Claude Code configuration and agents
- \`.claude-flow/\` - Claude Flow orchestration configuration

## Content Preserved

### Moved to docs/development/

- \`agents/\` - Agent specifications and configurations
- \`skills/\` - Skill definitions and documentation
- \`hooks/\` - Hook automation scripts
- \`swarms/\` - Swarm topology configurations
- \`workflows/\` - Workflow definitions
- \`memory/\` - Memory management configurations

### Archived

- Full backup: \`docs/archive/$ARCHIVE_NAME\`

## Restoration

To restore scaffolding directories:

\`\`\`bash
cd $PROJECT_ROOT
tar -xzf docs/archive/$ARCHIVE_NAME
\`\`\`

## Next Steps

1. Review docs/development/ for valuable documentation
2. Update README.md to reference new documentation location
3. Remove docs/archive/$ARCHIVE_NAME if backup no longer needed
4. Commit changes to version control

## Notes

- All configuration has been preserved in docs/
- Archive can be safely deleted after verification
- Update team documentation to reflect new structure
EOF

echo "Created: docs/archive/CLEANUP_SUMMARY.md"
echo -e "${GREEN}  Cleanup documentation created${NC}"

echo ""
echo -e "${GREEN}Step 7: Creating migration guide${NC}"
echo "--------------------------------------"

cat > docs/MIGRATION_FROM_SCAFFOLDING.md << EOF
# Migration from Development Scaffolding

This project has transitioned from development scaffolding to production structure.

## What Changed

### Removed Directories

- \`.claude/\` - Development-time Claude Code configuration
- \`.claude-flow/\` - Development-time orchestration configuration

### New Structure

All valuable content has been moved to \`docs/development/\`:

\`\`\`
docs/
├── development/
│   ├── agents/          # Agent specifications
│   ├── skills/          # Skill definitions
│   ├── hooks/           # Hook automation
│   ├── swarms/          # Swarm configurations
│   ├── workflows/       # Workflow definitions
│   └── memory/          # Memory patterns
└── archive/
    ├── CLEANUP_SUMMARY.md
    └── scaffolding_archive_*.tar.gz
\`\`\`

## Using Agents and Skills in Production

Agents and skills are now invoked through:

1. **Direct Python API**
   \`\`\`python
   from connascence_analyzer import QualityGate

   gate = QualityGate.from_config("quality_gate.config.yaml")
   results = gate.analyze_project(".")
   \`\`\`

2. **CLI Commands**
   \`\`\`bash
   python -m connascence_analyzer analyze --config quality_gate.config.yaml
   \`\`\`

3. **GitHub Actions** (Automated)
   - \`.github/workflows/self-analysis.yml\`
   - \`.github/workflows/create-violation-issues.yml\`

## Accessing Historical Information

If you need to access original scaffolding:

\`\`\`bash
tar -xzf docs/archive/scaffolding_archive_*.tar.gz
\`\`\`

## Updating Your Workflow

1. **Remove local .claude and .claude-flow directories** if synced
2. **Update documentation references** to point to docs/development/
3. **Use production CLI/API** instead of agent invocations
4. **Review GitHub Actions** for automated quality gates

## Questions?

See docs/archive/CLEANUP_SUMMARY.md for detailed cleanup information.
EOF

echo "Created: docs/MIGRATION_FROM_SCAFFOLDING.md"
echo -e "${GREEN}  Migration guide created${NC}"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Cleanup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Summary:"
echo "  - Scaffolding directories removed"
echo "  - Content preserved in docs/development/"
echo "  - Archive created: docs/archive/$ARCHIVE_NAME"
echo "  - Documentation updated"
echo ""
echo "Next steps:"
echo "  1. Review docs/development/ content"
echo "  2. Update README.md"
echo "  3. Commit changes"
echo "  4. Delete archive after verification (optional)"
echo ""
echo -e "${GREEN}Done!${NC}"
