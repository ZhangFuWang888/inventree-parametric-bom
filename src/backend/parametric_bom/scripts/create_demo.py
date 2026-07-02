"""Create a straight roller conveyor (直线辊道机) parametric BOM demo."""
import os, sys, django

_inventree_path = os.path.join(os.path.dirname(__file__), '..', '..', 'InvenTree')
if _inventree_path not in sys.path:
    sys.path.insert(0, _inventree_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
django.setup()

from django.db import transaction
from part.models import Part, PartCategory, BomItem
from parametric_bom.models import (
    PartParameterConfig, ParametricBomItem, PartVariable,
    VariantMapping, BomCandidatePart,
)
from parametric_bom.formula_engine import evaluate as eval_formula

cat = PartCategory.objects.get(pk=23)  # 直线辊道机-参数化

# ============ Part Templates (子件模板) ============
def get_or_create_part(name, IPN='', category=None, is_template=False,
                       assembly=False, component=True, virtual=False,
                       description='', units=''):
    existing = Part.objects.filter(name=name, category=category).first()
    if existing:
        print(f'  使用已有: {name} (PK={existing.pk})')
        return existing
    p = Part.objects.create(
        name=name, IPN=IPN, category=category,
        is_template=is_template, assembly=assembly, component=component,
        virtual=virtual, description=description or name, units=units,
    )
    print(f'  创建: {name} (PK={p.pk})')
    return p

ji_jia_cat = PartCategory.objects.get(pk=7)
gun_dao_cat = PartCategory.objects.get(pk=6)
qu_dong_cat = PartCategory.objects.get(pk=8)
biao_zhun_cat = PartCategory.objects.get(pk=9)

print('=== 子件 ===')
ji_jia = get_or_create_part('直线辊道机架体', 'GD-FRAME', ji_jia_cat,
    assembly=True, description='直线辊道机焊接机架主体')
ce_ban_tpl = get_or_create_part('辊道机侧板(模板)', 'GD-SIDE-TPL', ji_jia_cat,
    is_template=True, description='辊道机侧板模板（按长度派生变体）')
gun_tong_tpl = get_or_create_part('直辊筒(模板)', 'GD-ROLLER-TPL', gun_dao_cat,
    is_template=True, description='直辊筒模板（按宽度派生变体）')
zhi_tui = get_or_create_part('辊道机可调支腿', 'GD-LEG', ji_jia_cat,
    description='辊道机可调高度支腿')
qu_dong = get_or_create_part('辊道机驱动总成', 'GD-DRIVE', qu_dong_cat,
    assembly=True, description='辊道机驱动总成（含电机减速机）')
lian_jie = get_or_create_part('辊道机连接件套件', 'GD-JOINT', biao_zhun_cat,
    description='辊道机安装连接件（含螺栓垫圈）')

# ============ Main Product ============
product, created = Part.objects.get_or_create(
    name='直线辊道机 (参数化demo)', category=cat,
    defaults=dict(
        IPN='GD-301',
        assembly=True, component=True,
        description='参数化直线辊道机 - 通过L/W/P参数驱动BOM展开',
    ),
)
pid = product.pk
print(f'\n产品: {product.name} (PK={pid})')

# ============ Clean old data ============
PartParameterConfig.objects.filter(part=product).delete()
PartVariable.objects.filter(part=product).delete()
ParametricBomItem.objects.filter(bom_item__part=product).delete()
BomItem.objects.filter(part=product).delete()
VariantMapping.objects.filter(parametric_bom_item__bom_item__part=product).delete()

# ============ Parameters ============
print('\n=== 参数 ===')
params = [
    dict(name='L', parameter_type='number', default_value='3000',
         min_value='1000', max_value='6000', step_value='100',
         ui_hint='mm', is_driving=True, display_order=1),
    dict(name='W', parameter_type='option', default_value='500',
         options=['400','500','600','800','1000'],
         ui_hint='mm', is_driving=True, display_order=2),
    dict(name='P', parameter_type='option', default_value='120',
         options=['75','100','120','150','200'],
         ui_hint='mm', is_driving=True, display_order=3),
    dict(name='V', parameter_type='number', default_value='15',
         min_value='5', max_value='30', step_value='5',
         ui_hint='m/min', is_driving=True, display_order=4),
]
param_configs = {}
for pd in params:
    cfg = PartParameterConfig.objects.create(part=product, **pd)
    param_configs[cfg.name] = cfg
    print(f'  {cfg.name} = {cfg.default_value} ({cfg.parameter_type})')

# ============ Variables (documentation + used by formulas) ============
print('\n=== 变量 ===')
variables = [
    dict(name='N', formula='CEIL(param.L / param.P) + 1',
         description='辊子数量'),
    dict(name='机架长度', formula='param.L - 60',
         description='机架有效长度(mm)'),
    dict(name='支腿数量', formula='FLOOR(param.L / 1500) * 2 + 2',
         description='支腿组数'),
]
for vd in variables:
    v = PartVariable.objects.create(part=product, **vd)
    print(f'  {v.name} = {v.formula}')

# ============ BOM Items with inline formulas ============
print('\n=== BOM项 ===')

# --- 1) 机架主体 (static x 1) ---
bi = BomItem.objects.create(part=product, sub_part=ji_jia, quantity=1)
ParametricBomItem.objects.create(
    bom_item=bi,
    reference_formula='"L=" + param.L + "mm"',
)
print(f'  机架主体 × 1 [{bi.sub_part.name}]')

# --- 2) 侧板 (static qty=2, variant by length) ---
bi = BomItem.objects.create(part=product, sub_part=ce_ban_tpl, quantity=2)
pbi = ParametricBomItem.objects.create(
    bom_item=bi, enable_variant=True,
    reference_formula='(param.L-60) + "mm"',
)
VariantMapping.objects.create(
    parametric_bom_item=pbi, template_part=ce_ban_tpl,
    param_mapping={},
    variant_name_template='"侧板-" + (param.L - 60)',
    variant_ipn_template='"GD-SIDE-" + (param.L - 60)',
)
print(f'  侧板(变体) × 2 [机架长度: param.L-60]')

# --- 3) 辊筒 (qty = CEIL(L/P)+1, variant by width) ---
bi = BomItem.objects.create(part=product, sub_part=gun_tong_tpl, quantity=1)
pbi = ParametricBomItem.objects.create(
    bom_item=bi, enable_qty_formula=True,
    qty_formula='CEIL(param.L / param.P) + 1',
    enable_variant=True,
    reference_formula='"P=" + param.P',
)
VariantMapping.objects.create(
    parametric_bom_item=pbi, template_part=gun_tong_tpl,
    param_mapping={},
    variant_name_template='"辊筒-W" + param.W',
    variant_ipn_template='"GD-ROLLER-" + param.W',
)
print(f'  辊筒(变体) × [CEIL(L/P)+1] 变体名: 辊筒-W+W')

# --- 4) 支腿 (qty = FLOOR(L/1500)*2+2) ---
bi = BomItem.objects.create(part=product, sub_part=zhi_tui, quantity=1)
ParametricBomItem.objects.create(
    bom_item=bi, enable_qty_formula=True,
    qty_formula='FLOOR(param.L / 1500) * 2 + 2',
)
print(f'  支腿 × [FLOOR(L/1500)*2+2]')

# --- 5) 驱动总成 (static x 1) ---
bi = BomItem.objects.create(part=product, sub_part=qu_dong, quantity=1)
ParametricBomItem.objects.create(
    bom_item=bi,
    reference_formula='param.V + "m/min"',
)
print(f'  驱动总成 × 1 [V: param.V m/min]')

# --- 6) 连接件 (qty = N*2) ---
bi = BomItem.objects.create(part=product, sub_part=lian_jie, quantity=1)
ParametricBomItem.objects.create(
    bom_item=bi, enable_qty_formula=True,
    qty_formula='(CEIL(param.L / param.P) + 1) * 2',
)
print(f'  连接件 × [(CEIL(L/P)+1)*2]')

# ============ Verify ============
print('\n=== 公式验证 ===')
test_params = {'param': {'L': 3000, 'W': 500, 'P': 120, 'V': 15}}
for v in PartVariable.objects.filter(part=product).order_by('display_order', 'pk'):
    try:
        r = eval_formula(v.formula, context=test_params)
        print(f'  ✓ {v.name} = {v.formula} → {r}')
    except Exception as e:
        print(f'  ✗ {v.name} = {v.formula} → {e}')

# Test BOM formulas
bom_tests = [
    ('CEIL(param.L / param.P) + 1', '辊筒数量', 3000, 120),
    ('FLOOR(param.L / 1500) * 2 + 2', '支腿数量', 3000, None),
    ('(CEIL(param.L / param.P) + 1) * 2', '连接件数量', 3000, 120),
    ('"侧板-" + (param.L - 60)', '侧板变体名', 2000, None),
]
for formula, label, L_val, P_val in bom_tests:
    ctx = {'param': {'L': L_val, 'P': P_val or 120, 'W': 500, 'V': 15}}
    try:
        r = eval_formula(formula, context=ctx)
        print(f'  ✓ {label}: {formula} → {r}')
    except Exception as e:
        print(f'  ✗ {label}: {formula} → {e}')

print('\n✅ Demo 完成!')
print(f'  产品: {product.name} (PK={pid})')
print(f'  参数: {PartParameterConfig.objects.filter(part=product).count()} 个')
print(f'  变量: {PartVariable.objects.filter(part=product).count()} 个')
print(f'  BOM项: {BomItem.objects.filter(part=product).count()} 项')
