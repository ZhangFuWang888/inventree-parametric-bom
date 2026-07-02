"""REST API views for Parametric BOM models."""

from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
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
    ConfigParameterValue,
    ConfigStatusChoices,
    InheritanceMapping,
    ParametricBomItem,
    ParametricRule,
    PartAttributeFormula,
    PartParameterConfig,
    PartVariable,
    ProductConfiguration,
    VariantMapping,
)
from InvenTree.filters import SEARCH_ORDER_FILTER

from django.conf import settings
from django.http import StreamingHttpResponse, FileResponse
from django.contrib.contenttypes.models import ContentType

from parametric_bom.serializers import (
    BomCandidatePartSerializer,
    BomSpecificationSerializer,
    ConfigParameterValueSerializer,
    InheritanceMappingSerializer,
    ParametricBomItemSerializer,
    ParametricRuleSerializer,
    PartAttributeFormulaSerializer,
    PartParameterConfigSerializer,
    PartVariableSerializer,
    ProductConfigurationSerializer,
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


# ── Export: BOM XLSX ─────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_bom_csv(request):
    """Export evaluated BOM tree as XLSX download."""
    import openpyxl, io
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    from parametric_bom.bom_expander import evaluate_configuration, evaluate_part
    from parametric_bom.models import ProductConfiguration

    config_id = request.query_params.get('config_id')
    part_id = request.query_params.get('part_id')

    try:
        if config_id:
            config = ProductConfiguration.objects.get(pk=config_id)
            result = evaluate_configuration(config)
        elif part_id:
            from part.models import Part
            part = Part.objects.get(pk=part_id)
            user_params = {}
            if request.query_params.get('parameters'):
                import json
                user_params = json.loads(request.query_params['parameters'])
            result = evaluate_part(part, user_params)
        else:
            return Response({'error': 'Provide config_id or part_id'}, status=400)
    except Exception as exc:
        logger.exception('BOM export failed')
        return Response({'error': str(exc)}, status=500)

    bom_tree = result.get('bom_tree', {})
    part_name = result.get('part_name', 'BOM')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'BOM清单'

    # Styles
    header_font = Font(name='微软雅黑', bold=True, size=10, color='FFFFFF')
    header_fill = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
    header_align = Alignment(horizontal='center', vertical='center')
    cell_font = Font(name='微软雅黑', size=9)
    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB'),
    )

    headers = ['层级', '物料编码', '物料名称', '数量', '类型', '变体名称', '变体编码', '备注']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    def flatten(node, row_num=2, parent_qty=1.0):
        row = row_num
        children = node.get('children', [])
        for child in children:
            if child.get('excluded'):
                continue
            depth = child.get('depth', 0)
            pid = child.get('actual_part_id', child.get('part_id', ''))
            pname = child.get('actual_part_name', child.get('part_name', ''))
            qty = child.get('calculated_quantity', 1) * parent_qty
            ref = child.get('reference', '')
            mode = child.get('mode', 'static')
            vname = child.get('variant_name', '')
            vipn = child.get('variant_ipn', '')

            vals = [depth, pid, pname, qty, mode, vname, vipn, ref]
            for col, v in enumerate(vals, 1):
                cell = ws.cell(row=row, column=col, value=v)
                cell.font = cell_font
                cell.border = thin_border
                if col == 1:
                    cell.alignment = Alignment(horizontal='center')
                elif col == 4:
                    cell.number_format = '#,##0.00'
                    cell.alignment = Alignment(horizontal='right')
            row += 1
            row = flatten(child, row, qty)
        return row

    flatten(bom_tree)

    # Auto-width
    col_widths = [6, 14, 24, 10, 10, 16, 16, 20]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

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

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_attachment_zip(request):
    """Pack all attachments of BOM sub-parts into a ZIP download."""
    import zipfile, io, os

    from parametric_bom.bom_expander import evaluate_configuration, evaluate_part, _flatten_bom
    from parametric_bom.models import ProductConfiguration

    config_id = request.query_params.get('config_id')
    part_id = request.query_params.get('part_id')

    try:
        if config_id:
            config = ProductConfiguration.objects.get(pk=config_id)
            result = evaluate_configuration(config)
        elif part_id:
            from part.models import Part
            part = Part.objects.get(pk=part_id)
            user_params = {}
            if request.query_params.get('parameters'):
                import json
                user_params = json.loads(request.query_params['parameters'])
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


import structlog
logger = structlog.get_logger('inventree')
