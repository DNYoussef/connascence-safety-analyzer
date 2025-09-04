import ast
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .patch_api import PatchSuggestion
from analyzer.core import ConnascenceViolation


@dataclass
class AutofixConfig:
    """Configuration for autofix engine."""
    safety_level: str = 'moderate'  # conservative, moderate, aggressive
    max_patches_per_file: int = 10
    preserve_formatting: bool = True
    backup_enabled: bool = True
    

class AutofixEngine:
    """Main autofix engine for connascence violations."""
    
    def __init__(self, config: Optional[AutofixConfig] = None, dry_run: bool = False):
        self.config = config or AutofixConfig()
        self.dry_run = dry_run
        self.patch_generator = PatchGenerator()
        self.safe_autofixer = SafeAutofixer(self.config)
        self._fixers = self._register_fixers()
    
    def _register_fixers(self) -> Dict[str, callable]:
        """Register violation type fixers."""
        return {
            'connascence_of_meaning': self._fix_magic_literals,
            'connascence_of_position': self._fix_parameter_coupling,
            'god_object': self._fix_god_object,
            'connascence_of_algorithm': self._fix_algorithm_duplication
        }
    
    def generate_fixes(self, violations: List[ConnascenceViolation], 
                      source_code: str) -> List[PatchSuggestion]:
        """Generate fixes for violations."""
        patches = []
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return []  # Cannot fix files with syntax errors
        
        for violation in violations:
            if violation.type in self._fixers:
                fixer = self._fixers[violation.type]
                patch = fixer(violation, tree, source_code)
                if patch:
                    patches.append(patch)
        
        # Sort by confidence and safety
        patches.sort(key=lambda p: (p.confidence, p.safety_level == 'safe'), reverse=True)
        
        return patches[:self.config.max_patches_per_file]
    
    def _fix_magic_literals(self, violation: ConnascenceViolation, 
                           tree: ast.AST, source: str) -> Optional[PatchSuggestion]:
        """Fix magic literal violations."""
        return self.patch_generator.generate_magic_literal_fix(
            violation, tree, source
        )
    
    def _fix_parameter_coupling(self, violation: ConnascenceViolation,
                              tree: ast.AST, source: str) -> Optional[PatchSuggestion]:
        """Fix parameter position coupling."""
        return self.patch_generator.generate_parameter_object_fix(
            violation, tree, source
        )
    
    def _fix_god_object(self, violation: ConnascenceViolation,
                       tree: ast.AST, source: str) -> Optional[PatchSuggestion]:
        """Fix god object violations."""
        from .class_splits import ClassSplitFixer
        fixer = ClassSplitFixer()
        return fixer.generate_patch(violation, tree, source)
    
    def _fix_algorithm_duplication(self, violation: ConnascenceViolation,
                                  tree: ast.AST, source: str) -> Optional[PatchSuggestion]:
        """Fix algorithm duplication violations."""
        # Placeholder for algorithm deduplication
        return None


class PatchGenerator:
    """Generates specific patches for different violation types."""
    
    def __init__(self):
        self.magic_literal_patterns = {
            'numeric': r'\b\d+\.?\d*\b',
            'string': r'["\'][^"\'\n]*["\']',
            'timeout': r'\b(?:timeout|delay|wait).*?\d+',
            'buffer_size': r'\b(?:buffer|size|limit).*?\d+'
        }
    
    def generate_magic_literal_fix(self, violation: ConnascenceViolation,
                                  tree: ast.AST, source: str) -> Optional[PatchSuggestion]:
        """Generate fix for magic literal violations."""
        lines = source.splitlines()
        if violation.line_number > len(lines):
            return None
        
        line = lines[violation.line_number - 1]
        
        # Extract the magic literal
        literal_value = self._extract_literal_value(violation, line)
        if not literal_value:
            return None
        
        # Generate constant name
        constant_name = self._generate_constant_name(literal_value, violation.file_path)
        
        # Generate the fix
        old_code = line.strip()
        new_code = line.replace(literal_value, constant_name)
        
        # Add constant definition at top of file
        constant_definition = f"{constant_name} = {literal_value}"
        
        return PatchSuggestion(
            violation_id=getattr(violation, 'id', 'unknown'),
            confidence=0.8,
            description=f"Extract magic literal {literal_value} to constant {constant_name}",
            old_code=old_code,
            new_code=new_code,
            file_path=violation.file_path,
            line_range=(violation.line_number, violation.line_number),
            safety_level='safe',
            rollback_info={'constant_definition': constant_definition}
        )
    
    def generate_parameter_object_fix(self, violation: ConnascenceViolation,
                                    tree: ast.AST, source: str) -> Optional[PatchSuggestion]:
        """Generate parameter object fix for CoP violations."""
        # Find function with too many parameters
        func_finder = FunctionFinder(violation.line_number)
        func_finder.visit(tree)
        
        if not func_finder.found_function:
            return None
        
        func = func_finder.found_function
        if len(func.args.args) < 4:  # Only fix if 4+ parameters
            return None
        
        # Generate parameter object class
        param_class_name = f"{func.name.title()}Params"
        param_fields = [arg.arg for arg in func.args.args if arg.arg != 'self']
        
        class_definition = self._generate_param_class(param_class_name, param_fields)
        
        return PatchSuggestion(
            violation_id=getattr(violation, 'id', 'unknown'),
            confidence=0.7,
            description=f"Extract parameters to {param_class_name} class",
            old_code=f"def {func.name}({', '.join(param_fields)}):",
            new_code=f"def {func.name}(self, params: {param_class_name}):",
            file_path=violation.file_path,
            line_range=(func.lineno, func.lineno),
            safety_level='moderate',
            rollback_info={'class_definition': class_definition}
        )
    
    def _extract_literal_value(self, violation: ConnascenceViolation, line: str) -> Optional[str]:
        """Extract literal value from violation context."""
        if hasattr(violation, 'context') and 'literal_value' in violation.context:
            return violation.context['literal_value']
        
        # Fallback: try to extract from line
        for pattern in self.magic_literal_patterns.values():
            match = re.search(pattern, line)
            if match:
                return match.group(0)
        
        return None
    
    def _generate_constant_name(self, literal_value: str, file_path: str) -> str:
        """Generate appropriate constant name."""
        # Remove quotes for strings
        clean_value = literal_value.strip('"\'')
        
        # Generate based on context
        if 'timeout' in file_path.lower() or 'time' in clean_value.lower():
            return f'TIMEOUT_SECONDS'
        elif 'buffer' in file_path.lower() or 'size' in clean_value.lower():
            return f'BUFFER_SIZE'
        elif clean_value.isdigit():
            return f'DEFAULT_VALUE'
        else:
            # Generate from file name
            base_name = Path(file_path).stem.upper()
            return f'{base_name}_CONSTANT'
    
    def _generate_param_class(self, class_name: str, fields: List[str]) -> str:
        """Generate parameter object class definition."""
        field_definitions = [f'    {field}: Any = None' for field in fields]
        
        return f"""@dataclass
class {class_name}:
    \"\"\"Parameter object for {class_name.replace('Params', '').lower()} function.\"\"\"
{chr(10).join(field_definitions)}
"""


class SafeAutofixer:
    """Applies patches safely with validation and rollback."""
    
    def __init__(self, config: AutofixConfig):
        self.config = config
    
    def apply_patch(self, patch: PatchSuggestion, source_code: str) -> Tuple[bool, str, str]:
        """Apply patch safely with validation.
        
        Returns:
            (success, new_source, error_message)
        """
        if not self._validate_patch(patch, source_code):
            return False, source_code, "Patch validation failed"
        
        try:
            lines = source_code.splitlines()
            
            # Apply the patch
            start_line = patch.line_range[0] - 1
            end_line = patch.line_range[1] - 1
            
            # Replace the target line(s)
            new_lines = lines[:start_line] + [patch.new_code] + lines[end_line + 1:]
            new_source = '\n'.join(new_lines)
            
            # Validate the result can be parsed
            try:
                ast.parse(new_source)
            except SyntaxError as e:
                return False, source_code, f"Patch creates syntax error: {e}"
            
            return True, new_source, ""
            
        except Exception as e:
            return False, source_code, f"Failed to apply patch: {e}"
    
    def _validate_patch(self, patch: PatchSuggestion, source_code: str) -> bool:
        """Validate patch is safe to apply."""
        if patch.confidence < 0.5:
            return False
        
        if patch.safety_level == 'aggressive' and self.config.safety_level == 'conservative':
            return False
        
        # Ensure patch targets exist in source
        lines = source_code.splitlines()
        start_line = patch.line_range[0] - 1
        
        if start_line >= len(lines):
            return False
        
        return True


class FunctionFinder(ast.NodeVisitor):
    """AST visitor to find functions on specific lines."""
    
    def __init__(self, target_line: int):
        self.target_line = target_line
        self.found_function = None
    
    def visit_FunctionDef(self, node):
        if hasattr(node, 'lineno') and node.lineno <= self.target_line:
            end_line = getattr(node, 'end_lineno', node.lineno + 10)
            if self.target_line <= end_line:
                self.found_function = node
        self.generic_visit(node)