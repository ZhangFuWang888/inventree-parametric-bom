"""Tests for the formula engine.

Run with: venv/bin/python -m pytest parametric_bom/tests/test_formula_engine.py -v
"""

from parametric_bom.formula_engine import evaluate, validate, FormulaParser, ParseError

# ──────────────────────────────────────────────
#  Parser tests
# ──────────────────────────────────────────────


def test_parse_number():
    """Simple number parsing."""
    parser = FormulaParser('42')
    ast = parser.parse()
    assert repr(ast) == 'Number(42.0)'


def test_parse_string():
    """String literal parsing."""
    parser = FormulaParser('"hello"')
    ast = parser.parse()
    assert repr(ast) == "String('hello')"


def test_parse_string_single_quotes():
    parser = FormulaParser("'world'")
    ast = parser.parse()
    assert repr(ast) == "String('world')"


def test_parse_bool():
    parser = FormulaParser('TRUE')
    ast = parser.parse()
    assert repr(ast) == 'Bool(True)'

    parser = FormulaParser('FALSE')
    ast = parser.parse()
    assert repr(ast) == 'Bool(False)'


def test_parse_param():
    """Parameter reference parsing."""
    parser = FormulaParser('param.长度')
    ast = parser.parse()
    assert repr(ast) == 'Param(长度)'


def test_parse_parent_param():
    parser = FormulaParser('parent.宽度')
    ast = parser.parse()
    assert repr(ast) == 'ParentParam(宽度)'


def test_parse_sys_param():
    parser = FormulaParser('sys.quantity')
    ast = parser.parse()
    assert repr(ast) == 'SysParam(quantity)'


def test_parse_arithmetic():
    parser = FormulaParser('param.长度 / 500')
    ast = parser.parse()
    assert 'Param' in repr(ast) or '/' in repr(ast)

    parser = FormulaParser('(a + b) * 2')
    ast = parser.parse()


def test_parse_func_call():
    parser = FormulaParser('CEIL(x / 500)')
    ast = parser.parse()
    assert 'CEIL' in repr(ast)


def test_parse_if():
    parser = FormulaParser('IF(param.速度 > 15, 1, 0)')
    ast = parser.parse()
    assert 'IF' in repr(ast)


def test_parse_complex():
    """A realistic parametric BOM formula."""
    formula = 'CEIL(param.长度 / 500) * 2 + IF(param.速度 > 15, param.长度 * 0.02, 0)'
    parser = FormulaParser(formula)
    ast = parser.parse()
    assert ast is not None


def test_parse_error_unclosed_paren():
    import pytest
    with pytest.raises(ParseError):
        parser = FormulaParser('(1 + 2')
        parser.parse()


def test_parse_error_trailing_garbage():
    import pytest
    with pytest.raises(ParseError):
        parser = FormulaParser('1 + 2 extra')


# ──────────────────────────────────────────────
#  Evaluation tests
# ──────────────────────────────────────────────


def test_eval_simple_arithmetic():
    result = evaluate('2 + 3 * 4', context={})
    assert result == 14.0


def test_eval_parens():
    result = evaluate('(2 + 3) * 4', context={})
    assert result == 20.0


def test_eval_param_ref():
    context = {'param': {'长度': 5000}}
    result = evaluate('param.长度 / 1000', context)
    assert result == 5.0


def test_eval_ceil():
    result = evaluate('CEIL(5000 / 300)', context={})
    assert result == 17  # 5000/300 = 16.666..., CEIL = 17


def test_eval_floor():
    result = evaluate('FLOOR(5000 / 300)', context={})
    assert result == 16


def test_eval_if_true():
    result = evaluate('IF(5 > 3, 100, 200)', context={})
    assert result == 100


def test_eval_if_false():
    result = evaluate('IF(1 > 2, 100, 200)', context={})
    assert result == 200


def test_eval_and():
    result = evaluate('AND(1, 1)', context={})
    assert result is True

    result = evaluate('AND(1, 0)', context={})
    assert result is False


def test_eval_or():
    result = evaluate('OR(0, 1)', context={})
    assert result is True

    result = evaluate('OR(0, 0)', context={})
    assert result is False


def test_eval_not():
    result = evaluate('NOT(TRUE)', context={})
    assert result is False

    result = evaluate('NOT(FALSE)', context={})
    assert result is True


def test_eval_min_max():
    result = evaluate('MIN(10, 20, 5, 30)', context={})
    assert result == 5.0

    result = evaluate('MAX(10, 20, 5, 30)', context={})
    assert result == 30.0


def test_eval_comparison_gt():
    result = evaluate('5 > 3', context={})
    assert result is True

    result = evaluate('3 > 5', context={})
    assert result is False


def test_eval_comparison_eq():
    result = evaluate('5 = 5', context={})
    assert result is True

    result = evaluate('5 = 6', context={})
    assert result is False


def test_eval_abs():
    result = evaluate('ABS(-10)', context={})
    assert result == 10.0


def test_eval_realistic():
    """Real-world scenario: bolt quantity calculation."""
    context = {'param': {'长度': 5000, '间距': 500}}
    result = evaluate('CEIL(param.长度 / param.间距) * 2', context)
    # 5000/500 = 10, CEIL=10, *2 = 20
    assert result == 20.0


def test_eval_realistic_with_condition():
    """Real-world: protective cover material length."""
    context = {'param': {'速度': 12, '长度': 5000}}
    result = evaluate('IF(param.速度 > 15, param.长度 * 0.02, 0)', context)
    # 12 > 15 = false, so 0
    assert result == 0

    context['param']['速度'] = 20
    result = evaluate('IF(param.速度 > 15, param.长度 * 0.02, 0)', context)
    # 20 > 15 = true, so 5000 * 0.02 = 100
    assert result == 100.0


def test_eval_sys_variable():
    context = {'sys': {'quantity': 1}}
    result = evaluate('sys.quantity * 2', context)
    assert result == 2.0


def test_eval_string_concat():
    result = evaluate('"hello" + " world"', context={})
    # String concatenation via + 
    assert result == "hello world"


def test_eval_sum():
    result = evaluate('SUM(1, 2, 3, 4, 5)', context={})
    assert result == 15.0


def test_eval_avg():
    result = evaluate('AVG(10, 20, 30)', context={})
    assert result == 20.0


def test_eval_sqrt():
    result = evaluate('SQRT(25)', context={})
    assert result == 5.0


def test_eval_pow():
    result = evaluate('POW(2, 3)', context={})
    assert result == 8.0


def test_eval_mod():
    result = evaluate('MOD(10, 3)', context={})
    assert result == 1.0


def test_eval_division_by_zero():
    import pytest
    from parametric_bom.formula_engine import EvaluationError
    with pytest.raises(EvaluationError, match='Division by zero'):
        evaluate('10 / 0', context={})


def test_eval_ref_not_found():
    import pytest
    from parametric_bom.formula_engine import ReferenceError
    with pytest.raises(ReferenceError):
        evaluate('param.不存在的参数', context={'param': {}})


def test_eval_timeout():
    """Timeout protection - a deeply nested recursion."""
    import pytest
    from parametric_bom.formula_engine import TimeoutError
    # Slow formula — impossible by pure arithmetic, but let's ensure timeout works
    context = {'param': {'x': 1}}
    with pytest.raises(TimeoutError):
        # This shouldn't timeout for simple arithmetic, but just verify the mechanism
        evaluate('param.x + 1', context, timeout_ms=1)


# ──────────────────────────────────────────────
#  Validation API tests
# ──────────────────────────────────────────────


def test_validate_valid():
    result = validate('CEIL(param.长度 / 500) * 2')
    assert result['valid'] is True
    assert len(result['errors']) == 0


def test_validate_invalid():
    result = validate('CEIL(param.长度 / (500')  # unmatched paren
    assert result['valid'] is False
    assert len(result['errors']) > 0


def test_validate_empty():
    result = validate('')
    assert result['valid'] is True


def test_validate_whitespace():
    result = validate('   ')
    assert result['valid'] is True


def test_validate_collects_params():
    result = validate('CEIL(param.长度 / 500) + parent.宽度')
    assert result['valid']
    assert 'param.长度' in result['referenced_params']
    assert 'parent.宽度' in result['referenced_params']
