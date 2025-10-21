"""
AST Utility Functions

Provides common AST traversal and analysis utilities for connascence detectors.
This module consolidates AST operations that were previously duplicated across
multiple detector implementations.

NASA Rule 4 Compliant: All functions under 60 lines
"""

import ast
from typing import Any, Dict, List, Tuple, Type, Union


class ASTUtils:
    """
    Utility class for common AST operations.

    Provides static methods for AST traversal, node analysis, and information extraction.
    Used by detectors in analyzer/detectors/ to avoid code duplication.
    """

    @staticmethod
    def find_nodes_by_type(tree: ast.AST, node_types: Union[Type[ast.AST], Tuple[Type[ast.AST], ...]]) -> List[ast.AST]:
        """
        Find all nodes of specified type(s) in the AST tree.

        Args:
            tree: AST tree to search
            node_types: Single node type or tuple of node types to find

        Returns:
            List of matching AST nodes

        NASA Rule 4: Under 60 lines
        NASA Rule 5: Input assertions
        """
        assert isinstance(tree, ast.AST), "tree must be an AST node"
        assert isinstance(node_types, (type, tuple)), "node_types must be type or tuple of types"

        nodes = []
        for node in ast.walk(tree):
            if isinstance(node, node_types):
                nodes.append(node)

        return nodes

    @staticmethod
    def get_function_parameters(node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Extract detailed parameter information from a function definition.

        Args:
            node: FunctionDef AST node

        Returns:
            Dict with parameter counts and details:
                - positional_count: Number of positional parameters
                - keyword_only_count: Number of keyword-only parameters
                - total_count: Total number of parameters
                - has_varargs: Boolean, has *args
                - has_kwargs: Boolean, has **kwargs
                - parameter_names: List of parameter names

        NASA Rule 4: Under 60 lines
        NASA Rule 5: Input assertions
        """
        assert isinstance(node, ast.FunctionDef), "node must be FunctionDef"

        # Count positional arguments (excluding those starting with _)
        positional_args = [arg for arg in node.args.args if not arg.arg.startswith("_")]
        positional_count = len(positional_args)

        # Count keyword-only arguments
        keyword_only_count = len(node.args.kwonlyargs)

        # Check for *args and **kwargs
        has_varargs = node.args.vararg is not None
        has_kwargs = node.args.kwarg is not None

        # Get all parameter names
        parameter_names = [arg.arg for arg in node.args.args]
        parameter_names.extend([arg.arg for arg in node.args.kwonlyargs])

        return {
            "positional_count": positional_count,
            "keyword_only_count": keyword_only_count,
            "total_count": positional_count + keyword_only_count,
            "has_varargs": has_varargs,
            "has_kwargs": has_kwargs,
            "parameter_names": parameter_names,
            "all_args": node.args.args,
            "kwonly_args": node.args.kwonlyargs,
        }

    @staticmethod
    def get_node_location(node: ast.AST, file_path: str) -> Dict[str, Any]:
        """
        Get standardized location information for an AST node.

        Args:
            node: AST node
            file_path: Path to the source file

        Returns:
            Dict with location information:
                - file: File path
                - line: Line number (1-indexed)
                - column: Column number (0-indexed)
                - end_line: End line number (if available)
                - end_column: End column number (if available)

        NASA Rule 4: Under 60 lines
        NASA Rule 5: Input assertions
        """
        assert isinstance(node, ast.AST), "node must be an AST node"
        assert isinstance(file_path, str), "file_path must be string"

        location = {
            "file": file_path,
            "line": getattr(node, "lineno", 0),
            "column": getattr(node, "col_offset", 0),
        }

        # Add end location if available (Python 3.8+)
        if hasattr(node, "end_lineno"):
            location["end_line"] = node.end_lineno
        if hasattr(node, "end_col_offset"):
            location["end_column"] = node.end_col_offset

        return location

    @staticmethod
    def extract_code_snippet(source_lines: List[str], node: ast.AST, context_lines: int = 2) -> str:
        """
        Extract code snippet around the given AST node.

        This delegates to the existing code_utils.get_code_snippet_for_node()
        to avoid duplication. This method exists for API compatibility.

        Args:
            source_lines: Source code lines
            node: AST node to get snippet for
            context_lines: Number of context lines before/after

        Returns:
            Formatted code snippet with line numbers

        NASA Rule 4: Under 60 lines
        NASA Rule 5: Input assertions
        """
        assert isinstance(source_lines, list), "source_lines must be list"
        assert isinstance(node, ast.AST), "node must be an AST node"
        assert isinstance(context_lines, int), "context_lines must be integer"

        # Delegate to existing utility to avoid duplication
        from analyzer.utils.code_utils import get_code_snippet_for_node

        return get_code_snippet_for_node(node, source_lines, context_lines)

    @staticmethod
    def get_node_type_name(node: ast.AST) -> str:
        """
        Get the type name of an AST node as a string.

        Args:
            node: AST node

        Returns:
            String name of the node type (e.g., "FunctionDef", "If", "Assign")

        NASA Rule 4: Under 60 lines
        """
        assert isinstance(node, ast.AST), "node must be an AST node"
        return node.__class__.__name__
