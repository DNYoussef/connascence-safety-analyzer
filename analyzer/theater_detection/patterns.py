"""
Theater Pattern Library for Connascence Analysis

Comprehensive library of performance theater patterns specific to
code quality and connascence detection.
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatternRule:
    """Rule for detecting a specific theater pattern"""
    rule_id: str
    description: str
    check_function: Callable
    weight: float  # Importance weight 0-1
    categories: List[str]  # Pattern categories this rule belongs to


class TheaterPatternLibrary:
    """
    Library of theater patterns specific to connascence and code quality analysis.
    Provides pattern detection, classification, and scoring.
    """

    def __init__(self):
        """Initialize pattern library with comprehensive detection rules"""
        self.patterns = self._initialize_patterns()
        self.pattern_categories = self._initialize_categories()
        self.detection_history = []

    def _initialize_categories(self) -> Dict[str, str]:
        """Initialize pattern categories with descriptions"""
        return {
            "metric_manipulation": "Manipulating metrics to show false improvements",
            "evidence_fabrication": "Creating or altering evidence to support claims",
            "scope_gaming": "Manipulating analysis scope to hide problems",
            "cosmetic_changes": "Superficial changes presented as improvements",
            "test_theater": "Fake or meaningless test improvements",
            "documentation_theater": "Documentation that doesn't reflect reality",
            "automation_theater": "False claims about automation capabilities",
            "complexity_shifting": "Moving problems rather than solving them"
        }

    def _initialize_patterns(self) -> Dict[str, List[PatternRule]]:
        """Initialize comprehensive pattern detection rules"""
        return {
            "metric_manipulation": [
                PatternRule(
                    rule_id="MM001",
                    description="Round number improvements (exactly 50%, 75%, etc.)",
                    check_function=self._check_round_numbers,
                    weight=0.8,
                    categories=["metric_manipulation"]
                ),
                PatternRule(
                    rule_id="MM002",
                    description="All metrics improved by same percentage",
                    check_function=self._check_uniform_improvements,
                    weight=0.9,
                    categories=["metric_manipulation"]
                ),
                PatternRule(
                    rule_id="MM003",
                    description="Cherry-picked time windows",
                    check_function=self._check_time_window_manipulation,
                    weight=0.7,
                    categories=["metric_manipulation", "scope_gaming"]
                )
            ],
            "evidence_fabrication": [
                PatternRule(
                    rule_id="EF001",
                    description="Missing baseline measurements",
                    check_function=self._check_missing_baseline,
                    weight=0.9,
                    categories=["evidence_fabrication"]
                ),
                PatternRule(
                    rule_id="EF002",
                    description="Identical before/after evidence",
                    check_function=self._check_identical_evidence,
                    weight=1.0,
                    categories=["evidence_fabrication"]
                ),
                PatternRule(
                    rule_id="EF003",
                    description="Generated or synthetic data patterns",
                    check_function=self._check_synthetic_data,
                    weight=0.8,
                    categories=["evidence_fabrication"]
                )
            ],
            "scope_gaming": [
                PatternRule(
                    rule_id="SG001",
                    description="Excluding problematic files",
                    check_function=self._check_selective_exclusion,
                    weight=0.8,
                    categories=["scope_gaming"]
                ),
                PatternRule(
                    rule_id="SG002",
                    description="Only analyzing simple/clean code",
                    check_function=self._check_cherry_picked_files,
                    weight=0.7,
                    categories=["scope_gaming"]
                ),
                PatternRule(
                    rule_id="SG003",
                    description="Ignoring critical violations",
                    check_function=self._check_ignored_criticals,
                    weight=0.9,
                    categories=["scope_gaming", "metric_manipulation"]
                )
            ],
            "cosmetic_changes": [
                PatternRule(
                    rule_id="CC001",
                    description="Whitespace/formatting as improvement",
                    check_function=self._check_whitespace_changes,
                    weight=0.6,
                    categories=["cosmetic_changes"]
                ),
                PatternRule(
                    rule_id="CC002",
                    description="Comment changes without code changes",
                    check_function=self._check_comment_only_changes,
                    weight=0.5,
                    categories=["cosmetic_changes", "documentation_theater"]
                ),
                PatternRule(
                    rule_id="CC003",
                    description="Import reordering as optimization",
                    check_function=self._check_import_reordering,
                    weight=0.4,
                    categories=["cosmetic_changes"]
                )
            ],
            "test_theater": [
                PatternRule(
                    rule_id="TT001",
                    description="Tests without assertions",
                    check_function=self._check_assertionless_tests,
                    weight=0.9,
                    categories=["test_theater"]
                ),
                PatternRule(
                    rule_id="TT002",
                    description="100% coverage with no real tests",
                    check_function=self._check_fake_coverage,
                    weight=1.0,
                    categories=["test_theater", "metric_manipulation"]
                ),
                PatternRule(
                    rule_id="TT003",
                    description="Testing only trivial methods",
                    check_function=self._check_trivial_test_focus,
                    weight=0.7,
                    categories=["test_theater"]
                )
            ],
            "complexity_shifting": [
                PatternRule(
                    rule_id="CS001",
                    description="Moving complexity to config files",
                    check_function=self._check_complexity_to_config,
                    weight=0.8,
                    categories=["complexity_shifting"]
                ),
                PatternRule(
                    rule_id="CS002",
                    description="Hiding violations in generated code",
                    check_function=self._check_generated_code_hiding,
                    weight=0.9,
                    categories=["complexity_shifting", "scope_gaming"]
                ),
                PatternRule(
                    rule_id="CS003",
                    description="Reclassifying issues rather than fixing",
                    check_function=self._check_issue_reclassification,
                    weight=0.7,
                    categories=["complexity_shifting", "metric_manipulation"]
                )
            ]
        }

    # Pattern detection methods
    def _check_round_numbers(self, data: Dict) -> bool:
        """Check for suspiciously round improvement percentages"""
        if 'improvement_percent' not in data:
            return False

        improvement = data['improvement_percent']
        suspicious_values = [10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 100]
        return improvement in suspicious_values

    def _check_uniform_improvements(self, data: Dict) -> bool:
        """Check if all metrics improved by the same percentage"""
        if 'metrics' not in data or len(data['metrics']) < 2:
            return False

        improvements = [m.get('improvement', 0) for m in data['metrics'].values()]
        if len(set(improvements)) == 1 and improvements[0] != 0:
            return True

        # Check if improvements are suspiciously similar
        if len(improvements) > 2:
            avg = sum(improvements) / len(improvements)
            variance = sum((x - avg) ** 2 for x in improvements) / len(improvements)
            return variance < 1.0  # Very low variance

        return False

    def _check_time_window_manipulation(self, data: Dict) -> bool:
        """Check for cherry-picked time windows"""
        if 'measurement_window' not in data:
            return False

        window = data['measurement_window']
        # Suspicious if very short window or specific time selection
        return (window.get('duration_seconds', float('inf')) < 60 or
                'selected_period' in window or
                'best_results' in str(window).lower())

    def _check_missing_baseline(self, data: Dict) -> bool:
        """Check for missing baseline measurements"""
        return ('baseline_value' not in data or
                data.get('baseline_value') is None or
                data.get('baseline_value') == 0)

    def _check_identical_evidence(self, data: Dict) -> bool:
        """Check if before/after evidence is identical"""
        if 'evidence' not in data:
            return False

        evidence = data['evidence']
        if 'before' in evidence and 'after' in evidence:
            # Simple check - in practice would hash or diff
            return evidence['before'] == evidence['after']
        return False

    def _check_synthetic_data(self, data: Dict) -> bool:
        """Check for patterns indicating synthetic/generated data"""
        if 'measurements' not in data:
            return False

        measurements = data['measurements']
        if isinstance(measurements, list) and len(measurements) > 5:
            # Check for too-perfect patterns
            diffs = [measurements[i+1] - measurements[i] for i in range(len(measurements)-1)]
            # Perfect linear progression is suspicious
            return len(set(diffs)) == 1
        return False

    def _check_selective_exclusion(self, data: Dict) -> bool:
        """Check for selective file exclusion"""
        if 'excluded_files' in data or 'excluded_patterns' in data:
            # Excluding more than 20% is suspicious
            total = data.get('total_files', 0)
            excluded = len(data.get('excluded_files', []))
            if total > 0 and excluded / total > 0.2:
                return True

        # Check for suspicious exclusion keywords
        method = str(data.get('measurement_method', '')).lower()
        return any(keyword in method for keyword in ['excluding', 'except', 'ignoring', 'skipping'])

    def _check_cherry_picked_files(self, data: Dict) -> bool:
        """Check if only simple files were analyzed"""
        if 'analyzed_files' not in data:
            return False

        files = data['analyzed_files']
        # Check for suspicious patterns in file selection
        suspicious_patterns = ['test_', 'simple_', 'example_', '__init__', 'config']

        if isinstance(files, list):
            suspicious_count = sum(1 for f in files if any(p in str(f).lower() for p in suspicious_patterns))
            return suspicious_count > len(files) * 0.5
        return False

    def _check_ignored_criticals(self, data: Dict) -> bool:
        """Check if critical violations were ignored"""
        if 'violations' in data:
            violations = data['violations']
            # Check if criticals were mentioned but not addressed
            if 'critical' in violations:
                return violations['critical'].get('ignored', False) or violations['critical'].get('count', 0) > 0

        return 'ignoring_critical' in str(data).lower()

    def _check_whitespace_changes(self, data: Dict) -> bool:
        """Check if changes are primarily whitespace"""
        if 'changes' not in data:
            return False

        changes = data.get('changes', {})
        return (changes.get('type') == 'formatting' or
                changes.get('whitespace_only', False) or
                'indent' in str(changes).lower())

    def _check_comment_only_changes(self, data: Dict) -> bool:
        """Check if changes are only comments"""
        if 'changes' not in data:
            return False

        changes = data.get('changes', {})
        return (changes.get('type') == 'documentation' or
                changes.get('comment_only', False) or
                (changes.get('lines_added', 0) > 0 and changes.get('code_changed', 0) == 0))

    def _check_import_reordering(self, data: Dict) -> bool:
        """Check if import reordering is claimed as improvement"""
        desc = str(data.get('description', '')).lower()
        changes = str(data.get('changes', '')).lower()

        return (('import' in desc and 'reorder' in desc) or
                ('import' in changes and any(word in changes for word in ['sort', 'organize', 'reorder'])))

    def _check_assertionless_tests(self, data: Dict) -> bool:
        """Check for tests without assertions"""
        if 'test_metrics' not in data:
            return False

        metrics = data['test_metrics']
        return (metrics.get('assertion_count', 1) == 0 or
                metrics.get('assertion_ratio', 1) < 0.1)

    def _check_fake_coverage(self, data: Dict) -> bool:
        """Check for fake test coverage"""
        if 'coverage' not in data:
            return False

        coverage = data['coverage']
        # 100% coverage with few tests is suspicious
        return (coverage.get('percentage', 0) == 100 and
                coverage.get('test_count', float('inf')) < 10)

    def _check_trivial_test_focus(self, data: Dict) -> bool:
        """Check if testing only trivial methods"""
        if 'tested_methods' not in data:
            return False

        methods = data['tested_methods']
        trivial_patterns = ['getter', 'setter', 'toString', '__str__', '__repr__', 'init']

        if isinstance(methods, list):
            trivial_count = sum(1 for m in methods if any(p in str(m).lower() for p in trivial_patterns))
            return trivial_count > len(methods) * 0.7
        return False

    def _check_complexity_to_config(self, data: Dict) -> bool:
        """Check if complexity moved to configuration"""
        changes = data.get('changes', {})
        return (changes.get('config_lines_added', 0) > changes.get('code_lines_removed', 0) * 0.5 and
                changes.get('code_lines_removed', 0) > 10)

    def _check_generated_code_hiding(self, data: Dict) -> bool:
        """Check if violations hidden in generated code"""
        if 'excluded_patterns' in data:
            patterns = data['excluded_patterns']
            generated_patterns = ['generated', 'auto-gen', 'compiled', 'build', 'dist']
            return any(gen in str(patterns).lower() for gen in generated_patterns)
        return False

    def _check_issue_reclassification(self, data: Dict) -> bool:
        """Check if issues reclassified rather than fixed"""
        if 'reclassifications' in data:
            return data['reclassifications'].get('count', 0) > 0

        # Check for reclassification keywords
        desc = str(data.get('description', '')).lower()
        return any(word in desc for word in ['reclassified', 'recategorized', 'downgraded', 'suppressed'])

    def detect_patterns(self, data: Dict) -> Dict[str, List[str]]:
        """
        Detect all theater patterns in the provided data

        Args:
            data: Data to analyze for theater patterns

        Returns:
            Dictionary of detected patterns by category
        """
        detected = {}

        for category, rules in self.patterns.items():
            detected_in_category = []

            for rule in rules:
                try:
                    if rule.check_function(data):
                        detected_in_category.append(rule.rule_id)
                        logger.debug(f"Pattern detected: {rule.rule_id} - {rule.description}")
                except Exception as e:
                    logger.warning(f"Error checking pattern {rule.rule_id}: {e}")

            if detected_in_category:
                detected[category] = detected_in_category

        # Store in history
        self.detection_history.append({
            'data_hash': hash(str(data)),
            'patterns_detected': detected,
            'timestamp': __import__('time').time()
        })

        return detected

    def calculate_theater_score(self, detected_patterns: Dict[str, List[str]]) -> float:
        """
        Calculate overall theater score based on detected patterns

        Args:
            detected_patterns: Dictionary of detected patterns by category

        Returns:
            Theater score from 0 (no theater) to 1 (definite theater)
        """
        if not detected_patterns:
            return 0.0

        total_weight = 0.0
        total_patterns = 0

        for category, pattern_ids in detected_patterns.items():
            for pattern_id in pattern_ids:
                # Find the rule and add its weight
                for rules in self.patterns.values():
                    for rule in rules:
                        if rule.rule_id == pattern_id:
                            total_weight += rule.weight
                            total_patterns += 1
                            break

        if total_patterns == 0:
            return 0.0

        # Normalize score
        max_possible_weight = total_patterns * 1.0  # Maximum weight per pattern is 1.0
        score = min(1.0, total_weight / max_possible_weight)

        # Apply severity multiplier based on number of patterns
        if total_patterns >= 5:
            score = min(1.0, score * 1.3)
        elif total_patterns >= 3:
            score = min(1.0, score * 1.1)

        return round(score, 3)

    def get_pattern_description(self, pattern_id: str) -> Optional[str]:
        """Get description for a specific pattern ID"""
        for rules in self.patterns.values():
            for rule in rules:
                if rule.rule_id == pattern_id:
                    return rule.description
        return None

    def get_remediation_advice(self, detected_patterns: Dict[str, List[str]]) -> List[str]:
        """
        Generate remediation advice based on detected patterns

        Args:
            detected_patterns: Dictionary of detected patterns by category

        Returns:
            List of remediation recommendations
        """
        advice = []

        if 'metric_manipulation' in detected_patterns:
            advice.append("Provide raw, unprocessed metrics with full methodology")

        if 'evidence_fabrication' in detected_patterns:
            advice.append("Include comprehensive baseline measurements and verifiable evidence")

        if 'scope_gaming' in detected_patterns:
            advice.append("Analyze the complete codebase without selective exclusions")

        if 'cosmetic_changes' in detected_patterns:
            advice.append("Focus on substantive code improvements rather than formatting")

        if 'test_theater' in detected_patterns:
            advice.append("Write meaningful tests with proper assertions and coverage")

        if 'complexity_shifting' in detected_patterns:
            advice.append("Address root causes rather than moving problems elsewhere")

        if not advice:
            advice.append("Continue following best practices for transparent quality reporting")

        return advice