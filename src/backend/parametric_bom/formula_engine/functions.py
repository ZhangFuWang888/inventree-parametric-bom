"""Whitelist of allowed functions for the formula engine.

Only functions registered here can be called from formulas.
This is a key safety mechanism — no exec/eval, no Python builtins.
"""

import math
import re
from typing import Any, Callable, Union, Optional

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


# ══════════════════════════════════════════════
#  String functions
# ══════════════════════════════════════════════


def _concat(*args: Any) -> str:
    """CONCAT — concatenate strings."""
    return ''.join(str(a) for a in args)


def _left(s: str, n: int) -> str:
    """LEFT — first n characters."""
    return str(s)[:int(n)]


def _right(s: str, n: int) -> str:
    """RIGHT — last n characters."""
    return str(s)[-int(n):] if n > 0 else ''


def _mid(s: str, start: int, length: int) -> str:
    """MID — substring from start with length (1-indexed)."""
    s = str(s)
    start_i = int(start) - 1
    return s[start_i:start_i + int(length)]


def _len(s: Any) -> int:
    """LEN — length of string."""
    return len(str(s))


def _find(find_text: str, within_text: str, start_num: int = 1) -> int:
    """FIND — position of substring (1-indexed, case-sensitive)."""
    s = str(within_text)
    start = int(start_num) - 1
    pos = s.find(str(find_text), start)
    if pos == -1:
        return 0
    return pos + 1


def _upper(s: str) -> str:
    """UPPER — convert to uppercase."""
    return str(s).upper()


def _lower(s: str) -> str:
    """LOWER — convert to lowercase."""
    return str(s).lower()


def _trim(s: str) -> str:
    """TRIM — remove leading/trailing whitespace."""
    return str(s).strip()


def _replace(old_text: str, start: int, num_chars: int, new_text: str) -> str:
    """REPLACE — replace characters at position."""
    s = str(old_text)
    start_i = int(start) - 1
    return s[:start_i] + str(new_text) + s[start_i + int(num_chars):]


def _substitute(text: str, old: str, new: str) -> str:
    """SUBSTITUTE — replace all occurrences of old with new."""
    return str(text).replace(str(old), str(new))


# ══════════════════════════════════════════════
#  Trigonometric functions (degrees)
# ══════════════════════════════════════════════


def _sin(x: Numeric) -> float:
    """SIN — sine (degrees)."""
    return math.sin(math.radians(float(x)))


def _cos(x: Numeric) -> float:
    """COS — cosine (degrees)."""
    return math.cos(math.radians(float(x)))


def _tan(x: Numeric) -> float:
    """TAN — tangent (degrees)."""
    return math.tan(math.radians(float(x)))


def _asin(x: Numeric) -> float:
    """ASIN — arcsine (returns degrees)."""
    return math.degrees(math.asin(float(x)))


def _acos(x: Numeric) -> float:
    """ACOS — arccosine (returns degrees)."""
    return math.degrees(math.acos(float(x)))


def _atan(x: Numeric) -> float:
    """ATAN — arctangent (returns degrees)."""
    return math.degrees(math.atan(float(x)))


def _atan2(y: Numeric, x: Numeric) -> float:
    """ATAN2 — arctangent of y/x (returns degrees, full quadrant)."""
    return math.degrees(math.atan2(float(y), float(x)))


def _degrees(x: Numeric) -> float:
    """DEGREES — convert radians to degrees."""
    return math.degrees(float(x))


def _radians(x: Numeric) -> float:
    """RADIANS — convert degrees to radians."""
    return math.radians(float(x))


# ══════════════════════════════════════════════
#  Type conversion functions
# ══════════════════════════════════════════════


def _int_val(x: Any) -> int:
    """INT — convert to integer (truncates)."""
    return int(float(x)) if not isinstance(x, bool) else (1 if x else 0)


def _float_val(x: Any) -> float:
    """FLOAT — convert to float."""
    return float(x)


def _str_val(x: Any) -> str:
    """STR — convert to string."""
    if isinstance(x, float) and x == int(x):
        return str(int(x))
    return str(x)


def _bool_val(x: Any) -> bool:
    """BOOL — convert to boolean."""
    return bool(x)


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
    # String functions
    'CONCAT': FunctionDef('CONCAT', _concat, 1, 20, 'Concatenate strings'),
    'LEFT': FunctionDef('LEFT', _left, 2, 2, 'First N characters: LEFT(text, n)'),
    'RIGHT': FunctionDef('RIGHT', _right, 2, 2, 'Last N characters: RIGHT(text, n)'),
    'MID': FunctionDef('MID', _mid, 3, 3, 'Substring: MID(text, start, length)'),
    'LEN': FunctionDef('LEN', _len, 1, 1, 'Length of string'),
    'FIND': FunctionDef('FIND', _find, 2, 3, 'Find position: FIND(find, within, [start])'),
    'UPPER': FunctionDef('UPPER', _upper, 1, 1, 'Convert to uppercase'),
    'LOWER': FunctionDef('LOWER', _lower, 1, 1, 'Convert to lowercase'),
    'TRIM': FunctionDef('TRIM', _trim, 1, 1, 'Remove leading/trailing whitespace'),
    'REPLACE': FunctionDef('REPLACE', _replace, 4, 4, 'Replace chars: REPLACE(text, start, n, new)'),
    'SUBSTITUTE': FunctionDef('SUBSTITUTE', _substitute, 3, 3, 'Replace all: SUBSTITUTE(text, old, new)'),
    # Trigonometric functions (degrees)
    'SIN': FunctionDef('SIN', _sin, 1, 1, 'Sine (degrees)'),
    'COS': FunctionDef('COS', _cos, 1, 1, 'Cosine (degrees)'),
    'TAN': FunctionDef('TAN', _tan, 1, 1, 'Tangent (degrees)'),
    'ASIN': FunctionDef('ASIN', _asin, 1, 1, 'Arcsine (returns degrees)'),
    'ACOS': FunctionDef('ACOS', _acos, 1, 1, 'Arccosine (returns degrees)'),
    'ATAN': FunctionDef('ATAN', _atan, 1, 1, 'Arctangent (returns degrees)'),
    'ATAN2': FunctionDef('ATAN2', _atan2, 2, 2, 'Arctangent y/x (returns degrees, full quadrant)'),
    'DEGREES': FunctionDef('DEGREES', _degrees, 1, 1, 'Convert radians to degrees'),
    'RADIANS': FunctionDef('RADIANS', _radians, 1, 1, 'Convert degrees to radians'),
    # Type conversion
    'INT': FunctionDef('INT', _int_val, 1, 1, 'Convert to integer'),
    'FLOAT': FunctionDef('FLOAT', _float_val, 1, 1, 'Convert to float'),
    'STR': FunctionDef('STR', _str_val, 1, 1, 'Convert to string'),
    'BOOL': FunctionDef('BOOL', _bool_val, 1, 1, 'Convert to boolean'),
}


def get_function(name: str) -> FunctionDef:
    """Look up a function by name (case-insensitive)."""
    upper = name.upper()
    if upper not in FUNCTION_REGISTRY:
        raise ValueError(f'Unknown function: {name}')
    return FUNCTION_REGISTRY[upper]
