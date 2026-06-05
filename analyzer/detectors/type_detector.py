"""Dedicated Connascence of Type detector."""

import ast
from typing import List

from utils.types import ConnascenceViolation

from .base import DetectorBase


class TypeDetector(DetectorBase):
    """Detects type-coupling signals such as unannotated public functions."""

    SUPPORTED_EXTENSIONS = [".py"]

    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        self.violations.clear()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function_annotations(node)
        return self.violations

    def _check_function_annotations(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        if node.name.startswith("_"):
            return

        missing_params = [
            arg.arg
            for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
            if arg.arg not in {"self", "cls"} and arg.annotation is None
        ]
        missing_return = node.returns is None
        if not missing_params and not missing_return:
            return

        pieces = []
        if missing_params:
            pieces.append(f"parameters without annotations: {', '.join(missing_params)}")
        if missing_return:
            pieces.append("missing return annotation")

        self.violations.append(
            ConnascenceViolation(
                id=f"cot_{node.name}_{node.lineno}",
                rule_id="CON_CoT",
                type="connascence_of_type",
                severity="medium",
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Connascence of Type: {node.name} has {'; '.join(pieces)}",
                recommendation="Add explicit type annotations or a typed boundary object.",
                code_snippet=self.get_code_snippet(node),
                context={
                    "function_name": node.name,
                    "missing_parameters": missing_params,
                    "missing_return": missing_return,
                },
            )
        )
