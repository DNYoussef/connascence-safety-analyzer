"""
Comment Issues Detector - Code Clarity Detector

Detects comment quality issues.

NASA Rule 4 Compliant: All functions under 60 lines
NASA Rule 5 Compliant: Input assertions
"""

import ast
import re
from pathlib import Path
from typing import List, Set, Tuple

from analyzer.clarity_linter.base import BaseClarityDetector
from analyzer.clarity_linter.models import ClarityViolation


class CommentIssuesDetector(BaseClarityDetector):
    """
    Detects comment quality issues.

    Issues detected:
    - Commented-out code
    - TODO/FIXME without context
    - Redundant comments that repeat the code
    - Empty or trivial comments

    NASA Rule 4 Compliant: All methods under 60 lines
    NASA Rule 5 Compliant: Input assertions
    """

    rule_id = "CLARITY_COMMENT_ISSUES"
    rule_name = "Comment Issues"
    default_severity = "low"

    # Patterns for TODO/FIXME without context
    TODO_PATTERN = re.compile(
        r"#\s*(TODO|FIXME|XXX|HACK|BUG)[\s:]*$",
        re.IGNORECASE
    )

    # Patterns that suggest commented-out code
    CODE_PATTERNS = [
        re.compile(r"#\s*def\s+\w+\s*\("),  # Function definition
        re.compile(r"#\s*class\s+\w+"),  # Class definition
        re.compile(r"#\s*if\s+.+:"),  # If statement
        re.compile(r"#\s*for\s+\w+\s+in"),  # For loop
        re.compile(r"#\s*while\s+"),  # While loop
        re.compile(r"#\s*return\s+"),  # Return statement
        re.compile(r"#\s*import\s+"),  # Import statement
        re.compile(r"#\s*from\s+\w+\s+import"),  # From import
        re.compile(r"#\s*\w+\s*=\s*.+"),  # Assignment
        re.compile(r"#\s*\w+\.\w+\("),  # Method call
    ]

    # Redundant comment patterns
    REDUNDANT_PATTERNS = [
        (re.compile(r"#\s*increment\s+", re.I), r"\+=\s*1"),
        (re.compile(r"#\s*set\s+\w+\s+to", re.I), r"="),
        (re.compile(r"#\s*loop\s+(through|over)", re.I), r"for\s+"),
        (re.compile(r"#\s*if\s+\w+\s+is", re.I), r"if\s+"),
        (re.compile(r"#\s*return\s+(the\s+)?result", re.I), r"return"),
    ]

    def detect(
        self,
        tree: ast.Module,
        file_path: Path
    ) -> List[ClarityViolation]:
        """
        Detect comment issues in source file.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            tree: Parsed AST tree (used for context)
            file_path: Path to file being analyzed

        Returns:
            List of clarity violations found
        """
        # NASA Rule 5: Input validation
        assert tree is not None, "tree cannot be None"
        assert file_path is not None, "file_path cannot be None"

        violations = []

        # Read source file to analyze comments
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except (IOError, OSError):
            return violations

        self._analyze_comments(lines, file_path, violations)
        return violations

    def _analyze_comments(
        self,
        lines: List[str],
        file_path: Path,
        violations: List[ClarityViolation]
    ) -> None:
        """
        Analyze all comments in source lines.

        NASA Rule 4: Function under 60 lines
        """
        for line_num, line in enumerate(lines, start=1):
            # Find comment in line
            comment_start = self._find_comment_start(line)
            if comment_start == -1:
                continue

            comment = line[comment_start:].rstrip()

            # Check for various issues
            if self._is_empty_comment(comment):
                violations.append(
                    self._create_comment_violation(
                        file_path, line_num, "empty", comment
                    )
                )
            elif self._is_todo_without_context(comment):
                violations.append(
                    self._create_comment_violation(
                        file_path, line_num, "todo_no_context", comment
                    )
                )
            elif self._is_commented_code(comment):
                violations.append(
                    self._create_comment_violation(
                        file_path, line_num, "commented_code", comment
                    )
                )
            elif self._is_redundant_comment(comment, line[:comment_start]):
                violations.append(
                    self._create_comment_violation(
                        file_path, line_num, "redundant", comment
                    )
                )

    def _find_comment_start(self, line: str) -> int:
        """
        Find start of comment in line, ignoring strings.

        NASA Rule 4: Function under 60 lines
        """
        in_string = None
        for i, char in enumerate(line):
            if char in ('"', "'"):
                if in_string is None:
                    in_string = char
                elif in_string == char:
                    # Check for escape
                    if i > 0 and line[i-1] != "\\":
                        in_string = None
            elif char == "#" and in_string is None:
                return i
        return -1

    def _is_empty_comment(self, comment: str) -> bool:
        """
        Check if comment is empty or trivial.

        NASA Rule 4: Function under 60 lines
        """
        stripped = comment.lstrip("#").strip()
        return len(stripped) == 0 or stripped in ("...", "---", "===")

    def _is_todo_without_context(self, comment: str) -> bool:
        """
        Check if TODO/FIXME lacks description.

        NASA Rule 4: Function under 60 lines
        """
        return bool(self.TODO_PATTERN.match(comment))

    def _is_commented_code(self, comment: str) -> bool:
        """
        Check if comment appears to be commented-out code.

        NASA Rule 4: Function under 60 lines
        """
        for pattern in self.CODE_PATTERNS:
            if pattern.match(comment):
                return True
        return False

    def _is_redundant_comment(self, comment: str, code: str) -> bool:
        """
        Check if comment redundantly describes obvious code.

        NASA Rule 4: Function under 60 lines
        """
        for comment_pattern, code_pattern in self.REDUNDANT_PATTERNS:
            if comment_pattern.search(comment):
                if re.search(code_pattern, code):
                    return True
        return False

    def _create_comment_violation(
        self,
        file_path: Path,
        line_number: int,
        issue: str,
        comment: str
    ) -> ClarityViolation:
        """
        Create violation for comment issue.

        NASA Rule 4: Function under 60 lines
        """
        issue_messages = {
            "empty": "Empty or trivial comment",
            "todo_no_context": "TODO/FIXME without description",
            "commented_code": "Commented-out code detected",
            "redundant": "Redundant comment that repeats the code",
        }

        description = issue_messages.get(issue, "Comment issue detected")
        if len(comment) > 50:
            comment = comment[:47] + "..."
        description = f"{description}: {comment}"

        recommendations = {
            "empty": "Remove empty comments or add meaningful content.",
            "todo_no_context": "Add description of what needs to be done and why.",
            "commented_code": "Remove commented-out code. Use version control.",
            "redundant": "Remove obvious comments. Comments should explain why, not what.",
        }

        return self.create_violation(
            file_path=file_path,
            line_number=line_number,
            description=description,
            recommendation=recommendations.get(issue, "Improve comment quality."),
            context={
                "issue": issue,
                "comment": comment[:100],
                "issue_type": "comment_issue"
            }
        )


__all__ = ['CommentIssuesDetector']
