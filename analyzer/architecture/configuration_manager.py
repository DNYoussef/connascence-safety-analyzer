# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Configuration Manager - Configuration Handling and Validation
=============================================================

Extracted from UnifiedConnascenceAnalyzer's god object.
NASA Rule 4 Compliant: Functions under 60 lines.
Handles config loading, validation, and component initialization coordination.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages analyzer configuration with validation and component coordination."""

    def __init__(self):
        """Initialize configuration manager with defaults."""
        self.config = self._get_default_config()
        self.config_loaded_at = None
        self.validation_errors = []

    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load analyzer configuration with validation.
        NASA Rule 4 Compliant: Under 60 lines.
        """
        # NASA Rule 5: Input validation assertions
        if config_path is not None:
            assert isinstance(config_path, str), "config_path must be string or None"

        config = self._get_default_config()

        if config_path:
            try:
                loaded_config = self._load_config_file(config_path)
                validated_config = self._validate_and_merge_config(config, loaded_config)
                config = validated_config
                self.config_loaded_at = self._get_iso_timestamp()
                logger.info(f"Configuration loaded from {config_path}")
                
            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {e}")
                self.validation_errors.append(f"Config load error: {e}")

        self.config = config
        return config

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration structure and values. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert config is not None, "config cannot be None"
        assert isinstance(config, dict), "config must be dictionary"
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }

        # Validate required fields
        required_fields = ["enable_nasa_checks", "default_policy_preset"]
        validation_result = self._validate_required_fields(config, required_fields, validation_result)

        # Validate policy preset
        validation_result = self._validate_policy_preset(config, validation_result)

        # Validate component flags
        validation_result = self._validate_component_flags(config, validation_result)

        # Validate numerical limits
        validation_result = self._validate_numerical_limits(config, validation_result)

        return validation_result

    def get_component_configuration(self, component_name: str) -> Dict[str, Any]:
        """Get configuration for specific component. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert component_name is not None, "component_name cannot be None"
        assert isinstance(component_name, str), "component_name must be string"

        component_configs = {
            "ast_analyzer": self._get_ast_analyzer_config(),
            "mece_analyzer": self._get_mece_analyzer_config(),
            "nasa_integration": self._get_nasa_integration_config(),
            "smart_engine": self._get_smart_engine_config(),
            "failure_detector": self._get_failure_detector_config(),
        }

        return component_configs.get(component_name, {})

    def initialize_component_settings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize all component settings. NASA Rule 4 compliant."""
        component_settings = {}

        # Initialize each component with its specific configuration
        components = ["ast_analyzer", "mece_analyzer", "nasa_integration", "smart_engine", "failure_detector"]
        
        for component in components:
            try:
                component_settings[component] = self.get_component_configuration(component)
                logger.debug(f"Initialized settings for {component}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize {component} settings: {e}")
                component_settings[component] = {}

        return component_settings

    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file. NASA Rule 4 compliant."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        if not config_file.is_file():
            raise ValueError(f"Configuration path is not a file: {config_path}")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")

    def _validate_and_merge_config(self, default_config: Dict, loaded_config: Dict) -> Dict[str, Any]:
        """Validate and merge loaded config with defaults. NASA Rule 4 compliant."""
        merged_config = default_config.copy()
        
        # Validate loaded config structure
        validation_result = self.validate_configuration(loaded_config)
        
        if not validation_result["is_valid"]:
            self.validation_errors.extend(validation_result["errors"])
            logger.warning("Configuration validation failed, using defaults with valid overrides")
        
        # Merge valid configuration keys
        valid_keys = set(default_config.keys())
        for key, value in loaded_config.items():
            if key in valid_keys:
                merged_config[key] = value
            else:
                logger.warning(f"Unknown configuration key ignored: {key}")

        return merged_config

    def _validate_required_fields(self, config: Dict, required_fields: List[str], validation_result: Dict) -> Dict:
        """Validate required configuration fields. NASA Rule 4 compliant."""
        for field in required_fields:
            if field not in config:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["is_valid"] = False
        
        return validation_result

    def _validate_policy_preset(self, config: Dict, validation_result: Dict) -> Dict:
        """Validate policy preset value. NASA Rule 4 compliant."""
        valid_presets = ["service-defaults", "strict-core", "experimental", "balanced", "lenient"]
        preset = config.get("default_policy_preset")
        
        if preset not in valid_presets:
            validation_result["errors"].append(f"Invalid policy preset: {preset}. Valid: {valid_presets}")
            validation_result["is_valid"] = False
        
        return validation_result

    def _validate_component_flags(self, config: Dict, validation_result: Dict) -> Dict:
        """Validate component enable/disable flags. NASA Rule 4 compliant."""
        boolean_flags = [
            "enable_nasa_checks", "enable_mece_analysis", "enable_smart_integration",
            "enable_failure_detection", "enable_caching", "parallel_processing"
        ]
        
        for flag in boolean_flags:
            value = config.get(flag)
            if value is not None and not isinstance(value, bool):
                validation_result["warnings"].append(f"Non-boolean value for {flag}: {value}")
        
        return validation_result

    def _validate_numerical_limits(self, config: Dict, validation_result: Dict) -> Dict:
        """Validate numerical configuration limits. NASA Rule 4 compliant."""
        numerical_limits = {
            "max_workers": (1, 16),
            "analysis_timeout_seconds": (10, 3600),
            "cache_size_mb": (10, 1000),
            "max_violation_count": (100, 10000)
        }
        
        for key, (min_val, max_val) in numerical_limits.items():
            value = config.get(key)
            if value is not None:
                if not isinstance(value, (int, float)) or value < min_val or value > max_val:
                    validation_result["warnings"].append(
                        f"Invalid {key}: {value}. Should be between {min_val} and {max_val}"
                    )
        
        return validation_result

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration. NASA Rule 4 compliant."""
        return {
            "enable_nasa_checks": True,
            "enable_mece_analysis": True,
            "enable_smart_integration": True,
            "enable_failure_detection": False,
            "enable_caching": True,
            "default_policy_preset": "service-defaults",
            "parallel_processing": True,
            "max_workers": 4,
            "analysis_timeout_seconds": 300,
            "cache_size_mb": 100,
            "max_violation_count": 1000,
            "log_level": "INFO",
            "output_format": "json"
        }

    def _get_ast_analyzer_config(self) -> Dict[str, Any]:
        """Get AST analyzer specific configuration. NASA Rule 4 compliant."""
        return {
            "enabled": self.config.get("enable_nasa_checks", True),
            "max_depth": 10,
            "analyze_imports": True,
            "skip_test_files": True,
        }

    def _get_mece_analyzer_config(self) -> Dict[str, Any]:
        """Get MECE analyzer specific configuration. NASA Rule 4 compliant."""
        return {
            "enabled": self.config.get("enable_mece_analysis", True),
            "similarity_threshold": 0.8,
            "min_cluster_size": 2,
            "comprehensive_mode": True,
        }

    def _get_nasa_integration_config(self) -> Dict[str, Any]:
        """Get NASA integration specific configuration. NASA Rule 4 compliant."""
        return {
            "enabled": self.config.get("enable_nasa_checks", True),
            "strict_mode": False,
            "rule_weights": {
                "Rule1": 10, "Rule2": 9, "Rule3": 8, "Rule4": 7, "Rule5": 6
            },
        }

    def _get_smart_engine_config(self) -> Dict[str, Any]:
        """Get smart integration engine configuration. NASA Rule 4 compliant."""
        return {
            "enabled": self.config.get("enable_smart_integration", True),
            "correlation_analysis": True,
            "intelligent_recommendations": True,
            "cross_phase_analysis": True,
        }

    def _get_failure_detector_config(self) -> Dict[str, Any]:
        """Get failure detector configuration. NASA Rule 4 compliant."""
        return {
            "enabled": self.config.get("enable_failure_detection", False),
            "prediction_threshold": 0.7,
            "monitoring_enabled": True,
        }

    def update_config(self, key: str, value: Any) -> bool:
        """Update single configuration value. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation
        assert key is not None, "key cannot be None"
        assert isinstance(key, str), "key must be string"

        if key not in self.config:
            logger.warning(f"Attempting to update unknown config key: {key}")
            return False

        try:
            # Validate the update
            temp_config = self.config.copy()
            temp_config[key] = value
            validation_result = self.validate_configuration(temp_config)
            
            if validation_result["is_valid"]:
                self.config[key] = value
                logger.info(f"Configuration updated: {key} = {value}")
                return True
            else:
                logger.error(f"Invalid configuration update for {key}: {validation_result['errors']}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update configuration {key}: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()

    def get_validation_errors(self) -> List[str]:
        """Get configuration validation errors."""
        return self.validation_errors.copy()

    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format. NASA Rule 4 compliant."""
        return datetime.now().isoformat()