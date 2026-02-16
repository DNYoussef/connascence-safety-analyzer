"""CLI entry point for clarity_linter: python -m analyzer.clarity_linter"""

import argparse
import json
import logging
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Clarity Linter - code clarity analysis")
    parser.add_argument("--config", type=str, default=None, help="Path to clarity_linter.yaml")
    parser.add_argument("--output-format", choices=["json", "sarif", "text"], default="json")
    parser.add_argument("--output-file", type=str, default=None, help="Output file path")
    parser.add_argument("--severity-threshold", choices=["critical", "high", "medium", "low"], default="high")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("path", nargs="?", default=".", help="Path to analyze")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    from analyzer.clarity_linter import ClarityLinter

    config_path = Path(args.config) if args.config else None
    linter = ClarityLinter(config_path=config_path)

    project_path = Path(args.path)
    violations = linter.analyze_project(project_path)

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    threshold = severity_order.get(args.severity_threshold, 1)
    filtered = [v for v in violations if severity_order.get(getattr(v, "severity", "low"), 3) <= threshold]

    if args.output_format == "json":
        output = {
            "violations": [
                {
                    "file": str(getattr(v, "file_path", "")),
                    "line": getattr(v, "line_number", 0),
                    "rule_id": getattr(v, "rule_id", ""),
                    "severity": getattr(v, "severity", "medium"),
                    "category": getattr(v, "category", "clarity"),
                    "message": getattr(v, "message", ""),
                    "description": getattr(v, "description", ""),
                    "code_snippet": getattr(v, "code_snippet", ""),
                    "fix_suggestion": getattr(v, "fix_suggestion", ""),
                }
                for v in filtered
            ],
            "summary": linter.get_summary(),
        }
        text = json.dumps(output, indent=2)
    elif args.output_format == "sarif":
        sarif = linter.export_sarif(filtered)
        text = json.dumps(sarif, indent=2)
    else:
        lines = []
        for v in filtered:
            lines.append(f"{getattr(v, 'file_path', '')}:{getattr(v, 'line_number', 0)}: "
                         f"[{getattr(v, 'severity', '')}] {getattr(v, 'message', '')}")
        text = "\n".join(lines)

    if args.output_file:
        Path(args.output_file).write_text(text, encoding="utf-8")
        print(f"Wrote {len(filtered)} violations to {args.output_file}")
    else:
        print(text)


if __name__ == "__main__":
    main()
