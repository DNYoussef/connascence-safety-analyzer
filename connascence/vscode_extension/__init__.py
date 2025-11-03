"""VS Code extension shims for integration tests."""

from .src.services.configurationService import ConfigurationService
from .src.services.connascenceService import ConnascenceService

__all__ = ["ConfigurationService", "ConnascenceService"]
