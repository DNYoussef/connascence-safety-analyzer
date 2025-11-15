"""CLI module entry point for python -m cli.connascence."""

import os
import sys
import warnings

# Suppress import warnings from other modules
warnings.filterwarnings('ignore')

# Suppress stdout during imports to prevent warning messages
class SuppressOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

# Import with suppressed output
with SuppressOutput():
    from cli.connascence import main

if __name__ == "__main__":
    sys.exit(main())
