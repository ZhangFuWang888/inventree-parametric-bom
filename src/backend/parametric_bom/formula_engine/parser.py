"""Tokenizer and recursive-descent parser for parametric BOM formulas.

Grammar:
    expression     → logical_or
    logical_or     → logical_and ( ("OR") logical_and )*
    logical_and    → comparison ( ("AND") comparison )*
    comparison     → addition ( (">" | "<" | ">=" | "<=" | "=" | "!=") addition )?
    addition       → multiplication ( ("+" | "-") multiplication )*
    multiplication → unary ( ("*" | "/") unary )*
    unary          → ("-" | "NOT") unary | primary
    primary        → NUMBER | STRING | BOOL | "(" expression ")" | func_call | param_ref
    func_call      → IDENTIFIER "(" expression ("," expression)* ")"
    param_ref      → ("param" | "parent" | "sys") "." IDENTIFIER
"""

import re
from typing import Any, Optional

from .errors import ParseError

# ──────────────────────────────────────────────
#  Token types
# ──────────────────────────────────────────────

NUMBER = 'NUMBER'
STRING = 'STRING'
BOOL = 'BOOL'
IDENTIFIER = 'IDENTIFIER'
DOT = 'DOT'
LPAREN = 'LPAREN'
RPAREN = 'RPAREN'
COMMA = 'COMMA'
PLUS = 'PLUS'
MINUS = 'MINUS'
STAR = 'STAR'
SLASH = 'SLASH'
GT = 'GT'
LT = 'LT'
GTE = 'GTE'
LTE = 'LTE'
EQ = 'EQ'
NEQ = 'NEQ'
EOF = 'EOF'

# ──────────────────────────────────────────────
#  Token
# ──────────────────────────────────────────────


class Token:
    """A single token from the formula source."""

    __slots__ = ('type', 'value', 'pos')

    def __init__(self, type_: str, value: Any, pos: int):
        self.type = type_
        self.value = value
        self.pos = pos

    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, pos={self.pos})'


# ──────────────────────────────────────────────
#  AST Nodes
# ──────────────────────────────────────────────


class NumberNode:
    __slots__ = ('value',)

    def __init__(self, value: float):
        self.value = value

    def __repr__(self):
        return f'Number({self.value})'


class StringNode:
    __slots__ = ('value',)

    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f'String({self.value!r})'


class BoolNode:
    __slots__ = ('value',)

    def __init__(self, value: bool):
        self.value = value

    def __repr__(self):
        return f'Bool({self.value})'


class ParamNode:
    """Reference to a parameter in the current level."""

    __slots__ = ('name',)

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f'Param({self.name})'


class ParentParamNode:
    """Reference to a parameter in the parent BOM level."""

    __slots__ = ('name',)

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f'ParentParam({self.name})'


class SysParamNode:
    """Reference to a system variable (e.g., sys.quantity, sys.level)."""

    __slots__ = ('name',)

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f'SysParam({self.name})'


class BinOpNode:
    """Binary operation like a + b, a * b, etc."""

    __slots__ = ('left', 'op', 'right')

    def __init__(self, left, op: str, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f'({self.left} {self.op} {self.right})'


class CompareNode:
    """Comparison operation like a > b, a = b, etc."""

    __slots__ = ('left', 'op', 'right')

    def __init__(self, left, op: str, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f'({self.left} {self.op} {self.right})'


class UnaryOpNode:
    """Unary operation like -x or NOT x."""

    __slots__ = ('op', 'operand')

    def __init__(self, op: str, operand):
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f'({self.op}{self.operand})'


class FuncCallNode:
    """Function call like CEIL(x), IF(cond, a, b), etc."""

    __slots__ = ('name', 'args')

    def __init__(self, name: str, args: list):
        self.name = name
        self.args = args

    def __repr__(self):
        return f'{self.name}({", ".join(repr(a) for a in self.args)})'


# ──────────────────────────────────────────────
#  Tokenizer
# ──────────────────────────────────────────────

_TOKEN_SPEC = [
    (r'\s+', None),  # skip whitespace
    (r'>=', GTE),
    (r'<=', LTE),
    (r'!=', NEQ),
    (r'=', EQ),
    (r'>', GT),
    (r'<', LT),
    (r'\+', PLUS),
    (r'-', MINUS),
    (r'\*', STAR),
    (r'/', SLASH),
    (r'\(', LPAREN),
    (r'\)', RPAREN),
    (r',', COMMA),
    (r'\.', DOT),
    (r"'[^']*'|\"[^\"]*\"", STRING),
    (r'\d+\.?\d*', NUMBER),
    (r'[A-Za-z_\u4e00-\u9fff][A-Za-z0-9_\u4e00-\u9fff]*', IDENTIFIER),
]

TOKEN_REGEX = re.compile('|'.join(f'(?P<{name}>{pattern})' for pattern, name in _TOKEN_SPEC if name))

KEYWORDS = {
    'TRUE': BOOL,
    'FALSE': BOOL,
}

# Identifiers that are treated as parameter/system prefixes
PARAM_PREFIXES = {'param', 'parent', 'sys'}


def tokenize(source: str) -> list[Token]:
    """Convert formula string into a list of tokens."""
    tokens = []
    pos = 0

    for match in re.finditer(TOKEN_REGEX, source):
        kind = match.lastgroup
        value = match.group()

        if kind == 'IDENTIFIER':
            # Check if it's a keyword
            upper = value.upper()
            if upper in KEYWORDS:
                token_type = KEYWORDS[upper]
                if token_type == BOOL:
                    value = upper == 'TRUE'
                tokens.append(Token(token_type, value, match.start()))
            else:
                tokens.append(Token(IDENTIFIER, value, match.start()))
        elif kind == 'STRING':
            # Strip quotes and unescape
            value = value[1:-1].replace('\\"', '"').replace("\\'", "'")
            tokens.append(Token(STRING, value, match.start()))
        elif kind == 'NUMBER':
            tokens.append(Token(NUMBER, float(value), match.start()))
        else:
            # Default: use the group name as token type
            tokens.append(Token(kind, value, match.start()))

    tokens.append(Token(EOF, None, len(source)))
    return tokens


# ──────────────────────────────────────────────
#  Parser (Recursive Descent)
# ──────────────────────────────────────────────


class FormulaParser:
    """Recursive-descent parser for parametric BOM formulas."""

    def __init__(self, source: str):
        self.source = source
        self.tokens = tokenize(source)
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _expect(self, *types: str) -> Token:
        token = self._peek()
        if token.type not in types:
            expected = ' or '.join(types)
            got = repr(token.value)
            raise ParseError(
                f'Expected {expected} at position {token.pos}, got {got}'
            )
        return self._advance()

    def _check(self, *types: str) -> bool:
        return self._peek().type in types

    def parse(self):
        """Parse the full formula string."""
        result = self._expression()
        if self._peek().type != EOF:
            token = self._peek()
            raise ParseError(
                f'Unexpected token {token.value!r} at position {token.pos}'
            )
        return result

    # ── expression → logical_or ──

    def _expression(self):
        return self._logical_or()

    # ── logical_or → logical_and ( "OR" logical_and )* ──

    def _logical_or(self):
        left = self._logical_and()
        while self._check(IDENTIFIER) and self._peek().value.upper() == 'OR':
            self._advance()
            right = self._logical_and()
            left = BinOpNode(left, 'OR', right)
        return left

    # ── logical_and → comparison ( "AND" comparison )* ──

    def _logical_and(self):
        left = self._comparison()
        while self._check(IDENTIFIER) and self._peek().value.upper() == 'AND':
            self._advance()
            right = self._comparison()
            left = BinOpNode(left, 'AND', right)
        return left

    # ── comparison → addition ( (">" | "<" | ">=" | "<=" | "=" | "!=") addition )? ──

    def _comparison(self):
        left = self._addition()
        if self._check(GT, LT, GTE, LTE, EQ, NEQ):
            op = self._advance()
            right = self._addition()
            return CompareNode(left, op.type, right)
        return left

    # ── addition → multiplication ( ("+" | "-") multiplication )* ──

    def _addition(self):
        left = self._multiplication()
        while self._check(PLUS, MINUS):
            op = self._advance()
            right = self._multiplication()
            left = BinOpNode(left, op.type, right)
        return left

    # ── multiplication → unary ( ("*" | "/") unary )* ──

    def _multiplication(self):
        left = self._unary()
        while self._check(STAR, SLASH):
            op = self._advance()
            right = self._unary()
            left = BinOpNode(left, op.type, right)
        return left

    # ── unary → ("-" | "NOT") unary | primary ──

    def _unary(self):
        if self._check(MINUS):
            op = self._advance()
            operand = self._unary()
            return UnaryOpNode('-', operand)
        if self._check(IDENTIFIER) and self._peek().value.upper() == 'NOT':
            op = self._advance()
            operand = self._unary()
            return UnaryOpNode('NOT', operand)
        return self._primary()

    # ── primary ──

    def _primary(self):
        token = self._peek()

        # Literal values
        if token.type == NUMBER:
            self._advance()
            return NumberNode(token.value)

        if token.type == STRING:
            self._advance()
            return StringNode(token.value)

        if token.type == BOOL:
            self._advance()
            return BoolNode(token.value)

        # Parenthesized expression
        if token.type == LPAREN:
            self._advance()
            expr = self._expression()
            self._expect(RPAREN)
            return expr

        # Parameter reference: param.xxx, parent.xxx, sys.xxx
        if token.type == IDENTIFIER and token.value.lower() in PARAM_PREFIXES:
            prefix = self._advance().value.lower()
            self._expect(DOT)
            name_token = self._expect(IDENTIFIER)
            name = name_token.value

            prefix_map = {
                'param': ParamNode,
                'parent': ParentParamNode,
                'sys': SysParamNode,
            }
            return prefix_map[prefix](name)

        # Function call: IDENTIFIER(...)
        if token.type == IDENTIFIER:
            name = self._advance().value
            self._expect(LPAREN)
            args = []
            if not self._check(RPAREN):
                args.append(self._expression())
                while self._check(COMMA):
                    self._advance()
                    args.append(self._expression())
            self._expect(RPAREN)
            return FuncCallNode(name.upper(), args)

        raise ParseError(
            f'Unexpected token {token.value!r} at position {token.pos}'
        )
