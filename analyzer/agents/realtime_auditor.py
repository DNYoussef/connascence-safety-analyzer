"""
Real-Time Diagnostic Auditor Agent
===================================

Receives real-time diagnostic feeds from IDE/language servers and performs
continuous quality auditing with immediate feedback.

Data Sources:
- VS Code language server diagnostics (via MCP IDE integration)
- Python language server (pylsp, pyright)
- Real-time linting (ruff, mypy, bandit)
- Test runner events
- Git commit hooks

Audit Functions:
- Immediate violation detection
- Quality trend analysis
- Proactive remediation suggestions
- Compliance gate enforcement

@module RealtimeAuditor
@integration MCP-IDE, LSP, Git-Hooks
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from typing import Any, ClassVar, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticEvent:
    timestamp: str
    source: str
    file_path: str
    line_number: int
    severity: str
    message: str
    rule_id: Optional[str] = None
    code_context: Optional[str] = None


@dataclass
class AuditViolation:
    violation_id: str
    diagnostic_event: DiagnosticEvent
    violation_type: str
    severity: str
    quality_impact: str
    remediation_priority: int
    suggested_fix: Optional[str] = None


@dataclass
class AuditReport:
    period_start: str
    period_end: str
    total_events: int
    violation_count: int
    violations: List[AuditViolation]
    quality_score: float
    trend: str
    recommendations: List[str]


class RealtimeDiagnosticAuditor:
    # Constants for quality scoring
    SEVERITY_WEIGHTS: ClassVar[Dict[str, float]] = {"error": 5, "warning": 3, "information": 1, "hint": 0.5}
    QUALITY_THRESHOLDS: ClassVar[Dict[str, float]] = {"excellent": 0.95, "good": 0.85, "acceptable": 0.75, "poor": 0.60}

    # Magic value constants for trend detection and quality assessment
    MIN_SAMPLES_FOR_TREND: ClassVar[int] = 5
    TREND_WINDOW_SIZE: ClassVar[int] = 20
    TREND_THRESHOLD: ClassVar[float] = 0.05
    HIGH_PRIORITY_THRESHOLD: ClassVar[int] = 8

    def __init__(self, max_history: int = 1000):
        self.event_history: deque = deque(maxlen=max_history)
        self.violations: List[AuditViolation] = []
        self.quality_scores: deque = deque(maxlen=100)

    def ingest_diagnostic_event(self, diagnostic: Dict[str, Any]):
        event = DiagnosticEvent(
            timestamp=diagnostic.get("timestamp", datetime.now().isoformat()),
            source=diagnostic.get("source", "unknown"),
            file_path=diagnostic.get("file", ""),
            line_number=diagnostic.get("range", {}).get("start", {}).get("line", 0),
            severity=diagnostic.get("severity", "warning").lower(),
            message=diagnostic.get("message", ""),
            rule_id=diagnostic.get("code"),
            code_context=diagnostic.get("context"),
        )

        self.event_history.append(event)
        self._analyze_event(event)

    def _analyze_event(self, event: DiagnosticEvent):
        violation_type = self._classify_violation(event)

        if violation_type:
            quality_impact = self._assess_quality_impact(event, violation_type)
            priority = self._calculate_priority(event, quality_impact)

            violation = AuditViolation(
                violation_id=f"{event.source}:{event.file_path}:{event.line_number}",
                diagnostic_event=event,
                violation_type=violation_type,
                severity=event.severity,
                quality_impact=quality_impact,
                remediation_priority=priority,
                suggested_fix=self._generate_fix_suggestion(event, violation_type),
            )

            self.violations.append(violation)

    def _classify_violation(self, event: DiagnosticEvent) -> Optional[str]:
        message_lower = event.message.lower()

        if event.rule_id and event.rule_id.startswith("NASA"):
            return "nasa_compliance"

        if "security" in message_lower or "vulnerability" in message_lower:
            return "security"

        if "test" in message_lower and ("skip" in message_lower or "empty" in message_lower):
            return "test_quality"

        if "duplicate" in message_lower or "complexity" in message_lower:
            return "code_quality"

        if event.severity in ["error", "warning"]:
            return "general_quality"

        return None

    def _assess_quality_impact(self, event: DiagnosticEvent, violation_type: str) -> str:
        if violation_type == "nasa_compliance":
            return "critical"
        elif violation_type == "security" or event.severity == "error":
            return "high"
        elif violation_type == "test_quality" or event.severity == "warning":
            return "medium"
        else:
            return "low"

    def _calculate_priority(self, event: DiagnosticEvent, quality_impact: str) -> int:
        impact_scores = {"critical": 10, "high": 7, "medium": 4, "low": 2}

        severity_bonus = self.SEVERITY_WEIGHTS.get(event.severity, 0)
        base_priority = impact_scores.get(quality_impact, 5)

        return min(10, int(base_priority + severity_bonus / 2))

    def _generate_fix_suggestion(self, event: DiagnosticEvent, violation_type: str) -> Optional[str]:  # noqa: PLR0911
        """Generate fix suggestions for violations. Multiple returns needed for different violation types."""
        message_lower = event.message.lower()

        if violation_type == "nasa_compliance":
            if "function" in message_lower and "length" in message_lower:
                return "Refactor function to be under 60 lines per NASA Rule 1"
            elif "complexity" in message_lower:
                return "Reduce cyclomatic complexity below 15 per NASA Rule 2"
            elif "assertion" in message_lower:
                return "Add defensive assertions per NASA Rule 5"

        if violation_type == "security":
            if "password" in message_lower or "credential" in message_lower:
                return "Move credentials to environment variables or secrets manager"
            elif "sql" in message_lower:
                return "Use parameterized queries to prevent SQL injection"

        if violation_type == "test_quality":
            if "skip" in message_lower:
                return "Remove @skip decorator and fix test implementation"
            elif "assert true" in message_lower:
                return "Replace trivial assertion with meaningful test logic"

        return None

    def calculate_realtime_quality_score(self) -> float:
        if not self.event_history:
            return 1.0

        recent_events = list(self.event_history)[-50:]
        total_weight = 0.0
        violation_weight = 0.0

        for event in recent_events:
            weight = self.SEVERITY_WEIGHTS.get(event.severity, 1)
            total_weight += weight

            if event.severity in ["error", "warning"]:
                violation_weight += weight

        if total_weight == 0:
            return 1.0

        quality_score = 1.0 - (violation_weight / (total_weight * 2))
        quality_score = max(0.0, min(1.0, quality_score))

        self.quality_scores.append(quality_score)

        return quality_score

    def detect_quality_trend(self) -> str:
        if len(self.quality_scores) < self.MIN_SAMPLES_FOR_TREND:
            return "insufficient_data"

        recent = list(self.quality_scores)[-10:]
        avg_recent = sum(recent) / len(recent)

        older = (
            list(self.quality_scores)[-self.TREND_WINDOW_SIZE : -10]
            if len(self.quality_scores) >= self.TREND_WINDOW_SIZE
            else list(self.quality_scores)[:-10]
        )
        if not older:
            return "stable"

        avg_older = sum(older) / len(older)

        delta = avg_recent - avg_older

        if delta > self.TREND_THRESHOLD:
            return "improving"
        elif delta < -self.TREND_THRESHOLD:
            return "degrading"
        else:
            return "stable"

    def generate_recommendations(self, quality_score: float, trend: str) -> List[str]:
        recommendations = []

        if trend == "degrading":
            recommendations.append("URGENT: Quality trend is degrading - implement immediate quality intervention")

        high_priority_violations = [
            v for v in self.violations if v.remediation_priority >= self.HIGH_PRIORITY_THRESHOLD
        ]
        if high_priority_violations:
            recommendations.append(f"Address {len(high_priority_violations)} high-priority violations immediately")

        if quality_score < self.QUALITY_THRESHOLDS["acceptable"]:
            recommendations.append("Quality score below acceptable threshold - increase code review rigor")

        nasa_violations = [v for v in self.violations if v.violation_type == "nasa_compliance"]
        if nasa_violations:
            recommendations.append(f"Fix {len(nasa_violations)} NASA POT10 compliance violations before deployment")

        security_violations = [v for v in self.violations if v.violation_type == "security"]
        if security_violations:
            recommendations.append(f"Remediate {len(security_violations)} security vulnerabilities immediately")

        if not recommendations:
            recommendations.append("Quality metrics within acceptable range - maintain current practices")

        return recommendations

    def generate_audit_report(self, period_minutes: int = 60) -> AuditReport:
        now = datetime.now()
        period_start = (
            now.replace(microsecond=0) - __import__("datetime").timedelta(minutes=period_minutes)
        ).isoformat()
        period_end = now.isoformat()

        recent_events = [e for e in self.event_history if e.timestamp >= period_start]

        quality_score = self.calculate_realtime_quality_score()
        trend = self.detect_quality_trend()
        recommendations = self.generate_recommendations(quality_score, trend)

        return AuditReport(
            period_start=period_start,
            period_end=period_end,
            total_events=len(recent_events),
            violation_count=len(self.violations),
            violations=self.violations[-50:],
            quality_score=quality_score,
            trend=trend,
            recommendations=recommendations,
        )

    def export_report(self, report: AuditReport, output_path: str):
        report_data = {
            "audit_period": {"start": report.period_start, "end": report.period_end},
            "summary": {
                "total_events": report.total_events,
                "violation_count": report.violation_count,
                "quality_score": report.quality_score,
                "quality_level": self._get_quality_level(report.quality_score),
                "trend": report.trend,
            },
            "violations": [
                {
                    "id": v.violation_id,
                    "type": v.violation_type,
                    "severity": v.severity,
                    "quality_impact": v.quality_impact,
                    "priority": v.remediation_priority,
                    "file": v.diagnostic_event.file_path,
                    "line": v.diagnostic_event.line_number,
                    "message": v.diagnostic_event.message,
                    "suggested_fix": v.suggested_fix,
                }
                for v in report.violations
            ],
            "recommendations": report.recommendations,
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Audit report exported to {output_path}")

    def _get_quality_level(self, score: float) -> str:
        for level, threshold in sorted(self.QUALITY_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return level
        return "critical"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Real-Time Diagnostic Auditor")
    parser.add_argument("--diagnostics", required=True, help="Path to diagnostics JSON stream")
    parser.add_argument("--output", default="audit-report.json", help="Output file")
    parser.add_argument("--period-minutes", type=int, default=60, help="Audit period in minutes")

    args = parser.parse_args()

    auditor = RealtimeDiagnosticAuditor()

    with open(args.diagnostics) as f:
        diagnostics = json.load(f)

    if isinstance(diagnostics, list):
        for diagnostic in diagnostics:
            auditor.ingest_diagnostic_event(diagnostic)
    else:
        auditor.ingest_diagnostic_event(diagnostics)

    print(f"Processed {len(auditor.event_history)} diagnostic events")
    print(f"Identified {len(auditor.violations)} violations")

    report = auditor.generate_audit_report(args.period_minutes)

    print(f"\nQuality Score: {report.quality_score:.2%}")
    print(f"Trend: {report.trend}")
    print("\nRecommendations:")
    for rec in report.recommendations:
        print(f"  - {rec}")

    auditor.export_report(report, args.output)
    print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
