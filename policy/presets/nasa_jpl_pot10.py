# NASA JPL POT-10 Configuration Constants (CoM Improvement - Pass 2)
NASA_JPL_MAX_FUNCTION_PARAMS = 3
NASA_JPL_MAX_CYCLOMATIC_COMPLEXITY = 6

NASA_JPL_POT10_PROFILE = {
    'name': 'NASA JPL Power of Ten',
    'rules': {
        'recursion_banned': True,
        'max_function_params': NASA_JPL_MAX_FUNCTION_PARAMS,
        'nasa_rule_3_no_recursion': True,
        'nasa_rule_8_no_magic_numbers': True
    },
    'thresholds': {
        'max_function_params': NASA_JPL_MAX_FUNCTION_PARAMS,
        'max_cyclomatic_complexity': NASA_JPL_MAX_CYCLOMATIC_COMPLEXITY
    }
}
