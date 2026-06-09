"""Cost Estimator Service — Estimates cost of a parametric configuration.

Takes an expanded BOM tree from bom_expander and calculates the total cost
by looking up cached PartPricing data for each leaf part in the tree.

Phase 3 — Dynamic BOM Generation (cost estimation extension).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger('inventree')

# ──────────────────────────────────────────────
#  Pricing field preference mapping
# ──────────────────────────────────────────────

# Maps short names to (min_field, max_field) on PartPricing
_PRICING_FIELD_MAP: Dict[str, Tuple[str, str]] = {
    'internal': ('internal_cost_min', 'internal_cost_max'),
    'purchase': ('purchase_cost_min', 'purchase_cost_max'),
    'bom': ('bom_cost_min', 'bom_cost_max'),
    'supplier': ('supplier_price_min', 'supplier_price_max'),
    'overall': ('overall_min', 'overall_max'),
    'sale': ('sale_price_min', 'sale_price_max'),
}

# ──────────────────────────────────────────────
#  Main entry points
# ──────────────────────────────────────────────


def estimate_configuration_cost(
    config,
    markup_pct: float = 0.0,
    pricing_preference: str = 'internal',
) -> Dict[str, Any]:
    """Estimate cost for a ProductConfiguration.

    Evaluates the configuration to get the expanded BOM tree, then
    calculates total cost from leaf-item pricing data.

    Args:
        config: A ProductConfiguration instance.
        markup_pct: Percentage markup to apply (e.g., 15 for 15%).
        pricing_preference: Which PartPricing field to prioritise.
            One of: 'internal', 'purchase', 'bom', 'supplier', 'overall', 'sale'.

    Returns:
        Dict with total_cost, currency, items, errors, and config metadata.
    """
    from parametric_bom.bom_expander import evaluate_configuration

    result = evaluate_configuration(config)
    bom_tree = result.get('bom_tree', {})

    estimate = estimate_from_bom_tree(bom_tree, markup_pct, pricing_preference)

    # Enrich with config-level info
    estimate['config_id'] = config.pk
    estimate['title'] = config.title
    estimate['part_id'] = result.get('part_id')
    estimate['part_name'] = result.get('part_name')
    estimate['parameters'] = result.get('parameters', {})

    return estimate


def estimate_part_cost(
    part,
    user_params: Dict[str, Any],
    markup_pct: float = 0.0,
    pricing_preference: str = 'internal',
    timeout_ms: int = 500,
    max_depth: int = 10,
) -> Dict[str, Any]:
    """Estimate cost for a parametric Part with ad-hoc parameter values.

    No database configuration required — ideal for quick previews.

    Args:
        part: A Part model instance.
        user_params: User-provided driving parameters {param_name: value}.
        markup_pct: Percentage markup to apply.
        pricing_preference: Which PartPricing field to prioritise.
        timeout_ms: Formula evaluation timeout in milliseconds.
        max_depth: Max BOM recursion depth.

    Returns:
        Dict with total_cost, currency, items, errors, and part metadata.
    """
    from parametric_bom.bom_expander import evaluate_part

    result = evaluate_part(part, user_params, timeout_ms, max_depth)
    bom_tree = result.get('bom_tree', {})

    estimate = estimate_from_bom_tree(bom_tree, markup_pct, pricing_preference)

    # Enrich with part-level info
    estimate['part_id'] = result.get('part_id')
    estimate['part_name'] = result.get('part_name')
    estimate['parameters'] = result.get('parameters', {})

    return estimate


def estimate_from_bom_tree(
    bom_tree: Dict[str, Any],
    markup_pct: float = 0.0,
    pricing_preference: str = 'internal',
) -> Dict[str, Any]:
    """Estimate cost from an already-expanded BOM tree.

    This is the core calculation: flatten the tree to leaf items, look up
    unit costs from PartPricing, and compute the total.

    Args:
        bom_tree: Expanded BOM tree (from bom_expander.evaluate_configuration
            or evaluate_part).
        markup_pct: Percentage markup to apply (0 = no markup).
        pricing_preference: Which PartPricing field to prioritise.

    Returns:
        Dict with keys:
            total_cost (float): Total cost after markup.
            total_cost_before_markup (float): Cost before markup.
            markup_pct (float): Applied markup percentage.
            currency (str): Currency code (e.g., 'USD').
            items (list): Per-item cost breakdown.
            errors (list): Any pricing lookup errors.
            item_count (int): Number of leaf items costed.
    """
    items = _flatten_bom_for_cost(bom_tree)

    total_cost = Decimal('0.0')
    currency: Optional[str] = None
    cost_items: List[Dict[str, Any]] = []
    errors: List[str] = []

    for item in items:
        part_id = item['part_id']
        quantity = Decimal(str(item['quantity']))
        part_name = item['part_name']

        unit_cost, cost_currency, cost_error = _get_part_unit_cost(
            part_id, pricing_preference,
        )

        if cost_error:
            errors.append(cost_error)
            cost_items.append({
                'part_id': part_id,
                'part_name': part_name,
                'quantity': float(quantity),
                'unit_cost': None,
                'subtotal': None,
                'error': cost_error,
            })
            continue

        # Use first non-None currency found
        if currency is None and cost_currency:
            currency = cost_currency

        subtotal = quantity * unit_cost
        total_cost += subtotal

        cost_items.append({
            'part_id': part_id,
            'part_name': part_name,
            'quantity': float(quantity),
            'unit_cost': float(unit_cost),
            'subtotal': float(subtotal),
        })

    # Apply markup percentage
    if markup_pct > 0 and total_cost > 0:
        markup_factor = Decimal(str(1 + markup_pct / 100))
        total_cost_marked_up = total_cost * markup_factor
    else:
        markup_factor = Decimal('1.0')
        total_cost_marked_up = total_cost

    return {
        'total_cost': float(total_cost_marked_up),
        'total_cost_before_markup': float(total_cost),
        'markup_pct': markup_pct,
        'currency': currency or 'USD',
        'items': cost_items,
        'errors': errors,
        'item_count': len(cost_items),
    }


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────


def _flatten_bom_for_cost(
    node: Dict[str, Any],
    parent_qty: float = 1.0,
) -> List[Dict[str, Any]]:
    """Flatten a BOM tree into a list of leaf items with cumulative quantities.

    Each item's quantity is the product of all ancestor quantities up the
    assembly tree.  Assemblies (nodes with children) are *not* included as
    separate line items — only leaf parts are costed.

    Args:
        node: A BomTreeNode from the expanded BOM tree.
        parent_qty: Cumulative multiplier from parent assemblies.

    Returns:
        List of dicts with 'part_id', 'part_name', 'quantity'.
    """
    items: List[Dict[str, Any]] = []

    for child in node.get('children', []):
        if child.get('excluded'):
            continue

        qty = float(child.get('calculated_quantity', child.get('quantity', 1)))
        cumulative_qty = qty * parent_qty

        part_id = child.get('actual_part_id') or child.get('part_id')
        part_name = child.get('actual_part_name') or child.get('part_name')

        grandchildren = child.get('children', [])

        if grandchildren:
            # Assembly — recurse; do not add the assembly itself as a cost item
            sub_items = _flatten_bom_for_cost(child, cumulative_qty)
            items.extend(sub_items)
        else:
            # Leaf item
            items.append({
                'part_id': part_id,
                'part_name': part_name,
                'quantity': cumulative_qty,
            })

    return items


def _get_part_unit_cost(
    part_id: int,
    pricing_preference: str = 'internal',
) -> Tuple[Optional[Decimal], Optional[str], Optional[str]]:
    """Get the unit cost for a Part from its cached PartPricing data.

    Uses a fallback chain within the preferred category:
      1. The ``min`` price field for the preference (e.g. ``internal_cost_min``)
      2. The ``max`` price field for the preference (e.g. ``internal_cost_max``)
      3. If both are ``None``, tries ``overall_min`` as a last resort.

    Args:
        part_id: The Part primary key.
        pricing_preference: Which pricing field category to use.

    Returns:
        (unit_cost_amount, currency_code, error_message)
        - Amount is a Decimal (or None if unavailable).
        - Currency is a 3-letter code (e.g. 'USD') — may be None.
        - Error is a human-readable string, or None on success.
    """
    from part.models import Part, PartPricing

    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return None, None, f'Part {part_id} not found'

    try:
        pricing: PartPricing = part.pricing_data
    except PartPricing.DoesNotExist:
        return None, None, f'No pricing data for part {part_id} ({part.name})'

    if pricing is None:
        return None, None, f'No pricing data for part {part_id} ({part.name})'

    fields = _PRICING_FIELD_MAP.get(pricing_preference, _PRICING_FIELD_MAP['internal'])
    min_field, max_field = fields

    # Try preferred min field first
    cost = getattr(pricing, min_field, None)
    if cost is not None:
        return cost.amount, cost.currency, None

    # Fall back to preferred max field
    cost = getattr(pricing, max_field, None)
    if cost is not None:
        return cost.amount, cost.currency, None

    # Last resort: overall_min
    cost = getattr(pricing, 'overall_min', None)
    if cost is not None:
        logger.debug(
            'Fell back to overall_min for part %s (%s)',
            part_id, pricing_preference,
        )
        return cost.amount, cost.currency, None

    return (
        None,
        pricing.currency if pricing.currency else None,
        f'No {pricing_preference} pricing available for part {part_id} ({part.name})',
    )
