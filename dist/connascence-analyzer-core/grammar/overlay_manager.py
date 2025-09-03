"""
Grammar Overlay Manager

Manages grammar overlays that restrict language features for safety profiles.
Overlays can ban constructs (like goto), limit complexity, or enforce patterns
required by safety standards like NASA/JPL Power of Ten rules.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from .backends.tree_sitter_backend import LanguageSupport


@dataclass
class OverlayRule:
    """A single overlay rule that restricts or requires language features."""
    id: str
    name: str
    description: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    rule_type: str  # 'ban', 'limit', 'require', 'pattern'
    target: str  # node type, pattern, or feature
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass 
class GrammarOverlay:
    """A collection of rules that define a grammar subset."""
    id: str
    name: str
    description: str
    language: LanguageSupport
    rules: List[OverlayRule]
    inherits: Optional[List[str]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.inherits is None:
            self.inherits = []
        if self.metadata is None:
            self.metadata = {}


class OverlayManager:
    """Manages grammar overlays for safety and quality enforcement."""
    
    def __init__(self, overlay_directory: Optional[Path] = None):
        self.overlay_directory = overlay_directory or Path(__file__).parent / "overlays"
        self._overlays: Dict[str, GrammarOverlay] = {}
        self._rule_cache: Dict[str, Dict[str, List[OverlayRule]]] = {}
        
        # Initialize built-in overlays
        self._load_builtin_overlays()
        
        # Load external overlays if directory exists
        if self.overlay_directory.exists():
            self._load_external_overlays()
    
    def get_overlay(self, overlay_id: str) -> Optional[GrammarOverlay]:
        """Get overlay by ID."""
        return self._overlays.get(overlay_id)
    
    def list_overlays(self, language: Optional[LanguageSupport] = None) -> List[str]:
        """List available overlay IDs, optionally filtered by language."""
        if language is None:
            return list(self._overlays.keys())
        
        return [
            overlay_id for overlay_id, overlay in self._overlays.items()
            if overlay.language == language
        ]
    
    def get_rules_for_overlay(self, overlay_id: str) -> List[OverlayRule]:
        """Get all rules for an overlay, including inherited rules."""
        if overlay_id not in self._overlays:
            return []
        
        # Use cache if available
        if overlay_id in self._rule_cache:
            return sum(self._rule_cache[overlay_id].values(), [])
        
        overlay = self._overlays[overlay_id]
        all_rules = []
        
        # Collect inherited rules first
        for parent_id in overlay.inherits:
            parent_rules = self.get_rules_for_overlay(parent_id)
            all_rules.extend(parent_rules)
        
        # Add overlay's own rules
        all_rules.extend(overlay.rules)
        
        # Cache the result
        self._rule_cache[overlay_id] = {"all": all_rules}
        
        return all_rules
    
    def get_banned_constructs(self, overlay_id: str) -> Set[str]:
        """Get set of banned constructs for overlay."""
        rules = self.get_rules_for_overlay(overlay_id)
        banned = set()
        
        for rule in rules:
            if rule.rule_type == 'ban':
                banned.add(rule.target)
        
        return banned
    
    def get_complexity_limits(self, overlay_id: str) -> Dict[str, int]:
        """Get complexity limits defined by overlay."""
        rules = self.get_rules_for_overlay(overlay_id)
        limits = {}
        
        for rule in rules:
            if rule.rule_type == 'limit' and 'max_value' in rule.parameters:
                limits[rule.target] = rule.parameters['max_value']
        
        return limits
    
    def validate_code_against_overlay(self, ast_nodes: List[Any], overlay_id: str) -> List[Dict[str, Any]]:
        """Validate AST nodes against overlay rules."""
        if overlay_id not in self._overlays:
            return [{"error": f"Overlay {overlay_id} not found"}]
        
        violations = []
        rules = self.get_rules_for_overlay(overlay_id)
        
        for rule in rules:
            rule_violations = self._check_rule_against_nodes(rule, ast_nodes)
            violations.extend(rule_violations)
        
        return violations
    
    def create_overlay(self, overlay: GrammarOverlay) -> bool:
        """Create a new overlay."""
        if overlay.id in self._overlays:
            return False
        
        self._overlays[overlay.id] = overlay
        
        # Clear cache since we have a new overlay
        self._rule_cache.clear()
        
        return True
    
    def save_overlay(self, overlay_id: str, file_path: Optional[Path] = None) -> bool:
        """Save overlay to file."""
        if overlay_id not in self._overlays:
            return False
        
        overlay = self._overlays[overlay_id]
        
        if file_path is None:
            file_path = self.overlay_directory / f"{overlay_id}.yml"
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to serializable format
        overlay_data = self._overlay_to_dict(overlay)
        
        try:
            with open(file_path, 'w') as f:
                yaml.dump(overlay_data, f, default_flow_style=False, indent=2)
            return True
        except Exception:
            return False
    
    def _load_builtin_overlays(self):
        """Load built-in grammar overlays."""
        # NASA C Safety Overlay
        nasa_c_overlay = GrammarOverlay(
            id="nasa_c_safety",
            name="NASA C Safety Profile",
            description="NASA/JPL Power of Ten rules for C code",
            language=LanguageSupport.C,
            rules=[
                OverlayRule(
                    id="nasa_rule_1_goto",
                    name="No goto statements",
                    description="NASA Rule 1: Avoid complex flow constructs like goto",
                    severity="critical",
                    rule_type="ban",
                    target="goto_statement"
                ),
                OverlayRule(
                    id="nasa_rule_1_recursion", 
                    name="No recursion",
                    description="NASA Rule 1: Avoid recursion in safety-critical code",
                    severity="critical",
                    rule_type="ban",
                    target="recursive_function_call"
                ),
                OverlayRule(
                    id="nasa_rule_4_function_size",
                    name="Function size limit",
                    description="NASA Rule 4: Restrict function size to 60 lines",
                    severity="high",
                    rule_type="limit",
                    target="function_lines",
                    parameters={"max_value": 60}
                ),
                OverlayRule(
                    id="nasa_rule_9_pointer_indirection",
                    name="Pointer indirection limit", 
                    description="NASA Rule 9: Limit pointer indirection to one level",
                    severity="high",
                    rule_type="limit",
                    target="pointer_indirection",
                    parameters={"max_value": 1}
                ),
                OverlayRule(
                    id="nasa_rule_9_function_pointers",
                    name="No function pointers",
                    description="NASA Rule 9: Avoid function pointers",
                    severity="high", 
                    rule_type="ban",
                    target="function_pointer"
                )
            ]
        )
        self._overlays["nasa_c_safety"] = nasa_c_overlay
        
        # NASA Python Safety Overlay (adapted rules)
        nasa_python_overlay = GrammarOverlay(
            id="nasa_python_safety",
            name="NASA Python Safety Profile",
            description="NASA/JPL Power of Ten rules adapted for Python",
            language=LanguageSupport.PYTHON,
            rules=[
                OverlayRule(
                    id="nasa_python_exec_eval",
                    name="No exec/eval",
                    description="Python adaptation of NASA Rule 1: No dynamic execution",
                    severity="critical", 
                    rule_type="ban",
                    target="dynamic_execution"
                ),
                OverlayRule(
                    id="nasa_python_function_size",
                    name="Function size limit",
                    description="NASA Rule 4: Restrict function size to 60 lines", 
                    severity="high",
                    rule_type="limit",
                    target="function_lines",
                    parameters={"max_value": 60}
                ),
                OverlayRule(
                    id="nasa_python_recursion_bounded",
                    name="Bounded recursion only",
                    description="Python adaptation: Allow recursion only with depth guards",
                    severity="medium",
                    rule_type="require",
                    target="recursion_depth_guard"
                )
            ]
        )
        self._overlays["nasa_python_safety"] = nasa_python_overlay
        
        # C Macro Restrictions
        c_macro_overlay = GrammarOverlay(
            id="c_macro_restrictions",
            name="C Macro Safety",
            description="Restrict dangerous macro usage",
            language=LanguageSupport.C,
            rules=[
                OverlayRule(
                    id="ban_variadic_macros",
                    name="No variadic macros",
                    description="Ban macros with variable argument lists",
                    severity="medium",
                    rule_type="ban", 
                    target="variadic_macro"
                ),
                OverlayRule(
                    id="ban_token_pasting",
                    name="No token pasting",
                    description="Ban ## token pasting in macros",
                    severity="medium",
                    rule_type="ban",
                    target="token_pasting"
                ),
                OverlayRule(
                    id="macro_complexity_limit",
                    name="Macro complexity limit",
                    description="Limit macro complexity to prevent code obfuscation", 
                    severity="medium",
                    rule_type="limit",
                    target="macro_complexity",
                    parameters={"max_value": 3}
                )
            ]
        )
        self._overlays["c_macro_restrictions"] = c_macro_overlay
    
    def _load_external_overlays(self):
        """Load overlays from external files."""
        if not self.overlay_directory.exists():
            return
        
        for file_path in self.overlay_directory.glob("*.yml"):
            try:
                overlay = self._load_overlay_from_file(file_path)
                if overlay:
                    self._overlays[overlay.id] = overlay
            except Exception:
                # Skip invalid overlay files
                continue
        
        for file_path in self.overlay_directory.glob("*.json"):
            try:
                overlay = self._load_overlay_from_file(file_path)
                if overlay:
                    self._overlays[overlay.id] = overlay
            except Exception:
                continue
    
    def _load_overlay_from_file(self, file_path: Path) -> Optional[GrammarOverlay]:
        """Load overlay from YAML or JSON file."""
        try:
            with open(file_path) as f:
                if file_path.suffix == '.yml' or file_path.suffix == '.yaml':
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            return self._dict_to_overlay(data)
        except Exception:
            return None
    
    def _dict_to_overlay(self, data: Dict[str, Any]) -> GrammarOverlay:
        """Convert dictionary to GrammarOverlay object."""
        rules = []
        for rule_data in data.get('rules', []):
            rule = OverlayRule(
                id=rule_data['id'],
                name=rule_data['name'], 
                description=rule_data['description'],
                severity=rule_data['severity'],
                rule_type=rule_data['rule_type'],
                target=rule_data['target'],
                parameters=rule_data.get('parameters', {})
            )
            rules.append(rule)
        
        return GrammarOverlay(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            language=LanguageSupport(data['language']),
            rules=rules,
            inherits=data.get('inherits', []),
            metadata=data.get('metadata', {})
        )
    
    def _overlay_to_dict(self, overlay: GrammarOverlay) -> Dict[str, Any]:
        """Convert GrammarOverlay to dictionary for serialization."""
        rules_data = []
        for rule in overlay.rules:
            rule_data = {
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'severity': rule.severity,
                'rule_type': rule.rule_type,
                'target': rule.target,
                'parameters': rule.parameters
            }
            rules_data.append(rule_data)
        
        return {
            'id': overlay.id,
            'name': overlay.name,
            'description': overlay.description,
            'language': overlay.language.value,
            'rules': rules_data,
            'inherits': overlay.inherits,
            'metadata': overlay.metadata
        }
    
    def _check_rule_against_nodes(self, rule: OverlayRule, ast_nodes: List[Any]) -> List[Dict[str, Any]]:
        """Check a single rule against AST nodes."""
        violations = []
        
        for node in ast_nodes:
            violation = self._check_rule_against_node(rule, node)
            if violation:
                violations.append(violation)
        
        return violations
    
    def _check_rule_against_node(self, rule: OverlayRule, node: Any) -> Optional[Dict[str, Any]]:
        """Check rule against a single AST node."""
        # This would implement specific rule checking logic
        # For now, we'll do basic pattern matching
        
        if not hasattr(node, 'type'):
            return None
        
        if rule.rule_type == 'ban' and node.type == rule.target:
            return {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "severity": rule.severity,
                "message": f"Banned construct: {rule.target}",
                "line": getattr(node, 'start_point', (0, 0))[0] + 1,
                "column": getattr(node, 'start_point', (0, 0))[1],
                "type": "overlay_violation"
            }
        
        # Add more rule checking logic here
        
        return None