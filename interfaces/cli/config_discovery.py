# SPDX-License-Identifier: MIT
"""
Configuration discovery for connascence analyzer.

Automatically discovers and loads configuration from:
1. .connascence.yml file
2. pyproject.toml [tool.connascence] section
3. setup.cfg [connascence] section
4. .connascence.cfg file
5. Environment variables
"""

import configparser
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import toml

    TOML_AVAILABLE = True
except ImportError:
    try:
        import tomli as toml

        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigDiscovery:
    """Discovers configuration files and loads settings."""

    def __init__(self, start_path: Optional[Union[str, Path]] = None):
        self.start_path = Path(start_path or Path.cwd())

    def discover_config(self) -> Dict[str, Any]:
        """Discover configuration from multiple sources."""
        config = self._get_default_config()

        # Look for configuration files in order of preference
        config_sources = [
            self._load_connascence_yml,
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

        # Validate final configuration
        validated_config = self._validate_config(config)
        return validated_config

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
            "output_file": None,
            "ignore_failures": False,
            "parallel": True,
            "threshold": None,
            "detailed": False,
            "metrics": False,
            "baseline": None,
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

    def _load_connascence_yml(self) -> Optional[Dict[str, Any]]:
        """Load configuration from .connascence.yml."""
        if not YAML_AVAILABLE:
            return None

        config_file = self._find_config_file(".connascence.yml")
        if not config_file:
            # Also try .connascence.yaml
            config_file = self._find_config_file(".connascence.yaml")
            if not config_file:
                return None

        try:
            with open(config_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data and isinstance(data, dict):
                return self._normalize_config(data)

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
            "CONNASCENCE_OUTPUT_FILE": "output_file",
            "CONNASCENCE_IGNORE_FAILURES": "ignore_failures",
            "CONNASCENCE_PARALLEL": "parallel",
            "CONNASCENCE_THRESHOLD": "threshold",
            "CONNASCENCE_DETAILED": "detailed",
            "CONNASCENCE_METRICS": "metrics",
            "CONNASCENCE_BASELINE": "baseline",
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
            elif key in (
                "exit_zero",
                "show_source",
                "strict_mode",
                "nasa_validation",
                "ignore_failures",
                "parallel",
                "detailed",
                "metrics",
            ):
                # Convert to boolean
                normalized[key] = self._to_bool(value)
            elif key == "threshold" and value is not None:
                # Convert threshold to integer
                try:
                    normalized[key] = int(value)
                except (ValueError, TypeError):
                    normalized[key] = value
            else:
                normalized[key] = value

        return normalized

    def _convert_env_value(self, value: str, key: str) -> Any:
        """Convert environment variable value to appropriate type."""
        if key in (
            "exit_zero",
            "show_source",
            "strict_mode",
            "nasa_validation",
            "ignore_failures",
            "parallel",
            "detailed",
            "metrics",
        ):
            return self._to_bool(value)
        elif key in ("exclude", "include"):
            return [item.strip() for item in value.split(",") if item.strip()]
        elif key == "threshold":
            try:
                return int(value)
            except (ValueError, TypeError):
                return value
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

        if config_file.suffix in (".yml", ".yaml"):
            return self._load_yaml_file(config_file) or {}
        elif config_file.suffix in (".toml", ".tml"):
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

    def _load_yaml_file(self, config_file: Path) -> Optional[Dict[str, Any]]:
        """Load configuration from a YAML file."""
        if not YAML_AVAILABLE:
            raise ImportError("YAML support not available. Install 'pyyaml' package.")

        try:
            with open(config_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data and isinstance(data, dict):
                return self._normalize_config(data)

        except Exception:
            pass

        return None

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration values and apply constraints."""
        validated = config.copy()

        # Validate format option
        valid_formats = ["json", "text", "csv", "xml", "html", "yaml"]
        if validated.get("format") not in valid_formats:
            validated["format"] = "json"

        # Validate severity levels
        valid_severities = ["low", "medium", "high", "critical", None]
        if validated.get("severity") not in valid_severities:
            validated["severity"] = None

        # Validate threshold
        if "threshold" in validated and validated["threshold"] is not None:
            try:
                threshold = int(validated["threshold"])
                if threshold < 0:
                    validated["threshold"] = 0
                else:
                    validated["threshold"] = threshold
            except (ValueError, TypeError):
                validated["threshold"] = None

        # Ensure lists are actually lists
        for key in ("exclude", "include"):
            if key in validated and not isinstance(validated[key], list):
                validated[key] = []

        # Validate file paths
        if validated.get("output_file"):
            try:
                output_path = Path(validated["output_file"])
                # Ensure parent directory exists or can be created
                if output_path.parent != Path("."):
                    validated["output_file"] = str(output_path)
            except Exception:
                validated["output_file"] = None

        if validated.get("baseline"):
            baseline_path = Path(validated["baseline"])
            if not baseline_path.exists():
                validated["baseline"] = None

        return validated

    def get_config_template(self, format_type: str = "yml") -> str:
        """Generate a configuration file template."""
        if format_type.lower() in ("yml", "yaml"):
            return self._get_yaml_template()
        elif format_type.lower() == "toml":
            return self._get_toml_template()
        elif format_type.lower() in ("cfg", "ini"):
            return self._get_cfg_template()
        else:
            raise ValueError(f"Unsupported template format: {format_type}")

    def _get_yaml_template(self) -> str:
        """Generate YAML configuration template."""
        return """# Connascence Analyzer Configuration
# See: https://connascence.io for more information

# Analysis policy (default, strict, permissive)
policy: default

# Output format (json, text, csv, xml, html, yaml)  
format: json

# Files/patterns to exclude from analysis
exclude:
  - "test_*"
  - "*.pyc"
  - "__pycache__/*"

# Files/patterns to include (empty = all files)
include: []

# Maximum line length for position connascence
max_line_length: 120

# Show source code in output
show_source: false

# Exit with code 0 even if issues found
exit_zero: false

# Minimum severity level to report (low, medium, high, critical)
severity: null

# Enable strict validation mode
strict_mode: false

# Enable NASA coding standards validation
nasa_validation: false

# Output file path (optional)
output_file: null

# Ignore analysis failures and continue
ignore_failures: false

# Enable parallel processing
parallel: true

# Minimum connascence threshold to report
threshold: null

# Include detailed analysis information
detailed: false

# Include performance metrics in output
metrics: false

# Baseline file for comparison (optional)
baseline: null
"""

    def _get_toml_template(self) -> str:
        """Generate TOML configuration template."""
        return """# Connascence Analyzer Configuration
[tool.connascence]

# Analysis policy (default, strict, permissive)
policy = "default"

# Output format (json, text, csv, xml, html, yaml)
format = "json"

# Files/patterns to exclude from analysis
exclude = ["test_*", "*.pyc", "__pycache__/*"]

# Files/patterns to include (empty = all files)
include = []

# Maximum line length for position connascence
max_line_length = 120

# Show source code in output
show_source = false

# Exit with code 0 even if issues found
exit_zero = false

# Minimum severity level to report (low, medium, high, critical)
# severity = "medium"

# Enable strict validation mode
strict_mode = false

# Enable NASA coding standards validation
nasa_validation = false

# Output file path (optional)
# output_file = "connascence-report.json"

# Ignore analysis failures and continue
ignore_failures = false

# Enable parallel processing
parallel = true

# Minimum connascence threshold to report
# threshold = 5

# Include detailed analysis information
detailed = false

# Include performance metrics in output
metrics = false

# Baseline file for comparison (optional)
# baseline = "baseline.json"
"""

    def _get_cfg_template(self) -> str:
        """Generate CFG/INI configuration template."""
        return """# Connascence Analyzer Configuration
[connascence]

# Analysis policy (default, strict, permissive)
policy = default

# Output format (json, text, csv, xml, html, yaml)
format = json

# Files/patterns to exclude from analysis (comma-separated)
exclude = test_*, *.pyc, __pycache__/*

# Files/patterns to include (empty = all files)
include = 

# Maximum line length for position connascence
max_line_length = 120

# Show source code in output
show_source = false

# Exit with code 0 even if issues found
exit_zero = false

# Minimum severity level to report (low, medium, high, critical)
# severity = medium

# Enable strict validation mode
strict_mode = false

# Enable NASA coding standards validation
nasa_validation = false

# Output file path (optional)
# output_file = connascence-report.json

# Ignore analysis failures and continue
ignore_failures = false

# Enable parallel processing
parallel = true

# Minimum connascence threshold to report
# threshold = 5

# Include detailed analysis information
detailed = false

# Include performance metrics in output
metrics = false

# Baseline file for comparison (optional)
# baseline = baseline.json
"""

    def validate_config_file(self, config_path: str) -> List[str]:
        """Validate a configuration file and return any errors."""
        errors = []

        try:
            config = self.load_config_file(config_path)
            validated = self._validate_config(config)

            # Check for required dependencies
            config_file = Path(config_path)
            if config_file.suffix in (".yml", ".yaml") and not YAML_AVAILABLE:
                errors.append("YAML support not available. Install 'pyyaml' package.")
            elif config_file.suffix in (".toml", ".tml") and not TOML_AVAILABLE:
                errors.append("TOML support not available. Install 'toml' or 'tomli' package.")

            # Check for validation issues
            original_keys = set(config.keys())
            validated_keys = set(validated.keys())

            if original_keys != validated_keys:
                errors.append("Configuration was modified during validation")

        except FileNotFoundError:
            errors.append(f"Configuration file not found: {config_path}")
        except ValueError as e:
            errors.append(f"Invalid configuration format: {e}")
        except Exception as e:
            errors.append(f"Error loading configuration: {e}")

        return errors
