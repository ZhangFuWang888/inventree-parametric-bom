"""Variant Generator Service — Creates concrete Part variants from parametric configurations.

Takes a completed ProductConfiguration and:
1. Evaluates the configuration via bom_expander.evaluate_configuration()
2. Creates a new Part as a variant of the template_part
3. Copies parameter values as PartParameter records
4. Creates a static BOM (BomItem records) from the computed quantities
5. Updates the ProductConfiguration status to 'released' and stores the variant ID

Phase 3 — Dynamic BOM Generation / Release.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db import transaction

import structlog

from parametric_bom.bom_expander import evaluate_configuration
from parametric_bom.models import (
    ConfigParameterValue,
    ConfigStatusChoices,
    ProductConfiguration,
)

logger = structlog.get_logger('inventree')


# ──────────────────────────────────────────────
#  Flatten BOM tree into items for static BOM creation
# ──────────────────────────────────────────────


def _flatten_bom_tree(bom_tree: dict) -> List[Dict[str, Any]]:
    """Flatten a recursive BOM tree into a list of (part_id, quantity) items.

    Walks the tree breadth-first, skipping excluded nodes.
    The top-level node (the assembly itself) is not included.
    """
    items: List[Dict[str, Any]] = []
    _walk_bom_tree(bom_tree, items)
    return items


def _walk_bom_tree(node: dict, items: List[Dict[str, Any]]) -> None:
    """Recursively walk BOM tree children and collect leaf/child items."""
    for child in node.get('children', []):
        if child.get('excluded', False):
            continue

        # Determine the actual part ID (mode-aware resolution)
        part_id = (
            child.get('variant_part_id')       # variant mode
            or child.get('selected_candidate_part_id')  # candidate mode
            or child.get('actual_part_id')     # part_selector mode
            or child.get('part_id')            # fallback
        )
        part_name = (
            child.get('variant_part_name')
            or child.get('selected_candidate_part_name')
            or child.get('actual_part_name')
            or child.get('part_name', '')
        )
        qty = child.get('calculated_quantity') or child.get('quantity', 1)

        # Specification items are "virtual" — no Part record
        if child.get('mode') == 'specification':
            spec_fields = child.get('spec_fields_evaluated', [])
            spec_desc = '; '.join([
                f"{f['name']}={f['value']}{f.get('unit','')}"
                for f in spec_fields
            ])
            items.append({
                'part_id': None,
                'part_name': f"[规格] {child.get('part_name','')}: {spec_desc}",
                'quantity': qty,
                'optional': child.get('optional', False),
                'consumable': child.get('consumable', False),
                'reference': child.get('reference', ''),
                'bom_item_id': child.get('bom_item_id'),
                'is_specification': True,
            })
        else:
            items.append({
                'part_id': part_id,
                'part_name': part_name,
                'quantity': qty,
                'optional': child.get('optional', False),
                'consumable': child.get('consumable', False),
                'reference': child.get('reference', ''),
                'bom_item_id': child.get('bom_item_id'),
            })

        # Recurse into sub-children (skip spec items — no sub-BOM)
        if child.get('mode') != 'specification':
            _walk_bom_tree(child, items)


# ──────────────────────────────────────────────
#  Build variant part name from parameters
# ──────────────────────────────────────────────


def _build_variant_name(template_name: str, params: Dict[str, Any]) -> str:
    """Build a descriptive variant name.

    Format: "TemplateName (param1=val1, param2=val2)"
    """
    param_parts = []
    for key, val in params.items():
        if val is None:
            val = ''
        param_parts.append(f"{key}={val}")
    param_str = ", ".join(param_parts)
    return f"{template_name} ({param_str})"


# ──────────────────────────────────────────────
#  Main Generator
# ──────────────────────────────────────────────


@transaction.atomic
def generate_variant(config_id: int) -> Dict[str, Any]:
    """Generate a concrete Part variant from a completed ProductConfiguration.

    Args:
        config_id: PK of the ProductConfiguration to generate from.

    Returns:
        Dict with:
            success (bool)
            variant_part_id (int, optional)
            variant_part_name (str, optional)
            bom_items_created (int, optional)
            parameters_set (int, optional)
            config_id (int)
            error (str, optional)
    """
    # ── 1) Fetch and validate configuration ──────────────────────────
    try:
        config = ProductConfiguration.objects.select_related(
            'template_part',
            'created_by',
        ).prefetch_related(
            'parameter_values__template',
        ).get(pk=config_id)
    except ProductConfiguration.DoesNotExist:
        return {'success': False, 'error': f'Configuration {config_id} not found.', 'config_id': config_id}

    if config.status != ConfigStatusChoices.COMPLETED:
        return {
            'success': False,
            'error': (
                f"Cannot generate variant from configuration with status "
                f"'{config.status}'. Status must be 'completed'."
            ),
            'config_id': config_id,
        }

    # Check that parameters exist
    param_count = config.parameter_values.count()
    if param_count == 0:
        return {
            'success': False,
            'error': 'Configuration has no parameters set. Set parameters before generating a variant.',
            'config_id': config_id,
        }

    template_part = config.template_part
    logger.info(
        "variant_generation_started",
        config_id=config_id,
        template_part_id=template_part.pk,
        template_part_name=template_part.name,
    )

    # ── 2) Evaluate configuration to get expanded BOM ────────────────
    try:
        evaluation = evaluate_configuration(config)
    except Exception as exc:
        logger.exception("bom_evaluation_failed", config_id=config_id)
        return {
            'success': False,
            'error': f'BOM evaluation failed: {exc}',
            'config_id': config_id,
        }

    bom_tree = evaluation.get('bom_tree', {})
    all_params = evaluation.get('parameters', {})
    param_errors = evaluation.get('parameter_errors', [])

    if param_errors:
        logger.warning(
            "parameter_errors_during_evaluation",
            config_id=config_id,
            errors=param_errors,
        )

    # ── 3) Build variant name ────────────────────────────────────────
    variant_name = _build_variant_name(template_part.name, all_params)

    # ── 4) Create the variant Part ───────────────────────────────────
    from part.models import Part

    variant_part = Part.objects.create(
        name=variant_name,
        description=f"Variant generated from configuration '{config.title}' (rev {config.revision})",
        IPN=f"VAR-{template_part.pk}-{config.pk}",
        variant_of=template_part,
        category=template_part.category,
        is_template=False,
        assembly=True,
        component=False,
        active=True,
        virtual=False,
    )
    logger.info(
        "variant_part_created",
        variant_part_id=variant_part.pk,
        variant_name=variant_name,
    )

    # ── 5) Copy parameter values as PartParameter records ────────────
    from common.models import Parameter
    from django.contrib.contenttypes.models import ContentType

    part_content_type = ContentType.objects.get_for_model(Part)
    parameters_set = 0
    param_values = ConfigParameterValue.objects.filter(
        config=config,
    ).select_related('template')

    for pv in param_values:
        Parameter.objects.create(
            model_type=part_content_type,
            model_id=variant_part.pk,
            template=pv.template,
            data=str(pv.value) if pv.value is not None else '',
        )
        parameters_set += 1

    # Also copy computed params from evaluation that aren't in ConfigParameterValue
    # (these come from PartParameterConfig computation formulas)
    existing_template_names = set(
        pv.template.name for pv in param_values
    )
    for param_name, param_value in all_params.items():
        if param_name not in existing_template_names:
            try:
                template = ParameterTemplate.objects.get(name=param_name)
                Parameter.objects.create(
                    model_type=part_content_type,
                    model_id=variant_part.pk,
                    template=template,
                    data=str(param_value) if param_value is not None else '',
                )
                parameters_set += 1
            except ParameterTemplate.DoesNotExist:
                logger.warning(
                    "parameter_template_not_found",
                    param_name=param_name,
                    config_id=config_id,
                )

    # ── 6) Flatten BOM tree and create BomItem records ───────────────
    from part.models import BomItem

    bom_items = _flatten_bom_tree(bom_tree)
    bom_items_created = 0

    for item in bom_items:
        sub_part_id = item['part_id']
        if sub_part_id is None:
            logger.warning(
                "bom_item_skipped_no_part_id",
                item_name=item.get('part_name'),
                config_id=config_id,
            )
            continue

        try:
            sub_part = Part.objects.get(pk=sub_part_id)
        except Part.DoesNotExist:
            logger.warning(
                "bom_item_skipped_part_not_found",
                part_id=sub_part_id,
                config_id=config_id,
            )
            continue

        # Convert quantity to Decimal
        try:
            quantity = Decimal(str(item['quantity']))
        except (ValueError, TypeError):
            quantity = Decimal('1')

        BomItem.objects.create(
            part=variant_part,
            sub_part=sub_part,
            quantity=quantity,
            reference=item.get('reference', '')[:500] if item.get('reference') else '',
            optional=item.get('optional', False),
            consumable=item.get('consumable', False),
        )
        bom_items_created += 1

    # ── 7) Update configuration status to 'released' ─────────────────
    config.status = ConfigStatusChoices.RELEASED
    config.generated_bom = evaluation  # Store full evaluation result
    config.save(update_fields=['status', 'generated_bom', 'updated_at'])

    logger.info(
        "variant_generation_complete",
        config_id=config_id,
        variant_part_id=variant_part.pk,
        variant_name=variant_name,
        bom_items_created=bom_items_created,
        parameters_set=parameters_set,
    )

    return {
        'success': True,
        'variant_part_id': variant_part.pk,
        'variant_part_name': variant_name,
        'bom_items_created': bom_items_created,
        'parameters_set': parameters_set,
        'config_id': config_id,
    }
