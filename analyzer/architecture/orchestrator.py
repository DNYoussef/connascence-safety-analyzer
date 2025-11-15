# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Analysis Orchestrator - Phase Coordination Logic
==================================================

Extracted from UnifiedConnascenceAnalyzer's god object.
NASA Rule 4 Compliant: Functions under 60 lines.
Handles phase coordination and pipeline management.
"""

from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """Orchestrates analysis phases with comprehensive coordination."""

    def __init__(self):
        """Initialize orchestrator with minimal state."""
        self.current_phase = None
        self.audit_trail = []
        self.phase_metadata = {}

    def orchestrate_analysis_phases(
        self, project_path: Path, policy_preset: str, analyzers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orchestrate all analysis phases with enhanced coordination.
        NASA Rule 4 Compliant: Under 60 lines.
        """
        # NASA Rule 5: Input validation assertions
        assert project_path is not None, "project_path cannot be None"
        assert isinstance(policy_preset, str), "policy_preset must be string"
        assert analyzers is not None, "analyzers cannot be None"

        violations = {"connascence": [], "duplication": [], "nasa": []}
        phase_metadata = self._initialize_phase_metadata()

        try:
            # Phase 1-2: Core AST Analysis
            self._execute_ast_analysis_phase(project_path, violations, phase_metadata, analyzers)

            # Phase 3-4: Duplication Detection
            self._execute_duplication_phase(project_path, violations, phase_metadata, analyzers)

            # Phase 5: Smart Integration
            self._execute_smart_integration_phase(project_path, policy_preset, violations, phase_metadata, analyzers)

            # Phase 6: NASA Compliance
            self._execute_nasa_compliance_phase(project_path, violations, phase_metadata, analyzers)

        except Exception as e:
            logger.error(f"Phase orchestration failed: {e}")
            self._record_phase_error("orchestration", str(e), phase_metadata)

        violations["_metadata"] = phase_metadata
        return violations

    def _initialize_phase_metadata(self) -> Dict[str, Any]:
        """Initialize phase metadata structure. NASA Rule 4 compliant."""
        return {
            "audit_trail": [],
            "correlations": [],
            "smart_results": None,
            "phase_errors": [],
            "started_at": self._get_iso_timestamp(),
            "total_phases": 4,
        }

    def _execute_ast_analysis_phase(
        self, project_path: Path, violations: Dict, phase_metadata: Dict, analyzers: Dict
    ) -> None:
        """Execute AST analysis phase. NASA Rule 4 compliant: Under 60 lines."""
        # NASA Rule 5: Input validation
        assert project_path is not None, "project_path cannot be None"
        assert violations is not None, "violations cannot be None"

        phase_name = "ast_analysis"
        self.current_phase = phase_name

        try:
            logger.info("Phase 1-2: Starting core AST analysis")
            self._record_phase_start(phase_name, phase_metadata)

            # Execute AST analysis through analyzers
            if "ast_analyzer" in analyzers:
                ast_violations = self._run_ast_analysis_with_analyzers(project_path, analyzers)
                violations["connascence"].extend(ast_violations)

            self._record_phase_completion(phase_name, phase_metadata, len(violations["connascence"]))

        except Exception as e:
            logger.error(f"AST analysis phase failed: {e}")
            self._record_phase_error(phase_name, str(e), phase_metadata)

    def _execute_duplication_phase(
        self, project_path: Path, violations: Dict, phase_metadata: Dict, analyzers: Dict
    ) -> None:
        """Execute duplication detection phase. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert project_path is not None, "project_path cannot be None"

        phase_name = "duplication_analysis"
        self.current_phase = phase_name

        try:
            logger.info("Phase 3-4: Starting MECE duplication analysis")
            self._record_phase_start(phase_name, phase_metadata)

            if "mece_analyzer" in analyzers:
                dup_analysis = analyzers["mece_analyzer"].analyze_path(project_path, comprehensive=True)
                violations["duplication"] = dup_analysis.get("duplications", [])

            self._record_phase_completion(phase_name, phase_metadata, len(violations["duplication"]))

        except Exception as e:
            logger.error(f"Duplication analysis phase failed: {e}")
            self._record_phase_error(phase_name, str(e), phase_metadata)

    def _execute_smart_integration_phase(
        self, project_path: Path, policy_preset: str, violations: Dict, phase_metadata: Dict, analyzers: Dict
    ) -> None:
        """Execute smart integration phase. NASA Rule 4 compliant."""
        phase_name = "smart_integration"
        self.current_phase = phase_name

        try:
            logger.info("Phase 5: Running smart integration engine")
            self._record_phase_start(phase_name, phase_metadata)

            smart_results = self._run_smart_integration_with_analyzers(
                project_path, policy_preset, violations, analyzers
            )

            if smart_results:
                phase_metadata["smart_results"] = smart_results
                phase_metadata["correlations"] = smart_results.get("correlations", [])

            self._record_phase_completion(phase_name, phase_metadata, len(phase_metadata["correlations"]))

        except Exception as e:
            logger.error(f"Smart integration phase failed: {e}")
            self._record_phase_error(phase_name, str(e), phase_metadata)

    def _execute_nasa_compliance_phase(
        self, project_path: Path, violations: Dict, phase_metadata: Dict, analyzers: Dict
    ) -> None:
        """Execute NASA compliance phase. NASA Rule 4 compliant."""
        phase_name = "nasa_analysis"
        self.current_phase = phase_name

        try:
            logger.info("Phase 6: Running NASA compliance analysis")
            self._record_phase_start(phase_name, phase_metadata)

            nasa_violations = self._run_nasa_analysis_with_analyzers(
                project_path, violations["connascence"], phase_metadata, analyzers
            )
            violations["nasa"] = nasa_violations

            self._record_phase_completion(phase_name, phase_metadata, len(violations["nasa"]))

        except Exception as e:
            logger.error(f"NASA compliance phase failed: {e}")
            self._record_phase_error(phase_name, str(e), phase_metadata)

    def _record_phase_start(self, phase_name: str, phase_metadata: Dict) -> None:
        """Record phase start in audit trail. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert phase_name is not None, "phase_name cannot be None"
        assert phase_metadata is not None, "phase_metadata cannot be None"

        phase_metadata["audit_trail"].append(
            {"phase": phase_name, "started": self._get_iso_timestamp(), "status": "started"}
        )

    def _record_phase_completion(self, phase_name: str, phase_metadata: Dict, violations_count: int) -> None:
        """Record phase completion in audit trail. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert phase_name is not None, "phase_name cannot be None"
        assert violations_count >= 0, "violations_count must be non-negative"

        phase_metadata["audit_trail"].append(
            {
                "phase": phase_name,
                "completed": self._get_iso_timestamp(),
                "violations_found": violations_count,
                "status": "completed",
            }
        )

    def _record_phase_error(self, phase_name: str, error_message: str, phase_metadata: Dict) -> None:
        """Record phase error in metadata. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert phase_name is not None, "phase_name cannot be None"
        assert error_message is not None, "error_message cannot be None"

        error_record = {
            "phase": phase_name,
            "error": error_message,
            "timestamp": self._get_iso_timestamp(),
            "status": "failed",
        }

        phase_metadata["phase_errors"].append(error_record)
        phase_metadata["audit_trail"].append(error_record)

    def _run_ast_analysis_with_analyzers(self, project_path: Path, analyzers: Dict) -> List[Dict]:
        """Run AST analysis through available analyzers. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert project_path is not None, "project_path cannot be None"
        assert analyzers is not None, "analyzers cannot be None"

        all_violations = []

        # Run core AST analyzer
        if "ast_analyzer" in analyzers:
            ast_results = analyzers["ast_analyzer"].analyze_directory(project_path)
            all_violations.extend([self._violation_to_dict(v) for v in ast_results])

        # Run orchestrator analysis
        if "orchestrator_analyzer" in analyzers:
            god_results = analyzers["orchestrator_analyzer"].analyze_directory(project_path)
            all_violations.extend([self._violation_to_dict(v) for v in god_results])

        return all_violations

    def _run_smart_integration_with_analyzers(
        self, project_path: Path, policy_preset: str, violations: Dict, analyzers: Dict
    ) -> Optional[Dict]:
        """Run smart integration through analyzer. NASA Rule 4 compliant."""
        if "smart_engine" not in analyzers or not analyzers["smart_engine"]:
            return None

        try:
            base_results = analyzers["smart_engine"].comprehensive_analysis(str(project_path), policy_preset)

            # Enhanced correlation analysis
            if violations and base_results:
                correlations = analyzers["smart_engine"].analyze_correlations(
                    violations.get("connascence", []), violations.get("duplication", []), violations.get("nasa", [])
                )
                base_results["correlations"] = correlations

            return base_results

        except Exception as e:
            logger.warning(f"Smart integration execution failed: {e}")
            return None

    def _run_nasa_analysis_with_analyzers(
        self, project_path: Path, connascence_violations: List[Dict], phase_metadata: Dict, analyzers: Dict
    ) -> List[Dict]:
        """Run NASA analysis through available analyzers. NASA Rule 4 compliant."""
        nasa_violations = []

        # NASA integration analyzer
        if analyzers.get("nasa_integration"):
            for violation in connascence_violations:
                nasa_checks = analyzers["nasa_integration"].check_nasa_violations(violation)
                nasa_violations.extend(nasa_checks)

        # Dedicated NASA analyzer
        if "nasa_analyzer" in analyzers:
            dedicated_violations = self._run_dedicated_nasa_analyzer(project_path, analyzers["nasa_analyzer"])
            nasa_violations.extend(dedicated_violations)

        return nasa_violations

    def _run_dedicated_nasa_analyzer(self, project_path: Path, nasa_analyzer) -> List[Dict]:
        """Run dedicated NASA analyzer. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert project_path is not None, "project_path cannot be None"
        assert nasa_analyzer is not None, "nasa_analyzer cannot be None"

        nasa_violations = []

        try:
            for py_file in project_path.rglob("*.py"):
                if self._should_analyze_file(py_file):
                    with open(py_file, encoding="utf-8") as f:
                        source_code = f.read()

                    file_violations = nasa_analyzer.analyze_file(str(py_file), source_code)
                    nasa_violations.extend([self._nasa_violation_to_dict(v) for v in file_violations])

        except Exception as e:
            logger.warning(f"Dedicated NASA analysis failed: {e}")

        return nasa_violations

    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed. NASA Rule 4 compliant."""
        skip_patterns = ["__pycache__", ".git", ".pytest_cache", "test_", "_test.py"]
        path_str = str(file_path)
        return not any(pattern in path_str for pattern in skip_patterns)

    def _violation_to_dict(self, violation) -> Dict[str, Any]:
        """Convert violation object to dictionary. NASA Rule 4 compliant."""
        if isinstance(violation, dict):
            return violation

        return {
            "id": getattr(violation, "id", str(hash(str(violation)))),
            "rule_id": getattr(violation, "type", "CON_UNKNOWN"),
            "type": getattr(violation, "type", "unknown"),
            "severity": getattr(violation, "severity", "medium"),
            "description": getattr(violation, "description", str(violation)),
            "file_path": getattr(violation, "file_path", ""),
            "line_number": getattr(violation, "line_number", 0),
        }

    def _nasa_violation_to_dict(self, violation) -> Dict[str, Any]:
        """Convert NASA violation to dictionary. NASA Rule 4 compliant."""
        return {
            "id": f"nasa_{violation.context.get('nasa_rule', 'unknown')}_{violation.line_number}",
            "rule_id": violation.type,
            "type": violation.type,
            "severity": violation.severity,
            "description": violation.description,
            "file_path": violation.file_path,
            "line_number": violation.line_number,
            "column": violation.column,
            "context": {
                "analysis_engine": "dedicated_nasa",
                "nasa_rule": violation.context.get("nasa_rule", "unknown"),
                "recommendation": violation.recommendation,
            },
        }

    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format. NASA Rule 4 compliant."""
        return datetime.now().isoformat()

    def get_current_phase(self) -> Optional[str]:
        """Get current analysis phase."""
        return self.current_phase

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get complete audit trail."""
        return self.audit_trail.copy()
