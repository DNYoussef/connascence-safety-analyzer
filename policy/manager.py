import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from analyzer.core import ConnascenceViolation
from analyzer.thresholds import ThresholdConfig

# Policy Manager Configuration Constants (CoM Improvement - Pass 2)
STRICT_CORE_MAX_POSITIONAL_PARAMS = 2
STRICT_CORE_GOD_CLASS_METHODS = 15
STRICT_CORE_MAX_CYCLOMATIC_COMPLEXITY = 8
STRICT_CORE_COM_LIMIT = 3
STRICT_CORE_COP_LIMIT = 2
STRICT_CORE_TOTAL_VIOLATIONS_LIMIT = 10

SERVICE_DEFAULTS_MAX_POSITIONAL_PARAMS = 4
SERVICE_DEFAULTS_GOD_CLASS_METHODS = 25
SERVICE_DEFAULTS_MAX_CYCLOMATIC_COMPLEXITY = 12
SERVICE_DEFAULTS_COM_LIMIT = 8
SERVICE_DEFAULTS_COP_LIMIT = 5
SERVICE_DEFAULTS_TOTAL_VIOLATIONS_LIMIT = 30

EXPERIMENTAL_MAX_POSITIONAL_PARAMS = 6
EXPERIMENTAL_GOD_CLASS_METHODS = 35
EXPERIMENTAL_MAX_CYCLOMATIC_COMPLEXITY = 20
EXPERIMENTAL_COM_LIMIT = 15
EXPERIMENTAL_COP_LIMIT = 8
EXPERIMENTAL_TOTAL_VIOLATIONS_LIMIT = 50

class PolicyManager:
    def __init__(self):
        self.presets = {
            'strict-core': {
                'name': 'Strict Core',
                'thresholds': {
                    'max_positional_params': STRICT_CORE_MAX_POSITIONAL_PARAMS,
                    'god_class_methods': STRICT_CORE_GOD_CLASS_METHODS,
                    'max_cyclomatic_complexity': STRICT_CORE_MAX_CYCLOMATIC_COMPLEXITY
                },
                'budget_limits': {
                    'CoM': STRICT_CORE_COM_LIMIT,
                    'CoP': STRICT_CORE_COP_LIMIT,
                    'total_violations': STRICT_CORE_TOTAL_VIOLATIONS_LIMIT
                }
            },
            'service-defaults': {
                'name': 'Service Defaults', 
                'thresholds': {
                    'max_positional_params': SERVICE_DEFAULTS_MAX_POSITIONAL_PARAMS,
                    'god_class_methods': SERVICE_DEFAULTS_GOD_CLASS_METHODS,
                    'max_cyclomatic_complexity': SERVICE_DEFAULTS_MAX_CYCLOMATIC_COMPLEXITY
                },
                'budget_limits': {
                    'CoM': SERVICE_DEFAULTS_COM_LIMIT,
                    'CoP': SERVICE_DEFAULTS_COP_LIMIT,
                    'total_violations': SERVICE_DEFAULTS_TOTAL_VIOLATIONS_LIMIT
                }
            },
            'experimental': {
                'name': 'Experimental',
                'thresholds': {
                    'max_positional_params': EXPERIMENTAL_MAX_POSITIONAL_PARAMS,
                    'god_class_methods': EXPERIMENTAL_GOD_CLASS_METHODS,
                    'max_cyclomatic_complexity': EXPERIMENTAL_MAX_CYCLOMATIC_COMPLEXITY
                },
                'budget_limits': {
                    'CoM': EXPERIMENTAL_COM_LIMIT,
                    'CoP': EXPERIMENTAL_COP_LIMIT,
                    'total_violations': EXPERIMENTAL_TOTAL_VIOLATIONS_LIMIT
                }
            }
        }
        self.custom_policies = {}
    
    def get_preset(self, name: str) -> Dict[str, Any]:
        """Get a policy preset by name."""
        if name not in self.presets:
            raise ValueError(f"Unknown policy preset: {name}")
        return self.presets[name].copy()
    
    def list_presets(self) -> List[str]:
        """List available policy presets."""
        return list(self.presets.keys())
    
    def validate_preset_name(self, name: str) -> bool:
        """Validate if preset name exists."""
        return name in self.presets
    
    def validate_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Validate policy configuration."""
        validation_result = {'valid': True, 'errors': []}
        
        # Check required sections
        required_sections = ['name', 'thresholds', 'budget_limits']
        for section in required_sections:
            if section not in policy:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required section: {section}")
        
        # Validate thresholds
        if 'thresholds' in policy:
            thresholds = policy['thresholds']
            required_thresholds = ['max_positional_params', 'god_class_methods', 'max_cyclomatic_complexity']
            for threshold in required_thresholds:
                if threshold not in thresholds:
                    validation_result['errors'].append(f"Missing threshold: {threshold}")
                elif not isinstance(thresholds[threshold], (int, float)):
                    validation_result['errors'].append(f"Invalid threshold value for {threshold}")
        
        # Validate budget limits
        if 'budget_limits' in policy:
            budget_limits = policy['budget_limits']
            if 'total_violations' not in budget_limits:
                validation_result['errors'].append("Missing budget limit: total_violations")
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        return validation_result
    
    def merge_policies(self, base_policy: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Merge a base policy with overrides (policy inheritance)."""
        if base_policy not in self.presets:
            raise ValueError(f"Unknown base policy: {base_policy}")
        
        merged = self.presets[base_policy].copy()
        
        # Deep merge thresholds
        if 'thresholds' in overrides:
            merged['thresholds'] = {**merged['thresholds'], **overrides['thresholds']}
        
        # Deep merge budget limits
        if 'budget_limits' in overrides:
            merged['budget_limits'] = {**merged['budget_limits'], **overrides['budget_limits']}
        
        # Override other fields
        for key, value in overrides.items():
            if key not in ['thresholds', 'budget_limits']:
                merged[key] = value
                
        return merged
    
    def save_to_file(self, policy: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """Save policy to file."""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() in ['.yml', '.yaml']:
            with open(file_path, 'w') as f:
                yaml.dump(policy, f, default_flow_style=False)
        else:
            with open(file_path, 'w') as f:
                json.dump(policy, f, indent=2)
    
    def load_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load policy from file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Policy file not found: {file_path}")
        
        try:
            if file_path.suffix.lower() in ['.yml', '.yaml']:
                with open(file_path, 'r') as f:
                    policy = yaml.safe_load(f)
            else:
                with open(file_path, 'r') as f:
                    policy = json.load(f)
            
            # Validate loaded policy
            validation = self.validate_policy(policy)
            if not validation['valid']:
                raise ValueError(f"Invalid policy configuration: {validation['errors']}")
            
            return policy
            
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ValueError(f"Error parsing policy file: {e}")
    
    def register_custom_policy(self, name: str, policy: Dict[str, Any]) -> None:
        """Register a custom policy."""
        validation = self.validate_policy(policy)
        if not validation['valid']:
            raise ValueError(f"Invalid policy: {validation['errors']}")
        
        self.custom_policies[name] = policy.copy()
    
    def categorize_violations(self, violations: List[ConnascenceViolation], policy: Dict[str, Any]) -> Dict[str, List[ConnascenceViolation]]:
        """Categorize violations based on policy severity rules."""
        categories = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for violation in violations:
            severity = getattr(violation, 'severity', 'medium')
            if severity in categories:
                categories[severity].append(violation)
            else:
                categories['medium'].append(violation)
        
        return categories

class PolicyViolation:
    def __init__(self, violation_id: str, policy_rule: str, severity: str, 
                 description: str, file_path: str = None, line_number: int = None):
        self.violation_id = violation_id
        self.policy_rule = policy_rule
        self.severity = severity
        self.description = description
        self.file_path = file_path
        self.line_number = line_number
        self.timestamp = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'violation_id': self.violation_id,
            'policy_rule': self.policy_rule,
            'severity': self.severity,
            'description': self.description,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'timestamp': self.timestamp
        }