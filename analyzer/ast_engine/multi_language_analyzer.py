"""
Multi-Language Connascence Analyzer
Integrates Tree Sitter backend for C, JavaScript, and other language support
"""

import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from ..thresholds import ConnascenceType, Severity
from .base_analyzer import BaseConnascenceAnalyzer
from .violations import Violation

logger = logging.getLogger(__name__)

# Language file extensions mapping
LANGUAGE_EXTENSIONS = {
    'python': ['.py'],
    'c': ['.c', '.h'],
    'cpp': ['.cpp', '.cxx', '.cc', '.hpp', '.hxx'],
    'javascript': ['.js', '.mjs'],
    'typescript': ['.ts'],
    'json': ['.json']
}

EXTENSION_TO_LANGUAGE = {}
for lang, exts in LANGUAGE_EXTENSIONS.items():
    for ext in exts:
        EXTENSION_TO_LANGUAGE[ext] = lang


@dataclass
class ParseResult:
    """Result of parsing source code with Tree Sitter or AST."""
    language: str
    tree: Any
    source_lines: List[str]
    success: bool
    error_message: Optional[str] = None


class MultiLanguageAnalyzer(BaseConnascenceAnalyzer):
    """Multi-language connascence analyzer using Tree Sitter for non-Python languages."""
    
    def __init__(self, thresholds=None, weights=None, policy_preset=None, exclusions=None):
        super().__init__(thresholds, weights, policy_preset, exclusions)
        self.tree_sitter_available = self._init_tree_sitter()
        
    def _init_tree_sitter(self) -> bool:
        """Initialize Tree Sitter backend if available."""
        try:
            from ...grammar.backends.tree_sitter_backend import TreeSitterBackend
            self.tree_sitter = TreeSitterBackend()
            return True
        except ImportError:
            logger.warning("Tree Sitter backend not available, falling back to text-based analysis")
            self.tree_sitter = None
            return False
    
    def detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        suffix = file_path.suffix.lower()
        return EXTENSION_TO_LANGUAGE.get(suffix, 'unknown')
    
    def parse_file(self, file_path: Path) -> ParseResult:
        """Parse file using appropriate parser for the language."""
        language = self.detect_language(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            source_lines = source.splitlines()
            
            # Python uses AST
            if language == 'python':
                try:
                    tree = ast.parse(source, filename=str(file_path))
                    return ParseResult(language, tree, source_lines, True)
                except SyntaxError as e:
                    return ParseResult(language, None, source_lines, False, str(e))
            
            # Other languages use Tree Sitter if available
            elif self.tree_sitter_available and language in ['c', 'cpp', 'javascript']:
                try:
                    tree = self.tree_sitter.parse(source, language)
                    return ParseResult(language, tree, source_lines, True)
                except Exception as e:
                    logger.warning(f"Tree Sitter parsing failed for {language}: {e}")
                    # Fall back to text-based analysis
                    return ParseResult(language, None, source_lines, True)
            
            # Fallback: text-based analysis
            else:
                return ParseResult(language, None, source_lines, True)
                
        except Exception as e:
            return ParseResult('unknown', None, [], False, str(e))
    
    def analyze_file(self, file_path: Path) -> List[Violation]:
        """Analyze file with appropriate language-specific analysis."""
        if not self.should_analyze_file(file_path):
            return []
            
        self.current_file_path = str(file_path)
        parse_result = self.parse_file(file_path)
        
        if not parse_result.success:
            return [Violation(
                id="",
                type=ConnascenceType.NAME,
                severity=Severity.CRITICAL,
                file_path=self.current_file_path,
                line_number=1,
                column=0,
                description=f"Failed to parse {parse_result.language} file: {parse_result.error_message}",
                recommendation="Fix syntax errors before analyzing connascence"
            )]
        
        self.current_source_lines = parse_result.source_lines
        violations = []
        
        # Language-specific analysis
        if parse_result.language == 'python' and parse_result.tree:
            # Use existing Python AST analysis
            violations.extend(self._analyze_python_ast(parse_result.tree))
        
        elif parse_result.language == 'c' or parse_result.language == 'cpp':
            violations.extend(self._analyze_c_cpp(parse_result))
            
        elif parse_result.language == 'javascript':
            violations.extend(self._analyze_javascript(parse_result))
            
        else:
            # Text-based analysis for unknown languages
            violations.extend(self._analyze_text_based(parse_result))
        
        return violations
    
    def _analyze_python_ast(self, tree: ast.AST) -> List[Violation]:
        """Analyze Python code using AST (delegates to existing analyzers)."""
        # This would delegate to the existing Python analyzer components
        violations = []
        
        # Position analysis
        violations.extend(self._analyze_python_position(tree))
        
        # Magic literals
        violations.extend(self._analyze_python_magic_literals(tree))
        
        return violations
    
    def _analyze_c_cpp(self, parse_result: ParseResult) -> List[Violation]:
        """Analyze C/C++ code for connascence violations."""
        violations = []
        
        # C-specific connascence patterns
        violations.extend(self._analyze_c_function_signatures(parse_result))
        violations.extend(self._analyze_c_magic_numbers(parse_result))
        violations.extend(self._analyze_c_includes(parse_result))
        
        return violations
    
    def _analyze_javascript(self, parse_result: ParseResult) -> List[Violation]:
        """Analyze JavaScript code for connascence violations."""
        violations = []
        
        # JavaScript-specific patterns
        violations.extend(self._analyze_js_function_signatures(parse_result))
        violations.extend(self._analyze_js_magic_literals(parse_result))
        violations.extend(self._analyze_js_callback_patterns(parse_result))
        
        return violations
    
    def _analyze_text_based(self, parse_result: ParseResult) -> List[Violation]:
        """Text-based analysis for languages without specific parsers."""
        violations = []
        
        # Generic text analysis
        violations.extend(self._analyze_generic_magic_numbers(parse_result))
        violations.extend(self._analyze_generic_long_lines(parse_result))
        
        return violations
    
    def _analyze_c_function_signatures(self, parse_result: ParseResult) -> List[Violation]:
        """Analyze C function signatures for positional parameter violations."""
        violations = []
        
        for i, line in enumerate(parse_result.source_lines, 1):
            line = line.strip()
            
            # Simple pattern matching for C function declarations
            if ('(' in line and ')' in line and 
                any(keyword in line for keyword in ['int ', 'void ', 'char ', 'float ', 'double '])):
                
                # Count commas in function signature (rough approximation)
                paren_content = line[line.find('('):line.rfind(')')+1]
                param_count = paren_content.count(',') + 1 if paren_content != '()' else 0
                
                if param_count > self.thresholds.max_positional_params:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.POSITION,
                        severity=Severity.HIGH,
                        file_path=self.current_file_path,
                        line_number=i,
                        column=0,
                        description=f"C function has {param_count} parameters (>{self.thresholds.max_positional_params})",
                        recommendation="REFACTOR: Break down function or use struct parameters. Pattern: struct config_params instead of individual parameters",
                        locality="same_function",
                        context={"parameter_count": param_count, "language": "c"}
                    ))
        
        return violations
    
    def _analyze_c_magic_numbers(self, parse_result: ParseResult) -> List[Violation]:
        """Analyze C code for magic number violations."""
        violations = []
        
        for i, line in enumerate(parse_result.source_lines, 1):
            # Look for numeric literals (excluding 0, 1, -1)
            import re
            numbers = re.findall(r'\b(\d{2,})\b', line)
            
            for number in numbers:
                if int(number) not in [0, 1]:  # Common acceptable numbers
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.MEANING,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=i,
                        column=line.find(number),
                        description=f"Magic number '{number}' should be a named constant",
                        recommendation="REFACTOR: Define as #define constant. Pattern: #define MAX_SIZE 1024",
                        locality="same_module",
                        context={"magic_value": number, "language": "c"}
                    ))
        
        return violations
    
    def _analyze_c_includes(self, parse_result: ParseResult) -> List[Violation]:
        """Analyze C include dependencies for coupling violations."""
        violations = []
        include_count = 0
        
        for i, line in enumerate(parse_result.source_lines, 1):
            if line.strip().startswith('#include'):
                include_count += 1
        
        if include_count > 15:  # Threshold for excessive includes
            violations.append(Violation(
                id="",
                type=ConnascenceType.NAME,
                severity=Severity.MEDIUM,
                file_path=self.current_file_path,
                line_number=1,
                column=0,
                description=f"Excessive includes ({include_count}) may indicate tight coupling",
                recommendation="REFACTOR: Reduce dependencies, use forward declarations. Pattern: Use .h files with forward declarations",
                locality="cross_module",
                context={"include_count": include_count, "language": "c"}
            ))
        
        return violations
    
    def _analyze_js_function_signatures(self, parse_result: ParseResult) -> List[Violation]:
        """Analyze JavaScript function signatures."""
        violations = []
        
        for i, line in enumerate(parse_result.source_lines, 1):
            line = line.strip()
            
            # Match function declarations: function name(...) or const name = (...) =>
            if ('function ' in line or '=>' in line) and '(' in line:
                paren_start = line.find('(')
                paren_end = line.find(')', paren_start)
                
                if paren_start != -1 and paren_end != -1:
                    params = line[paren_start+1:paren_end]
                    param_count = params.count(',') + 1 if params.strip() else 0
                    
                    if param_count > self.thresholds.max_positional_params:
                        violations.append(Violation(
                            id="",
                            type=ConnascenceType.POSITION,
                            severity=Severity.HIGH,
                            file_path=self.current_file_path,
                            line_number=i,
                            column=paren_start,
                            description=f"JavaScript function has {param_count} parameters (>{self.thresholds.max_positional_params})",
                            recommendation="REFACTOR: Use options object or break down function. Pattern: function(config) instead of function(a, b, c, d, e, f, g)",
                            locality="same_function",
                            context={"parameter_count": param_count, "language": "javascript"}
                        ))
        
        return violations
    
    def _analyze_js_magic_literals(self, parse_result: ParseResult) -> List[Violation]:
        """Analyze JavaScript magic literals."""
        violations = []
        
        for i, line in enumerate(parse_result.source_lines, 1):
            # Look for string literals and numbers
            import re
            
            # Magic numbers (excluding common ones)
            numbers = re.findall(r'\b(\d{2,})\b', line)
            for number in numbers:
                if int(number) not in [0, 1, 100, 1000]:  # Common JS numbers
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.MEANING,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=i,
                        column=line.find(number),
                        description=f"Magic number '{number}' should be a named constant",
                        recommendation="REFACTOR: Use const declaration. Pattern: const MAX_SIZE = 1024;",
                        locality="same_module",
                        context={"magic_value": number, "language": "javascript"}
                    ))
            
            # Magic strings (excluding very short ones)
            strings = re.findall(r'"([^"]{4,})"', line) + re.findall(r"'([^']{4,})'", line)
            for string in strings:
                if not any(common in string.lower() for common in ['http', 'www', 'error', 'success']):
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.MEANING,
                        severity=Severity.LOW,
                        file_path=self.current_file_path,
                        line_number=i,
                        column=line.find(f'"{string}"') if f'"{string}"' in line else line.find(f"'{string}'"),
                        description=f"Magic string '{string[:30]}...' should be a named constant",
                        recommendation="REFACTOR: Extract to const variable. Pattern: const ERROR_MESSAGE = 'string';",
                        locality="same_module",
                        context={"magic_value": string[:50], "language": "javascript"}
                    ))
        
        return violations
    
    def _analyze_js_callback_patterns(self, parse_result: ParseResult) -> List[Violation]:
        """Analyze JavaScript callback patterns for timing connascence."""
        violations = []
        
        callback_indicators = ['setTimeout', 'setInterval', 'callback', 'then(', 'catch(', 'async', 'await']
        
        for i, line in enumerate(parse_result.source_lines, 1):
            for indicator in callback_indicators:
                if indicator in line:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.TIMING,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=i,
                        column=line.find(indicator),
                        description=f"Potential timing coupling detected with {indicator}",
                        recommendation="REFACTOR: Use Promise-based patterns or async/await consistently. Pattern: Use Promise.all() for concurrent operations",
                        locality="cross_function",
                        context={"timing_pattern": indicator, "language": "javascript"}
                    ))
                    break  # Only report one per line
        
        return violations
    
    def _analyze_generic_magic_numbers(self, parse_result: ParseResult) -> List[Violation]:
        """Generic magic number detection for any language."""
        violations = []
        
        for i, line in enumerate(parse_result.source_lines, 1):
            import re
            numbers = re.findall(r'\b(\d{3,})\b', line)  # 3+ digits
            
            for number in numbers:
                violations.append(Violation(
                    id="",
                    type=ConnascenceType.MEANING,
                    severity=Severity.LOW,
                    file_path=self.current_file_path,
                    line_number=i,
                    column=line.find(number),
                    description=f"Potential magic number '{number}' detected",
                    recommendation=f"Consider extracting '{number}' as a named constant",
                    locality="same_module",
                    context={"magic_value": number, "language": parse_result.language}
                ))
        
        return violations
    
    def _analyze_generic_long_lines(self, parse_result: ParseResult) -> List[Violation]:
        """Generic long line detection."""
        violations = []
        max_line_length = 120
        
        for i, line in enumerate(parse_result.source_lines, 1):
            if len(line) > max_line_length:
                violations.append(Violation(
                    id="",
                    type=ConnascenceType.POSITION,
                    severity=Severity.LOW,
                    file_path=self.current_file_path,
                    line_number=i,
                    column=max_line_length,
                    description=f"Line too long ({len(line)} characters > {max_line_length})",
                    recommendation="Break long lines for better readability",
                    locality="same_line",
                    context={"line_length": len(line), "language": parse_result.language}
                ))
        
        return violations
    
    def _analyze_python_position(self, tree: ast.AST) -> List[Violation]:
        """Analyze Python positional parameters."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if param_count > self.thresholds.max_positional_params:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.POSITION,
                        severity=Severity.HIGH,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Function '{node.name}' has {param_count} positional parameters (>{self.thresholds.max_positional_params})",
                        recommendation="REFACTOR: Use **kwargs, dataclass, or break down function",
                        function_name=node.name,
                        locality="same_function",
                        context={"parameter_count": param_count}
                    ))
        
        return violations
    
    def _analyze_python_magic_literals(self, tree: ast.AST) -> List[Violation]:
        """Analyze Python magic literals."""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)) and node.value not in [0, 1, -1]:
                    violations.append(Violation(
                        id="",
                        type=ConnascenceType.MEANING,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Magic literal '{node.value}' should be a named constant",
                        recommendation="Extract to a module-level constant with descriptive name",
                        locality="same_module",
                        context={"magic_value": str(node.value)}
                    ))
        
        return violations