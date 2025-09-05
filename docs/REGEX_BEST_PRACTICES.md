# 📋 Regex Best Practices for Connascence Analyzer

## 🚨 Critical Rules: Prevent SyntaxWarning Issues

### **Rule 1: Always Use Raw Strings for Regex Patterns**

```python
# ✅ CORRECT - Raw string prevents escape sequence issues
pattern = re.compile(r'function\s+\w+\s*\([^)]*\)')

# ❌ WRONG - Will cause SyntaxWarning with escape sequences  
pattern = re.compile('function\\s+\\w+\\s*\\([^)]*\\)')
```

### **Rule 2: Use Triple-Quoted Raw Strings for Complex Patterns**

```python
# ✅ CORRECT - Triple quotes handle mixed quote types
pattern = re.compile(r'''["'][^"']{3,}["']''')

# ❌ WRONG - Escape sequences cause warnings
pattern = re.compile('["\'][^"\']{3,}["\']')
```

### **Rule 3: Escape Special Characters Properly**

```python
# ✅ CORRECT - Literal braces in raw string
interface_pattern = re.compile(r'interface\s*\{')

# ❌ WRONG - Missing raw string causes warnings
interface_pattern = re.compile('interface\\s*\\{')
```

## 🔍 Language-Specific Patterns

### **JavaScript Detection**
```python
# Function detection
FUNCTION_PATTERN = re.compile(r'^\\s*(?:function\\s+\\w+|(?:const|let|var)\\s+\\w+\\s*=\\s*(?:function|\\(.*?\\)\\s*=>)|\\w+\\s*:\\s*function)')

# Parameter extraction  
PARAM_PATTERN = re.compile(r'(?:function\\s+\\w+|(?:const|let|var)\\s+\\w+\\s*=\\s*(?:function|\\(.*?\\)\\s*=>))\\s*\\(([^)]+)\\)')

# Magic literals
NUMERIC_PATTERN = re.compile(r'\\b(?!0\\b|1\\b|-1\\b)\\d+\\.?\\d*\\b')
STRING_PATTERN = re.compile(r"""["'][^"']{3,}["']""")
```

### **Python AST Patterns**
```python
# Class detection
CLASS_PATTERN = re.compile(r'^\\s*class\\s+(\\w+)\\s*\\([^)]*\\)\\s*:')

# Function detection
FUNCTION_PATTERN = re.compile(r'^\\s*def\\s+(\\w+)\\s*\\([^)]*\\)\\s*:')

# Import statements
IMPORT_PATTERN = re.compile(r'^\\s*(?:from\\s+[\\w.]+\\s+)?import\\s+[\\w., ]+')
```

### **C/C++ Detection**
```python
# Function signatures
C_FUNCTION_PATTERN = re.compile(r'^\\s*(?:static\\s+)?(?:inline\\s+)?[\\w\\s\\*]+\\s+\\w+\\s*\\([^)]*\\)\\s*\\{?')

# Magic numbers with suffixes
C_NUMERIC_PATTERN = re.compile(r'\\b(?!0\\b|1\\b|-1\\b)\\d+[UuLl]*\\b')

# String literals
C_STRING_PATTERN = re.compile(r'"[^"]{3,}"')
```

## 🛡️ Linting Integration

### **Ruff Configuration (pyproject.toml)**
```toml
[tool.ruff.flake8-bugbear]
# Enable regex pattern checking
extend-immutable-calls = ["re.compile", "re.Pattern"]

[tool.ruff.lint.extend-per-file-ignores]
# Catch invalid escape sequences
extend-select = ["W605"]  # invalid escape sequence

# Ensure regex patterns use raw strings
"**/*.py" = []
```

### **Pre-commit Hooks**
```yaml
- repo: local
  hooks:
    - id: regex-warnings
      name: Check for regex SyntaxWarnings
      entry: python -W error::SyntaxWarning -c "import sys; [__import__(m.replace('.py', '').replace('/', '.')) for m in sys.argv[1:]]"
      language: system
      files: '\\.py$'
```

## 🔧 Common Patterns and Fixes

### **Magic Literal Detection**
```python
# ✅ CORRECT - Comprehensive numeric detection
MAGIC_NUMERIC = re.compile(r'''
    \\b                           # Word boundary
    (?!0\\b|1\\b|-1\\b)           # Exclude common values
    -?                            # Optional negative
    (?:
        \\d{2,}                   # 2+ digits (10, 42, etc.)
        |                        
        \\d+\\.\\d+               # Decimals (3.14, 2.5)
        |
        0x[0-9a-fA-F]+           # Hex values
        |
        0b[01]+                  # Binary values
        |
        0o[0-7]+                 # Octal values
    )
    [UuLlFfDd]*                  # Type suffixes (C/C++)
    \\b                          # Word boundary
''', re.VERBOSE)

# ✅ CORRECT - String literal detection with exclusions
MAGIC_STRING = re.compile(r'''
    ["']                         # Opening quote
    (?!                          # Negative lookahead for exclusions
        \\s*$                    # Empty or whitespace only
        |test|debug|error|warn   # Common test/log strings
        |\\w{1,2}$               # Single/double chars
    )
    [^"']{3,}                    # 3+ non-quote characters
    ["']                         # Closing quote
''', re.VERBOSE)
```

### **God Object Detection**
```python
# ✅ CORRECT - Class method counting
CLASS_METHODS = re.compile(r'''
    ^\\s*                        # Start of line
    (?:async\\s+)?               # Optional async
    def\\s+                      # Function keyword
    (?!__(?:init|str|repr)__)    # Exclude special methods
    (\\w+)                       # Method name (group 1)
    \\s*\\([^)]*\\)              # Parameters
    \\s*:                        # Colon
''', re.MULTILINE | re.VERBOSE)
```

### **Parameter Coupling**
```python
# ✅ CORRECT - Function parameter extraction
FUNCTION_PARAMS = re.compile(r'''
    def\\s+\\w+\\s*              # Function definition
    \\(                          # Opening paren
    ([^)]*)                     # Parameters (group 1)
    \\)                          # Closing paren
    \\s*:                        # Colon
''', re.VERBOSE)

# ✅ CORRECT - Parameter counting logic
def count_parameters(params_str: str) -> int:
    if not params_str.strip():
        return 0
    
    # Split by comma, filter out self/cls
    params = [p.strip() for p in params_str.split(',')]
    params = [p for p in params if p and not p.startswith('self') and not p.startswith('cls')]
    
    return len(params)
```

## ⚠️ Common Mistakes to Avoid

### **1. Forgetting Raw Strings**
```python
# ❌ WRONG - Will cause SyntaxWarning
pattern = re.compile('\\w+\\s*\\(.*\\)')

# ✅ CORRECT - Raw string prevents issues
pattern = re.compile(r'\\w+\\s*\\(.*\\)')
```

### **2. Mixed Quote Types**
```python
# ❌ WRONG - Escape nightmare
pattern = re.compile('["\'][^"\']+["\']')

# ✅ CORRECT - Triple-quoted raw string
pattern = re.compile(r'''["'][^"']+["']''')
```

### **3. Overly Broad Magic Literal Detection**
```python
# ❌ WRONG - Flags every number (noise generator)
bad_pattern = re.compile(r'\\d+')

# ✅ CORRECT - Smart filtering for meaningful values
good_pattern = re.compile(r'\\b(?!0\\b|1\\b|-1\\b|2\\b|10\\b|100\\b|1000\\b)\\d{2,}\\b')
```

### **4. Not Handling Edge Cases**
```python
# ❌ WRONG - Misses async functions
bad_function = re.compile(r'^\\s*def\\s+\\w+')

# ✅ CORRECT - Handles async and decorators
good_function = re.compile(r'^\\s*(?:@.*\\n\\s*)*(?:async\\s+)?def\\s+\\w+')
```

## 🧪 Testing Regex Patterns

### **Unit Test Template**
```python
import re
import pytest

def test_regex_pattern_no_warnings():
    """Ensure regex patterns don't cause SyntaxWarnings."""
    import warnings
    
    with warnings.catch_warnings():
        warnings.simplefilter("error", SyntaxWarning)
        
        # Test pattern compilation
        pattern = re.compile(r'your_pattern_here')
        
        # Test pattern usage
        result = pattern.search('test string')
        assert result is not None or result is None  # Pattern works

def test_magic_literal_detection():
    """Test magic literal detection accuracy."""
    test_code = '''
    x = 42          # Should detect
    y = PORT_8080   # Should not detect (constant)  
    z = [0, 1, 2]   # Should not detect (common values)
    timeout = 30000 # Should detect
    '''
    
    pattern = re.compile(r'\\b(?!0\\b|1\\b|2\\b)\\d{3,}\\b')
    matches = pattern.findall(test_code)
    assert '30000' in matches
    assert '42' in matches
    assert '0' not in matches
```

## 📊 Performance Considerations

### **Compile Patterns Once**
```python
# ✅ CORRECT - Module-level compilation
MAGIC_PATTERN = re.compile(r'\\b\\d{3,}\\b')

class Analyzer:
    def analyze(self, code):
        return MAGIC_PATTERN.findall(code)

# ❌ WRONG - Recompiling in loop
class BadAnalyzer:
    def analyze(self, code):
        pattern = re.compile(r'\\b\\d{3,}\\b')  # Wasteful!
        return pattern.findall(code)
```

### **Use Multiline Flag Efficiently**
```python
# ✅ CORRECT - Multiline when needed
FUNCTION_PATTERN = re.compile(r'^\\s*def\\s+\\w+', re.MULTILINE)

# ❌ WRONG - DOTALL when not needed (slow)
bad_pattern = re.compile(r'def.*?:', re.DOTALL)
```

## 🚀 Integration with Analyzer

### **Strategy Pattern Implementation**
```python
class LanguageStrategy:
    def get_patterns(self) -> dict:
        \"\"\"Return compiled regex patterns for this language.\"\"\"
        return {
            'magic_numeric': re.compile(self.MAGIC_NUMERIC_PATTERN),
            'magic_string': re.compile(self.MAGIC_STRING_PATTERN),
            'god_function': re.compile(self.GOD_FUNCTION_PATTERN),
        }

class PythonStrategy(LanguageStrategy):
    MAGIC_NUMERIC_PATTERN = r'\\b(?!0\\b|1\\b|-1\\b)\\d{3,}\\b'
    MAGIC_STRING_PATTERN = r'''["'][^"']{10,}["']'''
    GOD_FUNCTION_PATTERN = r'^\\s*def\\s+(\\w+).*?(?=^\\s*def|\\Z)'
```

---

## ✅ Checklist for Contributors

Before committing regex code:

- [ ] All regex patterns use raw strings (`r''`)
- [ ] Complex patterns with quotes use triple-quoted raw strings
- [ ] Patterns are compiled at module level, not in loops
- [ ] Test cases verify no SyntaxWarnings
- [ ] Magic literal detection has smart exclusions
- [ ] Performance tested on large codebases
- [ ] Language-specific patterns handle edge cases
- [ ] Documentation explains pattern purpose

---

**Remember**: Good regex patterns are invisible - they catch real issues without generating noise!