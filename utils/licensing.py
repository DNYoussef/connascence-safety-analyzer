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

"""
Mock licensing module for import compatibility.
"""
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Dict, Optional

# Import central constants
sys.path.append(str(Path(__file__).parent.parent))
from config.central_constants import LicenseConstants


@dataclass
class LicenseValidationResult:
    """Mock license validation result."""
    is_valid: bool = True
    license_type: str = LicenseConstants.MIT
    expires_at: Optional[str] = None
    features_enabled: Dict[str, bool] = None
    message: str = LicenseConstants.MOCK_VALIDATION_MESSAGE

    def __post_init__(self):
        if self.features_enabled is None:
            self.features_enabled = LicenseConstants.DEFAULT_FEATURES.copy()


class LicenseValidator:
    """Mock license validator."""

    def __init__(self):
        self.is_valid = True

    def validate(self, license_key: Optional[str] = None) -> LicenseValidationResult:
        """Mock validation - always returns valid."""
        return LicenseValidationResult(
            is_valid=True,
            license_type=LicenseConstants.MIT,
            message=LicenseConstants.MOCK_ALL_FEATURES_MESSAGE
        )

    def check_feature(self, feature_name: str) -> bool:
        """Mock feature check - always returns True."""
        return True

    def get_license_info(self) -> Dict[str, Any]:
        """Get mock license information."""
        return {
            'type': LicenseConstants.MIT,
            'valid': True,
            'features': ['all'],
            'expires': None
        }
