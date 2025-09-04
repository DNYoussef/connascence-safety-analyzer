# General Safety Layer Configuration Constants
STRICT_MAX_FUNCTION_PARAMS = 3
STRICT_MAX_CYCLOMATIC_COMPLEXITY = 6

GENERAL_SAFETY_PROFILE = {
    'name': 'General Safety Layer',
    'description': 'Strict safety rules for high-quality code',
    'rules': {
        'recursion_banned': True,
        'max_function_params': STRICT_MAX_FUNCTION_PARAMS,
        'no_recursion_rule': True,
        'no_magic_numbers_rule': True
    },
    'thresholds': {
        'max_function_params': STRICT_MAX_FUNCTION_PARAMS,
        'max_cyclomatic_complexity': STRICT_MAX_CYCLOMATIC_COMPLEXITY
    }
}
