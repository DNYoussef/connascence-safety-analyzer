"""
Clarity Linter Configuration Loader

Loads and validates clarity_linter.yaml configuration files.

NASA Rule 4 Compliant: All functions under 60 lines
NASA Rule 5 Compliant: Input assertions
"""

from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("[WARNING] PyYAML not available, using default configuration")


class ClarityConfigLoader:
    """
    Loader for clarity_linter.yaml configuration files.

    Provides configuration loading, validation, and default fallbacks.

    NASA Rule 4 Compliant: All methods under 60 lines
    NASA Rule 5 Compliant: Input assertions
    """

    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load configuration from YAML file or return defaults.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            config_path: Optional path to clarity_linter.yaml

        Returns:
            Configuration dictionary
        """
        # NASA Rule 5: Input validation
        assert config_path is None or isinstance(config_path, (str, Path)), \
            "config_path must be None, string, or Path"

        if config_path and YAML_AVAILABLE:
            return ClarityConfigLoader._load_from_file(config_path)

        return ClarityConfigLoader._get_default_config()

    @staticmethod
    def _load_from_file(config_path: Path) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Loaded configuration dictionary
        """
        # NASA Rule 5: Input validation
        assert config_path is not None, "config_path cannot be None"
        assert isinstance(config_path, (str, Path)), "config_path must be string or Path"

        config_path = Path(config_path)

        if not config_path.exists():
            print(f"[WARNING] Config file not found: {config_path}")
            return ClarityConfigLoader._get_default_config()

        try:
            with open(config_path, encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # NASA Rule 5: Validate loaded config
            assert isinstance(config, dict), "Loaded config must be dictionary"

            # Validate required sections
            ClarityConfigLoader._validate_config(config)

            return config

        except Exception as e:
            print(f"[ERROR] Failed to load config from {config_path}: {e}")
            return ClarityConfigLoader._get_default_config()

    @staticmethod
    def _validate_config(config: Dict[str, Any]) -> None:
        """
        Validate configuration structure.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            config: Configuration dictionary to validate

        Raises:
            AssertionError: If configuration is invalid
        """
        # NASA Rule 5: Input validation
        assert isinstance(config, dict), "config must be dictionary"

        # Check required sections
        assert 'metadata' in config, "config must have 'metadata' section"
        assert 'rules' in config, "config must have 'rules' section"

        # Validate metadata
        metadata = config['metadata']
        assert isinstance(metadata, dict), "metadata must be dictionary"
        assert 'name' in metadata, "metadata must have 'name'"
        assert 'version' in metadata, "metadata must have 'version'"

        # Validate rules
        rules = config['rules']
        assert isinstance(rules, dict), "rules must be dictionary"
        assert len(rules) > 0, "rules must not be empty"

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """
        Get default configuration when YAML loading fails.

        NASA Rule 4: Function under 60 lines

        Returns:
            Default configuration dictionary
        """
        return {
            'metadata': {
                'name': 'Clarity Linter',
                'version': '1.0.0',
                'description': 'Default configuration'
            },
            'config': {
                'severity_levels': {
                    'critical': 90,
                    'high': 70,
                    'medium': 50,
                    'low': 30,
                    'info': 0
                },
                'default_thresholds': {
                    'max_function_length': 50,
                    'max_complexity': 10,
                    'max_nesting': 4,
                    'max_parameters': 6
                }
            },
            'rules': {
                'CLARITY_THIN_HELPER': {
                    'enabled': True,
                    'severity': 'medium',
                    'threshold': 3
                },
                'CLARITY_USELESS_INDIRECTION': {
                    'enabled': True,
                    'severity': 'medium',
                    'threshold': 1
                },
                'CLARITY_CALL_CHAIN': {
                    'enabled': True,
                    'severity': 'high',
                    'threshold': 3
                },
                'CLARITY_POOR_NAMING': {
                    'enabled': True,
                    'severity': 'medium',
                    'min_length': 3
                },
                'CLARITY_COMMENT_ISSUES': {
                    'enabled': True,
                    'severity': 'low'
                }
            },
            'exclusions': {
                'directories': [
                    'node_modules',
                    'venv',
                    '.venv',
                    '__pycache__',
                    '.git',
                    'dist',
                    'build'
                ],
                'files': [
                    '*.min.js',
                    '*.bundle.js',
                    '*_pb2.py'
                ]
            }
        }

    @staticmethod
    def get_rule_config(
        config: Dict[str, Any],
        rule_id: str
    ) -> Dict[str, Any]:
        """
        Get configuration for specific rule.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            config: Full configuration dictionary
            rule_id: Rule identifier to get config for

        Returns:
            Rule-specific configuration dictionary
        """
        # NASA Rule 5: Input validation
        assert isinstance(config, dict), "config must be dictionary"
        assert isinstance(rule_id, str), "rule_id must be string"

        rules = config.get('rules', {})
        return rules.get(rule_id, {})


__all__ = ['ClarityConfigLoader']
