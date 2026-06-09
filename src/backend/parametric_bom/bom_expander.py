"""BOM Expansion Service — Dynamic BOM tree generation.

Takes a ProductConfiguration (or Part + parameter values) and recursively
expands the BOM tree, evaluating formulas for quantities, conditions,
and part selection at each level.

Supports all 12 parametric scenarios including candidate selection,
variant generation, specification output, supplier selection,
attribute formulas, and parameter inheritance.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.utils import timezone

import structlog

from parametric_bom.formula_engine import evaluate as eval_formula
from parametric_bom.formula_engine.errors import (
    EvaluationError,
    ParseError,
    ReferenceError,
    TimeoutError,
)

logger = structlog.get_logger('inventree')

# ──────────────────────────────────────────────
#  Type Aliases
# ──────────────────────────────────────────────

ParamMap = Dict[str, Any]
BomTreeNode = Dict[str, Any]


# ──────────────────────────────────────────────
#  Helper utilities
# ──────────────────────────────────────────────


def _part_display(part) -> str:
    """Get a display string for a Part instance."""
    return getattr(part, 'full_name', None) or getattr(part, 'name', str(part))


def _part_pk(part) -> int:
    """Get the PK of a Part instance."""
    return getattr(part, 'pk', None) or getattr(part, 'id', 0)


def _coerce_value(val: str) -> Any:
    """Coerce a string value to numeric if possible."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        pass
    try:
        return float(val)
    except (ValueError, TypeError):
        pass
    if isinstance(val, str) and val.lower() in ('true', 'false'):
        return val.lower() == 'true'
    return val


# ──────────────────────────────────────────────
#  Core: Compute derived parameters + attributes
# ──────────────────────────────────────────────


def compute_parameters(
    part,
    user_params: ParamMap,
    parent_params: Optional[ParamMap] = None,
    timeout_ms: int = 500,
) -> Tuple[ParamMap, List[str]]:
    """Compute all parameters for a part: merge user params with computed.

    Also evaluates PartAttributeFormula records and includes the results
    in the returned params dict under a special 'attributes' key.

    Args:
        part: A Part model instance (the assembly).
        user_params: User-provided driving parameters {name: value}.
        parent_params: Parent-level parameters for inheritance.
        timeout_ms: Formula evaluation timeout.

    Returns:
        (all_params, errors) where all_params includes both user params and
        computed params, and errors lists any computation errors.
    """
    from parametric_bom.models import PartParameterConfig

    all_params: ParamMap = dict(user_params)
    errors: List[str] = []

    # Build context: own params + parent params
    formula_context = {'param': all_params}
    if parent_params:
        formula_context['parent'] = parent_params

    # ── 1) Compute formulas for PartParameterConfig ─────────────
    configs = PartParameterConfig.objects.filter(
        part=part,
    ).select_related('template').order_by('display_order')

    for cfg in configs:
        param_name = cfg.template.name
        if param_name in user_params:
            continue
        if cfg.is_computed and cfg.computation_formula:
            try:
                result = eval_formula(
                    cfg.computation_formula,
                    context=formula_context,
                    timeout_ms=timeout_ms,
                )
                all_params[param_name] = result
            except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
                errors.append(f"{param_name}: {e}")
                all_params[param_name] = cfg.default_value or None
        else:
            if cfg.default_value:
                all_params[param_name] = cfg.default_value

    # ── 2) Apply InheritanceMapping ────────────────────────────
    if parent_params:
        _apply_inheritance(part, all_params, parent_params, timeout_ms, errors)

    # ── 3) Compute PartAttributeFormula ─────────────────────────
    _compute_attributes(part, all_params, parent_params, timeout_ms, errors)

    return all_params, errors


def _apply_inheritance(
    part,
    all_params: ParamMap,
    parent_params: ParamMap,
    timeout_ms: int,
    errors: List[str],
) -> None:
    """Apply InheritanceMapping records to inherit params from parent."""
    from parametric_bom.models import InheritanceMapping

    mappings = InheritanceMapping.objects.filter(
        target_part=part,
        enabled=True,
    ).select_related('target_template', 'source_template')

    for mapping in mappings:
        param_name = mapping.target_template.name
        if param_name in all_params:
            continue  # Don't override user or computed params

        if mapping.formula:
            # Evaluate transformation formula
            try:
                result = eval_formula(
                    mapping.formula,
                    context={'param': all_params, 'parent': parent_params},
                    timeout_ms=timeout_ms,
                )
                all_params[param_name] = result
            except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
                errors.append(f"Inheritance {param_name}: {e}")
        elif mapping.source_template:
            # Direct pass-through from source
            src_name = mapping.source_template.name
            if src_name in parent_params:
                all_params[param_name] = parent_params[src_name]
        else:
            # Auto: same name from parent
            if param_name in parent_params:
                all_params[param_name] = parent_params[param_name]


def _compute_attributes(
    part,
    all_params: ParamMap,
    parent_params: Optional[ParamMap],
    timeout_ms: int,
    errors: List[str],
) -> None:
    """Evaluate PartAttributeFormula records and attach to params."""
    from parametric_bom.models import PartAttributeFormula

    attrs = PartAttributeFormula.objects.filter(
        part=part,
    ).order_by('display_order')

    if not attrs:
        return

    formula_context = {'param': all_params}
    if parent_params:
        formula_context['parent'] = parent_params

    computed_attrs = {}
    for attr in attrs:
        try:
            result = eval_formula(
                attr.formula,
                context=formula_context,
                timeout_ms=timeout_ms,
            )
            computed_attrs[attr.attribute_name] = {
                'value': result,
                'type': attr.attribute_type,
                'unit': attr.unit,
            }
        except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
            errors.append(f"Attribute {attr.attribute_name}: {e}")
            computed_attrs[attr.attribute_name] = {
                'value': None,
                'error': str(e),
                'unit': attr.unit,
            }

    if computed_attrs:
        all_params['_attributes'] = computed_attrs


# ──────────────────────────────────────────────
#  Core: Expand a single BOM level
# ──────────────────────────────────────────────


def expand_bom_level(
    part,
    params: ParamMap,
    parent_params: Optional[ParamMap] = None,
    depth: int = 0,
    max_depth: int = 10,
    timeout_ms: int = 500,
) -> BomTreeNode:
    """Recursively expand one level of a parametric BOM.

    Args:
        part: A Part model instance.
        params: Computed parameter values for this level.
        parent_params: Parent-level parameters for inheritance context.
        depth: Current recursion depth (starts at 0).
        max_depth: Maximum recursion depth to prevent infinite loops.
        timeout_ms: Formula evaluation timeout.

    Returns:
        A BomTreeNode dict with the expanded BOM tree.
    """
    node: BomTreeNode = {
        'part_id': _part_pk(part),
        'part_name': _part_display(part),
        'depth': depth,
        'quantity': 1,
        'calculated_quantity': 1,
        'children': [],
        'errors': [],
        'excluded': False,
        'exclude_reason': None,
    }

    if depth >= max_depth:
        node['errors'].append(f'Max recursion depth ({max_depth}) reached')
        return node

    # Attach computed attributes to node
    if '_attributes' in params:
        node['attributes'] = params.pop('_attributes')

    try:
        bom_items = part.bom_items.all().select_related('sub_part')
    except Exception:
        return node

    for bom_item in bom_items:
        child_node = _expand_single_bom_item(
            bom_item, params, parent_params, depth, max_depth, timeout_ms,
        )
        if child_node is not None:
            node['children'].append(child_node)

    return node


# ──────────────────────────────────────────────
#  Expand a single BomItem — mode-aware
# ──────────────────────────────────────────────


def _expand_single_bom_item(
    bom_item,
    params: ParamMap,
    parent_params: Optional[ParamMap] = None,
    depth: int = 0,
    max_depth: int = 10,
    timeout_ms: int = 500,
) -> Optional[BomTreeNode]:
    """Expand a single BomItem, evaluating its parametric formulas.

    Handles all 8 modes defined in BomItemModeChoices:
    - standard: Static item, no formulas
    - qty_formula: Dynamic quantity only
    - conditional: Quantity + condition formula
    - candidate: Select from BomCandidatePart list
    - variant: Generate variant from template (VariantMapping)
    - specification: Outsource by spec (BomSpecification)
    - supplier: Select supplier (SupplierSelectionRule)
    - structure: Structural sub-assembly control

    Returns None if the item is excluded by condition formula.
    """
    from parametric_bom.models import ParametricBomItem

    sub_part = bom_item.sub_part
    child_node: BomTreeNode = {
        'part_id': _part_pk(sub_part),
        'part_name': _part_display(sub_part),
        'depth': depth + 1,
        'quantity': float(bom_item.quantity),
        'calculated_quantity': float(bom_item.quantity),
        'children': [],
        'errors': [],
        'excluded': False,
        'exclude_reason': None,
        'bom_item_id': bom_item.pk,
        'optional': bom_item.optional,
        'consumable': bom_item.consumable,
        'reference': bom_item.reference or '',
    }

    try:
        parametric_cfg = ParametricBomItem.objects.get(bom_item=bom_item)
    except ParametricBomItem.DoesNotExist:
        child_node['parametric'] = False
        _expand_sub_part(child_node, sub_part, params, parent_params, depth, max_depth, timeout_ms)
        return child_node

    child_node['parametric'] = True
    child_node['mode'] = parametric_cfg.mode
    child_node['formulas'] = {
        'qty': parametric_cfg.qty_formula or None,
        'condition': parametric_cfg.condition_formula or None,
    }

    # ── 0) Condition evaluation (all modes except standard) ──
    if parametric_cfg.condition_formula:
        try:
            condition_result = eval_formula(
                parametric_cfg.condition_formula,
                context=_ctx(params, parent_params),
                timeout_ms=timeout_ms,
            )
            if not condition_result:
                child_node['excluded'] = True
                child_node['exclude_reason'] = (
                    f"Condition not met: {parametric_cfg.condition_formula}"
                )
                return child_node
        except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
            child_node['errors'].append(f"Condition formula error: {e}")
            child_node['condition_error'] = str(e)

    # ── 1) Quantity formula ──────────────────────────────────────
    if parametric_cfg.qty_formula:
        try:
            qty_result = eval_formula(
                parametric_cfg.qty_formula,
                context=_ctx(params, parent_params),
                timeout_ms=timeout_ms,
            )
            child_node['calculated_quantity'] = float(qty_result)
        except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
            child_node['errors'].append(f"Quantity formula error: {e}")

    # ── 2) Mode-specific sub-part resolution ──────────────────────
    actual_sub_part = sub_part

    if parametric_cfg.mode == 'candidate':
        actual_sub_part = _resolve_candidate(
            child_node, parametric_cfg, params, parent_params, timeout_ms,
        ) or sub_part

    elif parametric_cfg.mode == 'variant':
        actual_sub_part = _resolve_variant(
            child_node, parametric_cfg, params, parent_params, timeout_ms,
        ) or sub_part

    elif parametric_cfg.mode == 'specification':
        _resolve_specification(
            child_node, parametric_cfg, params, parent_params, timeout_ms,
        )
        # Spec items don't recurse into sub-parts — the spec IS the part
        return child_node

    elif parametric_cfg.mode == 'supplier':
        _resolve_supplier(
            child_node, parametric_cfg, params, parent_params, timeout_ms,
        )

    elif parametric_cfg.mode == 'structure':
        # Structure mode: the condition formula already controls inclusion.
        # Sub-assembly content follows normal recursion.
        pass

    # ── 3) Record actual sub-part info ────────────────────────────
    child_node['actual_part_id'] = _part_pk(actual_sub_part)
    child_node['actual_part_name'] = _part_display(actual_sub_part)

    # ── 4) Recurse into sub-part's BOM ────────────────────────────
    _expand_sub_part(child_node, actual_sub_part, params, parent_params, depth, max_depth, timeout_ms)

    return child_node


# ──────────────────────────────────────────────
#  Mode-specific resolvers
# ──────────────────────────────────────────────


def _ctx(params: ParamMap, parent_params: Optional[ParamMap] = None) -> dict:
    """Build formula context dict."""
    ctx: dict = {'param': params}
    if parent_params:
        ctx['parent'] = parent_params
    return ctx


def _resolve_candidate(
    node: BomTreeNode,
    cfg,
    params: ParamMap,
    parent_params: Optional[ParamMap],
    timeout_ms: int,
):
    """Resolve sub-part from BomCandidatePart list.

    Evaluates each candidate's condition in priority order.
    Returns the selected Part or None.
    """
    from parametric_bom.models import BomCandidatePart

    candidates = BomCandidatePart.objects.filter(
        parametric_bom_item=cfg,
    ).select_related('part').order_by('priority')

    if not candidates:
        node['errors'].append('No candidate parts configured')
        return None

    candidates_considered = []
    selected = None

    for candidate in candidates:
        match = False
        condition_error = None
        if candidate.condition_formula:
            try:
                result = eval_formula(
                    candidate.condition_formula,
                    context=_ctx(params, parent_params),
                    timeout_ms=timeout_ms,
                )
                match = bool(result)
            except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
                condition_error = str(e)
                match = False
        else:
            match = True  # Empty condition = always available

        candidates_considered.append({
            'part_id': candidate.part_id,
            'part_name': candidate.part.name,
            'label': candidate.label or '',
            'condition': candidate.condition_formula or '',
            'matched': match,
            'error': condition_error,
        })

        if match and selected is None:
            selected = candidate.part

    node['candidates_considered'] = candidates_considered
    if selected:
        node['selected_candidate_part_id'] = _part_pk(selected)
        node['selected_candidate_part_name'] = _part_display(selected)
    else:
        node['errors'].append('No candidate part matched conditions')

    return selected


def _resolve_variant(
    node: BomTreeNode,
    cfg,
    params: ParamMap,
    parent_params: Optional[ParamMap],
    timeout_ms: int,
):
    """Resolve sub-part via VariantMapping.

    Computes parameter mapping, looks up existing variant by name,
    or creates a new variant Part if none exists.
    """
    from parametric_bom.models import VariantMapping

    try:
        vm = VariantMapping.objects.get(parametric_bom_item=cfg)
    except VariantMapping.DoesNotExist:
        node['errors'].append('No variant mapping configured')
        return None

    template_part = vm.template_part
    node['template_part_id'] = _part_pk(template_part)
    node['template_part_name'] = _part_display(template_part)

    # Evaluate param_mapping
    computed_params: ParamMap = {}
    mapping_errors: List[str] = []
    for param_name, formula in (vm.param_mapping or {}).items():
        try:
            result = eval_formula(
                formula,
                context=_ctx(params, parent_params),
                timeout_ms=timeout_ms,
            )
            computed_params[param_name] = result
        except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
            mapping_errors.append(f"{param_name}: {e}")

    node['variant_computed_params'] = computed_params
    if mapping_errors:
        node['errors'].extend([f"Variant param {e}" for e in mapping_errors])

    if mapping_errors:
        return template_part  # Fall back to template on error

    # Build variant name
    if vm.variant_name_template:
        variant_name = vm.variant_name_template
        for k, v in computed_params.items():
            variant_name = variant_name.replace(f'{{{k}}}', str(v) if v is not None else '')
    else:
        param_parts = [f"{k}={v}" for k, v in computed_params.items()]
        variant_name = f"{_part_display(template_part)} ({', '.join(param_parts)})"

    node['variant_computed_name'] = variant_name

    # Look for existing variant by name
    from part.models import Part

    try:
        existing = Part.objects.filter(
            variant_of=template_part,
            name=variant_name,
        ).first()
        if existing:
            node['variant_existing'] = True
            node['variant_part_id'] = _part_pk(existing)
            node['variant_part_name'] = _part_display(existing)
            return existing
    except Exception:
        pass

    # Auto-generate new variant
    if vm.auto_generate:
        try:
            new_part = _create_variant_part(template_part, variant_name, computed_params)
            node['variant_generated'] = True
            node['variant_part_id'] = _part_pk(new_part)
            node['variant_part_name'] = _part_display(new_part)
            return new_part
        except Exception as e:
            node['errors'].append(f"Failed to create variant: {e}")
            return template_part

    # Auto-generate disabled — use template as-is
    node['variant_auto_disabled'] = True
    return template_part


def _create_variant_part(template_part, variant_name: str, params: ParamMap):
    """Create a new variant Part from a template with computed params."""
    from django.db import transaction
    from part.models import Part
    from common.models import Parameter
    from django.contrib.contenttypes.models import ContentType

    with transaction.atomic():
        variant = Part.objects.create(
            name=variant_name,
            description=f"Auto-generated variant of {_part_display(template_part)}",
            IPN=f"VAR-{template_part.pk}-{variant_name[:16]}",
            variant_of=template_part,
            category=template_part.category,
            is_template=False,
            assembly=template_part.assembly,
            component=template_part.component,
            active=True,
            virtual=False,
        )

        # Copy parameters
        part_ct = ContentType.objects.get_for_model(Part)
        for param_name, value in params.items():
            # Find template
            from common.models import ParameterTemplate
            tmpl = ParameterTemplate.objects.filter(name=param_name).first()
            if tmpl:
                Parameter.objects.create(
                    content_type=part_ct,
                    object_id=variant.pk,
                    template=tmpl,
                    data=str(value) if value is not None else '',
                )

        logger.info(
            "variant_part_auto_created",
            variant_part_id=variant.pk,
            variant_name=variant_name,
            template_part_id=_part_pk(template_part),
        )

        return variant


def _resolve_specification(
    node: BomTreeNode,
    cfg,
    params: ParamMap,
    parent_params: Optional[ParamMap],
    timeout_ms: int,
) -> None:
    """Evaluate BomSpecification and output spec fields to the BOM tree node.

    Spec items are leaf nodes (no sub-part recursion).
    """
    from parametric_bom.models import BomSpecification

    try:
        spec = BomSpecification.objects.get(parametric_bom_item=cfg)
    except BomSpecification.DoesNotExist:
        node['errors'].append('No specification configured')
        return

    node['mode'] = 'specification'
    node['spec_type'] = spec.spec_type

    # Evaluate spec fields
    evaluated_fields = []
    for field in (spec.spec_fields or []):
        name = field.get('name', '')
        formula = field.get('formula', '')
        unit = field.get('unit', '')

        if formula:
            try:
                value = eval_formula(
                    formula,
                    context=_ctx(params, parent_params),
                    timeout_ms=timeout_ms,
                )
            except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
                value = f"<error: {e}>"
                node['errors'].append(f"Spec field '{name}': {e}")
        else:
            value = ''

        evaluated_fields.append({
            'name': name,
            'value': value,
            'unit': unit,
        })

    node['spec_fields_evaluated'] = evaluated_fields

    # Evaluate drawing reference
    if spec.drawing_ref_formula:
        try:
            node['drawing_ref'] = eval_formula(
                spec.drawing_ref_formula,
                context=_ctx(params, parent_params),
                timeout_ms=timeout_ms,
            )
        except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
            node['errors'].append(f"Drawing ref: {e}")

    # Evaluate unit cost
    if spec.unit_cost_formula:
        try:
            node['unit_cost'] = eval_formula(
                spec.unit_cost_formula,
                context=_ctx(params, parent_params),
                timeout_ms=timeout_ms,
            )
        except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
            node['errors'].append(f"Unit cost: {e}")

    node['spec_notes'] = spec.notes


def _resolve_supplier(
    node: BomTreeNode,
    cfg,
    params: ParamMap,
    parent_params: Optional[ParamMap],
    timeout_ms: int,
) -> None:
    """Select supplier from SupplierSelectionRule list."""
    from parametric_bom.models import SupplierSelectionRule

    rules = SupplierSelectionRule.objects.filter(
        parametric_bom_item=cfg,
    ).select_related('supplier_part').order_by('priority')

    if not rules:
        node['errors'].append('No supplier rules configured')
        return

    rules_considered = []
    selected = None

    for rule in rules:
        match = False
        error = None
        if rule.condition_formula:
            try:
                result = eval_formula(
                    rule.condition_formula,
                    context=_ctx(params, parent_params),
                    timeout_ms=timeout_ms,
                )
                match = bool(result)
            except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
                error = str(e)
                match = False
        else:
            match = True

        rules_considered.append({
            'supplier_part_id': rule.supplier_part_id,
            'supplier_label': rule.label or '',
            'condition': rule.condition_formula or '',
            'matched': match,
            'error': error,
        })

        if match and selected is None:
            selected = rule.supplier_part

    node['supplier_rules_considered'] = rules_considered
    if selected:
        node['selected_supplier_part_id'] = _part_pk(selected)
        node['selected_supplier_name'] = str(selected)
    else:
        node['errors'].append('No supplier rule matched')


# ──────────────────────────────────────────────
#  Sub-part recursion
# ──────────────────────────────────────────────


def _expand_sub_part(
    child_node: BomTreeNode,
    sub_part,
    params: ParamMap,
    parent_params: Optional[ParamMap],
    depth: int,
    max_depth: int,
    timeout_ms: int,
) -> None:
    """Recursively expand sub-part's BOM.

    Passes current params as parent context for inheritance.
    """
    from parametric_bom.models import PartParameterConfig

    has_configs = PartParameterConfig.objects.filter(part=sub_part).exists()
    if has_configs:
        # Pass current params as parent context
        sub_params, sub_errors = compute_parameters(
            sub_part, {}, parent_params=params, timeout_ms=timeout_ms,
        )
        if sub_errors:
            child_node['errors'].extend([f"Sub-param {e}" for e in sub_errors])
        sub_tree = expand_bom_level(
            sub_part, sub_params, parent_params=params,
            depth=depth + 1, max_depth=max_depth, timeout_ms=timeout_ms,
        )
        child_node['children'] = sub_tree.get('children', [])
        child_node['sub_params'] = sub_params
    else:
        try:
            sub_bom_items = sub_part.bom_items.all().select_related('sub_part')
            if sub_bom_items.exists():
                for sub_bom in sub_bom_items:
                    grandchild = _expand_single_bom_item(
                        sub_bom, params, parent_params,
                        depth + 1, max_depth, timeout_ms,
                    )
                    if grandchild is not None:
                        child_node['children'].append(grandchild)
        except Exception:
            pass


# ──────────────────────────────────────────────
#  Main entry: Evaluate configuration
# ──────────────────────────────────────────────


def evaluate_configuration(
    config,
    timeout_ms: int = 500,
    max_depth: int = 10,
) -> Dict[str, Any]:
    """Full evaluation of a ProductConfiguration.

    Args:
        config: A ProductConfiguration instance.
        timeout_ms: Formula evaluation timeout.
        max_depth: Max BOM recursion depth.

    Returns:
        Dict with config_id, title, status, part info, parameters,
        computed attributes, bom_tree, total_cost, expanded_at.
    """
    from parametric_bom.models import ConfigParameterValue

    template_part = config.template_part

    user_params: ParamMap = {}
    param_values = ConfigParameterValue.objects.filter(
        config=config,
        source='manual',
    ).select_related('template')

    for pv in param_values:
        user_params[pv.template.name] = _coerce_value(pv.value)

    all_params, param_errors = compute_parameters(
        template_part, user_params, timeout_ms=timeout_ms,
    )

    other_values = ConfigParameterValue.objects.filter(
        config=config,
    ).exclude(source='manual').select_related('template')
    for pv in other_values:
        if pv.template.name not in all_params:
            all_params[pv.template.name] = _coerce_value(pv.value)

    bom_tree = expand_bom_level(
        template_part, all_params,
        depth=0, max_depth=max_depth, timeout_ms=timeout_ms,
    )

    total_quantity = _compute_total_quantity(bom_tree)

    # Extract computed attributes from root node
    attributes = bom_tree.pop('attributes', {})

    result: Dict[str, Any] = {
        'config_id': config.pk,
        'title': config.title,
        'status': config.status,
        'part_id': _part_pk(template_part),
        'part_name': _part_display(template_part),
        'parameters': all_params,
        'parameter_errors': param_errors,
        'bom_tree': bom_tree,
        'total_bom_items': total_quantity,
        'attributes': attributes,
        'expanded_at': timezone.now().isoformat(),
    }

    if config.total_cost:
        result['total_cost'] = float(config.total_cost)

    return result


def evaluate_part(
    part,
    user_params: ParamMap,
    timeout_ms: int = 500,
    max_depth: int = 10,
) -> Dict[str, Any]:
    """Evaluate a parametric Part with given user parameters (quick preview).

    Args:
        part: A Part model instance.
        user_params: User-provided driving parameters.
        timeout_ms: Formula evaluation timeout.
        max_depth: Max BOM recursion depth.

    Returns:
        Same structure as evaluate_configuration.
    """
    all_params, param_errors = compute_parameters(
        part, user_params, timeout_ms=timeout_ms,
    )

    bom_tree = expand_bom_level(
        part, all_params,
        depth=0, max_depth=max_depth, timeout_ms=timeout_ms,
    )

    total_quantity = _compute_total_quantity(bom_tree)
    attributes = bom_tree.pop('attributes', {})

    return {
        'part_id': _part_pk(part),
        'part_name': _part_display(part),
        'parameters': all_params,
        'parameter_errors': param_errors,
        'bom_tree': bom_tree,
        'total_bom_items': total_quantity,
        'attributes': attributes,
        'expanded_at': timezone.now().isoformat(),
    }


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────


def _compute_total_quantity(node: BomTreeNode) -> int:
    """Count total BOM items (leaf parts) in the tree."""
    count = 0
    for child in node.get('children', []):
        if child.get('excluded'):
            continue
        count += 1
        count += _compute_total_quantity(child)
    return count


def compute_bom_hash(bom_tree: BomTreeNode) -> str:
    """Compute a deterministic hash of the BOM tree for change detection."""
    raw = str(sorted(_flatten_bom(bom_tree)))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _flatten_bom(node: BomTreeNode) -> List[Tuple[int, float]]:
    """Flatten BOM tree to (part_id, quantity) pairs."""
    result: List[Tuple[int, float]] = []
    for child in node.get('children', []):
        if child.get('excluded'):
            continue
        pid = child.get('actual_part_id') or child.get('part_id', 0)
        qty = child.get('calculated_quantity', 1)
        result.append((pid, qty))
        result.extend(_flatten_bom(child))
    return result
