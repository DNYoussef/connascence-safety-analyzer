"""CLI package alias for backward compatibility.

This module provides backward-compatible imports for tests
expecting 'cli.connascence' while actual implementation lives
in 'interfaces.cli.connascence'.
"""

import warnings

# Suppress all warnings when importing CLI components
warnings.filterwarnings('ignore')

# Import from the actual location in interfaces.cli
from interfaces.cli.connascence import ConnascenceCLI
from interfaces.cli.main_python import main

try:
    # Import additional utilities if available
    from interfaces.cli.simple_cli import main as simple_main
except ImportError:
    simple_main = None

# Export for backward compatibility
__all__ = ['ConnascenceCLI', 'main']
if simple_main is not None:
    __all__.append('simple_main')
