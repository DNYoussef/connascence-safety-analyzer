# SPDX-License-Identifier: MIT
"""
Automatic policy detection based on project characteristics.

Analyzes project structure and content to suggest the most appropriate
connascence analysis policy.
"""

from pathlib import Path
import re
from typing import Any, Dict, List


class PolicyDetection:
    """Detects appropriate analysis policy based on project characteristics."""

    def __init__(self):
        self.policy_indicators = {
            "nasa_jpl_pot10": [
                # NASA/aerospace indicators
                "nasa", "jpl", "aerospace", "flight", "mission", "spacecraft",
                "embedded", "real-time", "safety-critical", "avionics",
                # Memory management patterns
                "malloc", "free", "memory_pool", "static_allocation",
                # Common in safety-critical code
                "assert", "precondition", "postcondition", "invariant"
            ],
            "strict-core": [
                # Enterprise/production indicators
                "enterprise", "production", "critical", "banking", "finance",
                "healthcare", "security", "audit", "compliance",
                # Complex architectures
                "microservice", "distributed", "kubernetes", "docker",
                "enterprise_integration", "message_queue",
                # Quality indicators
                "code_review", "quality_gate", "sonarqube", "static_analysis"
            ],
            "lenient": [
                # Development/experimental indicators
                "prototype", "experiment", "poc", "demo", "sandbox",
                "example", "tutorial", "learning", "playground",
                "test", "mock", "stub", "temporary"
            ]
        }

    def detect_policy(self, paths: List[str]) -> str:
        """Detect the most appropriate policy for the given paths."""
        if not paths:
            return "default"

        # Analyze all provided paths
        characteristics = self._analyze_paths(paths)

        # Score each policy based on detected characteristics
        scores = self._score_policies(characteristics)

        # Return the highest scoring policy, defaulting to "default"
        if not scores:
            return "default"

        best_policy = max(scores.items(), key=lambda x: x[1])

        # Map policy names to what the analyzer expects
        policy_mapping = {
            "nasa_jpl_pot10": "default",  # Use default for now since nasa-compliance isn't available
            "strict-core": "default",
            "lenient": "default"
        }

        selected_policy = best_policy[0] if best_policy[1] > 0 else "default"
        return policy_mapping.get(selected_policy, "default")

    def _analyze_paths(self, paths: List[str]) -> Dict[str, Any]:
        """Analyze project characteristics from the given paths."""
        characteristics = {
            "file_patterns": set(),
            "directory_names": set(),
            "file_contents": [],
            "config_files": set(),
            "dependencies": set(),
            "total_files": 0,
            "python_files": 0,
            "test_files": 0,
            "has_setup_py": False,
            "has_pyproject_toml": False,
            "has_requirements": False,
            "has_dockerfile": False,
            "has_ci_config": False,
        }

        for path_str in paths:
            path = Path(path_str)
            if path.is_file():
                self._analyze_file(path, characteristics)
            elif path.is_dir():
                self._analyze_directory(path, characteristics)

        return characteristics

    def _analyze_directory(self, directory: Path, characteristics: Dict[str, Any]) -> None:
        """Analyze a directory for policy indicators."""
        # Analyze directory structure
        characteristics["directory_names"].add(directory.name.lower())

        # Look for specific configuration files
        config_files = [
            "setup.py", "pyproject.toml", "requirements.txt", "Pipfile",
            "Dockerfile", ".github", ".gitlab-ci.yml", "tox.ini",
            "setup.cfg", "pytest.ini", ".pre-commit-config.yaml"
        ]

        for config_file in config_files:
            if (directory / config_file).exists():
                characteristics["config_files"].add(config_file)
                if config_file == "setup.py":
                    characteristics["has_setup_py"] = True
                elif config_file == "pyproject.toml":
                    characteristics["has_pyproject_toml"] = True
                elif config_file in ("requirements.txt", "Pipfile"):
                    characteristics["has_requirements"] = True
                elif config_file == "Dockerfile":
                    characteristics["has_dockerfile"] = True
                elif config_file in (".github", ".gitlab-ci.yml"):
                    characteristics["has_ci_config"] = True

        # Analyze Python files in the directory
        python_files = list(directory.rglob("*.py"))
        characteristics["total_files"] += len(python_files)
        characteristics["python_files"] += len(python_files)

        # Count test files
        test_files = [f for f in python_files if self._is_test_file(f)]
        characteristics["test_files"] += len(test_files)

        # Analyze a sample of files for content indicators
        sample_files = python_files[:20]  # Limit to avoid performance issues
        for py_file in sample_files:
            self._analyze_file(py_file, characteristics)

    def _analyze_file(self, file_path: Path, characteristics: Dict[str, Any]) -> None:
        """Analyze a single file for policy indicators."""
        characteristics["file_patterns"].add(file_path.suffix.lower())
        characteristics["total_files"] += 1

        if file_path.suffix.lower() == ".py":
            characteristics["python_files"] += 1

            if self._is_test_file(file_path):
                characteristics["test_files"] += 1

        # Analyze file content for keywords (limit size to avoid performance issues)
        try:
            if file_path.stat().st_size > 100000:  # Skip very large files
                return

            content = file_path.read_text(encoding="utf-8", errors="ignore")[:10000]  # First 10KB
            characteristics["file_contents"].append(content.lower())

            # Look for dependency patterns
            if file_path.name in ("requirements.txt", "Pipfile", "pyproject.toml"):
                self._extract_dependencies(content, characteristics)

        except (OSError, UnicodeDecodeError):
            # Skip files that can't be read
            pass

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file."""
        test_patterns = [
            r"test_.*\.py$",
            r".*_test\.py$",
            r".*/tests?/.*\.py$",
            r".*/test/.*\.py$"
        ]

        path_str = str(file_path).lower()
        return any(re.search(pattern, path_str) for pattern in test_patterns)

    def _extract_dependencies(self, content: str, characteristics: Dict[str, Any]) -> None:
        """Extract dependency information from config files."""
        # Simple dependency extraction
        dependency_patterns = [
            r"^\s*([a-zA-Z0-9_-]+)",  # First word on line (requirements.txt style)
            r'"([a-zA-Z0-9_-]+)"',    # Quoted dependencies
            r"'([a-zA-Z0-9_-]+)'"     # Single-quoted dependencies
        ]

        for pattern in dependency_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            characteristics["dependencies"].update(dep.lower() for dep in matches)

    def _score_policies(self, characteristics: Dict[str, Any]) -> Dict[str, float]:
        """Score each policy based on project characteristics."""
        scores = {}

        # Get all file content as one string for searching
        all_content = " ".join(characteristics["file_contents"])

        for policy, indicators in self.policy_indicators.items():
            score = 0.0

            # Score based on keyword matches in content
            for indicator in indicators:
                if indicator in all_content:
                    score += 1.0

            # Score based on directory/file names
            for name in characteristics["directory_names"]:
                for indicator in indicators:
                    if indicator in name:
                        score += 0.5

            # Score based on config files and dependencies
            for dep in characteristics["dependencies"]:
                for indicator in indicators:
                    if indicator in dep:
                        score += 0.3

            scores[policy] = score

        # Apply project structure bonuses
        scores = self._apply_structure_bonuses(scores, characteristics)

        return scores

    def _apply_structure_bonuses(self, scores: Dict[str, float],
                                characteristics: Dict[str, Any]) -> Dict[str, float]:
        """Apply bonuses based on project structure characteristics."""

        # NASA/safety-critical bonus
        if characteristics.get("has_ci_config") and characteristics.get("test_files", 0) > 5:
            scores["nasa_jpl_pot10"] = scores.get("nasa_jpl_pot10", 0) + 2.0

        # Enterprise/strict bonus
        if (characteristics.get("has_dockerfile") or
            characteristics.get("has_pyproject_toml") or
            len(characteristics.get("config_files", set())) > 3):
            scores["strict-core"] = scores.get("strict-core", 0) + 1.5

        # Lenient bonus for simple projects
        if (characteristics.get("python_files", 0) < 10 and
            not characteristics.get("has_setup_py") and
            not characteristics.get("has_requirements")):
            scores["lenient"] = scores.get("lenient", 0) + 1.0

        # Default bonus for balanced projects
        test_ratio = (characteristics.get("test_files", 0) /
                     max(characteristics.get("python_files", 1), 1))
        if 0.1 <= test_ratio <= 0.5:  # Reasonable test coverage
            scores["default"] = scores.get("default", 0) + 1.0

        return scores
