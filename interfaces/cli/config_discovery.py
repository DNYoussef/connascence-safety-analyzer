# SPDX-License-Identifier: MIT
"""
Configuration discovery for connascence analyzer.

Automatically discovers and loads configuration from:
1. pyproject.toml [tool.connascence] section
2. setup.cfg [connascence] section
3. .connascence.cfg file
4. Environment variables
"""

import configparser
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    try:
        import tomli as toml
        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False


class ConfigDiscovery:
    """Discovers configuration files and loads settings."""

    def __init__(self, start_path: Optional[Union[str, Path]] = None):
        self.start_path = Path(start_path or Path.cwd())

    def discover_config(self) -> Dict[str, Any]:
        """Discover configuration from multiple sources."""
        config = self._get_default_config()

        # Look for configuration files in order of preference
        config_sources = [
            self._load_pyproject_toml,
            self._load_setup_cfg,
            self._load_connascence_cfg,
        ]

        for loader in config_sources:
            try:
                found_config = loader()
                if found_config:
                    config.update(found_config)
                    break
            except Exception:
                continue

        # Override with environment variables
        env_config = self._load_from_environment()
        config.update(env_config)

        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "policy": "default",
            "format": "json",
            "exclude": [],
            "include": [],
            "max_line_length": 120,
            "show_source": False,
            "exit_zero": False,
            "severity": None,
            "strict_mode": False,
            "nasa_validation": False,
        }

    def _find_config_file(self, filename: str) -> Optional[Path]:
        """Find a configuration file by walking up the directory tree."""
        current = self.start_path

        while current != current.parent:  # Stop at filesystem root
            config_file = current / filename
            if config_file.exists():
                return config_file
            current = current.parent

        return None

    def _load_pyproject_toml(self) -> Optional[Dict[str, Any]]:
        """Load configuration from pyproject.toml."""
        if not TOML_AVAILABLE:
            return None

        config_file = self._find_config_file("pyproject.toml")
        if not config_file:
            return None

        try:
            data = toml.load(config_file)
            tool_config = data.get("tool", {})
            connascence_config = tool_config.get("connascence", {})

            if connascence_config:
                return self._normalize_config(connascence_config)

        except Exception:
            pass

        return None

    def _load_setup_cfg(self) -> Optional[Dict[str, Any]]:
        """Load configuration from setup.cfg."""
        config_file = self._find_config_file("setup.cfg")
        if not config_file:
            return None

        try:
            parser = configparser.ConfigParser()
            parser.read(config_file)

            if "connascence" in parser:
                section = parser["connascence"]
                return self._normalize_config(dict(section))

        except Exception:
            pass

        return None

    def _load_connascence_cfg(self) -> Optional[Dict[str, Any]]:
        """Load configuration from .connascence.cfg."""
        config_file = self._find_config_file(".connascence.cfg")
        if not config_file:
            return None

        try:
            parser = configparser.ConfigParser()
            parser.read(config_file)

            if "connascence" in parser:
                section = parser["connascence"]
                return self._normalize_config(dict(section))
            elif parser.sections():
                # Use first section if no [connascence] section
                first_section = parser.sections()[0]
                return self._normalize_config(dict(parser[first_section]))

        except Exception:
            pass

        return None

    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        env_mappings = {
            "CONNASCENCE_POLICY": "policy",
            "CONNASCENCE_FORMAT": "format",
            "CONNASCENCE_EXCLUDE": "exclude",
            "CONNASCENCE_INCLUDE": "include",
            "CONNASCENCE_SEVERITY": "severity",
            "CONNASCENCE_EXIT_ZERO": "exit_zero",
            "CONNASCENCE_SHOW_SOURCE": "show_source",
            "CONNASCENCE_STRICT_MODE": "strict_mode",
            "CONNASCENCE_NASA_VALIDATION": "nasa_validation",
        }

        for env_var, config_key in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                config[config_key] = self._convert_env_value(value, config_key)

        return config

    def _normalize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize configuration values to expected types."""
        normalized = {}

        for key, value in config.items():
            if key in ("exclude", "include") and isinstance(value, str):
                # Convert comma-separated strings to lists
                normalized[key] = [item.strip() for item in value.split(",") if item.strip()]
            elif key in ("exit_zero", "show_source", "strict_mode", "nasa_validation"):
                # Convert to boolean
                normalized[key] = self._to_bool(value)
            else:
                normalized[key] = value

        return normalized

    def _convert_env_value(self, value: str, key: str) -> Any:
        """Convert environment variable value to appropriate type."""
        if key in ("exit_zero", "show_source", "strict_mode", "nasa_validation"):
            return self._to_bool(value)
        elif key in ("exclude", "include"):
            return [item.strip() for item in value.split(",") if item.strip()]
        else:
            return value

    def _to_bool(self, value: Any) -> bool:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from a specific file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        if config_file.suffix in (".toml", ".tml"):
            return self._load_toml_file(config_file) or {}
        elif config_file.suffix in (".cfg", ".ini"):
            return self._load_cfg_file(config_file) or {}
        else:
            raise ValueError(f"Unsupported configuration file format: {config_file.suffix}")

    def _load_toml_file(self, config_file: Path) -> Optional[Dict[str, Any]]:
        """Load configuration from a TOML file."""
        if not TOML_AVAILABLE:
            raise ImportError("TOML support not available. Install 'toml' or 'tomli' package.")

        try:
            data = toml.load(config_file)
            if "tool" in data and "connascence" in data["tool"]:
                return self._normalize_config(data["tool"]["connascence"])
            elif "connascence" in data:
                return self._normalize_config(data["connascence"])
        except Exception:
            pass

        return None

    def _load_cfg_file(self, config_file: Path) -> Optional[Dict[str, Any]]:
        """Load configuration from a CFG/INI file."""
        try:
            parser = configparser.ConfigParser()
            parser.read(config_file)

            if "connascence" in parser:
                return self._normalize_config(dict(parser["connascence"]))
            elif parser.sections():
                first_section = parser.sections()[0]
                return self._normalize_config(dict(parser[first_section]))
        except Exception:
            pass

        return None
