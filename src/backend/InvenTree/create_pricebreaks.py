"""
为所有有价格的 SupplierPart 创建 SupplierPriceBreak
"""
import os; os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
import django; django.setup()

from decimal import Decimal
from company.models import SupplierPart, SupplierPriceBreak
from part.models import Part, PartPricing

# Get all SupplierParts with prices that don't have PriceBreaks yet
sps = SupplierPart.objects.filter(base_cost__gt=0)
total = sps.count()

existing_pb_ids = set(SupplierPriceBreak.objects.values_list('part_id', flat=True))
print(f'SupplierParts with base_cost: {total}')
print(f'已有PriceBreak: {len(existing_pb_ids)}')

to_create = []
for sp in sps:
    if sp.id not in existing_pb_ids:
        to_create.append(
            SupplierPriceBreak(
                part=sp,
                quantity=1,
                price=sp.base_cost,
            )
        )

if to_create:
    SupplierPriceBreak.objects.bulk_create(to_create, ignore_conflicts=True)
    print(f'创建了 {len(to_create)} 条 PriceBreak')

# Mark parts as purchaseable
part_ids = list(sps.values_list('part_id', flat=True).distinct())
Part.objects.filter(id__in=part_ids, purchaseable=False).update(purchaseable=True)
print(f'标记 {len(part_ids)} 个零件为可采购')

print(f'\n最终统计:')
print(f'  SupplierPart: {SupplierPart.objects.count()}')
print(f'  SupplierPriceBreak: {SupplierPriceBreak.objects.count()}')
print(f'  Part购买: {Part.objects.filter(purchaseable=True).count()}')
