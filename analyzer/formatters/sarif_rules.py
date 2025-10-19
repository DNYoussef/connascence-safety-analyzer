"""
SARIF rule definitions for all connascence types.

This module defines SARIF rule metadata for the 9 types of connascence,
including descriptions, severity levels, and help URLs.

NASA Rule 4: Function under 60 lines
"""

from typing import Dict, List


def get_connascence_rules() -> List[Dict]:
    """
    Get SARIF rule definitions for all connascence types.

    Returns:
        List of SARIF rule objects with metadata

    NASA Rule 4: Function under 60 lines (25 LOC)
    """
    return [
        # Static Connascences (Least Dangerous)
        {
            "id": "CoN",
            "name": "ConnascenceOfName",
            "shortDescription": {"text": "Connascence of Name"},
            "fullDescription": {
                "text": "Multiple components must agree on the name of something. "
                "This is the weakest form of connascence and is generally acceptable."
            },
            "helpUri": "https://connascence.io/name.html",
            "defaultConfiguration": {"level": "note"},
        },
        {
            "id": "CoT",
            "name": "ConnascenceOfType",
            "shortDescription": {"text": "Connascence of Type"},
            "fullDescription": {
                "text": "Multiple components must agree on the type of something. "
                "Type coupling can lead to refactoring difficulties."
            },
            "helpUri": "https://connascence.io/type.html",
            "defaultConfiguration": {"level": "warning"},
        },
        {
            "id": "CoM",
            "name": "ConnascenceOfMeaning",
            "shortDescription": {"text": "Connascence of Meaning"},
            "fullDescription": {
                "text": "Multiple components must agree on the meaning of values. "
                "Often manifests as magic numbers or flag parameters."
            },
            "helpUri": "https://connascence.io/meaning.html",
            "defaultConfiguration": {"level": "warning"},
        },
        {
            "id": "CoP",
            "name": "ConnascenceOfPosition",
            "shortDescription": {"text": "Connascence of Position"},
            "fullDescription": {
                "text": "Multiple components must agree on the order of values. "
                "Common with positional function parameters."
            },
            "helpUri": "https://connascence.io/position.html",
            "defaultConfiguration": {"level": "warning"},
        },
        {
            "id": "CoA",
            "name": "ConnascenceOfAlgorithm",
            "shortDescription": {"text": "Connascence of Algorithm"},
            "fullDescription": {
                "text": "Multiple components must agree on a particular algorithm. "
                "Acceptable when algorithm is well-documented."
            },
            "helpUri": "https://connascence.io/algorithm.html",
            "defaultConfiguration": {"level": "note"},
        },
        # Dynamic Connascences (More Dangerous)
        {
            "id": "CoE",
            "name": "ConnascenceOfExecution",
            "shortDescription": {"text": "Connascence of Execution"},
            "fullDescription": {
                "text": "The order of execution of multiple components is important. "
                "This creates temporal coupling and can lead to race conditions."
            },
            "helpUri": "https://connascence.io/execution.html",
            "defaultConfiguration": {"level": "error"},
        },
        {
            "id": "CoT2",
            "name": "ConnascenceOfTiming",
            "shortDescription": {"text": "Connascence of Timing"},
            "fullDescription": {
                "text": "The timing of execution of multiple components is important. "
                "Can cause intermittent bugs and is very difficult to debug."
            },
            "helpUri": "https://connascence.io/timing.html",
            "defaultConfiguration": {"level": "error"},
        },
        {
            "id": "CoV",
            "name": "ConnascenceOfValue",
            "shortDescription": {"text": "Connascence of Value"},
            "fullDescription": {
                "text": "Multiple components must agree on the value of something. "
                "Magic numbers and duplicate literals indicate this connascence."
            },
            "helpUri": "https://connascence.io/value.html",
            "defaultConfiguration": {"level": "error"},
        },
        {
            "id": "CoI",
            "name": "ConnascenceOfIdentity",
            "shortDescription": {"text": "Connascence of Identity"},
            "fullDescription": {
                "text": "Multiple components must reference the same object instance. "
                "The most dangerous form of connascence, often causes bugs."
            },
            "helpUri": "https://connascence.io/identity.html",
            "defaultConfiguration": {"level": "error"},
        },
    ]


def get_severity_mapping() -> Dict[str, str]:
    """
    Get connascence type to SARIF severity mapping.

    Returns:
        Dict mapping connascence type to SARIF level

    NASA Rule 4: Function under 60 lines (22 LOC)
    """
    return {
        # Dynamic connascences (most dangerous) → error
        "CoI": "error",  # Identity - most dangerous
        "CoE": "error",  # Execution - temporal coupling
        "CoV": "error",  # Value - magic numbers
        "CoT2": "error",  # Timing - race conditions
        # Static connascences (moderate) → warning
        "CoT": "warning",  # Type - refactoring difficulty
        "CoP": "warning",  # Position - parameter order
        "CoM": "warning",  # Meaning - semantic coupling
        # Static connascences (least dangerous) → note
        "CoA": "note",  # Algorithm - acceptable if documented
        "CoN": "note",  # Name - weakest coupling
    }
