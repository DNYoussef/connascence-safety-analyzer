"""
Core Theater Detection Components
==================================
Detects various forms of performance theater in software development.
Ported from SPEK template with enhancements for defense industry compliance.

Theater Types:
- Test Gaming: Empty tests, trivial assertions, gaming coverage metrics
- Error Masking: Silently ignoring exceptions, bare except clauses
- Metrics Inflation: Hardcoded perfect scores, impossible metrics
- Documentation Theater: TODO placeholders instead of real docs
- Quality Facade: Comments claiming fixes without actual implementation
"""

import re
import ast
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TheaterType(Enum):
    TEST_GAMING = "test_gaming"
    ERROR_MASKING = "error_masking"
    METRICS_INFLATION = "metrics_inflation"
    DOCUMENTATION_THEATER = "documentation_theater"
    QUALITY_FACADE = "quality_facade"


class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TheaterPattern:
    pattern_type: TheaterType
    severity: SeverityLevel
    file_path: str
    line_number: int
    description: str
    evidence: Dict[str, Any]
    recommendation: str
    confidence: float


@dataclass
class RealityValidationResult:
    is_valid: bool
    score: float
    issues: List[TheaterPattern]
    metrics: Dict[str, Any]
    timestamp: str


class TheaterDetector:
    def __init__(self):
        self.patterns = []

    def detect_test_gaming(self, file_path: str, content: str) -> List[TheaterPattern]:
        patterns = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        patterns.append(TheaterPattern(
                            pattern_type=TheaterType.TEST_GAMING,
                            severity=SeverityLevel.HIGH,
                            file_path=file_path,
                            line_number=node.lineno,
                            description="Empty test function - no actual testing",
                            evidence={"function_name": node.name, "body_length": len(node.body)},
                            recommendation="Implement actual test logic or remove empty test",
                            confidence=0.95
                        ))

                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Assert) and isinstance(stmt.test, ast.Constant):
                            if stmt.test.value is True:
                                patterns.append(TheaterPattern(
                                    pattern_type=TheaterType.TEST_GAMING,
                                    severity=SeverityLevel.CRITICAL,
                                    file_path=file_path,
                                    line_number=stmt.lineno,
                                    description="Test always passes with assert True",
                                    evidence={"function_name": node.name, "assertion": "True"},
                                    recommendation="Replace with meaningful assertions",
                                    confidence=0.98
                                ))

        except SyntaxError as e:
            logger.warning(f"Could not parse {file_path}: {e}")

        return patterns

    def detect_error_masking(self, file_path: str, content: str) -> List[TheaterPattern]:
        patterns = []

        if re.search(r'except\s*:', content):
            for i, line in enumerate(content.split('\n'), 1):
                if re.search(r'except\s*:', line):
                    patterns.append(TheaterPattern(
                        pattern_type=TheaterType.ERROR_MASKING,
                        severity=SeverityLevel.HIGH,
                        file_path=file_path,
                        line_number=i,
                        description="Bare except clause masks all errors",
                        evidence={"line": line.strip()},
                        recommendation="Catch specific exceptions and handle appropriately",
                        confidence=0.9
                    ))

        except_pass_pattern = r'except[^:]*:\s*\n\s*pass'
        for match in re.finditer(except_pass_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            patterns.append(TheaterPattern(
                pattern_type=TheaterType.ERROR_MASKING,
                severity=SeverityLevel.CRITICAL,
                file_path=file_path,
                line_number=line_num,
                description="Exception silently ignored with pass",
                evidence={"match": match.group()},
                recommendation="Log error or handle appropriately",
                confidence=0.95
            ))

        return patterns

    def detect_metrics_inflation(self, file_path: str, content: str) -> List[TheaterPattern]:
        patterns = []

        success_patterns = [
            r'coverage.*=.*100',
            r'score.*=.*1\.0',
            r'success.*=.*True',
            r'quality.*=.*"excellent"'
        ]

        for pattern in success_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                patterns.append(TheaterPattern(
                    pattern_type=TheaterType.METRICS_INFLATION,
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    line_number=line_num,
                    description="Hardcoded perfect metrics detected",
                    evidence={"match": match.group()},
                    recommendation="Calculate metrics dynamically from real data",
                    confidence=0.7
                ))

        return patterns

    def detect_all_patterns(self, file_path: str) -> List[TheaterPattern]:
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Could not read {file_path}: {e}")
            return []

        all_patterns = []
        all_patterns.extend(self.detect_test_gaming(file_path, content))
        all_patterns.extend(self.detect_error_masking(file_path, content))
        all_patterns.extend(self.detect_metrics_inflation(file_path, content))

        return all_patterns

    def analyze_directory(self, directory: str) -> List[TheaterPattern]:
        all_patterns = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    patterns = self.detect_all_patterns(file_path)
                    all_patterns.extend(patterns)

        return all_patterns

    def generate_report(self, patterns: List[TheaterPattern]) -> Dict[str, Any]:
        severity_counts = {s.value: 0 for s in SeverityLevel}
        type_counts = {t.value: 0 for t in TheaterType}

        for pattern in patterns:
            severity_counts[pattern.severity.value] += 1
            type_counts[pattern.pattern_type.value] += 1

        return {
            "total_patterns": len(patterns),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "patterns": [
                {
                    "type": p.pattern_type.value,
                    "severity": p.severity.value,
                    "file": p.file_path,
                    "line": p.line_number,
                    "description": p.description,
                    "evidence": p.evidence,
                    "recommendation": p.recommendation,
                    "confidence": p.confidence
                }
                for p in patterns
            ]
        }