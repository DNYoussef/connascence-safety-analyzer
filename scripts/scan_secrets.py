#!/usr/bin/env python3
"""Lightweight tracked-file secret scanner.

The scanner is intentionally conservative and never prints matched values.
Use `# pragma: allow-secret` on a line that intentionally contains a known
test fixture or documentation example.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


MAX_FILE_BYTES = 1_000_000
ALLOW_MARKERS = ("pragma: allow-secret", "nosec-secret")
SKIP_PATH_PARTS = {
    ".benchmarks",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "venv",
    "venv-connascence",
}
SKIP_FILENAMES = {"nul"}

PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "change-me",
    "dummy",
    "example",
    "fake",
    "none",
    "null",
    "placeholder",
    "redacted",
    "sample",
    "test",
    "todo",
    "your-api-key",
    "your_api_key",
    "your-secret",
    "your_secret",
}

SECRET_NAME = (
    r"(?:api[_-]?key|access[_-]?key|secret(?:[_-]?key)?|client[_-]?secret|"
    r"session(?:[_-]?(?:id|key|secret|token))?|auth[_-]?token|bearer[_-]?token|"
    r"refresh[_-]?token|private[_-]?key|password|passwd|pwd)"
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


LINE_RULES = (
    Rule(
        "secret-like assignment",
        re.compile(
            rf"(?i)\b{SECRET_NAME}\b\s*[:=]\s*(?:['\"]([^'\"]+)['\"]|([^'\"\s#]+))",
        ),
    ),
    Rule("private key material", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    Rule("aws access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    Rule("github token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b")),
    Rule("openai api key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    Rule("slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    Rule("jwt token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan tracked files for committed secret patterns.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional files to scan. Defaults to all git-tracked files.",
    )
    return parser.parse_args()


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    names = [name for name in result.stdout.decode("utf-8", errors="replace").split("\0") if name]
    return [Path(name) for name in names]


def is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\0" in chunk


def should_scan(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if path.name.lower() in SKIP_FILENAMES or parts.intersection(SKIP_PATH_PARTS):
        return False
    if not path.is_file():
        return False
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return False
    except OSError:
        return False
    return not is_binary(path)


def normalize_value(value: str) -> str:
    value = value.strip().strip("'\"")
    value = value.rstrip(",;")
    if value.startswith("${") and value.endswith("}"):
        return ""
    return value.lower()


def assignment_value(match: re.Match[str]) -> str:
    return next((group for group in match.groups() if group is not None), "")


def is_placeholder(value: str) -> bool:
    normalized = normalize_value(value)
    if normalized in PLACEHOLDER_VALUES:
        return True
    return normalized.startswith(("your_", "your-", "example_", "example-", "test_", "test-"))


def is_safe_reference(value: str) -> bool:
    normalized = normalize_value(value)
    safe_prefixes = (
        "$",
        "${",
        "${{",
        "env.",
        "os.environ",
        "os.getenv",
        "process.env",
        "settings.",
        "config.",
    )
    if normalized.startswith(safe_prefixes):
        return True
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", value.strip().strip("'\"").rstrip(",;")))


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    return -sum((value.count(char) / len(value)) * math.log2(value.count(char) / len(value)) for char in set(value))


def is_secret_like_value(value: str) -> bool:
    candidate = value.strip().strip("'\"").rstrip(",;")
    normalized = normalize_value(value)
    if is_placeholder(normalized) or is_safe_reference(normalized):
        return False
    if "(" in normalized or ")" in normalized:
        return False
    if len(normalized) < 12:
        return False
    character_classes = sum(
        bool(re.search(pattern, candidate))
        for pattern in (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]")
    )
    return character_classes >= 3 or (len(candidate) >= 20 and shannon_entropy(candidate) >= 3.5)


def scan_line(path: Path, line_number: int, line: str) -> list[Finding]:
    if any(marker in line for marker in ALLOW_MARKERS):
        return []
    if "tests" in {part.lower() for part in path.parts}:
        lower_line = line.lower()
        if "magic string" in lower_line or "security violation" in lower_line or "values violation" in lower_line:
            return []

    findings: list[Finding] = []
    for rule in LINE_RULES:
        match = rule.pattern.search(line)
        if not match:
            continue
        if rule.name == "secret-like assignment":
            if not is_secret_like_value(assignment_value(match)):
                continue
        findings.append(Finding(str(path), line_number, rule.name))
    return findings


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            findings.extend(scan_line(path, line_number, line))
    return findings


def main() -> int:
    args = parse_args()
    paths = [Path(path) for path in args.paths] if args.paths else tracked_files()
    scope = "provided" if args.paths else "tracked"

    findings: list[Finding] = []
    scanned_count = 0
    for path in paths:
        if path.name.lower().startswith(".env") and path.name.lower() != ".env.example":
            findings.append(Finding(str(path), 1, "tracked env file"))
            continue
        if should_scan(path):
            scanned_count += 1
            findings.extend(scan_file(path))

    if findings:
        print(f"Secret scan failed: {len(findings)} potential issue(s) found.")
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.rule}")
        print("Matched secret values are intentionally omitted from this output.")
        return 1

    print(f"Secret scan passed: scanned {scanned_count} {scope} file(s); no secret patterns found.")
    return 0


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parents[1])
    sys.exit(main())
