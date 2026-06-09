"""
Parameter Inheritance Service for Parametric BOM.

Provides three core capabilities:
1. inherit_from_template() — Copy all PartParameterConfig and matching
   ParametricBomItem records from a template part to a variant part.
2. inherit_parent_params() — During BOM expansion, pass parent-level
   parameters as contextual context for formula evaluation.
3. propagate_param_change() — When a parameter config changes on a
   template, mark all variant parts that inherit it as 'needs_review'.

Phase 2 — Parameter Inheritance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.db import transaction

import structlog

logger = structlog.get_logger('inventree')


# ──────────────────────────────────────────────
#  1.  Inherit from Template
# ──────────────────────────────────────────────


@transaction.atomic
def inherit_from_template(variant_part) -> Dict[str, int]:
    """Copy all parameter configs and matching BOM items from a template to a variant.

    The variant's *variant_of* FK is used to locate the template part.

    Args:
        variant_part: A Part instance whose variant_of points to a template.

    Returns:
        Dict with configs_copied, bom_items_copied counts.
    """
    from part.models import BomItem
    from parametric_bom.models import (
        ParametricBomItem,
        PartParameterConfig,
    )

    template_part = getattr(variant_part, 'variant_of', None)
    if template_part is None:
        logger.warning(
            "inherit_from_template_no_template",
            variant_part_id=variant_part.pk,
        )
        return {'configs_copied': 0, 'bom_items_copied': 0}

    configs_copied = 0
    bom_items_copied = 0

    # ── 1) Copy all PartParameterConfig records ──────────────────────
    template_configs = PartParameterConfig.objects.filter(
        part=template_part,
    ).select_related('template')

    for tpl_cfg in template_configs:
        # Avoid duplicates (unique_together = (part, template))
        PartParameterConfig.objects.get_or_create(
            part=variant_part,
            template=tpl_cfg.template,
            defaults={
                'default_value': tpl_cfg.default_value,
                'min_value': tpl_cfg.min_value,
                'max_value': tpl_cfg.max_value,
                'options': tpl_cfg.options,
                'is_driving': tpl_cfg.is_driving,
                'is_computed': tpl_cfg.is_computed,
                'computation_formula': tpl_cfg.computation_formula,
                'ui_hint': tpl_cfg.ui_hint,
                'display_order': tpl_cfg.display_order,
                'visible_on_config': tpl_cfg.visible_on_config,
            },
        )
        configs_copied += 1

    # ── 2) Copy ParametricBomItem records where the BomItem's
    #       sub_part matches between template BOM and variant BOM ─────
    template_bom_items = BomItem.objects.filter(part=template_part)
    variant_bom_items = BomItem.objects.filter(part=variant_part)

    # Build a lookup: sub_part_id → BomItem (for the variant)
    variant_bom_by_sub = {
        bi.sub_part_id: bi
        for bi in variant_bom_items.select_related('sub_part')
    }

    for tpl_bom in template_bom_items.select_related('sub_part'):
        # Try to get the parametric config on the template's BomItem
        try:
            tpl_param_bom = ParametricBomItem.objects.get(bom_item=tpl_bom)
        except ParametricBomItem.DoesNotExist:
            continue  # No parametric config on this template BomItem

        # Find matching BomItem on the variant by sub_part
        variant_bom = variant_bom_by_sub.get(tpl_bom.sub_part_id)
        if variant_bom is None:
            continue

        # Copy ParametricBomItem to the variant's BomItem
        ParametricBomItem.objects.update_or_create(
            bom_item=variant_bom,
            defaults={
                'qty_formula': tpl_param_bom.qty_formula,
                'condition_formula': tpl_param_bom.condition_formula,
                'part_selector_formula': tpl_param_bom.part_selector_formula,
            },
        )
        bom_items_copied += 1

    logger.info(
        "inherit_from_template_complete",
        variant_part_id=variant_part.pk,
        template_part_id=template_part.pk,
        configs_copied=configs_copied,
        bom_items_copied=bom_items_copied,
    )

    return {
        'configs_copied': configs_copied,
        'bom_items_copied': bom_items_copied,
    }


# ──────────────────────────────────────────────
#  2.  Inherit Parent Params (BOM expansion context)
# ──────────────────────────────────────────────


def inherit_parent_params(params: dict, parent_params: Optional[dict] = None) -> dict:
    """Prepare the evaluation context for a child BOM level.

    When expanding a child BOM level, the parent-level parameters are
    passed as 'parent' context so formulas can reference them via
    ``parent.paramName``.

    Args:
        params: Computed parameter values for the *current* (child) level.
        parent_params: Parameter values from the parent level, or None.

    Returns:
        Full context dict suitable for ``formula_engine.evaluate()``:
            {'param': child_params, 'parent': parent_params}
    """
    context: Dict[str, Any] = {'param': dict(params)}

    if parent_params is not None:
        context['parent'] = dict(parent_params)

    return context


# ──────────────────────────────────────────────
#  3.  Propagate Param Change
# ──────────────────────────────────────────────


def propagate_param_change(part_config_id: int) -> List[Dict[str, Any]]:
    """When a PartParameterConfig changes on a template, flag all variant
    parts that inherit this config as 'needs_review'.

    This is a soft notification mechanism — it logs the affected parts
    and returns their details for the caller to act upon (e.g., send
    a notification, add a review flag).

    Args:
        part_config_id: PK of the PartParameterConfig that was changed.

    Returns:
        List of dicts, each with:
            - part_id
            - part_name
            - template_part_id
            - config_id (the original changed config)
    """
    from parametric_bom.models import PartParameterConfig

    try:
        changed_config = PartParameterConfig.objects.select_related(
            'part', 'template',
        ).get(pk=part_config_id)
    except PartParameterConfig.DoesNotExist:
        logger.warning(
            "propagate_param_change_config_not_found",
            part_config_id=part_config_id,
        )
        return []

    template_part = changed_config.part
    template_name = changed_config.template.name

    # Find all variants of this template that have a matching config
    affected: List[Dict[str, Any]] = []

    # Get direct variants (variant_of = template_part)
    variant_configs = PartParameterConfig.objects.filter(
        part__variant_of=template_part,
        template=changed_config.template,
    ).select_related('part')

    for vc in variant_configs:
        logger.info(
            "propagate_param_change_variant_needs_review",
            variant_part_id=vc.part.pk,
            variant_name=vc.part.name,
            template_part_id=template_part.pk,
            template_name=template_name,
            config_id=part_config_id,
        )
        affected.append({
            'part_id': vc.part.pk,
            'part_name': vc.part.name,
            'template_part_id': template_part.pk,
            'config_id': part_config_id,
            'parameter_template': template_name,
        })

    return affected
