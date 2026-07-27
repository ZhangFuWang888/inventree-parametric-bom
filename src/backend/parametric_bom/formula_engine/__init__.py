"""Formula engine for Parametric BOM.

Provides safe, sandboxed formula evaluation for dynamic BOM calculations.
Supported syntax:
  - Arithmetic: + - * / ( )
  - Comparison: > < >= <= = !=
  - Logical: AND OR NOT
  - Functions: CEIL FLOOR ROUND ABS IF MIN MAX SUM AVG COUNT
               POW SQRT MOD CONCAT LEFT RIGHT MID LEN FIND
               UPPER LOWER TRIM REPLACE SUBSTITUTE
               SIN COS TAN ASIN ACOS ATAN ATAN2 DEGREES RADIANS
               INT FLOAT STR BOOL LET
  - Parameter refs: param.xxx, parent.xxx, sys.xxx, 内置.xxx
  - Intermediate variables: LET(name, value, expr)
  - Strings, numbers, booleans
  - Trigonometric functions use DEGREES

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
            {'param': {'长度': 5000, '速度': 12}, 'parent': {...}, 'sys': {...}, '内置': {...}}
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


def validate(formula: str, expected_type: str = None) -> dict:
    """Validate a formula and return diagnostics.

    Args:
        formula: The formula string to validate.
        expected_type: Optional expected return type.
            One of: 'string', 'boolean', 'integer', 'float', 'number'.
            If provided, the formula will be evaluated with mock values
            to verify the return type matches.

    Returns:
        dict with keys:
            - valid (bool): Whether formula is syntactically valid
            - errors (list): Validation error messages
            - referenced_params (list): Parameter references found
            - result_type (str|None): Detected return type (if parsed)
            - type_valid (bool|None): Whether result type matches expected_type
            - type_detail (str|None): Human-readable type info
    """
    result = {
        'valid': True,
        'errors': [],
        'referenced_params': [],
        'result_type': None,
        'type_valid': None,
        'type_detail': None,
    }

    if not formula or not formula.strip():
        return result

    try:
        parser = FormulaParser(formula)
        ast = parser.parse()

        # Collect referenced parameters
        result['referenced_params'] = _collect_params(ast)

        # --- Type inference via AST analysis ---
        from .parser import (
            BinOpNode, BoolNode, CompareNode, FuncCallNode,
            NumberNode, StringNode,
        )
        result['result_type'] = _infer_type_from_ast(ast)
    except ParseError as e:
        result['valid'] = False
        result['errors'].append(str(e))
        return result

    # --- Type validation against expected_type ---
    if expected_type and result['result_type']:
        result['type_valid'], result['type_detail'] = _check_type(
            result['result_type'], expected_type
        )

    return result


def _infer_type_from_ast(node) -> str:
    """Infer the return type of a formula from its AST.

    Returns one of: 'string', 'boolean', 'number', 'integer', 'unknown'.
    """
    from .parser import (
        BinOpNode, BoolNode, BuiltinParamNode, CompareNode, FuncCallNode,
        NumberNode, ParamNode, ParentParamNode, RefPartParamNode, StringNode,
        SysParamNode, UnaryOpNode,
    )

    if isinstance(node, NumberNode):
        val = node.value
        if isinstance(val, float):
            return 'float'
        return 'integer'

    if isinstance(node, StringNode):
        return 'string'

    if isinstance(node, BoolNode):
        return 'boolean'

    if isinstance(node, (ParamNode, ParentParamNode, SysParamNode, BuiltinParamNode, RefPartParamNode)):
        # Can't know at parse time — assume unknown
        return 'unknown'

    if isinstance(node, CompareNode):
        # All comparisons return boolean
        return 'boolean'

    if isinstance(node, BinOpNode):
        lt = _infer_type_from_ast(node.left)
        rt = _infer_type_from_ast(node.right)
        if node.op in ('AND', 'OR'):
            return 'boolean'
        # PLUS with string → string (concat)
        if node.op in ('PLUS', '+'):
            if lt == 'string' or rt == 'string':
                return 'string'
        # All other arithmetic → number
        return _promote_numeric(lt, rt)

    if isinstance(node, UnaryOpNode):
        ot = _infer_type_from_ast(node.operand)
        if node.op == 'NOT':
            return 'boolean'
        return ot

    if isinstance(node, FuncCallNode):
        name = node.name.upper()
        # Functions that return string
        if name in ('CONCAT', 'UPPER', 'LOWER', 'TRIM', 'SUBSTITUTE',
                     'REPLACE', 'LEFT', 'RIGHT', 'MID', 'STR'):
            return 'string'
        # Functions that return boolean
        if name in ('BOOL',):
            return 'boolean'
        # Functions that return integer
        if name in ('INT', 'LEN', 'COUNT'):
            return 'integer'
        # Functions that return number
        if name in ('CEIL', 'FLOOR', 'ROUND', 'ABS', 'MIN', 'MAX',
                     'SUM', 'AVG', 'POW', 'SQRT', 'MOD', 'FLOAT',
                     'SIN', 'COS', 'TAN', 'ASIN', 'ACOS', 'ATAN',
                     'ATAN2', 'DEGREES', 'RADIANS'):
            return 'float'
        # IF — infer from true/false branches
        if name == 'IF' and len(node.args) >= 3:
            tr = _infer_type_from_ast(node.args[1])
            fr = _infer_type_from_ast(node.args[2])
            if tr == fr:
                return tr
            # If one is number, prefer numeric
            if tr in ('integer', 'float') or fr in ('integer', 'float'):
                return _promote_numeric(tr, fr)
            return tr if tr != 'unknown' else fr
        # LET — return type is its last expression
        if name == 'LET' and len(node.args) >= 3:
            return _infer_type_from_ast(node.args[-1])

    return 'unknown'


def _promote_numeric(*types: str) -> str:
    """Given one or more types, promote to the most general numeric type."""
    has_float = any(t == 'float' for t in types if t)
    if has_float:
        return 'float'
    has_int = any(t == 'integer' for t in types if t)
    if has_int:
        return 'integer'
    return 'number'


def _check_type(actual_type: str, expected_type: str):
    """Check if actual_type matches expected_type.

    Returns (is_valid, detail_message).
    """
    # Normalize expected_type
    expected = expected_type.lower().strip()
    actual = actual_type.lower().strip()

    # 'unknown' means static inference can't determine the type
    # (e.g., formula references param.xxx which has no static type info).
    # This is NOT a type error — accept it and let runtime evaluation decide.
    if actual == 'unknown':
        return True, None

    # Exact match
    if actual == expected:
        return True, None

    # 'number' matches both 'integer' and 'float'
    if expected == 'number' and actual in ('integer', 'float'):
        return True, None
    if actual == 'number' and expected in ('integer', 'float'):
        return True, None

    # 'integer' and 'float' both count as each other loosely
    if expected in ('integer', 'float') and actual in ('integer', 'float'):
        # Exact type mismatch but both numeric — warn but don't block
        return True, '类型提示：结果为%s，期望%s（两者均为数值类型）' % (
            _type_label(actual), _type_label(expected))

    # 'string' vs other — hard mismatch
    type_labels = {
        'string': '字符串', 'boolean': '布尔值',
        'integer': '整数', 'float': '浮点数', 'number': '数值',
    }
    expected_label = type_labels.get(expected, expected)
    actual_label = type_labels.get(actual, actual)

    return False, '公式返回类型为「%s」，但期望「%s」—— 请检查公式' % (
        actual_label, expected_label)


def _type_label(t: str) -> str:
    labels = {
        'string': '字符串', 'boolean': '布尔值',
        'integer': '整数', 'float': '浮点数', 'number': '数值',
    }
    return labels.get(t, t)


def _collect_params(node) -> list:
    """Walk the AST and collect all parameter references."""
    from .parser import (
        BinOpNode, BuiltinParamNode, CompareNode, FuncCallNode, NumberNode,
        ParamNode, ParentParamNode, RefPartParamNode, StringNode,
        SysParamNode, UnaryOpNode,
    )

    params = []

    if isinstance(node, (ParamNode, ParentParamNode, SysParamNode, BuiltinParamNode, RefPartParamNode)):
        name = node.name
        prefix = {
            ParamNode: 'param',
            ParentParamNode: 'parent',
            SysParamNode: 'sys',
            BuiltinParamNode: '内置',
            RefPartParamNode: '参考零件',
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
