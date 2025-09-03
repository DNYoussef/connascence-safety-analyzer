
NASA_JPL_POT10_PROFILE = {
    'name': 'NASA JPL Power of Ten',
    'rules': {
        'recursion_banned': True,
        'max_function_params': 3,
        'nasa_rule_3_no_recursion': True,
        'nasa_rule_8_no_magic_numbers': True
    },
    'thresholds': {
        'max_function_params': 3,
        'max_cyclomatic_complexity': 6
    }
}
