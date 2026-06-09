"""Tests for the Cost Estimator Service.

Tests the core functions in cost_estimator.py:
  - estimate_configuration_cost()
  - estimate_part_cost()
  - estimate_from_bom_tree()
  - _flatten_bom_for_cost()
  - _get_part_unit_cost()

Run with:
  SKIP_MIGRATIONS=1 DJANGO_SETTINGS_MODULE=InvenTree.settings \
    venv/bin/python -m pytest parametric_bom/tests/test_cost_estimator.py -v

All tests use unittest.TestCase (not django.test.TestCase) because all
Django model queries are mocked. No database access is required.
"""

from unittest import TestCase, mock
from decimal import Decimal

# Real exception references — these are needed because @mock.patch('part.models.Part')
# replaces the Part class with a MagicMock, making Part.DoesNotExist a MagicMock
# instead of a real exception class.
from part.models import Part as _RealPart, PartPricing as _RealPartPricing


# ══════════════════════════════════════════════
#  Sample BOM tree data for tests
# ══════════════════════════════════════════════

SINGLE_LEAF_TREE = {
    'part_id': 1,
    'part_name': 'Assembly',
    'children': [
        {
            'part_id': 2,
            'part_name': 'Bolt',
            'quantity': 4,
            'calculated_quantity': 4.0,
            'children': [],
            'excluded': False,
        },
    ],
}

MULTI_LEAF_TREE = {
    'part_id': 1,
    'part_name': 'Assembly',
    'children': [
        {
            'part_id': 2,
            'part_name': 'Bolt',
            'quantity': 4,
            'calculated_quantity': 4.0,
            'children': [],
            'excluded': False,
        },
        {
            'part_id': 3,
            'part_name': 'Nut',
            'quantity': 4,
            'calculated_quantity': 4.0,
            'children': [],
            'excluded': False,
        },
    ],
}

NESTED_TREE = {
    'part_id': 1,
    'part_name': 'Assembly',
    'children': [
        {
            'part_id': 2,
            'part_name': 'SubAssembly',
            'quantity': 1,
            'calculated_quantity': 1.0,
            'children': [
                {
                    'part_id': 3,
                    'part_name': 'Bolt',
                    'quantity': 4,
                    'calculated_quantity': 4.0,
                    'children': [],
                    'excluded': False,
                },
            ],
            'excluded': False,
        },
    ],
}

TREE_WITH_EXCLUDED = {
    'part_id': 1,
    'part_name': 'Assembly',
    'children': [
        {
            'part_id': 2,
            'part_name': 'Included',
            'quantity': 2,
            'calculated_quantity': 2.0,
            'children': [],
            'excluded': False,
        },
        {
            'part_id': 3,
            'part_name': 'Excluded',
            'quantity': 5,
            'calculated_quantity': 5.0,
            'children': [],
            'excluded': True,
        },
    ],
}


# ══════════════════════════════════════════════
#  Tests for _flatten_bom_for_cost
# ══════════════════════════════════════════════


class TestFlattenBomForCost(TestCase):
    """Tests for the _flatten_bom_for_cost helper."""

    def test_single_leaf(self):
        from parametric_bom.cost_estimator import _flatten_bom_for_cost
        items = _flatten_bom_for_cost(SINGLE_LEAF_TREE)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['part_id'], 2)
        self.assertEqual(items[0]['quantity'], 4.0)

    def test_multiple_leaves(self):
        from parametric_bom.cost_estimator import _flatten_bom_for_cost
        items = _flatten_bom_for_cost(MULTI_LEAF_TREE)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['part_id'], 2)
        self.assertEqual(items[1]['part_id'], 3)

    def test_nested_assembly(self):
        from parametric_bom.cost_estimator import _flatten_bom_for_cost
        items = _flatten_bom_for_cost(NESTED_TREE)
        self.assertEqual(len(items), 1)
        # Quantity = 1 (parent) * 4 (child) = 4
        self.assertEqual(items[0]['quantity'], 4.0)

    def test_excluded_items_skipped(self):
        from parametric_bom.cost_estimator import _flatten_bom_for_cost
        items = _flatten_bom_for_cost(TREE_WITH_EXCLUDED)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['part_id'], 2)

    def test_no_children_returns_empty(self):
        from parametric_bom.cost_estimator import _flatten_bom_for_cost
        items = _flatten_bom_for_cost({'part_id': 1, 'children': []})
        self.assertEqual(len(items), 0)

    def test_uses_actual_part_id_when_available(self):
        from parametric_bom.cost_estimator import _flatten_bom_for_cost
        tree = {
            'part_id': 1,
            'children': [
                {
                    'part_id': 2,
                    'actual_part_id': 5,
                    'part_name': 'Selected',
                    'quantity': 1,
                    'calculated_quantity': 1.0,
                    'children': [],
                    'excluded': False,
                },
            ],
        }
        items = _flatten_bom_for_cost(tree)
        self.assertEqual(items[0]['part_id'], 5)


# ══════════════════════════════════════════════
#  Tests for _get_part_unit_cost
# ══════════════════════════════════════════════


class TestGetPartUnitCost(TestCase):
    """Tests for the _get_part_unit_cost helper."""

    @mock.patch('part.models.Part')
    @mock.patch('part.models.PartPricing')
    def test_internal_pricing_success(self, mock_pricing_cls, mock_part_cls):
        from parametric_bom.cost_estimator import _get_part_unit_cost

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.name = 'Bolt'
        mock_part_cls.objects.get.return_value = mock_part

        mock_pricing = mock.MagicMock()
        mock_cost = mock.MagicMock()
        mock_cost.amount = Decimal('2.50')
        mock_cost.currency = 'USD'
        mock_pricing.internal_cost_min = mock_cost
        mock_pricing.internal_cost_max = None
        mock_pricing.overall_min = None
        mock_part.pricing_data = mock_pricing

        cost, currency, error = _get_part_unit_cost(1, 'internal')
        self.assertEqual(cost, Decimal('2.50'))
        self.assertEqual(currency, 'USD')
        self.assertIsNone(error)

    @mock.patch('part.models.Part')
    @mock.patch('part.models.PartPricing')
    def test_falls_back_to_max_field(self, mock_pricing_cls, mock_part_cls):
        from parametric_bom.cost_estimator import _get_part_unit_cost

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.name = 'Bolt'
        mock_part_cls.objects.get.return_value = mock_part

        mock_pricing = mock.MagicMock()
        mock_pricing.internal_cost_min = None
        mock_cost = mock.MagicMock()
        mock_cost.amount = Decimal('3.00')
        mock_cost.currency = 'USD'
        mock_pricing.internal_cost_max = mock_cost
        mock_pricing.overall_min = None
        mock_part.pricing_data = mock_pricing

        cost, currency, error = _get_part_unit_cost(1, 'internal')
        self.assertEqual(cost, Decimal('3.00'))

    @mock.patch('part.models.Part')
    @mock.patch('part.models.PartPricing')
    def test_falls_back_to_overall_min(self, mock_pricing_cls, mock_part_cls):
        from parametric_bom.cost_estimator import _get_part_unit_cost

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.name = 'Bolt'
        mock_part_cls.objects.get.return_value = mock_part

        mock_pricing = mock.MagicMock()
        mock_pricing.internal_cost_min = None
        mock_pricing.internal_cost_max = None
        mock_cost = mock.MagicMock()
        mock_cost.amount = Decimal('5.00')
        mock_cost.currency = 'USD'
        mock_pricing.overall_min = mock_cost
        mock_part.pricing_data = mock_pricing

        cost, currency, error = _get_part_unit_cost(1, 'internal')
        self.assertEqual(cost, Decimal('5.00'))

    @mock.patch('part.models.Part')
    def test_part_not_found(self, mock_part_cls):
        from parametric_bom.cost_estimator import _get_part_unit_cost

        mock_part_cls.objects.get.side_effect = _RealPart.DoesNotExist()

        cost, currency, error = _get_part_unit_cost(999, 'internal')
        self.assertIsNone(cost)
        self.assertIsNotNone(error)
        self.assertIn('not found', error)

    @mock.patch('part.models.Part')
    @mock.patch('part.models.PartPricing')
    def test_no_pricing_data(self, mock_pricing_cls, mock_part_cls):
        from parametric_bom.cost_estimator import _get_part_unit_cost

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.name = 'Bolt'
        mock_part_cls.objects.get.return_value = mock_part

        mock_part.pricing_data = None

        cost, currency, error = _get_part_unit_cost(1, 'internal')
        self.assertIsNone(cost)
        self.assertIsNotNone(error)
        self.assertIn('No pricing data', error)

    @mock.patch('part.models.Part')
    @mock.patch('part.models.PartPricing')
    def test_pricing_does_not_exist(self, mock_pricing_cls, mock_part_cls):
        from parametric_bom.cost_estimator import _get_part_unit_cost

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.name = 'Bolt'
        mock_part_cls.objects.get.return_value = mock_part
        mock_part.pricing_data = None

        # Simulate PartPricing.DoesNotExist on access
        with mock.patch.object(type(mock_part), 'pricing_data', new_callable=mock.PropertyMock) as m_pd:
            m_pd.side_effect = _RealPartPricing.DoesNotExist()

            cost, currency, error = _get_part_unit_cost(1, 'internal')
            self.assertIsNone(cost)
            self.assertIsNotNone(error)
            self.assertIn('No pricing data', error)


# ══════════════════════════════════════════════
#  Tests for estimate_from_bom_tree
# ══════════════════════════════════════════════


class TestEstimateFromBomTree(TestCase):
    """Tests for the estimate_from_bom_tree() function."""

    @mock.patch('parametric_bom.cost_estimator._get_part_unit_cost')
    def test_basic_estimate(self, mock_get_cost):
        from parametric_bom.cost_estimator import estimate_from_bom_tree

        mock_get_cost.return_value = (Decimal('2.50'), 'USD', None)

        result = estimate_from_bom_tree(SINGLE_LEAF_TREE)

        self.assertEqual(result['total_cost'], 10.0)  # 4 * 2.50
        self.assertEqual(result['currency'], 'USD')
        self.assertEqual(result['item_count'], 1)
        self.assertEqual(len(result['errors']), 0)

    @mock.patch('parametric_bom.cost_estimator._get_part_unit_cost')
    def test_multi_item_estimate(self, mock_get_cost):
        from parametric_bom.cost_estimator import estimate_from_bom_tree

        mock_get_cost.return_value = (Decimal('1.00'), 'USD', None)

        result = estimate_from_bom_tree(MULTI_LEAF_TREE)

        self.assertEqual(result['total_cost'], 8.0)  # 4*1.00 + 4*1.00
        self.assertEqual(result['item_count'], 2)

    @mock.patch('parametric_bom.cost_estimator._get_part_unit_cost')
    def test_estimate_with_markup(self, mock_get_cost):
        from parametric_bom.cost_estimator import estimate_from_bom_tree

        mock_get_cost.return_value = (Decimal('10.00'), 'USD', None)

        result = estimate_from_bom_tree(SINGLE_LEAF_TREE, markup_pct=15)

        self.assertAlmostEqual(result['total_cost'], 46.0)  # 40 * 1.15
        self.assertEqual(result['total_cost_before_markup'], 40.0)
        self.assertEqual(result['markup_pct'], 15)

    @mock.patch('parametric_bom.cost_estimator._get_part_unit_cost')
    def test_estimate_with_pricing_error(self, mock_get_cost):
        from parametric_bom.cost_estimator import estimate_from_bom_tree

        mock_get_cost.return_value = (None, None, 'No pricing data for part 2 (Bolt)')

        result = estimate_from_bom_tree(SINGLE_LEAF_TREE)

        self.assertEqual(result['item_count'], 1)
        self.assertEqual(len(result['errors']), 1)
        self.assertIsNone(result['items'][0]['unit_cost'])
        self.assertIsNone(result['items'][0]['subtotal'])

    @mock.patch('parametric_bom.cost_estimator._get_part_unit_cost')
    def test_estimate_tracks_first_currency(self, mock_get_cost):
        from parametric_bom.cost_estimator import estimate_from_bom_tree

        def cost_side_effect(part_id, preference):
            if part_id == 2:
                return (Decimal('1.00'), 'EUR', None)
            elif part_id == 3:
                return (Decimal('2.00'), 'GBP', None)
            return (None, None, 'error')

        mock_get_cost.side_effect = cost_side_effect

        result = estimate_from_bom_tree(MULTI_LEAF_TREE)

        # First non-None currency is EUR
        self.assertEqual(result['currency'], 'EUR')


# ══════════════════════════════════════════════
#  Tests for estimate_part_cost
# ══════════════════════════════════════════════


class TestEstimatePartCost(TestCase):
    """Tests for estimate_part_cost() function."""

    @mock.patch('parametric_bom.cost_estimator.estimate_from_bom_tree')
    @mock.patch('parametric_bom.bom_expander.evaluate_part')
    def test_estimate_part_cost_basic(self, mock_eval_part, mock_estimate):
        from parametric_bom.cost_estimator import estimate_part_cost

        mock_part = mock.MagicMock()
        mock_part.pk = 42
        mock_part.name = 'MyAssembly'

        mock_eval_part.return_value = {
            'bom_tree': SINGLE_LEAF_TREE,
            'part_id': 42,
            'part_name': 'MyAssembly',
            'parameters': {'speed': 10},
        }

        mock_estimate.return_value = {
            'total_cost': 10.0,
            'total_cost_before_markup': 10.0,
            'markup_pct': 0,
            'currency': 'USD',
            'items': [{'part_id': 2, 'quantity': 4, 'unit_cost': 2.5, 'subtotal': 10.0}],
            'errors': [],
            'item_count': 1,
        }

        result = estimate_part_cost(mock_part, {'speed': 10})

        self.assertEqual(result['part_id'], 42)
        self.assertEqual(result['part_name'], 'MyAssembly')
        self.assertEqual(result['total_cost'], 10.0)
        mock_eval_part.assert_called_once_with(mock_part, {'speed': 10}, 500, 10)

    @mock.patch('parametric_bom.cost_estimator.estimate_from_bom_tree')
    @mock.patch('parametric_bom.bom_expander.evaluate_part')
    def test_estimate_part_cost_custom_args(self, mock_eval_part, mock_estimate):
        from parametric_bom.cost_estimator import estimate_part_cost

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.name = 'Test'

        mock_eval_part.return_value = {
            'bom_tree': {},
            'part_id': 1,
            'part_name': 'Test',
            'parameters': {},
        }
        mock_estimate.return_value = {
            'total_cost': 0, 'items': [], 'errors': [], 'item_count': 0,
        }

        result = estimate_part_cost(mock_part, {}, markup_pct=20,
                                    pricing_preference='purchase',
                                    timeout_ms=100, max_depth=5)

        mock_eval_part.assert_called_once_with(mock_part, {}, 100, 5)
        mock_estimate.assert_called_once_with({}, 20, 'purchase')


# ══════════════════════════════════════════════
#  Tests for estimate_configuration_cost
# ══════════════════════════════════════════════


class TestEstimateConfigurationCost(TestCase):
    """Tests for estimate_configuration_cost() function."""

    @mock.patch('parametric_bom.cost_estimator.estimate_from_bom_tree')
    @mock.patch('parametric_bom.bom_expander.evaluate_configuration')
    def test_estimate_config_cost_basic(self, mock_eval_config, mock_estimate):
        from parametric_bom.cost_estimator import estimate_configuration_cost

        mock_config = mock.MagicMock()
        mock_config.pk = 1
        mock_config.title = 'My Config'

        mock_eval_config.return_value = {
            'bom_tree': SINGLE_LEAF_TREE,
            'part_id': 42,
            'part_name': 'Assembly',
            'parameters': {'speed': 10},
        }

        mock_estimate.return_value = {
            'total_cost': 10.0,
            'currency': 'USD',
            'items': [],
            'errors': [],
            'item_count': 1,
        }

        result = estimate_configuration_cost(mock_config)

        self.assertEqual(result['config_id'], 1)
        self.assertEqual(result['title'], 'My Config')
        self.assertEqual(result['total_cost'], 10.0)
        self.assertEqual(result['part_id'], 42)

    @mock.patch('parametric_bom.cost_estimator.estimate_from_bom_tree')
    @mock.patch('parametric_bom.bom_expander.evaluate_configuration')
    def test_estimate_config_cost_custom_preference(self, mock_eval_config, mock_estimate):
        from parametric_bom.cost_estimator import estimate_configuration_cost

        mock_config = mock.MagicMock()
        mock_config.pk = 1
        mock_config.title = 'My Config'

        mock_eval_config.return_value = {
            'bom_tree': {},
            'part_id': 0,
            'part_name': '',
            'parameters': {},
        }
        mock_estimate.return_value = {
            'total_cost': 0, 'items': [], 'errors': [], 'item_count': 0,
        }

        result = estimate_configuration_cost(mock_config, markup_pct=10,
                                             pricing_preference='supplier')

        mock_estimate.assert_called_once_with({}, 10, 'supplier')
