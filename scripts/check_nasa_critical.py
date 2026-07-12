"""Fail-closed gate for the NASA critical-violation report."""

import json
import sys
from pathlib import Path

LIMIT = 5


def main(argv) -> int:
    if len(argv) != 2:
        print("NASA_CRITICAL_GATE_INVALID expected_report_path", file=sys.stderr)
        return 2

    try:
        report = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        if report.get("success") is not True:
            raise ValueError("analyzer did not report success")
        violations = report["violations"]
        if not isinstance(violations, list) or not all(
            isinstance(item, dict) and isinstance(item.get("severity"), str)
            for item in violations
        ):
            raise ValueError("violations must be a list of objects")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"NASA_CRITICAL_GATE_INVALID {type(error).__name__}", file=sys.stderr)
        return 2

    critical = sum(item.get("severity") == "critical" for item in violations)
    if critical > LIMIT:
        print(f"NASA_CRITICAL_GATE_RED critical={critical} limit={LIMIT}")
        return 1

    print(f"NASA_CRITICAL_GATE_GREEN critical={critical} limit={LIMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
