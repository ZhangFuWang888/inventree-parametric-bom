"""Whitelist of allowed functions for the formula engine.

Only functions registered here can be called from formulas.
This is a key safety mechanism — no exec/eval, no Python builtins.
"""

import math
from typing import Any, Callable, Union

Numeric = Union[int, float]


# ──────────────────────────────────────────────
#  Registered function type
# ──────────────────────────────────────────────

class FunctionDef:
    """Definition of a whitelisted function."""

    __slots__ = ('name', 'fn', 'min_args', 'max_args', 'description')

    def __init__(
        self,
        name: str,
        fn: Callable,
        min_args: int = 1,
        max_args: int = 10,
        description: str = '',
    ):
        self.name = name
        self.fn = fn
        self.min_args = min_args
        self.max_args = max_args
        self.description = description


# ──────────────────────────────────────────────
#  Function implementations
# ──────────────────────────────────────────────


def _ceil(x: Numeric) -> int:
    """CEIL — round up to nearest integer."""
    return int(math.ceil(float(x)))


def _floor(x: Numeric) -> int:
    """FLOOR — round down to nearest integer."""
    return int(math.floor(float(x)))


def _round(x: Numeric, decimals: int = 0) -> float:
    """ROUND — round to specified decimal places."""
    return round(float(x), int(decimals))


def _abs(x: Numeric) -> float:
    """ABS — absolute value."""
    return abs(float(x))


def _min(*args: Numeric) -> float:
    """MIN — minimum of provided values."""
    return min(float(a) for a in args)


def _max(*args: Numeric) -> float:
    """MAX — maximum of provided values."""
    return max(float(a) for a in args)


def _if(condition: Any, true_val: Any, false_val: Any) -> Any:
    """IF — conditional: if condition is truthy, returns true_val, else false_val."""
    return true_val if condition else false_val


def _and(*args: Any) -> bool:
    """AND — logical AND of all arguments."""
    return all(bool(a) for a in args)


def _or(*args: Any) -> bool:
    """OR — logical OR of all arguments."""
    return any(bool(a) for a in args)


def _not(x: Any) -> bool:
    """NOT — logical negation."""
    return not bool(x)


def _sum(*args: Numeric) -> float:
    """SUM — sum of all provided values."""
    return sum(float(a) for a in args)


def _count(*args: Any) -> int:
    """COUNT — count of provided values."""
    return len(args)


def _avg(*args: Numeric) -> float:
    """AVG — average of provided values."""
    nums = [float(a) for a in args]
    return sum(nums) / len(nums) if nums else 0.0


def _pow(x: Numeric, y: Numeric) -> float:
    """POW — x raised to power y."""
    return float(x) ** float(y)


def _sqrt(x: Numeric) -> float:
    """SQRT — square root."""
    return math.sqrt(float(x))


def _mod(x: Numeric, y: Numeric) -> float:
    """MOD — modulo (remainder)."""
    return float(x) % float(y)


# ──────────────────────────────────────────────
#  Registry
# ──────────────────────────────────────────────

FUNCTION_REGISTRY: dict[str, FunctionDef] = {
    'CEIL': FunctionDef('CEIL', _ceil, 1, 1, 'Round up to nearest integer'),
    'FLOOR': FunctionDef('FLOOR', _floor, 1, 1, 'Round down to nearest integer'),
    'ROUND': FunctionDef('ROUND', _round, 1, 2, 'Round to decimal places'),
    'ABS': FunctionDef('ABS', _abs, 1, 1, 'Absolute value'),
    'MIN': FunctionDef('MIN', _min, 1, 20, 'Minimum value'),
    'MAX': FunctionDef('MAX', _max, 1, 20, 'Maximum value'),
    'IF': FunctionDef('IF', _if, 3, 3, 'Conditional: IF(condition, true_val, false_val)'),
    'AND': FunctionDef('AND', _and, 1, 20, 'Logical AND'),
    'OR': FunctionDef('OR', _or, 1, 20, 'Logical OR'),
    'NOT': FunctionDef('NOT', _not, 1, 1, 'Logical NOT'),
    'SUM': FunctionDef('SUM', _sum, 1, 20, 'Sum of values'),
    'COUNT': FunctionDef('COUNT', _count, 1, 20, 'Count of values'),
    'AVG': FunctionDef('AVG', _avg, 1, 20, 'Average of values'),
    'POW': FunctionDef('POW', _pow, 2, 2, 'Power: x^y'),
    'SQRT': FunctionDef('SQRT', _sqrt, 1, 1, 'Square root'),
    'MOD': FunctionDef('MOD', _mod, 2, 2, 'Modulo: x % y'),
}


def get_function(name: str) -> FunctionDef:
    """Look up a function by name (case-insensitive)."""
    upper = name.upper()
    if upper not in FUNCTION_REGISTRY:
        raise ValueError(f'Unknown function: {name}')
    return FUNCTION_REGISTRY[upper]
