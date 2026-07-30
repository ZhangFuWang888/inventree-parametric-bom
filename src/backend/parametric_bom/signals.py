"""Signal handlers for Parametric BOM.

Prevents deletion of PartParameters (InvenTree Parameter) that are
referenced by parametric BOM formulas.
"""

import re
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
import logging

logger = logging.getLogger('parametric_bom')


# ── Helper: sanitize name like the frontend does ──

def _sanitize(s: str) -> str:
    """Match the frontend's sanitizeName() logic:
    replace non-identifier chars with _, collapse runs, strip edges.
    """
    result = re.sub(r'[^A-Za-z0-9_\u4e00-\u9fff]', '_', str(s))
    result = re.sub(r'_+', '_', result)
    return result.strip('_')


# ── All formula fields to scan ──

FORMULA_CHECK_FIELDS = [
    # PartParameterConfig
    # ('PartParameterConfig', 'computation_formula') - removed
    # ParametricBomItem
    ('ParametricBomItem', 'qty_formula'),
    ('ParametricBomItem', 'name_formula'),
    ('ParametricBomItem', 'condition_formula'),
    ('ParametricBomItem', 'reference_formula'),
    ('ParametricBomItem', 'price_formula'),
    # ParametricRule
    ('ParametricRule', 'condition_formula'),
    ('ParametricRule', 'value_formula'),
    # InheritanceMapping
    ('InheritanceMapping', 'formula'),
    # PartAttributeFormula
    ('PartAttributeFormula', 'formula'),
    # PartVariable
    ('PartVariable', 'formula'),
    # BomSpecification — drawing/unit_cost
    ('BomSpecification', 'drawing_ref_formula'),
    ('BomSpecification', 'unit_cost_formula'),
    # VariantMapping — variant name/IPN templates
    ('VariantMapping', 'variant_name_template'),
    ('VariantMapping', 'variant_ipn_template'),
    ('VariantMapping', 'param_mapping'),
]


def _scan_formulas_for_refpart(models_module, model_name, field_name, search_key: str) -> list:
    """Scan all rows of a model for the search_key in a specific formula field.

    Returns list of (part_name, field_label, formula_snippet) tuples.
    """
    try:
        Model = getattr(models_module, model_name)
    except AttributeError:
        return []

    field_label_map = {
        # 'computation_formula' - removed
        'qty_formula': '数量公式',
        'name_formula': '名称公式',
        'condition_formula': '条件公式',
        'reference_formula': '备注公式',
        'price_formula': '价格公式',
        'value_formula': '值公式',
        'formula': '公式',
        'drawing_ref_formula': '图纸参考公式',
        'unit_cost_formula': '单位成本公式',
        'param_mapping': '参数映射',
        'variant_name_template': '变体名称模板',
        'variant_ipn_template': '变体IPN模板',
    }
    label = field_label_map.get(field_name, field_name)
    results = []

    # Special case: VariantMapping.param_mapping is JSON
    if field_name == 'param_mapping':
        rows = Model.objects.exclude(**{field_name: {}}).exclude(**{field_name: None})
        for row in rows:
            val = getattr(row, field_name, {})
            if isinstance(val, dict):
                for k, v in val.items():
                    if isinstance(v, str) and search_key in v:
                        ref_text, prod_id = _resolve_ref(row)
                        results.append((ref_text, f'参数映射「{k}」', _truncate(v), prod_id))
        return results

    rows = Model.objects.exclude(**{field_name: ''}).exclude(**{field_name: None})
    for row in rows:
        val = getattr(row, field_name, '') or ''
        if search_key in val:
            ref_text, prod_id = _resolve_ref(row)
            results.append((ref_text, label, _truncate(val), prod_id))

    return results


def _resolve_ref(row):
    """Try to get a human-readable reference from a model instance.
    Returns (display_text, product_part_id) tuple.
    """
    product_part_id = None

    # Try common FK patterns
    for attr in ('part', 'product_part', 'bom_item__part', 'target_part'):
        try:
            parts = attr.split('__')
            obj = row
            for p in parts:
                obj = getattr(obj, p, None)
                if obj is None:
                    break
            if obj and hasattr(obj, 'name'):
                product_part_id = obj.pk
                return (f'物料「{obj.name}」', product_part_id)
        except Exception:
            continue
    # Handle VariantMapping: parametric_bom_item → bom_item → part
    try:
        if hasattr(row, 'parametric_bom_item') and row.parametric_bom_item:
            pbi = row.parametric_bom_item
            if hasattr(pbi, 'bom_item') and pbi.bom_item:
                part = pbi.bom_item.part
                if part and hasattr(part, 'name'):
                    product_part_id = part.pk
                    return (f'物料「{part.name}」', product_part_id)
    except Exception:
        pass
    return (f'{row._meta.model_name}#{row.pk}', None)


def _truncate(s: str, max_len: int = 60) -> str:
    return s if len(s) <= max_len else s[:max_len - 3] + '...'


def find_parameter_references(part_id: int, template_name: str) -> list:
    """Check if a PartParameter (on a given part) is referenced in any formula.

    Args:
        part_id: PK of the Part that owns the parameter.
        template_name: The ParameterTemplate name (e.g. '材质（牌号）').

    Returns:
        List of (product_ref, field_label, formula_snippet) tuples.
        Empty list means no references found (safe to delete).
    """
    from parametric_bom import models as pm

    # Build the search key: 参考零件.{sanitized_part_name}__{sanitized_param_name}
    try:
        from part.models import Part
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return []

    part_key = _sanitize(part.name) or ('p' + str(part_id))
    param_key = _sanitize(template_name) or ('param_' + str(part_id))
    search_key = f'参考零件.{part_key}__{param_key}'

    results = []

    # Scan all formula fields
    for model_name, field_name in FORMULA_CHECK_FIELDS:
        try:
            hits = _scan_formulas_for_refpart(pm, model_name, field_name, search_key)
            results.extend(hits)
        except Exception:
            pass

    # Also check VariantMapping.param_mapping (special JSON field)
    try:
        hits = _scan_formulas_for_refpart(pm, 'VariantMapping', 'param_mapping', search_key)
        results.extend(hits)
    except Exception:
        pass

    return results


# ── Signal handler ──

def check_parameter_delete(sender, instance, **kwargs):
    """Pre-delete handler for InvenTree Parameter.

    Raises ProtectedError if the parameter is referenced by any formula.
    """
    from django.db.models import ProtectedError

    template = instance.template
    if not template:
        return  # No template name — can't be referenced

    # Get the part_id from the generic FK
    from django.contrib.contenttypes.models import ContentType
    from part.models import Part
    part_ct = ContentType.objects.get_for_model(Part)
    if instance.model_type_id != part_ct.pk:
        return  # Not a Part parameter — skip

    part_id = instance.model_id
    template_name = template.name

    refs = find_parameter_references(part_id, template_name)

    if refs:
        lines = []
        product_urls = []
        for ref, field_label, snippet, prod_id in refs:
            lines.append(f'  • {ref} — {field_label}: "{snippet}"')

        seen_pids = set()
        for _, _, _, prod_id in refs:
            if prod_id and prod_id not in seen_pids:
                seen_pids.add(prod_id)
                from part.models import Part as PartModel2
                try:
                    prod = PartModel2.objects.get(pk=prod_id)
                    product_urls.append({
                        'url': f'/parametric-bom/product/{prod_id}/',
                        'name': prod.name,
                        'id': prod_id,
                    })
                except PartModel2.DoesNotExist:
                    pass

        msg = (
            f'无法删除参数「{template_name}」：该参数正在被以下公式引用：\n'
            + '\n'.join(lines)
        )
        if product_urls:
            msg += '\n\n🔗 相关产品配置：'
            for pu in product_urls:
                msg += f'\n  {pu["name"]}: {pu["url"]}'
        msg += '\n\n请先修改或删除相关公式后再执行删除。'

        raise ProtectedError((msg, {'product_urls': product_urls}), [instance])


# ── Variable rename: sync formulas ──


def _get_var_ref_regex(name: str) -> re.Pattern:
    """Build a regex that matches a bare variable name as a standalone identifier.

    Variable names are referenced without a prefix (unlike `param.xxx`).
    Uses lookbehind/lookahead to avoid partial matches inside longer identifiers.
    Example: name='总重量' matches 'CEIL(总重量/500)' but NOT '总重量系数'.
    """
    escaped = re.escape(name)
    return re.compile(
        r'(?<![A-Za-z0-9_\u4e00-\u9fff])' + escaped + r'(?![A-Za-z0-9_\u4e00-\u9fff])'
    )


def rename_variable_in_formulas(old_name: str, new_name: str) -> tuple:
    """Replace all bare ``OLD_NAME`` references with ``NEW_NAME`` across all formula fields.

    Returns (total_updated_count, [field_label × count, ...]).
    """
    from parametric_bom import models as pm

    pattern = _get_var_ref_regex(old_name)

    field_label_map = {
        'qty_formula': '数量公式',
        'name_formula': '名称公式',
        'condition_formula': '条件公式',
        'reference_formula': '备注公式',
        'price_formula': '价格公式',
        'value_formula': '值公式',
        'formula': '公式',
        'drawing_ref_formula': '图纸参考公式',
        'unit_cost_formula': '单位成本公式',
        'variant_name_template': '变体名称模板',
        'variant_ipn_template': '变体IPN模板',
    }

    total_updated = 0
    updated_fields = []

    for model_name, field_name in FORMULA_CHECK_FIELDS:
        try:
            Model = getattr(pm, model_name)
        except AttributeError:
            continue

        # Skip PartVariable's own formula field — self-referencing is invalid
        if model_name == 'PartVariable' and field_name == 'formula':
            continue

        # ── JSON field: VariantMapping.param_mapping ──
        if field_name == 'param_mapping':
            rows = Model.objects.exclude(**{field_name: {}}).exclude(**{field_name: None})
            count = 0
            for row in rows:
                val = getattr(row, field_name, {}) or {}
                if not isinstance(val, dict):
                    continue
                changed = False
                new_dict = {}
                for k, v in val.items():
                    if isinstance(v, str) and old_name in v:
                        new_val = pattern.sub(new_name, v)
                        if new_val != v:
                            new_dict[k] = new_val
                            changed = True
                        else:
                            new_dict[k] = v
                    else:
                        new_dict[k] = v
                if changed:
                    setattr(row, field_name, new_dict)
                    row.save(update_fields=[field_name])
                    count += 1
            if count > 0:
                total_updated += count
                updated_fields.append(f'参数映射×{count}')
            continue

        # ── Standard text field ──
        filter_kwargs = {field_name + '__icontains': old_name}
        rows = Model.objects.filter(**filter_kwargs)

        count = 0
        for row in rows:
            old_val = getattr(row, field_name, '') or ''
            new_val = pattern.sub(new_name, old_val)
            if new_val != old_val:
                setattr(row, field_name, new_val)
                row.save(update_fields=[field_name])
                count += 1

        if count > 0:
            total_updated += count
            label = field_label_map.get(field_name, field_name)
            updated_fields.append(f'{label}×{count}')

    # ── BomSpecification.spec_fields (JSON list) ──
    try:
        from parametric_bom.models import BomSpecification
        specs = BomSpecification.objects.exclude(spec_fields=[]).exclude(spec_fields=None)
        count = 0
        for spec in specs:
            fields = spec.spec_fields or []
            if not isinstance(fields, list):
                continue
            changed = False
            new_fields = []
            for sf in fields:
                if not isinstance(sf, dict):
                    new_fields.append(sf)
                    continue
                formula = sf.get('formula', '') or ''
                if old_name in formula:
                    new_formula = pattern.sub(new_name, formula)
                    if new_formula != formula:
                        sf = {**sf, 'formula': new_formula}
                        changed = True
                new_fields.append(sf)
            if changed:
                spec.spec_fields = new_fields
                spec.save(update_fields=['spec_fields'])
                count += 1
        if count > 0:
            total_updated += count
            updated_fields.append(f'规格字段公式×{count}')
    except Exception:
        pass

    return total_updated, updated_fields


def _on_variable_rename(sender, instance, **kwargs):
    """pre_save handler: auto-update formulas when a PartVariable is renamed."""
    if not instance.pk:
        return

    try:
        old = sender.objects.only('name').get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    old_name = old.name
    new_name = instance.name

    if old_name == new_name:
        return

    count, fields = rename_variable_in_formulas(old_name, new_name)
    if count > 0:
        logger.info(
            'variable_renamed old_name=%r new_name=%r updated=%d fields=%s',
            old_name, new_name, count, fields,
        )


# ── Register signals ──

def connect_signals():
    """Connect signal handlers. Called from AppConfig.ready()."""
    from common.models import Parameter
    from parametric_bom.models import PartVariable
    pre_delete.connect(check_parameter_delete, sender=Parameter, weak=False)
    pre_save.connect(_on_variable_rename, sender=PartVariable, weak=False)
