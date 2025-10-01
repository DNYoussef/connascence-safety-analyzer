"""CLI module with full backward compatibility."""

# Import from the actual location
from interfaces.cli import *
from interfaces.cli.connascence import ConnascenceCLI
from interfaces.cli.main_python import main
from interfaces.cli.simple_cli import main as simple_main

# Re-export for E2E tests (import from our local connascence.py)
try:
    from .connascence import ConnascenceCLI as CLI
except ImportError:
    CLI = ConnascenceCLI

# Export for backward compatibility
__all__ = ["CLI", "ConnascenceCLI", "main", "simple_main"]
