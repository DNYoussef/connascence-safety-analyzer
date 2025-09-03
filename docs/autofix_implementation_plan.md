# Autofix Implementation Plan

## Priority 1: CLI God Object Refactoring

### Current Issue
```python
class ConnascenceCLI:  # 735 lines, 24 methods - CRITICAL CoA violation
    def __init__(self): ...
    def create_parser(self): ...
    def _handle_scan(self): ...
    def _handle_scan_diff(self): ...
    def _handle_explain(self): ...
    def _handle_autofix(self): ...
    def _handle_baseline(self): ...
    def _handle_mcp(self): ...
    def _handle_license(self): ...
    # ... 15 more methods
```

### Autofix Solution
```python
# cli/base.py
class ConnascenceCLI:
    """Minimal orchestration class."""
    def __init__(self):
        self.handlers = {
            'scan': ScanCommandHandler(),
            'scan-diff': ScanDiffCommandHandler(), 
            'explain': ExplainCommandHandler(),
            'autofix': AutofixCommandHandler(),
            'baseline': BaselineCommandHandler(),
            'mcp': MCPCommandHandler(),
            'license': LicenseCommandHandler(),
        }
    
    def run(self, args=None):
        # Minimal orchestration logic
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        return self.handlers[parsed_args.command].handle(parsed_args)

# cli/handlers/scan.py
class ScanCommandHandler:
    """Handle scan command logic."""
    def handle(self, args): ...

# cli/handlers/autofix.py  
class AutofixCommandHandler:
    """Handle autofix command logic."""
    def handle(self, args): ...
```

## Priority 2: Magic Literal Constants

### High-Impact Fixes

```python
# cli/constants.py
class ExitCodes:
    """Standard exit codes for CLI operations."""
    SUCCESS = 0
    CRITICAL_VIOLATIONS_FOUND = 1
    CONFIGURATION_ERROR = 2
    LICENSE_VALIDATION_FAILED = 4
    USER_INTERRUPTED = 130

class ReportFormatting:
    """Constants for report formatting."""
    SEPARATOR_CHAR = "="
    SEPARATOR_WIDTH = 80
    TOP_VIOLATIONS_LIMIT = 10
    INDENT = "  "
    SECTION_BREAK = "\n"

class MessageTemplates:
    """Standard message templates."""
    OPERATION_CANCELLED = "\nOperation cancelled by user"
    ANALYSIS_HEADER = "CONNASCENCE ANALYSIS REPORT"
    SCANNING_MESSAGE = "Scanning {path} with policy '{policy}'..."
    RESULTS_WRITTEN = "Results written to {output}"
```

### Implementation Example
```python
# Before
return 130
print("=" * 80)
print("\nOperation cancelled by user")

# After  
return ExitCodes.USER_INTERRUPTED
print(ReportFormatting.SEPARATOR_CHAR * ReportFormatting.SEPARATOR_WIDTH)
print(MessageTemplates.OPERATION_CANCELLED)
```

## Priority 3: Position Connascence Fixes

### Test File Improvements
```python
# Before (test_schedules.py - 1,510 violations)
assert_schedule(start, end, freq, pattern, expected)

# After - Use keyword arguments
assert_schedule(
    start_time=start,
    end_time=end, 
    frequency=freq,
    pattern=pattern,
    expected_result=expected
)

# Or use dataclass
@dataclass
class ScheduleTest:
    start_time: str
    end_time: str
    frequency: str
    pattern: str
    expected_result: Any

def test_schedule_generation():
    test_case = ScheduleTest(
        start_time="09:00",
        end_time="17:00", 
        frequency="daily",
        pattern="weekdays",
        expected_result=expected_schedule
    )
    assert_schedule(test_case)
```

## Implementation Script

```python
#!/usr/bin/env python3
"""
Automated refactoring script for critical connascence violations.
"""

import ast
import astor
from pathlib import Path

class ConnascenceAutoFixer:
    def __init__(self):
        self.fixes_applied = 0
        
    def fix_magic_literals(self, file_path: Path):
        """Replace magic literals with named constants."""
        with open(file_path, 'r') as f:
            source = f.read()
            
        tree = ast.parse(source)
        transformer = MagicLiteralTransformer()
        new_tree = transformer.visit(tree)
        
        if transformer.changes_made:
            new_source = astor.to_source(new_tree)
            with open(file_path, 'w') as f:
                f.write(new_source)
            self.fixes_applied += transformer.changes_made
    
    def split_god_class(self, file_path: Path, class_name: str):
        """Split a god class into smaller focused classes."""
        # Implementation for god class refactoring
        pass

class MagicLiteralTransformer(ast.NodeTransformer):
    def __init__(self):
        self.changes_made = 0
        
    def visit_Num(self, node):
        """Replace magic numbers with constants."""
        if node.n == 130:
            self.changes_made += 1
            return ast.Attribute(
                value=ast.Name(id='ExitCodes', ctx=ast.Load()),
                attr='USER_INTERRUPTED',
                ctx=ast.Load()
            )
        elif node.n == 80:
            self.changes_made += 1
            return ast.Attribute(
                value=ast.Name(id='ReportFormatting', ctx=ast.Load()),
                attr='SEPARATOR_WIDTH', 
                ctx=ast.Load()
            )
        return node

if __name__ == "__main__":
    fixer = ConnascenceAutoFixer()
    
    # Fix CLI magic literals
    fixer.fix_magic_literals(Path("cli/connascence.py"))
    
    print(f"Applied {fixer.fixes_applied} automatic fixes")
```

## Validation Plan

After implementing autofixes:

1. **Re-run Analysis**: Verify violation count decreases
2. **Run Tests**: Ensure functionality preserved
3. **Manual Review**: Check refactored code quality
4. **Performance Test**: Confirm no performance regression

## Expected Outcomes

- **CLI violations**: 362 → ~100 (70% reduction)
- **Analyzer violations**: 2,348 → ~800 (65% reduction) 
- **Overall violations**: 49,741 → ~20,000 (60% reduction)
- **God objects eliminated**: 10+ classes refactored
- **Magic literals reduced**: 36,883 → ~5,000 (85% reduction)

This autofix plan addresses the most critical violations identified in our self-analysis while maintaining code functionality and improving maintainability.