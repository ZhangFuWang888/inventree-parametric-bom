"""REST API views for Parametric BOM models."""

from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
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
    ConfigParameterValue,
    ConfigStatusChoices,
    InheritanceMapping,
    ParametricBomItem,
    ParametricRule,
    PartAttributeFormula,
    PartParameterConfig,
    ProductConfiguration,
    SupplierSelectionRule,
    VariantMapping,
)
from parametric_bom.serializers import (
    BomCandidatePartSerializer,
    BomSpecificationSerializer,
    ConfigParameterValueSerializer,
    InheritanceMappingSerializer,
    ParametricBomItemSerializer,
    ParametricRuleSerializer,
    PartAttributeFormulaSerializer,
    PartParameterConfigSerializer,
    ProductConfigurationSerializer,
    SupplierSelectionRuleSerializer,
    VariantMappingSerializer,
)


class PartParameterConfigViewSet(viewsets.ModelViewSet):
    """API endpoint for PartParameterConfig."""
    queryset = PartParameterConfig.objects.select_related(
        'part', 'template'
    ).all()
    serializer_class = PartParameterConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['part', 'template', 'is_driving', 'is_computed']
    search_fields = ['part__name', 'template__name', 'ui_hint']


class ParametricBomItemViewSet(viewsets.ModelViewSet):
    """API endpoint for ParametricBomItem."""
    queryset = ParametricBomItem.objects.select_related(
        'bom_item__part', 'bom_item__sub_part'
    ).all()
    serializer_class = ParametricBomItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['bom_item', 'mode']
    search_fields = ['bom_item__part__name', 'qty_formula']


class ParametricRuleViewSet(viewsets.ModelViewSet):
    """API endpoint for ParametricRule."""
    queryset = ParametricRule.objects.select_related(
        'product_part', 'target_param'
    ).all()
    serializer_class = ParametricRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
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
    filterset_fields = ['template_part', 'status', 'revision']
    search_fields = ['title', 'notes']


class ConfigParameterValueViewSet(viewsets.ModelViewSet):
    """API endpoint for ConfigParameterValue."""
    queryset = ConfigParameterValue.objects.select_related(
        'config', 'template'
    ).all()
    serializer_class = ConfigParameterValueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['config', 'template', 'source']


# ── New Model ViewSets ─────────────────────

class BomCandidatePartViewSet(viewsets.ModelViewSet):
    """API endpoint for BomCandidatePart."""
    queryset = BomCandidatePart.objects.select_related(
        'parametric_bom_item', 'part'
    ).all()
    serializer_class = BomCandidatePartSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['parametric_bom_item', 'part']
    search_fields = ['label', 'part__name']


class VariantMappingViewSet(viewsets.ModelViewSet):
    """API endpoint for VariantMapping."""
    queryset = VariantMapping.objects.select_related(
        'parametric_bom_item', 'template_part'
    ).all()
    serializer_class = VariantMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['parametric_bom_item', 'template_part']


class BomSpecificationViewSet(viewsets.ModelViewSet):
    """API endpoint for BomSpecification."""
    queryset = BomSpecification.objects.select_related(
        'parametric_bom_item'
    ).all()
    serializer_class = BomSpecificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['parametric_bom_item', 'spec_type']


class SupplierSelectionRuleViewSet(viewsets.ModelViewSet):
    """API endpoint for SupplierSelectionRule."""
    queryset = SupplierSelectionRule.objects.select_related(
        'parametric_bom_item', 'supplier_part'
    ).all()
    serializer_class = SupplierSelectionRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['parametric_bom_item', 'supplier_part']


class InheritanceMappingViewSet(viewsets.ModelViewSet):
    """API endpoint for InheritanceMapping."""
    queryset = InheritanceMapping.objects.select_related(
        'target_part', 'target_template', 'source_template'
    ).all()
    serializer_class = InheritanceMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['target_part', 'target_template', 'enabled']


class PartAttributeFormulaViewSet(viewsets.ModelViewSet):
    """API endpoint for PartAttributeFormula."""
    queryset = PartAttributeFormula.objects.select_related('part').all()
    serializer_class = PartAttributeFormulaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['part', 'attribute_type']
    search_fields = ['attribute_name']


# ── Existing Function Endpoints ─────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bom_evaluate(request):
    """Evaluate a parametric BOM — expand BOM tree with formula computation."""
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
            return Response(result)
        elif part_id:
            from part.models import Part
            part = Part.objects.get(pk=part_id)
            user_params = request.data.get('parameters', {})
            result = evaluate_part(part, user_params, timeout_ms, max_depth)
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
        return Response(
            {'error': f'Evaluation failed: {exc}'},
            status=500,
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def formula_validate(request):
    """Validate a formula string."""
    formula = request.data.get('formula', '')
    result = validate_formula(formula)
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
            user_params = request.data.get('parameters', {})
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
    """Preview/evaluate a formula with sample parameter values."""
    formula = request.data.get('formula', '')
    context = request.data.get('context', {})
    timeout_ms = request.data.get('timeout_ms', 500)

    if not formula.strip():
        return Response({'success': False, 'error': 'Formula is empty'})

    try:
        result = evaluate(formula, context, timeout_ms=timeout_ms)
        return Response({'success': True, 'result': result})
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
            user_params = request.data.get('parameters', {})
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
            user_params = request.data.get('parameters', {})
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


import structlog
logger = structlog.get_logger('inventree')
