# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Unified Base Integration Pattern
================================

Consolidates 85.7% duplicate code across integration files into a single,
reusable base class that provides common functionality for all external
tool integrations (Black, MyPy, Ruff, Radon, etc.).

This eliminates the architectural fragmentation identified in the MECE report.
"""

import subprocess
import json
import logging
import shlex
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

# Import central constants
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.central_constants import (
    IntegrationConstants, PerformanceLimits, ExitCode
)

logger = logging.getLogger(__name__)


class IntegrationType(Enum):
    """Types of external tool integrations."""
    LINTER = "linter"
    FORMATTER = "formatter"
    TYPE_CHECKER = "type_checker"
    SECURITY_SCANNER = "security_scanner"
    COMPLEXITY_ANALYZER = "complexity_analyzer"
    DOCUMENTATION_GENERATOR = "doc_generator"


@dataclass
class IntegrationResult:
    """Standardized result from external tool integration."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    issues: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    execution_time: float
    
    @property
    def has_issues(self) -> bool:
        """Check if integration found any issues."""
        return len(self.issues) > 0
    
    @property
    def issue_count(self) -> int:
        """Get total number of issues found."""
        return len(self.issues)


class UnifiedBaseIntegration(ABC):
    """
    Unified base class for all external tool integrations.
    
    Provides common functionality that was duplicated across 85.7% of 
    integration files, including:
    - Tool availability checking
    - Version caching and retrieval
    - Subprocess execution with timeouts
    - Output parsing and standardization
    - Error handling and logging
    - Configuration management
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._version_cache: Optional[str] = None
        self._availability_cache: Optional[bool] = None
        self.logger = logging.getLogger(f"{__name__}.{self.tool_name}")
    
    # =================================================================
    # ABSTRACT PROPERTIES (Must be implemented by subclasses)
    # =================================================================
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the name of the external tool."""
        pass
    
    @property 
    @abstractmethod
    def tool_command(self) -> str:
        """Return the base command to run the tool."""
        pass
    
    @property
    @abstractmethod
    def version_command(self) -> List[str]:
        """Return the command to get tool version."""
        pass
    
    @property
    @abstractmethod
    def integration_type(self) -> IntegrationType:
        """Return the type of integration."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of the tool."""
        pass
    
    # =================================================================
    # CONCRETE IMPLEMENTATION (Common across all integrations)
    # =================================================================
    
    def is_available(self) -> bool:
        """
        Check if the external tool is available in the environment.
        Uses caching to avoid repeated subprocess calls.
        """
        if self._availability_cache is not None:
            return self._availability_cache
        
        try:
            result = self._run_command(
                self.version_command,
                timeout=PerformanceLimits.DEFAULT_TIMEOUT_SECONDS
            )
            self._availability_cache = result.returncode == 0
            return self._availability_cache
        except Exception as e:
            self.logger.warning(f"{self.tool_name} availability check failed: {e}")
            self._availability_cache = False
            return False
    
    def get_version(self) -> str:
        """
        Get the tool version with caching.
        Returns 'unknown' if version cannot be determined.
        """
        if self._version_cache:
            return self._version_cache
        
        if not self.is_available():
            return "unavailable"
        
        try:
            result = self._run_command(self.version_command)
            if result.returncode == 0:
                self._version_cache = self._parse_version(result.stdout)
                return self._version_cache
        except Exception as e:
            self.logger.warning(f"Failed to get {self.tool_name} version: {e}")
        
        self._version_cache = "unknown"
        return self._version_cache
    
    def run_analysis(self, 
                    file_path: Union[str, Path],
                    additional_args: Optional[List[str]] = None) -> IntegrationResult:
        """
        Run analysis on a file or directory.
        
        Args:
            file_path: Path to analyze
            additional_args: Additional command line arguments
            
        Returns:
            IntegrationResult with standardized output
        """
        if not self.is_available():
            return IntegrationResult(
                success=False,
                exit_code=ExitCode.ERROR,
                stdout="",
                stderr=f"{self.tool_name} is not available",
                issues=[],
                metadata={"error": "tool_unavailable"},
                execution_time=0.0
            )
        
        # Build command
        cmd = [self.tool_command]
        if additional_args:
            cmd.extend(additional_args)
        cmd.append(str(file_path))
        
        # Execute with timing
        import time
        start_time = time.time()
        
        try:
            result = self._run_command(
                cmd,
                timeout=PerformanceLimits.MAX_ANALYSIS_TIME_SECONDS
            )
            execution_time = time.time() - start_time
            
            # Parse output to issues
            issues = self._parse_output(result.stdout, result.stderr)
            
            return IntegrationResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                issues=issues,
                metadata=self._get_metadata(file_path),
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return IntegrationResult(
                success=False,
                exit_code=ExitCode.ERROR,
                stdout="",
                stderr=f"Analysis timed out after {PerformanceLimits.MAX_ANALYSIS_TIME_SECONDS}s",
                issues=[],
                metadata={"error": "timeout"},
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return IntegrationResult(
                success=False,
                exit_code=ExitCode.ERROR,
                stdout="",
                stderr=str(e),
                issues=[],
                metadata={"error": str(e)},
                execution_time=execution_time
            )
    
    def batch_analyze(self, 
                     file_paths: List[Union[str, Path]],
                     max_parallel: Optional[int] = None) -> Dict[str, IntegrationResult]:
        """
        Analyze multiple files with optional parallel processing.
        
        Args:
            file_paths: List of paths to analyze
            max_parallel: Maximum parallel analyses (defaults to config)
            
        Returns:
            Dictionary mapping file paths to results
        """
        max_parallel = max_parallel or PerformanceLimits.MAX_CONCURRENT_ANALYSES
        results = {}
        
        # For now, implement sequential processing
        # TODO: Add parallel processing with ThreadPoolExecutor
        for file_path in file_paths:
            try:
                results[str(file_path)] = self.run_analysis(file_path)
            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")
                results[str(file_path)] = IntegrationResult(
                    success=False,
                    exit_code=ExitCode.ERROR,
                    stdout="",
                    stderr=str(e),
                    issues=[],
                    metadata={"error": str(e)},
                    execution_time=0.0
                )
        
        return results
    
    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the integration."""
        return {
            'tool_name': self.tool_name,
            'description': self.description,
            'type': self.integration_type.value,
            'version': self.get_version(),
            'available': self.is_available(),
            'command': self.tool_command,
            'config': self.config
        }
    
    # =================================================================
    # PROTECTED METHODS (Can be overridden by subclasses)
    # =================================================================
    
    def _run_command(self, 
                    cmd: List[str],
                    timeout: Optional[int] = None,
                    cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """
        Run a subprocess command with consistent error handling.
        
        Args:
            cmd: Command and arguments
            timeout: Timeout in seconds
            cwd: Working directory
            
        Returns:
            CompletedProcess result
        """
        timeout = timeout or PerformanceLimits.DEFAULT_TIMEOUT_SECONDS
        
        self.logger.debug(f"Running command: {' '.join(shlex.quote(arg) for arg in cmd)}")
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            check=False  # Don't raise on non-zero exit
        )
    
    def _parse_version(self, version_output: str) -> str:
        """
        Parse version from tool output.
        Default implementation looks for semver patterns.
        """
        # Common version patterns
        patterns = [
            r'(\d+\.\d+\.\d+)',  # x.y.z
            r'(\d+\.\d+)',       # x.y
            r'v?(\d+\.\d+\.\d+)', # vx.y.z
        ]
        
        for pattern in patterns:
            match = re.search(pattern, version_output)
            if match:
                return match.group(1)
        
        # Fallback: return first word that contains numbers
        words = version_output.split()
        for word in words:
            if any(c.isdigit() for c in word):
                return word.strip('v')
        
        return "unknown"
    
    def _parse_output(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """
        Parse tool output into standardized issues.
        Default implementation returns empty list.
        Subclasses should override this for tool-specific parsing.
        """
        return []
    
    def _get_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get metadata for the analysis result."""
        file_path = Path(file_path)
        
        metadata = {
            'tool': self.tool_name,
            'version': self.get_version(),
            'file_path': str(file_path),
            'file_exists': file_path.exists(),
            'integration_type': self.integration_type.value
        }
        
        if file_path.exists():
            stat = file_path.stat()
            metadata.update({
                'file_size': stat.st_size,
                'file_mtime': stat.st_mtime,
                'is_directory': file_path.is_dir()
            })
        
        return metadata


# =============================================================================
# INTEGRATION REGISTRY
# =============================================================================

class IntegrationRegistry:
    """Registry for managing available integrations."""
    
    def __init__(self):
        self._integrations: Dict[str, UnifiedBaseIntegration] = {}
    
    def register(self, integration: UnifiedBaseIntegration):
        """Register an integration."""
        self._integrations[integration.tool_name] = integration
    
    def get(self, tool_name: str) -> Optional[UnifiedBaseIntegration]:
        """Get an integration by tool name."""
        return self._integrations.get(tool_name)
    
    def list_available(self) -> Dict[str, Dict[str, Any]]:
        """List all available integrations with their info."""
        return {
            name: integration.get_info()
            for name, integration in self._integrations.items()
            if integration.is_available()
        }
    
    def run_all(self, file_path: Union[str, Path]) -> Dict[str, IntegrationResult]:
        """Run all available integrations on a file."""
        results = {}
        
        for name, integration in self._integrations.items():
            if integration.is_available():
                try:
                    results[name] = integration.run_analysis(file_path)
                except Exception as e:
                    logger.error(f"Integration {name} failed: {e}")
                    results[name] = IntegrationResult(
                        success=False,
                        exit_code=ExitCode.ERROR,
                        stdout="",
                        stderr=str(e),
                        issues=[],
                        metadata={"error": str(e)},
                        execution_time=0.0
                    )
        
        return results


# Global registry instance
INTEGRATION_REGISTRY = IntegrationRegistry()