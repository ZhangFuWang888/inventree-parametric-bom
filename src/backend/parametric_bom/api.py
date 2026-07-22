"""REST API views for Parametric BOM models."""

from django.conf import settings
from django.contrib.auth import authenticate
from django.urls import reverse
from InvenTree.helpers import pui_url
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from parametric_bom.formula_engine import evaluate, validate as validate_formula
from parametric_bom.formula_engine.errors import (
    EvaluationError,
    ParseError,
    ReferenceError,
    TimeoutError,
)
from parametric_bom.models import (
    BomCandidatePart,
    BomSpecification,
    CartItem,
    ConfigParameterValue,
    ConfigStatusChoices,
    InheritanceMapping,
    ParametricBomItem,
    ParametricRule,
    PartAttributeFormula,
    PartParameterConfig,
    PartVariable,
    ProductConfiguration,
    Project,
    ProjectBatch,
    ProjectItem,
    ProjectLog,
    ProjectStatusChoices,
    VariantMapping,
)
from InvenTree.filters import SEARCH_ORDER_FILTER

from django.conf import settings
from django.http import StreamingHttpResponse, FileResponse
from django.contrib.contenttypes.models import ContentType
from django.db import models as django_models
from django.shortcuts import get_object_or_404

import structlog
logger = structlog.get_logger('inventree')

from parametric_bom.serializers import (
    BomCandidatePartSerializer,
    BomSpecificationSerializer,
    CartItemSerializer,
    ConfigParameterValueSerializer,
    FromCartSerializer,
    InheritanceMappingSerializer,
    ParametricBomItemSerializer,
    ParametricRuleSerializer,
    PartAttributeFormulaSerializer,
    PartParameterConfigSerializer,
    PartVariableSerializer,
    ProductConfigurationSerializer,
    ProjectDetailSerializer,
    ProjectItemSerializer,
    ProjectListSerializer,
    VariantMappingSerializer,
)


# ── Formula Reference Check Helpers ──────────

def _collect_formula_fields(part_id):
    """Collect all formula text fields for a given part.
    
    Returns a list of (model_label, field_label, formula_text) tuples.
    """
    from parametric_bom.models import (
        ParametricBomItem, ParametricRule, PartParameterConfig, PartVariable,
    )
    refs = []

    # 1. ParametricBomItem formulas (via bom_item.part)
    for item in ParametricBomItem.objects.filter(
        bom_item__part_id=part_id
    ).select_related('bom_item'):
        prefix = f'BOM「{item.bom_item.sub_part.name or item.bom_item.sub_part_id}」'
        for field, label in [
            ('qty_formula', '数量公式'),
            ('condition_formula', '条件公式'),
            ('reference_formula', '参考公式'),
        ]:
            val = getattr(item, field, '') or ''
            if val.strip():
                refs.append((prefix, label, val))

    # 2. ParametricRule formulas
    for rule in ParametricRule.objects.filter(product_part_id=part_id):
        prefix = f'规则#{rule.id}'
        for field, label in [
            ('condition_formula', '条件'),
            ('value_formula', '值公式'),
        ]:
            val = getattr(rule, field, '') or ''
            if val.strip():
                refs.append((prefix, label, val))

    # 3. PartParameterConfig computation formulas
    for cfg in PartParameterConfig.objects.filter(part_id=part_id):
        name = cfg.name or (cfg.template.name if cfg.template else f'参数#{cfg.id}')
        val = (cfg.computation_formula or '').strip()
        if val:
            refs.append((f'参数「{name}」', '计算公式', val))

    # 4. PartVariable formulas
    for var in PartVariable.objects.filter(part_id=part_id):
        name = var.name
        val = (var.formula or '').strip()
        if val:
            refs.append((f'变量「{name}」', '公式', val))

    return refs


def _find_param_references(part_id, param_name):
    """Check if param_name (referenced as param.xxx) is used in any formula."""
    results = []
    for prefix, label, formula in _collect_formula_fields(part_id):
        # Match: param.参数名 or param."参数名"
        import re
        pattern = re.compile(r'param\.\s*' + re.escape(param_name) + r'\b')
        if pattern.search(formula):
            results.append(f'{prefix} → {label}')
    return results


def _find_variable_references(part_id, var_name):
    """Check if var_name is referenced in any formula.
    
    Variables are referenced by bare name (not as param.xxx).
    We check for word-boundary matches of the variable name.
    """
    results = []
    for prefix, label, formula in _collect_formula_fields(part_id):
        import re
        # Match variable name as a whole word, but NOT preceded by "param."
        pattern = re.compile(r'(?<!param\.)\b' + re.escape(var_name) + r'\b')
        if pattern.search(formula):
            results.append(f'{prefix} → {label}')
    return results


class PartParameterConfigViewSet(viewsets.ModelViewSet):
    """API endpoint for PartParameterConfig."""
    queryset = PartParameterConfig.objects.select_related(
        'part'
    ).all()
    serializer_class = PartParameterConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['part', 'is_driving', 'is_computed']
    search_fields = ['name', 'part__name', 'ui_hint']

    def perform_destroy(self, instance):
        """Prevent deletion if parameter is referenced by any formula."""
        refs = _find_param_references(
            instance.part_id, instance.name or (instance.template.name if instance.template else '')
        )
        if refs:
            detail = '该参数被以下公式引用，无法删除：\n' + '\n'.join(refs)
            raise PermissionDenied(detail=detail)
        instance.delete()


class ParametricBomItemViewSet(viewsets.ModelViewSet):
    """API endpoint for ParametricBomItem."""
    queryset = ParametricBomItem.objects.select_related(
        'bom_item__part', 'bom_item__sub_part'
    ).all()
    serializer_class = ParametricBomItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['bom_item', 'bom_item__part', 'enable_qty_formula', 'enable_conditional',
                        'enable_candidate', 'enable_variant', 'enable_specification',
                        'enable_structure']
    search_fields = ['bom_item__part__name', 'qty_formula']


class ParametricRuleViewSet(viewsets.ModelViewSet):
    """API endpoint for ParametricRule."""
    queryset = ParametricRule.objects.select_related(
        'product_part', 'target_param'
    ).all()
    serializer_class = ParametricRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = [
        'product_part', 'rule_type', 'action', 'enabled',
    ]
    search_fields = ['product_part__name', 'condition_formula']


class ProductConfigurationViewSet(viewsets.ModelViewSet):
    """API endpoint for ProductConfiguration."""
    queryset = ProductConfiguration.objects.select_related(
        'template_part', 'created_by'
    ).prefetch_related('parameter_values').all()
    serializer_class = ProductConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['template_part', 'status', 'revision']
    search_fields = ['title', 'notes']


class ConfigParameterValueViewSet(viewsets.ModelViewSet):
    """API endpoint for ConfigParameterValue."""
    queryset = ConfigParameterValue.objects.select_related(
        'config', 'template'
    ).all()
    serializer_class = ConfigParameterValueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['config', 'template', 'source']


# ── New Model ViewSets ─────────────────────

class BomCandidatePartViewSet(viewsets.ModelViewSet):
    """API endpoint for BomCandidatePart."""
    queryset = BomCandidatePart.objects.select_related(
        'parametric_bom_item', 'part'
    ).all()
    serializer_class = BomCandidatePartSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['parametric_bom_item', 'part']
    search_fields = ['label', 'part__name']


class VariantMappingViewSet(viewsets.ModelViewSet):
    """API endpoint for VariantMapping."""
    queryset = VariantMapping.objects.select_related(
        'parametric_bom_item', 'template_part'
    ).all()
    serializer_class = VariantMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['parametric_bom_item', 'template_part']


class BomSpecificationViewSet(viewsets.ModelViewSet):
    """API endpoint for BomSpecification."""
    queryset = BomSpecification.objects.select_related(
        'parametric_bom_item'
    ).all()
    serializer_class = BomSpecificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['parametric_bom_item', 'spec_type']


class InheritanceMappingViewSet(viewsets.ModelViewSet):
    """API endpoint for InheritanceMapping."""
    queryset = InheritanceMapping.objects.select_related(
        'target_part', 'target_template', 'source_template'
    ).all()
    serializer_class = InheritanceMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['target_part', 'target_template', 'enabled']


class PartAttributeFormulaViewSet(viewsets.ModelViewSet):
    """API endpoint for PartAttributeFormula."""
    queryset = PartAttributeFormula.objects.select_related('part').all()
    serializer_class = PartAttributeFormulaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['part', 'attribute_type']
    search_fields = ['attribute_name']


class PartVariableViewSet(viewsets.ModelViewSet):
    """API endpoint for PartVariable."""
    queryset = PartVariable.objects.select_related('part').all()
    serializer_class = PartVariableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['part']
    search_fields = ['name']

    def perform_destroy(self, instance):
        """Prevent deletion if variable is referenced by any formula."""
        refs = _find_variable_references(instance.part_id, instance.name)
        if refs:
            detail = '该变量被以下公式引用，无法删除：\n' + '\n'.join(refs)
            raise PermissionDenied(detail=detail)
        instance.delete()


# ── Existing Function Endpoints ─────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bom_evaluate(request):
    """Evaluate a parametric BOM — expand BOM tree with formula computation."""
    import json, os
    from django.conf import settings

    # ═══ 临时调试日志 ═══
    _log_path = '/tmp/bom_evaluate_debug.log'
    _ts = __import__('datetime').datetime.now().isoformat()
    with open(_log_path, 'a') as _f:
        _f.write(f"\n=== [{_ts}] REQUEST ===\n")
        _f.write(f"parsed data: {json.dumps(dict(request.data), ensure_ascii=False)}\n")

    from parametric_bom.bom_expander import evaluate_configuration, evaluate_part
    from parametric_bom.models import ProductConfiguration

    config_id = request.data.get('config_id')
    part_id = request.data.get('part_id')
    timeout_ms = request.data.get('timeout_ms', 500)
    max_depth = request.data.get('max_depth', 10)

    try:
        if config_id:
            config = ProductConfiguration.objects.get(pk=config_id)
            result = evaluate_configuration(config, timeout_ms, max_depth)
            with open(_log_path, 'a') as _f:
                _f.write(f"RESPONSE parameters: {json.dumps(result.get('parameters',{}), ensure_ascii=False)}\n")
                _f.write(f"RESPONSE H: {result.get('parameters',{}).get('H','N/A')}\n")
            return Response(result)
        elif part_id:
            from part.models import Part
            part = Part.objects.get(pk=part_id)
            user_params = request.data.get('parameters', {}) or request.data.get('params', {})
            result = evaluate_part(part, user_params, timeout_ms, max_depth)
            with open(_log_path, 'a') as _f:
                _f.write(f"user_params: {json.dumps(user_params, ensure_ascii=False)}\n")
                _f.write(f"RESPONSE parameters: {json.dumps(result.get('parameters',{}), ensure_ascii=False)}\n")
                _f.write(f"RESPONSE H: {result.get('parameters',{}).get('H','N/A')}\n")
            return Response(result)
        else:
            return Response(
                {'error': 'Provide either config_id or part_id'},
                status=400,
            )
    except ProductConfiguration.DoesNotExist:
        return Response(
            {'error': f'Configuration {config_id} not found'},
            status=404,
        )
    except Part.DoesNotExist:
        return Response(
            {'error': f'Part {part_id} not found'},
            status=404,
        )
    except Exception as exc:
        logger.exception('BOM evaluation failed')
        import traceback
        with open('/tmp/bom_evaluate_debug.log', 'a') as _f:
            _f.write(f"EXCEPTION: {exc}\n")
            _f.write(traceback.format_exc() + "\n")
        return Response(
            {'error': f'Evaluation failed: {exc}'},
            status=500,
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def formula_validate(request):
    """Validate a formula string.

    Request body:
        formula (str): The formula to validate.
        expected_type (str, optional): Expected return type.
            One of: 'string', 'boolean', 'integer', 'float', 'number'.

    Returns:
        valid (bool): Whether the formula is valid.
        errors (list): Validation error messages.
        referenced_params (list): Parameter references found.
        result_type (str|None): Detected return type.
        type_valid (bool|None): Whether result type matches expected.
        type_detail (str|None): Type mismatch detail if applicable.
    """
    formula = request.data.get('formula', '')
    expected_type = request.data.get('expected_type')
    result = validate_formula(formula, expected_type=expected_type)
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def estimate_cost(request):
    """Estimate cost for a parametric configuration or part."""
    from parametric_bom.cost_estimator import (
        estimate_configuration_cost,
        estimate_part_cost,
    )
    from parametric_bom.models import ProductConfiguration

    config_id = request.data.get('config_id')
    part_id = request.data.get('part_id')
    markup_pct = float(request.data.get('markup_pct', 0.0))
    pricing_preference = request.data.get('pricing_preference', 'internal')
    timeout_ms = request.data.get('timeout_ms', 500)
    max_depth = request.data.get('max_depth', 10)

    valid_prefs = {'internal', 'purchase', 'bom', 'supplier', 'overall', 'sale'}
    if pricing_preference not in valid_prefs:
        return Response(
            {
                'error': (
                    f"Invalid pricing_preference '{pricing_preference}'. "
                    f"Must be one of: {', '.join(sorted(valid_prefs))}"
                ),
            },
            status=400,
        )

    try:
        if config_id:
            config = ProductConfiguration.objects.get(pk=config_id)
            result = estimate_configuration_cost(
                config, markup_pct=markup_pct, pricing_preference=pricing_preference,
            )
            return Response(result)
        elif part_id:
            from part.models import Part
            part = Part.objects.get(pk=part_id)
            user_params = request.data.get('parameters', {}) or request.data.get('params', {})
            result = estimate_part_cost(
                part, user_params,
                markup_pct=markup_pct, pricing_preference=pricing_preference,
                timeout_ms=timeout_ms, max_depth=max_depth,
            )
            return Response(result)
        else:
            return Response(
                {'error': 'Provide either config_id or part_id'},
                status=400,
            )
    except ProductConfiguration.DoesNotExist:
        return Response(
            {'error': f'Configuration {config_id} not found'},
            status=404,
        )
    except Part.DoesNotExist:
        return Response(
            {'error': f'Part {part_id} not found'},
            status=404,
        )
    except Exception as exc:
        logger.exception('Cost estimation failed')
        return Response(
            {'error': f'Cost estimation failed: {exc}'},
            status=500,
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def formula_preview(request):
    """Preview/evaluate a formula with sample parameter values.

    Returns the result value and its detected type (bool/number/str).
    """
    formula = request.data.get('formula', '')
    context = request.data.get('context', {})
    timeout_ms = request.data.get('timeout_ms', 500)

    if not formula.strip():
        return Response({'success': False, 'error': 'Formula is empty'})

    try:
        result = evaluate(formula, context, timeout_ms=timeout_ms)
        # Detect result type
        if isinstance(result, bool):
            result_type = 'bool'
        elif isinstance(result, (int, float)):
            result_type = 'number'
        elif isinstance(result, str):
            result_type = 'str'
        else:
            result_type = type(result).__name__
        return Response({'success': True, 'result': result, 'result_type': result_type})
    except ParseError as e:
        return Response({'success': False, 'error': f'Syntax error: {e}'})
    except ReferenceError as e:
        return Response({'success': False, 'error': str(e)})
    except TimeoutError as e:
        return Response({'success': False, 'error': str(e)})
    except (EvaluationError, ValueError, TypeError) as e:
        return Response({'success': False, 'error': f'Evaluation error: {e}'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def rules_evaluate(request):
    """Evaluate all parametric rules for a configuration or part."""
    from parametric_bom.rule_engine import (
        evaluate_config_rules,
        evaluate_rules,
    )

    config_id = request.data.get('config_id')
    part_id = request.data.get('part_id')
    timeout_ms = request.data.get('timeout_ms', 500)

    try:
        if config_id:
            config = ProductConfiguration.objects.get(pk=config_id)
            result = evaluate_config_rules(config, timeout_ms)
            return Response(result)
        elif part_id:
            from part.models import Part
            part = Part.objects.get(pk=part_id)
            user_params = request.data.get('parameters', {}) or request.data.get('params', {})
            result = evaluate_rules(part, user_params, timeout_ms)
            return Response(result)
        else:
            return Response(
                {'error': 'Provide either config_id or part_id'},
                status=400,
            )
    except ProductConfiguration.DoesNotExist:
        return Response(
            {'error': f'Configuration {config_id} not found'},
            status=404,
        )
    except Part.DoesNotExist:
        return Response(
            {'error': f'Part {part_id} not found'},
            status=404,
        )
    except Exception as exc:
        logger.exception('Rule evaluation failed')
        return Response(
            {'error': f'Rule evaluation failed: {exc}'},
            status=500,
        )


# ── Configuration Workflow ──────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def config_transition(request, config_id):
    """Transition a configuration to a new status."""
    from parametric_bom.config_workflow import transition_status

    new_status = request.data.get('status', '').strip().lower()
    valid_statuses = [c[0] for c in ConfigStatusChoices.choices]
    if new_status not in valid_statuses:
        return Response(
            {
                'success': False,
                'error': (
                    f"Invalid status '{request.data.get('status')}'. "
                    f"Valid choices: {', '.join(valid_statuses)}"
                ),
            },
            status=400,
        )

    try:
        config = ProductConfiguration.objects.get(pk=config_id)
    except ProductConfiguration.DoesNotExist:
        return Response(
            {'success': False, 'error': f'Configuration {config_id} not found.'},
            status=404,
        )

    result = transition_status(config, new_status)
    status_code = 200 if result.get('success') else 409
    return Response(result, status=status_code)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def config_set_params(request, config_id):
    """Batch-set parameter values on a configuration."""
    from parametric_bom.config_workflow import set_parameters

    params_dict = request.data.get('parameters', {})
    if not isinstance(params_dict, dict) or not params_dict:
        return Response(
            {
                'success': False,
                'error': (
                    'Provide a "parameters" dict mapping parameter names to values. '
                    'Example: {"parameters": {"长度": 5000, "速度": 12}}'
                ),
            },
            status=400,
        )

    try:
        config = ProductConfiguration.objects.get(pk=config_id)
    except ProductConfiguration.DoesNotExist:
        return Response(
            {'success': False, 'error': f'Configuration {config_id} not found.'},
            status=404,
        )

    result = set_parameters(config, params_dict)
    status_code = 200 if result.get('success') else 409
    return Response(result, status=status_code)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def config_snapshot(request, config_id):
    """Snapshot current parameter values to the configuration."""
    from parametric_bom.config_workflow import snapshot_parameters

    try:
        config = ProductConfiguration.objects.get(pk=config_id)
    except ProductConfiguration.DoesNotExist:
        return Response(
            {'success': False, 'error': f'Configuration {config_id} not found.'},
            status=404,
        )

    result = snapshot_parameters(config)
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def config_detail(request, config_id):
    """Get detailed configuration info including all parameter values."""
    from parametric_bom.config_workflow import get_config_detail

    try:
        config = ProductConfiguration.objects.get(pk=config_id)
    except ProductConfiguration.DoesNotExist:
        return Response(
            {'success': False, 'error': f'Configuration {config_id} not found.'},
            status=404,
        )

    result = get_config_detail(config)
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_variant(request):
    """Generate a concrete Part variant from a completed configuration."""
    from parametric_bom.variant_generator import generate_variant as gen_variant

    config_id = request.data.get('config_id')
    if not config_id:
        return Response(
            {'error': 'Provide config_id'},
            status=400,
        )

    result = gen_variant(config_id)
    status_code = 200 if result.get('success') else 409
    return Response(result, status=status_code)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_variant_from_params(request):
    """Generate variants directly from part_id + parameter values (no saved config needed).

    For each VariantMapping on the product's parametric BOM items, evaluates the
    mapping formulas, applies name/IPN templates, and creates/lookup variant Parts.
    """
    from parametric_bom.models import (
        ProductConfiguration,
        ConfigParameterValue,
        ConfigStatusChoices,
    )
    from parametric_bom.variant_generator import generate_variant as gen_variant
    from parametric_bom.models import VariantMapping, ParametricBomItem
    from part.models import Part
    from common.models import ParameterTemplate

    part_id = request.data.get('part_id')
    parameters = request.data.get('parameters', {})

    if not part_id:
        return Response({'error': 'Provide part_id'}, status=400)

    try:
        template_part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({'error': f'Part {part_id} not found'}, status=404)

    # Look up all VariantMappings for this product's parametric BOM items
    parametric_items = ParametricBomItem.objects.filter(
        bom_item__part=template_part,
    ).prefetch_related('variant_mapping')

    results = []
    for pbi in parametric_items:
        vm = getattr(pbi, 'variant_mapping', None)
        if not vm:
            continue
        if not vm.auto_generate:
            continue

        # Evaluate the name template against parameters
        def resolve_template(tpl, params, parent_params):
            """Replace {paramName} in a template string with values from params."""
            import re
            def replacer(m):
                key = m.group(1)
                # First try parent parameters
                if key in params:
                    return str(params[key])
                # Try mapping formulas
                formula = getattr(vm, 'param_mapping', {}).get(key, '')
                if formula.startswith('param.'):
                    pn = formula.replace('param.', '')
                    if pn in params:
                        return str(params[pn])
                return key
            return re.sub(r'\{(\w+)\}', replacer, tpl)

        resolved_name = resolve_template(
            vm.variant_name_template or '',
            parameters,
            getattr(vm, 'param_mapping', {}),
        ) or f'{vm.template_part.name} (auto)'

        resolved_ipn = resolve_template(
            vm.variant_ipn_template or '',
            parameters,
            getattr(vm, 'param_mapping', {}),
        ) or ''

        # Create a temp config for this sub-component variant
        sub_config = ProductConfiguration.objects.create(
            template_part=vm.template_part,
            title=f'Auto-{resolved_name}',
            status=ConfigStatusChoices.COMPLETED,
            params_snapshot=parameters,
        )

        # Set parameter values for the template part's own params
        for param_name, param_value in parameters.items():
            try:
                tmpl = ParameterTemplate.objects.get(name=param_name)
                ConfigParameterValue.objects.create(
                    config=sub_config,
                    template=tmpl,
                    value=param_value,
                )
            except ParameterTemplate.DoesNotExist:
                pass

        # Generate variant with name/IPN overrides
        result = gen_variant(
            sub_config.pk,
            variant_name=resolved_name if vm.variant_name_template else None,
            variant_ipn=resolved_ipn if vm.variant_ipn_template else None,
        )
        results.append(result)

    if not results:
        return Response({
            'success': False,
            'error': 'No active VariantMappings found for this product. Set up variant mappings in the BOM formula tab first.',
        }, status=200)

    return Response({
        'success': True,
        'results': results,
        'generated_count': sum(1 for r in results if r.get('success')),
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_bom_item(request):
    """Unified endpoint: create a BOM item (static or dynamic).

    For static items: BomItem + ParametricBomItem with param_mapping.
    For dynamic items: same + VariantMapping to track template part.
    Name/IPN templates are set later via double-click editing.

    Input:
        parent_part_id (int): The product that owns the BOM
        sub_part_id (int): The part to use as sub-part
        is_dynamic (bool): True for dynamic projects, False for static
        quantity (str, optional): BOM quantity (default '1')
        param_mappings (dict, optional): parameter value mappings {name: value}
    """
    from part.models import BomItem, Part
    from .models import ParametricBomItem, VariantMapping
    from decimal import Decimal

    parent_part_id = request.data.get('parent_part_id')
    sub_part_id = request.data.get('sub_part_id')
    is_dynamic = request.data.get('is_dynamic', False)
    quantity = request.data.get('quantity', '1')
    param_mappings = request.data.get('param_mappings', {})

    if not parent_part_id or not sub_part_id:
        return Response(
            {'success': False, 'error': 'Provide parent_part_id and sub_part_id'},
            status=400,
        )

    try:
        parent_part = Part.objects.get(pk=parent_part_id)
        sub_part = Part.objects.get(pk=sub_part_id)
    except Part.DoesNotExist as e:
        return Response(
            {'success': False, 'error': f'Part not found: {e}'},
            status=404,
        )

    try:
        qty = Decimal(str(quantity))
    except (ValueError, TypeError):
        qty = Decimal('1')

    # Create BomItem
    bom_item = BomItem.objects.create(
        part=parent_part,
        sub_part=sub_part,
        quantity=qty,
    )

    # Create ParametricBomItem
    pbi = ParametricBomItem.objects.create(
        bom_item=bom_item,
        enable_variant=is_dynamic,
        param_mapping=param_mappings,
    )

    # For dynamic items: create VariantMapping
    if is_dynamic:
        # Ensure template is marked as template
        if not sub_part.is_template:
            sub_part.is_template = True
            sub_part.save(update_fields=['is_template'])

        VariantMapping.objects.create(
            parametric_bom_item=pbi,
            template_part=sub_part,
            variant_name_template='',
            variant_ipn_template='',
            param_mapping=param_mappings,
        )

        logger.info(
            'dynamic_project_created',
            parent_part_id=parent_part.pk,
            template_part_id=sub_part.pk,
            bom_item_id=bom_item.pk,
            pbi_id=pbi.pk,
        )

    return Response({
        'success': True,
        'bom_item': {
            'pk': bom_item.pk,
            'part': bom_item.part_id,
            'sub_part': bom_item.sub_part_id,
            'sub_part_name': sub_part.name,
            'sub_part_IPN': sub_part.IPN or '',
            'quantity': str(bom_item.quantity),
            'is_dynamic': is_dynamic,
        },
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def inherit_params(request):
    """Trigger parameter inheritance for a configuration or part."""
    from parametric_bom.param_inheritance import inherit_params_for_config, inherit_params_for_part

    config_id = request.data.get('config_id')
    part_id = request.data.get('part_id')

    try:
        if config_id:
            config = ProductConfiguration.objects.get(pk=config_id)
            result = inherit_params_for_config(config)
            return Response(result)
        elif part_id:
            from part.models import Part
            part = Part.objects.get(pk=part_id)
            user_params = request.data.get('parameters', {}) or request.data.get('params', {})
            result = inherit_params_for_part(part, user_params)
            return Response(result)
        else:
            return Response(
                {'error': 'Provide either config_id or part_id'},
                status=400,
            )
    except ProductConfiguration.DoesNotExist:
        return Response(
            {'error': f'Configuration {config_id} not found'},
            status=404,
        )
    except Part.DoesNotExist:
        return Response(
            {'error': f'Part {part_id} not found'},
            status=404,
        )
    except Exception as exc:
        logger.exception('Inheritance failed')
        return Response(
            {'error': f'Inheritance failed: {exc}'},
            status=500,
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def affected_variants(request, part_config_id):
    """Find all configuration variants affected by a parameter change."""
    from parametric_bom.param_inheritance import find_affected_configs

    try:
        config = PartParameterConfig.objects.get(pk=part_config_id)
    except PartParameterConfig.DoesNotExist:
        return Response(
            {'error': f'PartParameterConfig {part_config_id} not found'},
            status=404,
        )

    result = find_affected_configs(config)
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def template_library_sync(request):
    """Sync parameter templates to the template library."""
    from parametric_bom.template_library import sync_templates

    category_id = request.data.get('category_id')
    result = sync_templates(category_id)
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def template_library_category_detail(request, category_id):
    """Get template library detail for a part category."""
    from parametric_bom.template_library import get_category_detail

    result = get_category_detail(category_id)
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def template_library_bulk_assign(request):
    """Bulk-assign parameter templates to parts."""
    from parametric_bom.template_library import bulk_assign_config

    category_id = request.data.get('category_id')
    template_ids = request.data.get('template_ids', [])
    result = bulk_assign_config(category_id, template_ids)
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def template_library_auto_sync(request):
    """Auto-sync parameter templates for a part category."""
    from parametric_bom.template_library import auto_sync_category

    category_id = request.data.get('category_id')
    result = auto_sync_category(category_id)
    return Response(result)


# ── Export: XLSX Helper ──────────────────────

def _build_bom_xlsx(result):
    """Build a mechanical-design BOM XLSX from evaluate result.
    
    Returns (BytesIO, part_name).
    Columns: 序号, 图号/代号, 名称, 数量, 单位, 备注
    """
    import openpyxl, io
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

    bom_tree = result.get('bom_tree', {})
    part_name = result.get('part_name', 'BOM')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'BOM清单'

    # Styles
    style_header_font = Font(name='微软雅黑', bold=True, size=10, color='FFFFFF')
    style_header_fill = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
    style_header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    style_cell_font = Font(name='微软雅黑', size=9)
    style_center = Alignment(horizontal='center', vertical='center')
    style_number = Alignment(horizontal='right', vertical='center')
    style_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB'),
    )

    headers = [
        '序号', '设备（大类）', '部装', '规格型号', '品名',
        '品牌', '单位', '应需数量', '预期到货', '类别',
        '材质（牌号）', '表面处理方式', '处理颜色', '重量', '备注',
        '采购员', '入库去向', '制购类别', '申请理由', '附图',
        '总数量', '问题环节', '技改原因分类',
    ]
    col_widths = [6, 14, 14, 16, 22, 8, 6, 10, 12, 8, 14, 14, 10, 8, 18, 8, 10, 10, 14, 8, 8, 10, 14]

    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = style_header_font
        cell.fill = style_header_fill
        cell.alignment = style_header_align
        cell.border = style_border
        ws.column_dimensions[get_column_letter(col)].width = w

    # Collect all unique part IDs for DB lookup
    part_ids = set()
    # 根产品ID — 设备（大类）取此产品的分类
    root_pid = bom_tree.get('actual_part_id') or bom_tree.get('part_id')
    if root_pid:
        part_ids.add(int(root_pid))
    def _collect_pids(node):
        for child in node.get('children', []):
            if child.get('excluded'):
                continue
            pid = child.get('actual_part_id') or child.get('part_id')
            if pid:
                part_ids.add(int(pid))
            _collect_pids(child)
    _collect_pids(bom_tree)

    # Bulk fetch Parts for IPN + units
    from part.models import Part
    part_map = {}
    # 根产品分类 — 所有行的"设备（大类）"共用此值
    root_category_name = ''
    if part_ids:
        for p in Part.objects.filter(pk__in=part_ids).select_related('category').only('pk', 'IPN', 'units', 'name', 'category'):
            part_map[p.pk] = p
            # 记录根产品的分类
            if root_pid and p.pk == root_pid and p.category:
                root_category_name = p.category.name

    # Try to get material from PartParameterConfig (if a "材料" parameter exists)
    from parametric_bom.models import PartParameterConfig
    from common.models import ParameterTemplate
    material_configs = {}
    try:
        mt = ParameterTemplate.objects.filter(name__in=['材料', '材质', 'material', 'Material']).first()
        if mt:
            for cfg in PartParameterConfig.objects.filter(
                part_id__in=part_ids, template=mt,
            ).select_related('template').only('part_id', 'default_value'):
                material_configs[cfg.part_id] = cfg.default_value
    except Exception:
        pass

    # Bulk fetch part parameters for 材质 / 表面处理 / 颜色 / 重量
    from common.models import Parameter
    from django.contrib.contenttypes.models import ContentType
    from part.models import Part as PartModel
    ct_part_exp = ContentType.objects.get_for_model(PartModel)
    param_names = ['材质（牌号）', '表面处理方式', '处理颜色', '重量']
    param_templates_map = {}
    for pn in param_names:
        try:
            tpl = ParameterTemplate.objects.get(name=pn)
            param_templates_map[pn] = tpl
        except ParameterTemplate.DoesNotExist:
            pass
    param_data = {}  # {part_id: {param_name: value}}
    if param_templates_map and part_ids:
        for par in Parameter.objects.filter(
            model_type=ct_part_exp,
            model_id__in=part_ids,
            template__in=list(param_templates_map.values()),
        ).select_related('template'):
            pid = par.model_id
            param_data.setdefault(pid, {})[par.template.name] = par.data

    row_num = 2
    seq = 0

    def flatten(node, parent_qty=1.0):
        nonlocal row_num, seq
        for child in node.get('children', []):
            if child.get('excluded'):
                continue
            seq += 1
            pid = child.get('actual_part_id') or child.get('part_id')
            pname = (
                child.get('calculated_name')
                or child.get('variant_name')
                or child.get('actual_part_name')
                or child.get('part_name')
                or ''
            )
            ipn = child.get('calculated_ipn') or child.get('variant_ipn', '') or ''
            qty = child.get('calculated_quantity', 1) * parent_qty
            ref = str(child.get('reference', '') or child.get('reference_formula', '') or '')
            units = ''

            # Look up Part for IPN + units
            if pid and pid in part_map:
                p = part_map[pid]
                if not ipn:
                    ipn = p.IPN or ''
                if not units:
                    units = p.units or ''

            # Look up part parameters (材质, 表面处理, 颜色, 重量)
            p_material = ''
            p_finish = ''
            p_color = ''
            p_weight = ''
            if pid and pid in param_data:
                p_material = param_data[pid].get('材质（牌号）', '')
                p_finish = param_data[pid].get('表面处理方式', '')
                p_color = param_data[pid].get('处理颜色', '')
                p_weight = param_data[pid].get('重量', '')

            vals = [
                seq,
                root_category_name,  # 设备（大类）— 配置产品的直接分类
                '',  # 部装
                ipn,  # 规格型号
                pname,  # 品名
                '',  # 品牌
                units,  # 单位
                qty,  # 应需数量
                '',  # 预期到货
                '',  # 类别
                p_material,  # 材质（牌号）
                p_finish,  # 表面处理方式
                p_color,  # 处理颜色
                p_weight,  # 重量
                ref,  # 备注
                '',  # 采购员
                '',  # 入库去向
                '',  # 制购类别
                '',  # 申请理由
                '',  # 附图
                qty,  # 总数量
                '',  # 问题环节
                '',  # 技改原因分类
            ]
            for col, v in enumerate(vals, 1):
                cell = ws.cell(row=row_num, column=col, value=v)
                cell.font = style_cell_font
                cell.border = style_border
                if col in (8, 21):
                    cell.number_format = '#,##0'
                cell.alignment = style_center

            row_num += 1
            flatten(child, qty)

    flatten(bom_tree)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf, part_name


# ── Export: BOM XLSX ─────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def export_bom_csv(request):
    """Export evaluated BOM tree as XLSX download.
    
    GET: ?part_id=xxx or ?config_id=xxx
    POST: JSON body {part_id, parameters:{}, config_id}
    """
    from parametric_bom.bom_expander import evaluate_configuration, evaluate_part
    from parametric_bom.models import ProductConfiguration

    if request.method == 'POST':
        data = request.data
    else:
        data = request.query_params

    config_id = data.get('config_id')
    part_id = data.get('part_id')

    try:
        if config_id:
            config = ProductConfiguration.objects.get(pk=config_id)
            result = evaluate_configuration(config)
        elif part_id:
            from part.models import Part
            part = Part.objects.get(pk=part_id)
            user_params = data.get('parameters', {})
            if isinstance(user_params, str):
                import json
                user_params = json.loads(user_params)
            result = evaluate_part(part, user_params)
        else:
            return Response({'error': 'Provide config_id or part_id'}, status=400)
    except Exception as exc:
        logger.exception('BOM export failed')
        return Response({'error': str(exc)}, status=500)

    buf, part_name = _build_bom_xlsx(result)
    safe_name = part_name.replace(' ', '_').replace('/', '_')
    response = FileResponse(
        buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=f'{safe_name}_BOM清单.xlsx',
    )
    response['Content-Disposition'] = (
        f'attachment; filename="{safe_name}_BOM清单.xlsx"'
    )
    return response


# ── Export: Attachment ZIP ──────────────────

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def export_attachment_zip(request):
    """Pack all attachments of BOM sub-parts into a ZIP download.
    
    GET: ?part_id=xxx or ?config_id=xxx
    POST: JSON body {part_id, parameters:{}, config_id}
    """
    import zipfile, io, os

    from parametric_bom.bom_expander import evaluate_configuration, evaluate_part, _flatten_bom
    from parametric_bom.models import ProductConfiguration

    if request.method == 'POST':
        data = request.data
    else:
        data = request.query_params

    config_id = data.get('config_id')
    part_id = data.get('part_id')

    try:
        if config_id:
            config = ProductConfiguration.objects.get(pk=config_id)
            result = evaluate_configuration(config)
        elif part_id:
            from part.models import Part
            part = Part.objects.get(pk=part_id)
            user_params = data.get('parameters', {})
            if isinstance(user_params, str):
                import json
                user_params = json.loads(user_params)
            result = evaluate_part(part, user_params)
        else:
            return Response({'error': 'Provide config_id or part_id'}, status=400)
    except Exception as exc:
        logger.exception('Attachment ZIP export failed')
        return Response({'error': str(exc)}, status=500)

    bom_tree = result.get('bom_tree', {})
    part_name = result.get('part_name', 'Attachments')

    # Collect all part IDs from flattened BOM
    part_ids = set()
    for pid, _ in _flatten_bom(bom_tree):
        if pid:
            part_ids.add(int(pid))

    if not part_ids:
        return Response({'error': '\u6ca1\u6709BOM\u7269\u6599\uff0c\u65e0\u9644\u4ef6\u53ef\u4e0b\u8f7d'}, status=400)

    # Find attachments via ContentType
    from common.models import Attachment
    part_ct = ContentType.objects.get(app_label='part', model='part')
    attachments = Attachment.objects.filter(
        model_type=part_ct,
        model_id__in=part_ids,
    ).exclude(attachment='').select_related('upload_user')

    if not attachments.exists():
        return Response({'error': '\u672a\u627e\u5230\u4efb\u4f55\u9644\u4ef6'}, status=404)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for att in attachments:
            try:
                file_path = att.attachment.path if hasattr(att.attachment, 'path') else str(att.attachment)
                if not os.path.isfile(file_path):
                    continue
                arcname = os.path.basename(file_path)
                zf.write(file_path, arcname)
            except Exception:
                logger.exception(f'Failed to add attachment {att.pk} to ZIP')

    buf.seek(0)

    safe_name = part_name.replace(' ', '_').replace('/', '_')
    response = FileResponse(
        buf, content_type='application/zip',
        filename=f'{safe_name}_attachments.zip',
    )
    response['Content-Disposition'] = (
        f'attachment; filename="{safe_name}_attachments.zip"'
    )
    return response


# ── Export: BOM + Attachments Bundle ZIP ────

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def export_bundle_zip(request):
    """Export BOM XLSX + all attachment files in one ZIP.
    
    ZIP structure:
      BOM清单.xlsx
      附件/xxx.pdf
      附件/yyy.jpg
      ...
    
    GET: ?part_id=xxx or ?config_id=xxx
    POST: JSON body {part_id, parameters:{}, config_id}
    """
    import zipfile, io, os

    from parametric_bom.bom_expander import evaluate_configuration, evaluate_part, _flatten_bom
    from parametric_bom.models import ProductConfiguration

    if request.method == 'POST':
        data = request.data
    else:
        data = request.query_params

    config_id = data.get('config_id')
    part_id = data.get('part_id')

    try:
        if config_id:
            config = ProductConfiguration.objects.get(pk=config_id)
            result = evaluate_configuration(config)
        elif part_id:
            from part.models import Part
            part = Part.objects.get(pk=part_id)
            user_params = data.get('parameters', {})
            if isinstance(user_params, str):
                import json
                user_params = json.loads(user_params)
            result = evaluate_part(part, user_params)
        else:
            return Response({'error': 'Provide config_id or part_id'}, status=400)
    except Exception as exc:
        logger.exception('Bundle export failed')
        return Response({'error': str(exc)}, status=500)

    # ── Generate XLSX via shared helper ──
    xlsx_buf, part_name = _build_bom_xlsx(result)

    # ── Collect attachments ──
    bom_tree = result.get('bom_tree', {})
    part_ids = set()
    for pid_v, _ in _flatten_bom(bom_tree):
        if pid_v:
            part_ids.add(int(pid_v))

    attachments = []
    if part_ids:
        from common.models import Attachment
        part_ct = ContentType.objects.get(app_label='part', model='part')
        attachments = list(Attachment.objects.filter(
            model_type=part_ct,
            model_id__in=part_ids,
        ).exclude(attachment=''))

    # ── Build ZIP ──
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add BOM xlsx
        zf.writestr('BOM清单.xlsx', xlsx_buf.getvalue())
        # Add attachments in 附件/ folder
        for att in attachments:
            try:
                file_path = att.attachment.path if hasattr(att.attachment, 'path') else str(att.attachment)
                if not os.path.isfile(file_path):
                    continue
                arcname = os.path.join('附件', os.path.basename(file_path))
                zf.write(file_path, arcname)
            except Exception:
                logger.exception(f'Failed to add attachment {att.pk} to bundle')

    buf.seek(0)

    safe_name = part_name.replace(' ', '_').replace('/', '_')
    response = FileResponse(
        buf, content_type='application/zip',
        filename=f'{safe_name}_BOM完整包.zip',
    )
    response['Content-Disposition'] = (
        f'attachment; filename="{safe_name}_BOM完整包.zip"'
    )
    return response


# ── Cart API ─────────────────────────────────


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cart_list(request):
    """List cart items for the current user/session."""
    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user)
    else:
        sk = request.session.session_key or ''
        items = CartItem.objects.filter(session_key=sk)
    serializer = CartItemSerializer(items, many=True)
    return Response(serializer.data)


def _calc_tree_total(node) -> float:
    """Recursively sum total_price from a BOM expansion tree node and its children."""
    total = 0.0
    # Node's own total (usually 0 for non-leaf, but include if set)
    tp = node.get('total_price')
    if tp is not None:
        total += float(tp)
    # Children totals
    for child in node.get('children', []):
        total += _calc_tree_total(child)
    return total


def _flatten_bom_subtree(children, depth=0):
    """Flatten recursive BOM tree children into a flat list for ProjectItem creation."""
    items = []
    for child in children:
        if child.get('excluded'):
            continue
        items.append(child)
        # Recurse into grandchildren
        grandchildren = child.get('children', [])
        if grandchildren:
            items.extend(_flatten_bom_subtree(grandchildren, depth + 1))
    return items


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def cart_add(request):
    """Add an item to the cart."""
    data = request.data.copy()

    # Compute unit_price at add time
    unit_price = None
    item_type = data.get('item_type', 'parametric')

    if item_type == 'parametric':
        # Accept both 'product_part' and 'parametric_part_id'
        product_part_id = data.get('product_part') or data.get('parametric_part_id')
        if not product_part_id:
            product_part_id = data.get('product_part_id')
        if product_part_id:
            data['product_part'] = int(product_part_id)  # normalize FK field name
            try:
                from part.models import Part
                part = Part.objects.get(pk=int(product_part_id))
                # Server-side BOM expansion for price calculation
                try:
                    from parametric_bom.bom_expander import expand_bom_level
                    params = data.get('parameters', {}) or data.get('params', {}) or {}
                    data['parameters'] = params  # normalize field name
                    bom_tree = expand_bom_level(part, params, timeout_ms=1000)
                    data['bom_snapshot'] = bom_tree
                    # Calculate total price from expanded BOM
                    total = _calc_tree_total(bom_tree)
                    if total and total > 0:
                        data['unit_price'] = str(round(total, 4))
                except Exception:
                    pass
            except Exception:
                pass

    elif item_type == 'static':
        part_id = data.get('part')
        if part_id:
            try:
                from part.models import Part
                part = Part.objects.get(pk=int(part_id))
                if hasattr(part, 'pricing') and part.pricing:
                    p = part.pricing
                    unit_price = float(
                        p.overall_min or p.overall_max or
                        p.internal_cost_min or p.internal_cost_max or
                        p.bom_cost_min or p.bom_cost_max or 0
                    )
            except Exception:
                pass

    if unit_price is not None:
        data['unit_price'] = str(unit_price)

    if request.user.is_authenticated:
        serializer = CartItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    else:
        if not request.session.session_key:
            request.session.create()
        data['session_key'] = request.session.session_key
        serializer = CartItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['PATCH', 'DELETE'])
@permission_classes([permissions.AllowAny])
def cart_item_detail(request, item_id):
    """Update or delete a cart item."""
    try:
        item = CartItem.objects.get(pk=item_id)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=404)
    # Ownership check
    if item.user and request.user.is_authenticated and item.user != request.user:
        return Response({'error': 'Permission denied'}, status=403)
    elif item.session_key and item.session_key != request.session.session_key:
        if not request.session.session_key and not request.user.is_authenticated:
            # Anonymous request, no session — allow (first-time visitors)
            pass
        elif item.session_key != request.session.session_key:
            return Response({'error': 'Permission denied'}, status=403)
    if request.method == 'DELETE':
        item.delete()
        return Response(status=204)
    # PATCH
    serializer = CartItemSerializer(item, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def cart_clear(request):
    """Clear all cart items for the current user/session."""
    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user)
    else:
        sk = request.session.session_key or ''
        items = CartItem.objects.filter(session_key=sk)
    count, _ = items.delete()
    return Response({'deleted': count})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cart_count(request):
    """Get the cart item count for the current user/session."""
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
    else:
        sk = request.session.session_key or ''
        count = CartItem.objects.filter(session_key=sk).count()
    return Response({'count': count})


# ── Cart → Order ────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cart_export_csv(request):
    """导出购物车为CSV订单文件。"""
    import csv
    from django.http import HttpResponse

    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user)
    else:
        sk = request.session.session_key or ''
        items = CartItem.objects.filter(session_key=sk)

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="cart_order.csv"'

    writer = csv.writer(response)
    writer.writerow(['序号', '类型', '名称', '编号/型号', '参数摘要', '数量', '单价', '小计'])

    total_qty = 0
    total_amt = 0.0

    for idx, item in enumerate(items, 1):
        item_type = '参数化' if item.item_type == 'parametric' else '标准件'
        name = item.title or ''
        ipn = ''
        params_summary = ''

        if item.item_type == 'parametric' and item.product_part:
            ipn = item.product_part.IPN or ''
            if item.parameters and isinstance(item.parameters, dict):
                param_parts = [f'{k}={v}' for k, v in item.parameters.items()]
                params_summary = ', '.join(param_parts)
        elif item.item_type == 'static' and item.part:
            ipn = item.part.IPN or ''

        qty = item.quantity or 1
        price = float(item.unit_price) if item.unit_price else 0.0
        subtotal = price * qty
        total_qty += qty
        total_amt += subtotal

        writer.writerow([idx, item_type, name, ipn, params_summary, qty, price, subtotal])

    writer.writerow([])
    writer.writerow(['', '', '', '', '合计', total_qty, '', round(total_amt, 2)])
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cart_create_order(request):
    """从购物车创建InvenTree销售订单(SalesOrder)。

    - 静态零件 → 直接作为行项添加
    - 参数化产品 → 将产品模板作为行项添加，参数存到备注
    创建成功后清空购物车。
    """
    from order.models import SalesOrder, SalesOrderLineItem
    from part.models import Part
    from company.models import Company

    try:
        items = CartItem.objects.filter(user=request.user)
        if not items.exists():
            return Response({'error': '购物车是空的'}, status=400)

        # 获取默认客户（取第一个客户，或允许传参）
        customer_id = request.data.get('customer_id')
        description = request.data.get('description', '参数化BOM购物车订单')

        if customer_id:
            customer = Company.objects.get(pk=customer_id)
        else:
            customer = Company.objects.filter(is_customer=True).first()
            if not customer:
                return Response({'error': '没有可用的客户，请先创建客户或指定customer_id'}, status=400)

        # 创建销售订单
        order = SalesOrder.objects.create(
            customer=customer,
            description=description,
            created_by=request.user,
        )

        line_items_created = 0
        for item in items:
            part = None
            notes = item.notes or ''

            if item.item_type == 'parametric' and item.product_part:
                part = item.product_part
                if item.parameters and isinstance(item.parameters, dict):
                    param_str = '; '.join(f'{k}={v}' for k, v in item.parameters.items())
                    if notes:
                        notes = f'参数: {param_str} | {notes}'
                    else:
                        notes = f'参数: {param_str}'
            elif item.item_type == 'static' and item.part:
                part = item.part

            if not part:
                continue

            SalesOrderLineItem.objects.create(
                order=order,
                part=part,
                quantity=item.quantity or 1,
                sale_price=float(item.unit_price) if item.unit_price else None,
                notes=notes[:500] if notes else '',
            )
            line_items_created += 1

        if line_items_created == 0:
            order.delete()
            return Response({'error': '没有有效的行项可创建'}, status=400)

        # 清空购物车
        items.delete()

        return Response({
            'success': True,
            'order_id': order.id,
            'order_reference': order.reference,
            'line_items': line_items_created,
        }, status=201)

    except Company.DoesNotExist:
        return Response({'error': '指定客户不存在'}, status=404)
    except Exception as e:
        logger.exception('创建订单失败')
        return Response({'error': f'创建订单失败: {str(e)}'}, status=500)


# ── Project Permission (RBAC) ─────────────────

def has_project_perm(project, user, permission):
    """Check if a user has a specific permission on a project.
    
    Owner and staff have all permissions.
    """
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    if project.owner == user:
        return True
    # Check via ProjectMembership → ProjectRole
    from parametric_bom.models import ProjectMembership
    try:
        membership = ProjectMembership.objects.get(project=project, user=user)
        return permission in membership.role.permissions
    except ProjectMembership.DoesNotExist:
        return False


def get_user_project_roles(project, user):
    """Get all info about a user's roles on a project."""
    if not user.is_authenticated:
        return {'role': 'none', 'permissions': []}
    if user.is_staff:
        from parametric_bom.models import PROJECT_PERMISSIONS
        return {
            'role': 'admin',
            'permissions': [p[0] for p in PROJECT_PERMISSIONS],
        }
    if project.owner == user:
        from parametric_bom.models import PROJECT_PERMISSIONS
        return {
            'role': 'owner',
            'permissions': [p[0] for p in PROJECT_PERMISSIONS],
        }
    from parametric_bom.models import ProjectMembership
    try:
        membership = ProjectMembership.objects.get(project=project, user=user)
        return {
            'role': membership.role.name,
            'permissions': membership.role.permissions,
        }
    except ProjectMembership.DoesNotExist:
        return {'role': 'none', 'permissions': []}


class ProjectPermission(permissions.BasePermission):
    """RBAC-based project permission check."""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff or obj.owner == user:
            return True
        # For safe methods, check view_project
        if request.method in permissions.SAFE_METHODS:
            if obj.is_public:
                return True
            return has_project_perm(obj, user, 'view_project')
        # For write methods, check edit_project
        return has_project_perm(obj, user, 'edit_project')


# ── Project ViewSet ─────────────────────────

class ProjectViewSet(viewsets.ModelViewSet):
    """API endpoints for Project management."""

    queryset = Project.objects.all()
    permission_classes = [permissions.IsAuthenticated, ProjectPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'project_code', 'description']
    ordering_fields = ['created_at', 'name', 'project_code', 'status']
    ordering = ['-created_at']
    filterset_fields = ['status', 'is_active']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectDetailSerializer

    def get_queryset(self):
        qs = Project.objects.all()
        user = self.request.user
        if not user.is_staff:
            from parametric_bom.models import ProjectMembership
            member_project_ids = ProjectMembership.objects.filter(
                user=user
            ).values_list('project_id', flat=True)
            qs = qs.filter(
                django_models.Q(owner=user)
                | django_models.Q(id__in=list(member_project_ids))
                | django_models.Q(is_public=True)
            ).distinct()
        # 列表模式默认只显示活跃项目，详情/更新/删除等不限制
        if self.action == 'list':
            inactive_param = self.request.query_params.get('inactive')
            if inactive_param == '1':
                qs = qs.filter(is_active=False)
            elif not inactive_param:
                qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        project = serializer.save(
            created_by=self.request.user,
            owner=self.request.user,
        )
        self._log(project, 'created', '项目已创建')

    def perform_update(self, serializer):
        old = self.get_object()
        project = serializer.save()
        changes = []
        for field in ['name', 'status', 'description', 'deadline']:
            old_val = getattr(old, field, None)
            new_val = getattr(project, field, None)
            if old_val != new_val:
                changes.append(f'{field}: {old_val} → {new_val}')
        if changes:
            self._log(project, 'updated', '; '.join(changes))

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Soft-delete (archive) a project."""
        project = self.get_object()
        project.is_active = False
        project.save(update_fields=['is_active'])
        self._log(project, 'archived', '项目已归档')
        return Response({'success': True, 'is_active': False})

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived project."""
        project = self.get_object()
        project.is_active = True
        project.save(update_fields=['is_active'])
        self._log(project, 'restored', '项目已恢复')
        return Response({'success': True, 'is_active': True})

    @action(detail=True, methods=['post'])
    def hard_delete(self, request, pk=None):
        """Permanently delete a project and all its data."""
        project = self.get_object()
        name = project.name
        code = project.project_code
        # Log before deletion
        self._log(project, 'hard_deleted', f'项目已永久删除: {code} - {name}')
        project.delete()  # CASCADE deletes items, logs, memberships
        return Response({'success': True, 'deleted': f'{code} - {name}'})

    def _log(self, project, action, description='', details=None):
        ProjectLog.objects.create(
            project=project,
            user=self.request.user if self.request else None,
            action=action,
            description=description,
            details=details,
        )

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get all items for a project."""
        project = self.get_object()
        items = project.items.all()
        serializer = ProjectItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add an item to a project."""
        project = self.get_object()
        data = {**request.data, 'project': project.id}

        # ── Merge: 同一批次内名称+型号相同则叠加数量 ──
        batch_name = data.get('batch_name', '')
        title = data.get('title', '')
        part_id = data.get('part')
        item_type = data.get('item_type', 'configuration')
        merge_filter = {
            'project': project,
            'batch_name': batch_name or None,
            'title': title,
            'item_type': item_type,
        }
        if part_id and item_type == 'part':
            merge_filter['part_id'] = int(part_id)
        existing = ProjectItem.objects.filter(**merge_filter).first()
        if existing:
            add_qty = int(data.get('quantity', 1))
            existing.quantity += add_qty
            existing.created_by = request.user
            existing.save(update_fields=['quantity', 'created_by'])
            self._log(project, 'item_merged',
                      f'合并条目: {title} 数量 +{add_qty} → {existing.quantity}')
            serializer = ProjectItemSerializer(existing, context={'request': request})
            return Response(serializer.data, status=200)

        # Auto-expand BOM for configuration items
        if data.get('item_type') == 'configuration':
            product_part_id = data.get('product_part_id') or data.get('product_part')
            if product_part_id:
                try:
                    from part.models import Part
                    from parametric_bom.bom_expander import expand_bom_level
                    from parametric_bom.models import ProductConfiguration
                    part = Part.objects.get(pk=int(product_part_id))
                    params = data.get('parameters', {}) or {}
                    bom_tree = expand_bom_level(part, params, timeout_ms=1000)
                    data['bom_snapshot'] = bom_tree
                    # Calculate price
                    total = _calc_tree_total(bom_tree)
                    if total and total > 0:
                        data['unit_price'] = str(round(total, 4))
                    # Create ProductConfiguration record
                    config = ProductConfiguration.objects.create(
                        template_part=part,
                        title=data.get('title', part.name),
                        params_snapshot=params,
                        generated_bom=bom_tree,
                        created_by=request.user,
                    )
                    data['product_config'] = config.id
                except Exception:
                    pass

        serializer = ProjectItemSerializer(
            data=data,
            context={'request': request},
        )
        if serializer.is_valid():
            item = serializer.save()
            # Set created_by on the item (not in serializer fields)
            item.created_by = request.user
            item.save(update_fields=['created_by'])
            self._log(project, 'item_added', f'添加条目: {item.title} x{item.quantity}')

            # Re-serialize to include created_by_name
            serializer = ProjectItemSerializer(item, context={'request': request})

            # Auto-expand BOM sub-items into project
            created_items = [serializer.data]
            bom_snapshot = getattr(item, 'bom_snapshot', None) or data.get('bom_snapshot')
            if bom_snapshot:
                # Handle both flat format {bom_tree: [...]} and tree format {children: [...]}
                bom_items = None
                if isinstance(bom_snapshot, dict):
                    if 'bom_tree' in bom_snapshot and isinstance(bom_snapshot['bom_tree'], list):
                        bom_items = bom_snapshot['bom_tree']
                    elif 'children' in bom_snapshot:
                        bom_items = _flatten_bom_subtree(bom_snapshot['children'])
                if bom_items:
                    batch_name = data.get('batch_name', '') or item.batch_name or ''
                    for bi in bom_items:
                        qty = bi.get('calculated_quantity', bi.get('quantity', 1))
                        up = bi.get('unit_price')
                        child = ProjectItem.objects.create(
                            project=project,
                            item_type='part',
                            title=bi.get('part_name', bi.get('calculated_name', '')),
                            part_id=bi.get('part_id'),
                            quantity=int(qty) if qty == int(qty) else qty,
                            unit_price=str(round(float(up), 4)) if up else None,
                            batch_name=batch_name,
                            created_by=request.user,
                        )
                        child_ser = ProjectItemSerializer(child, context={'request': request})
                        created_items.append(child_ser.data)
                    self._log(project, 'item_added',
                              f'并展开 {len(bom_items)} 个BOM子件')

            return Response(created_items if len(created_items) > 1 else created_items[0],
                          status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['patch', 'delete'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, pk=None, item_id=None):
        """Update or remove an item from a project."""
        project = self.get_object()
        item = get_object_or_404(ProjectItem, id=item_id, project=project)

        if request.method == 'DELETE':
            self._log(project, 'item_removed', f'移除条目: {item.title}')
            item.delete()
            return Response({'success': True}, status=200)

        # PATCH — update item fields
        serializer = ProjectItemSerializer(
            item,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        if serializer.is_valid():
            updated = serializer.save()
            self._log(project, 'item_updated',
                      f'更新条目: {item.title} → {updated.title} x{updated.quantity}')
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['post'])
    def from_cart(self, request):
        """Convert cart items into a project."""
        serializer = FromCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        cart_items = CartItem.objects.filter(id__in=data['cart_item_ids'])

        if not cart_items.exists():
            return Response({'error': '购物车中未找到指定条目'}, status=400)

        # Create the project
        customer = None
        if data.get('customer_id'):
            from company.models import Company
            try:
                customer = Company.objects.get(id=data['customer_id'])
            except Company.DoesNotExist:
                return Response({'error': '指定客户不存在'}, status=404)

        project = Project.objects.create(
            name=data['name'],
            customer=customer,
            description=data.get('description', ''),
            deadline=data.get('deadline'),
            created_by=request.user,
            owner=request.user,
        )

        # Create ProjectItems from CartItems
        item_count = 0
        for ci in cart_items:
            item_kwargs = {
                'project': project,
                'title': ci.title or ci.product_part.name if ci.product_part else ci.part.name if ci.part else '',
                'quantity': ci.quantity,
            }
            if ci.item_type == 'parametric' and ci.product_part:
                item_kwargs['item_type'] = 'configuration'
                # Create ProductConfiguration from CartItem data
                from parametric_bom.models import ProductConfiguration
                config = ProductConfiguration.objects.create(
                    template_part=ci.product_part,
                    title=ci.title or ci.product_part.name,
                    params_snapshot=ci.parameters,
                    generated_bom=ci.bom_snapshot,
                    created_by=request.user,
                )
                item_kwargs['product_config'] = config
                item_kwargs['bom_snapshot'] = ci.bom_snapshot
                item_kwargs['unit_cost'] = ci.unit_price
            else:
                item_kwargs['item_type'] = 'part'
                item_kwargs['part'] = ci.part
                item_kwargs['unit_price'] = ci.unit_price
            item_kwargs['created_by'] = request.user
            ProjectItem.objects.create(**item_kwargs)
            item_count += 1

        # Clear the converted cart items
        cart_items.delete()

        self._log(project, 'from_cart',
                  f'从购物车创建项目，包含 {item_count} 个条目')

        return Response(
            ProjectDetailSerializer(project, context={'request': request}).data,
            status=201,
        )

    @action(detail=True, methods=['post'])
    def create_purchase_orders(self, request, pk=None):
        """Generate PurchaseOrders from the project's BOM parts, grouped by supplier."""
        from company.models import Company, SupplierPart

        project = self.get_object()
        orders_created = []

        # Collect all unique parts from all items' BOM snapshots
        parts_needed = {}  # {part_id: {part: Part, quantity: int}}
        for item in project.items.all():
            if item.bom_snapshot:
                self._collect_bom_parts(item.bom_snapshot, parts_needed, item.quantity)
            elif item.part:
                pid = item.part.id
                if pid not in parts_needed:
                    parts_needed[pid] = {'part': item.part, 'quantity': 0}
                parts_needed[pid]['quantity'] += item.quantity

        if not parts_needed:
            return Response({'error': '项目中没有需要采购的零件'}, status=400)

        # Group by supplier from SupplierPart
        supplier_groups = {}  # {supplier_id: {supplier: Company, items: [{part, qty}]}}
        for pid, info in parts_needed.items():
            supplier_parts = SupplierPart.objects.filter(part=info['part'])
            if supplier_parts.exists():
                sp = supplier_parts.first()
                sid = sp.supplier.id
                if sid not in supplier_groups:
                    supplier_groups[sid] = {
                        'supplier': sp.supplier,
                        'items': [],
                    }
                supplier_groups[sid]['items'].append({
                    'part': info['part'],
                    'quantity': info['quantity'],
                    'sku': sp.SKU,
                })
            else:
                # No supplier — create an unassigned group
                if 0 not in supplier_groups:
                    supplier_groups[0] = {'supplier': None, 'items': []}
                supplier_groups[0]['items'].append({
                    'part': info['part'],
                    'quantity': info['quantity'],
                    'sku': None,
                })

        from order.models import PurchaseOrder, PurchaseOrderLineItem

        for sid, group in supplier_groups.items():
            if not group['supplier']:
                continue
            po = PurchaseOrder.objects.create(
                supplier=group['supplier'],
                created_by=request.user,
                description=f'Auto-generated from project: {project.project_code}',
            )
            for item in group['items']:
                PurchaseOrderLineItem.objects.create(
                    order=po,
                    part=item['part'],
                    quantity=item['quantity'],
                    reference=item.get('sku', ''),
                )
            orders_created.append({
                'order_id': po.id,
                'supplier': group['supplier'].name,
                'reference': str(po),
                'line_items': len(group['items']),
            })

        self._log(project, 'purchase_orders_created',
                  f'生成 {len([o for o in orders_created if o.get("order_id")])} 个采购订单')

        # Handle unassigned parts
        if 0 in supplier_groups:
            orders_created.append({
                'supplier': None,
                'parts': [f"{i['part'].name} x{i['quantity']}" for i in supplier_groups[0]['items']],
                'note': 'No supplier found for these parts',
            })

        return Response({'orders': orders_created}, status=201)

    @action(detail=True, methods=['post'])
    def create_sales_order(self, request, pk=None):
        """Generate a SalesOrder from the project."""
        from company.models import Company
        from order.models import SalesOrder, SalesOrderLineItem

        project = self.get_object()
        if not project.customer:
            return Response({'error': '项目未关联客户，无法创建销售订单'}, status=400)

        so = SalesOrder.objects.create(
            customer=project.customer,
            created_by=request.user,
            description=f'Auto-generated from project: {project.project_code} - {project.name}',
        )
        line_count = 0
        for item in project.items.all():
            part = None
            if item.item_type == 'configuration' and item.product_config:
                part = item.product_config.template_part
            elif item.item_type == 'part':
                part = item.part
            if part:
                SalesOrderLineItem.objects.create(
                    order=so,
                    part=part,
                    quantity=item.quantity,
                )
                line_count += 1

        self._log(project, 'sales_order_created',
                  f'生成销售订单，包含 {line_count} 条明细')

        return Response({
            'order_id': so.id,
            'reference': str(so),
            'line_items': line_count,
        }, status=201)

    @action(detail=True, methods=['get'])
    def cost_summary(self, request, pk=None):
        """Get cost summary for a project."""
        import re
        from part.models import Part, PartCategory
        project = self.get_object()
        total_cost = 0
        total_price = 0
        breakdown = []
        batch_breakdown = {}
        cat_breakdown = {}
        for item in project.items.all().select_related('part', 'product_config__template_part'):
            cost = float(item.unit_cost or 0) * item.quantity
            price = float(item.unit_price or 0) * item.quantity
            total_cost += cost
            total_price += price

            # Determine category name from the underlying Part
            part_obj = None
            if item.part_id:
                part_obj = item.part
            elif item.product_config and item.product_config.template_part_id:
                part_obj = item.product_config.template_part
            cat_name = '未分类'
            if part_obj and part_obj.category_id:
                cat_name = part_obj.category.name
                # Walk up to root for full path
                parent = part_obj.category
                path_parts = [parent.name]
                while parent.parent_id:
                    parent = parent.parent
                    path_parts.insert(0, parent.name)
                cat_name = ' / '.join(path_parts)

            breakdown.append({
                'title': item.title,
                'type': item.item_type,
                'quantity': item.quantity,
                'batch_name': item.batch_name or '未分组',
                'category': cat_name,
                'unit_cost': float(item.unit_cost or 0),
                'unit_price': float(item.unit_price or 0),
                'subtotal_cost': cost,
                'subtotal_price': price,
            })
            bname = item.batch_name or '未分组'
            if bname not in batch_breakdown:
                batch_breakdown[bname] = {'item_count': 0, 'total_qty': 0, 'total_cost': 0, 'total_price': 0}
            batch_breakdown[bname]['item_count'] += 1
            batch_breakdown[bname]['total_qty'] += item.quantity
            batch_breakdown[bname]['total_cost'] += cost
            batch_breakdown[bname]['total_price'] += price

            if cat_name not in cat_breakdown:
                cat_breakdown[cat_name] = {'count': 0, 'total_cost': 0, 'total_price': 0}
            cat_breakdown[cat_name]['count'] += 1
            cat_breakdown[cat_name]['total_cost'] += cost
            cat_breakdown[cat_name]['total_price'] += price

        # Sort batch breakdown: "第N批" by number desc, others by cost desc
        batch_list = []
        for bname, data in batch_breakdown.items():
            ma = re.match(r'^第(\d+)批$', bname) if bname != '未分组' else None
            bn = int(ma.group(1)) if ma else (0 if bname == '未分组' else 999)
            batch_list.append({'batch_name': bname, **data, '_sort_num': bn})
        batch_list.sort(key=lambda b: (1 if b['batch_name'] == '未分组' else 0, -b['_sort_num']))

        return Response({
            'project_id': project.id,
            'project_code': project.project_code,
            'total_cost': total_cost,
            'total_price': total_price,
            'profit': total_price - total_cost,
            'margin_pct': round((total_price - total_cost) / total_price * 100, 2) if total_price and total_price > 0 else (0 if total_price == 0 and total_cost == 0 else -100.0),
            'breakdown': breakdown,
            'batch_breakdown': batch_list,
            'category_breakdown': [
                {'category': cat, 'count': data['count'], 'total_cost': data['total_cost'], 'total_price': data['total_price']}
                for cat, data in sorted(cat_breakdown.items(), key=lambda x: -x[1]['total_cost'])
            ],
        })

    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """Get related purchase/sales orders for a project."""
        from InvenTree.helpers import pui_url
        from order.models import PurchaseOrder, SalesOrder
        project = self.get_object()
        # Search by description containing project code
        pos = PurchaseOrder.objects.filter(
            description__icontains=project.project_code
        ).order_by('-creation_date')[:20]
        sos = SalesOrder.objects.filter(
            description__icontains=project.project_code
        ).order_by('-creation_date')[:20]

        # Check if user has permission to view purchase/sales orders
        can_view_po = request.user.has_perm('order.view_purchaseorder')
        can_view_so = request.user.has_perm('order.view_salesorder')

        return Response({
            'purchase_orders': [{
                'id': po.id,
                'reference': str(po),
                'supplier': po.supplier.name if po.supplier else '',
                'status': po.status if hasattr(po, 'status') else '',
                'line_items': po.lines.count() if hasattr(po, 'lines') else 0,
                'created': po.creation_date.isoformat() if hasattr(po, 'creation_date') and po.creation_date else '',
                'url': pui_url(f'/purchasing/purchase-order/{po.pk}/') if can_view_po else '',
            } for po in pos],
            'sales_orders': [{
                'id': so.id,
                'reference': str(so),
                'customer': so.customer.name if so.customer else '',
                'status': so.status if hasattr(so, 'status') else '',
                'line_items': so.lines.count() if hasattr(so, 'lines') else 0,
                'created': so.creation_date.isoformat() if hasattr(so, 'creation_date') and so.creation_date else '',
                'url': pui_url(f'/sales/sales-order/{so.pk}/') if can_view_so else '',
            } for so in sos],
        })

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export project as CSV report."""
        import csv
        from django.http import HttpResponse

        project = self.get_object()

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="project_{project.project_code}.csv"'

        writer = csv.writer(response)

        # Header section
        writer.writerow(['项目报告', project.project_code, project.name])
        writer.writerow([])
        writer.writerow(['项目编号', '项目名称', '客户', '状态', '负责人', '截止日期', '创建时间'])
        writer.writerow([
            project.project_code,
            project.name,
            project.customer.name if project.customer else '',
            project.get_status_display(),
            project.owner.get_full_name() or project.owner.username if project.owner else '',
            project.deadline or '',
            project.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
        if project.description:
            writer.writerow(['描述', project.description])
        writer.writerow([])

        # Items section
        writer.writerow(['== 项目条目 =='])
        writer.writerow(['名称', '类型', '数量', '单价', '小计', '备注'])
        total_cost = 0
        total_price = 0
        for item in project.items.all():
            cost = float(item.unit_cost or 0) * item.quantity
            price = float(item.unit_price or 0) * item.quantity
            total_cost += cost
            total_price += price
            writer.writerow([
                item.title,
                item.get_item_type_display(),
                item.quantity,
                f'{item.unit_price or 0:.2f}',
                f'{price:.2f}',
                item.notes or '',
            ])

        # Cost summary
        writer.writerow([])
        writer.writerow(['== 成本汇总 =='])
        writer.writerow(['总成本', f'{total_cost:.2f}'])
        writer.writerow(['总售价', f'{total_price:.2f}'])
        writer.writerow(['利润', f'{total_price - total_cost:.2f}'])
        if total_price:
            margin = (total_price - total_cost) / total_price * 100
            writer.writerow(['毛利率', f'{margin:.1f}%'])

        return response

    @action(detail=True, methods=['post'])
    def save_as_template(self, request, pk=None):
        """Mark the project as a template, optionally with a new name."""
        project = self.get_object()
        name = request.data.get('template_name', '')
        if name:
            project.name = f'[模板] {name}'
        project.is_template = True
        project.save(update_fields=['is_template', 'name'])
        self._log(project, 'saved_as_template', f'保存为模板: {project.name}')
        return Response({
            'success': True,
            'project_id': project.id,
            'is_template': True,
            'template_name': project.name,
        })

    @action(detail=True, methods=['post'])
    def create_from_template(self, request, pk=None):
        """Create a new project from this template, copying items."""
        project = self.get_object()
        if not project.is_template:
            return Response({'error': '该项目不是模板'}, status=400)

        new_name = request.data.get('name', project.name.replace('[模板] ', '').strip() + ' (副本)')
        new_project = Project.objects.create(
            name=new_name,
            customer=project.customer,
            description=project.description,
            owner=request.user,
            created_by=request.user,
            template_source=project,
        )

        # Copy items
        for item in project.items.all():
            ProjectItem.objects.create(
                project=new_project,
                item_type=item.item_type,
                product_config=None,  # Don't copy config snapshots
                part=item.part,
                title=item.title,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                unit_price=item.unit_price,
                notes=item.notes,
                sort_order=item.sort_order,
            )

        serializer = ProjectDetailSerializer(new_project, context={'request': request})
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['get', 'post'])
    def attachments(self, request, pk=None):
        """List or upload attachments for a project."""
        from common.models import Attachment
        from common.serializers import AttachmentSerializer

        project = self.get_object()

        if request.method == 'GET':
            atts = Attachment.objects.filter(
                model_type='project', model_id=project.id
            )
            serializer = AttachmentSerializer(
                atts, many=True, context={'request': request}
            )
            return Response(serializer.data)

        # POST: upload a new attachment
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['model_type'] = 'project'
        data['model_id'] = project.id
        serializer = AttachmentSerializer(
            data=data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        attachment = serializer.save(
            model_type='project',
            model_id=project.id,
            upload_user=request.user,
        )
        self._log(project, 'attachment_uploaded',
                  f'上传附件: {attachment.basename or attachment.link or ""}')
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['delete'], url_path='attachments/(?P<att_id>[^/.]+)')
    def remove_attachment(self, request, pk=None, att_id=None):
        """Delete an attachment from a project."""
        from common.models import Attachment

        project = self.get_object()
        att = get_object_or_404(Attachment, id=att_id, model_type='project', model_id=project.id)
        name = att.basename or att.link or 'attachment'
        att.delete()
        self._log(project, 'attachment_removed', f'删除附件: {name}')
        return Response({'success': True}, status=200)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get change logs for a project."""
        project = self.get_object()
        logs = project.logs.all()[:50]
        data = [{
            'id': l.id,
            'action': l.action,
            'description': l.description,
            'user': l.user.get_full_name() or l.user.username if l.user else 'system',
            'created_at': l.created_at.isoformat(),
        } for l in logs]
        return Response(data)

    # ---- RBAC: Available permissions ----

    @action(detail=False, methods=['get'])
    def permissions_def(self, request):
        """Return all available project permissions."""
        from parametric_bom.models import PROJECT_PERMISSIONS
        return Response([{'code': p[0], 'label': p[1]} for p in PROJECT_PERMISSIONS])

    # ---- RBAC: Roles ----

    @action(detail=True, methods=['get'])
    def roles(self, request, pk=None):
        """List all roles for the project."""
        project = self.get_object()
        from parametric_bom.serializers import ProjectRoleSerializer
        roles = project.roles.all()
        return Response(ProjectRoleSerializer(roles, many=True).data)

    @action(detail=True, methods=['post'])
    def create_role(self, request, pk=None):
        """Create a custom role."""
        project = self.get_object()
        from parametric_bom.serializers import ProjectRoleSerializer
        serializer = ProjectRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        role = serializer.save(project=project, is_preset=False)
        self._log(project, 'role_created', f'创建角色: {role.name}')
        return Response(ProjectRoleSerializer(role).data, status=201)

    @action(detail=True, methods=['patch'], url_path='roles/(?P<role_id>[^/.]+)')
    def update_role(self, request, pk=None, role_id=None):
        """Update a role's name or permissions."""
        project = self.get_object()
        from parametric_bom.models import ProjectRole
        role = get_object_or_404(ProjectRole, id=role_id, project=project)
        name = request.data.get('name', role.name)
        permissions = request.data.get('permissions', role.permissions)
        role.name = name
        role.permissions = permissions
        role.save(update_fields=['name', 'permissions'])
        self._log(project, 'role_updated', f'更新角色: {role.name}')
        from parametric_bom.serializers import ProjectRoleSerializer
        return Response(ProjectRoleSerializer(role).data)

    @action(detail=True, methods=['delete'], url_path='roles/(?P<role_id>[^/.]+)')
    def delete_role(self, request, pk=None, role_id=None):
        """Delete a custom role (not preset)."""
        project = self.get_object()
        from parametric_bom.models import ProjectRole
        role = get_object_or_404(ProjectRole, id=role_id, project=project)
        if role.is_preset:
            return Response({'error': '预设角色不可删除'}, status=400)
        name = role.name
        role.delete()
        self._log(project, 'role_deleted', f'删除角色: {name}')
        return Response({'success': True})

    # ---- RBAC: Memberships ----

    @action(detail=True, methods=['get'])
    def members_list(self, request, pk=None):
        """List all memberships with role info."""
        project = self.get_object()
        from parametric_bom.serializers import ProjectMembershipSerializer
        memberships = project.memberships.select_related('user', 'role').all()
        return Response(ProjectMembershipSerializer(memberships, many=True).data)

    @action(detail=True, methods=['post'])
    def add_membership(self, request, pk=None):
        """Add a user as a member with a specific role."""
        project = self.get_object()
        user_id = request.data.get('user_id')
        role_id = request.data.get('role_id')
        if not user_id or not role_id:
            return Response({'error': '需要 user_id 和 role_id'}, status=400)
        from django.contrib.auth import get_user_model
        from parametric_bom.models import ProjectRole
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'user not found'}, status=404)
        role = get_object_or_404(ProjectRole, id=role_id, project=project)
        from parametric_bom.models import ProjectMembership
        membership, created = ProjectMembership.objects.get_or_create(
            project=project, user=user, defaults={'role': role},
        )
        if not created:
            membership.role = role
            membership.save(update_fields=['role'])
        self._log(project, 'membership_added', f'添加成员: {user.username} → {role.name}')
        from parametric_bom.serializers import ProjectMembershipSerializer
        return Response(ProjectMembershipSerializer(membership).data, status=201 if created else 200)

    @action(detail=True, methods=['post'], url_path='memberships/(?P<member_id>[^/.]+)/change_role')
    def change_member_role(self, request, pk=None, member_id=None):
        """Change a member's role."""
        project = self.get_object()
        from parametric_bom.models import ProjectMembership, ProjectRole
        membership = get_object_or_404(ProjectMembership, id=member_id, project=project)
        role_id = request.data.get('role_id')
        role = get_object_or_404(ProjectRole, id=role_id, project=project)
        membership.role = role
        membership.save(update_fields=['role'])
        self._log(project, 'role_changed', f'修改 {membership.user.username} 角色为: {role.name}')
        from parametric_bom.serializers import ProjectMembershipSerializer
        return Response(ProjectMembershipSerializer(membership).data)

    @action(detail=True, methods=['delete'], url_path='memberships/(?P<member_id>[^/.]+)')
    def remove_membership(self, request, pk=None, member_id=None):
        """Remove a member from the project."""
        project = self.get_object()
        from parametric_bom.models import ProjectMembership
        membership = get_object_or_404(ProjectMembership, id=member_id, project=project)
        self._log(project, 'membership_removed', f'移除成员: {membership.user.username}')
        membership.delete()
        return Response({'success': True})

    @action(detail=False, methods=['get'])
    def search_users(self, request):
        """Search users by name or username."""
        q = request.query_params.get('q', '').strip()
        if len(q) < 1:
            return Response([])
        limit = int(request.query_params.get('limit', 20))
        limit = min(limit, 100)  # cap at 100
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.filter(
            django_models.Q(username__icontains=q)
            | django_models.Q(first_name__icontains=q)
            | django_models.Q(last_name__icontains=q)
            | django_models.Q(email__icontains=q)
        )[:limit]
        return Response([{
            'id': u.id,
            'username': u.username,
            'name': u.get_full_name() or u.username,
        } for u in users])

    @action(detail=True, methods=['get'], url_path='export-batch-csv')
    def export_batch_csv(self, request, pk=None):
        """Export items of a specific batch as XLSX."""
        project = self.get_object()
        batch_name = request.query_params.get('batch_name', '').strip()
        items = project.items.filter(batch_name=batch_name).order_by('id')

        if not items.exists():
            return Response({'error': f'批次 "{batch_name}" 无条目'}, status=404)

        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

        wb = Workbook()
        ws = wb.active
        ws.title = batch_name[:31]

        thin = Side(style='thin', color='d0d5dd')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        header_font = Font(bold=True, size=11)
        header_fill = PatternFill(start_color='f0f4ff', end_color='f0f4ff', fill_type='solid')
        total_fill = PatternFill(start_color='f8fafc', end_color='f8fafc', fill_type='solid')

        ws.append(['项目', project.project_code, project.name])
        ws.append(['批次', batch_name])
        ws.append([])
        headers = ['名称', '类型', 'IPN', '数量', '单价', '小计', '含BOM', '备注']
        ws.append(headers)
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=4, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')

        total_price = 0
        for i, item in enumerate(items):
            price = float(item.unit_price or 0) * item.quantity
            total_price += price
            row = [
                item.title, item.get_item_type_display(),
                item.part.IPN if item.part else '',
                item.quantity, float(item.unit_price or 0),
                round(price, 2), '是' if item.bom_snapshot else '',
                item.notes or '',
            ]
            ws.append(row)
            r = i + 5
            for col in range(1, len(row) + 1):
                cell = ws.cell(row=r, column=col)
                cell.border = border

        ws.append([])
        summary_row = ['合计', '', '', '', '', round(total_price, 2)]
        ws.append(summary_row)
        r += 3
        for col in range(1, len(summary_row) + 1):
            cell = ws.cell(row=r, column=col)
            cell.fill = total_fill
            cell.font = Font(bold=True)

        # Column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 14
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 8
        ws.column_dimensions['E'].width = 10
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 8
        ws.column_dimensions['H'].width = 20

        safe = batch_name.replace(' ', '_').replace('-', '_')
        from django.http import HttpResponse
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{project.project_code}_{safe}.xlsx"'
        wb.save(response)
        return response

    @action(detail=True, methods=['get'], url_path='export-batch-zip')
    def export_batch_zip(self, request, pk=None):
        """Export items of a batch as ZIP: XLSX order table + individual BOM CSVs."""
        import zipfile, io

        project = self.get_object()
        batch_name = request.query_params.get('batch_name', '').strip()
        items = project.items.filter(batch_name=batch_name).order_by('id')

        if not items.exists():
            return Response({'error': f'批次 "{batch_name}" 无条目'}, status=404)

        buf = io.BytesIO()
        safe = batch_name.replace(' ', '_').replace('-', '_')

        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Main order XLSX
            wb = Workbook()
            ws = wb.active
            ws.title = '订单表'
            thin = Side(style='thin', color='d0d5dd')
            border = Border(left=thin, right=thin, top=thin, bottom=thin)
            hf = Font(bold=True, size=11)
            hfill = PatternFill(start_color='f0f4ff', end_color='f0f4ff', fill_type='solid')
            tfill = PatternFill(start_color='f8fafc', end_color='f8fafc', fill_type='solid')

            ws.append(['项目', project.project_code, project.name])
            ws.append(['批次', batch_name])
            ws.append([])
            headers = ['名称', '类型', 'IPN', '数量', '单价', '小计', '含BOM', '备注']
            ws.append(headers)
            for col in range(1, len(headers) + 1):
                c = ws.cell(row=4, column=col)
                c.font = hf; c.fill = hfill; c.border = border; c.alignment = Alignment(horizontal='center')

            total_price = 0
            for i, item in enumerate(items):
                price = float(item.unit_price or 0) * item.quantity
                total_price += price
                row = [item.title, item.get_item_type_display(),
                       item.part.IPN if item.part else '',
                       item.quantity, float(item.unit_price or 0),
                       round(price, 2), '是' if item.bom_snapshot else '', item.notes or '']
                ws.append(row)
                r = i + 5
                for col in range(1, len(row) + 1):
                    ws.cell(row=r, column=col).border = border

            ws.append([])
            ws.append(['合计', '', '', '', '', round(total_price, 2)])
            r += 3
            for col in range(1, 7):
                ws.cell(row=r, column=col).fill = tfill

            for letter, w in [('A',30),('B',14),('C',18),('D',8),('E',10),('F',12),('G',8),('H',20)]:
                ws.column_dimensions[letter].width = w

            xlsx_buf = io.BytesIO()
            wb.save(xlsx_buf)
            zf.writestr(f'{safe}_订单表.xlsx', xlsx_buf.getvalue())

            # 2. Individual BOM CSVs for items with bom_snapshot
            for item in items:
                if not item.bom_snapshot or not item.bom_snapshot.get('bom_tree'):
                    continue
                bom_items = item.bom_snapshot['bom_tree']
                bom_buf = io.StringIO()
                bw = csv.writer(bom_buf)
                part_name = item.bom_snapshot.get('part_name', item.title)
                bw.writerow([f'BOM — {part_name}'])
                bw.writerow(['子件名称', 'IPN', '数量', '单价', '单位'])

                def write_tree(tree, level=0):
                    for n in tree:
                        indent = '  ' * level
                        bw.writerow([
                            f'{indent}{n["part_name"]}',
                            n.get('IPN', ''),
                            n.get('quantity', 1),
                            f'{n.get("unit_price", 0):.2f}',
                            n.get('unit', ''),
                        ])
                        if 'children' in n:
                            write_tree(n['children'], level + 1)

                write_tree(bom_items)
                safe_title = item.title.replace(' ', '_').replace('/', '_')
                zf.writestr(f'{safe}/BOM_{safe_title}.csv', bom_buf.getvalue().encode('utf-8-sig'))

        from django.http import HttpResponse
        resp = HttpResponse(buf.getvalue(), content_type='application/zip')
        resp['Content-Disposition'] = f'attachment; filename="{project.project_code}_{safe}.zip"'
        return resp

    @action(detail=True, methods=['post'], url_path='batch-to-cart')
    def batch_to_cart(self, request, pk=None):
        """Move all items in a batch back to the shopping cart."""
        project = self.get_object()
        batch_name = request.data.get('batch_name', '').strip()

        if not batch_name:
            return Response({'error': '请指定批次名称'}, status=400)

        items = project.items.filter(batch_name=batch_name)
        if not items.exists():
            return Response({'error': f'批次 "{batch_name}" 无条目'}, status=404)

        # 禁止对已完成批次操作
        batch_obj = self._get_or_create_batch(project, batch_name)
        if batch_obj and batch_obj.status == 'completed':
            return Response({'error': '已完成批次不能还原到购物车'}, status=400)

        cart_items = []
        for item in items:
            if item.item_type == 'configuration':
                product_part = None
                parameters = None
                bom_snapshot = item.bom_snapshot
                if item.product_config:
                    product_part = item.product_config.template_part
                    parameters = item.product_config.params_snapshot
                ci = CartItem.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key if not request.user.is_authenticated else '',
                    item_type='parametric',
                    product_part=product_part,
                    title=item.title,
                    quantity=item.quantity,
                    parameters=parameters,
                    bom_snapshot=bom_snapshot,
                    unit_price=item.unit_cost or item.unit_price,
                )
            else:
                ci = CartItem.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key if not request.user.is_authenticated else '',
                    item_type='static',
                    part=item.part,
                    title=item.title,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
            cart_items.append(ci.id)

        count = items.count()
        items.delete()

        self._log(project, 'batch_to_cart',
                  f'批次 "{batch_name}" 的 {count} 个条目已还原到购物车')
        return Response({
            'success': True,
            'message': f'已还原 {count} 个条目到购物车',
            'cart_item_ids': cart_items,
        })

    @action(detail=True, methods=['post'], url_path='delete-batch')
    def delete_batch(self, request, pk=None):
        """Delete all items in a batch permanently."""
        project = self.get_object()
        batch_name = request.data.get('batch_name', '').strip()

        if not batch_name:
            return Response({'error': '请指定批次名称'}, status=400)
        if batch_name == '未分组':
            return Response({'error': '不能删除未分组批次'}, status=400)

        batch_obj = self._get_or_create_batch(project, batch_name)
        if batch_obj and batch_obj.status == 'completed':
            return Response({'error': '已完成批次不能删除'}, status=400)

        items = project.items.filter(batch_name=batch_name)
        count = items.count()
        if not count:
            return Response({'error': f'批次 "{batch_name}" 无条目'}, status=404)

        items.delete()
        self._log(project, 'batch_deleted',
                  f'已删除批次 "{batch_name}"（{count} 个条目）')
        return Response({
            'success': True,
            'message': f'已删除批次 "{batch_name}"，共 {count} 个条目',
        })

    @action(detail=True, methods=['get'])
    def batch_statuses(self, request, pk=None):
        """Return all batch statuses for the project."""
        project = self.get_object()
        statuses = {}
        for b in ProjectBatch.objects.filter(project=project):
            statuses[b.name] = b.status
        return Response(statuses)

    def _get_or_create_batch(self, project, batch_name):
        """Get or create a ProjectBatch record."""
        if not batch_name or batch_name == '未分组':
            return None
        batch, _ = ProjectBatch.objects.get_or_create(
            project=project, name=batch_name,
            defaults={'status': 'editing'},
        )
        return batch

    @action(detail=True, methods=['post'], url_path='batch-lock')
    def batch_lock(self, request, pk=None):
        """Lock a batch (editing → locked)."""
        project = self.get_object()
        batch_name = request.data.get('batch_name', '').strip()
        batch = self._get_or_create_batch(project, batch_name)
        if not batch:
            return Response({'error': '不能锁定未分组'}, status=400)
        batch.status = 'locked'
        batch.save(update_fields=['status', 'updated_at'])
        self._log(project, 'batch_locked', f'已锁定批次 "{batch_name}"')
        return Response({'success': True, 'status': 'locked', 'message': f'批次 "{batch_name}" 已锁定'})

    @action(detail=True, methods=['post'], url_path='batch-unlock')
    def batch_unlock(self, request, pk=None):
        """Unlock a batch (locked → editing)."""
        project = self.get_object()
        batch_name = request.data.get('batch_name', '').strip()
        try:
            batch = ProjectBatch.objects.get(project=project, name=batch_name)
        except ProjectBatch.DoesNotExist:
            return Response({'error': f'批次 "{batch_name}" 不存在'}, status=404)
        if batch.status != 'locked':
            return Response({'error': '只能反审已锁定的批次'}, status=400)
        batch.status = 'editing'
        batch.save(update_fields=['status', 'updated_at'])
        self._log(project, 'batch_unlocked', f'已反审解锁批次 "{batch_name}"')
        return Response({'success': True, 'status': 'editing', 'message': f'批次 "{batch_name}" 已解锁'})

    def _generate_batch_pos(self, project, batch_name, user):
        """Shared helper: generate POs for a batch, return (orders_created, unassigned, error_msg)."""
        from company.models import Company, SupplierPart
        from order.models import PurchaseOrder, PurchaseOrderLineItem

        items = project.items.filter(batch_name=batch_name)
        if not items.exists():
            return None, None, f'批次 "{batch_name}" 无条目'

        parts_needed = {}
        for item in items:
            if item.bom_snapshot:
                self._collect_bom_parts(item.bom_snapshot, parts_needed, item.quantity)
            elif item.part:
                pid = item.part.id
                if pid not in parts_needed:
                    parts_needed[pid] = {'part': item.part, 'quantity': 0}
                parts_needed[pid]['quantity'] += item.quantity

        if not parts_needed:
            return None, None, f'批次 "{batch_name}" 中没有需要采购的零件'

        supplier_groups = {}
        for pid, info in parts_needed.items():
            supplier_parts = SupplierPart.objects.filter(part=info['part'])
            if supplier_parts.exists():
                sp = supplier_parts.first()
                sid = sp.supplier.id
                if sid not in supplier_groups:
                    supplier_groups[sid] = {'supplier': sp.supplier, 'items': []}
                supplier_groups[sid]['items'].append({
                    'part': info['part'], 'quantity': info['quantity'], 'sku': sp.SKU,
                })
            else:
                if 0 not in supplier_groups:
                    supplier_groups[0] = {'supplier': None, 'items': []}
                supplier_groups[0]['items'].append({
                    'part_id': info['part'].id,
                    'part_name': info['part'].name,
                    'part_ipn': info['part'].IPN or '',
                    'quantity': info['quantity'], 'sku': None,
                })

        orders_created = []
        for sid, group in supplier_groups.items():
            if not group['supplier']:
                continue
            po = PurchaseOrder.objects.create(
                supplier=group['supplier'],
                created_by=user,
                description=f'Auto: {project.project_code} / {batch_name}',
            )
            for item in group['items']:
                # Use SupplierPart instead of Part for PurchaseOrderLineItem
                supplier_part = item.get('supplier_part')
                if not supplier_part:
                    supplier_part = SupplierPart.objects.filter(part=item['part']).first()
                if supplier_part:
                    PurchaseOrderLineItem.objects.create(
                        order=po, part=supplier_part,
                        quantity=item['quantity'], reference=item.get('sku', ''),
                    )
                else:
                    # Fallback: try Part directly
                    PurchaseOrderLineItem.objects.create(
                        order=po, part=item['part'],
                        quantity=item['quantity'], reference=item.get('sku', ''),
                    )
            orders_created.append({
                'order_id': po.id, 'supplier': group['supplier'].name,
                'reference': str(po), 'line_items': len(group['items']),
            })

        self._log(project, 'batch_purchase_orders',
                  f'批次 "{batch_name}" 生成 {len(orders_created)} 个采购订单')
        return orders_created, supplier_groups.get(0, {}).get('items', []), None

    @action(detail=True, methods=['post'], url_path='batch-purchase-orders')
    def batch_purchase_orders(self, request, pk=None):
        """Generate purchase orders for a specific batch."""
        project = self.get_object()
        batch_name = request.data.get('batch_name', '').strip()
        batch = self._get_or_create_batch(project, batch_name)
        if not batch:
            return Response({'error': '不能为未分组生成采购订单'}, status=400)
        if batch.status == 'completed':
            return Response({'error': '该批次已完成，不能重复生成'}, status=400)

        orders, unassigned, err = self._generate_batch_pos(project, batch_name, request.user)
        if err:
            return Response({'error': err}, status=400)

        return Response({
            'success': True,
            'orders': orders,
            'unassigned': unassigned,
            'message': f'已为批次 "{batch_name}" 生成 {len(orders)} 个采购订单',
        })

    @action(detail=True, methods=['post'], url_path='batch-complete')
    def batch_complete(self, request, pk=None):
        """Complete a batch — generates POs then marks as completed."""
        project = self.get_object()
        batch_name = request.data.get('batch_name', '').strip()
        batch = self._get_or_create_batch(project, batch_name)
        if not batch:
            return Response({'error': '不能为未分组完成'}, status=400)
        if batch.status == 'completed':
            return Response({'error': '该批次已完成'}, status=400)

        orders, unassigned, err = self._generate_batch_pos(project, batch_name, request.user)
        if err:
            # No purchasable parts — still allow marking as completed
            orders = []
            unassigned = []

        batch.status = 'completed'
        batch.save(update_fields=['status', 'updated_at'])
        self._log(project, 'batch_completed', f'批次 "{batch_name}" 已完成')

        msg = f'批次 "{batch_name}" 已完成'
        if orders:
            msg += f'，生成 {len(orders)} 个采购订单'
        else:
            msg += '（无可采购零件，未生成订单）'

        return Response({
            'success': True,
            'status': 'completed',
            'orders': orders,
            'unassigned': unassigned,
            'message': msg,
        })

    def _collect_bom_parts(self, node, parts_dict, multiplier=1):
        """Recursively collect parts from a BOM snapshot tree."""
        if node.get('part_id'):
            pid = node['part_id']
            qty = int(node.get('quantity', 1)) * multiplier
            if pid not in parts_dict:
                parts_dict[pid] = {'part': None, 'quantity': 0}
            parts_dict[pid]['quantity'] += qty
        for child in node.get('children', []):
            self._collect_bom_parts(child, parts_dict, multiplier)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def client_login(request):
    """C# WinForms 客户端登录 — 用户名密码换取 API Token"""
    username = request.data.get('username', '')
    password = request.data.get('password', '')

    if not username or not password:
        return Response(
            {'error': '请提供用户名和密码'},
            status=400
        )

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response(
            {'error': '用户名或密码错误'},
            status=401
        )

    if not user.is_active:
        return Response(
            {'error': '账号已被禁用'},
            status=403
        )

    # 创建或获取已有 Token
    import datetime
    from users.models import ApiToken

    today = datetime.date.today()
    token = ApiToken.objects.filter(
        user=user,
        name='BomQueryClient',
        revoked=False,
        expiry__gte=today
    ).first()

    if not token:
        token = ApiToken.objects.create(
            user=user,
            name='BomQueryClient'
        )

    return Response({
        'token': token.key,
        'user': {
            'id': user.pk,
            'username': user.username,
            'email': user.email,
        }
    })


# ── C# 客户端通用接口 ──────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_param_status(request):
    """检查物料是否为参数化产品（有 PartParameterConfig 则为参数化）。

    查询方式（二选一）：
      ?part_id=1          — 按物料 ID 查
      ?ipn=M3x10&name=螺钉 — 按型号(IPN)+名称查（名称可选，缩小范围）
    """
    from parametric_bom.models import PartParameterConfig as PPC
    from part.models import Part

    part_id = request.query_params.get('part_id')
    ipn = request.query_params.get('ipn')
    name = request.query_params.get('name')

    # ── 定位物料 ──────────────────────────────
    if part_id:
        try:
            part_id = int(part_id)
        except (ValueError, TypeError):
            return Response({'error': 'part_id 必须是整数'}, status=400)
        try:
            part = Part.objects.get(pk=part_id)
        except Part.DoesNotExist:
            return Response({'error': f'物料 {part_id} 不存在'}, status=404)
    elif ipn:
        qs = Part.objects.filter(IPN=ipn)
        if name:
            qs = qs.filter(name__icontains=name)
        if qs.count() == 0:
            return Response({'error': f'未找到型号为「{ipn}」的物料'}, status=404)
        if qs.count() > 1:
            return Response({'error': f'型号「{ipn}」匹配到 {qs.count()} 个物料，请缩小名称范围'}, status=400)
        part = qs.first()
    else:
        return Response({'error': '请提供 part_id 或 ipn（型号）'}, status=400)

    count = PPC.objects.filter(part_id=part.pk).count()
    return Response({
        'part_id': part.pk,
        'ipn': part.IPN or '',
        'name': part.name,
        'is_parametric': count > 0,
        'param_count': count,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def bom_subparts(request):
    """Return unique BOM sub-parts (reference parts) for a product.
    Used by the formula editor to load reference part parameters.
    """
    from part.models import BomItem

    part_id = request.query_params.get('part')
    if not part_id:
        return Response({'error': 'part parameter is required'}, status=400)

    items = BomItem.objects.filter(part_id=part_id).select_related('sub_part')
    seen = set()
    result = []
    for item in items:
        if item.sub_part_id not in seen:
            seen.add(item.sub_part_id)
            result.append({
                'id': item.sub_part_id,
                'name': item.sub_part.name,
            })

    return Response(result)


class PartLiteViewSet(viewsets.ReadOnlyModelViewSet):
    """Lightweight part list for dropdown selects — only pk, name, full_name, IPN."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from part.models import Part
        qs = Part.objects.all()
        search = self.request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(IPN__icontains=search) |
                Q(full_name__icontains=search)
            )
        return qs.order_by('-creation_date')[:200]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = [{'pk': p.pk, 'name': p.name, 'full_name': p.full_name, 'IPN': p.IPN}
                for p in qs]
        return Response(data)
