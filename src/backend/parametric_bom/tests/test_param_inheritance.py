"""Tests for the Parameter Inheritance Service.

Tests the core functions in param_inheritance.py:
  - inherit_from_template()
  - inherit_parent_params()
  - propagate_param_change()

Run with:
  SKIP_MIGRATIONS=1 DJANGO_SETTINGS_MODULE=InvenTree.settings \
    venv/bin/python -m pytest parametric_bom/tests/test_param_inheritance.py -v

All tests use unittest.TestCase (not django.test.TestCase) because all
Django model queries are mocked. No database access is required.
"""

from unittest import TestCase, mock


# ══════════════════════════════════════════════
#  Tests for inherit_parent_params
# ══════════════════════════════════════════════


class TestInheritParentParams(TestCase):
    """Tests for the inherit_parent_params() function."""

    def test_no_parent_params(self):
        from parametric_bom.param_inheritance import inherit_parent_params
        context = inherit_parent_params({'speed': 10, 'length': 500})
        self.assertEqual(context, {'param': {'speed': 10, 'length': 500}})
        self.assertNotIn('parent', context)

    def test_with_parent_params(self):
        from parametric_bom.param_inheritance import inherit_parent_params
        context = inherit_parent_params(
            {'speed': 10},
            parent_params={'parent_length': 8000},
        )
        self.assertIn('param', context)
        self.assertIn('parent', context)
        self.assertEqual(context['param'], {'speed': 10})
        self.assertEqual(context['parent'], {'parent_length': 8000})

    def test_empty_params(self):
        from parametric_bom.param_inheritance import inherit_parent_params
        context = inherit_parent_params({})
        self.assertEqual(context, {'param': {}})

    def test_parent_params_is_none(self):
        from parametric_bom.param_inheritance import inherit_parent_params
        context = inherit_parent_params({'x': 1}, parent_params=None)
        self.assertEqual(context, {'param': {'x': 1}})
        self.assertNotIn('parent', context)

    def test_context_is_copy_not_reference(self):
        from parametric_bom.param_inheritance import inherit_parent_params
        original = {'speed': 10}
        context = inherit_parent_params(original)
        original['speed'] = 20
        # Context should be a copy, not affected by mutation
        self.assertEqual(context['param']['speed'], 10)


# ══════════════════════════════════════════════
#  Tests for inherit_from_template
# ══════════════════════════════════════════════


class TestInheritFromTemplate(TestCase):
    """Tests for the inherit_from_template() function."""

    @mock.patch('django.db.backends.base.base.BaseDatabaseWrapper.get_autocommit', return_value=True)
    def test_no_variant_of(self, mock_autocommit):
        """Test that a part with no variant_of returns zero counts."""
        from parametric_bom.param_inheritance import inherit_from_template

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.variant_of = None

        result = inherit_from_template(mock_part)

        self.assertEqual(result['configs_copied'], 0)
        self.assertEqual(result['bom_items_copied'], 0)

    @mock.patch('django.db.backends.base.base.BaseDatabaseWrapper.get_autocommit', return_value=True)
    @mock.patch('parametric_bom.models.ParametricBomItem')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    @mock.patch('part.models.BomItem')
    def test_inherit_configs_and_bom_items(self, mock_bom_cls, mock_cfg_cls,
                                           mock_param_bom_cls, mock_autocommit):
        from parametric_bom.param_inheritance import inherit_from_template

        mock_template_part = mock.MagicMock()
        mock_template_part.pk = 10

        mock_variant = mock.MagicMock()
        mock_variant.pk = 1
        mock_variant.variant_of = mock_template_part

        # Mock template configs
        mock_template_cfg = mock.MagicMock()
        mock_template_cfg.template = mock.MagicMock()
        mock_template_cfg.template.pk = 100
        mock_template_cfg.default_value = '500'
        mock_template_cfg.min_value = None
        mock_template_cfg.max_value = None
        mock_template_cfg.options = None
        mock_template_cfg.is_driving = True
        mock_template_cfg.is_computed = False
        mock_template_cfg.computation_formula = ''
        mock_template_cfg.ui_hint = ''
        mock_template_cfg.display_order = 0
        mock_template_cfg.visible_on_config = True

        mock_cfg_cls.objects.filter.return_value.select_related.return_value = [mock_template_cfg]
        mock_cfg_cls.objects.get_or_create.return_value = (mock.MagicMock(), True)

        # Mock template BOM items
        mock_tpl_bom = mock.MagicMock()
        mock_tpl_bom.sub_part_id = 200
        mock_tpl_bom.pk = 50
        mock_bom_cls.objects.filter.return_value.select_related.return_value = [mock_tpl_bom]

        # Mock variant BOM items
        mock_var_bom = mock.MagicMock()
        mock_var_bom.sub_part_id = 200
        mock_var_bom.pk = 60

        def bom_filter_side_effect(**kwargs):
            if 'part' in kwargs and hasattr(kwargs['part'], 'pk'):
                part = kwargs['part']
                if part.pk == 10:  # Template
                    mock_qs = mock.MagicMock()
                    mock_qs.select_related.return_value = [mock_tpl_bom]
                    return mock_qs
                elif part.pk == 1:  # Variant
                    mock_qs = mock.MagicMock()
                    mock_qs.select_related.return_value = [mock_var_bom]
                    return mock_qs
            return mock.MagicMock()

        mock_bom_cls.objects.filter.side_effect = bom_filter_side_effect

        # Mock parametric BOM item on template
        mock_tpl_param_bom = mock.MagicMock()
        mock_tpl_param_bom.qty_formula = 'param.speed * 2'
        mock_tpl_param_bom.condition_formula = ''
        mock_tpl_param_bom.part_selector_formula = ''
        mock_param_bom_cls.objects.get.return_value = mock_tpl_param_bom
        mock_param_bom_cls.DoesNotExist = type('DoesNotExist', (Exception,), {})

        result = inherit_from_template(mock_variant)

        self.assertEqual(result['configs_copied'], 1)
        self.assertEqual(result['bom_items_copied'], 1)

    @mock.patch('django.db.backends.base.base.BaseDatabaseWrapper.get_autocommit', return_value=True)
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_inherit_skips_existing_configs(self, mock_cfg_cls, mock_autocommit):
        """Test that existing configs on the variant are not duplicated."""
        from parametric_bom.param_inheritance import inherit_from_template

        mock_template_part = mock.MagicMock()
        mock_template_part.pk = 10

        mock_variant = mock.MagicMock()
        mock_variant.pk = 1
        mock_variant.variant_of = mock_template_part

        mock_template_cfg = mock.MagicMock()
        mock_template_cfg.template = mock.MagicMock()
        mock_template_cfg.template.pk = 100
        mock_template_cfg.default_value = ''

        mock_cfg_cls.objects.filter.return_value.select_related.return_value = [mock_template_cfg]
        # Simulate that get_or_create did NOT create (config already existed)
        mock_cfg_cls.objects.get_or_create.return_value = (mock.MagicMock(), False)

        with mock.patch('part.models.BomItem') as mock_bom_cls:
            mock_bom_cls.objects.filter.return_value.select_related.return_value = []
            result = inherit_from_template(mock_variant)

        # Config existed -> get_or_create returned (obj, False) -> we still count it
        self.assertEqual(result['configs_copied'], 1)


# ══════════════════════════════════════════════
#  Tests for propagate_param_change
# ══════════════════════════════════════════════


class TestPropagateParamChange(TestCase):
    """Tests for the propagate_param_change() function."""

    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_propagate_no_variants(self, mock_cfg_cls):
        """Test with a template that has no variants."""
        from parametric_bom.param_inheritance import propagate_param_change

        mock_config = mock.MagicMock()
        mock_config.pk = 1
        mock_config.part = mock.MagicMock()
        mock_config.part.pk = 10
        mock_config.template.name = 'length'

        mock_cfg_cls.objects.select_related.return_value.get.return_value = mock_config

        # No variant configs
        mock_cfg_cls.objects.filter.return_value.select_related.return_value = []

        result = propagate_param_change(1)

        self.assertEqual(result, [])

    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_propagate_with_variants(self, mock_cfg_cls):
        """Test propagation to variant parts."""
        from parametric_bom.param_inheritance import propagate_param_change

        mock_config = mock.MagicMock()
        mock_config.pk = 1
        mock_config.part = mock.MagicMock()
        mock_config.part.pk = 10
        mock_config.template.name = 'length'

        mock_cfg_cls.objects.select_related.return_value.get.return_value = mock_config

        # Mock variant configs
        mock_var_cfg = mock.MagicMock()
        mock_var_cfg.part.pk = 20
        mock_var_cfg.part.name = 'Variant A'

        mock_cfg_cls.objects.filter.return_value.select_related.return_value = [mock_var_cfg]

        result = propagate_param_change(1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['part_id'], 20)
        self.assertEqual(result[0]['part_name'], 'Variant A')
        self.assertEqual(result[0]['template_part_id'], 10)
        self.assertEqual(result[0]['parameter_template'], 'length')
        self.assertEqual(result[0]['config_id'], 1)

    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_propagate_config_not_found(self, mock_cfg_cls):
        """Test when the config doesn't exist."""
        from parametric_bom.param_inheritance import propagate_param_change
        from parametric_bom.models import PartParameterConfig

        mock_cfg_cls.objects.select_related.return_value.get.side_effect = (
            PartParameterConfig.DoesNotExist()
        )

        result = propagate_param_change(999)

        self.assertEqual(result, [])

    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_propagate_multiple_variants(self, mock_cfg_cls):
        """Test propagation to multiple variant parts."""
        from parametric_bom.param_inheritance import propagate_param_change

        mock_config = mock.MagicMock()
        mock_config.pk = 1
        mock_config.part = mock.MagicMock()
        mock_config.part.pk = 10
        mock_config.template.name = 'length'

        mock_cfg_cls.objects.select_related.return_value.get.return_value = mock_config

        mock_var_cfg_1 = mock.MagicMock()
        mock_var_cfg_1.part.pk = 20
        mock_var_cfg_1.part.name = 'Variant A'

        mock_var_cfg_2 = mock.MagicMock()
        mock_var_cfg_2.part.pk = 21
        mock_var_cfg_2.part.name = 'Variant B'

        mock_cfg_cls.objects.filter.return_value.select_related.return_value = [
            mock_var_cfg_1, mock_var_cfg_2,
        ]

        result = propagate_param_change(1)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['part_name'], 'Variant A')
        self.assertEqual(result[1]['part_name'], 'Variant B')
