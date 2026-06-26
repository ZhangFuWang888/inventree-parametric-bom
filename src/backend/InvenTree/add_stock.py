"""
为所有零件添加库存（每个零件1件）- MPTT兼容版
"""
import os; os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
import django; django.setup()

from decimal import Decimal
from stock.models import StockItem, StockLocation
from part.models import Part

LOCATION_MAP = {
    10: 4,   # 电气类 → 电子料区
    9: 2,    # 标准件 → 原料区
    8: 2,    # 驱动类 → 原料区
    6: 2,    # 辊道类 → 原料区
    15: 3,   # 箱式输送物料 → 成品区
    7: 3,    # 机架类 → 成品区
}

existing_ids = set(StockItem.objects.values_list('part_id', flat=True))
parts = Part.objects.exclude(id__in=existing_ids)
total = parts.count()
print(f'已有库存: {len(existing_ids)}，需要创建: {total}')

created = 0
stats = {}
errors = []

for p in parts:
    cat_id = p.category_id if p.category else None
    loc_id = LOCATION_MAP.get(cat_id, 1)
    
    try:
        StockItem.objects.create(
            part=p,
            quantity=Decimal('1'),
            location_id=loc_id,
            status=10,
            delete_on_deplete=False,
        )
        created += 1
        cat_name = p.category.name if p.category else '未分类'
        stats[cat_name] = stats.get(cat_name, 0) + 1
    except Exception as e:
        errors.append((p.id, p.name, str(e)))
    
    if created % 300 == 0:
        print(f'  已创建: {created}/{total}')

print(f'\n创建完成: {created} 个库存记录')
print(f'总库存: {StockItem.objects.count()}')

if errors:
    print(f'\n错误 ({len(errors)}):')
    for pid, pname, err in errors[:5]:
        print(f'  Part {pid} {pname[:30]}: {err}')

print('\n各分类:')
for cat_name, cnt in sorted(stats.items(), key=lambda x: -x[1]):
    print(f'  {cat_name}: {cnt}')
