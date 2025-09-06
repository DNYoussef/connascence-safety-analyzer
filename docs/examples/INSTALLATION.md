# One-Command Installation Guide

## Quick Start (30 seconds)

```bash
# Install from current directory
pip install -e .

# Verify installation works
python -m analyzer.core --help

# Run on demo file (copy/paste ready)
curl -O https://raw.githubusercontent.com/DNYoussef/connascence-safety-analyzer/main/docs/examples/quick_start_demo.py
python -m analyzer.core --path quick_start_demo.py --policy strict-core
```

## Alternative Installation Methods

### Method 1: Direct from Repository
```bash
git clone https://github.com/DNYoussef/connascence-safety-analyzer.git
cd connascence-safety-analyzer
pip install -e .
python -m analyzer.core --path docs/examples/bad_example.py --policy nasa_jpl_pot10
```

### Method 2: PyPI (when available)
```bash
pip install connascence-analyzer
python -m analyzer.core --help
```

### Method 3: Docker (Enterprise)
```bash
docker run -v $(pwd):/workspace connascence-analyzer:latest --path /workspace --format json
```

## Verify Installation

Run this command to confirm everything works:

```bash
python -c "
import sys
sys.path.insert(0, '.')
from analyzer.core import main
print('✅ Connascence Analyzer installed successfully!')
print('📊 Ready to analyze your codebase')
"
```

If you see the success messages, you're ready to analyze code!

## Common Issues & Solutions

### Issue: "No module named 'analyzer'"
**Solution:** Make sure you're running from the repository root directory:
```bash
cd connascence-safety-analyzer  # Make sure you're in the right directory
python -m analyzer.core --help  # Should work now
```

### Issue: Missing dependencies
**Solution:** Install requirements:
```bash
pip install -r requirements.txt
```

### Issue: Python version compatibility  
**Solution:** Use Python 3.8+:
```bash
python --version  # Should show 3.8 or higher
```

## Quick Demo

Copy this into a file called `demo.py` and run the analyzer:

```python
class UserManager:
    def create_user(self, name, age, email, status):
        if age > 150 or status not in [1, 2, 3]:  # Magic numbers
            return False
        return {"id": 1, "name": name}  # Magic ID

def process_users(users, sort, filter, format):  # Parameter coupling
    return users
```

Then run:
```bash
python -m analyzer.core --path demo.py --policy strict-core
```

You should see violations for:
- Magic numbers (150, [1,2,3])  
- Parameter position coupling
- God object pattern

Total setup time: **Under 1 minute**