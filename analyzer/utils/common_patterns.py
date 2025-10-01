"""
Common Patterns - Eliminates Connascence of Algorithm
====================================================

Centralized utility functions that eliminate duplicate algorithms
and reduce Connascence of Algorithm across the analyzer system.
"""

import ast
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fixes.phase0.production_safe_assertions import ProductionAssert

logger = logging.getLogger(__name__)


@dataclass
class CodeLocation:
    """Represents a location in source code."""

    file_path: str
    line_number: int
    column: int = 0

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number}:{self.column}"


class ASTUtils:
    """
    Common AST utility functions that eliminate duplicated AST processing
    algorithms across multiple detectors.
    """

    @staticmethod
    def get_node_location(node: ast.AST, file_path: str) -> CodeLocation:
        """Get the location of an AST node."""
        return CodeLocation(
            file_path=file_path, line_number=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0)
        )

    @staticmethod
    def extract_code_snippet(source_lines: List[str], node: ast.AST, context_lines: int = 2) -> str:
        """
        Extract code snippet around an AST node.
        Eliminates duplicate snippet extraction algorithms.
        """
        if not hasattr(node, "lineno") or node.lineno <= 0:
            return ""

        try:
            start_line = max(0, node.lineno - context_lines - 1)
            end_line = min(len(source_lines), node.lineno + context_lines)

            lines = source_lines[start_line:end_line]
            return "\n".join(lines)
        except (IndexError, AttributeError):
            return ""

    @staticmethod
    def get_line_content(source_lines: List[str], node: ast.AST) -> str:
        """
        Get the content of the line containing a node.
        Eliminates duplicate line extraction patterns.
        """
        if not hasattr(node, "lineno") or node.lineno <= 0:
            return ""

        try:
            line_index = node.lineno - 1
            if 0 <= line_index < len(source_lines):
                return source_lines[line_index]
        except (IndexError, AttributeError):
            pass

        return ""

    @staticmethod
    def find_nodes_by_type(tree: ast.AST, node_type: type) -> List[ast.AST]:
        """
        Find all nodes of a specific type in an AST tree.
        Eliminates duplicate tree traversal patterns.
        """
        return [node for node in ast.walk(tree) if isinstance(node, node_type)]

    @staticmethod
    def get_function_complexity(node: ast.FunctionDef) -> int:
        """
        Calculate cyclomatic complexity of a function.
        Eliminates duplicate complexity calculation algorithms.
        """
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.Try):
                complexity += len(child.handlers)
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    @staticmethod
    def get_function_parameters(node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Extract function parameter information.
        Eliminates duplicate parameter analysis patterns.
        """
        params = {
            "total_count": 0,
            "positional_count": 0,
            "keyword_count": 0,
            "has_varargs": False,
            "has_kwargs": False,
            "parameter_names": [],
        }

        # Regular arguments
        if node.args.args:
            params["positional_count"] = len(node.args.args)
            params["parameter_names"] = [arg.arg for arg in node.args.args]

        # Keyword-only arguments
        if node.args.kwonlyargs:
            params["keyword_count"] = len(node.args.kwonlyargs)

        # Varargs (*args)
        if node.args.vararg:
            params["has_varargs"] = True

        # Kwargs (**kwargs)
        if node.args.kwarg:
            params["has_kwargs"] = True

        params["total_count"] = params["positional_count"] + params["keyword_count"]

        return params

    @staticmethod
    def normalize_function_signature(node: ast.FunctionDef) -> str:
        """
        Create normalized function signature for comparison.
        Eliminates duplicate signature normalization algorithms.
        """
        params = ASTUtils.get_function_parameters(node)

        signature_parts = [
            f"params:{params['total_count']}",
            f"pos:{params['positional_count']}",
            f"kw:{params['keyword_count']}",
        ]

        if params["has_varargs"]:
            signature_parts.append("varargs")
        if params["has_kwargs"]:
            signature_parts.append("kwargs")

        return "|".join(signature_parts)


class PatternMatcher:
    """
    Pattern matching utilities that eliminate duplicate pattern recognition
    algorithms across detectors.
    """

    @staticmethod
    def is_magic_number(value: Union[int, float], exclusions: Optional[Set] = None) -> bool:
        """
        Check if a number should be considered a magic number.
        Centralizes magic number detection logic.
        """
        if exclusions is None:
            # Common non-magic numbers
            exclusions = {0, 1, -1, 2, 10, 100, 1000}

        return value not in exclusions

    @staticmethod
    def is_magic_string(value: str, exclusions: Optional[Set[str]] = None) -> bool:
        """
        Check if a string should be considered a magic string.
        Centralizes magic string detection logic.
        """
        if exclusions is None:
            # Common non-magic strings
            exclusions = {"", " ", "\n", "\t", "utf-8", "ascii"}

        if value in exclusions:
            return False

        # Very short strings are usually not magic
        if len(value) <= 1:
            return False

        # Common Python keywords and patterns
        python_keywords = {"__main__", "__name__", "__file__", "__init__", "__str__", "__repr__"}

        return value not in python_keywords

    @staticmethod
    def detect_configuration_patterns(node: ast.AST, config_keywords: Set[str]) -> bool:
        """
        Detect if a node represents configuration-related code.
        Centralizes configuration pattern detection.
        """
        if isinstance(node, ast.Name):
            var_name = node.id.lower()
            return any(keyword in var_name for keyword in config_keywords)

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id.lower()
                    if any(keyword in var_name for keyword in config_keywords):
                        return True

        return False

    @staticmethod
    def extract_literal_values(tree: ast.AST) -> Dict[str, List[Tuple[ast.AST, Any]]]:
        """
        Extract all literal values from an AST tree.
        Eliminates duplicate literal extraction patterns.
        """
        literals = {"strings": [], "numbers": [], "booleans": [], "none_values": []}

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                value = node.value

                if isinstance(value, str):
                    literals["strings"].append((node, value))
                elif isinstance(value, (int, float)):
                    literals["numbers"].append((node, value))
                elif isinstance(value, bool):
                    literals["booleans"].append((node, value))
                elif value is None:
                    literals["none_values"].append((node, value))

        return literals


class ViolationFactory:
    """
    Factory for creating standardized violation objects.
    Eliminates duplicate violation creation patterns.
    """

    @staticmethod
    def create_violation(
        violation_type: str,
        severity: str,
        location: CodeLocation,
        description: str,
        recommendation: str,
        code_snippet: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized violation dictionary.
        Eliminates variation in violation object creation.
        """
        from utils.types import ConnascenceViolation

        return ConnascenceViolation(
            type=violation_type,
            severity=severity,
            file_path=location.file_path,
            line_number=location.line_number,
            column=location.column,
            description=description,
            recommendation=recommendation,
            code_snippet=code_snippet,
            context=context or {},
        )


class ErrorHandlingPatterns:
    """
    Common error handling patterns that eliminate duplicate error handling
    algorithms across the analyzer system.
    """

    @staticmethod
    def safe_ast_parse(source_code: str, file_path: str) -> Optional[ast.AST]:
        """
        Safely parse source code to AST with error handling.
        Eliminates duplicate parsing error patterns.
        """
        try:
            return ast.parse(source_code)
        except SyntaxError as e:
            logger.debug(f"Syntax error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return None

    @staticmethod
    def safe_file_read(file_path: str, encoding: str = "utf-8") -> Optional[Tuple[str, List[str]]]:
        """
        Safely read file content with error handling.
        Eliminates duplicate file reading error patterns.
        """
        try:
            with open(file_path, encoding=encoding) as f:
                content = f.read()
                lines = content.splitlines()
                return content, lines
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, encoding="latin-1") as f:
                    content = f.read()
                    lines = content.splitlines()
                    return content, lines
            except Exception as e:
                logger.warning(f"Failed to read {file_path} with latin-1: {e}")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")

        return None

    @staticmethod
    def handle_detector_error(detector_name: str, error: Exception, file_path: str) -> Dict[str, Any]:
        """
        Create standardized error result for detector failures.
        Eliminates duplicate error handling patterns.
        """
        logger.error(f"{detector_name} failed on {file_path}: {error}")

        return {
            "detector": detector_name,
            "file_path": file_path,
            "error": str(error),
            "error_type": type(error).__name__,
            "violations": [],
            "success": False,
        }


class ValidationPatterns:
    """
    Common validation patterns that eliminate duplicate validation
    algorithms across components.
    """

    @staticmethod
    def validate_ast_node(node: ast.AST, expected_type: type) -> bool:
        """Validate AST node type with error handling."""
        try:
            return isinstance(node, expected_type) and hasattr(node, "lineno")
        except Exception:
            return False

    @staticmethod
    def validate_source_lines(source_lines: List[str]) -> bool:
        """Validate source lines structure."""
        return (
            isinstance(source_lines, list)
            and len(source_lines) > 0
            and all(isinstance(line, str) for line in source_lines)
        )

    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """Validate file path format."""
        return isinstance(file_path, str) and len(file_path) > 0 and not file_path.isspace()

    @staticmethod
    def validate_configuration(config: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate configuration completeness.
        Returns (is_valid, missing_keys)
        """
        missing_keys = [key for key in required_keys if key not in config]
        return len(missing_keys) == 0, missing_keys


class AlgorithmDeduplication:
    """
    Utilities for eliminating algorithm duplication by providing
    common implementations of frequently used algorithms.
    """

    @staticmethod
    def find_duplicates_by_frequency(items: List[Any], min_frequency: int = 2) -> Dict[Any, int]:
        """
        Find items that appear with specified minimum frequency.
        Eliminates duplicate frequency-counting algorithms.
        """
        frequency_map = {}
        for item in items:
            frequency_map[item] = frequency_map.get(item, 0) + 1

        return {item: count for item, count in frequency_map.items() if count >= min_frequency}

    @staticmethod
    def group_by_attribute(items: List[Any], attribute: str) -> Dict[Any, List[Any]]:
        """
        Group items by a specific attribute.
        Eliminates duplicate grouping algorithms.
        """
        groups = {}
        for item in items:
            try:
                key = getattr(item, attribute)
                if key not in groups:
                    groups[key] = []
                groups[key].append(item)
            except AttributeError:
                continue

        return groups

    @staticmethod
    def filter_by_criteria(items: List[Any], criteria: Dict[str, Any]) -> List[Any]:
        """
        Filter items by multiple criteria.
        Eliminates duplicate filtering algorithms.
        """
        filtered_items = []

        for item in items:
            matches_all_criteria = True

            for attr_name, expected_value in criteria.items():
                try:
                    actual_value = getattr(item, attr_name)
                    if actual_value != expected_value:
                        matches_all_criteria = False
                        break
                except AttributeError:
                    matches_all_criteria = False
                    break

            if matches_all_criteria:
                filtered_items.append(item)

        return filtered_items

    @staticmethod
    def calculate_similarity_score(items1: List[str], items2: List[str]) -> float:
        """
        Calculate similarity score between two lists.
        Eliminates duplicate similarity calculation algorithms.
        """
        if not items1 or not items2:
            return 0.0

        set1 = set(items1)
        set2 = set(items2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0


# Factory function to create common utilities with configuration
def create_analysis_utilities(config_manager=None):
    """
    Factory function to create analysis utilities with configuration.
    Eliminates duplicate utility instantiation patterns.
    """
    ProductionAssert.not_none(config_manager, "config_manager")

    ProductionAssert.not_none(config_manager, "config_manager")

    if config_manager is None:
        from .config_manager import get_config_manager

        config_manager = get_config_manager()

    return {
        "ast_utils": ASTUtils(),
        "pattern_matcher": PatternMatcher(),
        "violation_factory": ViolationFactory(),
        "error_handler": ErrorHandlingPatterns(),
        "validator": ValidationPatterns(),
        "deduplicator": AlgorithmDeduplication(),
        "config_manager": config_manager,
    }
