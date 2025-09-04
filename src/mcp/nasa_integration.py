#!/usr/bin/env python3
"""
NASA Power of Ten Rules Integration
===================================

This module provides integration between the MCP server and NASA Power of Ten rules
for safety-critical software development. It checks violations against NASA rules
and provides context for AI-powered fixes.

The 10 Power of Ten Rules:
1. Avoid complex flow constructs (goto, recursion)
2. All loops must have fixed upper bounds
3. Do not use the heap after initialization
4. No function longer than 60 lines (single sheet of paper)
5. At least 2 runtime assertions per function
6. Declare data objects at smallest scope
7. Check return value of all non-void functions
8. Limit preprocessor use
9. Restrict pointer use (max 1 level indirection)
10. Compile with all warnings enabled, treat warnings as errors

Author: Connascence Safety Analyzer Team
"""

import os
import yaml
from typing import Dict, List, Any, Optional, Set
from pathlib import Path


class NASAPowerOfTenIntegration:
    """Integration layer for NASA Power of Ten rules with connascence analysis."""
    
    def __init__(self, rules_config_path: Optional[str] = None):
        self.rules_config = None
        self.rule_mappings = {}
        self.load_rules_configuration(rules_config_path)
    
    def load_rules_configuration(self, config_path: Optional[str] = None):
        """Load NASA Power of Ten rules configuration."""
        if config_path is None:
            # Default to policy presets directory
            policy_dir = Path(__file__).parent.parent / "policy" / "presets"
            config_path = policy_dir / "nasa_power_of_ten.yml"
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.rules_config = yaml.safe_load(f)
                self._build_rule_mappings()
            else:
                print(f"Warning: NASA Power of Ten config not found at {config_path}")
                self._load_default_rules()
        except Exception as e:
            print(f"Error loading NASA rules config: {e}")
            self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default NASA Power of Ten rules if config file unavailable."""
        self.rules_config = {
            'name': 'NASA Power of Ten Rules (Default)',
            'rules': {
                'nasa_rule_1': {
                    'title': 'Avoid complex flow constructs',
                    'description': 'Avoid goto and recursion',
                    'severity': 'critical'
                },
                'nasa_rule_2': {
                    'title': 'All loops must have fixed upper bounds',
                    'description': 'Statically determinable loop bounds',
                    'severity': 'critical'
                },
                'nasa_rule_3': {
                    'title': 'Do not use heap after initialization',
                    'description': 'Avoid dynamic allocation',
                    'severity': 'critical'
                },
                'nasa_rule_4': {
                    'title': 'Restrict function size',
                    'description': 'Max 60 lines per function',
                    'severity': 'high'
                },
                'nasa_rule_5': {
                    'title': 'Use at least 2 assertions per function',
                    'description': 'Runtime verification',
                    'severity': 'high'
                },
                'nasa_rule_6': {
                    'title': 'Declare data objects at smallest scope',
                    'description': 'Minimize scope',
                    'severity': 'medium'
                },
                'nasa_rule_7': {
                    'title': 'Check return values',
                    'description': 'Validate all non-void returns',
                    'severity': 'high'
                },
                'nasa_rule_8': {
                    'title': 'Limit preprocessor use',
                    'description': 'Simple macros only',
                    'severity': 'medium'
                },
                'nasa_rule_9': {
                    'title': 'Restrict pointer use',
                    'description': 'Max 1 level indirection',
                    'severity': 'high'
                },
                'nasa_rule_10': {
                    'title': 'Compile with all warnings',
                    'description': 'Warnings as errors',
                    'severity': 'critical'
                }
            }
        }
        self._build_rule_mappings()
    
    def _build_rule_mappings(self):
        """Build mappings between connascence violations and NASA rules."""
        if not self.rules_config:
            return
            
        # Map connascence types to NASA rules
        self.rule_mappings = {
            # Connascence of Algorithm -> NASA Rules 1, 4
            'algorithm': ['nasa_rule_1', 'nasa_rule_4'],
            'god_object': ['nasa_rule_4'],
            'recursive_function': ['nasa_rule_1'],
            
            # Connascence of Position -> NASA Rule 6
            'position': ['nasa_rule_6'],
            'variable_scope': ['nasa_rule_6'],
            
            # Connascence of Meaning -> NASA Rules 5, 7, 8
            'meaning': ['nasa_rule_5', 'nasa_rule_7', 'nasa_rule_8'],
            'magic_literal': ['nasa_rule_8'],
            'unchecked_return': ['nasa_rule_7'],
            
            # Connascence of Timing -> NASA Rule 3
            'timing': ['nasa_rule_3'],
            'heap_allocation': ['nasa_rule_3'],
            
            # Connascence of Execution -> NASA Rules 1, 2
            'execution': ['nasa_rule_1', 'nasa_rule_2'],
            'unbounded_loop': ['nasa_rule_2'],
            'goto_statement': ['nasa_rule_1'],
            
            # General violations
            'compiler_warning': ['nasa_rule_10'],
            'complex_macro': ['nasa_rule_8'],
            'multiple_pointers': ['nasa_rule_9']
        }
    
    def check_nasa_violations(self, violation: Dict[str, Any], 
                            context_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Check if a connascence violation also violates NASA Power of Ten rules.
        
        Args:
            violation: The connascence violation to check
            context_data: Additional context from analysis
            
        Returns:
            List of NASA rule violations found
        """
        nasa_violations = []
        
        violation_type = violation.get('type', '').lower()
        
        # Get applicable NASA rules for this violation type
        applicable_rules = self.rule_mappings.get(violation_type, [])
        
        for rule_id in applicable_rules:
            rule_config = self.rules_config['rules'].get(rule_id, {})
            if not rule_config:
                continue
                
            # Perform specific checks based on rule
            violation_details = self._check_specific_rule(rule_id, violation, context_data)
            
            if violation_details:
                nasa_violation = {
                    'rule_id': rule_id,
                    'rule_title': rule_config.get('title', 'Unknown Rule'),
                    'rule_description': rule_config.get('description', ''),
                    'severity': rule_config.get('severity', 'medium'),
                    'violation_details': violation_details,
                    'connascence_violation_id': violation.get('id', 'unknown')
                }
                nasa_violations.append(nasa_violation)
        
        return nasa_violations
    
    def _check_specific_rule(self, rule_id: str, violation: Dict[str, Any], 
                           context_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Check specific NASA rule against violation."""
        context = context_data or {}
        
        if rule_id == 'nasa_rule_1':  # Complex flow constructs
            return self._check_rule_1(violation, context)
        elif rule_id == 'nasa_rule_2':  # Loop bounds
            return self._check_rule_2(violation, context)
        elif rule_id == 'nasa_rule_3':  # Heap after init
            return self._check_rule_3(violation, context)
        elif rule_id == 'nasa_rule_4':  # Function size
            return self._check_rule_4(violation, context)
        elif rule_id == 'nasa_rule_5':  # Assertions
            return self._check_rule_5(violation, context)
        elif rule_id == 'nasa_rule_6':  # Variable scope
            return self._check_rule_6(violation, context)
        elif rule_id == 'nasa_rule_7':  # Return values
            return self._check_rule_7(violation, context)
        elif rule_id == 'nasa_rule_8':  # Preprocessor
            return self._check_rule_8(violation, context)
        elif rule_id == 'nasa_rule_9':  # Pointers
            return self._check_rule_9(violation, context)
        elif rule_id == 'nasa_rule_10':  # Compiler warnings
            return self._check_rule_10(violation, context)
        
        return None
    
    def _check_rule_1(self, violation, context) -> Optional[Dict]:
        """Check Rule 1: Avoid complex flow constructs."""
        if violation.get('type') in ['algorithm', 'recursive_function']:
            return {
                'check': 'complex_flow_constructs',
                'details': 'Complex algorithm or recursive function detected',
                'recommendation': 'Convert to iterative solution or simplify control flow'
            }
        return None
    
    def _check_rule_2(self, violation, context) -> Optional[Dict]:
        """Check Rule 2: All loops must have fixed upper bounds."""
        if 'loop' in violation.get('message', '').lower() or violation.get('type') == 'execution':
            return {
                'check': 'loop_bounds',
                'details': 'Potentially unbounded loop detected',
                'recommendation': 'Add explicit loop bounds or counter limits'
            }
        return None
    
    def _check_rule_3(self, violation, context) -> Optional[Dict]:
        """Check Rule 3: Do not use heap after initialization."""
        message = violation.get('message', '').lower()
        if any(word in message for word in ['malloc', 'new', 'alloc', 'free']):
            return {
                'check': 'heap_usage',
                'details': 'Dynamic memory allocation detected',
                'recommendation': 'Use static allocation or pre-allocated memory pools'
            }
        return None
    
    def _check_rule_4(self, violation, context) -> Optional[Dict]:
        """Check Rule 4: Restrict function size."""
        if violation.get('type') in ['algorithm', 'god_object']:
            # Check if we have line count information
            lines = context.get('function_lines', 0)
            if lines > 60:
                return {
                    'check': 'function_size',
                    'details': f'Function has {lines} lines (exceeds 60 line limit)',
                    'recommendation': 'Break function into smaller, focused functions'
                }
            else:
                return {
                    'check': 'function_complexity',
                    'details': 'Complex function detected (possible size issue)',
                    'recommendation': 'Review function size and complexity'
                }
        return None
    
    def _check_rule_5(self, violation, context) -> Optional[Dict]:
        """Check Rule 5: Use at least 2 assertions per function."""
        if violation.get('type') == 'meaning':
            return {
                'check': 'assertions',
                'details': 'Function may lack sufficient runtime assertions',
                'recommendation': 'Add precondition and postcondition assertions'
            }
        return None
    
    def _check_rule_6(self, violation, context) -> Optional[Dict]:
        """Check Rule 6: Declare data objects at smallest scope."""
        if violation.get('type') == 'position':
            return {
                'check': 'variable_scope',
                'details': 'Variable scope may be too wide',
                'recommendation': 'Move variable declarations closer to point of use'
            }
        return None
    
    def _check_rule_7(self, violation, context) -> Optional[Dict]:
        """Check Rule 7: Check return values."""
        if 'return' in violation.get('message', '').lower() or violation.get('type') == 'meaning':
            return {
                'check': 'return_values',
                'details': 'Unchecked return value or meaning violation',
                'recommendation': 'Check all function return values or cast to void with comment'
            }
        return None
    
    def _check_rule_8(self, violation, context) -> Optional[Dict]:
        """Check Rule 8: Limit preprocessor use."""
        message = violation.get('message', '').lower()
        if any(word in message for word in ['macro', 'define', '#']):
            return {
                'check': 'preprocessor',
                'details': 'Complex preprocessor usage detected',
                'recommendation': 'Replace complex macros with inline functions'
            }
        return None
    
    def _check_rule_9(self, violation, context) -> Optional[Dict]:
        """Check Rule 9: Restrict pointer use."""
        message = violation.get('message', '').lower()
        if any(word in message for word in ['pointer', 'ptr', '**']):
            return {
                'check': 'pointer_usage',
                'details': 'Multiple pointer indirection detected',
                'recommendation': 'Limit to single level of pointer indirection'
            }
        return None
    
    def _check_rule_10(self, violation, context) -> Optional[Dict]:
        """Check Rule 10: Compile with all warnings."""
        # This would typically be checked during build process
        return {
            'check': 'compiler_warnings',
            'details': 'Ensure all compiler warnings are enabled and treated as errors',
            'recommendation': 'Enable -Wall -Wextra -Werror compiler flags'
        }
    
    def get_nasa_rules_context(self, violation: Dict[str, Any]) -> str:
        """
        Generate NASA Power of Ten context for AI prompts.
        
        Args:
            violation: The connascence violation
            
        Returns:
            Formatted context string with applicable NASA rules
        """
        applicable_rules = self.rule_mappings.get(violation.get('type', ''), [])
        
        if not applicable_rules:
            return "**NASA POWER OF TEN RULES**: No specific rules apply to this violation type.\n"
        
        context_lines = ["**NASA POWER OF TEN RULES CONTEXT**:\n"]
        
        for rule_id in applicable_rules:
            rule_config = self.rules_config['rules'].get(rule_id, {})
            if rule_config:
                rule_num = rule_id.replace('nasa_rule_', '')
                context_lines.append(f"**Rule {rule_num}**: {rule_config.get('title', 'Unknown')}")
                context_lines.append(f"- Description: {rule_config.get('description', 'No description')}")
                context_lines.append(f"- Severity: {rule_config.get('severity', 'medium').upper()}")
                context_lines.append("")
        
        return "\n".join(context_lines)
    
    def calculate_nasa_compliance_score(self, nasa_violations: List[Dict[str, Any]]) -> float:
        """
        Calculate NASA compliance score based on violations found.
        
        Args:
            nasa_violations: List of NASA rule violations
            
        Returns:
            Compliance score from 0.0 (non-compliant) to 1.0 (fully compliant)
        """
        if not nasa_violations:
            return 1.0  # Perfect compliance
        
        # Weight violations by severity
        severity_weights = {
            'critical': 0.3,  # Critical violations heavily impact score
            'high': 0.2,
            'medium': 0.1,
            'low': 0.05
        }
        
        total_penalty = 0.0
        for violation in nasa_violations:
            severity = violation.get('severity', 'medium')
            penalty = severity_weights.get(severity, 0.1)
            total_penalty += penalty
        
        # Calculate compliance score (capped at 0.0)
        compliance_score = max(0.0, 1.0 - total_penalty)
        return compliance_score
    
    def get_nasa_compliance_actions(self, nasa_violations: List[Dict[str, Any]]) -> List[str]:
        """
        Get specific actions needed for NASA compliance.
        
        Args:
            nasa_violations: List of NASA rule violations
            
        Returns:
            List of actionable recommendations
        """
        actions = []
        
        for violation in nasa_violations:
            rule_title = violation.get('rule_title', 'Unknown Rule')
            recommendation = violation.get('violation_details', {}).get('recommendation', 'Review code')
            actions.append(f"{rule_title}: {recommendation}")
        
        return actions
    
    def get_all_nasa_rules(self) -> Dict[str, Any]:
        """Get all NASA Power of Ten rules configuration."""
        return self.rules_config
    
    def is_nasa_compliant(self, nasa_violations: List[Dict[str, Any]], 
                         threshold: float = 0.9) -> bool:
        """
        Check if code is NASA compliant based on violations.
        
        Args:
            nasa_violations: List of violations found
            threshold: Minimum compliance score required (default 0.9)
            
        Returns:
            True if compliant, False otherwise
        """
        compliance_score = self.calculate_nasa_compliance_score(nasa_violations)
        return compliance_score >= threshold


# Global instance for use by MCP server
nasa_integration = NASAPowerOfTenIntegration()