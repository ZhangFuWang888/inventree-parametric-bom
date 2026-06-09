"""Tests for the BOM expansion service.

Tests the core functions in bom_expander.py:
  - compute_parameters()
  - expand_bom_level()
  - evaluate_part()
  - evaluate_configuration()

Run with:
  SKIP_MIGRATIONS=1 DJANGO_SETTINGS_MODULE=InvenTree.settings \\
    venv/bin/python -m pytest parametric_bom/tests/test_bom_expander.py -v

All tests use unittest.TestCase (not django.test.TestCase) because all
Django model queries are mocked. No database access is required.
"""

from unittest import TestCase, mock

import pytest


class MockParameterTemplate:
    """Minimal mock for ParameterTemplate (only needs .name)."""

    def __init__(self, name):
        self.name = name


class MockPartParameterConfig:
    """Minimal mock for PartParameterConfig.

    Matches the model fields accessed by compute_parameters():
      - template (FK -> ParameterTemplate)
      - default_value
      - is_driving
      - is_computed
      - computation_formula
    """

    def __init__(self, template_name, default_value='', is_driving=True,
                 is_computed=False, computation_formula=''):
        self.template = MockParameterTemplate(template_name)
        self.default_value = default_value
        self.is_driving = is_driving
        self.is_computed = is_computed
        self.computation_formula = computation_formula


class MockBomItem:
    """Minimal mock for BomItem.

    Matches the attributes accessed in expand_bom_level / _expand_single_bom_item:
      - part: parent Part
      - sub_part: child Part
      - quantity (Decimal)
      - optional (bool)
      - consumable (bool)
      - reference (str)
      - pk (int)
    """

    def __init__(self, part, sub_part, quantity=1.0, optional=False,
                 consumable=False, reference='', pk=1):
        self.part = part
        self.sub_part = sub_part
        self.quantity = quantity
        self.optional = optional
        self.consumable = consumable
        self.reference = reference
        self.pk = pk


class MockPart:
    """Minimal mock for Part.

    Fields accessed in bom_expander:
      - pk / id
      - name
      - full_name (property, falls back to name)
      - bom_items (related manager, all().select_related())
      - category (for part selector)
    """

    def __init__(self, name='TestPart', pk=1, category=None):
        self.pk = pk
        self.id = pk
        self.name = name
        self._full_name = None
        self.category = category
        self._bom_items = []

    @property
    def full_name(self):
        return self._full_name or self.name

    @full_name.setter
    def full_name(self, value):
        self._full_name = value

    def add_bom_item(self, sub_part, quantity=1.0, optional=False,
                     consumable=False, reference='', pk=None):
        """Helper to add a BomItem to this part's BOM."""
        if pk is None:
            pk = len(self._bom_items) + 1
        item = MockBomItem(
            part=self, sub_part=sub_part, quantity=quantity,
            optional=optional, consumable=consumable,
            reference=reference, pk=pk,
        )
        self._bom_items.append(item)
        return item

    @property
    def bom_items(self):
        return _MockRelatedManager(self._bom_items)


class _MockRelatedManager:
    """Mocks a Django related manager with .all().select_related() chain."""

    def __init__(self, items):
        self._items = list(items)
        self._select_related_fields = []

    def all(self):
        return self

    def select_related(self, *fields):
        self._select_related_fields = list(fields)
        return self

    def exists(self):
        return len(self._items) > 0

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def filter(self, **kwargs):
        return self


class MockParametricBomItem:
    """Minimal mock for ParametricBomItem.

    Fields accessed in _expand_single_bom_item:
      - qty_formula
      - condition_formula
      - part_selector_formula
    """

    def __init__(self, bom_item, qty_formula='', condition_formula='',
                 part_selector_formula=''):
        self.bom_item = bom_item
        self.qty_formula = qty_formula
        self.condition_formula = condition_formula
        self.part_selector_formula = part_selector_formula


_DoesNotExist = type('DoesNotExist', (Exception,), {})


def _make_cfg_mock(exists_return=True, configs=None):
    """Create a PartParameterConfig mock.

    Args:
        exists_return: What .exists() should return on filter queries
                       (used by _expand_sub_part to check if sub-part has configs)
        configs: List of configs for compute_parameters (select_related chain)
    """
    mock_cfg = mock.MagicMock()
    if configs is not None:
        mock_cfg.select_related.return_value = mock_cfg
        mock_cfg.order_by.return_value = configs
    mock_exists_qs = mock.MagicMock()
    mock_exists_qs.exists.return_value = exists_return
    if configs is not None:
        # If configs provided, filter returns config-returning mock
        mock_cfg.filter.return_value = mock_cfg
    else:
        mock_cfg.filter.return_value = mock_exists_qs
    return mock_cfg


# ══════════════════════════════════════════════
#  Tests for compute_parameters()
# ══════════════════════════════════════════════


class TestComputeParameters(TestCase):
    """Tests for the compute_parameters() function."""

    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_basic_computation(self, mock_config_cls):
        """Test that a computed parameter is evaluated correctly."""
        mock_part = MockPart('Assembly', pk=1)

        cfg_length = MockPartParameterConfig(
            template_name='length',
            default_value='1000',
            is_driving=False,
            is_computed=True,
            computation_formula='500 * 2',
        )

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = [cfg_length]
        mock_config_cls.objects.filter.return_value = mock_qs

        from parametric_bom.bom_expander import compute_parameters

        params, errors = compute_parameters(mock_part, {})

        self.assertIn('length', params)
        self.assertEqual(params['length'], 1000.0)  # 500 * 2
        self.assertEqual(len(errors), 0)

    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_skips_user_provided_params(self, mock_config_cls):
        """Test that user-provided params are not overwritten."""
        mock_part = MockPart('Assembly', pk=1)

        cfg = MockPartParameterConfig(
            template_name='length',
            default_value='1000',
            is_driving=True,
            is_computed=True,
            computation_formula='999',
        )

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = [cfg]
        mock_config_cls.objects.filter.return_value = mock_qs

        from parametric_bom.bom_expander import compute_parameters

        params, errors = compute_parameters(mock_part, {'length': 5000})

        self.assertEqual(params['length'], 5000)  # User value preserved
        self.assertEqual(len(errors), 0)

    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_fallback_to_default(self, mock_config_cls):
        """Test that non-computed params fall back to default_value."""
        mock_part = MockPart('Assembly', pk=1)

        cfg = MockPartParameterConfig(
            template_name='color',
            default_value='red',
            is_driving=True,
            is_computed=False,
        )

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = [cfg]
        mock_config_cls.objects.filter.return_value = mock_qs

        from parametric_bom.bom_expander import compute_parameters

        params, errors = compute_parameters(mock_part, {})

        self.assertEqual(params['color'], 'red')

    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_skips_empty_default(self, mock_config_cls):
        """Test that a non-computed param with empty default_value is skipped."""
        mock_part = MockPart('Assembly', pk=1)

        cfg = MockPartParameterConfig(
            template_name='optional_param',
            default_value='',
            is_driving=True,
            is_computed=False,
        )

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = [cfg]
        mock_config_cls.objects.filter.return_value = mock_qs

        from parametric_bom.bom_expander import compute_parameters

        params, errors = compute_parameters(mock_part, {})

        self.assertNotIn('optional_param', params)

    @mock.patch('parametric_bom.formula_engine.evaluate')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_formula_error_fallback(self, mock_config_cls, mock_eval):
        """Test that formula evaluation errors result in a fallback to default."""
        from parametric_bom.formula_engine import ParseError

        mock_part = MockPart('Assembly', pk=1)

        cfg = MockPartParameterConfig(
            template_name='bad_param',
            default_value='fallback_val',
            is_driving=False,
            is_computed=True,
            computation_formula='INVALID(())',
        )

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = [cfg]
        mock_config_cls.objects.filter.return_value = mock_qs

        mock_eval.side_effect = ParseError('Syntax error')

        from parametric_bom.bom_expander import compute_parameters

        params, errors = compute_parameters(mock_part, {})

        self.assertEqual(params['bad_param'], 'fallback_val')
        self.assertEqual(len(errors), 1)
        self.assertIn('bad_param', errors[0])

    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_multiple_ordered_params(self, mock_config_cls):
        """Test that params are processed in display_order."""
        mock_part = MockPart('Assembly', pk=1)

        cfg_a = MockPartParameterConfig(
            template_name='a',
            default_value='1',
            is_computed=False,
        )
        cfg_b = MockPartParameterConfig(
            template_name='b',
            default_value='2',
            is_computed=False,
        )
        cfg_c = MockPartParameterConfig(
            template_name='c',
            default_value='3',
            is_computed=False,
        )

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = [cfg_a, cfg_b, cfg_c]
        mock_config_cls.objects.filter.return_value = mock_qs

        from parametric_bom.bom_expander import compute_parameters

        params, errors = compute_parameters(mock_part, {})

        self.assertEqual(params, {'a': '1', 'b': '2', 'c': '3'})
        self.assertEqual(len(errors), 0)


# ══════════════════════════════════════════════
#  Tests for expand_bom_level()
# ══════════════════════════════════════════════


class TestExpandBomLevel(TestCase):
    """Tests for the expand_bom_level() function."""

    # Helper: make a PartParameterConfig filter mock that returns exists()=False
    @staticmethod
    def _no_configs_mock(mock_config_cls):
        """Configure PartParameterConfig mock so .filter().exists() = False."""
        mock_cfg_qs = mock.MagicMock()
        mock_cfg_qs.exists.return_value = False
        mock_config_cls.objects.filter.return_value = mock_cfg_qs

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_basic_expansion_no_parametric(self, mock_config_cls, mock_pbom_cls):
        """Test basic BOM expansion without any parametric configs."""
        parent = MockPart('Assembly', pk=1)
        child = MockPart('Bolt', pk=2)
        parent.add_bom_item(child, quantity=4.0)

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.side_effect = _DoesNotExist()
        self._no_configs_mock(mock_config_cls)

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={'speed': 10}, max_depth=5)

        self.assertEqual(tree['part_id'], 1)
        self.assertEqual(tree['part_name'], 'Assembly')
        self.assertEqual(tree['depth'], 0)
        self.assertEqual(len(tree['children']), 1)

        child_node = tree['children'][0]
        self.assertEqual(child_node['part_id'], 2)
        self.assertEqual(child_node['part_name'], 'Bolt')
        self.assertEqual(child_node['depth'], 1)
        self.assertEqual(child_node['quantity'], 4.0)
        self.assertEqual(child_node['calculated_quantity'], 4.0)
        self.assertFalse(child_node.get('parametric', False))

    @mock.patch('parametric_bom.models.ParametricBomItem')
    def test_max_depth_limit(self, mock_pbom_cls):
        """Test that max_depth is respected."""
        parent = MockPart('Root', pk=1)

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.side_effect = _DoesNotExist()

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={}, max_depth=0, depth=0)

        self.assertEqual(tree['depth'], 0)
        self.assertIn('Max recursion depth', tree['errors'][0])
        self.assertEqual(len(tree['children']), 0)

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_condition_exclusion(self, mock_config_cls, mock_pbom_cls):
        """Test that condition formula excludes a BOM item."""
        parent = MockPart('Assembly', pk=1)
        child = MockPart('OptionalItem', pk=2)
        bij = parent.add_bom_item(child, quantity=1.0)

        param_cfg = MockParametricBomItem(
            bom_item=bij,
            condition_formula='param.speed > 20',
        )

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.return_value = param_cfg
        self._no_configs_mock(mock_config_cls)

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={'speed': 10}, max_depth=5)

        self.assertEqual(len(tree['children']), 1)
        child_node = tree['children'][0]
        self.assertTrue(child_node['excluded'])
        self.assertIsNotNone(child_node['exclude_reason'])
        self.assertIn('Condition not met', child_node['exclude_reason'])

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_condition_not_excluded_when_met(self, mock_config_cls, mock_pbom_cls):
        """Test that condition formula includes item when condition is met."""
        parent = MockPart('Assembly', pk=1)
        child = MockPart('OptionalItem', pk=2)
        bij = parent.add_bom_item(child, quantity=2.0)

        param_cfg = MockParametricBomItem(
            bom_item=bij,
            condition_formula='param.speed > 5',
        )

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.return_value = param_cfg
        self._no_configs_mock(mock_config_cls)

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={'speed': 10}, max_depth=5)

        child_node = tree['children'][0]
        self.assertFalse(child_node['excluded'])
        self.assertIsNone(child_node.get('exclude_reason'))

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_quantity_formula(self, mock_config_cls, mock_pbom_cls):
        """Test that quantity formula overrides static quantity."""
        parent = MockPart('Assembly', pk=1)
        child = MockPart('Bracket', pk=2)
        bij = parent.add_bom_item(child, quantity=1.0)

        param_cfg = MockParametricBomItem(
            bom_item=bij,
            qty_formula='param.length / 500',
        )

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.return_value = param_cfg
        self._no_configs_mock(mock_config_cls)

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={'length': 2000}, max_depth=5)

        child_node = tree['children'][0]
        self.assertEqual(child_node['calculated_quantity'], 4.0)  # 2000/500
        self.assertTrue(child_node.get('parametric', False))

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_quantity_formula_error(self, mock_config_cls, mock_pbom_cls):
        """Test that quantity formula errors are captured."""
        parent = MockPart('Assembly', pk=1)
        child = MockPart('Bracket', pk=2)
        bij = parent.add_bom_item(child, quantity=1.0)

        param_cfg = MockParametricBomItem(
            bom_item=bij,
            qty_formula='INVALID(((',
        )

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.return_value = param_cfg
        self._no_configs_mock(mock_config_cls)

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={'length': 2000}, max_depth=5)

        child_node = tree['children'][0]
        self.assertIn('Quantity formula error', child_node['errors'][0])

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_multiple_bom_items(self, mock_config_cls, mock_pbom_cls):
        """Test expansion with multiple BOM items."""
        parent = MockPart('Assembly', pk=1)
        child1 = MockPart('Screw', pk=2)
        child2 = MockPart('Nut', pk=3)
        parent.add_bom_item(child1, quantity=4.0)
        parent.add_bom_item(child2, quantity=4.0)

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.side_effect = _DoesNotExist()
        self._no_configs_mock(mock_config_cls)

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={}, max_depth=5)

        self.assertEqual(len(tree['children']), 2)
        self.assertEqual(tree['children'][0]['part_name'], 'Screw')
        self.assertEqual(tree['children'][1]['part_name'], 'Nut')

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_condition_formula_error_keeps_item(self, mock_config_cls, mock_pbom_cls):
        """Test that a condition formula error does NOT exclude item."""
        parent = MockPart('Assembly', pk=1)
        child = MockPart('DodgyItem', pk=2)
        bij = parent.add_bom_item(child, quantity=1.0)

        param_cfg = MockParametricBomItem(
            bom_item=bij,
            condition_formula='INVALID(((',
        )

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.return_value = param_cfg
        self._no_configs_mock(mock_config_cls)

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={'speed': 10}, max_depth=5)

        child_node = tree['children'][0]
        self.assertFalse(child_node['excluded'])
        self.assertIn('Condition formula error', child_node['errors'][0])

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_sub_part_recursion_no_params(self, mock_config_cls, mock_pbom_cls):
        """Test that sub-parts without param configs still get BOM recursion."""
        parent = MockPart('Assembly', pk=1)
        sub_assy = MockPart('SubAssembly', pk=2)
        leaf = MockPart('LeafPart', pk=3)
        sub_assy.add_bom_item(leaf, quantity=3.0)
        parent.add_bom_item(sub_assy, quantity=1.0)

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.side_effect = _DoesNotExist()
        self._no_configs_mock(mock_config_cls)

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={}, max_depth=5)

        self.assertEqual(len(tree['children']), 1)
        sub_node = tree['children'][0]
        self.assertEqual(sub_node['part_name'], 'SubAssembly')
        self.assertEqual(len(sub_node['children']), 1)
        self.assertEqual(sub_node['children'][0]['part_name'], 'LeafPart')
        self.assertEqual(sub_node['children'][0]['quantity'], 3.0)

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_sub_part_recursion_with_params(self, mock_config_cls, mock_pbom_cls):
        """Test that sub-parts with parameter configs trigger compute_parameters."""
        parent = MockPart('Assembly', pk=1)
        sub_assy = MockPart('SubAssembly', pk=2)
        leaf = MockPart('LeafPart', pk=3)
        sub_assy.add_bom_item(leaf, quantity=2.0)
        parent.add_bom_item(sub_assy, quantity=1.0)

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.side_effect = _DoesNotExist()

        cfg = MockPartParameterConfig(
            template_name='length',
            default_value='500',
        )

        # Mock for _expand_sub_part: check if sub_assy has configs
        mock_config_exists_qs = mock.MagicMock()
        mock_config_exists_qs.exists.return_value = True
        mock_config_exists_qs.select_related = mock_config_exists_qs

        # Mock for compute_parameters call within _expand_sub_part
        mock_config_filter_qs = mock.MagicMock()
        mock_config_filter_qs.select_related.return_value = mock_config_filter_qs
        mock_config_filter_qs.order_by.return_value = [cfg]

        def filter_side_effect(**kwargs):
            return mock_config_filter_qs

        mock_config_cls.objects.filter.side_effect = filter_side_effect

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={'speed': 10}, max_depth=5)

        self.assertEqual(len(tree['children']), 1)
        sub_node = tree['children'][0]
        self.assertEqual(sub_node['part_name'], 'SubAssembly')
        self.assertEqual(len(sub_node['children']), 1)
        self.assertEqual(sub_node['children'][0]['part_name'], 'LeafPart')


# ══════════════════════════════════════════════
#  Tests for evaluate_part()
# ══════════════════════════════════════════════


class TestEvaluatePart(TestCase):
    """Tests for the evaluate_part() function."""

    @mock.patch('django.utils.timezone.now', return_value=mock.MagicMock(
        isoformat=lambda: '2025-01-01T00:00:00',
    ))
    @mock.patch('parametric_bom.bom_expander.expand_bom_level')
    @mock.patch('parametric_bom.bom_expander.compute_parameters')
    def test_evaluate_part_basic(self, mock_compute, mock_expand, mock_now):
        """Test basic evaluate_part flow."""
        from parametric_bom.bom_expander import evaluate_part

        mock_part = MockPart('MyAssembly', pk=42)

        mock_compute.return_value = ({'speed': 10, 'length': 5000}, [])
        mock_expand.return_value = {
            'part_id': 42,
            'part_name': 'MyAssembly',
            'depth': 0,
            'quantity': 1,
            'calculated_quantity': 1,
            'children': [],
            'errors': [],
            'excluded': False,
            'exclude_reason': None,
        }

        result = evaluate_part(mock_part, {'speed': 10})

        self.assertEqual(result['part_id'], 42)
        self.assertEqual(result['part_name'], 'MyAssembly')
        self.assertEqual(result['parameters'], {'speed': 10, 'length': 5000})
        self.assertEqual(result['parameter_errors'], [])
        self.assertEqual(result['total_bom_items'], 0)
        self.assertIsNotNone(result['expanded_at'])

        mock_compute.assert_called_once_with(mock_part, {'speed': 10}, 500)
        mock_expand.assert_called_once()

    @mock.patch('django.utils.timezone.now', return_value=mock.MagicMock(
        isoformat=lambda: '2025-01-01T00:00:00',
    ))
    @mock.patch('parametric_bom.bom_expander.expand_bom_level')
    @mock.patch('parametric_bom.bom_expander.compute_parameters')
    def test_evaluate_part_with_errors(self, mock_compute, mock_expand, mock_now):
        """Test evaluate_part with parameter computation errors."""
        from parametric_bom.bom_expander import evaluate_part

        mock_part = MockPart('ErrorPart', pk=99)

        mock_compute.return_value = (
            {'speed': 10},
            ['bad_param: Parse error at line 1'],
        )
        mock_expand.return_value = {
            'part_id': 99,
            'part_name': 'ErrorPart',
            'children': [],
            'errors': [],
            'excluded': False,
            'exclude_reason': None,
        }

        result = evaluate_part(mock_part, {'speed': 10})

        self.assertIn('bad_param', result['parameter_errors'][0])
        self.assertEqual(result['total_bom_items'], 0)

    @mock.patch('django.utils.timezone.now', return_value=mock.MagicMock(
        isoformat=lambda: '2025-01-01T00:00:00',
    ))
    @mock.patch('parametric_bom.bom_expander.expand_bom_level')
    @mock.patch('parametric_bom.bom_expander.compute_parameters')
    def test_evaluate_part_custom_timeout(self, mock_compute, mock_expand, mock_now):
        """Test evaluate_part with custom timeout and max_depth."""
        from parametric_bom.bom_expander import evaluate_part

        mock_part = MockPart('TimedPart', pk=7)

        mock_compute.return_value = ({'x': 1}, [])
        mock_expand.return_value = {
            'part_id': 7,
            'part_name': 'TimedPart',
            'children': [],
            'errors': [],
            'excluded': False,
            'exclude_reason': None,
        }

        result = evaluate_part(mock_part, {'x': 1}, timeout_ms=100, max_depth=3)

        mock_compute.assert_called_once_with(mock_part, {'x': 1}, 100)
        mock_expand.assert_called_once_with(
            mock_part, {'x': 1}, depth=0, max_depth=3, timeout_ms=100,
        )


# ══════════════════════════════════════════════
#  Tests for tree structure output
# ══════════════════════════════════════════════


class TestTreeStructure(TestCase):
    """Tests for the tree structure output of expand_bom_level."""

    @mock.patch('parametric_bom.models.ParametricBomItem')
    def test_minimal_tree_structure(self, mock_pbom_cls):
        """Verify the tree node structure has all expected keys."""
        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.side_effect = _DoesNotExist()

        from parametric_bom.bom_expander import expand_bom_level

        part = MockPart('Empty', pk=0)

        tree = expand_bom_level(part, params={}, max_depth=10)

        expected_keys = {
            'part_id', 'part_name', 'depth', 'quantity',
            'calculated_quantity', 'children', 'errors',
            'excluded', 'exclude_reason',
        }
        self.assertEqual(set(tree.keys()), expected_keys)
        self.assertEqual(tree['part_id'], 0)
        self.assertEqual(tree['part_name'], 'Empty')
        self.assertEqual(tree['depth'], 0)
        self.assertEqual(tree['quantity'], 1)
        self.assertEqual(tree['calculated_quantity'], 1)
        self.assertEqual(tree['children'], [])
        self.assertEqual(tree['errors'], [])
        self.assertFalse(tree['excluded'])
        self.assertIsNone(tree['exclude_reason'])

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_child_node_structure(self, mock_config_cls, mock_pbom_cls):
        """Verify child node has all expected keys."""
        parent = MockPart('Parent', pk=1)
        child = MockPart('Child', pk=2)
        parent.add_bom_item(child, quantity=3.0)

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.side_effect = _DoesNotExist()

        mock_cfg_qs = mock.MagicMock()
        mock_cfg_qs.exists.return_value = False
        mock_config_cls.objects.filter.return_value = mock_cfg_qs

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={}, max_depth=10)
        child_node = tree['children'][0]

        expected_child_keys = {
            'part_id', 'part_name', 'depth', 'quantity',
            'calculated_quantity', 'children', 'errors',
            'excluded', 'exclude_reason',
            'bom_item_id', 'optional', 'consumable', 'reference',
        }
        self.assertTrue(expected_child_keys.issubset(set(child_node.keys())))
        self.assertEqual(child_node['part_id'], 2)
        self.assertEqual(child_node['part_name'], 'Child')
        self.assertEqual(child_node['depth'], 1)
        self.assertEqual(child_node['quantity'], 3.0)
        self.assertFalse(child_node['optional'])
        self.assertFalse(child_node['consumable'])
        self.assertEqual(child_node['reference'], '')
        self.assertIsNotNone(child_node['bom_item_id'])

    @mock.patch('parametric_bom.models.ParametricBomItem')
    def test_total_bom_count(self, mock_pbom_cls):
        """Test _compute_total_quantity via evaluate_part."""
        parent = MockPart('Root', pk=1)
        child1 = MockPart('Leaf1', pk=2)
        child2 = MockPart('Leaf2', pk=3)

        grandchild = MockPart('Leaf3', pk=4)
        child2.add_bom_item(grandchild, quantity=1.0)

        parent.add_bom_item(child1, quantity=1.0)
        parent.add_bom_item(child2, quantity=1.0)

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.side_effect = _DoesNotExist()

        with mock.patch('parametric_bom.models.PartParameterConfig') as m_cfg:
            m_cfg_qs = mock.MagicMock()
            m_cfg_qs.exists.return_value = False
            m_cfg.objects.filter.return_value = m_cfg_qs

            with mock.patch('django.utils.timezone.now', return_value=mock.MagicMock(
                isoformat=lambda: '2025-01-01T00:00:00',
            )):
                from parametric_bom.bom_expander import evaluate_part

                result = evaluate_part(parent, {})

                # Total count: child1 (1) + child2 (1) + grandchild (1) = 3
                self.assertEqual(result['total_bom_items'], 3)


# ══════════════════════════════════════════════
#  Tests for condition formula exclusion
# ══════════════════════════════════════════════


class TestConditionExclusion(TestCase):
    """Focused tests on condition formula exclusion behavior."""

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_excluded_item_has_no_children(self, mock_config_cls, mock_pbom_cls):
        """Test that excluded items are not recursed into."""
        parent = MockPart('Parent', pk=1)
        child = MockPart('Sub', pk=2)
        grandchild = MockPart('Grandchild', pk=3)
        child.add_bom_item(grandchild, quantity=1.0)
        bij = parent.add_bom_item(child, quantity=1.0)

        param_cfg = MockParametricBomItem(
            bom_item=bij,
            condition_formula='FALSE',
        )

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.return_value = param_cfg
        mock_cfg_qs = mock.MagicMock()
        mock_cfg_qs.exists.return_value = False
        mock_config_cls.objects.filter.return_value = mock_cfg_qs

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={}, max_depth=10)

        self.assertEqual(len(tree['children']), 1)
        child_node = tree['children'][0]
        self.assertTrue(child_node['excluded'])
        self.assertIn('Condition not met', child_node['exclude_reason'])
        self.assertEqual(child_node['children'], [])

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_included_item_still_has_children(self, mock_config_cls, mock_pbom_cls):
        """Test that included items still get recursed into."""
        parent = MockPart('Parent', pk=1)
        child = MockPart('Sub', pk=2)
        grandchild = MockPart('Grandchild', pk=3)
        child.add_bom_item(grandchild, quantity=1.0)
        bij = parent.add_bom_item(child, quantity=1.0)

        param_cfg = MockParametricBomItem(
            bom_item=bij,
            condition_formula='TRUE',
        )

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.return_value = param_cfg

        mock_cfg_qs = mock.MagicMock()
        mock_cfg_qs.exists.return_value = False
        mock_config_cls.objects.filter.return_value = mock_cfg_qs

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={}, max_depth=10)

        child_node = tree['children'][0]
        self.assertFalse(child_node['excluded'])
        self.assertIsNone(child_node.get('exclude_reason'))

    @mock.patch('parametric_bom.models.ParametricBomItem')
    def test_excluded_in_total_count(self, mock_pbom_cls):
        """Test that excluded items are not counted in total_bom_items."""
        parent = MockPart('Parent', pk=1)
        child1 = MockPart('Included', pk=2)
        child2 = MockPart('Excluded', pk=3)
        parent.add_bom_item(child1, quantity=1.0)
        bij2 = parent.add_bom_item(child2, quantity=1.0)

        param_cfg2 = MockParametricBomItem(
            bom_item=bij2,
            condition_formula='FALSE',
        )

        def get_side_effect(bom_item=None, **kwargs):
            if bom_item == bij2:
                return param_cfg2
            raise _DoesNotExist()

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.side_effect = get_side_effect

        with mock.patch('parametric_bom.models.PartParameterConfig') as m_cfg:
            m_cfg_qs = mock.MagicMock()
            m_cfg_qs.exists.return_value = False
            m_cfg.objects.filter.return_value = m_cfg_qs

            with mock.patch('django.utils.timezone.now', return_value=mock.MagicMock(
                isoformat=lambda: '2025-01-01T00:00:00',
            )):
                from parametric_bom.bom_expander import evaluate_part

                result = evaluate_part(parent, {})
                self.assertEqual(result['total_bom_items'], 1)

    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_empty_condition_means_included(self, mock_config_cls, mock_pbom_cls):
        """Test that an empty condition_formula means the item is always included."""
        parent = MockPart('Parent', pk=1)
        child = MockPart('Child', pk=2)
        parent.add_bom_item(child, quantity=1.0)

        mock_pbom_cls.DoesNotExist = _DoesNotExist
        mock_pbom_cls.objects.get.side_effect = _DoesNotExist()

        mock_cfg_qs = mock.MagicMock()
        mock_cfg_qs.exists.return_value = False
        mock_config_cls.objects.filter.return_value = mock_cfg_qs

        from parametric_bom.bom_expander import expand_bom_level

        tree = expand_bom_level(parent, params={}, max_depth=10)

        self.assertEqual(len(tree['children']), 1)
        self.assertFalse(tree['children'][0]['excluded'])


# ══════════════════════════════════════════════
#  Tests for helper functions
# ══════════════════════════════════════════════


class TestHelpers(TestCase):
    """Tests for internal helper functions."""

    def test_part_display(self):
        """Test _part_display helper."""
        from parametric_bom.bom_expander import _part_display

        p = MockPart('MyPart')
        self.assertEqual(_part_display(p), 'MyPart')

        p.full_name = 'MyPart (Full)'
        self.assertEqual(_part_display(p), 'MyPart (Full)')

    def test_part_pk(self):
        """Test _part_pk helper."""
        from parametric_bom.bom_expander import _part_pk

        p = MockPart('Test', pk=42)
        self.assertEqual(_part_pk(p), 42)

    def test_coerce_value(self):
        """Test _coerce_value helper."""
        from parametric_bom.bom_expander import _coerce_value

        self.assertEqual(_coerce_value('42'), 42)
        self.assertEqual(_coerce_value('3.14'), 3.14)
        self.assertEqual(_coerce_value('true'), True)
        self.assertEqual(_coerce_value('false'), False)
        self.assertEqual(_coerce_value('hello'), 'hello')
        self.assertIsNone(_coerce_value(None))

    def test_compute_total_quantity(self):
        """Test _compute_total_quantity."""
        from parametric_bom.bom_expander import _compute_total_quantity

        self.assertEqual(_compute_total_quantity({'children': []}), 0)

        tree = {
            'children': [
                {'excluded': False, 'children': []},
            ]
        }
        self.assertEqual(_compute_total_quantity(tree), 1)

        tree = {
            'children': [
                {'excluded': True, 'children': []},
            ]
        }
        self.assertEqual(_compute_total_quantity(tree), 0)

        tree = {
            'children': [
                {'excluded': False, 'children': []},
                {
                    'excluded': False,
                    'children': [
                        {'excluded': False, 'children': []},
                    ],
                },
            ]
        }
        self.assertEqual(_compute_total_quantity(tree), 3)

    def test_flatten_bom(self):
        """Test _flatten_bom helper."""
        from parametric_bom.bom_expander import _flatten_bom

        tree = {
            'children': [
                {'part_id': 1, 'calculated_quantity': 2.0, 'children': []},
                {
                    'part_id': 2,
                    'calculated_quantity': 1.0,
                    'children': [
                        {'part_id': 3, 'calculated_quantity': 4.0, 'children': []},
                    ],
                },
            ]
        }
        flat = _flatten_bom(tree)
        self.assertIn((1, 2.0), flat)
        self.assertIn((2, 1.0), flat)
        self.assertIn((3, 4.0), flat)

    def test_flatten_bom_excluded(self):
        """Test excluded items are skipped in flatten."""
        from parametric_bom.bom_expander import _flatten_bom

        tree = {
            'children': [
                {'part_id': 1, 'calculated_quantity': 1.0, 'excluded': True, 'children': []},
                {'part_id': 2, 'calculated_quantity': 1.0, 'children': []},
            ]
        }
        flat = _flatten_bom(tree)
        self.assertEqual(len(flat), 1)
        self.assertEqual(flat[0], (2, 1.0))

    def test_compute_bom_hash(self):
        """Test compute_bom_hash is deterministic."""
        from parametric_bom.bom_expander import compute_bom_hash

        tree1 = {
            'children': [
                {'part_id': 1, 'calculated_quantity': 2.0, 'children': []},
            ]
        }
        tree2 = {
            'children': [
                {'part_id': 1, 'calculated_quantity': 2.0, 'children': []},
            ]
        }

        h1 = compute_bom_hash(tree1)
        h2 = compute_bom_hash(tree2)

        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 16)
