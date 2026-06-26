"""
批量触发所有有SupplierPart的零件的定价缓存更新
"""
import os; os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
import django; django.setup()
from part.models import Part, PartPricing
from company.models import SupplierPart

part_ids = list(SupplierPart.objects.values_list('part_id', flat=True).distinct())
print('需要更新定价的零件:', len(part_ids))

updated = 0
for pid in part_ids:
    try:
        pricing = PartPricing.objects.get(part_id=pid)
    except PartPricing.DoesNotExist:
        try:
            pricing = PartPricing.objects.create(part_id=pid)
        except:
            continue
    try:
        pricing.update_pricing(cascade=False)
        updated += 1
        if updated % 100 == 0:
            print('已更新:', updated, '/', len(part_ids))
    except:
        pass

print('更新完成:', updated, '个零件')

# Verify
print('\n验证:')
test_ids = [2153, 2342, 2015, 709, 508, 2130]
for pid in test_ids:
    p = Part.objects.get(id=pid)
    pricing = PartPricing.objects.get(part=p)
    sup = str(pricing.supplier_price_min or '-')
    ovr = str(pricing.overall_min or '-')
    print(f'  {p.name[:35]:35s} supplier_min={sup:>8s} overall_min={ovr:>8s}')
