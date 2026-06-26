"""
分析零件描述中的品牌和价格信息
"""
import os, django, re
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()

from part.models import Part
from collections import Counter

parts = Part.objects.all().exclude(description__isnull=True).exclude(description='')
total = Part.objects.count()
has_desc = parts.count()

brand_parts = 0
price_parts = 0
brands = Counter()
price_parts_list = []

for p in parts:
    desc = p.description or ''
    
    # Extract brand
    brand_match = re.search(r'品牌:\s*(\S+)', desc)
    price_match = re.search(r'单价:\s*[¥￥]?([0-9.]+)', desc)
    note_match = re.search(r'备注:\s*([^|]+)', desc)
    
    brand = brand_match.group(1) if brand_match else None
    price = float(price_match.group(1)) if price_match else None
    
    if brand and brand != '无':
        brand_parts += 1
        brands[brand] += 1
    
    if price:
        price_parts += 1
        price_parts_list.append((p.id, p.name, (p.IPN or ''), brand, price, desc[:80]))

print(f'零件总数: {total}')
print(f'有描述的零件: {has_desc}')
print(f'有品牌的零件: {brand_parts}')
print(f'有价格的零件: {price_parts}')

print('\n=== 品牌分布（按数量降序）===')
for b, cnt in brands.most_common():
    print(f'  {b}: {cnt} 个零件')

print(f'\n=== 有价格的零件示例（前30个）===')
for pid, pname, pipn, brand, price, desc in price_parts_list[:30]:
    b = str(brand or '无')
    print(f'  ID:{pid} {pipn} {pname[:30]:30s} 品牌:{b:10s} ¥{price}')
print(f'  ... 共 {len(price_parts_list)} 个有价格')
