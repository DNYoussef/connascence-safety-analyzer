"""
Evidence Validator for Theater Detection

Validates evidence quality and authenticity for connascence analysis claims.
"""

from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class EvidenceValidator:
    """
    Validates evidence provided for quality improvement claims.
    Checks for authenticity, completeness, and consistency.
    """

    def __init__(self):
        """Initialize evidence validator with validation rules"""
        self.validation_rules = self._initialize_validation_rules()
        self.evidence_cache = {}
        self.validation_history = []

    def _initialize_validation_rules(self) -> Dict[str, Dict]:
        """Initialize validation rules for different evidence types"""
        return {
            "metrics_report": {
                "required_fields": ["timestamp", "metrics", "file_count", "violation_count"],
                "format_patterns": [r"\.json$", r"\.xml$", r"\.csv$"],
                "min_size_bytes": 100,
                "max_age_days": 30,
            },
            "baseline_measurement": {
                "required_fields": ["baseline_date", "baseline_values", "measurement_method"],
                "format_patterns": [r"\.json$", r"\.log$", r"\.txt$"],
                "min_size_bytes": 50,
                "max_age_days": 90,
            },
            "improvement_data": {
                "required_fields": ["before", "after", "change_percentage"],
                "format_patterns": [r"\.json$", r"\.csv$"],
                "min_size_bytes": 100,
                "max_age_days": 7,
            },
            "test_results": {
                "required_fields": ["test_count", "pass_count", "coverage"],
                "format_patterns": [r"\.xml$", r"\.json$", r"\.html$"],
                "min_size_bytes": 500,
                "max_age_days": 3,
            },
            "violation_report": {
                "required_fields": ["violations", "severity_distribution", "file_list"],
                "format_patterns": [r"\.json$", r"\.sarif$", r"\.xml$"],
                "min_size_bytes": 200,
                "max_age_days": 7,
            },
        }

    def validate_evidence_file(self, file_path: str, evidence_type: str) -> Tuple[bool, str, float]:
        """
        Validate an evidence file

        Args:
            file_path: Path to the evidence file
            evidence_type: Type of evidence (metrics_report, baseline_measurement, etc.)

        Returns:
            Tuple of (is_valid, validation_message, confidence_score)
        """
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            return False, f"File does not exist: {file_path}", 0.0

        # Get validation rules for this evidence type
        if evidence_type not in self.validation_rules:
            return False, f"Unknown evidence type: {evidence_type}", 0.0

        rules = self.validation_rules[evidence_type]
        confidence_score = 1.0
        issues = []

        # Check file format
        format_valid = any(re.search(pattern, file_path) for pattern in rules["format_patterns"])
        if not format_valid:
            confidence_score *= 0.7
            issues.append(f"Non-standard format for {evidence_type}")

        # Check file size
        file_size = path.stat().st_size
        if file_size < rules["min_size_bytes"]:
            confidence_score *= 0.5
            issues.append(f"File too small ({file_size} bytes)")

        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
        if file_age.days > rules["max_age_days"]:
            confidence_score *= 0.8
            issues.append(f"File is {file_age.days} days old")

        # Try to parse and validate content
        content_valid, content_message, content_score = self._validate_file_content(path, rules["required_fields"])
        if not content_valid:
            issues.append(content_message)
        confidence_score *= content_score

        # Generate validation message
        if confidence_score >= 0.8:
            message = "Evidence file validated successfully"
        elif confidence_score >= 0.5:
            message = f"Evidence partially validated. Issues: {', '.join(issues)}"
        else:
            message = f"Evidence validation failed. Issues: {', '.join(issues)}"

        # Cache result
        file_hash = self._hash_file(path)
        self.evidence_cache[file_hash] = {
            "path": file_path,
            "type": evidence_type,
            "valid": confidence_score >= 0.5,
            "score": confidence_score,
            "timestamp": datetime.now().isoformat(),
        }

        return confidence_score >= 0.5, message, confidence_score

    def _validate_file_content(self, path: Path, required_fields: List[str]) -> Tuple[bool, str, float]:
        """Validate the content of an evidence file"""
        try:
            # Try to read file content
            content = path.read_text(encoding="utf-8")

            # Try JSON parsing
            if path.suffix == ".json":
                try:
                    data = json.loads(content)
                    return self._validate_json_structure(data, required_fields)
                except json.JSONDecodeError:
                    return False, "Invalid JSON format", 0.3

            # Check for required fields in text content
            found_fields = sum(1 for field in required_fields if field in content.lower())
            field_ratio = found_fields / len(required_fields) if required_fields else 1.0

            if field_ratio >= 0.8:
                return True, "Content structure validated", field_ratio
            elif field_ratio >= 0.5:
                return True, "Partial content structure found", field_ratio * 0.8
            else:
                return False, "Required fields missing", field_ratio * 0.5

        except Exception as e:
            return False, f"Error reading file: {e!s}", 0.1

    def _validate_json_structure(self, data: Dict, required_fields: List[str]) -> Tuple[bool, str, float]:
        """Validate JSON structure against required fields"""
        missing_fields = [field for field in required_fields if field not in data]

        if not missing_fields:
            return True, "All required fields present", 1.0
        elif len(missing_fields) < len(required_fields) / 2:
            return True, f"Some fields missing: {', '.join(missing_fields)}", 0.7
        else:
            return False, f"Many fields missing: {', '.join(missing_fields)}", 0.3

    def validate_evidence_consistency(self, evidence_files: List[Dict[str, Any]]) -> Tuple[bool, str, float]:
        """
        Validate consistency across multiple evidence files

        Args:
            evidence_files: List of evidence file metadata

        Returns:
            Tuple of (is_consistent, message, confidence_score)
        """
        if len(evidence_files) < 2:
            return True, "Single evidence file", 0.7

        confidence_score = 1.0
        inconsistencies = []

        # Check temporal consistency
        timestamps = []
        for file_data in evidence_files:
            if "timestamp" in file_data:
                timestamps.append(file_data["timestamp"])

        if timestamps:
            timestamps.sort()
            # Check for suspicious gaps or patterns
            for i in range(1, len(timestamps)):
                gap = timestamps[i] - timestamps[i - 1]
                if gap < 1:  # Less than 1 second between files
                    confidence_score *= 0.7
                    inconsistencies.append("Suspiciously close timestamps")
                    break

        # Check metric consistency
        metrics = []
        for file_data in evidence_files:
            if "metrics" in file_data:
                metrics.append(file_data["metrics"])

        if metrics and self._check_metric_inconsistency(metrics):
            confidence_score *= 0.6
            inconsistencies.append("Inconsistent metrics across files")

        # Check for duplicate content
        if self._check_duplicate_evidence(evidence_files):
            confidence_score *= 0.3
            inconsistencies.append("Duplicate evidence detected")

        # Generate consistency message
        if confidence_score >= 0.8:
            message = "Evidence is consistent"
        elif confidence_score >= 0.5:
            message = f"Minor inconsistencies: {', '.join(inconsistencies)}"
        else:
            message = f"Major inconsistencies: {', '.join(inconsistencies)}"

        return confidence_score >= 0.5, message, confidence_score

    def _check_metric_inconsistency(self, metrics: List[Dict]) -> bool:
        """Check for inconsistencies in metrics across files"""
        if len(metrics) < 2:
            return False

        # Check if metrics contradict each other
        for i in range(1, len(metrics)):
            prev = metrics[i - 1]
            curr = metrics[i]

            # Check for impossible improvements
            for key in set(prev.keys()) & set(curr.keys()):
                if isinstance(prev[key], (int, float)) and isinstance(curr[key], (int, float)):
                    # Violations should decrease, not increase
                    if "violation" in key.lower() and curr[key] > prev[key] * 1.5:
                        return True
                    # Complexity should decrease, not increase
                    if "complexity" in key.lower() and curr[key] > prev[key] * 1.2:
                        return True

        return False

    def _check_duplicate_evidence(self, evidence_files: List[Dict]) -> bool:
        """Check for duplicate evidence across files"""
        hashes = set()
        for file_data in evidence_files:
            if "content_hash" in file_data:
                if file_data["content_hash"] in hashes:
                    return True
                hashes.add(file_data["content_hash"])
        return False

    def validate_measurement_methodology(self, methodology: str) -> Tuple[bool, str, float]:
        """
        Validate the measurement methodology description

        Args:
            methodology: Description of measurement methodology

        Returns:
            Tuple of (is_valid, message, confidence_score)
        """
        if not methodology or len(methodology) < 20:
            return False, "Methodology description too short or missing", 0.1

        confidence_score = 0.5  # Base score
        good_indicators = []
        bad_indicators = []

        # Check for good methodology keywords
        good_keywords = [
            "baseline",
            "control",
            "repeated",
            "average",
            "statistical",
            "sample",
            "measurement",
            "methodology",
            "procedure",
            "protocol",
            "before",
            "after",
            "comparison",
            "benchmark",
            "standard",
        ]

        for keyword in good_keywords:
            if keyword in methodology.lower():
                confidence_score += 0.05
                good_indicators.append(keyword)

        # Check for bad methodology indicators
        bad_keywords = [
            "roughly",
            "approximately",
            "guess",
            "estimate",
            "probably",
            "maybe",
            "instant",
            "immediate",
            "perfect",
            "magic",
        ]

        for keyword in bad_keywords:
            if keyword in methodology.lower():
                confidence_score -= 0.1
                bad_indicators.append(keyword)

        # Check for specific measurements
        if re.search(r"\d+", methodology):
            confidence_score += 0.1  # Contains numbers
            good_indicators.append("specific measurements")

        # Check for time periods
        if re.search(r"\d+\s*(day|hour|minute|second|week|month)", methodology.lower()):
            confidence_score += 0.05
            good_indicators.append("time periods specified")

        # Ensure score is within bounds
        confidence_score = max(0.0, min(1.0, confidence_score))

        # Generate message
        if confidence_score >= 0.7:
            message = f"Methodology appears robust. Good: {', '.join(good_indicators[:3])}"
        elif confidence_score >= 0.4:
            message = "Methodology needs more detail"
            if bad_indicators:
                message += f". Concerns: {', '.join(bad_indicators[:2])}"
        else:
            message = "Methodology insufficient or suspicious"
            if bad_indicators:
                message += f". Red flags: {', '.join(bad_indicators)}"

        return confidence_score >= 0.4, message, confidence_score

    def validate_improvement_claim(self, baseline: float, improved: float, claim_type: str) -> Tuple[bool, str, float]:
        """
        Validate an improvement claim based on baseline and improved values

        Args:
            baseline: Baseline value
            improved: Improved value
            claim_type: Type of metric being claimed

        Returns:
            Tuple of (is_valid, message, confidence_score)
        """
        if baseline <= 0:
            return False, "Invalid baseline value", 0.0

        improvement_percent = ((baseline - improved) / baseline) * 100

        # Different validation based on claim type
        if claim_type == "violations":
            # Violations should decrease
            if improved >= baseline:
                return False, "Violations increased or stayed same", 0.0
            if improvement_percent > 95:
                return False, "Unrealistic violation reduction", 0.2
            if improvement_percent < 1:
                return False, "Negligible improvement", 0.3
            confidence = min(1.0, 0.5 + (improvement_percent / 100))

        elif claim_type == "complexity":
            # Complexity should decrease
            if improved >= baseline:
                return False, "Complexity increased or stayed same", 0.0
            if improvement_percent > 80:
                return False, "Unrealistic complexity reduction", 0.3
            confidence = min(1.0, 0.4 + (improvement_percent / 80))

        elif claim_type == "coverage":
            # Coverage should increase
            if improved <= baseline:
                return False, "Coverage decreased or stayed same", 0.0
            improvement_percent = ((improved - baseline) / baseline) * 100
            if improvement_percent > 100:
                return False, "Impossible coverage increase", 0.0
            confidence = min(1.0, 0.5 + (improvement_percent / 100))

        else:
            # Generic validation
            confidence = 0.5
            if abs(improvement_percent) > 90:
                confidence *= 0.5
            if improvement_percent == 0:
                return False, "No improvement claimed", 0.0

        message = f"Improvement of {improvement_percent:.1f}% validated"
        return confidence >= 0.4, message, confidence

    def _hash_file(self, path: Path) -> str:
        """Generate hash of file content for caching"""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def generate_validation_report(
        self, evidence_files: List[str], methodology: str, claims: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive evidence validation report

        Args:
            evidence_files: List of evidence file paths
            methodology: Measurement methodology description
            claims: List of improvement claims

        Returns:
            Comprehensive validation report
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "evidence_files": [],
            "methodology_validation": {},
            "claims_validation": [],
            "overall_assessment": {},
        }

        # Validate each evidence file
        total_score = 0.0
        for file_path in evidence_files:
            # Guess evidence type from filename
            evidence_type = self._guess_evidence_type(file_path)
            is_valid, message, score = self.validate_evidence_file(file_path, evidence_type)
            report["evidence_files"].append(
                {"path": file_path, "type": evidence_type, "valid": is_valid, "message": message, "score": score}
            )
            total_score += score

        # Validate methodology
        method_valid, method_message, method_score = self.validate_measurement_methodology(methodology)
        report["methodology_validation"] = {"valid": method_valid, "message": method_message, "score": method_score}
        total_score += method_score

        # Validate claims
        for claim in claims:
            claim_valid = True
            claim_message = "Claim validated"
            claim_score = 0.5

            if "baseline" in claim and "improved" in claim:
                claim_valid, claim_message, claim_score = self.validate_improvement_claim(
                    claim["baseline"], claim["improved"], claim.get("type", "generic")
                )

            report["claims_validation"].append(
                {
                    "claim": claim.get("description", "Unknown claim"),
                    "valid": claim_valid,
                    "message": claim_message,
                    "score": claim_score,
                }
            )
            total_score += claim_score

        # Calculate overall assessment
        total_items = len(evidence_files) + 1 + len(claims)  # +1 for methodology
        average_score = total_score / total_items if total_items > 0 else 0

        report["overall_assessment"] = {
            "average_score": round(average_score, 3),
            "confidence_level": self._get_confidence_level(average_score),
            "recommendation": self._get_validation_recommendation(average_score),
            "total_evidence_files": len(evidence_files),
            "valid_evidence_files": sum(1 for f in report["evidence_files"] if f["valid"]),
            "valid_claims": sum(1 for c in report["claims_validation"] if c["valid"]),
        }

        # Store in history
        self.validation_history.append(report)

        return report

    def _guess_evidence_type(self, file_path: str) -> str:
        """Guess evidence type from filename"""
        path_lower = file_path.lower()

        if "baseline" in path_lower:
            return "baseline_measurement"
        elif "test" in path_lower or "coverage" in path_lower:
            return "test_results"
        elif "violation" in path_lower or "issue" in path_lower:
            return "violation_report"
        elif "improve" in path_lower or "after" in path_lower:
            return "improvement_data"
        else:
            return "metrics_report"

    def _get_confidence_level(self, score: float) -> str:
        """Get confidence level description from score"""
        if score >= 0.8:
            return "High confidence"
        elif score >= 0.6:
            return "Moderate confidence"
        elif score >= 0.4:
            return "Low confidence"
        else:
            return "Very low confidence"

    def _get_validation_recommendation(self, score: float) -> str:
        """Get validation recommendation based on score"""
        if score >= 0.8:
            return "Evidence is credible and well-documented. Accept claims with confidence."
        elif score >= 0.6:
            return "Evidence is reasonable but has some gaps. Conditional acceptance recommended."
        elif score >= 0.4:
            return "Evidence is weak. Request additional documentation before acceptance."
        else:
            return "Evidence is insufficient or suspicious. Reject claims pending proper validation."
