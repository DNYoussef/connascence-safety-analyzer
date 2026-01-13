"""
ISO 27001:2022 Control Mapper
==============================

Maps codebase security controls to ISO 27001:2022 requirements
for Information Security Management System (ISMS) compliance.

ISO 27001:2022 Control Domains (Annex A):
- Organizational controls (37 controls)
- People controls (8 controls)
- Physical controls (14 controls)
- Technological controls (34 controls)

Focus: Technological Controls (most relevant for code analysis)
- Access control (A.5.15-A.5.18)
- Cryptography (A.8.24)
- Secure development (A.8.25-A.8.28)
- Supplier security (A.8.29-A.8.30)

@module ISO27001Mapper
@compliance ISO27001:2022, ISMS
"""

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ControlMapping:
    control_id: str
    control_name: str
    implementation_status: str
    evidence_files: List[str]
    gap_analysis: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ISO27001Report:
    total_controls: int
    implemented_controls: int
    partial_controls: int
    missing_controls: int
    compliance_percentage: float
    control_mappings: List[ControlMapping]
    domain_summary: Dict[str, Dict[str, int]]


class ISO27001Mapper:
    TECHNOLOGICAL_CONTROLS = {
        "A.5.15": "Access control",
        "A.5.16": "Identity management",
        "A.5.17": "Authentication information",
        "A.5.18": "Access rights",
        "A.8.1": "User endpoint devices",
        "A.8.2": "Privileged access rights",
        "A.8.3": "Information access restriction",
        "A.8.4": "Access to source code",
        "A.8.5": "Secure authentication",
        "A.8.6": "Capacity management",
        "A.8.7": "Protection against malware",
        "A.8.8": "Management of technical vulnerabilities",
        "A.8.9": "Configuration management",
        "A.8.10": "Information deletion",
        "A.8.11": "Data masking",
        "A.8.12": "Data leakage prevention",
        "A.8.13": "Information backup",
        "A.8.14": "Redundancy of information processing facilities",
        "A.8.15": "Logging",
        "A.8.16": "Monitoring activities",
        "A.8.17": "Clock synchronization",
        "A.8.18": "Use of privileged utility programs",
        "A.8.19": "Installation of software on operational systems",
        "A.8.20": "Networks security",
        "A.8.21": "Security of network services",
        "A.8.22": "Segregation of networks",
        "A.8.23": "Web filtering",
        "A.8.24": "Use of cryptography",
        "A.8.25": "Secure development life cycle",
        "A.8.26": "Application security requirements",
        "A.8.27": "Secure system architecture and engineering principles",
        "A.8.28": "Secure coding",
        "A.8.29": "Security testing in development and acceptance",
        "A.8.30": "Outsourced development",
        "A.8.31": "Separation of development, test and production environments",
        "A.8.32": "Change management",
        "A.8.33": "Test information",
        "A.8.34": "Protection of information systems during audit testing",
    }

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.mappings: List[ControlMapping] = []

    def map_access_controls(self) -> List[ControlMapping]:
        mappings = []

        gitignore = self.project_root / ".gitignore"
        auth_files = list(self.project_root.glob("**/auth*.py")) + list(self.project_root.glob("**/authentication*.py"))

        if gitignore.exists():
            with open(gitignore) as f:
                content = f.read()

            secrets_protected = any(p in content for p in ["*.key", "*.pem", ".env", "credentials"])

            mappings.append(
                ControlMapping(
                    control_id="A.5.17",
                    control_name="Authentication information",
                    implementation_status="implemented" if secrets_protected else "partial",
                    evidence_files=[str(gitignore.relative_to(self.project_root))],
                    gap_analysis=None if secrets_protected else "Some credential types may not be protected",
                    recommendations=[] if secrets_protected else ["Add all credential file patterns to .gitignore"],
                )
            )

        if auth_files:
            mappings.append(
                ControlMapping(
                    control_id="A.8.5",
                    control_name="Secure authentication",
                    implementation_status="implemented",
                    evidence_files=[str(f.relative_to(self.project_root)) for f in auth_files[:5]],
                    recommendations=["Review authentication implementation for password hashing and MFA support"],
                )
            )

        self.mappings.extend(mappings)
        return mappings

    def map_secure_development(self) -> List[ControlMapping]:
        mappings = []

        ci_cd_configs = list(self.project_root.glob(".github/workflows/*.yml")) + list(
            self.project_root.glob(".github/workflows/*.yaml")
        )

        test_dirs = [self.project_root / "tests", self.project_root / "test"]
        test_files = []
        for test_dir in test_dirs:
            if test_dir.exists():
                test_files.extend(list(test_dir.glob("**/*test*.py")))

        if ci_cd_configs or test_files:
            status = "implemented" if ci_cd_configs and test_files else "partial"

            mappings.append(
                ControlMapping(
                    control_id="A.8.25",
                    control_name="Secure development life cycle",
                    implementation_status=status,
                    evidence_files=[str(f.relative_to(self.project_root)) for f in (ci_cd_configs + test_files)[:10]],
                    gap_analysis=None if status == "implemented" else "CI/CD or testing infrastructure incomplete",
                    recommendations=(
                        ["Maintain comprehensive test coverage"]
                        if status == "implemented"
                        else ["Implement CI/CD and testing infrastructure"]
                    ),
                )
            )

        security_configs = [
            self.project_root / ".bandit",
            self.project_root / "bandit.yml",
            self.project_root / ".github" / "workflows" / "security.yml",
        ]
        security_found = [c for c in security_configs if c.exists()]

        mappings.append(
            ControlMapping(
                control_id="A.8.29",
                control_name="Security testing in development and acceptance",
                implementation_status="implemented" if security_found else "missing",
                evidence_files=[str(f.relative_to(self.project_root)) for f in security_found],
                gap_analysis=None if security_found else "No automated security testing found",
                recommendations=[] if security_found else ["Implement Bandit or similar security scanning tools"],
            )
        )

        requirements = [self.project_root / "requirements.txt", self.project_root / "Pipfile"]
        dep_mgmt = [r for r in requirements if r.exists()]

        mappings.append(
            ControlMapping(
                control_id="A.8.30",
                control_name="Outsourced development",
                implementation_status="implemented" if dep_mgmt else "partial",
                evidence_files=[str(f.relative_to(self.project_root)) for f in dep_mgmt],
                recommendations=["Maintain SBOM and dependency vulnerability scanning"],
            )
        )

        self.mappings.extend(mappings)
        return mappings

    def map_cryptography(self) -> List[ControlMapping]:
        mappings = []

        crypto_files = (
            list(self.project_root.glob("**/crypto*.py"))
            + list(self.project_root.glob("**/encryption*.py"))
            + list(self.project_root.glob("**/hash*.py"))
        )

        if crypto_files:
            mappings.append(
                ControlMapping(
                    control_id="A.8.24",
                    control_name="Use of cryptography",
                    implementation_status="implemented",
                    evidence_files=[str(f.relative_to(self.project_root)) for f in crypto_files[:5]],
                    recommendations=["Ensure cryptography uses approved algorithms (AES-256, SHA-256+, RSA-2048+)"],
                )
            )
        else:
            mappings.append(
                ControlMapping(
                    control_id="A.8.24",
                    control_name="Use of cryptography",
                    implementation_status="not_applicable",
                    evidence_files=[],
                    gap_analysis="No cryptographic operations detected in codebase",
                )
            )

        self.mappings.extend(mappings)
        return mappings

    def map_logging_monitoring(self) -> List[ControlMapping]:
        mappings = []

        log_files = list(self.project_root.glob("**/log*.py")) + list(self.project_root.glob("**/logger*.py"))

        if log_files:
            mappings.append(
                ControlMapping(
                    control_id="A.8.15",
                    control_name="Logging",
                    implementation_status="implemented",
                    evidence_files=[str(f.relative_to(self.project_root)) for f in log_files[:5]],
                    recommendations=["Ensure logs include security events and access attempts"],
                )
            )

        monitoring_files = list(self.project_root.glob("**/monitor*.py")) + list(
            self.project_root.glob("**/metrics*.py")
        )

        if monitoring_files:
            mappings.append(
                ControlMapping(
                    control_id="A.8.16",
                    control_name="Monitoring activities",
                    implementation_status="implemented",
                    evidence_files=[str(f.relative_to(self.project_root)) for f in monitoring_files[:5]],
                    recommendations=["Configure alerting for security-relevant events"],
                )
            )

        self.mappings.extend(mappings)
        return mappings

    def map_all_controls(self) -> List[ControlMapping]:
        self.mappings.clear()

        self.map_access_controls()
        self.map_secure_development()
        self.map_cryptography()
        self.map_logging_monitoring()

        return self.mappings

    def generate_report(self) -> ISO27001Report:
        if not self.mappings:
            self.map_all_controls()

        implemented = len([m for m in self.mappings if m.implementation_status == "implemented"])
        partial = len([m for m in self.mappings if m.implementation_status == "partial"])
        missing = len([m for m in self.mappings if m.implementation_status == "missing"])
        not_applicable = len([m for m in self.mappings if m.implementation_status == "not_applicable"])

        total_applicable = len(self.mappings) - not_applicable
        compliance_percentage = (implemented + 0.5 * partial) / total_applicable if total_applicable > 0 else 0.0

        domain_summary = {}
        for control_id in self.TECHNOLOGICAL_CONTROLS:
            domain = control_id.split(".")[0]
            if domain not in domain_summary:
                domain_summary[domain] = {"implemented": 0, "partial": 0, "missing": 0, "not_applicable": 0}

        for mapping in self.mappings:
            domain = mapping.control_id.split(".")[0]
            if domain in domain_summary:
                status = mapping.implementation_status
                if status in domain_summary[domain]:
                    domain_summary[domain][status] += 1

        return ISO27001Report(
            total_controls=len(self.TECHNOLOGICAL_CONTROLS),
            implemented_controls=implemented,
            partial_controls=partial,
            missing_controls=missing,
            compliance_percentage=compliance_percentage,
            control_mappings=self.mappings,
            domain_summary=domain_summary,
        )

    def export_report(self, report: ISO27001Report, output_path: str):
        report_data = {
            "standard": "ISO 27001:2022",
            "scope": "Technological Controls (Annex A)",
            "compliance_summary": {
                "total_controls": report.total_controls,
                "implemented": report.implemented_controls,
                "partial": report.partial_controls,
                "missing": report.missing_controls,
                "compliance_percentage": report.compliance_percentage,
            },
            "domain_summary": report.domain_summary,
            "control_mappings": [
                {
                    "control_id": m.control_id,
                    "control_name": m.control_name,
                    "implementation_status": m.implementation_status,
                    "evidence_count": len(m.evidence_files),
                    "evidence_files": m.evidence_files,
                    "gap_analysis": m.gap_analysis,
                    "recommendations": m.recommendations,
                }
                for m in report.control_mappings
            ],
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"ISO 27001 report exported to {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ISO 27001:2022 Control Mapper")
    parser.add_argument("--project", default=".", help="Project root directory")
    parser.add_argument("--output", default="iso27001-mapping.json", help="Output file")

    args = parser.parse_args()

    mapper = ISO27001Mapper(args.project)

    logger.info("Mapping ISO 27001:2022 controls for %s...", args.project)

    mappings = mapper.map_all_controls()
    logger.info("Mapped %s controls", len(mappings))

    report = mapper.generate_report()

    logger.info("ISO 27001:2022 Compliance: %.1f%%", report.compliance_percentage * 100)
    logger.info("  Implemented: %s", report.implemented_controls)
    logger.info("  Partial: %s", report.partial_controls)
    logger.info("  Missing: %s", report.missing_controls)

    logger.info("Domain Summary:")
    for domain, stats in report.domain_summary.items():
        logger.info(
            "  %s: %s implemented, %s partial, %s missing",
            domain,
            stats["implemented"],
            stats["partial"],
            stats["missing"],
        )

    mapper.export_report(report, args.output)
    logger.info("Report saved to: %s", args.output)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
