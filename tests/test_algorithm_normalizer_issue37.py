"""Regression tests for issue #37: CoA must compare bodies, not shapes.

Fixture distilled from the GuardSpine W4.3d case (GuardSpine PR #104):
dispatch/registry handlers share a uniform SHAPE (arity check -> eval ->
guard -> return) but carry DISTINCT logic; the old statement-type-skeleton
normalization hashed them identically and flagged them as duplicate
algorithms, while the detector's true target -- copy-paste duplication
with renamed variables -- is what must keep firing.
"""

import ast

from analyzer.detectors.algorithm_detector import AlgorithmDetector
from analyzer.detectors.algorithm_normalizer import normalized_algorithm_hash

# Same shape, DISTINCT logic: miniatures of GuardSpine's _fn_t / _fn_not /
# _fn_isblank handlers. Old skeleton: identical. Bodies: different methods,
# different operators, different constants.
DISTINCT_LOGIC_SRC = '''
class Dispatch:
    def fn_t(self, name, expr, sheet, coord):
        if len(expr.args) != 1:
            return Result(False, reason=f"{name}-arity")
        value = self.eval_expr(expr.args[0], sheet, coord)
        if not value.supported:
            return value
        return Result(True, value.value if isinstance(value.value, str) else "")

    def fn_not(self, name, expr, sheet, coord):
        if len(expr.args) != 1:
            return Result(False, reason=f"{name}-arity")
        value = self.eval_expr(expr.args[0], sheet, coord)
        if not value.supported:
            return value
        return Result(True, not self.coerce_bool(value.value))

    def fn_isblank(self, name, expr, sheet, coord):
        if len(expr.args) != 1:
            return Result(False, reason=f"{name}-arity")
        value = self.eval_expr(expr.args[0], sheet, coord)
        if not value.supported:
            return value
        return Result(True, value.value is None)
'''

# True copy-paste duplication: identical logic, locals renamed, docstring
# differs. This is what CoA exists to catch and MUST keep firing.
COPY_PASTE_SRC = '''
def total_alpha(items, rate):
    """Computes the alpha total."""
    accum = 0
    for item in items:
        scaled = item * rate
        if scaled > 10:
            accum += scaled
    return accum

def total_beta(entries, factor):
    """Beta variant -- different docstring, renamed locals."""
    bucket = 0
    for entry in entries:
        adjusted = entry * factor
        if adjusted > 10:
            bucket += adjusted
    return bucket
'''


def _functions(src):
    tree = ast.parse(src)
    return tree, [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]


def test_distinct_logic_same_shape_hashes_differ():
    _, funcs = _functions(DISTINCT_LOGIC_SRC)
    hashes = {f.name: normalized_algorithm_hash(f) for f in funcs}
    assert len(set(hashes.values())) == 3, (
        f"distinct-logic handlers must not hash equal: {hashes}"
    )


def test_copy_paste_with_renamed_locals_hashes_equal():
    _, funcs = _functions(COPY_PASTE_SRC)
    h = [normalized_algorithm_hash(f) for f in funcs]
    assert h[0] == h[1], "rename-only copy-paste must still hash equal"


def test_detector_flags_copy_paste_not_dispatch_handlers():
    src = DISTINCT_LOGIC_SRC + COPY_PASTE_SRC
    tree = ast.parse(src)
    detector = AlgorithmDetector("fixture.py", src.splitlines())
    violations = detector.detect_violations(tree)
    flagged = {v.context["function_name"] for v in violations}
    assert "total_alpha" in flagged and "total_beta" in flagged, (
        f"copy-paste duplicates must still be flagged, got {flagged}"
    )
    assert not {"fn_t", "fn_not", "fn_isblank"} & flagged, (
        f"distinct-logic handlers must NOT be flagged, got {flagged}"
    )


def test_normalization_does_not_mutate_the_tree():
    tree, funcs = _functions(COPY_PASTE_SRC)
    before = ast.dump(tree)
    for f in funcs:
        normalized_algorithm_hash(f)
    assert ast.dump(tree) == before, "normalizer must not mutate shared AST"


def test_hash_is_deterministic():
    _, funcs = _functions(COPY_PASTE_SRC)
    assert normalized_algorithm_hash(funcs[0]) == normalized_algorithm_hash(funcs[0])
