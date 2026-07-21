"""Signal handlers for Parametric BOM.

Prevents deletion of PartParameters (InvenTree Parameter) that are
referenced by parametric BOM formulas.
"""

import re
from django.db.models.signals import pre_delete
from django.dispatch import receiver


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
    ('PartParameterConfig', 'computation_formula'),
    # ParametricBomItem
    ('ParametricBomItem', 'qty_formula'),
    ('ParametricBomItem', 'name_formula'),
    ('ParametricBomItem', 'condition_formula'),
    ('ParametricBomItem', 'reference_formula'),
    ('ParametricBomItem', 'price_formula'),
    # ParametricRule
    ('ParametricRule', 'condition_formula'),
    ('ParametricRule', 'value_formula'),
    # BomSpecification
    ('BomSpecification', 'condition_formula'),
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
        'computation_formula': '计算公式',
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


# ── Register signals ──

def connect_signals():
    """Connect signal handlers. Called from AppConfig.ready()."""
    from common.models import Parameter
    pre_delete.connect(check_parameter_delete, sender=Parameter, weak=False)
