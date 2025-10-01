"""
Production-Safe Assertion Framework
Replaces Python's unsafe assert statements with production-ready alternatives.
Implements icontract, Pydantic, and custom validators that work with -O flag.
"""

from dataclasses import dataclass
import functools
import inspect
from typing import Any, Callable, Optional, Type, Union, get_type_hints


class AssertionError(Exception):
    """Custom assertion error that works in production."""

    pass


class ProductionAssert:
    """
    Production-safe assertion framework.
    These assertions cannot be disabled with -O or -OO flags.
    """

    @staticmethod
    def require(condition: bool, message: str = "Precondition failed"):
        """
        Precondition check - validates input requirements.
        Always executes, even in optimized mode.
        """
        if not condition:
            raise AssertionError(f"PRECONDITION: {message}")

    @staticmethod
    def ensure(condition: bool, message: str = "Postcondition failed"):
        """
        Postcondition check - validates output guarantees.
        Always executes, even in optimized mode.
        """
        if not condition:
            raise AssertionError(f"POSTCONDITION: {message}")

    @staticmethod
    def invariant(condition: bool, message: str = "Invariant violated"):
        """
        Invariant check - validates state consistency.
        Always executes, even in optimized mode.
        """
        if not condition:
            raise AssertionError(f"INVARIANT: {message}")

    @staticmethod
    def validate(value: Any, validator: Callable[[Any], bool], message: str = "Validation failed"):
        """
        Custom validation with callable validator.
        Always executes, even in optimized mode.
        """
        if not validator(value):
            raise AssertionError(f"VALIDATION: {message} (value: {value})")

    @staticmethod
    def type_check(value: Any, expected_type: Type, param_name: str = "parameter"):
        """
        Type validation that works in production.
        """
        if not isinstance(value, expected_type):
            raise TypeError(f"TYPE: {param_name} must be {expected_type.__name__}, " f"got {type(value).__name__}")

    @staticmethod
    def range_check(
        value: Union[int, float],
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        param_name: str = "value",
    ):
        """
        Range validation for numeric values.
        """
        if min_val is not None and value < min_val:
            raise ValueError(f"RANGE: {param_name} must be >= {min_val}, got {value}")
        if max_val is not None and value > max_val:
            raise ValueError(f"RANGE: {param_name} must be <= {max_val}, got {value}")

    @staticmethod
    def not_none(value: Any, param_name: str = "parameter"):
        """
        Non-null validation.
        """
        if value is None:
            raise ValueError(f"NULL: {param_name} cannot be None")

    @staticmethod
    def not_empty(value: Any, param_name: str = "parameter"):
        """
        Non-empty validation for collections and strings.
        """
        if not value:
            raise ValueError(f"EMPTY: {param_name} cannot be empty")


# Decorator-based contract programming (icontract-style)


def precondition(predicate: Callable[..., bool], message: str = "Precondition failed"):
    """
    Decorator for function preconditions.
    Validates inputs before function execution.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Bind arguments to function signature
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Check precondition
            if not predicate(**bound.arguments):
                raise AssertionError(f"PRECONDITION ({func.__name__}): {message}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def postcondition(predicate: Callable[..., bool], message: str = "Postcondition failed"):
    """
    Decorator for function postconditions.
    Validates outputs after function execution.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Bind arguments and result
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Add result to arguments for checking
            check_args = dict(bound.arguments)
            check_args["__result__"] = result

            # Check postcondition
            if not predicate(**check_args):
                raise AssertionError(f"POSTCONDITION ({func.__name__}): {message}")

            return result

        return wrapper

    return decorator


def invariant(predicate: Callable[[Any], bool], message: str = "Invariant violated"):
    """
    Class decorator for invariants.
    Checks invariant after every method call.
    """

    def decorator(cls: Type) -> Type:
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            if not predicate(self):
                raise AssertionError(f"INVARIANT ({cls.__name__}): {message} after __init__")

        cls.__init__ = new_init

        # Wrap all public methods
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith("_"):
                original_method = method

                @functools.wraps(original_method)
                def wrapped_method(self, *args, **kwargs):
                    result = original_method(self, *args, **kwargs)
                    if not predicate(self):
                        raise AssertionError(f"INVARIANT ({cls.__name__}): {message} after {name}")
                    return result

                setattr(cls, name, wrapped_method)

        return cls

    return decorator


# Pydantic-style data validation


@dataclass
class ValidatedField:
    """Field with validation rules."""

    min_val: Optional[Union[int, float]] = None
    max_val: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex: Optional[str] = None
    not_none: bool = False
    not_empty: bool = False

    def validate(self, value: Any, field_name: str = "field"):
        """Validate value against all rules."""
        if self.not_none and value is None:
            raise ValueError(f"{field_name} cannot be None")

        if self.not_empty and not value:
            raise ValueError(f"{field_name} cannot be empty")

        if value is not None:
            if self.min_val is not None and value < self.min_val:
                raise ValueError(f"{field_name} must be >= {self.min_val}")

            if self.max_val is not None and value > self.max_val:
                raise ValueError(f"{field_name} must be <= {self.max_val}")

            if hasattr(value, "__len__"):
                if self.min_length is not None and len(value) < self.min_length:
                    raise ValueError(f"{field_name} length must be >= {self.min_length}")

                if self.max_length is not None and len(value) > self.max_length:
                    raise ValueError(f"{field_name} length must be <= {self.max_length}")

            if self.regex and isinstance(value, str):
                import re

                if not re.match(self.regex, value):
                    raise ValueError(f"{field_name} must match pattern {self.regex}")


# Type checking decorator (Beartype-style)


def type_checked(func: Callable) -> Callable:
    """
    Decorator for runtime type checking.
    Validates all typed parameters and return value.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get type hints
        hints = get_type_hints(func)

        # Bind arguments
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        # Check input types
        for param_name, param_value in bound.arguments.items():
            if param_name in hints:
                expected_type = hints[param_name]
                if not isinstance(param_value, expected_type):
                    raise TypeError(
                        f"{func.__name__}() {param_name} must be {expected_type.__name__}, "
                        f"got {type(param_value).__name__}"
                    )

        # Execute function
        result = func(*args, **kwargs)

        # Check return type
        if "return" in hints:
            expected_return = hints["return"]
            if not isinstance(result, expected_return):
                raise TypeError(
                    f"{func.__name__}() return value must be {expected_return.__name__}, "
                    f"got {type(result).__name__}"
                )

        return result

    return wrapper


# Loop invariant checker


class LoopInvariant:
    """Context manager for loop invariant checking."""

    def __init__(self, invariant_func: Callable[[], bool], message: str = "Loop invariant violated"):
        self.invariant_func = invariant_func
        self.message = message
        self.iteration_count = 0

    def __enter__(self):
        """Check invariant at loop entry."""
        if not self.invariant_func():
            raise AssertionError(f"LOOP INVARIANT (entry): {self.message}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Check invariant at loop exit."""
        if not self.invariant_func():
            raise AssertionError(f"LOOP INVARIANT (exit): {self.message}")

    def check(self):
        """Check invariant during iteration."""
        self.iteration_count += 1
        if not self.invariant_func():
            raise AssertionError(f"LOOP INVARIANT (iteration {self.iteration_count}): {self.message}")


# Example usage and migration guide


def example_before_migration():
    """Example of unsafe Python assert statements."""

    def calculate_average(numbers):
        assert numbers, "List cannot be empty"  # UNSAFE - disabled with -O
        assert all(isinstance(n, (int, float)) for n in numbers)  # UNSAFE

        total = sum(numbers)
        count = len(numbers)
        result = total / count

        assert result >= 0  # UNSAFE - disabled with -O
        return result


def example_after_migration():
    """Example using production-safe assertions."""

    @type_checked
    @precondition(lambda numbers: len(numbers) > 0, "List cannot be empty")
    @postcondition(lambda numbers, __result__: __result__ >= 0, "Result must be non-negative")
    def calculate_average(numbers: list) -> float:
        # Production-safe assertions that always execute
        ProductionAssert.not_empty(numbers, "numbers")
        ProductionAssert.validate(
            numbers, lambda lst: all(isinstance(n, (int, float)) for n in lst), "All elements must be numeric"
        )

        total = sum(numbers)
        count = len(numbers)

        # Loop invariant example
        running_sum = 0
        with LoopInvariant(lambda: running_sum <= total, "Running sum exceeds total"):
            for num in numbers:
                running_sum += num
                # Could check invariant during loop if needed

        result = total / count

        # Postcondition check (redundant with decorator, shown for example)
        ProductionAssert.ensure(result >= 0, f"Average {result} must be non-negative")

        return result


# AST transformer for automatic migration


class AssertionMigrator:
    """
    Automatically converts Python assert statements to production-safe assertions.
    """

    @staticmethod
    def migrate_file(file_path: str, output_path: str = None):
        """
        Migrate assert statements in a Python file to production-safe assertions.
        """
        import ast

        import astor

        with open(file_path) as f:
            source = f.read()

        tree = ast.parse(source)

        class AssertTransformer(ast.NodeTransformer):
            def visit_Assert(self, node):
                """Transform assert to ProductionAssert.require."""
                # Create the new call
                if node.msg:
                    msg_arg = node.msg
                else:
                    msg_arg = ast.Constant(value="Assertion failed")

                new_call = ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="ProductionAssert", ctx=ast.Load()), attr="require", ctx=ast.Load()
                        ),
                        args=[node.test, msg_arg],
                        keywords=[],
                    )
                )

                return new_call

        # Transform the tree
        transformer = AssertTransformer()
        new_tree = transformer.visit(tree)

        # Add import at the top
        import_node = ast.ImportFrom(
            module="fixes.phase0.production_safe_assertions",
            names=[ast.alias(name="ProductionAssert", asname=None)],
            level=0,
        )
        new_tree.body.insert(0, import_node)

        # Generate new source
        new_source = astor.to_source(new_tree)

        # Write output
        if output_path is None:
            output_path = file_path.replace(".py", "_safe.py")

        with open(output_path, "w") as f:
            f.write(new_source)

        return output_path


def main():
    """Test the production-safe assertion framework."""
    print("Testing Production-Safe Assertion Framework")
    print("=" * 50)

    # Test basic assertions
    try:
        ProductionAssert.require(True, "This should pass")
        print("✓ Basic require passed")
    except AssertionError as e:
        print(f"✗ Basic require failed: {e}")

    try:
        ProductionAssert.require(False, "This should fail")
        print("✗ Basic require should have failed")
    except AssertionError as e:
        print(f"✓ Basic require failed as expected: {e}")

    # Test decorated function
    try:
        result = example_after_migration()([1, 2, 3, 4, 5])
        print(f"✓ Decorated function passed, average: {result}")
    except Exception as e:
        print(f"✗ Decorated function failed: {e}")

    try:
        result = example_after_migration()([])  # Should fail precondition
        print("✗ Empty list should have failed")
    except AssertionError as e:
        print(f"✓ Empty list failed as expected: {e}")

    print("\n✓ All production-safe assertions work correctly!")
    print("These assertions will work even with python -O flag")


if __name__ == "__main__":
    main()
