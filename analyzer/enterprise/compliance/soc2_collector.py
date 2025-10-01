"""
SOC 2 Type II Evidence Collector
=================================

Automates collection of evidence for SOC 2 Type II compliance audits.

SOC 2 Trust Service Criteria:
- Security (CC1-CC9): Access controls, encryption, monitoring
- Availability (A1): System uptime and reliability
- Processing Integrity (PI1): Data processing accuracy
- Confidentiality (C1): Data protection
- Privacy (P1-P8): Personal information handling

Evidence Types:
- System logs and monitoring data
- Access control records
- Change management documentation
- Incident response records
- Testing and validation results

@module SOC2Collector
@compliance SOC2-TypeII, AICPA-TSC
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SOC2Evidence:
    control_id: str
    criterion: str
    evidence_type: str
    description: str
    timestamp: str
    data: Dict[str, Any]
    attestation: Optional[str] = None


@dataclass
class SOC2Report:
    period_start: str
    period_end: str
    evidence_items: List[SOC2Evidence]
    criteria_coverage: Dict[str, int]
    compliance_score: float


class SOC2Collector:
    TSC_CRITERIA = {
        "CC1": "Control Environment",
        "CC2": "Communication and Information",
        "CC3": "Risk Assessment",
        "CC4": "Monitoring Activities",
        "CC5": "Control Activities",
        "CC6": "Logical and Physical Access Controls",
        "CC7": "System Operations",
        "CC8": "Change Management",
        "CC9": "Risk Mitigation",
        "A1": "Availability",
        "PI1": "Processing Integrity",
        "C1": "Confidentiality",
        "P1-P8": "Privacy",
    }

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.evidence: List[SOC2Evidence] = []

    def collect_access_control_evidence(self) -> List[SOC2Evidence]:
        evidence = []

        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path) as f:
                gitignore_content = f.read()

            secrets_protected = any(
                pattern in gitignore_content for pattern in ["*.key", "*.pem", ".env", "secrets", "credentials"]
            )

            evidence.append(
                SOC2Evidence(
                    control_id="CC6.1",
                    criterion="Logical and Physical Access Controls",
                    evidence_type="configuration",
                    description="Secrets and credentials excluded from version control",
                    timestamp=datetime.now().isoformat(),
                    data={
                        "gitignore_exists": True,
                        "secrets_protected": secrets_protected,
                        "patterns_found": [p for p in ["*.key", "*.pem", ".env", "secrets"] if p in gitignore_content],
                    },
                )
            )

        try:
            result = subprocess.run(
                ["git", "log", "--all", "--format=%H %an %ae %ai", "-n", "100"],
                check=False,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                commits = result.stdout.strip().split("\n")
                authors = set()
                for commit in commits:
                    if commit:
                        parts = commit.split(" ", 3)
                        if len(parts) >= 3:
                            authors.add(parts[2])

                evidence.append(
                    SOC2Evidence(
                        control_id="CC6.2",
                        criterion="Logical and Physical Access Controls",
                        evidence_type="audit_log",
                        description="Git commit audit trail with author attribution",
                        timestamp=datetime.now().isoformat(),
                        data={
                            "total_commits_analyzed": len(commits),
                            "unique_authors": len(authors),
                            "audit_trail_available": True,
                        },
                    )
                )

        except Exception as e:
            logger.warning(f"Could not collect git audit evidence: {e}")

        self.evidence.extend(evidence)
        return evidence

    def collect_change_management_evidence(self) -> List[SOC2Evidence]:
        evidence = []

        try:
            result = subprocess.run(
                ["git", "log", "--all", "--format=%H %s", "--since=30.days.ago"],
                check=False,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                commits = result.stdout.strip().split("\n")
                total_changes = len([c for c in commits if c])

                reviewed_changes = len(
                    [c for c in commits if any(keyword in c.lower() for keyword in ["review", "approved", "merge"])]
                )

                evidence.append(
                    SOC2Evidence(
                        control_id="CC8.1",
                        criterion="Change Management",
                        evidence_type="process_documentation",
                        description="Change management process with review workflow",
                        timestamp=datetime.now().isoformat(),
                        data={
                            "period_days": 30,
                            "total_changes": total_changes,
                            "reviewed_changes": reviewed_changes,
                            "review_rate": reviewed_changes / max(1, total_changes),
                        },
                    )
                )

        except Exception as e:
            logger.warning(f"Could not collect change management evidence: {e}")

        ci_config = self.project_root / ".github" / "workflows"
        if ci_config.exists():
            workflow_files = list(ci_config.glob("*.yml")) + list(ci_config.glob("*.yaml"))

            evidence.append(
                SOC2Evidence(
                    control_id="CC8.2",
                    criterion="Change Management",
                    evidence_type="automated_controls",
                    description="Automated CI/CD pipeline for change validation",
                    timestamp=datetime.now().isoformat(),
                    data={"ci_cd_enabled": True, "workflow_count": len(workflow_files), "automated_testing": True},
                )
            )

        self.evidence.extend(evidence)
        return evidence

    def collect_monitoring_evidence(self) -> List[SOC2Evidence]:
        evidence = []

        test_dirs = [self.project_root / "tests", self.project_root / "test", self.project_root / "__tests__"]

        test_files_found = 0
        for test_dir in test_dirs:
            if test_dir.exists():
                test_files_found += len(list(test_dir.glob("**/*test*.py")))
                test_files_found += len(list(test_dir.glob("**/*spec*.py")))

        evidence.append(
            SOC2Evidence(
                control_id="CC4.1",
                criterion="Monitoring Activities",
                evidence_type="testing_evidence",
                description="Automated testing for system monitoring",
                timestamp=datetime.now().isoformat(),
                data={"test_files_found": test_files_found, "automated_testing_enabled": test_files_found > 0},
            )
        )

        security_scan_configs = [
            self.project_root / ".bandit",
            self.project_root / "bandit.yml",
            self.project_root / ".github" / "workflows" / "security.yml",
        ]

        security_monitoring = any(config.exists() for config in security_scan_configs)

        evidence.append(
            SOC2Evidence(
                control_id="CC4.2",
                criterion="Monitoring Activities",
                evidence_type="security_monitoring",
                description="Automated security scanning and vulnerability monitoring",
                timestamp=datetime.now().isoformat(),
                data={
                    "security_scanning_enabled": security_monitoring,
                    "configs_found": [str(c.name) for c in security_scan_configs if c.exists()],
                },
            )
        )

        self.evidence.extend(evidence)
        return evidence

    def collect_all_evidence(self) -> List[SOC2Evidence]:
        self.evidence.clear()

        self.collect_access_control_evidence()
        self.collect_change_management_evidence()
        self.collect_monitoring_evidence()

        return self.evidence

    def generate_report(self, period_start: Optional[str] = None, period_end: Optional[str] = None) -> SOC2Report:
        if not period_end:
            period_end = datetime.now().isoformat()

        if not period_start:
            start_dt = datetime.now() - timedelta(days=90)
            period_start = start_dt.isoformat()

        if not self.evidence:
            self.collect_all_evidence()

        criteria_coverage = {}
        for criterion in self.TSC_CRITERIA.keys():
            count = len([e for e in self.evidence if e.control_id.startswith(criterion.split("-")[0])])
            criteria_coverage[criterion] = count

        total_criteria = len(self.TSC_CRITERIA)
        covered_criteria = len([c for c in criteria_coverage.values() if c > 0])
        compliance_score = covered_criteria / total_criteria if total_criteria > 0 else 0.0

        return SOC2Report(
            period_start=period_start,
            period_end=period_end,
            evidence_items=self.evidence,
            criteria_coverage=criteria_coverage,
            compliance_score=compliance_score,
        )

    def export_report(self, report: SOC2Report, output_path: str):
        report_data = {
            "period": {"start": report.period_start, "end": report.period_end},
            "compliance_score": report.compliance_score,
            "criteria_coverage": report.criteria_coverage,
            "evidence_count": len(report.evidence_items),
            "evidence": [
                {
                    "control_id": e.control_id,
                    "criterion": e.criterion,
                    "evidence_type": e.evidence_type,
                    "description": e.description,
                    "timestamp": e.timestamp,
                    "data": e.data,
                }
                for e in report.evidence_items
            ],
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"SOC 2 report exported to {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="SOC 2 Type II Evidence Collector")
    parser.add_argument("--project", default=".", help="Project root directory")
    parser.add_argument("--output", default="soc2-evidence.json", help="Output file")
    parser.add_argument("--period-start", help="Audit period start date (ISO format)")
    parser.add_argument("--period-end", help="Audit period end date (ISO format)")

    args = parser.parse_args()

    collector = SOC2Collector(args.project)

    print(f"Collecting SOC 2 evidence from {args.project}...")

    evidence = collector.collect_all_evidence()
    print(f"Collected {len(evidence)} evidence items")

    report = collector.generate_report(args.period_start, args.period_end)

    print(f"\nSOC 2 Compliance Score: {report.compliance_score:.1%}")
    print("\nCriteria Coverage:")
    for criterion, count in report.criteria_coverage.items():
        status = "✓" if count > 0 else "✗"
        description = SOC2Collector.TSC_CRITERIA[criterion]
        print(f"  {status} {criterion}: {description} ({count} evidence items)")

    collector.export_report(report, args.output)
    print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
