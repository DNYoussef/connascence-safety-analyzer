# ReportGenerator - Quick Reference

**Location**: `analyzer/architecture/report_generator.py`
**LOC**: 441 lines
**Status**: Production Ready

---

## Import

```python
from analyzer.architecture.report_generator import ReportGenerator
```

---

## Quick Start

```python
# Initialize
generator = ReportGenerator({"version": "1.0.0"})

# Generate JSON
json_str = generator.generate_json(result, Path("output.json"))

# Generate Markdown
md_str = generator.generate_markdown(result, Path("summary.md"))

# Generate SARIF
sarif_dict = generator.generate_sarif(violations, Path("results.sarif"))

# Generate ALL formats
paths = generator.generate_all_formats(result, violations, output_dir)
```

---

## Configuration

```python
config = {
    "version": "1.0.0",              # Analyzer version
    "max_violations_to_show": 10,    # Markdown violation limit
    "max_files_to_show": 5,          # Markdown file limit
    "indent": 2,                     # JSON indentation
    "sort_keys": True                # Sort JSON keys
}
generator = ReportGenerator(config)
```

---

## Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `generate_json(result, path?)` | JSON report | str |
| `generate_markdown(result, path?)` | Markdown summary | str |
| `generate_sarif(violations, path?, source_root?)` | SARIF 2.1.0 | dict |
| `format_summary(metrics)` | Text summary | str |
| `generate_all_formats(result, violations, dir, name?)` | All formats | dict |

---

## Output Formats

### JSON (Machine-Readable)
- Deterministic ordering
- Comprehensive metadata
- Policy compliance info
- File statistics

### Markdown (Human-Readable)
- PR comment friendly
- Emoji indicators
- Top violations
- Actionable recommendations

### SARIF (CI/CD Integration)
- GitHub Code Scanning
- VS Code integration
- Azure DevOps compatible
- GitLab support

---

## Examples

### Example 1: Single Format
```python
generator = ReportGenerator()
json_report = generator.generate_json(analysis_result)
print(json_report)
```

### Example 2: Write to File
```python
generator = ReportGenerator()
generator.generate_markdown(result, Path("summary.md"))
```

### Example 3: All Formats
```python
generator = ReportGenerator()
paths = generator.generate_all_formats(
    result=analysis_result,
    violations=violations,
    output_dir=Path("reports"),
    base_name="analysis"
)
# Returns: {"json": Path(...), "markdown": Path(...), "sarif": Path(...)}
```

### Example 4: Text Summary
```python
generator = ReportGenerator()
summary = generator.format_summary({
    "total_violations": 42,
    "critical_count": 3,
    "overall_quality_score": 0.85
})
print(summary)
```

---

## Integration

### With UnifiedConnascenceAnalyzer

```python
class UnifiedConnascenceAnalyzer:
    def __init__(self):
        self.report_generator = ReportGenerator({
            "version": self.version
        })

    def export_reports(self, result, violations, output_dir):
        return self.report_generator.generate_all_formats(
            result, violations, output_dir
        )
```

---

## Error Handling

All methods include comprehensive error handling:

```python
try:
    generator.generate_json(result, Path("output.json"))
except IOError as e:
    print(f"File write failed: {e}")
except TypeError as e:
    print(f"Serialization failed: {e}")
```

---

## Files

| File | Size | Purpose |
|------|------|---------|
| `analyzer/architecture/report_generator.py` | 16KB | Main class |
| `docs/REPORT_GENERATOR_EXTRACTION.md` | 15KB | Full documentation |
| `docs/EXTRACTION_SUMMARY.md` | 8.8KB | Executive summary |
| `examples/report_generator_usage.py` | 5.5KB | Usage examples |

---

## Testing

### Syntax Check
```bash
python -m py_compile analyzer/architecture/report_generator.py
```

### Run Examples
```bash
python examples/report_generator_usage.py
```

---

## NASA Compliance

- ✅ All functions < 60 lines
- ✅ No recursion
- ✅ Clear error handling
- ✅ Minimal nesting
- ✅ Explicit assertions

---

**Last Updated**: 2025-11-13
**Version**: 1.0.0
