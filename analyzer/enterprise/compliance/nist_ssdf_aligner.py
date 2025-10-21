"""
NIST SSDF Alignment Checker
============================

Aligns software development practices with NIST Secure Software Development
Framework (SSDF) version 1.1 requirements.

NIST SSDF Practice Groups:
- PO (Prepare the Organization)
- PS (Protect the Software)
- PW (Produce Well-Secured Software)
- RV (Respond to Vulnerabilities)

Focus Areas for Code Analysis:
- PS: Developer training, security requirements, threat modeling
- PW: Secure coding, testing, code review, build processes
- RV: Vulnerability detection, incident response

@module NISTSSDFAligner
@compliance NIST-SSDF-1.1, EO-14028
"""

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class SSDFPractice:
    practice_id: str
    practice_name: str
    implementation_level: str
    evidence: List[str]
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SSDFReport:
    total_practices: int
    implemented_practices: int
    maturity_level: str
    practice_assessments: List[SSDFPractice]
    group_summary: Dict[str, Dict[str, int]]


class NISTSSDFAligner:
    SSDF_PRACTICES = {
        "PO.1": "Define and use a secure software development framework",
        "PO.3": "Implement roles and responsibilities",
        "PO.5": "Implement and maintain secure environments",
        "PS.1": "Protect software from unauthorized access and tampering",
        "PS.2": "Provide training for secure development",
        "PS.3": "Define security requirements",
        "PW.1": "Design software to meet security requirements",
        "PW.2": "Review software design",
        "PW.4": "Reuse existing, secure software",
        "PW.5": "Create source code by adhering to secure coding practices",
        "PW.6": "Configure software to have secure settings by default",
        "PW.7": "Review and/or analyze code",
        "PW.8": "Test executables",
        "PW.9": "Configure software to have secure settings by default",
        "RV.1": "Identify and confirm vulnerabilities",
        "RV.2": "Assess and prioritize vulnerabilities",
        "RV.3": "Remediate vulnerabilities",
    }

    MATURITY_LEVELS = {
        0: "Not Implemented",
        1: "Initial/Ad-hoc",
        2: "Managed",
        3: "Defined",
        4: "Quantitatively Managed",
    }

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.practices: List[SSDFPractice] = []

    def assess_prepare_organization(self) -> List[SSDFPractice]:
        practices = []

        readme = self.project_root / "README.md"
        docs_dir = self.project_root / "docs"

        framework_docs = []
        if readme.exists():
            framework_docs.append("README.md")
        if docs_dir.exists():
            framework_docs.extend([str(f.relative_to(self.project_root)) for f in docs_dir.glob("*.md")])

        practices.append(
            SSDFPractice(
                practice_id="PO.1",
                practice_name="Define and use a secure software development framework",
                implementation_level="defined" if framework_docs else "initial",
                evidence=framework_docs[:10],
                gaps=[] if framework_docs else ["No documented secure development framework found"],
                recommendations=[] if framework_docs else ["Document secure development processes and standards"],
            )
        )

        ci_cd = list(self.project_root.glob(".github/workflows/*.yml")) + list(
            self.project_root.glob(".github/workflows/*.yaml")
        )

        practices.append(
            SSDFPractice(
                practice_id="PO.5",
                practice_name="Implement and maintain secure environments",
                implementation_level="defined" if ci_cd else "initial",
                evidence=[str(f.relative_to(self.project_root)) for f in ci_cd[:5]],
                gaps=[] if ci_cd else ["No automated build/deployment environment found"],
                recommendations=(
                    ["Maintain isolated dev/test/prod environments"]
                    if ci_cd
                    else ["Implement CI/CD with environment isolation"]
                ),
            )
        )

        self.practices.extend(practices)
        return practices

    def assess_protect_software(self) -> List[SSDFPractice]:
        practices = []

        gitignore = self.project_root / ".gitignore"
        secrets_protected = False

        if gitignore.exists():
            with open(gitignore) as f:
                content = f.read()
            secrets_protected = any(p in content for p in ["*.key", "*.pem", ".env", "credentials", "secrets"])

        practices.append(
            SSDFPractice(
                practice_id="PS.1",
                practice_name="Protect software from unauthorized access and tampering",
                implementation_level="defined" if secrets_protected else "initial",
                evidence=[".gitignore"] if secrets_protected else [],
                gaps=[] if secrets_protected else ["Credential protection incomplete"],
                recommendations=[] if secrets_protected else ["Protect all credential types in version control"],
            )
        )

        security_docs = list(self.project_root.glob("**/SECURITY.md")) + list(self.project_root.glob("**/security*.md"))

        practices.append(
            SSDFPractice(
                practice_id="PS.3",
                practice_name="Define security requirements",
                implementation_level="defined" if security_docs else "initial",
                evidence=[str(f.relative_to(self.project_root)) for f in security_docs],
                gaps=[] if security_docs else ["No documented security requirements found"],
                recommendations=[] if security_docs else ["Create SECURITY.md with security requirements and policies"],
            )
        )

        self.practices.extend(practices)
        return practices

    def assess_produce_well_secured(self) -> List[SSDFPractice]:
        practices = []

        test_dirs = [self.project_root / "tests", self.project_root / "test"]
        test_files = []
        for test_dir in test_dirs:
            if test_dir.exists():
                test_files.extend(list(test_dir.glob("**/*test*.py")))

        practices.append(
            SSDFPractice(
                practice_id="PW.1",
                practice_name="Design software to meet security requirements",
                implementation_level="defined" if test_files else "initial",
                evidence=[str(f.relative_to(self.project_root)) for f in test_files[:10]],
                gaps=[] if test_files else ["No automated security testing found"],
                recommendations=(
                    ["Maintain comprehensive security test coverage"]
                    if test_files
                    else ["Implement security-focused test suite"]
                ),
            )
        )

        code_review_configs = [
            self.project_root / ".github" / "CODEOWNERS",
            self.project_root / ".github" / "pull_request_template.md",
        ]
        review_process = [c for c in code_review_configs if c.exists()]

        practices.append(
            SSDFPractice(
                practice_id="PW.7",
                practice_name="Review and/or analyze code",
                implementation_level="defined" if review_process else "initial",
                evidence=[str(f.relative_to(self.project_root)) for f in review_process],
                gaps=[] if review_process else ["No formal code review process configured"],
                recommendations=[] if review_process else ["Implement CODEOWNERS and PR review requirements"],
            )
        )

        security_scan_configs = [
            self.project_root / ".bandit",
            self.project_root / "bandit.yml",
            self.project_root / ".github" / "workflows" / "security.yml",
        ]
        security_scans = [c for c in security_scan_configs if c.exists()]

        practices.append(
            SSDFPractice(
                practice_id="PW.8",
                practice_name="Test executables",
                implementation_level="quantitatively_managed" if security_scans else "initial",
                evidence=[str(f.relative_to(self.project_root)) for f in security_scans],
                gaps=[] if security_scans else ["No automated security scanning found"],
                recommendations=(
                    ["Track security scan metrics over time"]
                    if security_scans
                    else ["Implement Bandit and dependency scanning"]
                ),
            )
        )

        self.practices.extend(practices)
        return practices

    def assess_respond_to_vulnerabilities(self) -> List[SSDFPractice]:
        practices = []

        security_policy = self.project_root / "SECURITY.md"
        vuln_response = security_policy.exists()

        practices.append(
            SSDFPractice(
                practice_id="RV.1",
                practice_name="Identify and confirm vulnerabilities",
                implementation_level="defined" if vuln_response else "initial",
                evidence=["SECURITY.md"] if vuln_response else [],
                gaps=[] if vuln_response else ["No vulnerability disclosure policy found"],
                recommendations=[] if vuln_response else ["Create SECURITY.md with vulnerability reporting process"],
            )
        )

        dependabot_config = self.project_root / ".github" / "dependabot.yml"
        auto_patching = dependabot_config.exists()

        practices.append(
            SSDFPractice(
                practice_id="RV.3",
                practice_name="Remediate vulnerabilities",
                implementation_level="defined" if auto_patching else "initial",
                evidence=["dependabot.yml"] if auto_patching else [],
                gaps=[] if auto_patching else ["No automated vulnerability remediation configured"],
                recommendations=[] if auto_patching else ["Configure Dependabot for automated dependency updates"],
            )
        )

        self.practices.extend(practices)
        return practices

    def assess_all_practices(self) -> List[SSDFPractice]:
        self.practices.clear()

        self.assess_prepare_organization()
        self.assess_protect_software()
        self.assess_produce_well_secured()
        self.assess_respond_to_vulnerabilities()

        return self.practices

    def calculate_maturity_level(self) -> str:
        if not self.practices:
            return self.MATURITY_LEVELS[0]

        level_counts = {"quantitatively_managed": 0, "defined": 0, "managed": 0, "initial": 0}

        for practice in self.practices:
            level = practice.implementation_level
            if level in level_counts:
                level_counts[level] += 1

        total = len(self.practices)
        quantitative_ratio = level_counts["quantitatively_managed"] / total
        defined_ratio = level_counts["defined"] / total
        managed_ratio = level_counts["managed"] / total

        if quantitative_ratio >= 0.7:
            return self.MATURITY_LEVELS[4]
        elif defined_ratio >= 0.6:
            return self.MATURITY_LEVELS[3]
        elif managed_ratio >= 0.4:
            return self.MATURITY_LEVELS[2]
        else:
            return self.MATURITY_LEVELS[1]

    def generate_report(self) -> SSDFReport:
        if not self.practices:
            self.assess_all_practices()

        implemented = len(
            [p for p in self.practices if p.implementation_level in ["defined", "quantitatively_managed"]]
        )

        maturity_level = self.calculate_maturity_level()

        group_summary = {}
        for practice_id in self.SSDF_PRACTICES:
            group = practice_id.split(".")[0]
            if group not in group_summary:
                group_summary[group] = {"quantitatively_managed": 0, "defined": 0, "managed": 0, "initial": 0}

        for practice in self.practices:
            group = practice.practice_id.split(".")[0]
            if group in group_summary:
                level = practice.implementation_level
                if level in group_summary[group]:
                    group_summary[group][level] += 1

        return SSDFReport(
            total_practices=len(self.SSDF_PRACTICES),
            implemented_practices=implemented,
            maturity_level=maturity_level,
            practice_assessments=self.practices,
            group_summary=group_summary,
        )

    def export_report(self, report: SSDFReport, output_path: str):
        report_data = {
            "framework": "NIST SSDF v1.1",
            "maturity_summary": {
                "total_practices": report.total_practices,
                "implemented_practices": report.implemented_practices,
                "maturity_level": report.maturity_level,
            },
            "group_summary": report.group_summary,
            "practice_assessments": [
                {
                    "practice_id": p.practice_id,
                    "practice_name": p.practice_name,
                    "implementation_level": p.implementation_level,
                    "evidence_count": len(p.evidence),
                    "evidence": p.evidence,
                    "gaps": p.gaps,
                    "recommendations": p.recommendations,
                }
                for p in report.practice_assessments
            ],
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"NIST SSDF report exported to {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="NIST SSDF Alignment Checker")
    parser.add_argument("--project", default=".", help="Project root directory")
    parser.add_argument("--output", default="nist-ssdf-alignment.json", help="Output file")

    args = parser.parse_args()

    aligner = NISTSSDFAligner(args.project)

    print(f"Assessing NIST SSDF compliance for {args.project}...")

    practices = aligner.assess_all_practices()
    print(f"Assessed {len(practices)} practices")

    report = aligner.generate_report()

    print(f"\nNIST SSDF Maturity Level: {report.maturity_level}")
    print(f"  Implemented Practices: {report.implemented_practices}/{report.total_practices}")

    print("\nPractice Group Summary:")
    for group, stats in report.group_summary.items():
        total = sum(stats.values())
        advanced = stats.get("quantitatively_managed", 0) + stats.get("defined", 0)
        print(f"  {group}: {advanced}/{total} practices at defined or higher maturity")

    aligner.export_report(report, args.output)
    print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
