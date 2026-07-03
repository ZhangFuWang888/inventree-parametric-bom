"""Create a parametric shelf (参数化货架) BOM demo.

Creates a shelf system with:
- 7 parameters: L (length), W (width), H (height), N (shelves), Color, C (columns), 立柱类型 (column type)
- 6 sub-parts: 立柱, 横梁, 层板, 背板, 连接件, 脚杯 (立柱/横梁/层板/背板 as template parts)
- 6 BOM items with quantity formulas using N and C
- VariantMappings for 立柱/横梁/层板/背板 (IPNs include size info: LX-BEAM-W600, LX-SHELF-L1200-W600, etc.)
- Candidate parts for column type selection (标准立柱 / 重型立柱50*80)

Run: python3 scripts/create_shelf.py
"""
import os, sys

_inventree_path = os.path.join(os.path.dirname(__file__), '..', '..', 'InvenTree')
if _inventree_path not in sys.path:
    sys.path.insert(0, _inventree_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
django.setup()

from decimal import Decimal
from django.db import transaction
from part.models import Part, PartCategory, BomItem
from parametric_bom.models import PartParameterConfig, ParametricBomItem, BomCandidatePart


def get_or_create_part(name, IPN='', category=None, is_template=False,
                       assembly=False, component=True, description='', units='pcs'):
    """Find or create a Part."""
    existing = Part.objects.filter(name=name, category=category).first()
    if existing:
        print(f'  使用已有: {name} (PK={existing.pk})')
        return existing
    p = Part.objects.create(
        name=name, IPN=IPN, category=category,
        is_template=is_template, assembly=assembly,
        component=component, purchaseable=True, salable=True,
        active=True, units=units, description=description,
    )
    print(f'  ✅ 创建: {name} (PK={p.pk}, IPN={IPN})')
    return p


def upsert_param_config(part, name, param_type, default_value, options=None,
                        min_val=None, max_val=None, step=1, hint='',
                        display_order=99, driving=True):
    """Create or update a PartParameterConfig."""
    cfg, created = PartParameterConfig.objects.update_or_create(
        part=part, name=name,
        defaults={
            'parameter_type': param_type,
            'default_value': str(default_value),
            'options': options,
            'min_value': Decimal(str(min_val)) if min_val is not None else None,
            'max_value': Decimal(str(max_val)) if max_val is not None else None,
            'step_value': Decimal(str(step)),
            'is_driving': driving,
            'is_computed': False,
            'computation_formula': '',
            'ui_hint': hint,
            'display_order': display_order,
            'visible_on_config': True,
        }
    )
    status = '✅ 创建' if created else '📌 已存在'
    print(f'  {status}: {name} ({param_type}) = {default_value} | order={display_order}')
    return cfg


def upsert_bom_config(product, sub_part, default_qty, qty_formula='',
                      enable_candidate=False):
    """Create BomItem + ParametricBomItem for a sub-part."""
    bi, created = BomItem.objects.get_or_create(
        part=product, sub_part=sub_part,
        defaults={
            'quantity': Decimal(str(default_qty)),
            'allow_variants': True,
        }
    )
    if not created:
        bi.quantity = Decimal(str(default_qty))
        bi.save(update_fields=['quantity'])
    
    pbi, _ = ParametricBomItem.objects.update_or_create(
        bom_item=bi,
        defaults={
            'enable_qty_formula': bool(qty_formula),
            'qty_formula': qty_formula,
            'enable_conditional': False,
            'condition_formula': '',
            'enable_candidate': enable_candidate,
            'enable_variant': False,
            'enable_specification': False,
            'enable_structure': False,
            'reference_formula': '',
            'param_mapping': {},
        }
    )
    status = '✅ 创建' if created else '📌 已存在'
    qty_info = f'qty_formula={qty_formula}' if qty_formula else f'default_qty={default_qty}'
    print(f'  {status}: BOM {bi.pk} | {sub_part.name:<12} | {qty_info}')
    return pbi


@transaction.atomic
def create_shelf_demo():
    print('=' * 60)
    print('创建 参数化货架 演示数据')
    print('=' * 60)
    
    # Get/create category
    cat, _ = PartCategory.objects.get_or_create(
        name='货架类',
        defaults={'description': '货架、货架系统等结构件'}
    )
    if _:
        print(f'✅ 创建分类: 货架类 (PK={cat.pk})')
    else:
        print(f'📌 使用已有分类: 货架类 (PK={cat.pk})')
    
    # Sub-parts
    sub_parts = [
        ('货架立柱', 'LX-COLUMN', '货架立柱，用于支撑货架结构', cat),
        ('货架横梁', 'LX-BEAM', '货架横梁，连接立柱', cat),
        ('货架层板', 'LX-SHELF', '货架层板，放置物品', cat),
        ('货架背板', 'LX-BACK', '货架背板，防护和美观', cat),
        ('货架连接件', 'LX-CONN', '货架连接件，连接立柱与横梁', cat),
        ('货架脚杯', 'LX-FOOT', '货架脚杯，调节高度和保护地面', cat),
    ]
    
    parts = {}
    for name, ipn, desc, category in sub_parts:
        p = get_or_create_part(name, IPN=ipn, category=category, description=desc)
        parts[name] = p
    
    # Create a heavy column variant too
    heavy_col = get_or_create_part(
        '货架立柱50*80', IPN='LX-300', category=cat,
        description='重型立柱50*80mm，适用于重型货架',
        is_template=False, component=True,
    )
    
    # Create template product
    product = get_or_create_part(
        '参数化货架', IPN='LX-SHELF-SYS', category=cat,
        description='参数化货架系统，支持长度/宽度/高度/层数/列数配置',
        is_template=True, assembly=True, component=False,
    )
    
    # Parameters (order matters!)
    print(f'\n--- 参数定义 ---')
    upsert_param_config(product, 'L', 'number', '1200',
                        min_val=600, max_val=3000, step=100,
                        hint='货架长度(mm)', display_order=1)
    upsert_param_config(product, 'W', 'option', '600',
                        options=['400', '500', '600', '800', '1000'],
                        hint='货架宽度(mm)', display_order=2)
    upsert_param_config(product, 'H', 'number', '2000',
                        min_val=1000, max_val=4000, step=100,
                        hint='货架高度(mm)', display_order=3)
    upsert_param_config(product, 'N', 'option', '3',
                        options=['1', '2', '3', '4', '5'],
                        hint='层数', display_order=4)
    upsert_param_config(product, 'Color', 'option', '白色',
                        options=['白色', '灰色', '蓝色', '橘色'],
                        hint='颜色', display_order=5)
    upsert_param_config(product, 'C', 'option', '1',
                        options=['1', '2', '3', '4'],
                        hint='货架列数', display_order=6)
    upsert_param_config(product, '立柱类型', 'option', '标准立柱',
                        options=['标准立柱', '重型立柱(50*80)'],
                        hint='立柱类型', display_order=7)
    
    # BOM items
    print(f'\n--- BOM公式 ---')
    pbi_column = upsert_bom_config(
        product, parts['货架立柱'], default_qty=4,
        qty_formula='(param.C + 1) * 2',
        enable_candidate=True,
    )
    upsert_bom_config(product, parts['货架横梁'], default_qty=2,
                      qty_formula='param.N * 2 * param.C')
    upsert_bom_config(product, parts['货架层板'], default_qty=1,
                      qty_formula='param.N * param.C')
    upsert_bom_config(product, parts['货架背板'], default_qty=1,
                      qty_formula='param.N * param.C')
    upsert_bom_config(product, parts['货架连接件'], default_qty=8,
                      qty_formula='param.N * 4 * param.C + 4')
    upsert_bom_config(product, parts['货架脚杯'], default_qty=4,
                      qty_formula='(param.C + 1) * 2')
    
    # Candidate parts for columns
    print(f'\n--- 候选零件(立柱) ---')
    cand_std, _ = BomCandidatePart.objects.update_or_create(
        parametric_bom_item=pbi_column,
        part=parts['货架立柱'],
        defaults={
            'label': '标准立柱',
            'condition_formula': 'param.立柱类型 = "标准立柱"',
            'priority': 10,
        }
    )
    print(f'  ✅ 候选: 标准立柱 → 货架立柱 (priority=10)')
    
    cand_hvy, _ = BomCandidatePart.objects.update_or_create(
        parametric_bom_item=pbi_column,
        part=heavy_col,
        defaults={
            'label': '重型立柱(50*80)',
            'condition_formula': 'param.立柱类型 = "重型立柱(50*80)"',
            'priority': 20,
        }
    )
    print(f'  ✅ 候选: 重型立柱 → 货架立柱50*80 (priority=20)')
    
    # ── Template parts: 使子件可生成变体（型号含尺寸） ──
    print(f'\n--- 模板零件设置 ---')
    from parametric_bom.models import VariantMapping
    
    template_parts = [parts['货架立柱'], parts['货架横梁'], parts['货架层板'], parts['货架背板']]
    for tp in template_parts:
        if not tp.is_template:
            tp.is_template = True
            tp.save(update_fields=['is_template'])
            print(f'  ✅ {tp.name} → is_template=True')
    
    # 为模板子件添加参数
    print(f'\n--- 模板参数 ---')
    PartParameterConfig.objects.update_or_create(
        part=parts['货架横梁'], name='W',
        defaults={'parameter_type':'option','options':['400','500','600','800','1000'],
                  'default_value':'600','step_value':Decimal('1'),
                  'is_driving':True,'is_computed':False,'ui_hint':'横梁长度=货架宽度',
                  'display_order':1,'visible_on_config':False})
    for pname, pnames in [('货架层板', ['长度','宽度']), ('货架背板', ['长度','高度'])]:
        for pn in pnames:
            opts = {'长度':['600','800','1000','1200','1500','1800','2000','2500','3000'],
                    '宽度':['400','500','600','800','1000'],
                    '高度':['1000','1200','1400','1600','1800','2000','2500','3000','3500','4000']}
            PartParameterConfig.objects.update_or_create(
                part=parts[pname], name=pn,
                defaults={'parameter_type':'option','options':opts[pn],
                          'default_value':opts[pn][0],'step_value':Decimal('1'),
                          'is_driving':True,'is_computed':False,
                          'ui_hint':f'{pname}{pn}','display_order':1,'visible_on_config':False})
            print(f'  ✅ {pname}: {pn}参数')
    PartParameterConfig.objects.update_or_create(
        part=parts['货架立柱'], name='H',
        defaults={'parameter_type':'option','options':['1000','1200','1400','1600','1800','2000','2500','3000','3500','4000'],
                  'default_value':'2000','step_value':Decimal('1'),
                  'is_driving':True,'is_computed':False,'ui_hint':'立柱高度',
                  'display_order':1,'visible_on_config':False})
    print(f'  ✅ 货架立柱: H参数')
    
    # ── VariantMappings（型号含尺寸） ──
    print(f'\n--- 变体映射(VariantMapping) ---')
    vms = [
        (pbi_column, parts['货架立柱'],
         'IF(param.立柱类型="标准立柱", "LX-COLUMN-H"+STR(INT(param.H)), "LX-300-H"+STR(INT(param.H)))',
         'IF(param.立柱类型="标准立柱", "立柱-H"+STR(INT(param.H)), "重型立柱-H"+STR(INT(param.H)))',
         {'H': 'param.H'}),
        (ParametricBomItem.objects.get(bom_item__part=product, bom_item__sub_part=parts['货架横梁']), parts['货架横梁'],
         '"LX-BEAM-W"+STR(INT(param.W))',
         '"横梁(W="+STR(INT(param.W))+")"',
         {'W': 'param.W'}),
        (ParametricBomItem.objects.get(bom_item__part=product, bom_item__sub_part=parts['货架层板']), parts['货架层板'],
         '"LX-SHELF-L"+STR(INT(param.L))+"-W"+STR(INT(param.W))',
         '"层板(L="+STR(INT(param.L))+" W="+STR(INT(param.W))+")"',
         {'长度': 'param.L', '宽度': 'param.W'}),
        (ParametricBomItem.objects.get(bom_item__part=product, bom_item__sub_part=parts['货架背板']), parts['货架背板'],
         '"LX-BACK-L"+STR(INT(param.L))+"-H"+STR(INT(param.H))',
         '"背板(L="+STR(INT(param.L))+" H="+STR(INT(param.H))+")"',
         {'长度': 'param.L', '高度': 'param.H'}),
    ]
    for pbi, tpl_part, ipn_tpl, name_tpl, pmap in vms:
        pbi.enable_variant = True
        pbi.save(update_fields=['enable_variant'])
        VariantMapping.objects.update_or_create(
            parametric_bom_item=pbi,
            defaults={'template_part': tpl_part, 'param_mapping': pmap,
                      'variant_name_template': name_tpl, 'variant_ipn_template': ipn_tpl})
        print(f'  ✅ {tpl_part.name}: {ipn_tpl}')
    
    print(f'\n{"=" * 60}')
    print(f'✅ 完成！货架参数化BOM数据创建成功！')
    print(f'产品PK: {product.pk}')
    print(f'分类PK: {cat.pk}')
    print(f'BOM配置数: {ParametricBomItem.objects.filter(bom_item__part=product).count()}')
    print(f'参数数: {PartParameterConfig.objects.filter(part=product).count()}')
    print(f'打开配置器: /parametric-bom/')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    create_shelf_demo()
