"""Formula engine for Parametric BOM.

Provides safe, sandboxed formula evaluation for dynamic BOM calculations.
Supported syntax:
  - Arithmetic: + - * / ( )
  - Comparison: > < >= <= = !=
  - Logical: AND OR NOT
  - Functions: CEIL FLOOR ROUND ABS IF MIN MAX
  - Parameter refs: param.xxx, parent.xxx, sys.xxx
  - Strings and numbers

Safety:
  - 500ms timeout on evaluation
  - 20-level recursion limit
  - Function whitelist only (no exec/eval)
  - No access to Python builtins
"""

from .parser import FormulaParser, ParseError
from .evaluator import FormulaEvaluator, EvaluationError
from .functions import FUNCTION_REGISTRY

__all__ = [
    'FormulaParser',
    'FormulaEvaluator',
    'ParseError',
    'EvaluationError',
    'FUNCTION_REGISTRY',
]


def evaluate(formula: str, context: dict, timeout_ms: int = 500, max_recursion: int = 20):
    """One-shot formula evaluation.

    Args:
        formula: The formula string to evaluate.
        context: Parameter values dict. Format:
            {'param': {'长度': 5000, '速度': 12}, 'parent': {...}, 'sys': {...}}
        timeout_ms: Max evaluation time in milliseconds.
        max_recursion: Max recursion depth for nested formulas.

    Returns:
        The computed value (int, float, str, or bool).

    Raises:
        ParseError: If the formula syntax is invalid.
        EvaluationError: If evaluation fails (timeout, ref error, type error).
    """
    parser = FormulaParser(formula)
    ast = parser.parse()

    evaluator = FormulaEvaluator(context, timeout_ms=timeout_ms, max_recursion=max_recursion)
    return evaluator.evaluate(ast)


def validate(formula: str) -> dict:
    """Validate a formula and return diagnostics.

    Returns:
        dict with keys: valid (bool), errors (list), referenced_params (list)
    """
    result = {
        'valid': True,
        'errors': [],
        'referenced_params': [],
    }

    if not formula or not formula.strip():
        return result

    try:
        parser = FormulaParser(formula)
        ast = parser.parse()

        # Collect referenced parameters
        result['referenced_params'] = _collect_params(ast)
    except ParseError as e:
        result['valid'] = False
        result['errors'].append(str(e))

    return result


def _collect_params(node) -> list:
    """Walk the AST and collect all parameter references."""
    from .parser import (
        BinOpNode, CompareNode, FuncCallNode, NumberNode,
        ParamNode, ParentParamNode, StringNode, SysParamNode, UnaryOpNode,
    )

    params = []

    if isinstance(node, (ParamNode, ParentParamNode, SysParamNode)):
        name = node.name
        prefix = {
            ParamNode: 'param',
            ParentParamNode: 'parent',
            SysParamNode: 'sys',
        }.get(type(node), '?')
        params.append(f'{prefix}.{name}')
    elif isinstance(node, (BinOpNode, CompareNode)):
        params += _collect_params(node.left)
        if hasattr(node, 'right') and node.right is not None:
            params += _collect_params(node.right)
    elif isinstance(node, UnaryOpNode):
        params += _collect_params(node.operand)
    elif isinstance(node, FuncCallNode):
        for arg in node.args:
            params += _collect_params(arg)

    return params
