"""Tests for the Variant Generator Service.

Tests the core functions in variant_generator.py:
  - generate_variant()
  - _flatten_bom_tree()
  - _walk_bom_tree()
  - _build_variant_name()

Run with:
  SKIP_MIGRATIONS=1 DJANGO_SETTINGS_MODULE=InvenTree.settings \
    venv/bin/python -m pytest parametric_bom/tests/test_variant_generator.py -v

All tests use unittest.TestCase (not django.test.TestCase) because all
Django model queries are mocked. No database access is required.
"""

from unittest import TestCase, mock


# ══════════════════════════════════════════════
#  Sample BOM tree data
# ══════════════════════════════════════════════

SAMPLE_BOM_TREE = {
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
            'optional': False,
            'consumable': False,
            'reference': '',
        },
        {
            'part_id': 3,
            'part_name': 'Nut',
            'quantity': 4,
            'calculated_quantity': 4.0,
            'children': [],
            'excluded': False,
            'optional': False,
            'consumable': False,
            'reference': '',
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
            'optional': False,
            'consumable': False,
            'reference': '',
        },
        {
            'part_id': 3,
            'part_name': 'Excluded',
            'quantity': 5,
            'calculated_quantity': 5.0,
            'children': [],
            'excluded': True,
            'optional': False,
            'consumable': False,
            'reference': '',
        },
    ],
}

TREE_WITH_ACTUAL_PART = {
    'part_id': 1,
    'part_name': 'Assembly',
    'children': [
        {
            'part_id': 2,
            'actual_part_id': 5,
            'part_name': 'Original',
            'actual_part_name': 'SelectedPart',
            'quantity': 3,
            'calculated_quantity': 3.0,
            'children': [],
            'excluded': False,
            'optional': False,
            'consumable': False,
            'reference': '',
        },
    ],
}


# ══════════════════════════════════════════════
#  Tests for _build_variant_name
# ══════════════════════════════════════════════


class TestBuildVariantName(TestCase):
    """Tests for the _build_variant_name helper."""

    def test_basic(self):
        from parametric_bom.variant_generator import _build_variant_name
        name = _build_variant_name('Motor', {'speed': 10, 'power': 'high'})
        self.assertIn('Motor', name)
        self.assertIn('speed=10', name)
        self.assertIn('power=high', name)

    def test_empty_params(self):
        from parametric_bom.variant_generator import _build_variant_name
        name = _build_variant_name('Motor', {})
        self.assertEqual(name, 'Motor ()')

    def test_none_value_uses_empty_string(self):
        from parametric_bom.variant_generator import _build_variant_name
        name = _build_variant_name('Motor', {'speed': None})
        self.assertIn('speed=', name)


# ══════════════════════════════════════════════
#  Tests for _flatten_bom_tree / _walk_bom_tree
# ══════════════════════════════════════════════


class TestFlattenBomTree(TestCase):
    """Tests for the _flatten_bom_tree helper."""

    def test_basic_flatten(self):
        from parametric_bom.variant_generator import _flatten_bom_tree
        items = _flatten_bom_tree(SAMPLE_BOM_TREE)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['part_id'], 2)
        self.assertEqual(items[1]['part_id'], 3)

    def test_excluded_skipped(self):
        from parametric_bom.variant_generator import _flatten_bom_tree
        items = _flatten_bom_tree(TREE_WITH_EXCLUDED)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['part_id'], 2)

    def test_uses_actual_part_id(self):
        from parametric_bom.variant_generator import _flatten_bom_tree
        items = _flatten_bom_tree(TREE_WITH_ACTUAL_PART)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['part_id'], 5)
        self.assertEqual(items[0]['part_name'], 'SelectedPart')

    def test_nested_structure(self):
        from parametric_bom.variant_generator import _flatten_bom_tree
        nested_tree = {
            'part_id': 1,
            'children': [
                {
                    'part_id': 2,
                    'part_name': 'Sub',
                    'quantity': 1,
                    'calculated_quantity': 1.0,
                    'children': [
                        {
                            'part_id': 3,
                            'part_name': 'Leaf',
                            'quantity': 4,
                            'calculated_quantity': 4.0,
                            'children': [],
                            'excluded': False,
                            'optional': False,
                            'consumable': False,
                            'reference': '',
                        },
                    ],
                    'excluded': False,
                    'optional': False,
                    'consumable': False,
                    'reference': '',
                },
            ],
        }
        items = _flatten_bom_tree(nested_tree)
        self.assertEqual(len(items), 2)  # Both Sub and Leaf are included


# ══════════════════════════════════════════════
#  Tests for generate_variant
# ══════════════════════════════════════════════


class TestGenerateVariant(TestCase):
    """Tests for the generate_variant() function."""

    def _make_mock_config(self, status='completed', has_params=True):
        """Create a mock ProductConfiguration."""
        mock_config = mock.MagicMock()
        mock_config.pk = 1
        mock_config.status = status
        mock_config.title = 'My Config'
        mock_config.revision = '1.0'

        mock_template_part = mock.MagicMock()
        mock_template_part.pk = 10
        mock_template_part.name = 'Motor'
        mock_template_part.category = None
        mock_config.template_part = mock_template_part

        if has_params:
            mock_param_val = mock.MagicMock()
            mock_param_val.template.name = 'speed'
            mock_param_val.value = '10'
            mock_param_val.pk = 1
            mock_config.parameter_values.all.return_value = [mock_param_val]
            mock_config.parameter_values.count.return_value = 1
        else:
            mock_config.parameter_values.all.return_value = []
            mock_config.parameter_values.count.return_value = 0

        return mock_config

    @mock.patch('django.db.transaction.atomic')
    @mock.patch('parametric_bom.variant_generator.BomItem')
    @mock.patch('parametric_bom.variant_generator.Parameter')
    @mock.patch('parametric_bom.variant_generator.ContentType')
    @mock.patch('parametric_bom.variant_generator.Part')
    @mock.patch('parametric_bom.variant_generator.evaluate_configuration')
    @mock.patch('parametric_bom.variant_generator.ProductConfiguration')
    @mock.patch('parametric_bom.variant_generator.ConfigParameterValue')
    def test_generate_variant_success(self, mock_cpv_cls, mock_config_cls,
                                      mock_eval_config, mock_part_cls,
                                      mock_ct_cls, mock_param_cls,
                                      mock_bomitem_cls, mock_atomic):
        from parametric_bom.variant_generator import generate_variant

        mock_config = self._make_mock_config()
        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value.prefetch_related.return_value.get.return_value = mock_config
        mock_config_cls.objects = mock_qs

        # Mock evaluation
        mock_eval_config.return_value = {
            'bom_tree': SAMPLE_BOM_TREE,
            'parameters': {'speed': 10, 'power': 'high'},
            'parameter_errors': [],
        }

        # Mock parameter value queryset
        mock_pv_qs = mock.MagicMock()
        mock_pv_qs.select_related.return_value = mock_config.parameter_values.all()
        mock_cpv_cls.objects.filter.return_value = mock_pv_qs

        # Mock Part creation
        mock_variant_part = mock.MagicMock()
        mock_variant_part.pk = 100
        mock_variant_part.name = 'Motor (speed=10, power=high)'
        mock_part_cls.objects.create.return_value = mock_variant_part

        # Mock ContentType
        mock_ct = mock.MagicMock()
        mock_ct_cls.objects.get_for_model.return_value = mock_ct

        # Mock ParameterTemplate lookup for computed params
        with mock.patch('parametric_bom.variant_generator.ParameterTemplate') as mock_pt_cls:
            mock_pt = mock.MagicMock()
            mock_pt.name = 'power'
            mock_pt_cls.objects.get.return_value = mock_pt

            result = generate_variant(1)

        self.assertTrue(result['success'])
        self.assertEqual(result['variant_part_id'], 100)
        self.assertEqual(result['config_id'], 1)
        self.assertGreater(result['bom_items_created'], 0)
        self.assertGreater(result['parameters_set'], 0)

    def test_generate_variant_config_not_found(self):
        from parametric_bom.variant_generator import generate_variant
        from parametric_bom.models import ProductConfiguration

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value.prefetch_related.return_value.get.side_effect = (
            ProductConfiguration.DoesNotExist()
        )

        with mock.patch('parametric_bom.variant_generator.ProductConfiguration.objects', mock_qs):
            result = generate_variant(999)

        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])

    @mock.patch('parametric_bom.variant_generator.ProductConfiguration')
    def test_generate_variant_wrong_status(self, mock_config_cls):
        from parametric_bom.variant_generator import generate_variant

        mock_config = self._make_mock_config(status='draft')
        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value.prefetch_related.return_value.get.return_value = mock_config
        mock_config_cls.objects = mock_qs

        result = generate_variant(1)

        self.assertFalse(result['success'])
        self.assertIn('status', result['error'])

    @mock.patch('parametric_bom.variant_generator.ProductConfiguration')
    def test_generate_variant_no_params(self, mock_config_cls):
        from parametric_bom.variant_generator import generate_variant

        mock_config = self._make_mock_config(has_params=False)
        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value.prefetch_related.return_value.get.return_value = mock_config
        mock_config_cls.objects = mock_qs

        result = generate_variant(1)

        self.assertFalse(result['success'])
        self.assertIn('no parameters', result['error'].lower())

    @mock.patch('django.db.transaction.atomic')
    @mock.patch('parametric_bom.variant_generator.evaluate_configuration')
    @mock.patch('parametric_bom.variant_generator.ProductConfiguration')
    def test_generate_variant_evaluation_error(self, mock_config_cls,
                                               mock_eval_config, mock_atomic):
        from parametric_bom.variant_generator import generate_variant

        mock_config = self._make_mock_config()
        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value.prefetch_related.return_value.get.return_value = mock_config
        mock_config_cls.objects = mock_qs

        mock_eval_config.side_effect = ValueError('BOM evaluation exploded')

        result = generate_variant(1)

        self.assertFalse(result['success'])
        self.assertIn('BOM evaluation failed', result['error'])
