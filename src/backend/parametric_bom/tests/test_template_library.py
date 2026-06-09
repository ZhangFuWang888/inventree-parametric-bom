"""Tests for the Template Library Service.

Tests the core functions in template_library.py:
  - sync_part_params_from_category()
  - get_category_template_detail()
  - bulk_assign_templates()
  - auto_sync_for_new_part()

Run with:
  SKIP_MIGRATIONS=1 DJANGO_SETTINGS_MODULE=InvenTree.settings \
    venv/bin/python -m pytest parametric_bom/tests/test_template_library.py -v

All tests use unittest.TestCase (not django.test.TestCase) because all
Django model queries are mocked. No database access is required.
"""

from unittest import TestCase, mock

# Real exception references — needed because @mock.patch replaces model classes
# with MagicMock, making Model.DoesNotExist a non-exception.
from part.models import PartCategory as _RealPartCategory
from common.models import ParameterTemplate as _RealParameterTemplate


# ══════════════════════════════════════════════
#  Tests for sync_part_params_from_category
# ══════════════════════════════════════════════


class TestSyncPartParamsFromCategory(TestCase):
    """Tests for the sync_part_params_from_category() function."""

    @mock.patch('part.models.PartCategoryParameterTemplate')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_sync_creates_new_configs(self, mock_cfg_cls, mock_cat_tpl_cls):
        from parametric_bom.template_library import sync_part_params_from_category

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.category = mock.MagicMock()
        mock_part.category.pk = 10
        mock_part.category.get_ancestors.return_value = [mock_part.category]

        mock_template = mock.MagicMock()
        mock_template.pk = 100
        mock_template.name = 'length'

        mock_cat_tpl = mock.MagicMock()
        mock_cat_tpl.template = mock_template
        mock_cat_tpl.default_value = '5000'

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value.order_by.return_value = [mock_cat_tpl]
        mock_cat_tpl_cls.objects.filter.return_value = mock_qs

        # Config does not exist yet
        mock_cfg_cls.objects.filter.return_value.exists.return_value = False

        result = sync_part_params_from_category(mock_part)

        self.assertEqual(result['created'], 1)
        self.assertEqual(result['skipped'], 0)
        mock_cfg_cls.objects.create.assert_called_once()

    @mock.patch('part.models.PartCategoryParameterTemplate')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_sync_skips_existing_configs(self, mock_cfg_cls, mock_cat_tpl_cls):
        from parametric_bom.template_library import sync_part_params_from_category

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.category = mock.MagicMock()
        mock_part.category.pk = 10
        mock_part.category.get_ancestors.return_value = [mock_part.category]

        mock_template = mock.MagicMock()
        mock_template.pk = 100

        mock_cat_tpl = mock.MagicMock()
        mock_cat_tpl.template = mock_template
        mock_cat_tpl.default_value = '5000'

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value.order_by.return_value = [mock_cat_tpl]
        mock_cat_tpl_cls.objects.filter.return_value = mock_qs

        # Config already exists
        mock_cfg_cls.objects.filter.return_value.exists.return_value = True

        result = sync_part_params_from_category(mock_part)

        self.assertEqual(result['created'], 0)
        self.assertEqual(result['skipped'], 1)
        mock_cfg_cls.objects.create.assert_not_called()

    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_sync_no_category_returns_empty(self, mock_cfg_cls):
        from parametric_bom.template_library import sync_part_params_from_category

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.category = None

        result = sync_part_params_from_category(mock_part)

        self.assertEqual(result['created'], 0)
        self.assertEqual(result['skipped'], 0)
        self.assertEqual(len(result['errors']), 0)

    @mock.patch('part.models.PartCategoryParameterTemplate')
    @mock.patch('parametric_bom.models.PartParameterConfig')
    def test_sync_skips_duplicate_templates_across_ancestors(self, mock_cfg_cls, mock_cat_tpl_cls):
        from parametric_bom.template_library import sync_part_params_from_category

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_cat1 = mock.MagicMock()
        mock_cat1.pk = 10
        mock_cat2 = mock.MagicMock()
        mock_cat2.pk = 20
        mock_part.category = mock_cat2
        mock_part.category.get_ancestors.return_value = [mock_cat1, mock_cat2]

        mock_template = mock.MagicMock()
        mock_template.pk = 100  # Same template across both categories

        mock_cat_tpl1 = mock.MagicMock()
        mock_cat_tpl1.template = mock_template
        mock_cat_tpl1.default_value = ''

        mock_cat_tpl2 = mock.MagicMock()
        mock_cat_tpl2.template = mock_template
        mock_cat_tpl2.default_value = 'override'

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value.order_by.return_value = [mock_cat_tpl1, mock_cat_tpl2]
        mock_cat_tpl_cls.objects.filter.return_value = mock_qs

        mock_cfg_cls.objects.filter.return_value.exists.return_value = False

        result = sync_part_params_from_category(mock_part)

        # Should only have created 1 config (duplicate skipped)
        self.assertEqual(result['created'], 1)


# ══════════════════════════════════════════════
#  Tests for get_category_template_detail
# ══════════════════════════════════════════════


class TestGetCategoryTemplateDetail(TestCase):
    """Tests for the get_category_template_detail() function."""

    @mock.patch('parametric_bom.models.PartParameterConfig')
    @mock.patch('part.models.Part')
    @mock.patch('part.models.PartCategoryParameterTemplate')
    @mock.patch('part.models.PartCategory')
    def test_get_detail_success(self, mock_cat_cls, mock_cat_tpl_cls,
                                mock_part_cls, mock_cfg_cls):
        from parametric_bom.template_library import get_category_template_detail

        mock_category = mock.MagicMock()
        mock_category.pk = 10
        mock_category.name = 'Electronics'
        mock_cat_cls.objects.get.return_value = mock_category

        mock_template = mock.MagicMock()
        mock_template.pk = 100
        mock_template.name = 'voltage'

        mock_cat_tpl = mock.MagicMock()
        mock_cat_tpl.template = mock_template
        mock_cat_tpl.default_value = '12'
        mock_cat_tpl.pk = 500

        mock_cat_tpl_qs = mock.MagicMock()
        mock_cat_tpl_qs.select_related.return_value = [mock_cat_tpl]
        mock_cat_tpl_cls.objects.filter.return_value = mock_cat_tpl_qs

        # Mock parts in category
        mock_part_qs = mock.MagicMock()
        mock_part_qs.filter.return_value.values_list.return_value.distinct.return_value = [1, 2, 3]
        mock_part_cls.objects.filter.return_value = mock_part_qs

        # Mock config count
        mock_cfg_qs = mock.MagicMock()
        mock_cfg_qs.count.return_value = 5
        mock_cfg_cls.objects.filter.return_value = mock_cfg_qs

        result = get_category_template_detail(10)

        self.assertIn('templates', result)
        self.assertEqual(result['category_name'], 'Electronics')
        self.assertEqual(result['summary']['total_templates'], 1)
        self.assertEqual(result['templates'][0]['template_name'], 'voltage')
        self.assertEqual(result['templates'][0]['parametric_config_count'], 5)
        self.assertEqual(result['templates'][0]['category_template_id'], 500)

    def test_get_detail_not_found(self):
        from parametric_bom.template_library import get_category_template_detail

        mock_cat_cls = mock.MagicMock()
        mock_cat_cls.objects.get.side_effect = _RealPartCategory.DoesNotExist()

        with mock.patch('part.models.PartCategory', mock_cat_cls):
            result = get_category_template_detail(999)

        self.assertIn('error', result)
        self.assertIn('not found', result['error'])


# ══════════════════════════════════════════════
#  Tests for bulk_assign_templates
# ══════════════════════════════════════════════


class TestBulkAssignTemplates(TestCase):
    """Tests for the bulk_assign_templates() function."""

    @mock.patch('common.models.ParameterTemplate')
    @mock.patch('part.models.PartCategoryParameterTemplate')
    @mock.patch('part.models.PartCategory')
    def test_bulk_assign_new_templates(self, mock_cat_cls, mock_cat_tpl_cls, mock_pt_cls):
        from parametric_bom.template_library import bulk_assign_templates

        mock_category = mock.MagicMock()
        mock_category.pk = 10
        mock_cat_cls.objects.get.return_value = mock_category

        # Mock the existing queryset to have no existing templates
        mock_existing_qs = mock.MagicMock()
        mock_existing_qs.values_list.return_value = []
        # .filter(category=category) should return the mock
        mock_cat_tpl_cls.objects.filter.return_value = mock_existing_qs
        # .delete() returns (count, details_dict)
        mock_existing_qs.filter.return_value.delete.return_value = (0, {})

        # Template exists
        mock_template = mock.MagicMock()
        mock_template.pk = 100
        mock_template.name = 'length'
        mock_pt_cls.objects.get.return_value = mock_template

        result = bulk_assign_templates(10, [{'template_id': 100, 'default_value': '500'}])

        self.assertEqual(result['assigned'], 1)
        self.assertEqual(result['removed'], 0)
        self.assertEqual(len(result['errors']), 0)

    @mock.patch('part.models.PartCategoryParameterTemplate')
    @mock.patch('part.models.PartCategory')
    def test_bulk_assign_replaces_existing(self, mock_cat_cls, mock_cat_tpl_cls):
        from parametric_bom.template_library import bulk_assign_templates

        mock_category = mock.MagicMock()
        mock_category.pk = 10
        mock_cat_cls.objects.get.return_value = mock_category

        # Existing templates: ids {100, 200}
        mock_existing_qs = mock.MagicMock()
        mock_existing_qs.values_list.return_value = [100, 200]
        mock_cat_tpl_cls.objects.filter.return_value = mock_existing_qs
        mock_existing_qs.filter.return_value.delete.return_value = (1, {})

        # Incoming: only template 100 (so 200 should be removed)
        result = bulk_assign_templates(10, [100])

        self.assertEqual(result['removed'], 1)

    @mock.patch('common.models.ParameterTemplate')
    @mock.patch('part.models.PartCategoryParameterTemplate')
    @mock.patch('part.models.PartCategory')
    def test_bulk_assign_template_not_found(self, mock_cat_cls, mock_cat_tpl_cls, mock_pt_cls):
        from parametric_bom.template_library import bulk_assign_templates

        mock_category = mock.MagicMock()
        mock_category.pk = 10
        mock_cat_cls.objects.get.return_value = mock_category

        mock_existing_qs = mock.MagicMock()
        mock_existing_qs.values_list.return_value = []
        mock_cat_tpl_cls.objects.filter.return_value = mock_existing_qs
        mock_existing_qs.filter.return_value.delete.return_value = (0, {})

        mock_pt_cls.objects.get.side_effect = _RealParameterTemplate.DoesNotExist()

        result = bulk_assign_templates(10, [{'template_id': 999}])

        self.assertEqual(result['assigned'], 0)
        self.assertGreater(len(result['errors']), 0)

    def test_bulk_assign_category_not_found(self):
        from parametric_bom.template_library import bulk_assign_templates

        mock_cat_cls = mock.MagicMock()
        mock_cat_cls.objects.get.side_effect = _RealPartCategory.DoesNotExist()

        with mock.patch('part.models.PartCategory', mock_cat_cls):
            result = bulk_assign_templates(999, [])

        self.assertIn('error', result)

    @mock.patch('part.models.PartCategoryParameterTemplate')
    @mock.patch('part.models.PartCategory')
    def test_bulk_assign_invalid_template_id(self, mock_cat_cls, mock_cat_tpl_cls):
        from parametric_bom.template_library import bulk_assign_templates

        mock_category = mock.MagicMock()
        mock_category.pk = 10
        mock_cat_cls.objects.get.return_value = mock_category

        mock_existing_qs = mock.MagicMock()
        mock_existing_qs.values_list.return_value = []
        mock_cat_tpl_cls.objects.filter.return_value = mock_existing_qs
        mock_existing_qs.filter.return_value.delete.return_value = (0, {})

        result = bulk_assign_templates(10, [{'template_id': 'not-a-number'}])

        self.assertGreater(len(result['errors']), 0)


# ══════════════════════════════════════════════
#  Tests for auto_sync_for_new_part
# ══════════════════════════════════════════════


class TestAutoSyncForNewPart(TestCase):
    """Tests for the auto_sync_for_new_part() function."""

    @mock.patch('parametric_bom.template_library.sync_part_params_from_category')
    def test_auto_sync_syncs_from_category(self, mock_sync):
        from parametric_bom.template_library import auto_sync_for_new_part

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.variant_of = None  # No parent

        mock_sync.return_value = {'created': 2, 'skipped': 1, 'errors': []}

        result = auto_sync_for_new_part(mock_part)

        self.assertEqual(result['synced_from_category']['created'], 2)
        self.assertEqual(result['inherited_from_parent']['created'], 0)
        mock_sync.assert_called_once_with(mock_part)

    @mock.patch('parametric_bom.template_library.sync_part_params_from_category')
    def test_auto_sync_inherits_from_parent(self, mock_sync):
        from parametric_bom.template_library import auto_sync_for_new_part

        mock_parent = mock.MagicMock()
        mock_parent.pk = 10

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.variant_of = mock_parent

        mock_sync.return_value = {'created': 0, 'skipped': 0, 'errors': []}

        mock_parent_config = mock.MagicMock()
        mock_parent_config.template = mock.MagicMock()
        mock_parent_config.template.pk = 100
        mock_parent_config.default_value = '500'
        mock_parent_config.min_value = None
        mock_parent_config.max_value = None
        mock_parent_config.options = None
        mock_parent_config.is_driving = True
        mock_parent_config.is_computed = False
        mock_parent_config.computation_formula = ''
        mock_parent_config.ui_hint = ''
        mock_parent_config.display_order = 0
        mock_parent_config.visible_on_config = True

        with mock.patch('parametric_bom.models.PartParameterConfig') as mock_cfg_cls:
            mock_cfg_cls.objects.filter.return_value.select_related.return_value = [mock_parent_config]
            # Config does not exist on child
            mock_cfg_cls.objects.filter.return_value.exists.return_value = False

            result = auto_sync_for_new_part(mock_part)

        self.assertEqual(result['inherited_from_parent']['created'], 1)

    @mock.patch('parametric_bom.template_library.sync_part_params_from_category')
    def test_auto_sync_handles_sync_error(self, mock_sync):
        from parametric_bom.template_library import auto_sync_for_new_part

        mock_part = mock.MagicMock()
        mock_part.pk = 1
        mock_part.variant_of = None

        mock_sync.side_effect = RuntimeError('Something went wrong')

        result = auto_sync_for_new_part(mock_part)

        self.assertGreater(len(result['errors']), 0)
        self.assertIn('Category sync failed', result['errors'][0])
