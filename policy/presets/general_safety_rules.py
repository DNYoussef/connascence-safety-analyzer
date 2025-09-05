# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

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
