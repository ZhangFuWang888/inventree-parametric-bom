"""Custom exceptions for the formula engine."""


class FormulaError(Exception):
    """Base exception for formula engine errors."""


class ParseError(FormulaError):
    """Raised when formula syntax is invalid."""


class EvaluationError(FormulaError):
    """Raised when formula evaluation fails (timeout, type error, etc.)."""


class ReferenceError(FormulaError):
    """Raised when a referenced parameter does not exist."""


class TimeoutError(FormulaError):
    """Raised when formula evaluation exceeds the time limit."""


class RecursionError(FormulaError):
    """Raised when formula evaluation exceeds the recursion limit."""
