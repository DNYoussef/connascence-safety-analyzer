# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Unified Import Strategy
======================

Eliminates the try/except import hell and fallback mode dependencies that
cause 1,177 parameter bomb violations and fragmented import strategies
across the codebase.

This provides a single, consistent way to import modules with proper
dependency resolution and graceful degradation.
"""

from dataclasses import dataclass, field
from enum import Enum
import importlib
import importlib.util
import logging
from pathlib import Path
import sys
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ImportStatus(Enum):
    """Status of module import."""

    SUCCESS = "success"
    FAILED = "failed"
    FALLBACK = "fallback"
    NOT_FOUND = "not_found"
    VERSION_MISMATCH = "version_mismatch"


@dataclass
class ImportResult:
    """Result of a module import attempt."""

    module: Optional[Any]
    status: ImportStatus
    error_message: Optional[str] = None
    fallback_used: bool = False
    version: Optional[str] = None
    import_path: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if import was successful."""
        return self.status == ImportStatus.SUCCESS

    @property
    def has_module(self) -> bool:
        """Check if a module was imported (including fallbacks)."""
        return self.module is not None


@dataclass
class ImportSpec:
    """Specification for a module import."""

    module_name: str
    attribute_name: Optional[str] = None
    fallback_modules: List[str] = field(default_factory=list)
    required: bool = True
    min_version: Optional[str] = None
    custom_loader: Optional[Callable] = None
    search_paths: List[Union[str, Path]] = field(default_factory=list)

    def __post_init__(self):
        """Convert string paths to Path objects."""
        self.search_paths = [Path(p) for p in self.search_paths]


class UnifiedImportManager:
    """
    Centralized import management system.

    Replaces scattered try/except import patterns with a unified
    approach that provides:
    - Graceful fallback handling
    - Version checking
    - Custom search paths
    - Import caching
    - Dependency tracking
    - Clear error reporting
    """

    def __init__(self):
        self._import_cache: Dict[str, ImportResult] = {}
        self._search_paths: List[Path] = []
        self._fallback_registry: Dict[str, Dict[str, Any]] = {}
        self._dependency_graph: Dict[str, List[str]] = {}

        # Add common search paths
        self._add_default_search_paths()

    def _add_default_search_paths(self):
        """Add common search paths for the connascence analyzer."""
        base_path = Path(__file__).parent.parent

        common_paths = [
            base_path,
            base_path / "analyzer",
            base_path / "mcp",
            base_path / "utils",
            base_path / "config",
            base_path / "integrations",
            base_path / "autofix",
            base_path / "grammar",
            base_path / "experimental" / "src",
        ]

        for path in common_paths:
            if path.exists():
                self.add_search_path(path)

    def add_search_path(self, path: Union[str, Path]):
        """Add a directory to the module search path."""
        path = Path(path)
        if path.exists() and path not in self._search_paths:
            self._search_paths.append(path)
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))

    def register_fallback(self, primary_module: str, fallback_data: Dict[str, Any]):
        """Register fallback data for when a module cannot be imported."""
        self._fallback_registry[primary_module] = fallback_data

    def import_module(self, spec: ImportSpec) -> ImportResult:
        """
        Import a module according to the specification.

        Args:
            spec: ImportSpec defining how to import the module

        Returns:
            ImportResult with the imported module or fallback
        """
        cache_key = f"{spec.module_name}::{spec.attribute_name or ''}"

        # Check cache first
        if cache_key in self._import_cache:
            return self._import_cache[cache_key]

        result = self._attempt_import(spec)

        # Cache the result
        self._import_cache[cache_key] = result

        return result

    def _attempt_import(self, spec: ImportSpec) -> ImportResult:
        """Attempt to import a module with fallback handling."""

        # Try primary module
        result = self._try_import_single(spec.module_name, spec.attribute_name)
        if result.success:
            # Check version if required
            if spec.min_version and not self._check_version(result.module, spec.min_version):
                return ImportResult(
                    module=None,
                    status=ImportStatus.VERSION_MISMATCH,
                    error_message=f"Version requirement not met: {spec.min_version}",
                    import_path=spec.module_name,
                )

            result.import_path = spec.module_name
            return result

        # Try fallback modules
        for fallback_name in spec.fallback_modules:
            fallback_result = self._try_import_single(fallback_name, spec.attribute_name)
            if fallback_result.success:
                fallback_result.fallback_used = True
                fallback_result.import_path = fallback_name
                fallback_result.status = ImportStatus.FALLBACK
                logger.info(f"Using fallback {fallback_name} for {spec.module_name}")
                return fallback_result

        # Try custom loader
        if spec.custom_loader:
            try:
                module = spec.custom_loader()
                return ImportResult(
                    module=module, status=ImportStatus.SUCCESS, fallback_used=True, import_path="custom_loader"
                )
            except Exception as e:
                logger.warning(f"Custom loader failed: {e}")

        # Check for registered fallback data
        if spec.module_name in self._fallback_registry:
            fallback_data = self._fallback_registry[spec.module_name]
            return ImportResult(
                module=fallback_data, status=ImportStatus.FALLBACK, fallback_used=True, import_path="fallback_registry"
            )

        # All import attempts failed
        error_msg = f"Failed to import {spec.module_name}"
        if spec.fallback_modules:
            error_msg += f" or fallbacks: {', '.join(spec.fallback_modules)}"

        status = ImportStatus.NOT_FOUND if spec.required else ImportStatus.FAILED

        return ImportResult(module=None, status=status, error_message=error_msg, import_path=spec.module_name)

    def _try_import_single(self, module_name: str, attribute_name: Optional[str] = None) -> ImportResult:
        """Try to import a single module."""
        try:
            # Try direct import first
            module = importlib.import_module(module_name)

            # If attribute requested, get it from the module
            if attribute_name:
                try:
                    module = getattr(module, attribute_name)
                except AttributeError:
                    return ImportResult(
                        module=None,
                        status=ImportStatus.FAILED,
                        error_message=f"Attribute {attribute_name} not found in {module_name}",
                    )

            return ImportResult(module=module, status=ImportStatus.SUCCESS)

        except ImportError as e:
            # Try searching in additional paths
            for search_path in self._search_paths:
                module_file = search_path / f"{module_name.replace('.', '/')}.py"
                if module_file.exists():
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, module_file)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)

                            if attribute_name:
                                module = getattr(module, attribute_name)

                            return ImportResult(module=module, status=ImportStatus.SUCCESS)
                    except Exception as path_error:
                        logger.debug(f"Failed to load {module_name} from {search_path}: {path_error}")
                        continue

            return ImportResult(module=None, status=ImportStatus.FAILED, error_message=str(e))

    def _check_version(self, module: Any, min_version: str) -> bool:
        """Check if module meets minimum version requirement."""
        try:
            # Try common version attributes
            for attr in ["__version__", "version", "VERSION"]:
                if hasattr(module, attr):
                    version = getattr(module, attr)
                    if isinstance(version, str):
                        # Simple version comparison (for complex cases, use packaging.version)
                        return version >= min_version
                    elif hasattr(version, "__iter__"):
                        # Handle version tuples like (1, 2, 3)
                        version_str = ".".join(map(str, version))
                        return version_str >= min_version

            # If no version found, assume it's okay
            return True

        except Exception:
            # If version check fails, assume it's okay
            return True

    def import_constants(self) -> ImportResult:
        """Import the central constants with fallbacks."""
        spec = ImportSpec(
            module_name="config.central_constants",
            fallback_modules=["analyzer.constants", "experimental.src.constants"],
            required=True,
        )
        return self.import_module(spec)

    def import_unified_analyzer(self) -> ImportResult:
        """Import the unified analyzer with fallback mode."""
        spec = ImportSpec(
            module_name="analyzer.unified_analyzer",
            attribute_name="UnifiedConnascenceAnalyzer",
            fallback_modules=["analyzer.core"],
            required=False,
        )
        result = self.import_module(spec)

        if not result.success:
            logger.warning("Unified analyzer not available, using fallback mode")

        return result

    def import_mcp_server(self) -> ImportResult:
        """Import MCP server components with fallbacks."""
        spec = ImportSpec(module_name="mcp.server", fallback_modules=["utils.mcp_fallback"], required=False)
        return self.import_module(spec)

    def import_reporting(self, reporter_type: str = "json") -> ImportResult:
        """Import reporting components."""
        module_map = {
            "json": "analyzer.reporting.json",
            "sarif": "analyzer.reporting.sarif",
            "markdown": "analyzer.reporting.markdown",
        }

        spec = ImportSpec(
            module_name=module_map.get(reporter_type, "analyzer.reporting.json"),
            fallback_modules=["analyzer.reporting"],
            required=False,
        )
        return self.import_module(spec)

    def get_import_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all attempted imports."""
        status = {}

        for cache_key, result in self._import_cache.items():
            module_name = cache_key.split("::")[0]
            status[module_name] = {
                "status": result.status.value,
                "success": result.success,
                "fallback_used": result.fallback_used,
                "has_module": result.has_module,
                "error": result.error_message,
                "import_path": result.import_path,
            }

        return status

    def clear_cache(self):
        """Clear the import cache."""
        self._import_cache.clear()


# =============================================================================
# GLOBAL INSTANCE AND CONVENIENCE FUNCTIONS
# =============================================================================

# Global import manager instance
IMPORT_MANAGER = UnifiedImportManager()


def import_with_fallback(
    module_name: str, attribute_name: Optional[str] = None, fallback_modules: Optional[List[str]] = None
) -> ImportResult:
    """
    Convenience function for importing with fallbacks.

    Args:
        module_name: Primary module to import
        attribute_name: Specific attribute to get from module
        fallback_modules: List of fallback module names

    Returns:
        ImportResult
    """
    spec = ImportSpec(
        module_name=module_name, attribute_name=attribute_name, fallback_modules=fallback_modules or [], required=False
    )
    return IMPORT_MANAGER.import_module(spec)


def safe_import(module_name: str, default=None) -> Any:
    """
    Safe import that returns a default value on failure.

    Args:
        module_name: Module to import
        default: Default value to return on failure

    Returns:
        Imported module or default value
    """
    result = import_with_fallback(module_name)
    return result.module if result.has_module else default


# =============================================================================
# LEGACY COMPATIBILITY LAYER
# =============================================================================


def get_constants():
    """Legacy function to get constants with unified import strategy."""
    result = IMPORT_MANAGER.import_constants()
    if result.has_module:
        return result.module

    # Ultimate fallback: create minimal constants inline
    class MinimalConstants:
        NASA_COMPLIANCE_THRESHOLD = 0.95
        MECE_QUALITY_THRESHOLD = 0.80
        OVERALL_QUALITY_THRESHOLD = 0.75
        VIOLATION_WEIGHTS = {"critical": 10, "high": 5, "medium": 2, "low": 1}

    return MinimalConstants()


def get_unified_analyzer():
    """Legacy function to get unified analyzer with fallback."""
    result = IMPORT_MANAGER.import_unified_analyzer()
    return result.module if result.has_module else None


# Register common fallbacks
IMPORT_MANAGER.register_fallback(
    "analyzer.core", {"UNIFIED_ANALYZER_AVAILABLE": False, "ConnascenceViolation": type("MockViolation", (), {})}
)

# Add analyzer-specific constants
IMPORT_MANAGER.register_fallback("constants", get_constants())

__all__ = [
    "IMPORT_MANAGER",
    "ImportResult",
    "ImportSpec",
    "ImportStatus",
    "UnifiedImportManager",
    "get_constants",
    "get_unified_analyzer",
    "import_with_fallback",
    "safe_import",
]
