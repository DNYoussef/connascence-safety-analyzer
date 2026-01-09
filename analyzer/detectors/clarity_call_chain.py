"""
Call Chain Depth Detector - Code Clarity Detector

Detects excessive call chain depth (>3 levels by default).

NASA Rule 4 Compliant: All functions under 60 lines
NASA Rule 5 Compliant: Input assertions
"""

import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple

from analyzer.clarity_linter.base import BaseClarityDetector
from analyzer.clarity_linter.models import ClarityViolation


class CallChainDepthDetector(BaseClarityDetector):
    """
    Detects excessive call chain depth.

    Call chains like: obj.method1().method2().method3().method4()
    are hard to read and debug. This detector flags chains exceeding
    the configured threshold (default: 3).

    NASA Rule 4 Compliant: All methods under 60 lines
    NASA Rule 5 Compliant: Input assertions
    """

    rule_id = "CLARITY_CALL_CHAIN"
    rule_name = "Excessive Call Chain Depth"
    default_severity = "medium"

    # Default maximum chain depth before flagging
    DEFAULT_MAX_DEPTH = 3

    # Fluent API patterns that are acceptable
    FLUENT_EXEMPTIONS: Set[str] = {
        "filter", "map", "reduce", "sort", "sorted",
        "join", "split", "strip", "replace", "format",
        "encode", "decode", "upper", "lower", "title",
        "where", "select", "order_by", "group_by",
        "add_argument", "set_defaults", "add_parser",
    }

    def detect(
        self,
        tree: ast.Module,
        file_path: Path
    ) -> List[ClarityViolation]:
        """
        Detect excessive call chain depth in AST tree.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            tree: Parsed AST tree to analyze
            file_path: Path to file being analyzed

        Returns:
            List of clarity violations found
        """
        # NASA Rule 5: Input validation
        assert tree is not None, "tree cannot be None"
        assert isinstance(tree, ast.Module), "tree must be ast.Module"
        assert file_path is not None, "file_path cannot be None"

        violations = []
        max_depth = self._get_max_depth()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                chain_info = self._analyze_call_chain(node)
                if chain_info and chain_info["depth"] > max_depth:
                    if not self._is_fluent_api(chain_info["methods"]):
                        violation = self._create_chain_violation(
                            node, file_path, chain_info, max_depth
                        )
                        violations.append(violation)

        return violations

    def _get_max_depth(self) -> int:
        """
        Get maximum chain depth from configuration.

        NASA Rule 4: Function under 60 lines
        """
        return self.rule_config.get("max_depth", self.DEFAULT_MAX_DEPTH)

    def _analyze_call_chain(self, node: ast.Call) -> Dict:
        """
        Analyze a call node to determine chain depth.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        # NASA Rule 5: Input validation
        assert node is not None, "node cannot be None"

        methods = []
        depth = 0
        current = node

        # Walk up the chain
        while isinstance(current, ast.Call):
            depth += 1
            if isinstance(current.func, ast.Attribute):
                methods.append(current.func.attr)
                current = current.func.value
            elif isinstance(current.func, ast.Name):
                methods.append(current.func.id)
                break
            else:
                break

        if depth <= 1:
            return None

        return {
            "depth": depth,
            "methods": list(reversed(methods)),
            "line": node.lineno,
            "col": node.col_offset
        }

    def _is_fluent_api(self, methods: List[str]) -> bool:
        """
        Check if chain represents acceptable fluent API usage.

        NASA Rule 4: Function under 60 lines
        """
        # If most methods are fluent exemptions, allow it
        exemption_count = sum(
            1 for m in methods if m.lower() in self.FLUENT_EXEMPTIONS
        )
        return exemption_count > len(methods) / 2

    def _create_chain_violation(
        self,
        node: ast.Call,
        file_path: Path,
        chain_info: Dict,
        max_depth: int
    ) -> ClarityViolation:
        """
        Create violation for excessive call chain.

        NASA Rule 4: Function under 60 lines
        """
        chain_str = ".".join(chain_info["methods"])
        if len(chain_str) > 50:
            chain_str = chain_str[:47] + "..."

        description = (
            f"Call chain depth of {chain_info['depth']} exceeds maximum of "
            f"{max_depth}. Chain: {chain_str}"
        )

        recommendation = (
            "Break the call chain into intermediate variables with descriptive "
            "names. This improves readability and makes debugging easier."
        )

        return self.create_violation(
            file_path=file_path,
            line_number=chain_info["line"],
            description=description,
            recommendation=recommendation,
            context={
                "depth": chain_info["depth"],
                "max_depth": max_depth,
                "methods": chain_info["methods"],
                "issue_type": "excessive_call_chain"
            }
        )


__all__ = ['CallChainDepthDetector']
