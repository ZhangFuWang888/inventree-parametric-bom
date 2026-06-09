"""
Template Library Service for Parametric BOM.

Provides tools to sync PartCategoryParameterTemplate (InvenTree core) records
with PartParameterConfig (parametric_bom) records, inspect category templates,
bulk-assign templates to categories, and auto-sync on part creation.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger('inventree')


# ─────────────────────────────────────────────────────────
#  1.  Sync PartParameterConfig from category templates
# ─────────────────────────────────────────────────────────


def sync_part_params_from_category(part) -> dict[str, Any]:
    """Fetch PartCategoryParameterTemplate records for *part*'s category
    (including ancestors) and create any missing PartParameterConfig entries.

    Args:
        part: A ``Part`` instance (or anything with ``category`` and ``pk``).

    Returns:
        dict with keys ``created``, ``skipped``, ``errors``.
    """
    from part.models import PartCategoryParameterTemplate
    from parametric_bom.models import PartParameterConfig

    result: dict[str, Any] = {'created': 0, 'skipped': 0, 'errors': []}

    if not part.category:
        logger.info('Part %s has no category — nothing to sync', part.pk)
        return result

    # Gather category templates (self + ancestors)
    categories = part.category.get_ancestors(include_self=True)

    category_templates = (
        PartCategoryParameterTemplate.objects.filter(
            category__in=categories,
        )
        .select_related('template')
        .order_by('-category__level')
    )

    seen_template_ids: set[int] = set()

    for ct in category_templates:
        tpl_id = ct.template.pk

        # Skip duplicate template across ancestor categories
        if tpl_id in seen_template_ids:
            continue
        seen_template_ids.add(tpl_id)

        # Check if a PartParameterConfig already exists for this part+template
        exists = PartParameterConfig.objects.filter(
            part=part,
            template=ct.template,
        ).exists()

        if exists:
            result['skipped'] += 1
            continue

        try:
            PartParameterConfig.objects.create(
                part=part,
                template=ct.template,
                default_value=ct.default_value or '',
            )
            result['created'] += 1
        except Exception as exc:
            msg = (
                f'Failed to create PartParameterConfig for '
                f'part={part.pk}, template={tpl_id}: {exc}'
            )
            logger.warning(msg)
            result['errors'].append(msg)

    return result


# ─────────────────────────────────────────────────────────
#  2.  Category template detail
# ─────────────────────────────────────────────────────────


def get_category_template_detail(category_id: int) -> dict[str, Any]:
    """Return full detail about all ParameterTemplates assigned to a category.

    Includes:
      - All ``PartCategoryParameterTemplate`` records
      - Which parts in this category (and children) use each template
      - A summary of the parametric config state for each template

    Args:
        category_id: PK of the ``PartCategory`` to inspect.

    Returns:
        A dict with keys ``category_id``, ``templates`` (list), ``summary``.
    """
    from part.models import Part, PartCategory, PartCategoryParameterTemplate
    from parametric_bom.models import PartParameterConfig

    try:
        category = PartCategory.objects.get(pk=category_id)
    except PartCategory.DoesNotExist:
        return {'error': f'Category {category_id} not found'}

    cat_templates = PartCategoryParameterTemplate.objects.filter(
        category=category,
    ).select_related('template')

    templates_detail: list[dict[str, Any]] = []
    summary = {'total_templates': 0, 'total_parts_affected': 0}

    for ct in cat_templates:
        template = ct.template

        # Parts in this category (or descendants) that have this template
        parts_in_category = Part.objects.filter(
            category__in=category.get_descendants(include_self=True),
        )
        parts_using = parts_in_category.filter(
            parametric_configs__template=template,
        )
        parts_using_ids = list(
            parts_using.values_list('pk', flat=True).distinct()
        )

        # Config summary
        config_count = PartParameterConfig.objects.filter(
            part__in=parts_in_category,
            template=template,
        ).count()

        templates_detail.append(
            {
                'template_id': template.pk,
                'template_name': template.name,
                'template_description': getattr(template, 'description', ''),
                'template_units': getattr(template, 'units', ''),
                'default_value': ct.default_value or '',
                'category_template_id': ct.pk,
                'parts_using_count': len(parts_using_ids),
                'parts_using_ids': parts_using_ids,
                'parametric_config_count': config_count,
            }
        )

    summary['total_templates'] = len(templates_detail)
    summary['total_parts_affected'] = sum(
        t['parts_using_count'] for t in templates_detail
    )

    return {
        'category_id': category.pk,
        'category_name': category.name,
        'category_path': category.pathstring if hasattr(category, 'pathstring') else '',
        'templates': templates_detail,
        'summary': summary,
    }


# ─────────────────────────────────────────────────────────
#  3.  Bulk-assign templates to a category
# ─────────────────────────────────────────────────────────


def bulk_assign_templates(
    category_id: int,
    templates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assign multiple templates to a category, replacing existing mappings.

    Args:
        category_id: PK of the ``PartCategory``.
        templates: List of dicts, each with ``template_id``
            and optional ``default_value``.

    Returns:
        dict with keys ``assigned``, ``removed``, ``errors``.
    """
    from part.models import PartCategory, PartCategoryParameterTemplate

    result: dict[str, Any] = {'assigned': 0, 'removed': 0, 'errors': []}

    try:
        category = PartCategory.objects.get(pk=category_id)
    except PartCategory.DoesNotExist:
        return {**result, 'error': f'Category {category_id} not found'}

    # Normalise input
    incoming: list[dict[str, Any]] = []
    for item in templates:
        if isinstance(item, dict):
            tpl_id = item.get('template_id')
            default_val = item.get('default_value', '')
        else:
            tpl_id = item
            default_val = ''

        if tpl_id is None:
            continue
        try:
            incoming.append(
                {
                    'template_id': int(tpl_id),
                    'default_value': str(default_val or ''),
                }
            )
        except (ValueError, TypeError):
            result['errors'].append(f'Invalid template_id: {tpl_id}')

    incoming_ids = {x['template_id'] for x in incoming}

    # Remove old mappings not in the incoming list
    existing = PartCategoryParameterTemplate.objects.filter(category=category)
    existing_ids = set(existing.values_list('template_id', flat=True))

    to_remove = existing_ids - incoming_ids
    removed_count, _ = existing.filter(template_id__in=to_remove).delete()
    result['removed'] = removed_count

    # Create new mappings
    from common.models import ParameterTemplate

    for item in incoming:
        tpl_id = item['template_id']
        if tpl_id in existing_ids:
            # Update default_value if it already exists
            PartCategoryParameterTemplate.objects.filter(
                category=category, template_id=tpl_id
            ).update(default_value=item['default_value'])
            continue

        try:
            template = ParameterTemplate.objects.get(pk=tpl_id)
            PartCategoryParameterTemplate.objects.create(
                category=category,
                template=template,
                default_value=item['default_value'],
            )
            result['assigned'] += 1
        except ParameterTemplate.DoesNotExist:
            result['errors'].append(f'ParameterTemplate {tpl_id} not found')
        except Exception as exc:
            result['errors'].append(
                f'Failed to assign template {tpl_id}: {exc}'
            )

    return result


# ─────────────────────────────────────────────────────────
#  4.  Auto-sync for new part (signal handler)
# ─────────────────────────────────────────────────────────


def auto_sync_for_new_part(part) -> dict[str, Any]:
    """Callable signal handler / post-save hook for parametric Parts.

    When a parametric Part is created:
      1. Calls ``sync_part_params_from_category`` to create missing
         ``PartParameterConfig`` entries from the part's category templates.
      2. If ``part.variant_of`` is set, also copies configs from the
         parent variant (where they don't already exist).

    Args:
        part: A ``Part`` instance that was just created.

    Returns:
        dict with keys ``synced_from_category``, ``inherited_from_parent``,
        and ``errors``.
    """
    from parametric_bom.models import PartParameterConfig

    result: dict[str, Any] = {
        'synced_from_category': {'created': 0, 'skipped': 0},
        'inherited_from_parent': {'created': 0, 'skipped': 0},
        'errors': [],
    }

    # Step 1 — Sync from category templates
    try:
        cat_sync = sync_part_params_from_category(part)
        result['synced_from_category'] = {
            'created': cat_sync['created'],
            'skipped': cat_sync['skipped'],
        }
        result['errors'].extend(cat_sync.get('errors', []))
    except Exception as exc:
        msg = f'Category sync failed for part {part.pk}: {exc}'
        logger.exception(msg)
        result['errors'].append(msg)

    # Step 2 — Inherit params from parent variant
    if part.variant_of:
        try:
            parent_configs = PartParameterConfig.objects.filter(
                part=part.variant_of,
            ).select_related('template')

            for pcfg in parent_configs:
                exists = PartParameterConfig.objects.filter(
                    part=part,
                    template=pcfg.template,
                ).exists()

                if exists:
                    result['inherited_from_parent']['skipped'] += 1
                    continue

                PartParameterConfig.objects.create(
                    part=part,
                    template=pcfg.template,
                    default_value=pcfg.default_value,
                    min_value=pcfg.min_value,
                    max_value=pcfg.max_value,
                    options=pcfg.options,
                    is_driving=pcfg.is_driving,
                    is_computed=pcfg.is_computed,
                    computation_formula=pcfg.computation_formula,
                    ui_hint=pcfg.ui_hint,
                    display_order=pcfg.display_order,
                    visible_on_config=pcfg.visible_on_config,
                )
                result['inherited_from_parent']['created'] += 1

        except Exception as exc:
            msg = (
                f'Parent inheritance failed for part {part.pk} '
                f'(parent={part.variant_of.pk}): {exc}'
            )
            logger.exception(msg)
            result['errors'].append(msg)

    return result
