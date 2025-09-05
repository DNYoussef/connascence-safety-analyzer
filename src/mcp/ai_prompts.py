"""
MCP AI Prompt System with Enhanced Technical Context

Provides comprehensive AI context for connascence violations including:
- Full technical context (file paths, line numbers, code snippets)
- NASA Power of Ten rule guidance and compliance status
- Before/after code examples with explanations  
- Safety tier classifications and risk assessments
- Multi-file refactoring impact analysis
- Step-by-step implementation guidance

This system integrates with the MCP control loop to provide AI agents with
everything needed for intelligent, safety-aware code refactoring.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path
import re

# Import our existing systems for integration
try:
    from autofix.tier_classifier import AutofixTierClassifier, SafetyTier
    from autofix.patch_generator import PatchGenerator  
except ImportError:
    # Fallback for when imports aren't available
    class SafetyTier:
        TIER_C_AUTO = "tier_c_auto"
        TIER_B_REVIEW = "tier_b_review"
        TIER_A_MANUAL = "tier_a_manual"
        UNSAFE = "unsafe"

@dataclass
class AIContext:
    """Complete AI context for a violation or refactoring task"""
    violation_context: Dict[str, Any]
    fix_strategy: Dict[str, Any]
    implementation_guide: Dict[str, Any]
    safety_assessment: Dict[str, Any]
    nasa_guidance: Dict[str, Any]
    code_examples: Dict[str, Any]
    refactoring_patterns: List[str]
    risk_factors: List[str]
    confidence_score: float

class MCPPromptSystem:
    """
    Enhanced AI prompt system for MCP server with comprehensive technical context.
    
    Provides rich, contextual prompts that include file paths, NASA compliance,
    code examples, safety assessments, and step-by-step guidance for AI agents.
    """
    
    def __init__(self):
        # Initialize integrated systems
        try:
            self.tier_classifier = AutofixTierClassifier()
            self.patch_generator = PatchGenerator()
        except:
            self.tier_classifier = None
            self.patch_generator = None
        
        # NASA Power of Ten Rules (complete reference)
        self.nasa_rules = {
            1: {
                'rule': 'Avoid complex flow constructs, such as goto and recursion.',
                'rationale': 'Restricts the procedural call tree and makes code predictable',
                'compliance_check': lambda code: 'goto' not in code.lower() and self._check_recursion_depth(code) < 3
            },
            2: {
                'rule': 'All loops must have fixed bounds.',
                'rationale': 'Prevents runaway code and ensures deterministic execution',
                'compliance_check': lambda code: not re.search(r'while.*(?!.*break)', code)
            },
            3: {
                'rule': 'Avoid heap memory allocation.',
                'rationale': 'Prevents memory leaks and non-deterministic behavior',
                'compliance_check': lambda code: not any(word in code for word in ['malloc', 'new', 'alloc'])
            },
            4: {
                'rule': 'Restrict functions to a single printed page (60 lines).',
                'rationale': 'Ensures functions are testable and understandable',
                'compliance_check': lambda code: code.count('\n') <= 60
            },
            5: {
                'rule': 'Use a minimum of two runtime assertions per function.',
                'rationale': 'Increases software reliability and catches errors early',
                'compliance_check': lambda code: code.count('assert') >= 2 or code.count('if') >= 2
            },
            6: {
                'rule': 'Restrict the scope of data to the smallest possible.',
                'rationale': 'Reduces coupling and improves maintainability',
                'compliance_check': lambda code: 'global' not in code.lower()
            },
            7: {
                'rule': 'Check the return value of all non-void functions.',
                'rationale': 'Ensures error conditions are handled properly',
                'compliance_check': lambda code: self._check_return_values(code)
            },
            8: {
                'rule': 'Use the preprocessor sparingly.',
                'rationale': 'Improves code readability and debuggability',
                'compliance_check': lambda code: code.count('#') <= 5
            },
            9: {
                'rule': 'Limit pointer use to a single dereference.',
                'rationale': 'Reduces complexity and potential for errors',
                'compliance_check': lambda code: not re.search(r'\*\*+', code)
            },
            10: {
                'rule': 'Compile with all possible warnings active.',
                'rationale': 'Static analysis tools catch many bugs before runtime',
                'compliance_check': lambda code: True  # This is a compilation flag
            }
        }
        
        # Connascence type explanations with examples
        self.connascence_explanations = {
            'connascence_of_name': {
                'description': 'Multiple components must agree on the name of an entity',
                'examples': {
                    'bad': 'user.getName() vs user.get_name()',
                    'good': 'Consistent naming: user.getName() everywhere'
                },
                'refactoring_patterns': ['Rename Method', 'Rename Variable', 'Extract Interface']
            },
            'connascence_of_type': {
                'description': 'Multiple components must agree on the type of an entity',
                'examples': {
                    'bad': 'Function expects string, caller passes int',
                    'good': 'Type-safe interfaces with proper validation'
                },
                'refactoring_patterns': ['Introduce Type Safety', 'Extract Parameter Object']
            },
            'connascence_of_meaning': {
                'description': 'Multiple components must agree on the meaning of specific values',
                'examples': {
                    'bad': 'if (status == 1) // what does 1 mean?',
                    'good': 'if (status == STATUS_ACTIVE) // clear meaning'
                },
                'refactoring_patterns': ['Replace Magic Number', 'Extract Constant', 'Introduce Enum']
            },
            'connascence_of_position': {
                'description': 'Multiple components must agree on the order of values',
                'examples': {
                    'bad': 'createUser(name, email, age, role, dept, salary)',
                    'good': 'createUser(UserConfig config)'
                },
                'refactoring_patterns': ['Introduce Parameter Object', 'Named Parameters']
            },
            'connascence_of_algorithm': {
                'description': 'Multiple components must agree on a particular algorithm',
                'examples': {
                    'bad': 'Identical complex logic duplicated across classes',
                    'good': 'Shared algorithm extracted to single location'
                },
                'refactoring_patterns': ['Extract Method', 'Strategy Pattern', 'Template Method']
            },
            'god_object': {
                'description': 'A class that knows too much or does too much',
                'examples': {
                    'bad': 'UserManager: validate, save, email, report, backup, etc.',
                    'good': 'UserValidator, UserRepository, EmailService, etc.'
                },
                'refactoring_patterns': ['Extract Class', 'Single Responsibility', 'Facade Pattern']
            }
        }
    
    def generate_violation_context(self, violation: Dict[str, Any], 
                                 file_context: Dict[str, Any],
                                 code_context: str = "") -> AIContext:
        """
        Generate comprehensive AI context for a specific violation.
        
        Args:
            violation: Violation details (type, location, severity, etc.)
            file_context: File metadata (path, size, complexity, etc.)
            code_context: Surrounding code context
            
        Returns:
            AIContext with complete technical and safety information
        """
        
        violation_type = violation.get('type', 'unknown')
        file_path = violation.get('file_path', 'unknown')
        line_number = violation.get('line_number', 0)
        
        # Generate violation context
        violation_context = {
            'file_path': file_path,
            'file_name': Path(file_path).name,
            'line_number': line_number,
            'violation_type': violation_type,
            'severity': violation.get('severity', 'medium'),
            'code_context': code_context,
            'surrounding_lines': self._get_surrounding_lines(code_context, line_number),
            'class_name': violation.get('class_name'),
            'function_name': violation.get('function_name'),
            'module_path': str(Path(file_path).parent)
        }
        
        # Analyze safety and NASA compliance
        safety_assessment = self._assess_safety(violation, code_context)
        nasa_guidance = self._generate_nasa_guidance(violation, code_context)
        
        # Generate fix strategy
        fix_strategy = self._generate_fix_strategy(violation_type, violation_context)
        
        # Generate implementation guide
        implementation_guide = self._generate_implementation_guide(violation_type, fix_strategy, safety_assessment)
        
        # Get code examples
        code_examples = self._generate_code_examples(violation_type, code_context)
        
        # Determine refactoring patterns
        refactoring_patterns = self.connascence_explanations.get(violation_type, {}).get('refactoring_patterns', [])
        
        # Assess risk factors
        risk_factors = self._assess_risk_factors(violation, file_context)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(violation, safety_assessment)
        
        return AIContext(
            violation_context=violation_context,
            fix_strategy=fix_strategy,
            implementation_guide=implementation_guide,
            safety_assessment=safety_assessment,
            nasa_guidance=nasa_guidance,
            code_examples=code_examples,
            refactoring_patterns=refactoring_patterns,
            risk_factors=risk_factors,
            confidence_score=confidence_score
        )
    
    def generate_refactoring_strategy_prompt(self, violation_type: str, 
                                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic refactoring guidance based on VS Code prompts"""
        
        if violation_type == 'magic_literal':
            return self._generate_magic_literal_strategy(context)
        elif violation_type == 'god_object':
            return self._generate_god_object_strategy(context)
        elif violation_type == 'connascence_of_position':
            return self._generate_parameter_strategy(context)
        elif 'connascence' in violation_type:
            return self._generate_connascence_strategy(violation_type, context)
        else:
            return self._generate_generic_strategy(violation_type, context)
    
    def generate_planning_prompts(self, violations: List[Dict[str, Any]], 
                                architectural_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meta-planning prompts for architectural decisions"""
        
        # Analyze violation patterns
        violation_patterns = self._analyze_violation_patterns(violations)
        
        # Identify architectural smells
        architectural_issues = self._identify_architectural_issues(violations, architectural_context)
        
        # Generate planning strategy
        planning_strategy = {
            'root_causes': self._identify_root_causes(violation_patterns),
            'leverage_points': self._identify_leverage_points(violations),
            'refactoring_sequence': self._plan_refactoring_sequence(violations),
            'risk_mitigation': self._plan_risk_mitigation(violations),
            'nasa_compliance_plan': self._plan_nasa_compliance(violations)
        }
        
        return {
            'violation_patterns': violation_patterns,
            'architectural_issues': architectural_issues,
            'planning_strategy': planning_strategy,
            'recommended_approach': self._recommend_approach(planning_strategy),
            'pr_breakdown': self._suggest_pr_breakdown(planning_strategy)
        }
    
    def generate_ai_agent_context(self, violation: Dict[str, Any], 
                                 full_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete context for external AI agents.
        
        This is the key integration point that provides everything an AI agent
        needs for intelligent, safety-aware code generation.
        """
        
        ai_context = self.generate_violation_context(
            violation, 
            full_context.get('file_context', {}),
            full_context.get('code_context', '')
        )
        
        # Format for AI agent consumption
        return {
            # Technical Context
            'file_path': ai_context.violation_context['file_path'],
            'line_number': ai_context.violation_context['line_number'], 
            'violation_type': ai_context.violation_context['violation_type'],
            'code_context': ai_context.violation_context['code_context'],
            
            # Safety Assessment
            'nasa_rule_violated': ai_context.nasa_guidance.get('violated_rules', []),
            'nasa_compliant': ai_context.safety_assessment.get('nasa_compliant', True),
            'safety_tier': ai_context.safety_assessment.get('safety_tier', 'tier_b_review'),
            
            # Fix Guidance
            'fix_examples': ai_context.code_examples,
            'before_code': ai_context.code_examples.get('before', ''),
            'after_code': ai_context.code_examples.get('after', ''),
            'explanation': ai_context.fix_strategy.get('explanation', ''),
            
            # Implementation Steps
            'implementation_steps': ai_context.implementation_guide.get('steps', []),
            'refactoring_patterns': ai_context.refactoring_patterns,
            'risk_factors': ai_context.risk_factors,
            
            # NASA Coding Style Guide
            'nasa_coding_style_rules': self._format_nasa_rules_for_ai(),
            'compliance_requirements': ai_context.nasa_guidance.get('requirements', []),
            
            # Multi-file Context
            'affected_files': ai_context.implementation_guide.get('affected_files', []),
            'impact_analysis': ai_context.implementation_guide.get('impact_analysis', {}),
            
            # Confidence and Quality
            'confidence_score': ai_context.confidence_score,
            'estimated_effort': ai_context.implementation_guide.get('estimated_effort', 'medium'),
            'review_required': ai_context.safety_assessment.get('safety_tier') != 'tier_c_auto'
        }
    
    # Enhanced strategy methods (copied and improved from VS Code)
    
    def _generate_magic_literal_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced magic literal refactoring strategy"""
        
        return {
            'title': 'Magic Literal Extraction Strategy',
            'pattern': 'Replace Magic Number/String with Named Constant',
            'explanation': 'Extract magic literals to named constants for better readability and maintainability',
            'approach': 'Extract Constant refactoring pattern',
            'benefits': [
                'Improves code readability and self-documentation',
                'Centralizes literal values for easier maintenance', 
                'Reduces connascence of meaning',
                'Enables easier testing and configuration'
            ],
            'considerations': [
                'Choose descriptive constant names that explain the meaning',
                'Place constants at appropriate scope (module, class, or function level)',
                'Group related constants together',
                'Consider using enums for related constant sets'
            ],
            'nasa_compliance': 'Preserves all NASA Power of Ten rules',
            'safety_impact': 'Low risk - improves code clarity without changing behavior'
        }
    
    def _generate_god_object_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced god object refactoring strategy"""
        
        return {
            'title': 'God Object Decomposition Strategy', 
            'pattern': 'Single Responsibility Principle + Extract Class',
            'explanation': 'Break down god object into smaller, focused classes with single responsibilities',
            'approach': 'Systematic responsibility extraction',
            'benefits': [
                'Improves maintainability and testability',
                'Reduces coupling and increases cohesion',
                'Enables parallel development',
                'Follows SOLID principles'
            ],
            'decomposition_strategy': [
                'Identify distinct responsibilities within the class',
                'Extract data access logic to Repository classes',
                'Extract business logic to Service classes',
                'Extract validation logic to Validator classes',
                'Keep only coordination logic in original class'
            ],
            'nasa_compliance': 'Helps comply with NASA Rule 4 (function size) and Rule 6 (data scope)',
            'safety_impact': 'High risk - requires careful dependency analysis and testing'
        }
    
    def _generate_parameter_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced parameter position refactoring strategy"""
        
        return {
            'title': 'Parameter Position Refactoring Strategy',
            'pattern': 'Introduce Parameter Object or Named Parameters',
            'explanation': 'Replace long parameter lists with parameter objects or named parameters',
            'approach': 'Parameter object pattern or named parameter pattern',
            'benefits': [
                'Reduces parameter coupling (connascence of position)',
                'Improves API usability and readability',
                'Makes function calls less error-prone',
                'Enables easier parameter validation'
            ],
            'implementation_options': [
                'Parameter Object: Create a class/struct to hold parameters',
                'Named Parameters: Use dictionary or keyword arguments',
                'Builder Pattern: Fluent interface for parameter construction',
                'Configuration Object: Centralize related parameters'
            ],
            'nasa_compliance': 'Supports NASA Rule 4 (readable functions) and Rule 6 (data scope)',
            'safety_impact': 'Medium risk - requires updating all call sites'
        }
    
    def _assess_safety(self, violation: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """Assess safety implications and tier classification"""
        
        # Use tier classifier if available
        if self.tier_classifier:
            try:
                classification = self.tier_classifier.classify_autofix(
                    violation.get('type', ''),
                    code_context,
                    violation.get('file_path', ''),
                    f"Fix {violation.get('type', 'unknown')} violation"
                )
                
                return {
                    'safety_tier': classification.tier.value,
                    'confidence': classification.confidence,
                    'nasa_compliant': classification.nasa_compliance,
                    'risk_factors': classification.risk_factors,
                    'safety_checks': classification.safety_checks,
                    'estimated_impact': classification.estimated_impact
                }
            except:
                pass
        
        # Fallback safety assessment
        return {
            'safety_tier': 'tier_b_review',
            'confidence': 0.7,
            'nasa_compliant': True,
            'risk_factors': ['requires_review'],
            'safety_checks': ['manual_verification_needed'],
            'estimated_impact': 'medium'
        }
    
    def _generate_nasa_guidance(self, violation: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """Generate NASA Power of Ten compliance guidance"""
        
        violated_rules = []
        requirements = []
        
        # Check each NASA rule against the violation
        violation_type = violation.get('type', '')
        
        if violation_type == 'god_object':
            violated_rules.append(4)  # Function size
            violated_rules.append(6)  # Data scope
            requirements.extend([
                'Break large functions into smaller, testable units',
                'Limit data scope to smallest necessary'
            ])
        
        if violation_type == 'magic_literal':
            # Magic literals can violate readability but don't directly violate NASA rules
            requirements.append('Use named constants to improve code clarity')
        
        if 'unbounded_loop' in violation_type:
            violated_rules.append(2)  # Bounded loops
            requirements.append('All loops must have fixed, deterministic bounds')
        
        if 'dynamic_allocation' in violation_type:
            violated_rules.append(3)  # Heap allocation
            requirements.append('Avoid dynamic memory allocation - use stack allocation')
        
        return {
            'violated_rules': violated_rules,
            'requirements': requirements,
            'compliance_status': 'compliant' if not violated_rules else 'violations_detected',
            'rule_details': {rule: self.nasa_rules[rule] for rule in violated_rules if rule in self.nasa_rules}
        }
    
    def _format_nasa_rules_for_ai(self) -> str:
        """Format NASA rules as coding style guide for AI agents"""
        
        rules_text = "NASA Power of Ten Coding Rules (Safety-Critical Style Guide):\n\n"
        
        for rule_num, rule_data in self.nasa_rules.items():
            rules_text += f"{rule_num}. {rule_data['rule']}\n"
            rules_text += f"   Rationale: {rule_data['rationale']}\n\n"
        
        rules_text += "\nAlways follow these rules when generating or modifying code for safety-critical systems."
        
        return rules_text
    
    # Helper methods
    
    def _get_surrounding_lines(self, code_context: str, line_number: int, context_lines: int = 3) -> Dict[str, str]:
        """Get surrounding lines of code for context"""
        
        if not code_context:
            return {'before': '', 'target': '', 'after': ''}
        
        lines = code_context.split('\n')
        target_line = max(0, line_number - 1)  # Convert to 0-based
        
        before_start = max(0, target_line - context_lines)
        after_end = min(len(lines), target_line + context_lines + 1)
        
        return {
            'before': '\n'.join(lines[before_start:target_line]),
            'target': lines[target_line] if target_line < len(lines) else '',
            'after': '\n'.join(lines[target_line + 1:after_end])
        }
    
    def _generate_fix_strategy(self, violation_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fix strategy based on violation type"""
        
        explanation = self.connascence_explanations.get(violation_type, {})
        
        return {
            'violation_description': explanation.get('description', f'Fix {violation_type} violation'),
            'examples': explanation.get('examples', {}),
            'recommended_patterns': explanation.get('refactoring_patterns', []),
            'explanation': f"Address {violation_type} through appropriate refactoring patterns"
        }
    
    def _generate_implementation_guide(self, violation_type: str, 
                                     fix_strategy: Dict[str, Any],
                                     safety_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate step-by-step implementation guide"""
        
        if violation_type == 'magic_literal':
            steps = [
                'Identify the magic literal and its usage context',
                'Choose a descriptive constant name that explains the meaning',
                'Add constant definition at appropriate scope level',
                'Replace literal usage with constant reference',
                'Verify no other instances need updating',
                'Run tests to ensure behavior is preserved'
            ]
        elif violation_type == 'god_object':
            steps = [
                'Analyze class responsibilities and identify distinct concerns',
                'Plan extraction strategy (which methods/data go together)',
                'Create new classes for extracted responsibilities',
                'Move methods and data to appropriate classes',
                'Update references and dependency injection',
                'Run comprehensive tests and integration tests'
            ]
        else:
            steps = [
                f'Analyze the {violation_type} violation context',
                'Plan the refactoring approach',
                'Implement the changes incrementally',
                'Test at each step to ensure correctness',
                'Verify NASA Power of Ten compliance'
            ]
        
        return {
            'steps': steps,
            'estimated_effort': self._estimate_effort(violation_type),
            'affected_files': [fix_strategy.get('file_path', 'current_file')],
            'impact_analysis': {
                'breaking_changes': safety_assessment.get('estimated_impact', 'low') in ['high', 'significant'],
                'test_impact': 'requires_test_updates' if violation_type == 'god_object' else 'minimal_test_impact',
                'deployment_risk': safety_assessment.get('safety_tier', 'tier_b_review')
            }
        }
    
    def _generate_code_examples(self, violation_type: str, code_context: str) -> Dict[str, str]:
        """Generate before/after code examples"""
        
        # Use tier classifier examples if available
        if self.tier_classifier:
            examples = self.tier_classifier.get_autofix_examples(violation_type)
            if examples:
                return examples
        
        # Use connascence examples
        explanation = self.connascence_explanations.get(violation_type, {})
        examples = explanation.get('examples', {})
        
        if examples:
            return {
                'before': examples.get('bad', '// Original code with violation'),
                'after': examples.get('good', '// Refactored code addressing violation'),
                'explanation': f'Fix {violation_type} through proper refactoring'
            }
        
        # Generic examples
        return {
            'before': '// Code with violation',
            'after': '// Refactored code', 
            'explanation': f'Address {violation_type} violation'
        }
    
    def _assess_risk_factors(self, violation: Dict[str, Any], file_context: Dict[str, Any]) -> List[str]:
        """Assess risk factors for the refactoring"""
        
        risks = []
        
        if violation.get('severity') == 'critical':
            risks.append('high_severity_violation')
        
        if violation.get('type') == 'god_object':
            risks.append('architectural_change_required')
            risks.append('multiple_file_impact')
        
        if file_context.get('is_public_api', False):
            risks.append('public_api_change')
        
        if file_context.get('test_coverage', 1.0) < 0.8:
            risks.append('insufficient_test_coverage')
        
        return risks
    
    def _calculate_confidence(self, violation: Dict[str, Any], safety_assessment: Dict[str, Any]) -> float:
        """Calculate confidence score for the fix"""
        
        base_confidence = 0.8
        
        # Adjust based on violation type
        if violation.get('type') == 'magic_literal':
            base_confidence = 0.95  # High confidence for simple fixes
        elif violation.get('type') == 'god_object':
            base_confidence = 0.6   # Lower confidence for complex refactoring
        
        # Adjust based on safety assessment
        if safety_assessment.get('safety_tier') == 'tier_c_auto':
            base_confidence += 0.1
        elif safety_assessment.get('safety_tier') == 'unsafe':
            base_confidence -= 0.3
        
        return max(0.1, min(1.0, base_confidence))
    
    def _estimate_effort(self, violation_type: str) -> str:
        """Estimate implementation effort"""
        
        effort_map = {
            'magic_literal': 'low',
            'connascence_of_name': 'low', 
            'connascence_of_type': 'medium',
            'connascence_of_position': 'medium',
            'god_object': 'high',
            'connascence_of_algorithm': 'high'
        }
        
        return effort_map.get(violation_type, 'medium')
    
    def _check_recursion_depth(self, code: str) -> int:
        """Check recursion depth in code (simplified)"""
        # Simplified recursion detection
        return code.lower().count('def ') if 'def ' in code.lower() else 0
    
    def _check_return_values(self, code: str) -> bool:
        """Check if return values are handled (simplified)"""
        # Simplified check - in practice would need AST analysis
        return 'return' in code and ('=' in code or 'if' in code)
    
    # Planning and architectural methods
    
    def _analyze_violation_patterns(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns across multiple violations"""
        
        pattern_analysis = {
            'violation_types': {},
            'affected_files': set(),
            'severity_distribution': {},
            'architectural_smells': []
        }
        
        for violation in violations:
            v_type = violation.get('type', 'unknown')
            severity = violation.get('severity', 'medium')
            file_path = violation.get('file_path', '')
            
            pattern_analysis['violation_types'][v_type] = pattern_analysis['violation_types'].get(v_type, 0) + 1
            pattern_analysis['severity_distribution'][severity] = pattern_analysis['severity_distribution'].get(severity, 0) + 1
            pattern_analysis['affected_files'].add(file_path)
        
        # Identify architectural smells
        if pattern_analysis['violation_types'].get('god_object', 0) > 3:
            pattern_analysis['architectural_smells'].append('excessive_god_objects')
        
        if pattern_analysis['violation_types'].get('magic_literal', 0) > 10:
            pattern_analysis['architectural_smells'].append('configuration_management_needed')
        
        return pattern_analysis
    
    def _identify_root_causes(self, violation_patterns: Dict[str, Any]) -> List[str]:
        """Identify root causes of violation patterns"""
        
        root_causes = []
        
        if 'excessive_god_objects' in violation_patterns.get('architectural_smells', []):
            root_causes.append('lack_of_single_responsibility_principle')
            root_causes.append('insufficient_architectural_boundaries')
        
        if 'configuration_management_needed' in violation_patterns.get('architectural_smells', []):
            root_causes.append('missing_configuration_management')
            root_causes.append('hardcoded_values_throughout_codebase')
        
        return root_causes
    
    def _identify_leverage_points(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify high-impact refactoring opportunities"""
        
        # This would integrate with the graph exporter's hotspot analysis
        leverage_points = []
        
        for violation in violations:
            if violation.get('severity') == 'critical' and violation.get('type') == 'god_object':
                leverage_points.append({
                    'type': 'architectural_refactoring',
                    'target': violation.get('file_path'),
                    'impact': 'high',
                    'effort': 'high',
                    'priority': 'highest'
                })
        
        return leverage_points
    
    def _plan_refactoring_sequence(self, violations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Plan optimal sequence for addressing violations"""
        
        # Sort by impact and effort
        sequence = []
        
        # Phase 1: Low-effort, high-impact fixes
        magic_literals = [v for v in violations if v.get('type') == 'magic_literal']
        for violation in magic_literals[:5]:  # Limit to first 5
            sequence.append({
                'phase': 'quick_wins',
                'description': f"Extract magic literals in {violation.get('file_path', 'unknown')}",
                'effort': 'low',
                'impact': 'medium'
            })
        
        # Phase 2: Medium complexity refactoring
        position_violations = [v for v in violations if v.get('type') == 'connascence_of_position']
        for violation in position_violations:
            sequence.append({
                'phase': 'parameter_refactoring',
                'description': f"Refactor parameters in {violation.get('file_path', 'unknown')}",
                'effort': 'medium',
                'impact': 'medium'
            })
        
        # Phase 3: Architectural refactoring
        god_objects = [v for v in violations if v.get('type') == 'god_object']
        for violation in god_objects:
            sequence.append({
                'phase': 'architectural_refactoring',
                'description': f"Decompose god object in {violation.get('file_path', 'unknown')}",
                'effort': 'high',
                'impact': 'high'
            })
        
        return sequence
    
    def _plan_risk_mitigation(self, violations: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Plan risk mitigation strategies"""
        
        return {
            'before_refactoring': [
                'Ensure comprehensive test coverage',
                'Create baseline performance benchmarks',
                'Document current behavior',
                'Set up feature flags for gradual rollout'
            ],
            'during_refactoring': [
                'Refactor incrementally with frequent testing',
                'Maintain backward compatibility where possible',
                'Use dependency injection for loose coupling',
                'Follow NASA Power of Ten rules for safety'
            ],
            'after_refactoring': [
                'Run full test suite including integration tests',
                'Perform code review with focus on NASA compliance',
                'Monitor performance and error rates',
                'Document architectural changes'
            ]
        }
    
    def _plan_nasa_compliance(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Plan NASA Power of Ten compliance strategy"""
        
        nasa_plan = {
            'compliance_goals': [],
            'specific_actions': [],
            'validation_steps': []
        }
        
        # Check for NASA rule violations
        for violation in violations:
            if violation.get('type') == 'god_object':
                nasa_plan['compliance_goals'].append('Achieve Rule 4 compliance (function size limits)')
                nasa_plan['specific_actions'].append('Break large functions into smaller, testable units')
        
        nasa_plan['validation_steps'] = [
            'Run static analysis tools to verify NASA rule compliance',
            'Review code for adherence to each of the 10 rules',
            'Ensure all functions are under 60 lines',
            'Verify bounded loops and no dynamic allocation',
            'Check return value handling and assertion usage'
        ]
        
        return nasa_plan
    
    def _recommend_approach(self, planning_strategy: Dict[str, Any]) -> str:
        """Recommend overall refactoring approach"""
        
        root_causes = planning_strategy.get('root_causes', [])
        
        if 'lack_of_single_responsibility_principle' in root_causes:
            return 'systematic_responsibility_extraction'
        elif 'missing_configuration_management' in root_causes:
            return 'configuration_centralization'
        else:
            return 'incremental_refactoring'
    
    def _suggest_pr_breakdown(self, planning_strategy: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest how to break work into reviewable PRs"""
        
        sequence = planning_strategy.get('refactoring_sequence', [])
        
        prs = []
        current_pr = []
        
        for item in sequence:
            if item.get('phase') != (current_pr[-1].get('phase') if current_pr else None):
                if current_pr:
                    prs.append({
                        'title': f"Phase: {current_pr[0]['phase'].replace('_', ' ').title()}",
                        'description': f"Address {len(current_pr)} violations in {current_pr[0]['phase']} phase",
                        'items': current_pr
                    })
                current_pr = [item]
            else:
                current_pr.append(item)
        
        if current_pr:
            prs.append({
                'title': f"Phase: {current_pr[0]['phase'].replace('_', ' ').title()}",
                'description': f"Address {len(current_pr)} violations in {current_pr[0]['phase']} phase", 
                'items': current_pr
            })
        
        return prs
    
    def _identify_architectural_issues(self, violations: List[Dict[str, Any]], 
                                     architectural_context: Dict[str, Any]) -> List[str]:
        """Identify higher-level architectural issues"""
        
        issues = []
        
        god_object_count = sum(1 for v in violations if v.get('type') == 'god_object')
        if god_object_count > 2:
            issues.append('insufficient_separation_of_concerns')
        
        magic_literal_count = sum(1 for v in violations if v.get('type') == 'magic_literal')
        if magic_literal_count > 10:
            issues.append('missing_configuration_management')
        
        return issues


# Convenience functions for external use

def generate_ai_context_for_violation(violation: Dict[str, Any], 
                                    full_context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AI context for a single violation"""
    prompt_system = MCPPromptSystem()
    return prompt_system.generate_ai_agent_context(violation, full_context)

def generate_planning_context(violations: List[Dict[str, Any]], 
                            architectural_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate planning context for multiple violations"""
    prompt_system = MCPPromptSystem()
    return prompt_system.generate_planning_prompts(violations, architectural_context or {})


if __name__ == "__main__":
    # Example usage
    sample_violation = {
        'type': 'magic_literal',
        'file_path': 'src/api/handlers.py',
        'line_number': 42,
        'severity': 'medium',
        'class_name': 'RequestHandler',
        'function_name': 'handle_request'
    }
    
    sample_context = {
        'file_context': {'is_public_api': True, 'test_coverage': 0.85},
        'code_context': 'if response.status_code == 404:\n    return None'
    }
    
    ai_context = generate_ai_context_for_violation(sample_violation, sample_context)
    
    print("Generated AI Context:")
    print(f"File: {ai_context['file_path']}:{ai_context['line_number']}")
    print(f"Safety Tier: {ai_context['safety_tier']}")
    print(f"NASA Compliant: {ai_context['nasa_compliant']}")
    print(f"Confidence: {ai_context['confidence_score']}")
    print(f"Fix Example: {ai_context['explanation']}")