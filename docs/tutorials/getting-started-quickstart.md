# Quick Start Guide

**Get up and running with Connascence Analysis in 5 minutes**

## What is Connascence?

Connascence is a software engineering metric that measures the strength of coupling between code elements. Lower connascence leads to more maintainable, flexible, and robust code.

**This guide will help you:**
- Install and configure the analyzer
- Run your first analysis
- Understand common violations
- Apply basic fixes

---

## Installation

### Option 1: VS Code Extension (Recommended)
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Connascence Safety Analyzer"
4. Click Install

### Option 2: Command Line
```bash
# Clone the repository
git clone https://github.com/your-org/connascence-analyzer.git
cd connascence-analyzer

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -m analyzer.core --help
```

---

## First Analysis

### Using VS Code Extension

1. **Open a Python project** in VS Code
2. **Create a sample file** to analyze:

```python
# sample.py - Contains common connascence violations

class UserProcessor:  # This will become a "god object"
    def __init__(self):
        self.users = []
        self.config = {}
        self.db_connection = None
        self.email_service = None
        self.report_generator = None
    
    # Too many parameters (Position coupling - CoP)
    def create_user(self, name, email, age, department, role, salary, start_date):
        # Magic numbers (Meaning coupling - CoM)
        if age < 18:  # Magic number
            return False
        if salary < 30000:  # Another magic number
            return False
        
        user = {
            'name': name,
            'email': email,
            'age': age,
            'department': department,
            'role': role,
            'salary': salary,
            'start_date': start_date,
            'status': 'active'  # Magic string
        }
        
        self.users.append(user)
        self.send_welcome_email(user)
        self.update_payroll(user)
        self.generate_id_card(user)
        return True
    
    def send_welcome_email(self, user):
        # More magic values
        smtp_port = 587  # Magic number
        timeout = 5000   # Magic number
        # Email logic here...
    
    def update_payroll(self, user):
        # Payroll logic mixed with user creation
        pass
    
    def generate_id_card(self, user):
        # ID card generation mixed with user creation
        pass
    
    def delete_user(self, user_id):
        # More functionality in the same class
        pass
```

3. **Save the file** - The extension automatically analyzes it
4. **Check the Problems panel** (Ctrl+Shift+M) to see detected violations
5. **Look for colored highlights** in the editor:
   - 🔴 **Red** = Critical violations
   - 🟡 **Yellow** = Major violations  
   - 🔵 **Blue** = Minor violations

### Using Command Line

```bash
# Analyze the file
python -m analyzer.core --path sample.py --policy nasa_jpl_pot10 --format json

# Or analyze entire directory
python -m analyzer.core --path . --format sarif --output report.sarif
```

---

## Understanding Your Results

### Common Violation Types

#### 1. **CoM (Connascence of Meaning)**
**What:** Magic numbers/strings without clear meaning
```python
# ❌ BAD: Magic numbers
if age < 18:
    return False

# ✅ GOOD: Named constants
MIN_AGE = 18
if age < MIN_AGE:
    return False
```

#### 2. **CoP (Connascence of Position)**
**What:** Functions with too many parameters in specific order
```python
# ❌ BAD: Too many parameters
def create_user(name, email, age, dept, role, salary, start_date):
    pass

# ✅ GOOD: Parameter object
from dataclasses import dataclass

@dataclass
class UserData:
    name: str
    email: str
    age: int
    department: str
    role: str
    salary: float
    start_date: str

def create_user(user_data: UserData):
    pass
```

#### 3. **God Object**
**What:** Classes that do too many things
```python
# ❌ BAD: God object handling everything
class UserProcessor:
    def create_user(self): pass
    def send_email(self): pass
    def update_payroll(self): pass
    def generate_reports(self): pass

# ✅ GOOD: Separated responsibilities
class UserRepository:
    def create_user(self): pass

class EmailService:
    def send_welcome_email(self): pass

class PayrollService:
    def update_payroll(self): pass

class UserManager:  # Coordinates other services
    def __init__(self):
        self.user_repo = UserRepository()
        self.email_service = EmailService()
        self.payroll_service = PayrollService()
```

---

## Quick Fixes

### Using VS Code Extension

1. **Hover over a highlighted violation**
2. **Click "Quick Fix"** or press Ctrl+.
3. **Select suggested fix** from the menu
4. **Review and apply** the changes

### Manual Fixes

#### Fix 1: Extract Magic Numbers
```python
# Before
if age < 18:
    return False
if salary < 30000:
    return False

# After  
MIN_AGE = 18
MIN_SALARY = 30000

if age < MIN_AGE:
    return False
if salary < MIN_SALARY:
    return False
```

#### Fix 2: Use Parameter Objects
```python
# Before
def create_user(self, name, email, age, department, role, salary, start_date):
    # Implementation

# After
from dataclasses import dataclass

@dataclass
class UserData:
    name: str
    email: str
    age: int
    department: str
    role: str
    salary: float
    start_date: str

def create_user(self, user_data: UserData):
    # Implementation - now type-safe and easier to extend
```

#### Fix 3: Break Down God Objects
```python
# Before: Everything in one class
class UserProcessor:
    def create_user(self): pass
    def send_email(self): pass
    def update_payroll(self): pass

# After: Separate concerns
class UserValidator:
    def validate(self, user_data: UserData) -> bool:
        return user_data.age >= MIN_AGE and user_data.salary >= MIN_SALARY

class UserRepository:
    def save(self, user_data: UserData) -> None:
        # Database operations

class EmailService:
    def send_welcome_email(self, user_data: UserData) -> None:
        # Email operations

class UserService:  # Orchestrates other services
    def __init__(self):
        self.validator = UserValidator()
        self.repository = UserRepository()
        self.email_service = EmailService()
    
    def create_user(self, user_data: UserData) -> bool:
        if not self.validator.validate(user_data):
            return False
        
        self.repository.save(user_data)
        self.email_service.send_welcome_email(user_data)
        return True
```

---

## Interpreting Quality Scores

### Quality Score Ranges
- **90-100**: Excellent - Very low coupling
- **80-89**: Good - Minor coupling issues
- **70-79**: Acceptable - Some refactoring recommended
- **60-69**: Poor - Significant coupling problems
- **Below 60**: Critical - Immediate attention required

### Prioritizing Fixes
1. **Critical violations** (Red) - Fix immediately
2. **Major violations** (Yellow) - High impact fixes
3. **Minor violations** (Blue) - Quick wins

---

## Using the Dashboard (VS Code)

1. **Open dashboard**: Click the broken chain icon in the status bar
2. **View metrics**:
   - Overall quality score
   - Violation counts by severity
   - Files needing attention
3. **Explore violations**: Click on items to navigate to code
4. **Track progress**: Quality score updates as you fix violations

---

## Configuration

### Basic Configuration (VS Code)
1. **Open Settings** (Ctrl+,)
2. **Search for "connascence"**
3. **Key settings to adjust**:
   - **Safety Profile**: Choose analysis strictness
   - **Real-time Analysis**: Enable/disable live analysis
   - **Max Diagnostics**: Control number of violations shown

### Configuration File
Create `.connascence.json` in your project root:

```json
{
  "safetyProfile": "nasa_jpl_pot10",
  "threshold": 0.8,
  "strictMode": false,
  "excludePatterns": [
    "**/tests/**",
    "**/node_modules/**"
  ],
  "customRules": [
    {
      "name": "no-legacy-patterns",
      "pattern": "legacy_\\w+",
      "severity": "warning",
      "message": "Legacy pattern detected - consider refactoring"
    }
  ]
}
```

---

## Best Practices

### Start Small
1. **Analyze one file** first to understand the tool
2. **Fix high-impact violations** before moving to the next file
3. **Gradually expand** to larger codebases

### Refactoring Strategy
1. **Extract constants** (easiest wins)
2. **Simplify parameter lists** (moderate effort)
3. **Break down large classes** (highest impact)

### Team Adoption
1. **Set team standards** for acceptable quality scores
2. **Use pre-commit hooks** to prevent new violations
3. **Track quality trends** over time
4. **Share knowledge** about connascence principles

---

## Next Steps

### Learn More
- **Read the theory**: Understanding connascence principles
- **Explore advanced features**: NASA compliance, MECE analysis
- **Set up CI/CD integration**: Automated quality checks
- **Join the community**: Share experiences and get help

### Advanced Usage
- **Custom rules**: Define project-specific patterns
- **Multiple output formats**: JSON, SARIF, Markdown reports
- **Integration**: GitHub Actions, pre-commit hooks
- **Team dashboards**: Track organization-wide quality

### Troubleshooting
- **Extension not working?** Check Python is installed and accessible
- **False positives?** Adjust threshold settings or exclude patterns  
- **Performance issues?** Disable real-time analysis for large files
- **Need help?** Check the documentation or file an issue

---

## Success Metrics

After using the analyzer for a week, you should see:
- **Improved code readability** - Less magic numbers and unclear parameters
- **Easier testing** - Smaller, focused classes are easier to test
- **Faster development** - Well-structured code is easier to modify
- **Fewer bugs** - Lower coupling reduces unexpected side effects

**Congratulations!** You're now equipped to improve your codebase quality using connascence analysis. Start small, fix incrementally, and watch your code become more maintainable over time. 🎉