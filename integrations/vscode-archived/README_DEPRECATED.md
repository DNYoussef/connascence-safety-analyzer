# ⚠️ DEPRECATED - Connascence VSCode Extension (Legacy)

**Status**: 🔴 **DEPRECATED** - Do not use for new development
**Archived Date**: 2025-10-07
**Reason**: Consolidated into `interfaces/vscode/`

---

## Migration Notice

This VSCode extension implementation has been **deprecated** and **archived**.

### ✅ Use Instead

**Primary Extension**: `interfaces/vscode/` (v2.0.2+)

The active, maintained extension is located at:
```
connascence/interfaces/vscode/
```

### Why Was This Deprecated?

1. **Duplicate Functionality**: Two separate VSCode extension implementations caused confusion
2. **Feature Disparity**: `interfaces/vscode/` has 40+ files vs this version's 9 files
3. **More Comprehensive**: Primary version includes:
   - Advanced pipeline provider
   - AI fix suggestions
   - Visual highlighting
   - Quality gate integration
   - File watcher service
   - Settings panel UI
   - And 10+ more features

### What Happened to This Code?

- **Archived Location**: `integrations/vscode-archived/`
- **Useful Components Migrated**:
  - ✅ Simpler MCP client pattern → Integrated into `interfaces/vscode/src/services/mcpClient.ts`
  - ✅ Basic analyzer wrapper pattern → Reviewed and incorporated where appropriate
  - ✅ Test patterns → Reviewed for test suite design

### Migration Path

If you were using this extension:

**For Users:**
1. Uninstall this extension
2. Install the primary extension from `interfaces/vscode/`
3. Configuration will be automatically migrated

**For Developers:**
1. Switch to `interfaces/vscode/` directory
2. Run `npm install`
3. Use the comprehensive API in `src/services/connascenceService.ts`

### Historical Context

This implementation served as:
- **Prototype**: Initial proof-of-concept for VSCode integration
- **Learning Tool**: Helped validate MCP communication patterns
- **Simplicity Reference**: Demonstrated minimal viable implementation

However, the production-grade implementation at `interfaces/vscode/` is:
- More feature-complete (15+ advanced features)
- Better tested (comprehensive test suite)
- Better documented (detailed API docs)
- Actively maintained (receives all new features)

---

## Archive Contents

This archived version contains:

### Source Files (9 files)
- `src/extension.ts` - Basic extension entry point
- `src/analyzer.ts` - Simple analyzer wrapper
- `src/mcpClient.ts` - WebSocket MCP client (✅ pattern migrated)
- `src/diagnostics.ts` - Basic diagnostics provider
- `src/codeActions.ts` - Simple code actions
- `src/treeViewProviders.ts` - Basic tree view
- `src/test/` - Basic test structure

### Key Differences vs Primary

| Feature | This (Archived) | interfaces/vscode (Primary) |
|---------|----------------|----------------------------|
| Files | 9 | 40+ |
| Features | Basic (5) | Comprehensive (15+) |
| MCP Integration | Simple | Production-grade |
| Configuration | 5 options | 40+ options |
| Testing | Basic | Comprehensive |
| Documentation | Minimal | Detailed |

---

## Historical Reference Only

**DO NOT:**
- ❌ Use this code for new development
- ❌ Submit PRs to this archived version
- ❌ File issues against this code
- ❌ Distribute or publish this extension

**YOU MAY:**
- ✅ Reference for learning purposes
- ✅ Review commit history
- ✅ Study architecture decisions
- ✅ Understand evolution of the project

---

## Support

For support, issues, or questions:

- **Primary Extension**: `interfaces/vscode/`
- **Documentation**: `interfaces/vscode/README.md`
- **Issues**: File against main project repository
- **Migration Help**: See `docs/EXTENSION_CONSOLIDATION_ANALYSIS.md`

---

## Archive Metadata

- **Original Version**: 2.0.0
- **Last Updated**: 2025-01-15
- **Deprecated**: 2025-10-07
- **Lines of Code**: ~1,200
- **Primary Author**: Connascence Systems Team
- **License**: MIT

---

**Thank you for your interest in the Connascence project!**

Please use the actively maintained extension at `interfaces/vscode/` for the best experience.
