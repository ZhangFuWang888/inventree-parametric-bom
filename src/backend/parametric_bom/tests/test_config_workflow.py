"""Tests for the Configuration Workflow Service.

Tests the core functions in config_workflow.py:
  - transition_status()
  - _validate_transition()
  - status_is_locked()
  - can_edit_parameters()
  - can_delete()
  - set_parameters()
  - delete_parameter()
  - snapshot_parameters()
  - get_configuration_detail()

Run with:
  SKIP_MIGRATIONS=1 DJANGO_SETTINGS_MODULE=InvenTree.settings \
    venv/bin/python -m pytest parametric_bom/tests/test_config_workflow.py -v

All tests use unittest.TestCase (not django.test.TestCase) because all
Django model queries are mocked. No database access is required.
"""

from unittest import TestCase, mock


# ══════════════════════════════════════════════
#  Tests for _validate_transition
# ══════════════════════════════════════════════


class TestValidateTransition(TestCase):
    """Tests for the _validate_transition() function."""

    def test_valid_transition_draft_to_completed(self):
        from parametric_bom.config_workflow import _validate_transition
        self.assertIsNone(_validate_transition('draft', 'completed'))

    def test_valid_transition_completed_to_released(self):
        from parametric_bom.config_workflow import _validate_transition
        self.assertIsNone(_validate_transition('completed', 'released'))

    def test_valid_transition_released_to_obsolete(self):
        from parametric_bom.config_workflow import _validate_transition
        self.assertIsNone(_validate_transition('released', 'obsolete'))

    def test_invalid_transition_draft_to_released(self):
        from parametric_bom.config_workflow import _validate_transition
        error = _validate_transition('draft', 'released')
        self.assertIsNotNone(error)
        self.assertIn('Cannot transition', error)

    def test_invalid_transition_completed_to_draft(self):
        from parametric_bom.config_workflow import _validate_transition
        error = _validate_transition('completed', 'draft')
        self.assertIsNotNone(error)

    def test_obsolete_is_terminal(self):
        from parametric_bom.config_workflow import _validate_transition
        error = _validate_transition('obsolete', 'draft')
        self.assertIsNotNone(error)
        self.assertIn('terminal state', error)

    def test_unknown_current_status(self):
        from parametric_bom.config_workflow import _validate_transition
        error = _validate_transition('unknown_status', 'draft')
        self.assertIsNotNone(error)
        self.assertIn('Unknown current status', error)


# ══════════════════════════════════════════════
#  Tests for status utility functions
# ══════════════════════════════════════════════


class TestStatusHelpers(TestCase):
    """Tests for status_is_locked, can_edit_parameters, can_delete."""

    def test_status_is_locked(self):
        from parametric_bom.config_workflow import status_is_locked
        self.assertFalse(status_is_locked('draft'))
        self.assertTrue(status_is_locked('completed'))
        self.assertTrue(status_is_locked('released'))
        self.assertTrue(status_is_locked('obsolete'))

    def test_can_edit_parameters(self):
        from parametric_bom.config_workflow import can_edit_parameters

        draft_config = mock.MagicMock()
        draft_config.status = 'draft'
        self.assertTrue(can_edit_parameters(draft_config))

        completed_config = mock.MagicMock()
        completed_config.status = 'completed'
        self.assertFalse(can_edit_parameters(completed_config))

    def test_can_delete(self):
        from parametric_bom.config_workflow import can_delete

        draft_config = mock.MagicMock()
        draft_config.status = 'draft'
        self.assertTrue(can_delete(draft_config))

        released_config = mock.MagicMock()
        released_config.status = 'released'
        self.assertFalse(can_delete(released_config))


# ══════════════════════════════════════════════
#  Tests for transition_status
# ══════════════════════════════════════════════


class TestTransitionStatus(TestCase):
    """Tests for the transition_status() function."""

    @mock.patch('parametric_bom.serializers.ProductConfigurationSerializer')
    def test_successful_transition(self, mock_serializer):
        from parametric_bom.config_workflow import transition_status

        mock_config = mock.MagicMock()
        mock_config.pk = 1
        mock_config.status = 'draft'
        mock_config.title = 'My Config'
        mock_config.revision = '1.0'

        mock_serializer.return_value.data = {
            'id': 1, 'title': 'My Config', 'status': 'completed',
        }

        result = transition_status(mock_config, 'completed')

        self.assertTrue(result['success'])
        self.assertEqual(result['config']['status'], 'completed')
        mock_config.save.assert_called_once_with(update_fields=['status', 'updated_at'])

    def test_invalid_transition_returns_error(self):
        from parametric_bom.config_workflow import transition_status

        mock_config = mock.MagicMock()
        mock_config.status = 'draft'
        mock_config.pk = 1

        result = transition_status(mock_config, 'released')

        self.assertFalse(result['success'])
        self.assertIn('error', result)
        mock_config.save.assert_not_called()


# ══════════════════════════════════════════════
#  Tests for set_parameters
# ══════════════════════════════════════════════


class TestSetParameters(TestCase):
    """Tests for the set_parameters() function."""

    @mock.patch('django.db.transaction.atomic')
    @mock.patch('common.models.ParameterTemplate')
    @mock.patch('parametric_bom.config_workflow.ConfigParameterValue')
    def test_set_parameters_draft(self, mock_cpv_cls, mock_template_cls, mock_atomic):
        from parametric_bom.config_workflow import set_parameters

        mock_config = mock.MagicMock()
        mock_config.status = 'draft'
        mock_config.pk = 1

        mock_template = mock.MagicMock()
        mock_template.name = 'length'
        mock_template.pk = 101
        mock_template_cls.objects.filter.return_value = [mock_template]

        mock_cpv = mock.MagicMock()
        mock_cpv.value = '5000'
        mock_cpv.source = 'manual'
        mock_cpv_cls.objects.update_or_create.return_value = (mock_cpv, True)

        result = set_parameters(mock_config, {'length': '5000'})

        self.assertTrue(result['success'])
        self.assertEqual(len(result['parameters']), 1)
        self.assertEqual(result['parameters'][0]['template_name'], 'length')
        mock_cpv_cls.objects.update_or_create.assert_called_once()

    def test_set_parameters_non_draft_returns_error(self):
        from parametric_bom.config_workflow import set_parameters

        mock_config = mock.MagicMock()
        mock_config.status = 'completed'

        result = set_parameters(mock_config, {'length': '5000'})

        self.assertFalse(result['success'])
        self.assertIn('error', result)

    @mock.patch('django.db.transaction.atomic')
    @mock.patch('common.models.ParameterTemplate')
    @mock.patch('parametric_bom.config_workflow.ConfigParameterValue')
    def test_set_parameters_unknown_template(self, mock_cpv_cls, mock_template_cls, mock_atomic):
        from parametric_bom.config_workflow import set_parameters

        mock_config = mock.MagicMock()
        mock_config.status = 'draft'
        mock_config.pk = 1

        # No templates found
        mock_template_cls.objects.filter.return_value = []

        result = set_parameters(mock_config, {'unknown_param': 'value'})

        self.assertFalse(result['success'])
        self.assertIsNotNone(result['errors'])
        self.assertIn('unknown_param', str(result['errors']))

    @mock.patch('django.db.transaction.atomic')
    @mock.patch('common.models.ParameterTemplate')
    @mock.patch('parametric_bom.config_workflow.ConfigParameterValue')
    def test_set_parameters_none_value_uses_empty_string(self, mock_cpv_cls, mock_template_cls, mock_atomic):
        from parametric_bom.config_workflow import set_parameters

        mock_config = mock.MagicMock()
        mock_config.status = 'draft'
        mock_config.pk = 1

        mock_template = mock.MagicMock()
        mock_template.name = 'optional'
        mock_template.pk = 102
        mock_template_cls.objects.filter.return_value = [mock_template]

        mock_cpv = mock.MagicMock()
        mock_cpv.value = ''
        mock_cpv.source = 'manual'
        mock_cpv_cls.objects.update_or_create.return_value = (mock_cpv, True)

        result = set_parameters(mock_config, {'optional': None})

        self.assertTrue(result['success'])
        # Should pass empty string for None
        call_kwargs = mock_cpv_cls.objects.update_or_create.call_args[1]
        self.assertEqual(call_kwargs['defaults']['value'], '')


# ══════════════════════════════════════════════
#  Tests for delete_parameter
# ══════════════════════════════════════════════


class TestDeleteParameter(TestCase):
    """Tests for the delete_parameter() function."""

    def test_delete_parameter_draft(self):
        from parametric_bom.config_workflow import delete_parameter

        mock_config = mock.MagicMock()
        mock_config.status = 'draft'
        mock_config.pk = 1

        mock_qs = mock.MagicMock()
        mock_qs.filter.return_value.delete.return_value = (1, {})

        with mock.patch('parametric_bom.config_workflow.ConfigParameterValue.objects', mock_qs):
            result = delete_parameter(mock_config, 101)

        self.assertTrue(result['success'])

    def test_delete_parameter_not_found(self):
        from parametric_bom.config_workflow import delete_parameter

        mock_config = mock.MagicMock()
        mock_config.status = 'draft'
        mock_config.pk = 1

        mock_qs = mock.MagicMock()
        mock_qs.filter.return_value.delete.return_value = (0, {})

        with mock.patch('parametric_bom.config_workflow.ConfigParameterValue.objects', mock_qs):
            result = delete_parameter(mock_config, 999)

        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])

    def test_delete_parameter_locked_status(self):
        from parametric_bom.config_workflow import delete_parameter

        mock_config = mock.MagicMock()
        mock_config.status = 'completed'

        result = delete_parameter(mock_config, 101)

        self.assertFalse(result['success'])
        self.assertIn('Cannot delete', result['error'])


# ══════════════════════════════════════════════
#  Tests for snapshot_parameters
# ══════════════════════════════════════════════


class TestSnapshotParameters(TestCase):
    """Tests for the snapshot_parameters() function."""

    @mock.patch('parametric_bom.config_workflow.ConfigParameterValue')
    def test_snapshot_success(self, mock_cpv_cls):
        from parametric_bom.config_workflow import snapshot_parameters

        mock_config = mock.MagicMock()
        mock_config.pk = 1

        mock_pv1 = mock.MagicMock()
        mock_pv1.template.name = 'length'
        mock_pv1.value = '5000'

        mock_pv2 = mock.MagicMock()
        mock_pv2.template.name = 'color'
        mock_pv2.value = 'red'

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value = [mock_pv1, mock_pv2]
        mock_cpv_cls.objects.filter.return_value = mock_qs

        result = snapshot_parameters(mock_config)

        self.assertTrue(result['success'])
        self.assertEqual(result['snapshot'], {'length': '5000', 'color': 'red'})
        mock_config.save.assert_called_once_with(update_fields=['params_snapshot', 'updated_at'])

    @mock.patch('parametric_bom.config_workflow.ConfigParameterValue')
    def test_snapshot_empty(self, mock_cpv_cls):
        from parametric_bom.config_workflow import snapshot_parameters

        mock_config = mock.MagicMock()
        mock_config.pk = 1

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value = []
        mock_cpv_cls.objects.filter.return_value = mock_qs

        result = snapshot_parameters(mock_config)

        self.assertTrue(result['success'])
        self.assertEqual(result['snapshot'], {})


# ══════════════════════════════════════════════
#  Tests for get_configuration_detail
# ══════════════════════════════════════════════


class TestGetConfigurationDetail(TestCase):
    """Tests for the get_configuration_detail() function."""

    @mock.patch('parametric_bom.serializers.ConfigParameterValueSerializer')
    @mock.patch('parametric_bom.serializers.ProductConfigurationSerializer')
    @mock.patch('parametric_bom.config_workflow.ParametricRule')
    @mock.patch('parametric_bom.config_workflow.ConfigParameterValue')
    @mock.patch('parametric_bom.config_workflow.ProductConfiguration')
    def test_get_detail_success(self, mock_config_cls, mock_cpv_cls,
                                mock_rule_cls, mock_ser_config, mock_ser_params):
        from parametric_bom.config_workflow import get_configuration_detail

        mock_config = mock.MagicMock()
        mock_config.pk = 1
        mock_config.status = 'draft'
        mock_config.title = 'My Config'
        mock_config.revision = '1.0'
        mock_config.generated_bom = None
        mock_config.total_cost = None

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value.prefetch_related.return_value.get.return_value = mock_config
        mock_config_cls.objects = mock_qs

        mock_ser_config.return_value.data = {'id': 1, 'status': 'draft'}

        mock_cpv_qs = mock.MagicMock()
        mock_cpv_qs.select_related.return_value.order_by.return_value = []
        mock_cpv_cls.objects.filter.return_value = mock_cpv_qs
        mock_ser_params.return_value.data = []

        mock_rule_qs = mock.MagicMock()
        mock_rule_qs.select_related.return_value.order_by.return_value = []
        mock_rule_cls.objects.filter.return_value = mock_rule_qs

        result = get_configuration_detail(1)

        self.assertTrue(result['success'])
        self.assertEqual(result['config']['id'], 1)
        self.assertFalse(result['is_locked'])
        self.assertTrue(result['can_edit'])
        self.assertTrue(result['can_delete'])

    def test_get_detail_not_found(self):
        from parametric_bom.models import ProductConfiguration
        from parametric_bom.config_workflow import get_configuration_detail

        mock_qs = mock.MagicMock()
        mock_qs.select_related.return_value.prefetch_related.return_value.get.side_effect = (
            ProductConfiguration.DoesNotExist('not found')
        )

        with mock.patch('parametric_bom.config_workflow.ProductConfiguration.objects', mock_qs):
            result = get_configuration_detail(999)

        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])
