"""
Language-specific strategy implementations for connascence detection.
Consolidates duplicate algorithms across JavaScript and C language detection.
"""

from pathlib import Path
import re
from typing import Dict, List

from utils.types import ConnascenceViolation

try:
    from .constants import (
        DETECTION_MESSAGES,
        GOD_OBJECT_LOC_THRESHOLD,
        NASA_PARAMETER_THRESHOLD,
        REGEX_PATTERNS,
    )
except ImportError:
    # Fallback when running as script
    from constants import (
        DETECTION_MESSAGES,
        GOD_OBJECT_LOC_THRESHOLD,
        NASA_PARAMETER_THRESHOLD,
        REGEX_PATTERNS,
    )


# ConnascenceViolation now imported from utils.types


class LanguageStrategy:
    """Base strategy for language-specific connascence detection."""

    def __init__(self, language_name: str):
        self.language_name = language_name

    def detect_magic_literals(self, file_path: Path, source_lines: List[str]) -> List[ConnascenceViolation]:
        """Detect magic literals using formal grammar analysis when possible."""
        violations = []

        # Try to use formal grammar analyzer first
        try:
            from .formal_grammar import FormalGrammarEngine

            engine = FormalGrammarEngine()
            source_code = "\n".join(source_lines)
            matches = engine.analyze_file(str(file_path), source_code, self.language_name)

            # Convert grammar matches to violations
            for match in matches:
                if match.pattern_type.value == "magic_literal":
                    violations.append(self._create_formal_magic_literal_violation(file_path, match, source_lines))
            return violations
        except ImportError:
            # Fallback to regex-based detection
            pass

        # Original regex-based detection as fallback
        patterns = self.get_magic_literal_patterns()

        for line_num, line in enumerate(source_lines, 1):
            # Skip comments using language-specific comment detection
            if self.is_comment_line(line):
                continue

            # Apply numeric patterns
            for match in patterns["numeric"].finditer(line):
                violations.append(
                    self._create_magic_literal_violation(file_path, line_num, match, "number", line.strip())
                )

            # Apply string patterns
            for match in patterns["string"].finditer(line):
                literal = match.group()
                if not self.is_excluded_string_literal(literal):
                    violations.append(
                        self._create_magic_literal_violation(file_path, line_num, match, "string", line.strip())
                    )

        return violations

    def detect_god_functions(self, file_path: Path, source_lines: List[str]) -> List[ConnascenceViolation]:
        """Detect god functions using language-specific patterns."""
        violations = []
        function_detector = self.get_function_detector()

        in_function = False
        function_start = 0
        function_name = ""
        brace_count = 0

        for line_num, line in enumerate(source_lines, 1):
            if not in_function:
                match = function_detector.match(line)
                if match:
                    in_function = True
                    function_start = line_num
                    function_name = self.extract_function_name(line)
                    brace_count = self.count_braces(line)
            else:
                brace_count += self.count_braces(line)
                if brace_count <= 0:
                    # Function ended
                    function_length = line_num - function_start + 1
                    if function_length > GOD_OBJECT_LOC_THRESHOLD // 10:  # 50 lines threshold
                        violations.append(
                            self._create_god_function_violation(
                                file_path, function_start, function_name, function_length
                            )
                        )
                    in_function = False

        return violations

    def detect_parameter_coupling(self, file_path: Path, source_lines: List[str]) -> List[ConnascenceViolation]:
        """Detect parameter coupling using language-specific patterns."""
        violations = []
        param_detector = self.get_parameter_detector()

        for line_num, line in enumerate(source_lines, 1):
            match = param_detector.search(line)
            if match:
                params = match.group(1)
                param_count = self.count_parameters(params)

                if param_count > NASA_PARAMETER_THRESHOLD:
                    violations.append(
                        self._create_parameter_violation(file_path, line_num, match.start(), param_count, line.strip())
                    )

        return violations

    # Abstract methods to be implemented by language-specific strategies
    def get_magic_literal_patterns(self) -> Dict[str, re.Pattern]:
        """Return regex patterns for magic literal detection."""
        raise NotImplementedError

    def get_function_detector(self) -> re.Pattern:
        """Return regex pattern for function detection."""
        raise NotImplementedError

    def get_parameter_detector(self) -> re.Pattern:
        """Return regex pattern for parameter detection."""
        raise NotImplementedError

    def is_comment_line(self, line: str) -> bool:
        """Check if line is a comment."""
        raise NotImplementedError

    def extract_function_name(self, line: str) -> str:
        """Extract function name from definition line."""
        raise NotImplementedError

    def count_braces(self, line: str) -> int:
        """Count brace difference for function boundary detection."""
        return line.count("{") - line.count("}")

    def count_parameters(self, params: str) -> int:
        """Count parameters in parameter string."""
        return len([p.strip() for p in params.split(",") if p.strip()]) if params.strip() else 0

    def is_excluded_string_literal(self, literal: str) -> bool:
        """Check if string literal should be excluded."""
        return any(skip in literal.lower() for skip in ["test", "error", "warning", "debug"])

    # Helper methods for creating violations
    def _create_formal_magic_literal_violation(
        self, file_path: Path, match, source_lines: List[str]
    ) -> ConnascenceViolation:
        """Create a violation from formal grammar match."""
        # Extract context information from the match
        context = match.metadata
        severity_score = context.get("severity_score", 5.0)

        # Map severity score to severity level
        if severity_score > 8.0:
            severity = "high"
        elif severity_score > 5.0:
            severity = "medium"
        elif severity_score > 2.0:
            severity = "low"
        else:
            severity = "informational"

        # Create enhanced description
        formal_context = context.get("context")
        if formal_context:
            description = f"Context-aware magic literal '{match.text}' in {formal_context.__class__.__name__.lower()}"
        else:
            description = f"Magic literal '{match.text}' detected"

        # Get recommendations from context
        recommendations = context.get("recommendations", [])
        recommendation = (
            "; ".join(recommendations) if recommendations else f"Extract to a {self.get_constant_recommendation()}"
        )

        return ConnascenceViolation(
            type="connascence_of_meaning",
            severity=severity,
            file_path=str(file_path),
            line_number=match.line_number,
            column=match.column,
            description=description,
            recommendation=recommendation,
            code_snippet=match.text,
            context={
                "literal_value": context.get("value", match.text),
                "formal_analysis": True,
                "confidence": match.confidence,
                "analysis_metadata": context,
            },
        )

    def _create_magic_literal_violation(
        self, file_path: Path, line_num: int, match: re.Match, literal_type: str, code_snippet: str
    ) -> ConnascenceViolation:
        """Create a magic literal violation."""
        return ConnascenceViolation(
            type="connascence_of_meaning",
            severity="medium",
            file_path=str(file_path),
            line_number=line_num,
            column=match.start(),
            description=DETECTION_MESSAGES["magic_literal"].format(value=match.group()),
            recommendation=f"Extract to a {self.get_constant_recommendation()}",
            code_snippet=code_snippet,
            context={"literal_type": literal_type, "value": match.group()},
        )

    def _create_god_function_violation(
        self, file_path: Path, line_num: int, function_name: str, length: int
    ) -> ConnascenceViolation:
        """Create a god function violation."""
        return ConnascenceViolation(
            type="god_object",
            severity="high" if length > 100 else "medium",
            file_path=str(file_path),
            line_number=line_num,
            column=0,
            description=f"Function too long ({length} lines) - potential god function",
            recommendation="Break into smaller, focused functions",
            code_snippet=function_name,
            context={"function_length": length, "threshold": 50},
        )

    def _create_parameter_violation(
        self, file_path: Path, line_num: int, column: int, param_count: int, code_snippet: str
    ) -> ConnascenceViolation:
        """Create a parameter coupling violation."""
        return ConnascenceViolation(
            type="connascence_of_position",
            severity="high" if param_count > 10 else "medium",
            file_path=str(file_path),
            line_number=line_num,
            column=column,
            description=f"Too many parameters ({param_count}) - high connascence of position",
            recommendation="Use parameter objects or reduce parameters",
            code_snippet=code_snippet,
            context={"parameter_count": param_count, "threshold": NASA_PARAMETER_THRESHOLD},
        )

    def get_constant_recommendation(self) -> str:
        """Get language-specific constant recommendation."""
        return "named constant"


class JavaScriptStrategy(LanguageStrategy):
    """JavaScript-specific connascence detection strategy."""

    def __init__(self):
        super().__init__("javascript")

    def get_magic_literal_patterns(self) -> Dict[str, re.Pattern]:
        return {"numeric": re.compile(r"\b(?!0\b|1\b|-1\b)\d+\.?\d*\b"), "string": re.compile(r"""["'][^"']{3,}["']""")}

    def get_function_detector(self) -> re.Pattern:
        return re.compile(REGEX_PATTERNS["function_def"].replace("def", "function"))

    def get_parameter_detector(self) -> re.Pattern:
        return re.compile(r"(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:function|\(.*?\)\s*=>))\s*\(([^)]+)\)")

    def is_comment_line(self, line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("//") or ("/*" in line and "*/" in line)

    def extract_function_name(self, line: str) -> str:
        clean_line = line.strip()
        return clean_line[:50] + "..." if len(clean_line) > 50 else clean_line

    def get_constant_recommendation(self) -> str:
        return "const or enum"


class CStrategy(LanguageStrategy):
    """C/C++-specific connascence detection strategy."""

    def __init__(self):
        super().__init__("c")

    def get_magic_literal_patterns(self) -> Dict[str, re.Pattern]:
        return {"numeric": re.compile(r"\b(?!0\b|1\b|-1\b)\d+[UuLl]*\b"), "string": re.compile(r'"[^"]{3,}"')}

    def get_function_detector(self) -> re.Pattern:
        return re.compile(r"^\s*(?:static\s+)?(?:inline\s+)?[\w\s\*]+\s+\w+\s*\([^)]*\)\s*\{?")

    def get_parameter_detector(self) -> re.Pattern:
        return re.compile(r"[\w\s\*]+\s+\w+\s*\(([^)]+)\)")

    def is_comment_line(self, line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("/*")

    def extract_function_name(self, line: str) -> str:
        # Extract function name from C function definition
        match = re.search(r"\w+\s*\(", line)
        return match.group().replace("(", "") if match else "unknown_function"

    def get_constant_recommendation(self) -> str:
        return "#define or const"


class PythonStrategy(LanguageStrategy):
    """Python-specific connascence detection strategy (extends AST analysis)."""

    def __init__(self):
        super().__init__("python")

    def get_magic_literal_patterns(self) -> Dict[str, re.Pattern]:
        return {"numeric": re.compile(r"\b(?!0\b|1\b|-1\b)\d+\.?\d*\b"), "string": re.compile(r"""["'][^"']{3,}["']""")}

    def get_function_detector(self) -> re.Pattern:
        return re.compile(r"^\s*def\s+\w+\s*\(")

    def get_parameter_detector(self) -> re.Pattern:
        return re.compile(r"def\s+\w+\s*\(([^)]+)\)")

    def is_comment_line(self, line: str) -> bool:
        return line.strip().startswith("#")

    def extract_function_name(self, line: str) -> str:
        match = re.search(r"def\s+(\w+)", line)
        return match.group(1) if match else "unknown_function"

    def get_constant_recommendation(self) -> str:
        return "module-level constant"
