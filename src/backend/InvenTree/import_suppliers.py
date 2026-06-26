"""
批量导入品牌/供应商/价格数据 v2 - 使用bulk_create
"""
import os, django, re
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()

from decimal import Decimal
from company.models import Company, ManufacturerPart, SupplierPart
from part.models import Part


def parse_desc(desc):
    if not desc:
        return None, None, None
    brand_match = re.search(r'品牌:\s*(\S+)', desc)
    brand = brand_match.group(1) if brand_match else None
    if brand in ('无', '无品牌', '无品牌'):
        brand = None
    price_match = re.search(r'单价:\s*[¥￥]?\s*([0-9.]+)', desc)
    price = Decimal(price_match.group(1)) if price_match else None
    return brand, price, None


parts = list(Part.objects.all().exclude(description__isnull=True).exclude(description=''))
print(f'零件总数: {len(parts)}')

# Collect all data
brand_data = {}  # brand -> list of (part, price)
price_only_parts = []  # parts with price but no brand
company_map = {c.name: c for c in Company.objects.all()}

for p in parts:
    brand, price, _ = parse_desc(p.description)
    if brand:
        if brand not in brand_data:
            brand_data[brand] = []
        brand_data[brand].append((p, price))
    elif price is not None:
        price_only_parts.append((p, price))

print(f'有品牌的零件: {sum(len(v) for v in brand_data.values())}')
print(f'有品牌数量: {len(brand_data)}')
print(f'自制件(有价格无品牌): {len(price_only_parts)}')

# Phase 1: Create ManufacturerParts in bulk
mp_to_create = []
mp_count = 0
existing_mps = set()

for brand, items in brand_data.items():
    company = company_map[brand]
    for p, price in items:
        ipn = (p.IPN or '')[:50]
        mp = ManufacturerPart(
            part=p,
            manufacturer=company,
            MPN=ipn,
            description=f'品牌: {brand}',
        )
        mp_to_create.append(mp)
        mp_count += 1
        
        if len(mp_to_create) >= 500:
            ManufacturerPart.objects.bulk_create(mp_to_create, ignore_conflicts=True)
            print(f'  创建 ManufacturerPart: {mp_count}')
            mp_to_create = []

if mp_to_create:
    ManufacturerPart.objects.bulk_create(mp_to_create, ignore_conflicts=True)
    print(f'  创建 ManufacturerPart: {mp_count}')

# Phase 2: Create SupplierParts + update base_cost in bulk
sp_to_create = []
sp_count = 0
base_cost_updates = []

# Build lookup: (part_id, company_id) -> ManufacturerPart
all_mps = ManufacturerPart.objects.select_related('part', 'manufacturer').all()
mp_lookup = {}
for mp in all_mps:
    mp_lookup[(mp.part_id, mp.manufacturer_id)] = mp

for brand, items in brand_data.items():
    company = company_map[brand]
    for p, price in items:
        if price is not None:
            mp = mp_lookup.get((p.id, company.id))
            if mp:
                ipn = (p.IPN or '')[:50]
                sku = ipn if ipn else p.name[:50]
                sp = SupplierPart(
                    part=p,
                    supplier=company,
                    manufacturer_part=mp,
                    SKU=sku,
                    base_cost=price,
                    active=True,
                    primary=True,
                )
                sp_to_create.append(sp)
                sp_count += 1
                
                # Track base_cost update
                base_cost_updates.append((p.id, price))
        
        if len(sp_to_create) >= 500:
            SupplierPart.objects.bulk_create(sp_to_create, ignore_conflicts=True)
            print(f'  创建 SupplierPart: {sp_count}')
            sp_to_create = []

if sp_to_create:
    SupplierPart.objects.bulk_create(sp_to_create, ignore_conflicts=True)
    print(f'  创建 SupplierPart: {sp_count}')

# Phase 3: Update Part.base_cost in bulk using raw SQL
if base_cost_updates:
    cases = " ".join([f"WHEN {pid} THEN {price}" for pid, price in base_cost_updates])
    ids = ",".join(str(pid) for pid, _ in base_cost_updates)
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE part_part SET base_cost = CASE id {cases} END WHERE id IN ({ids})"
        )
    print(f'  Part.base_cost 更新: {len(base_cost_updates)}')

# Phase 4: Update base_cost for 自制件
if price_only_parts:
    cases = " ".join([f"WHEN {pid} THEN {price}" for pid, price in price_only_parts])
    ids = ",".join(str(pid) for pid, _ in price_only_parts)
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE part_part SET base_cost = CASE id {cases} END WHERE id IN ({ids})"
        )
    print(f'  自制件 base_cost 更新: {len(price_only_parts)}')

# Final summary
print(f'\n=== 最终统计 ===')
print(f'  Companies: {Company.objects.count()}')
print(f'  ManufacturerParts: {ManufacturerPart.objects.count()}')
print(f'  SupplierParts: {SupplierPart.objects.count()}')
print(f'  Parts with base_cost>0: {Part.objects.filter(base_cost__gt=0).count()}')
