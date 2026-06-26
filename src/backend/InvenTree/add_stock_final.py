"""
Bulk insert stock items for parts without stock
"""
import os; os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
import django; django.setup()
from django.db import connection
from datetime import datetime

loc_map = {10: 4, 9: 2, 8: 2, 6: 2, 15: 3, 7: 3}

with connection.cursor() as c:
    c.execute('SELECT MAX(tree_id) FROM stock_stockitem')
    max_tree = c.fetchone()[0] or 0
    c.execute('SELECT p.id, COALESCE(p.category_id, 1) FROM part_part p LEFT JOIN stock_stockitem s ON p.id = s.part_id WHERE s.id IS NULL')
    parts_data = c.fetchall()

print(f'Start tree_id: {max_tree + 1}, parts: {len(parts_data)}')

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
BATCH = 200

for i in range(0, len(parts_data), BATCH):
    batch = parts_data[i:i+BATCH]
    value_rows = []
    tid = max_tree + 1 + i
    for pid, cat_id in batch:
        loc_id = loc_map.get(cat_id, 1)
        empty_json = '{}'
        value_rows.append(
            f'(10000, 10, 0, 0, 0, "", "", "", "", {pid}, {loc_id}, 1, 2, {tid}, 0, \'{empty_json}\', "{now}")'
        )
        tid += 1
    
    cols = ('(quantity, status, delete_on_deplete, is_building, serial_int, '
            'barcode_data, barcode_hash, link, batch, part_id, location_id, '
            'lft, rght, tree_id, level, metadata, creation_date)')
    sql = f'INSERT INTO stock_stockitem {cols} VALUES ' + ','.join(value_rows)
    
    try:
        with connection.cursor() as c2:
            c2.execute(sql)
        done = min(i + BATCH, len(parts_data))
        print(f'OK batch {i//BATCH+1}: {done}/{len(parts_data)}')
    except Exception as e:
        print(f'ERR batch {i//BATCH+1}: {e}')
        break

with connection.cursor() as c:
    c.execute('SELECT COUNT(*) FROM stock_stockitem')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM part_part p LEFT JOIN stock_stockitem s ON p.id = s.part_id WHERE s.id IS NULL')
    rem = c.fetchone()[0]
    print(f'\nStockItems: {total}')
    print(f'无库存: {rem}')
    if rem == 0:
        print('全部完成!')
