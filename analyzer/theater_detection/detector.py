"""
Theater Detection System for Connascence Analysis

Validates genuine quality improvements and prevents fabricated optimization claims.
Provides evidence-based verification of measurable quality gains.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
import functools
import json
import logging
import operator
from pathlib import Path
import statistics
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class QualityClaim:
    """Quality improvement claim to be validated"""

    claim_id: str
    description: str
    metric_name: str
    baseline_value: float
    improved_value: float
    improvement_percent: float
    measurement_method: str
    evidence_files: List[str]
    timestamp: float
    claim_type: str = "quality"  # quality, performance, security, maintainability


@dataclass
class ValidationResult:
    """Result of quality claim validation"""

    claim_id: str
    is_valid: bool
    confidence_score: float
    validation_method: str
    evidence_quality: str
    theater_indicators: List[str]
    genuine_indicators: List[str]
    recommendation: str
    risk_level: str  # low, medium, high


@dataclass
class TheaterPattern:
    """Pattern that indicates quality theater"""

    pattern_name: str
    description: str
    indicators: List[str]
    severity: str  # low, medium, high, critical
    detection_method: str
    applies_to: List[str]  # claim types this pattern applies to


class TheaterDetector:
    """
    Advanced theater detection system for connascence analysis that validates
    quality claims through evidence analysis, statistical validation, and pattern recognition.
    """

    def __init__(self):
        """Initialize theater detector with connascence-specific patterns"""
        self.validation_history: List[ValidationResult] = []
        self.theater_patterns = self._initialize_theater_patterns()
        self.connascence_weights = self._initialize_connascence_weights()

        # Validation thresholds optimized for code quality metrics
        self.validation_thresholds = {
            "minimum_improvement": 1.0,  # 1% minimum measurable improvement
            "maximum_believable": 95.0,  # 95% maximum believable improvement
            "confidence_threshold": 0.65,  # 65% confidence required
            "sample_size_minimum": 5,  # Minimum files/measurements
            "measurement_variance_max": 0.4,  # Maximum acceptable variance
            "evidence_completeness": 0.6,  # 60% evidence required
        }

        # Connascence-specific thresholds
        self.connascence_thresholds = {
            "critical_violations_max": 0,  # No critical violations allowed
            "high_violations_reduction": 50,  # Must reduce high violations by 50%
            "complexity_reduction": 20,  # 20% complexity reduction expected
            "maintainability_increase": 10,  # 10% maintainability improvement
        }

    def _initialize_theater_patterns(self) -> List[TheaterPattern]:
        """Initialize patterns that indicate quality theater in code analysis"""
        return [
            TheaterPattern(
                pattern_name="perfect_metrics",
                description="Claims perfect or near-perfect quality metrics",
                indicators=[
                    "zero violations claimed without evidence",
                    "100% test coverage with no test files",
                    "perfect maintainability index",
                    "all metrics improved by exact same percentage",
                ],
                severity="critical",
                detection_method="statistical_analysis",
                applies_to=["quality", "maintainability"],
            ),
            TheaterPattern(
                pattern_name="vanity_metrics",
                description="Focus on meaningless or easily gamed metrics",
                indicators=[
                    "only line count metrics reported",
                    "comment ratio as primary metric",
                    "file count reduction without context",
                    "formatting changes counted as improvements",
                ],
                severity="high",
                detection_method="metric_analysis",
                applies_to=["quality", "performance"],
            ),
            TheaterPattern(
                pattern_name="cherry_picked_results",
                description="Selective reporting of favorable results only",
                indicators=[
                    "only best files analyzed",
                    "ignoring test failures",
                    "excluding problematic modules",
                    "time window manipulation",
                ],
                severity="high",
                detection_method="completeness_analysis",
                applies_to=["quality", "security", "performance"],
            ),
            TheaterPattern(
                pattern_name="fake_refactoring",
                description="Cosmetic changes presented as structural improvements",
                indicators=[
                    "only whitespace changes",
                    "variable renaming without logic changes",
                    "comment additions without code changes",
                    "import reordering as optimization",
                ],
                severity="high",
                detection_method="diff_analysis",
                applies_to=["quality", "maintainability"],
            ),
            TheaterPattern(
                pattern_name="measurement_gaming",
                description="Manipulating measurement conditions for better results",
                indicators=[
                    "excluding initialization from timing",
                    "measuring empty test cases",
                    "baseline from debug mode",
                    "optimized build vs unoptimized baseline",
                ],
                severity="medium",
                detection_method="methodology_review",
                applies_to=["performance"],
            ),
            TheaterPattern(
                pattern_name="false_automation",
                description="Manual fixes claimed as automated improvements",
                indicators=[
                    "instant fix claims for complex issues",
                    "no automation code provided",
                    "fixes that require human judgment",
                    "pattern fixes without pattern detection",
                ],
                severity="medium",
                detection_method="automation_analysis",
                applies_to=["quality"],
            ),
            TheaterPattern(
                pattern_name="complexity_hiding",
                description="Moving complexity rather than reducing it",
                indicators=[
                    "complexity moved to external files",
                    "logic hidden in configuration",
                    "problems moved to dependencies",
                    "issues reclassified rather than fixed",
                ],
                severity="high",
                detection_method="structural_analysis",
                applies_to=["quality", "maintainability"],
            ),
            TheaterPattern(
                pattern_name="test_theater",
                description="Fake or meaningless test improvements",
                indicators=[
                    "test coverage without assertions",
                    "duplicate tests for coverage",
                    "testing getters/setters only",
                    "mocked everything tests",
                ],
                severity="high",
                detection_method="test_analysis",
                applies_to=["quality"],
            ),
        ]

    def _initialize_connascence_weights(self) -> Dict[str, float]:
        """Initialize importance weights for different connascence types"""
        return {
            "identity": 1.5,  # High weight - impacts maintainability
            "meaning": 1.2,  # Medium-high - affects understanding
            "algorithm": 2.0,  # Highest - correctness critical
            "position": 1.0,  # Medium - structural coupling
            "execution": 1.8,  # High - runtime dependencies
            "timing": 2.0,  # Highest - hardest to fix
            "values": 1.1,  # Medium - data coupling
            "type": 1.3,  # Medium-high - type safety
            "convention": 0.8,  # Lower - style issues
        }

    def validate_quality_claim(self, claim: QualityClaim) -> ValidationResult:
        """Comprehensive validation of quality improvement claim"""

        # Initialize validation result
        validation_result = ValidationResult(
            claim_id=claim.claim_id,
            is_valid=False,
            confidence_score=0.0,
            validation_method="comprehensive_analysis",
            evidence_quality="unknown",
            theater_indicators=[],
            genuine_indicators=[],
            recommendation="",
            risk_level="medium",
        )

        # Step 1: Statistical plausibility check
        statistical_score = self._validate_statistical_plausibility(claim)

        # Step 2: Evidence quality assessment
        evidence_score = self._assess_evidence_quality(claim)

        # Step 3: Theater pattern detection
        theater_indicators = self._detect_theater_patterns(claim)

        # Step 4: Genuine improvement indicators
        genuine_indicators = self._detect_genuine_indicators(claim)

        # Step 5: Connascence-specific validation
        connascence_score = self._validate_connascence_claim(claim)

        # Calculate overall confidence score
        confidence_score = self._calculate_confidence_score(
            statistical_score, evidence_score, connascence_score, theater_indicators, genuine_indicators
        )

        # Determine validity
        is_valid = (
            confidence_score >= self.validation_thresholds["confidence_threshold"]
            and len(theater_indicators) < 2
            and len(genuine_indicators) >= 2
        )

        # Determine risk level
        risk_level = self._assess_risk_level(confidence_score, theater_indicators)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            claim, statistical_score, evidence_score, connascence_score, theater_indicators, genuine_indicators
        )

        # Update validation result
        validation_result.is_valid = is_valid
        validation_result.confidence_score = confidence_score
        validation_result.evidence_quality = self._categorize_evidence_quality(evidence_score)
        validation_result.theater_indicators = theater_indicators
        validation_result.genuine_indicators = genuine_indicators
        validation_result.recommendation = recommendation
        validation_result.risk_level = risk_level

        # Store validation history
        self.validation_history.append(validation_result)

        logger.info(
            f"Validation complete for {claim.claim_id}: {'VALID' if is_valid else 'INVALID'} "
            f"(confidence: {confidence_score:.2f}, risk: {risk_level})"
        )

        return validation_result

    def _validate_statistical_plausibility(self, claim: QualityClaim) -> float:
        """Validate statistical plausibility of quality claim"""
        plausibility_score = 1.0

        # Check improvement magnitude
        improvement = abs(claim.improvement_percent)

        if improvement < self.validation_thresholds["minimum_improvement"]:
            plausibility_score *= 0.3  # Too small to be meaningful
        elif improvement > self.validation_thresholds["maximum_believable"]:
            plausibility_score *= 0.1  # Too large to be believable
        elif improvement > 70.0:
            plausibility_score *= 0.6  # Large improvements need strong evidence

        # Check for suspicious round numbers
        if improvement in [10.0, 20.0, 25.0, 50.0, 75.0, 90.0, 95.0, 100.0]:
            plausibility_score *= 0.5  # Suspiciously round

        # Check relationship between baseline and improved values
        if claim.baseline_value <= 0:
            plausibility_score *= 0.2  # Invalid baseline

        # Special checks for connascence metrics
        if "connascence" in claim.metric_name.lower() or "violation" in claim.metric_name.lower():
            # Violations should decrease
            if claim.improved_value > claim.baseline_value:
                plausibility_score *= 0.1  # Violations increased!

            # Complete elimination is suspicious
            if claim.improved_value == 0 and claim.baseline_value > 10:
                plausibility_score *= 0.3  # Suspicious complete elimination

        return max(0.0, min(1.0, plausibility_score))

    def _assess_evidence_quality(self, claim: QualityClaim) -> float:
        """Assess quality of evidence provided for quality claim"""
        evidence_score = 0.0
        evidence_components = []

        # Check for evidence files
        if not claim.evidence_files:
            return 0.1  # No evidence provided

        # Check measurement method description
        if claim.measurement_method:
            method = claim.measurement_method.lower()

            # Good methodology keywords
            good_keywords = [
                "baseline",
                "before",
                "after",
                "comparison",
                "measured",
                "analyzed",
                "files",
                "modules",
                "violations",
                "metrics",
            ]
            keyword_score = sum(1 for keyword in good_keywords if keyword in method)
            evidence_components.append(min(0.3, keyword_score * 0.05))

            # Check for specific measurement details
            if any(char.isdigit() for char in method):
                evidence_components.append(0.1)  # Contains numbers

            if len(method) > 50:
                evidence_components.append(0.1)  # Detailed description

        # Check evidence files
        for evidence_file in claim.evidence_files:
            file_path = Path(evidence_file)

            # Check file naming
            if any(
                keyword in evidence_file.lower()
                for keyword in ["report", "analysis", "metrics", "violations", "before", "after"]
            ):
                evidence_components.append(0.1)

            # Check file extensions
            if file_path.suffix in [".json", ".xml", ".csv", ".log", ".txt", ".md"]:
                evidence_components.append(0.05)

            # Bonus for multiple evidence files
            if len(claim.evidence_files) >= 2:
                evidence_components.append(0.1)
            if len(claim.evidence_files) >= 3:
                evidence_components.append(0.1)

        # Calculate total evidence score
        evidence_score = min(1.0, sum(evidence_components))

        return evidence_score

    def _detect_theater_patterns(self, claim: QualityClaim) -> List[str]:
        """Detect patterns that indicate quality theater"""
        detected_patterns = []

        for pattern in self.theater_patterns:
            if claim.claim_type in pattern.applies_to or "quality" in pattern.applies_to:
                if self._check_theater_pattern(claim, pattern):
                    detected_patterns.append(pattern.pattern_name)

        return detected_patterns

    def _check_theater_pattern(self, claim: QualityClaim, pattern: TheaterPattern) -> bool:
        """Check if a specific theater pattern is present"""

        if pattern.pattern_name == "perfect_metrics":
            # Check for suspiciously perfect improvements
            return claim.improved_value == 0 or claim.improvement_percent in {100.0, 0.0}

        elif pattern.pattern_name == "vanity_metrics":
            # Check if focusing on less important metrics
            metric = claim.metric_name.lower()
            vanity_keywords = ["lines", "files", "comments", "whitespace", "format"]
            return any(keyword in metric for keyword in vanity_keywords)

        elif pattern.pattern_name == "measurement_gaming":
            # Check for measurement manipulation indicators
            method = claim.measurement_method.lower()
            gaming_keywords = ["selected", "best", "excluding", "only", "subset"]
            return any(keyword in method for keyword in gaming_keywords)

        elif pattern.pattern_name == "fake_refactoring":
            # Check for cosmetic changes
            if "refactor" in claim.description.lower():
                return claim.improvement_percent < 5.0  # Small improvement for "refactoring"

        return False

    def _detect_genuine_indicators(self, claim: QualityClaim) -> List[str]:
        """Detect indicators of genuine quality improvements"""
        genuine_indicators = []

        # Realistic improvement magnitude
        improvement = abs(claim.improvement_percent)
        if 5.0 <= improvement <= 60.0:
            genuine_indicators.append("realistic_improvement_magnitude")

        # Non-round improvement percentage
        if improvement != round(improvement, 0) or improvement % 5 != 0:
            genuine_indicators.append("precise_measurement")

        # Multiple evidence sources
        if len(claim.evidence_files) >= 2:
            genuine_indicators.append("multiple_evidence_sources")

        # Detailed methodology
        if claim.measurement_method and len(claim.measurement_method) > 100:
            genuine_indicators.append("detailed_methodology")

        # Gradual improvement (not instant fix)
        if "gradual" in claim.description.lower() or "iterative" in claim.description.lower():
            genuine_indicators.append("gradual_improvement")

        # Specific metric targeting
        if any(conn_type in claim.metric_name.lower() for conn_type in self.connascence_weights):
            genuine_indicators.append("specific_connascence_targeting")

        return genuine_indicators

    def _validate_connascence_claim(self, claim: QualityClaim) -> float:
        """Validate claims specific to connascence improvements"""
        if "connascence" not in claim.metric_name.lower() and "violation" not in claim.metric_name.lower():
            return 0.5  # Not a connascence-specific claim, neutral score

        validation_score = 1.0

        # Check if targeting high-value connascence types
        for conn_type, weight in self.connascence_weights.items():
            if conn_type in claim.metric_name.lower():
                if weight >= 1.5:  # High-value target
                    validation_score *= 1.2
                break

        # Validate improvement magnitude based on connascence type
        improvement = claim.improvement_percent

        # Different expectations for different violation severities
        if "critical" in claim.description.lower():
            if improvement < 80.0:
                validation_score *= 0.7  # Critical should be mostly eliminated
        elif "high" in claim.description.lower() and improvement < 50.0:
            validation_score *= 0.8  # High should be significantly reduced

        # Check for comprehensive coverage
        if "all files" in claim.measurement_method.lower() or "entire codebase" in claim.measurement_method.lower():
            validation_score *= 1.1  # Bonus for comprehensive analysis

        return min(1.0, validation_score)

    def _calculate_confidence_score(
        self,
        statistical_score: float,
        evidence_score: float,
        connascence_score: float,
        theater_indicators: List[str],
        genuine_indicators: List[str],
    ) -> float:
        """Calculate overall confidence score for quality claim"""

        # Weighted base score
        base_score = (
            statistical_score * 0.3
            + evidence_score * 0.3
            + connascence_score * 0.4  # Higher weight for domain-specific validation
        )

        # Heavy penalty for theater indicators
        theater_penalty = len(theater_indicators) * 0.25
        base_score = max(0.0, base_score - theater_penalty)

        # Bonus for genuine indicators
        genuine_bonus = min(0.3, len(genuine_indicators) * 0.08)
        confidence_score = min(1.0, base_score + genuine_bonus)

        return round(confidence_score, 3)

    def _assess_risk_level(self, confidence_score: float, theater_indicators: List[str]) -> str:
        """Assess risk level of accepting the claim"""
        if len(theater_indicators) >= 3 or confidence_score < 0.3:
            return "high"
        elif len(theater_indicators) >= 1 or confidence_score < 0.6:
            return "medium"
        else:
            return "low"

    def _categorize_evidence_quality(self, evidence_score: float) -> str:
        """Categorize evidence quality based on score"""
        if evidence_score >= 0.8:
            return "excellent"
        elif evidence_score >= 0.6:
            return "good"
        elif evidence_score >= 0.4:
            return "fair"
        elif evidence_score >= 0.2:
            return "poor"
        else:
            return "insufficient"

    def _generate_recommendation(
        self,
        claim: QualityClaim,
        statistical_score: float,
        evidence_score: float,
        connascence_score: float,
        theater_indicators: List[str],
        genuine_indicators: List[str],
    ) -> str:
        """Generate actionable recommendation based on validation results"""

        if len(theater_indicators) >= 2:
            return (
                f"REJECT: Multiple theater patterns detected ({', '.join(theater_indicators)}). "
                f"Provide genuine evidence with comprehensive methodology and reproducible results."
            )

        if evidence_score < 0.3:
            return (
                "INSUFFICIENT EVIDENCE: Provide comprehensive analysis reports, "
                "before/after metrics, and detailed methodology description."
            )

        if statistical_score < 0.4:
            return (
                "STATISTICAL CONCERNS: Improvement claims appear unrealistic. "
                "Verify measurements and provide additional validation data."
            )

        if connascence_score < 0.4:
            return (
                "DOMAIN VALIDATION FAILED: Connascence improvements don't align with expectations. "
                "Focus on high-impact violation types with realistic reduction targets."
            )

        if len(genuine_indicators) < 2:
            return (
                "NEEDS VALIDATION: Provide additional evidence such as "
                "progressive improvement data, comprehensive coverage reports, "
                "or third-party verification."
            )

        confidence = statistical_score * 0.3 + evidence_score * 0.3 + connascence_score * 0.4

        if confidence >= 0.8 and len(genuine_indicators) >= 4:
            return "ACCEPT: Quality improvement claim validated with high confidence. Evidence is comprehensive and credible."
        elif confidence >= 0.65:
            return "CONDITIONAL ACCEPT: Quality improvement appears genuine but requires monitoring and follow-up validation."
        else:
            return "REVIEW REQUIRED: Additional review and evidence needed before acceptance."

    def detect_systemic_theater(self, claims: List[QualityClaim]) -> Dict[str, Any]:
        """Detect systemic patterns across multiple claims that indicate theater"""
        if len(claims) < 2:
            return {"error": "Need at least 2 claims for systemic analysis"}

        systemic_indicators = []

        # Check for uniform improvements
        improvements = [c.improvement_percent for c in claims]
        if statistics.stdev(improvements) < 3.0:
            systemic_indicators.append("uniform_improvements_across_claims")

        # Check for escalating claims
        if all(improvements[i] < improvements[i + 1] for i in range(len(improvements) - 1)):
            systemic_indicators.append("escalating_improvement_pattern")

        # Check for identical evidence patterns
        evidence_patterns = [len(c.evidence_files) for c in claims]
        if len(set(evidence_patterns)) == 1:
            systemic_indicators.append("identical_evidence_structure")

        # Check for timing patterns
        timestamps = [c.timestamp for c in claims]
        if len(timestamps) > 2:
            intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
            if all(abs(interval - intervals[0]) < 60 for interval in intervals):
                systemic_indicators.append("suspiciously_regular_timing")

        return {
            "systemic_theater_indicators": systemic_indicators,
            "risk_assessment": "high" if len(systemic_indicators) >= 2 else "medium" if systemic_indicators else "low",
            "recommendation": self._generate_systemic_recommendation(systemic_indicators),
        }

    def _generate_systemic_recommendation(self, indicators: List[str]) -> str:
        """Generate recommendation based on systemic patterns"""
        if not indicators:
            return "No systemic theater patterns detected. Individual claim validation recommended."
        elif len(indicators) >= 3:
            return "CRITICAL: Multiple systemic theater patterns detected. Full audit required."
        elif len(indicators) >= 2:
            return "WARNING: Systemic patterns suggest coordinated theater. Independent validation required."
        else:
            return "CAUTION: Some patterns detected. Additional scrutiny recommended."

    def export_validation_report(self, claims: List[QualityClaim], output_path: Optional[Path] = None) -> str:
        """Export comprehensive validation report"""

        # Validate all claims
        results = [self.validate_quality_claim(claim) for claim in claims]

        # Perform systemic analysis
        systemic_analysis = self.detect_systemic_theater(claims)

        # Generate report
        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "analyzer": "Connascence Theater Detector",
                "version": "1.0.0",
                "total_claims": len(claims),
            },
            "summary": {
                "valid_claims": sum(1 for r in results if r.is_valid),
                "invalid_claims": sum(1 for r in results if not r.is_valid),
                "average_confidence": statistics.mean([r.confidence_score for r in results]),
                "high_risk_claims": sum(1 for r in results if r.risk_level == "high"),
            },
            "systemic_analysis": systemic_analysis,
            "individual_results": [asdict(r) for r in results],
            "theater_patterns_detected": list(set(functools.reduce(operator.iadd, [r.theater_indicators for r in results], []))),
            "recommendations": {
                "immediate_actions": self._generate_immediate_actions(results),
                "long_term_improvements": self._generate_long_term_improvements(results),
            },
        }

        # Save report
        if output_path is None:
            output_path = Path(f".claude/.artifacts/theater_detection/report_{int(time.time())}.json")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Theater detection report exported to {output_path}")
        return str(output_path)

    def _generate_immediate_actions(self, results: List[ValidationResult]) -> List[str]:
        """Generate immediate action items based on validation results"""
        actions = []

        invalid_count = sum(1 for r in results if not r.is_valid)
        if invalid_count > 0:
            actions.append(f"Review and re-validate {invalid_count} rejected claims")

        high_risk = [r for r in results if r.risk_level == "high"]
        if high_risk:
            actions.append(f"Immediate audit required for {len(high_risk)} high-risk claims")

        common_patterns = {}
        for r in results:
            for pattern in r.theater_indicators:
                common_patterns[pattern] = common_patterns.get(pattern, 0) + 1

        if common_patterns:
            most_common = max(common_patterns, key=common_patterns.get)
            actions.append(f"Address '{most_common}' pattern (found in {common_patterns[most_common]} claims)")

        return actions if actions else ["No immediate actions required"]

    def _generate_long_term_improvements(self, results: List[ValidationResult]) -> List[str]:
        """Generate long-term improvement recommendations"""
        improvements = []

        avg_confidence = statistics.mean([r.confidence_score for r in results])
        if avg_confidence < 0.7:
            improvements.append("Improve evidence collection and documentation processes")

        poor_evidence = sum(1 for r in results if r.evidence_quality in ["poor", "insufficient"])
        if poor_evidence > len(results) * 0.3:
            improvements.append("Establish standardized evidence requirements and templates")

        if any("fake_refactoring" in r.theater_indicators for r in results):
            improvements.append("Implement automated diff analysis for refactoring claims")

        if any("measurement_gaming" in r.theater_indicators for r in results):
            improvements.append("Standardize measurement methodology and tooling")

        improvements.append("Regular training on quality metrics and genuine improvement techniques")

        return improvements
