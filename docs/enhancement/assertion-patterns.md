# NASA POT10 Assertion Patterns & Best Practices for Python

## Executive Summary

This document provides comprehensive research on NASA Power of 10 (POT10) Rule 5 assertion patterns and implementation strategies for Python codebases. Current assertion density: **0%**. Target: **2%+ (minimum 2 assertions per function)**.

**Key Finding**: NASA POT10 Rule 5 requires assertion density averaging **minimally two assertions per function** for safety-critical code. However, Python's `assert` statement has critical limitations for production code that require alternative approaches.

---

## Table of Contents

1. [NASA POT10 Rule 5 Requirements](#nasa-pot10-rule-5-requirements)
2. [Critical Python Assertion Limitations](#critical-python-assertion-limitations)
3. [Assertion Pattern Library](#assertion-pattern-library)
4. [Production-Safe Alternatives](#production-safe-alternatives)
5. [Automated Injection Strategies](#automated-injection-strategies)
6. [Implementation Templates](#implementation-templates)
7. [Real-World Examples](#real-world-examples)
8. [Tool Recommendations](#tool-recommendations)

---

## NASA POT10 Rule 5 Requirements

### Official Requirements

**Rule 5**: "The code's assertion density should average to minimally two assertions per function."

**Key Characteristics**:
- **Density**: Minimum 2 assertions per function average
- **Purpose**: Check anomalous conditions that should never occur in real-life executions
- **Side-Effect Free**: Assertions must have no side effects
- **Boolean Tests**: Must be defined as Boolean tests
- **Recovery Actions**: Explicit recovery action required when assertion fails
- **Meaningful Only**: Cannot use trivial assertions like `assert True`

### Rationale

Statistics from industrial coding efforts:
- Unit tests find **1 defect per 10-100 lines of code**
- **Assertion density directly correlates** with defect interception rates
- Part of **strong defensive coding strategy**
- Critical for **mission-critical software** where post-deployment debugging is impossible

### Verification Categories

Developers should use assertions to verify:
1. **Preconditions**: Function input validity
2. **Postconditions**: Function output validity
3. **Parameter values**: Input validation
4. **Return values**: Output validation
5. **Loop invariants**: State consistency during iteration

---

## Critical Python Assertion Limitations

### CRITICAL WARNING: assert Statements in Production

**Python's `assert` statement is UNSAFE for production validation** due to optimization flags:

```python
# ❌ DANGEROUS: This validation disappears with -O flag
def process_payment(amount):
    assert amount > 0, "Amount must be positive"
    # Process payment...
```

```bash
# All assertions are REMOVED when running with optimization
python -O script.py   # -O flag disables all assertions
python -OO script.py  # -OO flag disables assertions and docstrings
```

### Why This Matters

1. **Security Risk**: Validation bypassed in optimized code
2. **Unpredictable Behavior**: Code behaves differently in dev vs. production
3. **Silent Failures**: No warning that validations are disabled
4. **Compliance Violation**: Cannot meet NASA POT10 requirements with disabled checks

### Official Python Guidance

From Python documentation and community consensus:
- **Assert is for debugging aids**, not runtime error handling
- **Never use assert for data validation**
- **Never rely on assert for critical checks in production**
- **Use explicit error handling (exceptions) instead**

---

## Assertion Pattern Library

### Pattern 1: Precondition Validation

**Purpose**: Validate function inputs before execution

```python
# ❌ Unsafe for production (assert disabled with -O)
def normalize_rectangle(rect):
    assert len(rect) == 4, 'Rectangles must contain 4 coordinates'
    x0, y0, x1, y1 = rect
    assert x0 < x1, 'Invalid X coordinates'
    assert y0 < y1, 'Invalid Y coordinates'
    # ... process

# ✅ Production-safe alternative
def normalize_rectangle(rect):
    if len(rect) != 4:
        raise ValueError('Rectangles must contain 4 coordinates')
    x0, y0, x1, y1 = rect
    if x0 >= x1:
        raise ValueError(f'Invalid X coordinates: x0={x0} >= x1={x1}')
    if y0 >= y1:
        raise ValueError(f'Invalid Y coordinates: y0={y0} >= y1={y1}')
    # ... process
```

### Pattern 2: Postcondition Validation

**Purpose**: Validate function outputs before return

```python
# ❌ Unsafe for production
def calculate_bounds(data):
    result = compute_bounds(data)
    upper_x = result['upper_x']
    assert 0 < upper_x <= 1.0, f'Invalid upper_x: {upper_x}'
    return result

# ✅ Production-safe alternative
def calculate_bounds(data):
    result = compute_bounds(data)
    upper_x = result['upper_x']
    if not (0 < upper_x <= 1.0):
        raise RuntimeError(f'Postcondition failed: Invalid upper_x={upper_x}')
    return result
```

### Pattern 3: Loop Invariant Validation

**Purpose**: Ensure conditions remain true during iteration

```python
# ❌ Unsafe for production
def running_sum(values):
    result = [values[0]]
    for v in values[1:]:
        assert result[-1] >= 0, f'Invariant violated: {result[-1]} < 0'
        result.append(result[-1] + v)
    return result

# ✅ Production-safe alternative
def running_sum(values):
    result = [values[0]]
    for v in values[1:]:
        if result[-1] < 0:
            raise RuntimeError(f'Loop invariant violated: {result[-1]} < 0')
        result.append(result[-1] + v)
    return result
```

### Pattern 4: Type Validation

**Purpose**: Runtime type checking for critical parameters

```python
# ❌ Unsafe for production
def divide(x, y):
    assert isinstance(x, (int, float)), f'x must be numeric, got {type(x)}'
    assert isinstance(y, (int, float)), f'y must be numeric, got {type(y)}'
    assert y != 0, 'Division by zero'
    return x / y

# ✅ Production-safe alternative
def divide(x, y):
    if not isinstance(x, (int, float)):
        raise TypeError(f'x must be numeric, got {type(x).__name__}')
    if not isinstance(y, (int, float)):
        raise TypeError(f'y must be numeric, got {type(y).__name__}')
    if y == 0:
        raise ValueError('Division by zero')
    return x / y
```

### Pattern 5: Edge Case Validation

**Purpose**: Check boundary conditions and edge cases

```python
# ❌ Unsafe for production
def get_element(lst, index):
    assert 0 <= index < len(lst), f'Index {index} out of bounds'
    assert len(lst) > 0, 'List must not be empty'
    return lst[index]

# ✅ Production-safe alternative
def get_element(lst, index):
    if len(lst) == 0:
        raise ValueError('List must not be empty')
    if not (0 <= index < len(lst)):
        raise IndexError(f'Index {index} out of bounds [0, {len(lst)})')
    return lst[index]
```

---

## Production-Safe Alternatives

### Approach 1: Contract Programming Libraries

**icontract** - Comprehensive contract programming with inheritance support

```python
from icontract import pre, post, invariant, ViolationError

@pre(lambda x: x > 0, "x must be positive")
@pre(lambda y: y != 0, "y must not be zero")
@post(lambda result: result > 0, "result must be positive")
def divide_positive(x: float, y: float) -> float:
    """Divide two positive numbers."""
    return x / y

# Usage
try:
    result = divide_positive(10, -2)  # Raises ViolationError
except ViolationError as e:
    print(f"Contract violated: {e}")
```

**Benefits**:
- ✅ Cannot be disabled with -O flag
- ✅ Detailed violation messages
- ✅ Inheritance support (Liskov Substitution Principle)
- ✅ Clear separation of contracts from logic

### Approach 2: Runtime Type Validation

**Pydantic** - Data validation with automatic coercion

```python
from pydantic import BaseModel, validator, Field

class PaymentRequest(BaseModel):
    amount: float = Field(gt=0, description="Payment amount")
    currency: str = Field(min_length=3, max_length=3)

    @validator('amount')
    def validate_amount(cls, v):
        if v > 1000000:
            raise ValueError('Amount exceeds maximum')
        return v

# Usage
payment = PaymentRequest(amount=100.50, currency="USD")  # ✅ Valid
# PaymentRequest(amount=-10, currency="USD")  # ❌ Raises ValidationError
```

**Beartype** - Zero-overhead runtime type checking

```python
from beartype import beartype
from typing import List

@beartype
def process_data(items: List[int]) -> int:
    """Process list of integers."""
    if len(items) == 0:
        raise ValueError("Items list cannot be empty")
    return sum(items) // len(items)

# Type checking happens at runtime with O(1) complexity
result = process_data([1, 2, 3])  # ✅ Valid
# process_data(["a", "b"])  # ❌ Raises BeartypeCallHintParamViolation
```

**Typeguard** - Comprehensive runtime type enforcement

```python
from typeguard import typechecked
from typing import List, Optional

@typechecked
def find_max(numbers: List[float]) -> Optional[float]:
    """Find maximum value in list."""
    if not numbers:
        return None
    if not all(isinstance(n, (int, float)) for n in numbers):
        raise TypeError("All elements must be numeric")
    return max(numbers)
```

### Approach 3: Custom Validation Decorators

**Production-safe assertion decorator**:

```python
from functools import wraps
from typing import Callable, Any

class ProductionAssertionError(RuntimeError):
    """Custom exception for production assertions."""
    pass

def requires(condition: Callable[..., bool], message: str = "Precondition failed"):
    """Precondition decorator that cannot be disabled."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not condition(*args, **kwargs):
                raise ProductionAssertionError(f"{func.__name__}: {message}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def ensures(condition: Callable[..., bool], message: str = "Postcondition failed"):
    """Postcondition decorator that cannot be disabled."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if not condition(result):
                raise ProductionAssertionError(f"{func.__name__}: {message}")
            return result
        return wrapper
    return decorator

# Usage
@requires(lambda x, y: y != 0, "Divisor cannot be zero")
@ensures(lambda result: not math.isnan(result), "Result cannot be NaN")
def safe_divide(x: float, y: float) -> float:
    return x / y
```

---

## Automated Injection Strategies

### Strategy 1: AST-Based Assertion Injection

**Automated validation injection using Python AST**:

```python
import ast
import inspect
from typing import List, Set

class AssertionInjector(ast.NodeTransformer):
    """Inject validation checks into function definitions."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Add precondition checks to function entry."""
        preconditions = []

        # Add parameter type checks
        for arg in node.args.args:
            if arg.annotation:
                type_check = self._create_type_check(arg.arg, arg.annotation)
                preconditions.append(type_check)

        # Add null checks for required parameters
        for arg in node.args.args:
            null_check = self._create_null_check(arg.arg)
            preconditions.append(null_check)

        # Inject at function start
        node.body = preconditions + node.body
        return node

    def _create_type_check(self, param: str, annotation: ast.expr) -> ast.If:
        """Create runtime type validation."""
        return ast.If(
            test=ast.UnaryOp(
                op=ast.Not(),
                operand=ast.Call(
                    func=ast.Name(id='isinstance', ctx=ast.Load()),
                    args=[
                        ast.Name(id=param, ctx=ast.Load()),
                        annotation
                    ],
                    keywords=[]
                )
            ),
            body=[
                ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id='TypeError', ctx=ast.Load()),
                        args=[ast.Constant(value=f'{param} type mismatch')],
                        keywords=[]
                    )
                )
            ],
            orelse=[]
        )

    def _create_null_check(self, param: str) -> ast.If:
        """Create null/None validation."""
        return ast.If(
            test=ast.Compare(
                left=ast.Name(id=param, ctx=ast.Load()),
                ops=[ast.Is()],
                comparators=[ast.Constant(value=None)]
            ),
            body=[
                ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id='ValueError', ctx=ast.Load()),
                        args=[ast.Constant(value=f'{param} cannot be None')],
                        keywords=[]
                    )
                )
            ],
            orelse=[]
        )

# Usage
def inject_assertions(source_code: str) -> str:
    """Automatically inject assertions into Python code."""
    tree = ast.parse(source_code)
    injector = AssertionInjector()
    new_tree = injector.visit(tree)
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree)
```

### Strategy 2: Decorator-Based Auto-Validation

**Automatic validation from type hints**:

```python
from typing import get_type_hints, get_origin, get_args
import functools
import inspect

def auto_validate(func):
    """Automatically validate parameters and return values from type hints."""
    hints = get_type_hints(func)
    sig = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Bind arguments
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        # Validate parameters
        for param_name, param_value in bound.arguments.items():
            if param_name in hints:
                expected_type = hints[param_name]
                if not _check_type(param_value, expected_type):
                    raise TypeError(
                        f"{func.__name__}: {param_name} must be {expected_type}, "
                        f"got {type(param_value).__name__}"
                    )

        # Execute function
        result = func(*args, **kwargs)

        # Validate return value
        if 'return' in hints:
            expected_return = hints['return']
            if not _check_type(result, expected_return):
                raise TypeError(
                    f"{func.__name__}: return value must be {expected_return}, "
                    f"got {type(result).__name__}"
                )

        return result

    return wrapper

def _check_type(value, expected_type):
    """Check if value matches expected type (simplified)."""
    origin = get_origin(expected_type)
    if origin is None:
        return isinstance(value, expected_type)
    # Handle generics (List, Dict, etc.)
    if origin in (list, List):
        if not isinstance(value, list):
            return False
        args = get_args(expected_type)
        if args:
            return all(_check_type(item, args[0]) for item in value)
    return True

# Usage
@auto_validate
def process_items(items: List[int], threshold: float) -> float:
    """Process items above threshold."""
    filtered = [x for x in items if x > threshold]
    return sum(filtered) / len(filtered) if filtered else 0.0
```

### Strategy 3: Static Analysis Integration

**Automated assertion suggestion using static analysis**:

```python
import ast
from typing import List, Tuple, Dict

class AssertionSuggester(ast.NodeVisitor):
    """Suggest assertion locations using static analysis."""

    def __init__(self):
        self.suggestions: List[Dict] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Analyze function for assertion opportunities."""
        func_name = node.name

        # Check for missing preconditions
        if not self._has_parameter_validation(node):
            self.suggestions.append({
                'type': 'precondition',
                'location': f'{func_name}:entry',
                'reason': 'No parameter validation found',
                'suggestion': 'Add type and null checks for parameters'
            })

        # Check for division operations without zero checks
        for child in ast.walk(node):
            if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Div):
                if not self._has_zero_check(node, child):
                    self.suggestions.append({
                        'type': 'precondition',
                        'location': f'{func_name}:line_{child.lineno}',
                        'reason': 'Division without zero check',
                        'suggestion': 'Add divisor != 0 validation'
                    })

        # Check for list/array access without bounds check
        for child in ast.walk(node):
            if isinstance(child, ast.Subscript):
                if not self._has_bounds_check(node, child):
                    self.suggestions.append({
                        'type': 'precondition',
                        'location': f'{func_name}:line_{child.lineno}',
                        'reason': 'Array access without bounds check',
                        'suggestion': 'Add index bounds validation'
                    })

        self.generic_visit(node)

    def _has_parameter_validation(self, node: ast.FunctionDef) -> bool:
        """Check if function validates parameters."""
        # Look for isinstance or type checks in first few statements
        for stmt in node.body[:3]:
            if isinstance(stmt, ast.If):
                if self._is_type_check(stmt.test):
                    return True
        return False

    def _has_zero_check(self, func_node: ast.FunctionDef, div_node: ast.BinOp) -> bool:
        """Check if divisor is validated against zero."""
        # Simplified check - look for comparisons with 0
        for stmt in ast.walk(func_node):
            if isinstance(stmt, ast.Compare):
                if any(isinstance(c, ast.Constant) and c.value == 0
                       for c in stmt.comparators):
                    return True
        return False

    def _has_bounds_check(self, func_node: ast.FunctionDef, subscript: ast.Subscript) -> bool:
        """Check if array access has bounds validation."""
        # Look for len() comparisons or index checks
        for stmt in ast.walk(func_node):
            if isinstance(stmt, ast.Compare):
                if self._mentions_len(stmt):
                    return True
        return False

    def _is_type_check(self, node: ast.expr) -> bool:
        """Check if expression is a type check."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'isinstance':
                return True
        return False

    def _mentions_len(self, node: ast.Compare) -> bool:
        """Check if comparison involves len()."""
        if isinstance(node.left, ast.Call):
            if isinstance(node.left.func, ast.Name) and node.left.func.id == 'len':
                return True
        return False

# Usage
def analyze_code_for_assertions(source_code: str) -> List[Dict]:
    """Analyze code and suggest assertion locations."""
    tree = ast.parse(source_code)
    suggester = AssertionSuggester()
    suggester.visit(tree)
    return suggester.suggestions
```

---

## Implementation Templates

### Template 1: Function Precondition Pattern

```python
def function_with_preconditions(param1: type1, param2: type2) -> return_type:
    """
    Function description.

    Preconditions:
        - param1 must satisfy condition1
        - param2 must satisfy condition2
    """
    # PRECONDITION 1: Parameter type validation
    if not isinstance(param1, type1):
        raise TypeError(f"param1 must be {type1.__name__}")

    # PRECONDITION 2: Parameter value validation
    if not condition_on_param1(param1):
        raise ValueError(f"param1 must satisfy: {condition_description}")

    # PRECONDITION 3: Parameter relationship validation
    if not relationship_between_params(param1, param2):
        raise ValueError(f"Invalid parameter relationship: {description}")

    # Function implementation
    result = implementation(param1, param2)

    return result
```

### Template 2: Function Postcondition Pattern

```python
def function_with_postconditions(params) -> return_type:
    """
    Function description.

    Postconditions:
        - Return value must satisfy condition1
        - System state must satisfy condition2
    """
    # Function implementation
    result = implementation(params)

    # POSTCONDITION 1: Return value type validation
    if not isinstance(result, return_type):
        raise RuntimeError(f"Postcondition failed: Invalid return type")

    # POSTCONDITION 2: Return value range validation
    if not valid_range(result):
        raise RuntimeError(f"Postcondition failed: Result {result} out of range")

    # POSTCONDITION 3: State consistency validation
    if not state_is_consistent():
        raise RuntimeError(f"Postcondition failed: Inconsistent state")

    return result
```

### Template 3: Loop Invariant Pattern

```python
def function_with_loop_invariants(items: List[type]) -> result_type:
    """
    Function description.

    Loop invariants:
        - Invariant condition that holds on every iteration
    """
    # Preconditions
    if not items:
        raise ValueError("Items list cannot be empty")

    result = initial_value

    for i, item in enumerate(items):
        # INVARIANT 1: Result consistency check
        if not result_is_valid(result):
            raise RuntimeError(f"Loop invariant violated at iteration {i}")

        # INVARIANT 2: State consistency check
        if not state_is_consistent():
            raise RuntimeError(f"State invariant violated at iteration {i}")

        # Loop body
        result = process(result, item)

        # INVARIANT 3: Progress validation
        if not progress_made(result, previous_result):
            raise RuntimeError(f"Progress invariant violated at iteration {i}")

    return result
```

### Template 4: Class Invariant Pattern

```python
class ClassWithInvariants:
    """
    Class description.

    Class invariants:
        - Invariant condition that must always hold
    """

    def __init__(self, param1, param2):
        # Initialize state
        self._state1 = param1
        self._state2 = param2

        # Validate invariants after initialization
        self._check_invariants()

    def _check_invariants(self):
        """Validate all class invariants."""
        # INVARIANT 1: State consistency
        if not self._state_is_consistent():
            raise RuntimeError("Class invariant violated: Inconsistent state")

        # INVARIANT 2: Value constraints
        if not self._values_in_range():
            raise RuntimeError("Class invariant violated: Values out of range")

        # INVARIANT 3: Relationship constraints
        if not self._relationships_valid():
            raise RuntimeError("Class invariant violated: Invalid relationships")

    def modify_state(self, new_value):
        """Modify state while maintaining invariants."""
        # Preconditions
        if not self._is_valid_transition(new_value):
            raise ValueError(f"Invalid state transition to {new_value}")

        # Perform modification
        old_state = self._state1
        self._state1 = new_value

        # Check invariants after modification
        try:
            self._check_invariants()
        except RuntimeError:
            # Rollback on invariant violation
            self._state1 = old_state
            raise

    def _state_is_consistent(self) -> bool:
        """Check state consistency."""
        return True  # Implementation specific

    def _values_in_range(self) -> bool:
        """Check value constraints."""
        return True  # Implementation specific

    def _relationships_valid(self) -> bool:
        """Check relationship constraints."""
        return True  # Implementation specific
```

---

## Real-World Examples

### Example 1: Financial Calculation with Defensive Programming

```python
from decimal import Decimal, InvalidOperation
from typing import Optional

class FinancialCalculator:
    """Financial calculations with NASA-level defensive programming."""

    @staticmethod
    def calculate_compound_interest(
        principal: Decimal,
        rate: Decimal,
        periods: int,
        compounds_per_period: int = 1
    ) -> Decimal:
        """
        Calculate compound interest with comprehensive validation.

        Preconditions:
            - principal must be positive Decimal
            - rate must be between 0 and 1
            - periods must be positive integer
            - compounds_per_period must be positive integer

        Postconditions:
            - Result must be >= principal (no negative interest)
            - Result must be finite and valid Decimal
        """
        # PRECONDITION 1: Type validation
        if not isinstance(principal, Decimal):
            raise TypeError(f"principal must be Decimal, got {type(principal).__name__}")
        if not isinstance(rate, Decimal):
            raise TypeError(f"rate must be Decimal, got {type(rate).__name__}")
        if not isinstance(periods, int):
            raise TypeError(f"periods must be int, got {type(periods).__name__}")
        if not isinstance(compounds_per_period, int):
            raise TypeError(f"compounds_per_period must be int, got {type(compounds_per_period).__name__}")

        # PRECONDITION 2: Value validation
        if principal <= 0:
            raise ValueError(f"principal must be positive, got {principal}")
        if not (Decimal('0') <= rate <= Decimal('1')):
            raise ValueError(f"rate must be between 0 and 1, got {rate}")
        if periods <= 0:
            raise ValueError(f"periods must be positive, got {periods}")
        if compounds_per_period <= 0:
            raise ValueError(f"compounds_per_period must be positive, got {compounds_per_period}")

        # PRECONDITION 3: Overflow prevention
        max_periods = 10000
        if periods > max_periods:
            raise ValueError(f"periods exceeds maximum {max_periods}")

        # Calculate compound interest: A = P(1 + r/n)^(nt)
        try:
            rate_per_compound = rate / Decimal(compounds_per_period)
            total_compounds = periods * compounds_per_period
            multiplier = (Decimal('1') + rate_per_compound) ** total_compounds
            result = principal * multiplier
        except (InvalidOperation, OverflowError) as e:
            raise RuntimeError(f"Calculation error: {e}")

        # POSTCONDITION 1: Result validation
        if result < principal:
            raise RuntimeError(
                f"Postcondition failed: result {result} < principal {principal}"
            )

        # POSTCONDITION 2: Finite check
        if not result.is_finite():
            raise RuntimeError(f"Postcondition failed: result {result} not finite")

        # POSTCONDITION 3: Precision check
        if result.as_tuple().exponent < -10:
            raise RuntimeError(f"Postcondition failed: excessive precision loss")

        return result
```

### Example 2: Data Processing with Loop Invariants

```python
from typing import List, Optional

def calculate_moving_average(
    data: List[float],
    window_size: int
) -> List[float]:
    """
    Calculate moving average with comprehensive validation.

    Preconditions:
        - data must be non-empty list of floats
        - window_size must be positive and <= len(data)
        - All data values must be finite

    Loop invariants:
        - result length increases by 1 each iteration
        - Each result value is within data range
        - No NaN or Inf values in result

    Postconditions:
        - Result length = len(data) - window_size + 1
        - All result values are finite
    """
    # PRECONDITION 1: Type validation
    if not isinstance(data, list):
        raise TypeError(f"data must be list, got {type(data).__name__}")
    if not isinstance(window_size, int):
        raise TypeError(f"window_size must be int, got {type(window_size).__name__}")

    # PRECONDITION 2: Non-empty validation
    if not data:
        raise ValueError("data cannot be empty")

    # PRECONDITION 3: Window size validation
    if window_size <= 0:
        raise ValueError(f"window_size must be positive, got {window_size}")
    if window_size > len(data):
        raise ValueError(
            f"window_size {window_size} exceeds data length {len(data)}"
        )

    # PRECONDITION 4: Data validity
    import math
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in data):
        raise ValueError("All data values must be finite numbers")

    # Calculate moving average
    result = []
    data_min = min(data)
    data_max = max(data)

    for i in range(len(data) - window_size + 1):
        # INVARIANT 1: Result length check
        if len(result) != i:
            raise RuntimeError(
                f"Loop invariant violated: expected {i} results, got {len(result)}"
            )

        # Calculate window average
        window = data[i:i + window_size]
        avg = sum(window) / window_size

        # INVARIANT 2: Range check
        if not (data_min <= avg <= data_max):
            raise RuntimeError(
                f"Loop invariant violated: avg {avg} outside range [{data_min}, {data_max}]"
            )

        # INVARIANT 3: Finite check
        if not math.isfinite(avg):
            raise RuntimeError(f"Loop invariant violated: avg {avg} not finite")

        result.append(avg)

    # POSTCONDITION 1: Length check
    expected_length = len(data) - window_size + 1
    if len(result) != expected_length:
        raise RuntimeError(
            f"Postcondition failed: expected {expected_length} results, got {len(result)}"
        )

    # POSTCONDITION 2: Finite check
    if not all(math.isfinite(x) for x in result):
        raise RuntimeError("Postcondition failed: result contains non-finite values")

    return result
```

### Example 3: State Machine with Invariants

```python
from enum import Enum
from typing import Optional, Set

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"

class ConnectionManager:
    """
    Connection manager with state invariants.

    Class invariants:
        - State transitions must be valid
        - Active connections count must match state
        - Error state must have error message
    """

    VALID_TRANSITIONS = {
        ConnectionState.DISCONNECTED: {ConnectionState.CONNECTING},
        ConnectionState.CONNECTING: {ConnectionState.CONNECTED, ConnectionState.ERROR},
        ConnectionState.CONNECTED: {ConnectionState.DISCONNECTING},
        ConnectionState.DISCONNECTING: {ConnectionState.DISCONNECTED, ConnectionState.ERROR},
        ConnectionState.ERROR: {ConnectionState.DISCONNECTED}
    }

    def __init__(self):
        self._state = ConnectionState.DISCONNECTED
        self._active_connections = 0
        self._error_message: Optional[str] = None
        self._check_invariants()

    def _check_invariants(self):
        """Validate all class invariants."""
        # INVARIANT 1: State-connection count consistency
        if self._state == ConnectionState.CONNECTED:
            if self._active_connections != 1:
                raise RuntimeError(
                    f"Invariant violated: CONNECTED state but "
                    f"{self._active_connections} active connections"
                )
        elif self._state in (ConnectionState.DISCONNECTED, ConnectionState.ERROR):
            if self._active_connections != 0:
                raise RuntimeError(
                    f"Invariant violated: {self._state.value} state but "
                    f"{self._active_connections} active connections"
                )

        # INVARIANT 2: Error state must have error message
        if self._state == ConnectionState.ERROR:
            if not self._error_message:
                raise RuntimeError(
                    "Invariant violated: ERROR state without error message"
                )

        # INVARIANT 3: Non-negative connection count
        if self._active_connections < 0:
            raise RuntimeError(
                f"Invariant violated: negative connection count {self._active_connections}"
            )

    def transition_to(self, new_state: ConnectionState, error_msg: Optional[str] = None):
        """
        Transition to new state with validation.

        Preconditions:
            - new_state must be valid ConnectionState
            - Transition must be valid from current state
            - If new_state is ERROR, error_msg must be provided
        """
        # PRECONDITION 1: Type validation
        if not isinstance(new_state, ConnectionState):
            raise TypeError(f"new_state must be ConnectionState, got {type(new_state).__name__}")

        # PRECONDITION 2: Valid transition check
        valid_next_states = self.VALID_TRANSITIONS.get(self._state, set())
        if new_state not in valid_next_states:
            raise ValueError(
                f"Invalid transition from {self._state.value} to {new_state.value}"
            )

        # PRECONDITION 3: Error message validation
        if new_state == ConnectionState.ERROR and not error_msg:
            raise ValueError("ERROR state requires error message")

        # Save old state for rollback
        old_state = self._state
        old_connections = self._active_connections
        old_error = self._error_message

        try:
            # Perform state transition
            self._state = new_state

            # Update connection count
            if new_state == ConnectionState.CONNECTED:
                self._active_connections = 1
            elif new_state in (ConnectionState.DISCONNECTED, ConnectionState.ERROR):
                self._active_connections = 0

            # Update error message
            if new_state == ConnectionState.ERROR:
                self._error_message = error_msg
            else:
                self._error_message = None

            # Validate invariants
            self._check_invariants()

        except RuntimeError:
            # Rollback on invariant violation
            self._state = old_state
            self._active_connections = old_connections
            self._error_message = old_error
            raise

    def connect(self):
        """Initiate connection."""
        self.transition_to(ConnectionState.CONNECTING)
        # ... connection logic ...
        self.transition_to(ConnectionState.CONNECTED)

    def disconnect(self):
        """Initiate disconnection."""
        self.transition_to(ConnectionState.DISCONNECTING)
        # ... disconnection logic ...
        self.transition_to(ConnectionState.DISCONNECTED)
```

---

## Tool Recommendations

### Production-Ready Tools

1. **icontract** (Recommended for new code)
   - **Strengths**: Comprehensive contract support, inheritance, detailed errors
   - **Use for**: Critical business logic, API implementations
   - **Installation**: `pip install icontract`

2. **Pydantic** (Recommended for data validation)
   - **Strengths**: Fast (Rust core), automatic coercion, wide adoption
   - **Use for**: API request/response validation, configuration
   - **Installation**: `pip install pydantic`

3. **Beartype** (Recommended for performance-critical code)
   - **Strengths**: O(1) complexity, zero overhead, type checking
   - **Use for**: High-performance systems, large codebases
   - **Installation**: `pip install beartype`

4. **Typeguard** (Recommended for development)
   - **Strengths**: Comprehensive checking, easy integration
   - **Use for**: Development/debugging, test environments
   - **Installation**: `pip install typeguard`

### Static Analysis Tools

1. **Mypy** - Static type checking
   - Catches type errors before runtime
   - `pip install mypy`

2. **Pyright** - Microsoft's static type checker
   - Fast, accurate type checking
   - `npm install -g pyright`

3. **Bandit** - Security issue detection
   - Finds security vulnerabilities
   - `pip install bandit`

### Custom Tooling

Create project-specific assertion injection tools:

```bash
# Example: Automated assertion density calculator
python scripts/calculate_assertion_density.py --target 2.0 --report

# Example: Assertion suggestion tool
python scripts/suggest_assertions.py --file module.py --output suggestions.json

# Example: AST-based assertion injector
python scripts/inject_assertions.py --input module.py --output module_safe.py
```

---

## Implementation Roadmap for 759 Python Files

### Phase 1: Assessment (Week 1)
1. Calculate current assertion density per file
2. Identify high-risk modules (financial, security, data processing)
3. Generate automated assertion suggestions

### Phase 2: Library Integration (Week 2)
1. Install and configure icontract for new code
2. Add Pydantic for data validation
3. Integrate Beartype for type checking

### Phase 3: Automated Injection (Week 3-4)
1. Run AST-based assertion injector on low-risk modules
2. Review and approve suggested assertions
3. Apply auto-generated validations

### Phase 4: Manual Review (Week 5-6)
1. Add domain-specific assertions to critical modules
2. Implement class invariants for stateful objects
3. Add loop invariants for complex algorithms

### Phase 5: Validation (Week 7-8)
1. Run comprehensive test suite
2. Measure assertion density improvements
3. Verify NASA POT10 compliance

### Target Metrics
- **Assertion Density**: 0% → 2%+ average
- **Coverage**: 100% of functions with ≥2 validations
- **Critical Modules**: 3%+ assertion density
- **Zero**: Production assert statements (all converted to exceptions)

---

## Summary

### Key Takeaways

1. **Python assert is UNSAFE for production** - Always use explicit exceptions
2. **NASA POT10 requires 2+ assertions per function** - Use production-safe alternatives
3. **Use contract programming libraries** - icontract, Pydantic, Beartype
4. **Automate assertion injection** - AST-based tools, static analysis
5. **Validate thoroughly** - Preconditions, postconditions, invariants, edge cases

### Production-Safe Assertion Strategy

```python
# ❌ NEVER in production
assert condition, "message"

# ✅ ALWAYS in production
if not condition:
    raise AppropriateException("message")

# ✅ OR use libraries
@icontract.pre(lambda x: condition(x))
def function(x): ...
```

### Next Steps

1. **Audit existing code** - Find all assert statements
2. **Replace with exceptions** - Convert to production-safe validations
3. **Integrate libraries** - Add icontract, Pydantic, Beartype
4. **Automate injection** - Use AST tools for systematic coverage
5. **Measure progress** - Track assertion density metrics

---

## References

1. NASA Power of 10 Rules: https://spinroot.com/gerard/pdf/P10.pdf
2. JPL Coding Standards: https://lars-lab.jpl.nasa.gov/jpl_coding_standard.pdf
3. Python Assert Documentation: https://docs.python.org/3/reference/simple_stmts.html#assert
4. icontract Library: https://icontract.readthedocs.io/
5. Pydantic Documentation: https://docs.pydantic.dev/
6. Beartype Documentation: https://github.com/beartype/beartype
7. Defensive Programming Guide: https://swc-osg-workshop.github.io/2017-05-17-JLAB/novice/python/05-defensive.html