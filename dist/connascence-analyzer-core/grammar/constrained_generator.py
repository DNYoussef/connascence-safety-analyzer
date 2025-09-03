"""
Constrained Code Generator

Ensures that generated code adheres to grammar overlays and safety profiles.
Provides token-level constraints for LLM generation and validates output
before returning to ensure syntactic correctness.
"""

import re
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from .backends.tree_sitter_backend import TreeSitterBackend, LanguageSupport, ParseResult
from .overlay_manager import OverlayManager, GrammarOverlay


class GenerationMode(Enum):
    """Code generation modes with different constraint levels."""
    PERMISSIVE = "permissive"  # Allow most constructs, warn on violations
    GUIDED = "guided"         # Guide towards safe patterns, soft constraints  
    STRICT = "strict"         # Hard constraints, refuse unsafe generation
    SAFETY_CRITICAL = "safety_critical"  # Maximum constraints for safety code


@dataclass
class GenerationConstraints:
    """Constraints for code generation."""
    language: LanguageSupport
    overlays: List[str] = None
    mode: GenerationMode = GenerationMode.GUIDED
    max_tokens: int = 1000
    banned_constructs: Set[str] = None
    required_patterns: List[str] = None
    complexity_limits: Dict[str, int] = None
    
    def __post_init__(self):
        if self.overlays is None:
            self.overlays = []
        if self.banned_constructs is None:
            self.banned_constructs = set()
        if self.required_patterns is None:
            self.required_patterns = []
        if self.complexity_limits is None:
            self.complexity_limits = {}


@dataclass
class GenerationResult:
    """Result of constrained code generation."""
    success: bool
    code: str = ""
    violations: List[Dict[str, Any]] = None
    warnings: List[str] = None
    tokens_used: int = 0
    constraints_applied: List[str] = None
    
    def __post_init__(self):
        if self.violations is None:
            self.violations = []
        if self.warnings is None:
            self.warnings = []
        if self.constraints_applied is None:
            self.constraints_applied = []


class ConstrainedGenerator:
    """Generates code under grammar and safety constraints."""
    
    def __init__(self, backend: TreeSitterBackend, overlay_manager: OverlayManager):
        self.backend = backend
        self.overlay_manager = overlay_manager
        self._token_filters: Dict[str, Callable] = {}
        self._pattern_validators: Dict[str, Callable] = {}
        
        # Initialize built-in filters and validators
        self._initialize_filters()
    
    def get_next_tokens(self, prefix: str, constraints: GenerationConstraints) -> List[str]:
        """Get valid next tokens given current prefix and constraints."""
        # Get base tokens from grammar
        base_tokens = self.backend.get_next_tokens(
            prefix, constraints.language
        )
        
        # Apply overlay constraints
        filtered_tokens = base_tokens
        for overlay_id in constraints.overlays:
            filtered_tokens = self._apply_overlay_filter(
                filtered_tokens, overlay_id, prefix
            )
        
        # Apply mode-specific filtering
        filtered_tokens = self._apply_mode_filter(
            filtered_tokens, constraints.mode, prefix
        )
        
        # Apply banned constructs filter
        if constraints.banned_constructs:
            filtered_tokens = [
                token for token in filtered_tokens
                if not any(banned in token for banned in constraints.banned_constructs)
            ]
        
        return filtered_tokens[:50]  # Limit to reasonable number
    
    def validate_generation(self, code: str, constraints: GenerationConstraints) -> GenerationResult:
        """Validate generated code against constraints."""
        # Parse the code
        parse_result = self.backend.parse(code, constraints.language)
        
        if not parse_result.success:
            return GenerationResult(
                success=False,
                code=code,
                violations=[{
                    "type": "parse_error",
                    "message": "Generated code has syntax errors",
                    "errors": parse_result.errors
                }]
            )
        
        violations = []
        warnings = []
        constraints_applied = []
        
        # Check overlay constraints
        for overlay_id in constraints.overlays:
            overlay = self.overlay_manager.get_overlay(overlay_id)
            if overlay:
                overlay_violations = self.overlay_manager.validate_code_against_overlay(
                    [parse_result.ast], overlay_id
                )
                violations.extend(overlay_violations)
                constraints_applied.append(f"overlay:{overlay_id}")
        
        # Check complexity limits
        if constraints.complexity_limits:
            complexity_violations = self._check_complexity_limits(
                parse_result.ast, constraints.complexity_limits
            )
            violations.extend(complexity_violations)
            constraints_applied.append("complexity_limits")
        
        # Check required patterns
        if constraints.required_patterns:
            pattern_violations = self._check_required_patterns(
                code, constraints.required_patterns
            )
            violations.extend(pattern_violations)
            constraints_applied.append("required_patterns")
        
        # Determine success based on mode
        success = self._determine_success(violations, warnings, constraints.mode)
        
        return GenerationResult(
            success=success,
            code=code,
            violations=violations,
            warnings=warnings,
            tokens_used=len(code.split()),
            constraints_applied=constraints_applied
        )
    
    def suggest_fixes(self, result: GenerationResult, 
                     constraints: GenerationConstraints) -> List[str]:
        """Suggest fixes for constraint violations."""
        suggestions = []
        
        for violation in result.violations:
            if violation.get("type") == "banned_construct":
                banned = violation.get("construct", "")
                suggestions.append(f"Replace banned construct '{banned}' with safe alternative")
            
            elif violation.get("rule") == "nasa_rule_1":
                if "goto" in violation.get("message", ""):
                    suggestions.append("Replace goto with structured control flow (if/else, loops)")
                elif "recursion" in violation.get("message", ""):
                    suggestions.append("Convert recursion to iterative algorithm")
            
            elif violation.get("rule") == "nasa_rule_4":
                suggestions.append("Split large function into smaller, focused functions")
            
            elif violation.get("type") == "complexity_limit":
                suggestions.append("Reduce cyclomatic complexity by extracting methods")
        
        return suggestions
    
    def auto_repair(self, code: str, constraints: GenerationConstraints,
                   max_attempts: int = 3) -> GenerationResult:
        """Attempt to automatically repair constraint violations."""
        current_code = code
        
        for attempt in range(max_attempts):
            result = self.validate_generation(current_code, constraints)
            
            if result.success:
                return result
            
            # Try simple repairs
            repaired_code = self._attempt_simple_repairs(
                current_code, result.violations, constraints
            )
            
            if repaired_code == current_code:
                # No repairs possible
                break
            
            current_code = repaired_code
        
        # Return the best attempt
        return self.validate_generation(current_code, constraints)
    
    def _initialize_filters(self):
        """Initialize built-in token filters."""
        # NASA C safety filters
        self._token_filters['nasa_c_safety'] = self._nasa_c_token_filter
        
        # Python safety filters  
        self._token_filters['nasa_python_safety'] = self._python_safety_token_filter
    
    def _apply_overlay_filter(self, tokens: List[str], overlay_id: str, 
                             prefix: str) -> List[str]:
        """Apply overlay-specific token filtering."""
        overlay = self.overlay_manager.get_overlay(overlay_id)
        if not overlay:
            return tokens
        
        banned_constructs = self.overlay_manager.get_banned_constructs(overlay_id)
        
        # Filter out banned constructs
        filtered = []
        for token in tokens:
            if not any(banned in token.lower() for banned in banned_constructs):
                filtered.append(token)
        
        # Apply custom filter if available
        if overlay_id in self._token_filters:
            filtered = self._token_filters[overlay_id](filtered, prefix)
        
        return filtered
    
    def _apply_mode_filter(self, tokens: List[str], mode: GenerationMode,
                          prefix: str) -> List[str]:
        """Apply mode-specific token filtering."""
        if mode == GenerationMode.PERMISSIVE:
            return tokens  # Allow everything
        
        elif mode == GenerationMode.GUIDED:
            # Prefer safer alternatives
            return self._prefer_safe_tokens(tokens, prefix)
        
        elif mode == GenerationMode.STRICT:
            # Remove risky tokens
            return self._remove_risky_tokens(tokens, prefix)
        
        elif mode == GenerationMode.SAFETY_CRITICAL:
            # Maximum restrictions
            return self._safety_critical_filter(tokens, prefix)
        
        return tokens
    
    def _nasa_c_token_filter(self, tokens: List[str], prefix: str) -> List[str]:
        """NASA C safety-specific token filtering."""
        # Remove dangerous keywords
        dangerous = {'goto', 'setjmp', 'longjmp'}
        filtered = [t for t in tokens if t.lower() not in dangerous]
        
        # If we're in a function context, prefer simple constructs
        if self._is_in_function_context(prefix):
            # Prefer simple control flow
            safe_control = {'if', 'else', 'for', 'while', 'return'}
            if any(t in safe_control for t in filtered):
                filtered = [t for t in filtered if t in safe_control or not t.isalpha()]
        
        return filtered
    
    def _python_safety_token_filter(self, tokens: List[str], prefix: str) -> List[str]:
        """Python safety-specific token filtering."""
        # Remove dangerous functions
        dangerous = {'exec', 'eval', 'compile', '__import__'}
        filtered = [t for t in tokens if t not in dangerous]
        
        # Discourage wildcard imports
        if prefix.strip().endswith('import'):
            filtered = [t for t in filtered if t != '*']
        
        return filtered
    
    def _prefer_safe_tokens(self, tokens: List[str], prefix: str) -> List[str]:
        """Prefer safer alternatives in guided mode."""
        # Sort tokens by safety (safer tokens first)
        safe_order = {
            # Control flow - safest first
            'if': 1, 'else': 1, 'elif': 1,
            'for': 2, 'while': 3,
            'return': 1, 'break': 2, 'continue': 2,
            
            # Data types - safest first  
            'int': 1, 'float': 1, 'str': 1, 'bool': 1,
            'list': 2, 'dict': 2, 'set': 3,
            
            # Functions
            'def': 1, 'class': 1,
            'print': 1, 'len': 1, 'range': 1,
        }
        
        return sorted(tokens, key=lambda t: safe_order.get(t, 10))
    
    def _remove_risky_tokens(self, tokens: List[str], prefix: str) -> List[str]:
        """Remove risky tokens in strict mode."""
        risky = {
            'exec', 'eval', 'compile', '__import__',
            'goto', 'setjmp', 'longjmp',
            '*',  # Wildcard import
        }
        
        return [t for t in tokens if t not in risky]
    
    def _safety_critical_filter(self, tokens: List[str], prefix: str) -> List[str]:
        """Maximum restrictions for safety-critical code."""
        # Very conservative - only allow basic, safe constructs
        safe_tokens = {
            # Basic control flow
            'if', 'else', 'elif', 'for', 'while', 'return',
            'break', 'continue',
            
            # Basic data types
            'int', 'float', 'str', 'bool', 'None', 'True', 'False',
            
            # Basic operators
            '+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=',
            'and', 'or', 'not',
            
            # Basic punctuation
            '(', ')', '[', ']', '{', '}', ':', ';', ',', '.',
        }
        
        return [t for t in tokens if t in safe_tokens or not t.isalpha()]
    
    def _check_complexity_limits(self, ast, limits: Dict[str, int]) -> List[Dict[str, Any]]:
        """Check code against complexity limits."""
        violations = []
        
        if 'cyclomatic_complexity' in limits:
            functions = self.backend.extract_functions(ast, LanguageSupport.PYTHON)
            for func in functions:
                # Simple complexity estimate (would use real calculator)
                estimated_complexity = self._estimate_complexity(func)
                if estimated_complexity > limits['cyclomatic_complexity']:
                    violations.append({
                        "type": "complexity_limit",
                        "target": "cyclomatic_complexity",
                        "function": func.get('name', 'unknown'),
                        "actual": estimated_complexity,
                        "limit": limits['cyclomatic_complexity'],
                        "message": f"Function complexity {estimated_complexity} exceeds limit {limits['cyclomatic_complexity']}"
                    })
        
        return violations
    
    def _check_required_patterns(self, code: str, patterns: List[str]) -> List[Dict[str, Any]]:
        """Check for required patterns in code."""
        violations = []
        
        for pattern in patterns:
            if pattern == "type_hints" and "def " in code:
                # Check if functions have type hints
                if not re.search(r'def \w+\([^)]*:[^)]+\)', code):
                    violations.append({
                        "type": "missing_pattern",
                        "pattern": pattern,
                        "message": "Functions should have type hints"
                    })
            
            elif pattern == "docstrings" and ("def " in code or "class " in code):
                # Check for docstrings
                if not '"""' in code and not "'''" in code:
                    violations.append({
                        "type": "missing_pattern",
                        "pattern": pattern,
                        "message": "Functions and classes should have docstrings"
                    })
        
        return violations
    
    def _determine_success(self, violations: List[Dict], warnings: List[str], 
                          mode: GenerationMode) -> bool:
        """Determine if generation was successful based on mode."""
        if mode == GenerationMode.PERMISSIVE:
            # Only fail on critical violations
            critical_violations = [v for v in violations if v.get('severity') == 'critical']
            return len(critical_violations) == 0
        
        elif mode == GenerationMode.GUIDED:
            # Fail on critical and high violations
            serious_violations = [
                v for v in violations 
                if v.get('severity') in ['critical', 'high']
            ]
            return len(serious_violations) == 0
        
        elif mode in [GenerationMode.STRICT, GenerationMode.SAFETY_CRITICAL]:
            # Fail on any violations
            return len(violations) == 0
        
        return len(violations) == 0
    
    def _attempt_simple_repairs(self, code: str, violations: List[Dict],
                               constraints: GenerationConstraints) -> str:
        """Attempt simple automatic repairs."""
        repaired = code
        
        for violation in violations:
            if violation.get('type') == 'banned_construct':
                # Try to replace banned constructs
                if 'goto' in violation.get('message', '').lower():
                    # This would implement goto removal (complex)
                    pass
            
            elif violation.get('type') == 'missing_pattern':
                if violation.get('pattern') == 'type_hints':
                    # Add basic type hints
                    repaired = re.sub(
                        r'def (\w+)\(([^)]*)\):',
                        r'def \1(\2) -> None:',
                        repaired
                    )
        
        return repaired
    
    def _is_in_function_context(self, prefix: str) -> bool:
        """Check if we're currently inside a function."""
        # Simple heuristic - count braces/indentation
        return 'def ' in prefix or '{' in prefix
    
    def _estimate_complexity(self, func: Dict[str, Any]) -> int:
        """Rough estimate of cyclomatic complexity."""
        # This would implement real complexity calculation
        # For now, use line count as proxy
        return max(1, func.get('body_lines', 1) // 10)