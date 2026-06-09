"""AST evaluator for the formula engine.

Walks the AST produced by the parser and computes the final value.
Enforces safety: timeout, recursion limit, no Python builtins.
"""

import signal
import threading
from typing import Any, Optional

from .errors import EvaluationError, ReferenceError, TimeoutError
from .functions import get_function
from .parser import (
    BinOpNode,
    BoolNode,
    CompareNode,
    FuncCallNode,
    NumberNode,
    ParamNode,
    ParentParamNode,
    StringNode,
    SysParamNode,
    UnaryOpNode,
)


class FormulaEvaluator:
    """Evaluates a formula AST against a given context.

    Args:
        context: Dict with 'param', 'parent', 'sys' namespaces.
        timeout_ms: Max evaluation time in milliseconds.
        max_recursion: Max recursion depth.
    """

    def __init__(
        self,
        context: dict,
        timeout_ms: int = 500,
        max_recursion: int = 20,
    ):
        self.context = context
        self.timeout_ms = timeout_ms
        self.max_recursion = max_recursion
        self._depth = 0

    def evaluate(self, node) -> Any:
        """Evaluate a single AST node, with timeout protection."""

        # Check recursion depth
        self._depth += 1
        if self._depth > self.max_recursion:
            self._depth -= 1
            raise EvaluationError(
                f'Max recursion depth ({self.max_recursion}) exceeded'
            )

        try:
            if self.timeout_ms > 0:
                result = self._evaluate_with_timeout(node)
            else:
                result = self._eval_node(node)
            return result
        finally:
            self._depth -= 1

    def _evaluate_with_timeout(self, node) -> Any:
        """Evaluate with signal-based timeout."""

        # Use threading timer for cross-platform timeout
        result = [None]
        exception = [None]
        event = threading.Event()

        def worker():
            try:
                result[0] = self._eval_node(node)
            except Exception as e:
                exception[0] = e
            finally:
                event.set()

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        if not event.wait(timeout=self.timeout_ms / 1000.0):
            raise TimeoutError(
                f'Formula evaluation exceeded {self.timeout_ms}ms timeout'
            )

        if exception[0]:
            raise exception[0]

        return result[0]

    def _eval_node(self, node) -> Any:
        """Dispatch to the appropriate evaluation method based on node type."""

        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, StringNode):
            return node.value

        if isinstance(node, BoolNode):
            return node.value

        if isinstance(node, ParamNode):
            return self._resolve_param('param', node.name)

        if isinstance(node, ParentParamNode):
            return self._resolve_param('parent', node.name)

        if isinstance(node, SysParamNode):
            return self._resolve_sys(node.name)

        if isinstance(node, BinOpNode):
            return self._eval_binop(node)

        if isinstance(node, CompareNode):
            return self._eval_compare(node)

        if isinstance(node, UnaryOpNode):
            return self._eval_unary(node)

        if isinstance(node, FuncCallNode):
            return self._eval_func(node)

        raise EvaluationError(f'Unknown AST node type: {type(node).__name__}')

    def _resolve_param(self, namespace: str, name: str) -> Any:
        """Resolve a parameter reference from the context."""
        ns = self.context.get(namespace, {})
        if name not in ns:
            raise ReferenceError(
                f"Parameter '{namespace}.{name}' not found in context"
            )
        val = ns[name]
        # Try numeric conversion for string values that look like numbers
        if isinstance(val, str):
            try:
                return float(val)
            except ValueError:
                return val
        return val

    def _resolve_sys(self, name: str) -> Any:
        """Resolve a system variable."""
        sys_vars = self.context.get('sys', {})
        if name in sys_vars:
            return sys_vars[name]

        # Default system variables
        defaults = {
            'quantity': 1,
            'level': 0,
            'pi': 3.141592653589793,
        }
        if name in defaults:
            return defaults[name]

        raise ReferenceError(f"System variable 'sys.{name}' not found")

    def _eval_binop(self, node: BinOpNode) -> Any:
        """Evaluate binary operations."""
        left = self._eval_node(node.left)
        right = self._eval_node(node.right)

        if node.op in ('AND', 'OR'):
            left_bool = bool(left)
            right_bool = bool(right)
            if node.op == 'AND':
                return left_bool and right_bool
            return left_bool or right_bool

        # Arithmetic — coerce to numeric
        left_num = self._to_number(left)
        right_num = self._to_number(right)

        if node.op == 'PLUS' or node.op == '+':
            return left_num + right_num
        elif node.op == 'MINUS' or node.op == '-':
            return left_num - right_num
        elif node.op == 'STAR' or node.op == '*':
            return left_num * right_num
        elif node.op == 'SLASH' or node.op == '/':
            if right_num == 0:
                raise EvaluationError('Division by zero')
            return left_num / right_num

        raise EvaluationError(f'Unknown binary operator: {node.op}')

    def _eval_compare(self, node: CompareNode) -> bool:
        """Evaluate comparison operations."""
        left = self._eval_node(node.left)
        right = self._eval_node(node.right)

        # Coerce to same type for comparison
        if isinstance(left, (int, float)) and isinstance(right, str):
            right = self._to_number(right)
        elif isinstance(left, str) and isinstance(right, (int, float)):
            left = self._to_number(left)

        if node.op == 'GT' or node.op == '>':
            return left > right
        elif node.op == 'LT' or node.op == '<':
            return left < right
        elif node.op == 'GTE' or node.op == '>=':
            return left >= right
        elif node.op == 'LTE' or node.op == '<=':
            return left <= right
        elif node.op == 'EQ' or node.op == '=':
            return left == right
        elif node.op == 'NEQ' or node.op == '!=':
            return left != right

        raise EvaluationError(f'Unknown comparison operator: {node.op}')

    def _eval_unary(self, node: UnaryOpNode) -> Any:
        """Evaluate unary operations."""
        operand = self._eval_node(node.operand)

        if node.op == '-':
            return -self._to_number(operand)
        elif node.op == 'NOT':
            return not bool(operand)

        raise EvaluationError(f'Unknown unary operator: {node.op}')

    def _eval_func(self, node: FuncCallNode) -> Any:
        """Evaluate a function call."""
        try:
            fn_def = get_function(node.name)
        except ValueError as e:
            raise EvaluationError(str(e))

        # Validate argument count
        if len(node.args) < fn_def.min_args:
            raise EvaluationError(
                f"Function '{node.name}' requires at least {fn_def.min_args} arguments, "
                f"got {len(node.args)}"
            )
        if len(node.args) > fn_def.max_args:
            raise EvaluationError(
                f"Function '{node.name}' accepts at most {fn_def.max_args} arguments, "
                f"got {len(node.args)}"
            )

        # Evaluate all arguments
        evaluated_args = [self._eval_node(arg) for arg in node.args]

        # Call the function
        try:
            return fn_def.fn(*evaluated_args)
        except (TypeError, ValueError) as e:
            raise EvaluationError(
                f"Error in function '{node.name}': {e}"
            )

    @staticmethod
    def _to_number(value) -> float:
        """Coerce a value to a number."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                raise EvaluationError(f'Cannot convert string {value!r} to number')
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        raise EvaluationError(f'Cannot convert {type(value).__name__} to number')
