# SPDX-License-Identifier: MIT
"""
Formal Grammar Analysis Engine
==============================

Replaces regex-based pattern matching with proper Abstract Syntax Tree (AST)
analysis for accurate code pattern detection. Provides language-specific
formal grammar definitions and parsing rules.
"""

import ast
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum
from pathlib import Path

class PatternType(Enum):
    """Types of code patterns for formal grammar analysis."""
    FUNCTION_DEFINITION = "function_definition"
    CLASS_DEFINITION = "class_definition"
    MAGIC_LITERAL = "magic_literal"
    PARAMETER_LIST = "parameter_list"
    IMPORT_STATEMENT = "import_statement"
    VARIABLE_ASSIGNMENT = "variable_assignment"
    CONTROL_STRUCTURE = "control_structure"
    METHOD_CALL = "method_call"
    DOCSTRING = "docstring"
    COMMENT = "comment"

@dataclass
class GrammarMatch:
    """Represents a match found by formal grammar analysis."""
    pattern_type: PatternType
    node: ast.AST
    file_path: str
    line_number: int
    column: int
    text: str
    metadata: Dict[str, Any]
    confidence: float = 1.0

@dataclass
class MagicLiteralContext:
    """Context information for magic literal detection."""
    literal_value: Any
    literal_type: type
    in_conditional: bool
    in_loop: bool
    in_return: bool
    in_assignment: bool
    variable_name: Optional[str] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    is_constant: bool = False
    is_configuration: bool = False

class FormalGrammarAnalyzer(ABC):
    """Abstract base class for language-specific formal grammar analyzers."""
    
    @abstractmethod
    def analyze_file(self, file_path: str, source_code: str) -> List[GrammarMatch]:
        """Analyze source code using formal grammar rules."""
        pass
    
    @abstractmethod
    def detect_magic_literals(self, source_code: str) -> List[GrammarMatch]:
        """Detect magic literals using AST analysis."""
        pass
    
    @abstractmethod
    def detect_function_signatures(self, source_code: str) -> List[GrammarMatch]:
        """Detect function signatures and parameter patterns."""
        pass

class PythonGrammarAnalyzer(FormalGrammarAnalyzer):
    """Python-specific formal grammar analyzer using AST."""
    
    def __init__(self):
        self.magic_number_whitelist = {0, 1, -1, 2, 10, 100, 1000}
        self.magic_string_whitelist = {'', ' ', '\n', '\t', 'utf-8', 'ascii', 'None', 'True', 'False'}
        self.config_indicators = ['config', 'setting', 'const', 'default', 'option']
        
    def analyze_file(self, file_path: str, source_code: str) -> List[GrammarMatch]:
        """Comprehensive analysis using Python AST."""
        matches = []
        
        try:
            tree = ast.parse(source_code, filename=file_path)
            visitor = PythonASTVisitor(file_path, source_code.split('\n'))
            visitor.visit(tree)
            matches.extend(visitor.matches)
        except SyntaxError as e:
            # Handle syntax errors gracefully
            matches.append(GrammarMatch(
                pattern_type=PatternType.COMMENT,
                node=None,
                file_path=file_path,
                line_number=e.lineno or 1,
                column=e.offset or 0,
                text=f"Syntax error: {e.msg}",
                metadata={'error': str(e)},
                confidence=0.5
            ))
        
        return matches
    
    def detect_magic_literals(self, source_code: str) -> List[GrammarMatch]:
        """Detect magic literals with comprehensive context analysis."""
        matches = []
        
        try:
            tree = ast.parse(source_code)
            detector = MagicLiteralDetector(source_code.split('\n'))
            detector.visit(tree)
            matches.extend(detector.get_violations())
        except SyntaxError:
            # Fall back to regex for malformed code
            return self._regex_fallback_magic_literals(source_code)
        
        return matches
    
    def detect_function_signatures(self, source_code: str) -> List[GrammarMatch]:
        """Detect function signatures using AST analysis."""
        matches = []
        
        try:
            tree = ast.parse(source_code)
            detector = FunctionSignatureDetector(source_code.split('\n'))
            detector.visit(tree)
            matches.extend(detector.get_violations())
        except SyntaxError:
            return []
        
        return matches
    
    def _regex_fallback_magic_literals(self, source_code: str) -> List[GrammarMatch]:
        """Fallback regex-based magic literal detection for malformed code."""
        matches = []
        lines = source_code.split('\n')
        
        # Simple regex patterns as fallback
        number_pattern = re.compile(r'\b(?!0\b|1\b|-1\b)\d+\.?\d*\b')
        string_pattern = re.compile(r'''["'][^"']{3,}["']''')
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#'):
                continue
                
            # Find numeric literals
            for match in number_pattern.finditer(line):
                try:
                    value = float(match.group()) if '.' in match.group() else int(match.group())
                    if value not in self.magic_number_whitelist:
                        matches.append(GrammarMatch(
                            pattern_type=PatternType.MAGIC_LITERAL,
                            node=None,
                            file_path="<fallback>",
                            line_number=line_num,
                            column=match.start(),
                            text=match.group(),
                            metadata={'value': value, 'type': 'number', 'fallback': True},
                            confidence=0.7
                        ))
                except ValueError:
                    continue
            
            # Find string literals
            for match in string_pattern.finditer(line):
                value = match.group()[1:-1]  # Remove quotes
                if value not in self.magic_string_whitelist:
                    matches.append(GrammarMatch(
                        pattern_type=PatternType.MAGIC_LITERAL,
                        node=None,
                        file_path="<fallback>",
                        line_number=line_num,
                        column=match.start(),
                        text=match.group(),
                        metadata={'value': value, 'type': 'string', 'fallback': True},
                        confidence=0.7
                    ))
        
        return matches

class PythonASTVisitor(ast.NodeVisitor):
    """AST visitor for comprehensive Python code analysis."""
    
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.matches = []
        self.current_class = None
        self.current_function = None
        self.scope_stack = []
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions."""
        self.current_class = node.name
        self.scope_stack.append(('class', node.name))
        
        self.matches.append(GrammarMatch(
            pattern_type=PatternType.CLASS_DEFINITION,
            node=node,
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            text=f"class {node.name}",
            metadata={
                'class_name': node.name,
                'base_classes': [ast.unparse(base) if hasattr(ast, 'unparse') else str(base) for base in node.bases],
                'method_count': len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
                'decorator_count': len(node.decorator_list)
            }
        ))
        
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_class = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        self.current_function = node.name
        self.scope_stack.append(('function', node.name))
        
        # Analyze parameters
        param_count = len(node.args.args)
        has_varargs = node.args.vararg is not None
        has_kwargs = node.args.kwarg is not None
        default_count = len(node.args.defaults)
        
        self.matches.append(GrammarMatch(
            pattern_type=PatternType.FUNCTION_DEFINITION,
            node=node,
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            text=f"def {node.name}",
            metadata={
                'function_name': node.name,
                'parameter_count': param_count,
                'has_varargs': has_varargs,
                'has_kwargs': has_kwargs,
                'default_count': default_count,
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'decorator_count': len(node.decorator_list),
                'in_class': self.current_class
            }
        ))
        
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_function = None
    
    def visit_Import(self, node: ast.Import):
        """Visit import statements."""
        for alias in node.names:
            self.matches.append(GrammarMatch(
                pattern_type=PatternType.IMPORT_STATEMENT,
                node=node,
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                text=f"import {alias.name}",
                metadata={
                    'module': alias.name,
                    'alias': alias.asname,
                    'import_type': 'direct'
                }
            ))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from...import statements."""
        for alias in node.names:
            self.matches.append(GrammarMatch(
                pattern_type=PatternType.IMPORT_STATEMENT,
                node=node,
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                text=f"from {node.module} import {alias.name}",
                metadata={
                    'module': node.module,
                    'name': alias.name,
                    'alias': alias.asname,
                    'import_type': 'from',
                    'level': node.level
                }
            ))
        self.generic_visit(node)

class MagicLiteralDetector(ast.NodeVisitor):
    """Specialized detector for magic literals with context analysis."""
    
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.violations = []
        self.current_class = None
        self.current_function = None
        self.assignments = {}  # Track variable assignments
        self.constants = set()  # Track constants (ALL_CAPS variables)
        
        # Context tracking
        self.in_conditional = False
        self.in_loop = False
        self.in_return = False
        self.in_assignment = False
        self.current_assignment_target = None
        
        # Whitelists
        self.safe_numbers = {0, 1, -1, 2, 10, 100, 1000, 24, 60, 365, 1024}
        self.safe_strings = {'', ' ', '\n', '\t', 'utf-8', 'ascii', 'None', 'True', 'False'}
        self.config_patterns = [r'.*[Cc]onfig.*', r'.*[Ss]etting.*', r'.*[Cc]onst.*', r'.*[Dd]efault.*']
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track class context."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function context."""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_If(self, node: ast.If):
        """Track conditional context."""
        old_conditional = self.in_conditional
        self.in_conditional = True
        self.visit(node.test)  # Visit the condition
        self.in_conditional = old_conditional
        
        # Visit body and orelse normally
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)
    
    def visit_For(self, node: ast.For):
        """Track loop context."""
        old_loop = self.in_loop
        self.in_loop = True
        self.generic_visit(node)
        self.in_loop = old_loop
    
    def visit_While(self, node: ast.While):
        """Track loop context."""
        old_loop = self.in_loop
        self.in_loop = True
        self.generic_visit(node)
        self.in_loop = old_loop
    
    def visit_Return(self, node: ast.Return):
        """Track return context."""
        old_return = self.in_return
        self.in_return = True
        if node.value:
            self.visit(node.value)
        self.in_return = old_return
    
    def visit_Assign(self, node: ast.Assign):
        """Track assignment context and constants."""
        old_assignment = self.in_assignment
        old_target = self.current_assignment_target
        
        self.in_assignment = True
        
        # Extract assignment target names
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.current_assignment_target = target.id
                # Track constants (ALL_CAPS variables)
                if target.id.isupper() and len(target.id) > 1:
                    self.constants.add(target.id)
                # Store assignment for context
                if isinstance(node.value, ast.Constant):
                    self.assignments[target.id] = node.value.value
        
        self.visit(node.value)
        
        self.in_assignment = old_assignment
        self.current_assignment_target = old_target
    
    def visit_Constant(self, node: ast.Constant):
        """Analyze constant literals with comprehensive context."""
        if self._should_ignore_literal(node):
            return
        
        context = self._build_context(node)
        severity = self._calculate_severity(context)
        
        if severity > 0:
            self.violations.append(GrammarMatch(
                pattern_type=PatternType.MAGIC_LITERAL,
                node=node,
                file_path="<current>",
                line_number=node.lineno,
                column=node.col_offset,
                text=repr(node.value),
                metadata={
                    'context': context,
                    'severity_score': severity,
                    'literal_type': type(node.value).__name__,
                    'recommendations': self._generate_recommendations(context)
                },
                confidence=min(1.0, severity / 10.0)
            ))
        
        self.generic_visit(node)
    
    def _should_ignore_literal(self, node: ast.Constant) -> bool:
        """Determine if a literal should be ignored based on whitelists."""
        value = node.value
        
        # Ignore whitelisted numbers
        if isinstance(value, (int, float)) and value in self.safe_numbers:
            return True
        
        # Ignore whitelisted strings
        if isinstance(value, str) and value in self.safe_strings:
            return True
        
        # Ignore single characters
        if isinstance(value, str) and len(value) == 1:
            return True
        
        # Ignore boolean and None
        if value is None or isinstance(value, bool):
            return True
        
        return False
    
    def _build_context(self, node: ast.Constant) -> MagicLiteralContext:
        """Build comprehensive context for a magic literal."""
        return MagicLiteralContext(
            literal_value=node.value,
            literal_type=type(node.value),
            in_conditional=self.in_conditional,
            in_loop=self.in_loop,
            in_return=self.in_return,
            in_assignment=self.in_assignment,
            variable_name=self.current_assignment_target,
            function_name=self.current_function,
            class_name=self.current_class,
            is_constant=self.current_assignment_target in self.constants if self.current_assignment_target else False,
            is_configuration=self._is_configuration_context()
        )
    
    def _is_configuration_context(self) -> bool:
        """Check if the current context suggests configuration usage."""
        # Check class name
        if self.current_class:
            for pattern in self.config_patterns:
                if re.match(pattern, self.current_class):
                    return True
        
        # Check function name
        if self.current_function:
            config_functions = ['configure', 'setup', 'initialize', 'load_config', 'get_setting']
            if any(func in self.current_function.lower() for func in config_functions):
                return True
        
        # Check variable name
        if self.current_assignment_target:
            config_vars = ['config', 'setting', 'option', 'default', 'param']
            if any(var in self.current_assignment_target.lower() for var in config_vars):
                return True
        
        return False
    
    def _calculate_severity(self, context: MagicLiteralContext) -> float:
        """Calculate severity score for a magic literal based on context."""
        base_severity = 5.0  # Base severity
        
        # Reduce severity for constants
        if context.is_constant:
            base_severity *= 0.3
        
        # Reduce severity for configuration contexts
        if context.is_configuration:
            base_severity *= 0.5
        
        # Increase severity for conditionals
        if context.in_conditional:
            base_severity *= 1.5
        
        # Increase severity for business logic functions
        if context.function_name and 'process' in context.function_name.lower():
            base_severity *= 1.3
        
        # Reduce severity for small numbers in loops
        if context.in_loop and isinstance(context.literal_value, int) and context.literal_value < 10:
            base_severity *= 0.7
        
        # String-specific adjustments
        if isinstance(context.literal_value, str):
            # Very short strings are less problematic
            if len(context.literal_value) < 5:
                base_severity *= 0.6
            # URLs and file paths are often legitimate
            if any(pattern in context.literal_value for pattern in ['http', '/', '.', '@']):
                base_severity *= 0.4
        
        return base_severity
    
    def _generate_recommendations(self, context: MagicLiteralContext) -> List[str]:
        """Generate context-specific recommendations for magic literal fixes."""
        recommendations = []
        
        if context.is_configuration:
            recommendations.append("Consider moving to configuration file or environment variable")
        elif context.is_constant:
            recommendations.append("Already a constant - consider better naming or documentation")
        else:
            recommendations.append("Extract to a named constant with descriptive name")
        
        if context.in_conditional:
            recommendations.append("Magic literals in conditionals are particularly error-prone")
        
        if isinstance(context.literal_value, str):
            recommendations.append("Consider using enum or constants for string literals")
        elif isinstance(context.literal_value, (int, float)):
            recommendations.append("Use named constants for numeric values")
        
        return recommendations
    
    def get_violations(self) -> List[GrammarMatch]:
        """Get all detected magic literal violations."""
        return self.violations

class FunctionSignatureDetector(ast.NodeVisitor):
    """Detector for function signature issues using formal grammar analysis."""
    
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.violations = []
        self.nasa_param_threshold = 6  # NASA Power of Ten rule
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Analyze function signatures for parameter coupling."""
        param_count = len(node.args.args)
        
        # Exclude 'self' parameter for methods
        if param_count > 0 and node.args.args[0].arg in ['self', 'cls']:
            effective_param_count = param_count - 1
        else:
            effective_param_count = param_count
        
        if effective_param_count > self.nasa_param_threshold:
            self.violations.append(GrammarMatch(
                pattern_type=PatternType.PARAMETER_LIST,
                node=node,
                file_path="<current>",
                line_number=node.lineno,
                column=node.col_offset,
                text=f"def {node.name}(...)",
                metadata={
                    'function_name': node.name,
                    'parameter_count': effective_param_count,
                    'threshold': self.nasa_param_threshold,
                    'has_defaults': len(node.args.defaults) > 0,
                    'has_varargs': node.args.vararg is not None,
                    'has_kwargs': node.args.kwarg is not None,
                    'recommendations': self._get_parameter_recommendations(effective_param_count, node)
                },
                confidence=1.0
            ))
        
        self.generic_visit(node)
    
    def _get_parameter_recommendations(self, param_count: int, node: ast.FunctionDef) -> List[str]:
        """Generate recommendations for reducing parameter count."""
        recommendations = []
        
        if param_count > 10:
            recommendations.append("Consider using a configuration object or data class")
        elif param_count > 6:
            recommendations.append("Group related parameters into objects")
        
        if len(node.args.defaults) == 0:
            recommendations.append("Consider using default parameters for optional arguments")
        
        if not node.args.kwarg:
            recommendations.append("Consider using **kwargs for optional parameters")
        
        recommendations.append("Apply the NASA Power of Ten rule: limit to 6 parameters maximum")
        
        return recommendations
    
    def get_violations(self) -> List[GrammarMatch]:
        """Get all detected function signature violations."""
        return self.violations

class JavaScriptGrammarAnalyzer(FormalGrammarAnalyzer):
    """JavaScript-specific formal grammar analyzer."""
    
    def analyze_file(self, file_path: str, source_code: str) -> List[GrammarMatch]:
        """Analyze JavaScript using regex patterns (AST parsing would require JS parser)."""
        # For JavaScript, we'd need a JavaScript AST parser
        # For now, provide improved regex-based analysis
        return self._enhanced_regex_analysis(file_path, source_code)
    
    def detect_magic_literals(self, source_code: str) -> List[GrammarMatch]:
        """Detect JavaScript magic literals using enhanced regex."""
        matches = []
        lines = source_code.split('\n')
        
        # Enhanced patterns for JavaScript
        number_pattern = re.compile(r'\b(?!0\b|1\b|-1\b)\d+\.?\d*\b')
        string_pattern = re.compile(r'''(?:["'](?:[^"'\\]|\\.){3,}["'])''')
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if '//' in line:
                line = line[:line.index('//')]
            
            for match in number_pattern.finditer(line):
                matches.append(GrammarMatch(
                    pattern_type=PatternType.MAGIC_LITERAL,
                    node=None,
                    file_path=file_path,
                    line_number=line_num,
                    column=match.start(),
                    text=match.group(),
                    metadata={'value': match.group(), 'type': 'number'},
                    confidence=0.8
                ))
        
        return matches
    
    def detect_function_signatures(self, source_code: str) -> List[GrammarMatch]:
        """Detect JavaScript function signatures."""
        matches = []
        lines = source_code.split('\n')
        
        # Enhanced JavaScript function patterns
        function_patterns = [
            re.compile(r'function\s+(\w+)\s*\(([^)]*)\)'),
            re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*function\s*\(([^)]*)\)'),
            re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>'),
            re.compile(r'(\w+)\s*:\s*function\s*\(([^)]*)\)')
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in function_patterns:
                match = pattern.search(line)
                if match:
                    func_name = match.group(1)
                    params = match.group(2).strip()
                    param_count = len([p.strip() for p in params.split(',') if p.strip()]) if params else 0
                    
                    if param_count > 6:  # NASA threshold
                        matches.append(GrammarMatch(
                            pattern_type=PatternType.FUNCTION_DEFINITION,
                            node=None,
                            file_path="<current>",
                            line_number=line_num,
                            column=match.start(),
                            text=match.group(),
                            metadata={
                                'function_name': func_name,
                                'parameter_count': param_count,
                                'language': 'javascript'
                            },
                            confidence=0.9
                        ))
        
        return matches
    
    def _enhanced_regex_analysis(self, file_path: str, source_code: str) -> List[GrammarMatch]:
        """Enhanced regex-based analysis for JavaScript."""
        matches = []
        matches.extend(self.detect_magic_literals(source_code))
        matches.extend(self.detect_function_signatures(source_code))
        return matches

class FormalGrammarEngine:
    """Main engine that coordinates formal grammar analysis across languages."""
    
    def __init__(self):
        self.analyzers = {
            'python': PythonGrammarAnalyzer(),
            'javascript': JavaScriptGrammarAnalyzer(),
            'typescript': JavaScriptGrammarAnalyzer(),  # Use JS analyzer for TS
        }
    
    def analyze_file(self, file_path: str, source_code: str, language: Optional[str] = None) -> List[GrammarMatch]:
        """Analyze a file using the appropriate formal grammar analyzer."""
        if not language:
            language = self._detect_language(file_path)
        
        analyzer = self.analyzers.get(language)
        if not analyzer:
            return []  # Unsupported language
        
        return analyzer.analyze_file(file_path, source_code)
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file extension."""
        extension = Path(file_path).suffix.lower()
        
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript'
        }
        
        return extension_map.get(extension)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.analyzers.keys())