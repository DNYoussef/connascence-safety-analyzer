# Getting Started with Connascence Analysis

This tutorial will walk you through using the Connascence Safety Analyzer to improve your code quality.

## 🎯 What You'll Learn

- How to identify connascence violations in your code
- Using AI-powered suggestions to fix coupling issues
- Leveraging the dashboard for comprehensive analysis
- Understanding the theory behind connascence

## 📋 Prerequisites

- VS Code 1.74.0 or higher
- A project with Python, JavaScript, TypeScript, C, or C++ files
- Basic understanding of code coupling concepts

## 🚀 Step 1: First Analysis

Let's start with a simple example. Create a new file called `example.py`:

```python
# example.py - Contains several connascence violations

class UserManager:  # God Object violation
    def __init__(self):
        self.users = []
        self.config = {}
        self.logger = None
    
    def validate_user(self, name, email, age, role, department, salary):  # Position coupling
        if age < 18:  # Magic literal
            return False
        if salary < 30000:  # Another magic literal
            return False
        return True
    
    def save_user(self, user_data):
        # More responsibilities in the same class
        print("Saving user...")  # Magic literal
        
    def send_email(self, user):
        # Email logic mixed with user management
        smtp_port = 587  # Magic literal
        print(f"Sending email via port {smtp_port}")
    
    def generate_report(self):
        # Report generation mixed with user management
        timeout = 5000  # Magic literal
        print(f"Generating report with timeout {timeout}ms")
```

## 🔍 Step 2: Analyze the Code

1. **Open the file** in VS Code
2. **Look for colored highlights** - The extension automatically detects violations
3. **Check the status bar** - Shows total violation count
4. **Open the Problems panel** (`Ctrl+Shift+M`) - Lists all detected issues

You should see:
- 🔴 **Red highlights** for critical violations (God Object)
- 🟡 **Yellow highlights** for major violations (Magic literals)
- 🔵 **Blue highlights** for minor violations (Parameter coupling)

## 🤖 Step 3: Get AI-Powered Help

1. **Hover over any red highlight** to see:
   - Explanation of the violation
   - Why it matters for code quality
   - AI-generated fix suggestions with confidence scores
   - Quick action buttons

2. **Try the AI suggestions**:
   - Click "Apply Fix" for high-confidence suggestions (🟢 80%+)
   - Click "Preview Changes" for medium-confidence suggestions (🟡 60-80%)
   - Get detailed explanations for any violation type

## 📊 Step 4: Use the Dashboard

1. **Open the dashboard**: 
   - Click the status bar item, or
   - Press `Ctrl+Shift+P` → "Connascence: Show Dashboard"

2. **Explore the features**:
   - **Quality Score**: Overall code health metric
   - **Violation Charts**: Visual breakdown by type and severity
   - **AI Chat**: Ask questions about your violations

3. **Try the AI Chat**:
   ```
   User: "What are my critical violations?"
   AI: "You have 1 critical violation - a God Object in UserManager class..."
   
   User: "How do I fix magic literals?"
   AI: "Extract magic literals into named constants. For example..."
   ```

## 🔧 Step 5: Apply Refactoring

Let's fix the violations step by step:

### Fix 1: Extract Constants (Magic Literals)
```python
# Constants at the top of the file
MIN_AGE = 18
MIN_SALARY = 30000
SMTP_PORT = 587
REPORT_TIMEOUT_MS = 5000

class UserManager:
    def validate_user(self, name, email, age, role, department, salary):
        if age < MIN_AGE:  # Now using named constant
            return False
        if salary < MIN_SALARY:  # Much clearer intent
            return False
        return True
```

### Fix 2: Use Named Parameters (Position Coupling)
```python
from dataclasses import dataclass

@dataclass
class UserData:
    name: str
    email: str
    age: int
    role: str
    department: str
    salary: float

class UserManager:
    def validate_user(self, user_data: UserData):  # Single parameter object
        if user_data.age < MIN_AGE:
            return False
        if user_data.salary < MIN_SALARY:
            return False
        return True
```

### Fix 3: Split Responsibilities (God Object)
```python
class UserValidator:
    def validate(self, user_data: UserData) -> bool:
        if user_data.age < MIN_AGE:
            return False
        if user_data.salary < MIN_SALARY:
            return False
        return True

class UserRepository:
    def save(self, user_data: UserData) -> None:
        print("Saving user...")

class EmailService:
    def send_welcome_email(self, user: UserData) -> None:
        print(f"Sending email via port {SMTP_PORT}")

class ReportGenerator:
    def generate_user_report(self) -> str:
        print(f"Generating report with timeout {REPORT_TIMEOUT_MS}ms")
        return "Report content"

class UserManager:  # Now focused on coordination only
    def __init__(self):
        self.validator = UserValidator()
        self.repository = UserRepository()
        self.email_service = EmailService()
        self.report_generator = ReportGenerator()
    
    def create_user(self, user_data: UserData) -> bool:
        if self.validator.validate(user_data):
            self.repository.save(user_data)
            self.email_service.send_welcome_email(user_data)
            return True
        return False
```

## 📈 Step 6: Verify Improvements

1. **Check the violations** - Should be significantly reduced
2. **View updated dashboard** - Quality score should improve
3. **Run analysis again** - `Ctrl+Shift+P` → "Connascence: Analyze File"

Your quality score should improve from around 60% to 85%+ after these refactoring!

## 🎓 Step 7: Learn More

1. **Explore the help system**: `Ctrl+Shift+P` → "Connascence: Show Help"
2. **Read about connascence theory** in the help documentation
3. **Try the AI chat** with questions like:
   - "Explain connascence hierarchy"
   - "What are best practices for refactoring?"
   - "Show me examples of each violation type"

## 🏆 Best Practices

### Priority Order for Fixes
1. **Critical violations** (Red) - Fix immediately
2. **Major violations** (Yellow) - High impact, moderate effort
3. **Minor violations** (Blue) - Quick wins

### AI Confidence Levels
- 🟢 **80%+ confidence** - Safe to apply automatically
- 🟡 **60-80% confidence** - Review before applying
- 🔴 **<60% confidence** - Use as inspiration, implement manually

### Refactoring Strategy
1. Start with **Extract Constants** (easiest wins)
2. Move to **Parameter Objects** (moderate effort)
3. Finish with **Class Extraction** (highest impact)

## 🚀 Next Steps

- **Analyze your real projects** - Apply these techniques to your actual codebase
- **Set up team standards** - Configure the extension for your team's preferences
- **Explore advanced features** - MCP server integration, custom rules
- **Join the community** - Share your experiences and learn from others

## 💡 Pro Tips

- **Use the sidebar markdown navigator** to quickly access documentation
- **Enable real-time analysis** for immediate feedback as you type
- **Configure debouncing** if analysis feels too aggressive
- **Use the dashboard chat** when you need contextual help

Congratulations! You've completed the getting started tutorial. You now have the knowledge to identify and fix connascence violations, improving your code's maintainability and quality. 🎉