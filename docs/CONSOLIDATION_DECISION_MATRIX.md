# File Consolidation Decision Matrix

## Decision Criteria

**KEEP** - Unique content, latest version, or master file
**MERGE** - Contains unique insights to be consolidated  
**DELETE** - Duplicate or superseded content

## Large JSON Analysis Files (34MB+ files)

| File | Size | Decision | Rationale |
|------|------|----------|-----------|
| FULL_CODEBASE_ANALYSIS.json | 34MB | **KEEP** | Master comprehensive analysis, latest timestamp |
| final_validation_nasa.json | 34MB | **KEEP** | Unique NASA compliance validation |
| final_validation_full.json | 34MB | **DELETE** | Near-duplicate of FULL_CODEBASE_ANALYSIS.json |
| reports/final_test_report.json | 34MB | **DELETE** | Duplicate validation data |

## Medium JSON Analysis Files (15-30MB)

| File | Size | Decision | Rationale |
|------|------|----------|-----------|
| reports/final_nasa_test.json | 30MB | **DELETE** | Superseded by final_validation_nasa.json |
| reports/validation_analysis_report.json | 17MB | **DELETE** | Content covered in master analysis |
| reports/consolidated_analysis_report.json | 17MB | **DELETE** | Redundant consolidation |
| reports/nasa_compliance_report.json | 16MB | **DELETE** | Superseded by final_validation_nasa.json |
| reports/connascence_analysis_report.json | 16MB | **DELETE** | Duplicate analysis content |
| reports/complete_analysis_report.json | 16MB | **DELETE** | Duplicate analysis content |

## Folder-Specific Analysis Files

| File | Size | Decision | Rationale |
|------|------|----------|-----------|
| analysis_results_analyzer.json | 1.1MB | **MERGE** | Analyzer-specific insights to preserve |
| analysis_results_integrations.json | 855KB | **MERGE** | Integration analysis insights |
| analysis_results_policy.json | 321KB | **MERGE** | Policy compliance insights |
| analysis_results_mcp.json | 307KB | **MERGE** | MCP-specific analysis |
| analysis_results_security.json | 277KB | **MERGE** | Security analysis insights |
| analysis_results_cli.json | 110KB | **MERGE** | CLI analysis insights |
| analysis_results_config.json | 48KB | **MERGE** | Configuration analysis |
| analysis_results_utils.json | 36KB | **MERGE** | Utils analysis insights |
| analysis_results_tests.json | 2.7KB | **DELETE** | Minimal content |
| analysis_results_experimental.json | 433B | **DELETE** | Minimal experimental data |

## Validation Documentation Duplicates

| File | Size | Decision | Rationale |
|------|------|----------|-----------|
| docs/vscode-extension-validation-report.md | 8.5KB | **KEEP** | Primary location in docs |
| enterprise-package/technical/architecture/vscode-extension-validation-report.md | 8.5KB | **DELETE** | Exact duplicate |
| docs/reports/validation/DOGFOODING_VALIDATION_REPORT.md | 7.9KB | **KEEP** | Primary reports location |
| analysis/self-analysis/DOGFOODING_VALIDATION_REPORT.md | 7.9KB | **DELETE** | Exact duplicate |
| docs/analysis/SINGLE_COMMAND_VERIFICATION.md | 8.1KB | **KEEP** | Primary version |
| enterprise-package/validation/SINGLE_COMMAND_VERIFICATION.md | 7.2KB | **MERGE** | Different content, extract insights |

## Architectural Documentation

| File | Size | Decision | Rationale |
|------|------|----------|-----------|
| docs/integration-analysis/implementation-roadmap.md | 31KB | **KEEP** | Comprehensive roadmap |
| docs/integration-analysis/architecture-diagram.md | 20KB | **KEEP** | Architecture documentation |
| docs/integration-analysis/gap-analysis-report.md | 18KB | **KEEP** | Gap analysis insights |
| analysis/CROSS_FOLDER_DEPENDENCY_MAPPING_REPORT.md | 12KB | **MERGE** | Dependency insights |
| docs/integration-analysis/mece-integration-matrix.md | 11KB | **KEEP** | MECE analysis matrix |
| analysis/architectural_analysis_comprehensive.md | 10KB | **MERGE** | Architectural insights |
| docs/integration-analysis/README.md | 9.5KB | **KEEP** | Integration documentation |

## Summary and Executive Reports

| File | Size | Decision | Rationale |
|------|------|----------|-----------|
| reports/FINAL_COMPREHENSIVE_SUMMARY.md | 7.5KB | **KEEP** | Primary comprehensive summary |
| reports/COMPREHENSIVE_ANALYSIS_SUMMARY.md | 6.4KB | **KEEP** | Technical analysis summary |
| reports/EXECUTIVE_DUPLICATION_SUMMARY.md | 6.0KB | **DELETE** | Redundant executive summary |
| reports/COMPREHENSIVE_SENSOR_ANALYSIS_AIVILLAGE.md | 6.0KB | **DELETE** | Specific analysis, not general |
| reports/FINAL_ACTIONABLE_ANALYSIS.md | 4.8KB | **KEEP** | Action items summary |
| reports/ANALYSIS_COMMANDS_AND_FILES.md | 4.3KB | **DELETE** | Outdated command reference |

## Small Test and Utility Files

| File | Size | Decision | Rationale |
|------|------|----------|-----------|
| reports/aivillage_duplication_summary.json | 7.8KB | **KEEP** | Specific analysis results |
| reports/enhanced_aivillage_analysis.json | 90KB | **KEEP** | Enhanced analysis insights |
| reports/fixed_aivillage_mcp_analysis.json | 765KB | **KEEP** | Fixed analysis version |
| reports/warning_test_analysis.json | 248KB | **KEEP** | Warning analysis results |
| reports/mece_duplication_report.json | 4.4KB | **DELETE** | Duplicate of other MECE analysis |
| reports/final_consolidation_mece_report.json | 4.4KB | **DELETE** | Redundant MECE analysis |
| reports/post_consolidation_mece_report.json | 13KB | **DELETE** | Redundant MECE analysis |
| reports/final_mece_test.json | 13KB | **DELETE** | Test file, not production |
| reports/single_file_test.json | 627B | **DELETE** | Test file |
| reports/fixed_single_file_test.json | 3.7KB | **DELETE** | Test file |
| reports/full_analysis_report.json | 683B | **DELETE** | Minimal content |

## Temporary and Backup Files

| File/Directory | Decision | Rationale |
|----------------|----------|-----------|
| temp-artifacts/ | **DELETE** | Temporary verification files |
| vscode-extension-backup-20250905-142126/ | **DELETE** | Backup directory |
| test_activation.py (root) | **DELETE** | Should be in tests/ directory |

## Critical Files to Preserve

| File | Purpose | Status |
|------|---------|--------|
| FULL_CODEBASE_ANALYSIS.json | Master analysis | PROTECTED |
| final_validation_nasa.json | NASA compliance | PROTECTED |
| docs/CRITICAL_VIOLATIONS_ACTION_PLAN.json | Action plan | PROTECTED |
| docs/VIOLATION_HEATMAPS.json | Violation analysis | PROTECTED |
| docs/integration-analysis/* | Integration roadmap | PROTECTED |
| enterprise-package/validation/ACCURACY_REPORT.md | Enterprise validation | PROTECTED |

## Merge Operations Required

### 1. Folder Analysis Consolidation
Create `docs/CONSOLIDATED_FOLDER_ANALYSIS.md` from:
- analysis_results_analyzer.json (key insights)
- analysis_results_integrations.json (integration issues)  
- analysis_results_policy.json (policy violations)
- analysis_results_mcp.json (MCP analysis)
- analysis_results_security.json (security findings)
- analysis_results_cli.json (CLI issues)
- analysis_results_config.json (config problems)
- analysis_results_utils.json (utility issues)

### 2. Architectural Analysis Consolidation  
Merge into `docs/integration-analysis/`:
- analysis/architectural_analysis_comprehensive.md
- analysis/CROSS_FOLDER_DEPENDENCY_MAPPING_REPORT.md

### 3. Single Command Verification Merge
Combine unique content from:
- docs/analysis/SINGLE_COMMAND_VERIFICATION.md (primary)
- enterprise-package/validation/SINGLE_COMMAND_VERIFICATION.md (extract unique insights)

## Execution Priority

1. **HIGH**: Remove large duplicate JSON files (160MB+ savings)
2. **HIGH**: Remove backup and temporary directories  
3. **MEDIUM**: Process merge operations for unique content
4. **MEDIUM**: Clean up redundant summary reports
5. **LOW**: Final organization and validation

## Risk Assessment

### Low Risk:
- Large JSON duplicates (content preserved in master files)
- Exact document duplicates (identical checksums)
- Temporary/backup files

### Medium Risk:  
- Folder-specific analyses (merge required to preserve insights)
- Architectural documentation overlaps

### High Risk:
- None identified - all critical content preserved

## Success Metrics

- **Storage reduction**: 150MB+ (75% reduction in analysis files)
- **File count reduction**: 45+ files (60% reduction in analysis files)  
- **Organization improvement**: Clean docs/ structure
- **Content preservation**: 100% of unique insights maintained