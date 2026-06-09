"""Tests for the Rule Engine Service.

Tests the core functions in rule_engine.py:
  - evaluate_rules()
  - evaluate_config_rules()
  - _coerce_param_value()
  - Action implementations: SET_VALUE, SET_MIN, SET_MAX, SHOW, HIDE, REQUIRE

Run with:
  SKIP_MIGRATIONS=1 DJANGO_SETTINGS_MODULE=InvenTree.settings \
    venv/bin/python -m pytest parametric_bom/tests/test_rule_engine.py -v

All tests use unittest.TestCase (not django.test.TestCase) because all
Django model queries are mocked. No database access is required.
"""

from unittest import TestCase, mock


class MockParameterTemplate:
    """Minimal mock for ParameterTemplate (only needs .name .pk)."""

    def __init__(self, name, pk=1):
        self.name = name
        self.pk = pk


class MockPart:
    """Minimal mock for Part."""

    def __init__(self, name='TestPart', pk=1):
        self.pk = pk
        self.name = name


class MockParametricRule:
    """Minimal mock for ParametricRule.

    Fields accessed in evaluate_rules / _evaluate_single_rule:
      - pk
      - product_part
      - enabled
      - condition_formula
      - target_param (FK -> ParameterTemplate)
      - action
      - value_formula
      - error_message
      - priority
      - get_rule_type_display()
    """

    def __init__(self, pk=1, condition_formula='', target_param=None,
                 action='set_value', value_formula='', error_message='',
                 priority=100, rule_type='constraint'):
        self.pk = pk
        self.condition_formula = condition_formula
        self.target_param = target_param
        self.action = action
        self.value_formula = value_formula
        self.error_message = error_message
        self.priority = priority
        self.rule_type = rule_type
        self.enabled = True

    def get_rule_type_display(self):
        return self.rule_type.capitalize()


# ══════════════════════════════════════════════
#  Tests for _coerce_param_value
# ══════════════════════════════════════════════


class TestCoerceParamValue(TestCase):
    """Tests for the _coerce_param_value helper."""

    def test_none(self):
        from parametric_bom.rule_engine import _coerce_param_value
        self.assertIsNone(_coerce_param_value(None))

    def test_int_float_bool_passthrough(self):
        from parametric_bom.rule_engine import _coerce_param_value
        self.assertEqual(_coerce_param_value(42), 42)
        self.assertEqual(_coerce_param_value(3.14), 3.14)
        self.assertEqual(_coerce_param_value(True), True)
        self.assertEqual(_coerce_param_value(False), False)

    def test_coerce_int_string(self):
        from parametric_bom.rule_engine import _coerce_param_value
        self.assertEqual(_coerce_param_value('42'), 42)
        self.assertEqual(_coerce_param_value('-5'), -5)

    def test_coerce_float_string(self):
        from parametric_bom.rule_engine import _coerce_param_value
        self.assertEqual(_coerce_param_value('3.14'), 3.14)

    def test_coerce_bool_string(self):
        from parametric_bom.rule_engine import _coerce_param_value
        self.assertEqual(_coerce_param_value('true'), True)
        self.assertEqual(_coerce_param_value('TRUE'), True)
        self.assertEqual(_coerce_param_value('yes'), True)
        self.assertEqual(_coerce_param_value('1'), True)
        self.assertEqual(_coerce_param_value('false'), False)
        self.assertEqual(_coerce_param_value('FALSE'), False)
        self.assertEqual(_coerce_param_value('no'), False)
        self.assertEqual(_coerce_param_value('0'), False)

    def test_empty_string_returns_none(self):
        from parametric_bom.rule_engine import _coerce_param_value
        self.assertIsNone(_coerce_param_value(''))
        self.assertIsNone(_coerce_param_value('   '))

    def test_plain_string_passthrough(self):
        from parametric_bom.rule_engine import _coerce_param_value
        self.assertEqual(_coerce_param_value('hello'), 'hello')
        self.assertEqual(_coerce_param_value('abc-def'), 'abc-def')


# ══════════════════════════════════════════════
#  Tests for evaluate_rules
# ══════════════════════════════════════════════


class TestEvaluateRules(TestCase):
    """Tests for the evaluate_rules() function."""

    @staticmethod
    def _make_rule_queryset(rules, exists=True):
        """Create a mock QuerySet chain for ParametricRule.objects.filter().

        The chain .filter().select_related().order_by() all return the same
        mock queryset, and iterating yields the provided rules list.
        """
        mock_qs = mock.MagicMock()
        mock_qs.exists.return_value = exists
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.__iter__.return_value = iter(rules)
        return mock_qs

    @mock.patch('parametric_bom.models.ParametricRule')
    def test_no_rules_returns_empty(self, mock_rule_cls):
        """Test with no rules configured."""
        mock_part = MockPart('Product', pk=1)
        mock_qs = self._make_rule_queryset([], exists=False)
        mock_rule_cls.objects.filter.return_value = mock_qs

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {'speed': 10})

        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(result['param_overrides'], {})
        self.assertEqual(result['param_visibility'], {})

    @mock.patch('parametric_bom.models.ParametricRule')
    @mock.patch('parametric_bom.rule_engine._evaluate_single_rule')
    def test_rules_evaluated_in_priority_order(self, mock_eval_single, mock_rule_cls):
        """Test that rules are evaluated in priority order and overrides accumulate."""
        mock_part = MockPart('Product', pk=1)
        mock_target = MockParameterTemplate('length')
        rule1 = MockParametricRule(pk=1, condition_formula='', target_param=mock_target,
                                   action='set_value', value_formula='100', priority=50)
        rule2 = MockParametricRule(pk=2, condition_formula='', target_param=mock_target,
                                   action='set_value', value_formula='200', priority=100)

        mock_qs = self._make_rule_queryset([rule1, rule2])
        mock_rule_cls.objects.filter.return_value = mock_qs

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {'speed': 10})

        self.assertEqual(mock_eval_single.call_count, 2)

    @mock.patch('parametric_bom.models.ParametricRule')
    @mock.patch('parametric_bom.formula_engine.evaluate')
    def test_set_value_action(self, mock_eval, mock_rule_cls):
        """Test SET_VALUE action overrides param."""
        mock_part = MockPart('Product', pk=1)
        mock_target = MockParameterTemplate('length')
        rule = MockParametricRule(pk=1, condition_formula='',
                                  target_param=mock_target,
                                  action='set_value', value_formula='500 * 2')

        mock_qs = self._make_rule_queryset([rule])
        mock_rule_cls.objects.filter.return_value = mock_qs
        mock_eval.return_value = 1000.0

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {'speed': 10})

        self.assertEqual(result['param_overrides'], {'length': 1000.0})

    @mock.patch('parametric_bom.models.ParametricRule')
    @mock.patch('parametric_bom.formula_engine.evaluate')
    def test_set_min_creates_constraint(self, mock_eval, mock_rule_cls):
        """Test SET_MIN creates constraint when current value is too low."""
        mock_part = MockPart('Product', pk=1)
        mock_target = MockParameterTemplate('length')
        rule = MockParametricRule(pk=1, condition_formula='',
                                  target_param=mock_target,
                                  action='set_min', value_formula='50',
                                  error_message='Length too short!')

        mock_qs = self._make_rule_queryset([rule])
        mock_rule_cls.objects.filter.return_value = mock_qs
        mock_eval.return_value = 50

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {'length': 10})

        self.assertFalse(result['valid'])
        self.assertEqual(len(result['constraints']), 1)
        self.assertIn('Length too short!', result['constraints'][0]['message'])
        self.assertEqual(result['param_overrides'].get('length__min'), 50)

    @mock.patch('parametric_bom.models.ParametricRule')
    @mock.patch('parametric_bom.formula_engine.evaluate')
    def test_set_min_no_constraint_when_ok(self, mock_eval, mock_rule_cls):
        """Test SET_MIN does not create constraint when value is above min."""
        mock_part = MockPart('Product', pk=1)
        mock_target = MockParameterTemplate('length')
        rule = MockParametricRule(pk=1, condition_formula='',
                                  target_param=mock_target,
                                  action='set_min', value_formula='50')

        mock_qs = self._make_rule_queryset([rule])
        mock_rule_cls.objects.filter.return_value = mock_qs
        mock_eval.return_value = 50

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {'length': 100})

        self.assertTrue(result['valid'])
        self.assertEqual(len(result['constraints']), 0)

    @mock.patch('parametric_bom.models.ParametricRule')
    @mock.patch('parametric_bom.formula_engine.evaluate')
    def test_set_max_creates_constraint(self, mock_eval, mock_rule_cls):
        """Test SET_MAX creates constraint when current value exceeds max."""
        mock_part = MockPart('Product', pk=1)
        mock_target = MockParameterTemplate('length')
        rule = MockParametricRule(pk=1, condition_formula='',
                                  target_param=mock_target,
                                  action='set_max', value_formula='100')

        mock_qs = self._make_rule_queryset([rule])
        mock_rule_cls.objects.filter.return_value = mock_qs
        mock_eval.return_value = 100

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {'length': 200})

        self.assertFalse(result['valid'])
        self.assertEqual(len(result['constraints']), 1)

    @mock.patch('parametric_bom.models.ParametricRule')
    def test_show_action(self, mock_rule_cls):
        """Test SHOW action marks param as visible."""
        mock_part = MockPart('Product', pk=1)
        mock_target = MockParameterTemplate('advanced_option')
        rule = MockParametricRule(pk=1, condition_formula='param.speed > 10',
                                  target_param=mock_target,
                                  action='show')

        mock_qs = self._make_rule_queryset([rule])
        mock_rule_cls.objects.filter.return_value = mock_qs

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {'speed': 20})

        self.assertEqual(result['param_visibility'], {'advanced_option': True})

    @mock.patch('parametric_bom.models.ParametricRule')
    def test_hide_action(self, mock_rule_cls):
        """Test HIDE action marks param as hidden."""
        mock_part = MockPart('Product', pk=1)
        mock_target = MockParameterTemplate('high_speed_option')
        rule = MockParametricRule(pk=1, condition_formula='param.speed < 10',
                                  target_param=mock_target,
                                  action='hide')

        mock_qs = self._make_rule_queryset([rule])
        mock_rule_cls.objects.filter.return_value = mock_qs

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {'speed': 5})

        self.assertEqual(result['param_visibility'], {'high_speed_option': False})

    @mock.patch('parametric_bom.models.ParametricRule')
    def test_require_action(self, mock_rule_cls):
        """Test REQUIRE action adds parameter requirement."""
        mock_part = MockPart('Product', pk=1)
        mock_target = MockParameterTemplate('safety_cert')
        rule = MockParametricRule(pk=1, condition_formula='param.speed > 20',
                                  target_param=mock_target,
                                  action='require')

        mock_qs = self._make_rule_queryset([rule])
        mock_rule_cls.objects.filter.return_value = mock_qs

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {'speed': 25})

        self.assertIn('safety_cert', result['param_requirements'])

    @mock.patch('parametric_bom.models.ParametricRule')
    def test_condition_not_met_skips_rule(self, mock_rule_cls):
        """Test that condition not met means the action is not taken."""
        mock_part = MockPart('Product', pk=1)
        mock_target = MockParameterTemplate('length')
        rule = MockParametricRule(pk=1, condition_formula='FALSE',
                                  target_param=mock_target,
                                  action='set_value', value_formula='999')

        mock_qs = self._make_rule_queryset([rule])
        mock_rule_cls.objects.filter.return_value = mock_qs

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {'speed': 10})

        self.assertEqual(result['param_overrides'], {})

    @mock.patch('parametric_bom.models.ParametricRule')
    @mock.patch('parametric_bom.formula_engine.evaluate')
    def test_formula_error_still_accumulates_overrides(self, mock_eval, mock_rule_cls):
        """Test that when a formula errors, prior overrides still accumulate."""
        mock_part = MockPart('Product', pk=1)
        target1 = MockParameterTemplate('a')
        target2 = MockParameterTemplate('b')

        rule1 = MockParametricRule(pk=1, condition_formula='',
                                   target_param=target1,
                                   action='set_value', value_formula='10')
        rule2 = MockParametricRule(pk=2, condition_formula='',
                                   target_param=target2,
                                   action='set_value', value_formula='INVALID(')

        mock_qs = self._make_rule_queryset([rule1, rule2])
        mock_rule_cls.objects.filter.return_value = mock_qs

        from parametric_bom.formula_engine import ParseError

        def eval_side_effect(formula, **kwargs):
            if formula == 'INVALID(':
                raise ParseError('Bad formula')
            return 10

        mock_eval.side_effect = eval_side_effect

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {})

        self.assertIn('a', result['param_overrides'])
        self.assertEqual(result['param_overrides']['a'], 10)
        self.assertGreater(len(result['errors']), 0)

    @mock.patch('parametric_bom.models.ParametricRule')
    def test_unknown_action_adds_warning(self, mock_rule_cls):
        """Test that an unknown action is warned about."""
        mock_part = MockPart('Product', pk=1)
        rule = MockParametricRule(pk=1, condition_formula='',
                                  target_param=None,
                                  action='unknown_action')

        mock_qs = self._make_rule_queryset([rule])
        mock_rule_cls.objects.filter.return_value = mock_qs

        from parametric_bom.rule_engine import evaluate_rules
        result = evaluate_rules(mock_part, {})

        self.assertGreater(len(result['warnings']), 0)
        self.assertIn('unknown_action', result['warnings'][0])


# ══════════════════════════════════════════════
#  Tests for evaluate_config_rules
# ══════════════════════════════════════════════


class TestEvaluateConfigRules(TestCase):
    """Tests for the evaluate_config_rules() function."""

    @mock.patch('parametric_bom.models.ConfigParameterValue')
    @mock.patch('parametric_bom.models.ParametricRule')
    def test_evaluate_config_rules_basic(self, mock_rule_cls, mock_cpv_cls):
        """Test evaluate_config_rules with a mock configuration."""
        from parametric_bom.rule_engine import evaluate_config_rules

        mock_config = mock.MagicMock()
        mock_config.pk = 1
        mock_config.template_part.pk = 1
        mock_config.template_part.name = 'Product'
        mock_config.status = 'draft'

        # Mock parameter values
        mock_param_val_1 = mock.MagicMock()
        mock_param_val_1.template.name = 'speed'
        mock_param_val_1.value = '10'

        mock_pv_qs = mock.MagicMock()
        mock_pv_qs.select_related.return_value = [mock_param_val_1]
        mock_cpv_cls.objects.filter.return_value = mock_pv_qs

        # Mock no rules
        mock_qs = mock.MagicMock()
        mock_qs.exists.return_value = False
        mock_qs.select_related.return_value = mock_qs
        mock_rule_cls.objects.filter.return_value = mock_qs

        result = evaluate_config_rules(mock_config)

        self.assertTrue(result['valid'])
        mock_rule_cls.objects.filter.assert_called_once()


# ══════════════════════════════════════════════
#  Tests for action helpers (edge cases)
# ══════════════════════════════════════════════


class TestActionEdgeCases(TestCase):
    """Tests for the individual action functions with edge cases."""

    def test_set_value_no_target(self):
        """Test SET_VALUE with no target param yields error."""
        from parametric_bom.rule_engine import _action_set_value, RuleEvaluationResult

        mock_rule = MockParametricRule(pk=1)
        result = RuleEvaluationResult()
        _action_set_value(mock_rule, None, {'speed': 10}, result, 500)

        self.assertGreater(len(result.errors), 0)
        self.assertIn('requires a target_param', result.errors[0])

    def test_set_value_no_formula(self):
        """Test SET_VALUE with empty value_formula yields error."""
        from parametric_bom.rule_engine import _action_set_value, RuleEvaluationResult

        mock_rule = MockParametricRule(pk=1, target_param=MockParameterTemplate('x'))
        mock_rule.value_formula = ''
        result = RuleEvaluationResult()
        _action_set_value(mock_rule, 'x', {'speed': 10}, result, 500)

        self.assertGreater(len(result.errors), 0)
        self.assertIn('requires a value_formula', result.errors[0])

    def test_set_min_no_target(self):
        """Test SET_MIN with no target param yields error."""
        from parametric_bom.rule_engine import _action_set_min, RuleEvaluationResult

        mock_rule = MockParametricRule(pk=1)
        result = RuleEvaluationResult()
        _action_set_min(mock_rule, None, {'speed': 10}, result, 500)

        self.assertGreater(len(result.errors), 0)

    def test_set_max_no_target(self):
        """Test SET_MAX with no target param yields error."""
        from parametric_bom.rule_engine import _action_set_max, RuleEvaluationResult

        mock_rule = MockParametricRule(pk=1)
        result = RuleEvaluationResult()
        _action_set_max(mock_rule, None, {'speed': 10}, result, 500)

        self.assertGreater(len(result.errors), 0)

    def test_show_no_target(self):
        """Test SHOW with no target yields warning."""
        from parametric_bom.rule_engine import _action_show, RuleEvaluationResult

        result = RuleEvaluationResult()
        _action_show(None, result)

        self.assertGreater(len(result.warnings), 0)

    def test_hide_no_target(self):
        """Test HIDE with no target yields warning."""
        from parametric_bom.rule_engine import _action_hide, RuleEvaluationResult

        result = RuleEvaluationResult()
        _action_hide(None, result)

        self.assertGreater(len(result.warnings), 0)

    def test_require_no_target(self):
        """Test REQUIRE with no target yields warning."""
        from parametric_bom.rule_engine import _action_require, RuleEvaluationResult

        result = RuleEvaluationResult()
        _action_require(None, result)

        self.assertGreater(len(result.warnings), 0)

    def test_rule_result_to_dict(self):
        """Test RuleEvaluationResult.to_dict() serialization."""
        from parametric_bom.rule_engine import RuleEvaluationResult

        r = RuleEvaluationResult()
        r.valid = False
        r.errors.append('some error')
        r.warnings.append('some warning')
        r.param_overrides['x'] = 10

        d = r.to_dict()
        self.assertFalse(d['valid'])
        self.assertEqual(d['errors'], ['some error'])
        self.assertEqual(d['warnings'], ['some warning'])
        self.assertEqual(d['param_overrides'], {'x': 10})
        self.assertEqual(d['param_visibility'], {})
        self.assertEqual(d['param_requirements'], [])
        self.assertEqual(d['constraints'], [])
