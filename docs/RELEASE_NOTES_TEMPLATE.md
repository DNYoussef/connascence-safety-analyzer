# Release Notes Template

## Version X.Y.Z - YYYY-MM-DD

### 🚀 New Features
- **Feature Name**: Brief description with concrete benefit
  - Example: `--nasa-validation` flag for Power of Ten compliance checking
  - Impact: Enables mission-critical software validation
  - Usage: `python -m analyzer.core --path . --nasa-validation`

### 🔧 Improvements  
- **Performance**: Specific measurement (e.g., "25% faster analysis on large codebases")
- **Accuracy**: Concrete improvement (e.g., "Reduced false positives by 12%")
- **Usability**: Clear benefit (e.g., "Clearer error messages with fix suggestions")

### 🐛 Bug Fixes
- **Issue #123**: Fixed incorrect magic number detection in list comprehensions
- **Issue #456**: Resolved crash when analyzing empty Python files  
- **Issue #789**: Corrected NASA compliance scoring algorithm

### 💔 Breaking Changes
- **API Change**: `--output-format` renamed to `--format` for consistency
  - **Migration**: Replace `--output-format json` with `--format json`
  - **Timeline**: Old flag deprecated in v2.1, removed in v3.0

### 📊 Performance Metrics
- **Analysis Speed**: X% faster than previous version
- **Memory Usage**: Reduced by Y% on average
- **Accuracy**: Z% precision on test suite of 74,237 violations

### 🔗 Integration Updates
- **VS Code Extension**: Compatible with version A.B.C+
- **CI/CD**: Updated GitHub Action to use this version
- **MCP Server**: Enhanced Claude Code integration

### 📖 Documentation
- Added [concrete examples](docs/examples/) with real analyzer output
- Updated [installation guide](docs/examples/INSTALLATION.md) for one-command setup
- Created [before/after comparison](docs/examples/README.md) demos

### 🧪 Testing
- **Test Coverage**: X% (target: 95%+)
- **Validation**: Tested on Y popular open-source projects  
- **Regression**: All Z existing test cases pass

### 💡 Migration Guide

#### From v2.0 to v2.1
1. Update installation: `pip install -U connascence-analyzer`
2. Update CLI usage:
   ```bash
   # Old
   python -m analyzer.core --output-format json
   
   # New  
   python -m analyzer.core --format json
   ```
3. Review new NASA compliance features in output

#### Configuration Updates
```yaml
# .connascence.yaml - New options
analysis:
  policy: nasa_jpl_pot10  # New policy option
  confidence_threshold: 0.85  # New setting
  
output:
  include_recommendations: true  # New feature
```

### 🙏 Contributors
- @username1 - Feature implementation and testing
- @username2 - Documentation improvements  
- @username3 - Bug fixes and performance optimization

### 📈 Usage Statistics (Optional)
- **Downloads**: X this month (+Y% from last month)
- **Active Repositories**: Z codebases using the analyzer
- **Violations Detected**: W new violations found in production

### 🔄 Next Release Preview
Planned for v(X+1).Y.Z in [timeframe]:
- Multi-language analysis expansion
- Real-time VS Code integration
- Enhanced SARIF output format
- Performance improvements for enterprise scale

---

## Example Release Notes (v2.1.0)

### Version 2.1.0 - 2024-12-06

### 🚀 New Features
- **NASA Power of Ten Compliance**: Added `--nasa-validation` flag for mission-critical software
  - Validates against all 10 NASA JPL coding standards
  - Generates compliance score (target: 95%+)  
  - Usage: `python -m analyzer.core --path . --nasa-validation`

- **Concrete Examples**: Added [docs/examples/](docs/examples/) with real code and analyzer output
  - 30-line Python file showing 12 common violations
  - Before/after refactoring comparison  
  - Real JSON and text output samples

### 🔧 Improvements
- **Performance**: 35% faster analysis on files >1000 lines
- **Accuracy**: Reduced false positives from 2.3% to 1.1%
- **Usability**: Error messages now include specific fix recommendations

### 🐛 Bug Fixes  
- **Issue #234**: Fixed crash when analyzing files with Unicode comments
- **Issue #567**: Corrected magic number detection in f-strings
- **Issue #890**: Resolved incorrect god object scoring for inheritance

### 📊 Performance Metrics
- **Analysis Speed**: 35% faster than v2.0  
- **Memory Usage**: Reduced by 18% on large codebases
- **Accuracy**: 98.9% precision on 74,237-violation test suite

### 🔗 Integration Updates
- **VS Code Extension**: Full compatibility with v1.2.0+
- **GitHub Actions**: Updated workflow templates
- **MCP Server**: Enhanced Claude Code suggestions

### 💡 Try It Now
```bash
# One-command demo
python -m analyzer.core --path docs/examples/bad_example.py --policy nasa_jpl_pot10

# Expected output: 12 violations, 42% NASA compliance score
```

### 📖 Documentation
- [Installation Guide](docs/examples/INSTALLATION.md): True one-command setup
- [Concrete Examples](docs/examples/README.md): Real code with actual output  
- [Before/After Comparison](docs/examples/): See violations and fixes side-by-side