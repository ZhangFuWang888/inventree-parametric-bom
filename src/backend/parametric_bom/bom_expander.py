"""BOM Expansion Service — Dynamic BOM tree generation.

Takes a ProductConfiguration (or Part + parameter values) and recursively
expands the BOM tree, evaluating formulas for quantities, conditions,
and part selection at each level.

Phase 3 — Dynamic BOM Generation.
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

# A flat dict of param_name → value for a single level
ParamMap = Dict[str, Any]

# An expanded BOM tree node
BomTreeNode = Dict[str, Any]


# ──────────────────────────────────────────────
#  Helper: resolve part name for display
# ──────────────────────────────────────────────


def _part_display(part) -> str:
    """Get a display string for a Part instance."""
    return getattr(part, 'full_name', None) or getattr(part, 'name', str(part))


def _part_pk(part) -> int:
    """Get the PK of a Part instance."""
    return getattr(part, 'pk', None) or getattr(part, 'id', 0)


# ──────────────────────────────────────────────
#  Core: Compute derived parameters
# ──────────────────────────────────────────────


def compute_parameters(
    part,
    user_params: ParamMap,
    timeout_ms: int = 500,
) -> Tuple[ParamMap, List[str]]:
    """Compute all parameters for a part: merge user params with computed.

    Args:
        part: A Part model instance (the assembly).
        user_params: User-provided driving parameters {name: value}.
        timeout_ms: Formula evaluation timeout.

    Returns:
        (all_params, errors) where all_params includes both user params and
        computed params, and errors lists any computation errors.
    """
    from parametric_bom.models import PartParameterConfig

    all_params: ParamMap = dict(user_params)
    errors: List[str] = []

    # Fetch all parameter configs for this part, ordered by display_order
    configs = PartParameterConfig.objects.filter(
        part=part,
    ).select_related('template').order_by('display_order')

    for cfg in configs:
        param_name = cfg.template.name

        # 1) If user already provided a driving param, use it as-is
        if param_name in user_params:
            continue

        # 2) If the param has a computation formula → evaluate it
        if cfg.is_computed and cfg.computation_formula:
            try:
                result = eval_formula(
                    cfg.computation_formula,
                    context={'param': all_params},
                    timeout_ms=timeout_ms,
                )
                all_params[param_name] = result
            except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
                errors.append(f"{param_name}: {e}")
                all_params[param_name] = cfg.default_value or None

        # 3) Fall back to default value
        else:
            if cfg.default_value:
                all_params[param_name] = cfg.default_value

    return all_params, errors


# ──────────────────────────────────────────────
#  Core: Expand a single BOM level
# ──────────────────────────────────────────────


def expand_bom_level(
    part,
    params: ParamMap,
    depth: int = 0,
    max_depth: int = 10,
    timeout_ms: int = 500,
) -> BomTreeNode:
    """Recursively expand one level of a parametric BOM.

    Args:
        part: A Part model instance.
        params: Computed parameter values for this level.
        depth: Current recursion depth (starts at 0).
        max_depth: Maximum recursion depth to prevent infinite loops.
        timeout_ms: Formula evaluation timeout.

    Returns:
        A BomTreeNode dict with the expanded BOM tree.
    """
    from parametric_bom.models import ParametricBomItem

    node: BomTreeNode = {
        'part_id': _part_pk(part),
        'part_name': _part_display(part),
        'depth': depth,
        'quantity': 1,  # Overridden by parent
        'calculated_quantity': 1,
        'children': [],
        'errors': [],
        'excluded': False,
        'exclude_reason': None,
    }

    if depth >= max_depth:
        node['errors'].append(f'Max recursion depth ({max_depth}) reached')
        return node

    # Fetch all BOM items for this part
    try:
        bom_items = part.bom_items.all().select_related('sub_part')
    except Exception:
        # Part may not have a bom_items relation
        return node

    for bom_item in bom_items:
        child_node = _expand_single_bom_item(
            bom_item, params, depth, max_depth, timeout_ms,
        )
        if child_node is not None:
            node['children'].append(child_node)

    return node


def _expand_single_bom_item(
    bom_item,
    params: ParamMap,
    depth: int,
    max_depth: int,
    timeout_ms: int,
) -> Optional[BomTreeNode]:
    """Expand a single BomItem, evaluating its parametric formulas.

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

    # Try to get parametric config for this BomItem
    try:
        parametric_cfg = ParametricBomItem.objects.get(bom_item=bom_item)
    except ParametricBomItem.DoesNotExist:
        parametric_cfg = None

    if parametric_cfg is None:
        # No parametric config → static item, but still recurse if sub-part is parametric
        child_node['parametric'] = False
        _expand_sub_part(child_node, sub_part, params, depth, max_depth, timeout_ms)
        return child_node

    child_node['parametric'] = True
    child_node['formulas'] = {
        'qty': parametric_cfg.qty_formula or None,
        'condition': parametric_cfg.condition_formula or None,
        'part_selector': parametric_cfg.part_selector_formula or None,
    }

    # 1) Evaluate condition formula — skip if false
    if parametric_cfg.condition_formula:
        try:
            condition_result = eval_formula(
                parametric_cfg.condition_formula,
                context={'param': params},
                timeout_ms=timeout_ms,
            )
            if not condition_result:
                child_node['excluded'] = True
                child_node['exclude_reason'] = (
                    f"Condition not met: {parametric_cfg.condition_formula}"
                )
                return child_node
        except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
            child_node['errors'].append(
                f"Condition formula error: {e}"
            )
            # On error, include the item anyway
            child_node['condition_error'] = str(e)

    # 2) Evaluate part selector formula — determine actual sub-part
    actual_sub_part = sub_part
    if parametric_cfg.part_selector_formula:
        try:
            selected = eval_formula(
                parametric_cfg.part_selector_formula,
                context={'param': params},
                timeout_ms=timeout_ms,
            )
            if selected and isinstance(selected, str) and selected != sub_part.name:
                # Try to find the selected part by name within the same category
                selected_part = _resolve_part_selection(sub_part, selected)
                if selected_part:
                    actual_sub_part = selected_part
                    child_node['selected_part'] = _part_display(selected_part)
                    child_node['selected_part_id'] = _part_pk(selected_part)
                else:
                    child_node['errors'].append(
                        f"Part selector: could not find part '{selected}'"
                    )
        except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
            child_node['errors'].append(
                f"Part selector formula error: {e}"
            )

    child_node['actual_part_id'] = _part_pk(actual_sub_part)
    child_node['actual_part_name'] = _part_display(actual_sub_part)

    # 3) Evaluate quantity formula
    if parametric_cfg.qty_formula:
        try:
            qty_result = eval_formula(
                parametric_cfg.qty_formula,
                context={'param': params},
                timeout_ms=timeout_ms,
            )
            child_node['calculated_quantity'] = float(qty_result)
        except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
            child_node['errors'].append(
                f"Quantity formula error: {e}"
            )

    # 4) Recurse into sub-part's BOM
    _expand_sub_part(child_node, actual_sub_part, params, depth, max_depth, timeout_ms)

    return child_node


def _resolve_part_selection(original_part, selected_name: str):
    """Try to find a part matching the selected name.

    Looks for:
    1. A variant of original_part with the matching name
    2. Any part with a matching name in the same category
    """
    from part.models import Part

    # Check variants first
    try:
        for variant in original_part.get_descendants(include_self=False):
            if variant.name == selected_name or variant.full_name == selected_name:
                return variant
    except Exception:
        pass

    # Check same category
    try:
        category = original_part.category
        if category:
            matches = Part.objects.filter(
                category=category,
                name=selected_name,
            )[:1]
            if matches:
                return matches[0]
    except Exception:
        pass

    return None


def _expand_sub_part(
    child_node: BomTreeNode,
    sub_part,
    params: ParamMap,
    depth: int,
    max_depth: int,
    timeout_ms: int,
) -> None:
    """Recursively expand sub-part's BOM if it has parametric configs."""
    from parametric_bom.models import PartParameterConfig

    # Check if sub-part has parametric configs
    has_configs = PartParameterConfig.objects.filter(part=sub_part).exists()
    if has_configs:
        # Compute sub-part's own derived params and expand its BOM
        sub_params, sub_errors = compute_parameters(sub_part, params, timeout_ms)
        if sub_errors:
            child_node['errors'].extend(
                [f"Sub-param {e}" for e in sub_errors]
            )
        sub_tree = expand_bom_level(
            sub_part, sub_params, depth + 1, max_depth, timeout_ms,
        )
        child_node['children'] = sub_tree.get('children', [])
        child_node['sub_params'] = sub_params
    else:
        # Static sub-part — still check if it has its own BOM (non-parametric)
        try:
            sub_bom_items = sub_part.bom_items.all().select_related('sub_part')
            if sub_bom_items.exists():
                for sub_bom in sub_bom_items:
                    grandchild = _expand_single_bom_item(
                        sub_bom, params, depth + 1, max_depth, timeout_ms,
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
        Dict with:
            - config_id, title, status
            - part_id, part_name
            - parameters: computed params dict
            - parameter_errors: list of errors from parameter computation
            - bom_tree: expanded BOM tree
            - total_cost: cost estimate (if available)
            - expanded_at: ISO timestamp
    """
    from parametric_bom.models import ConfigParameterValue

    template_part = config.template_part

    # 1) Collect user-provided (manual) parameter values
    user_params: ParamMap = {}
    param_values = ConfigParameterValue.objects.filter(
        config=config,
        source='manual',
    ).select_related('template')

    for pv in param_values:
        user_params[pv.template.name] = _coerce_value(pv.value)

    # 2) Compute all params (manual + computed)
    all_params, param_errors = compute_parameters(
        template_part, user_params, timeout_ms,
    )

    # 3) Also include inherited / default params from the config
    other_values = ConfigParameterValue.objects.filter(
        config=config,
    ).exclude(source='manual').select_related('template')
    for pv in other_values:
        if pv.template.name not in all_params:
            all_params[pv.template.name] = _coerce_value(pv.value)

    # 4) Expand BOM tree
    bom_tree = expand_bom_level(
        template_part, all_params,
        depth=0, max_depth=max_depth, timeout_ms=timeout_ms,
    )

    # 5) Compute totals
    total_quantity = _compute_total_quantity(bom_tree)

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
    """Evaluate a parametric Part with given user parameters (no DB config needed).

    This is the "quick preview" mode — just pass a part and parameter values.

    Args:
        part: A Part model instance (must be parametric with PartParameterConfigs).
        user_params: User-provided driving parameters.
        timeout_ms: Formula evaluation timeout.
        max_depth: Max BOM recursion depth.

    Returns:
        Same structure as evaluate_configuration, but without config-level fields.
    """
    # 1) Compute all params
    all_params, param_errors = compute_parameters(
        part, user_params, timeout_ms,
    )

    # 2) Expand BOM tree
    bom_tree = expand_bom_level(
        part, all_params,
        depth=0, max_depth=max_depth, timeout_ms=timeout_ms,
    )

    # 3) Compute totals
    total_quantity = _compute_total_quantity(bom_tree)

    return {
        'part_id': _part_pk(part),
        'part_name': _part_display(part),
        'parameters': all_params,
        'parameter_errors': param_errors,
        'bom_tree': bom_tree,
        'total_bom_items': total_quantity,
        'expanded_at': timezone.now().isoformat(),
    }


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────


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
    if val.lower() in ('true', 'false'):
        return val.lower() == 'true'
    return val


def _compute_total_quantity(node: BomTreeNode) -> int:
    """Count total BOM items (leaf parts) in the tree."""
    count = 0
    for child in node.get('children', []):
        if child.get('excluded'):
            continue
        # Count this item
        count += 1
        # Recurse into children
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
