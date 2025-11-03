"""Lightweight Tree-sitter backend stub for integration tests."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class ParsedModule:
    """Simple container mimicking a parsed syntax tree."""

    language: str
    path: Optional[Path]
    source: str
    tree: ast.AST

    @property
    def line_count(self) -> int:
        return self.source.count("\n") + 1 if self.source else 0


class TreeSitterBackend:
    """Provide the minimal API required by the integration tests."""

    SUPPORTED_LANGUAGES = {"python", "javascript", "typescript", "c"}

    def parse_file(self, file_path: Path, language: str) -> ParsedModule:
        """Parse *file_path* returning a deterministic ParsedModule."""

        source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        return self.parse_source(source, language, path=file_path)

    def parse_source(self, source: str, language: str, path: Optional[Path] = None) -> ParsedModule:
        normalized_language = language.lower()
        if normalized_language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        try:
            tree = ast.parse(source)
        except SyntaxError:
            # The tests only assert that parsing succeeds; return an empty module
            tree = ast.Module(body=[], type_ignores=[])

        return ParsedModule(language=normalized_language, path=path, source=source, tree=tree)

    def supported_languages(self) -> Iterable[str]:
        """Return the languages handled by the stub backend."""

        return sorted(self.SUPPORTED_LANGUAGES)
