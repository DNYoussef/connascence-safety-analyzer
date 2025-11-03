"""Compatibility namespace bridging legacy integration tests."""
from importlib import import_module
from typing import Any

__all__ = ["grammar", "security", "sales", "vscode_extension"]


def _alias(submodule: str, target: str) -> Any:
    module = import_module(target)
    globals()[submodule] = module
    return module

# Bridge to existing first-party packages when available. These imports are
# best-effort; integrations rely on the attribute being present even if the
# underlying implementation is a lightweight shim.
try:  # pragma: no cover - defensive import
    _alias("policy", "policy")
except ModuleNotFoundError:
    pass
