"""CLI compatibility module for E2E tests."""

# Import the actual CLI class from interfaces
from interfaces.cli.connascence import ConnascenceCLI
from interfaces.cli.main_python import main

# Export for backward compatibility
__all__ = ["ConnascenceCLI", "main"]
