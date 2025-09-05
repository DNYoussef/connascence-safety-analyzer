# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Base integration class for external tool integrations.

Provides common functionality for integrating with external tools
like linters, formatters, and security scanners.
"""

import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseIntegration(ABC):
    """Base class for external tool integrations."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._version_cache: Optional[str] = None
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the name of the external tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of the tool."""
        pass
    
    @property
    @abstractmethod
    def version_command(self) -> List[str]:
        """Return the command to get tool version."""
        pass
    
    def is_available(self) -> bool:
        """Check if the external tool is available in the environment."""
        try:
            result = subprocess.run(self.version_command, 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_version(self) -> str:
        """Get the tool version."""
        if self._version_cache:
            return self._version_cache
        
        try:
            result = subprocess.run(self.version_command,
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self._version_cache = result.stdout.strip()
                return self._version_cache
            return "unknown"
        except FileNotFoundError:
            return "not available"
    
    def run_command(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Run a command with the external tool."""
        cmd = [self.tool_name] + args
        return subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    
    @abstractmethod
    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze a file with the external tool."""
        pass
    
    def get_integration_info(self) -> Dict[str, Any]:
        """Get information about this integration."""
        return {
            'tool_name': self.tool_name,
            'description': self.description,
            'version': self.get_version(),
            'available': self.is_available(),
            'config': self.config
        }