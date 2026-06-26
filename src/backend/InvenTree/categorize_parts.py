"""
分类剩余147个未分类零件
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()

from django.db import connection
from part.models import Part, PartCategory

def classify(p):
    name = p.name
    ipn = (p.IPN or '')
    desc = (p.description or '')

    # 标准件 (ID: 9)
    if ipn.startswith('GB/') or ipn.startswith('DIN') or ipn.startswith('JB/'): return 9
    if '宁波宁力' in desc: return 9
    if '标准件' in desc: return 9
    if name.startswith('T型螺栓') or name.startswith('膨胀螺栓'): return 9
    if '压铆螺柱' in name or '组合螺钉' in name: return 9
    if name.startswith('内六角') or name.startswith('十字槽'): return 9
    if name.startswith('六角头') or name.startswith('六角法兰') or name.startswith('六角螺母') or name.startswith('六角薄'): return 9
    if '垫圈' in name or '自锁' in name or '紧定螺钉' in name: return 9
    if '圆柱头螺钉' in name or '沉头螺钉' in name or '盘头螺钉' in name: return 9
    if '内锯齿锁紧' in name or '钢制双叠自锁' in name: return 9
    if '内六角平圆头' in name or '内六角圆柱头' in name or '内六角沉头' in name: return 9
    if '弹簧' in name and ('色' in name and '模具' in name): return 9
    if '橡胶脚垫' in name: return 9
    if 'ISOFLEX' in name or '润滑脂' in name or '黄油' in name: return 9
    if '搭扣' in name: return 9

    # 电气类 (ID: 10)
    if '伺服驱动器' in name or ('驱动器' in name and '安装' not in name): return 10
    if '上海步科' in desc: return 10
    if '线缆' in name or '电缆' in name: return 10
    if '集电器' in name: return 10
    if '接近开关' in name: return 10
    if '扫码器' in name: return 10
    if '扭矩铰链' in name: return 10
    if '拖链' in name: return 10
    if '过线保护管' in name: return 10
    if '光电检测板' in name or '光电安装板' in name: return 10
    if '驱动器安装板' in name: return 10
    if '施耐德' in desc: return 10
    if '伺服电机' in name or '微型总线伺服' in name: return 10
    if '电机' in name and ('步科' in desc or '德晟' in desc): return 10
    if '通用光电支架' in name: return 10
    if '传感器' in name: return 10
    # NEW
    if '可调光电' in name: return 10
    if '旋转电机护罩' in name: return 10
    if '检测板' in name and '光电' not in name: return 10
    if '超界光电支架' in name: return 10
    if '站台超界光电支架' in name: return 10
    if '线槽' in name: return 10  # cable troughs
    if '电机护罩' in name or '电机端护罩' in name: return 10
    if '站台接线安装盒' in name or '站台接线安装罩' in name: return 10
    if '光电连接杆' in name or '光电镜反板' in name: return 10

    # 驱动类 (ID: 8)
    if '伸叉' in name or '伸缩同步带' in name: return 8
    if '驱动轴' in name: return 8
    if '麦克' in name: return 8
    if '多楔带轮' in name or '斜轮圆带轮' in name: return 8
    if '六角轴' in name: return 8
    if '减速机' in name: return 8
    if '万向伸缩联轴器' in name or '联轴器' in name: return 8
    if '外叉板' in name or '内叉板' in name or '上叉臂' in name or '下叉臂' in name: return 8
    if '拉模' in name: return 8
    if '滚珠花键' in name: return 8
    if '直线滑轨' in name: return 8
    if '直线轴承' in name: return 8
    if '轴支架' in name: return 8
    if '通用伸叉轴承座' in name: return 8
    if '主动带轮' in name or '从动带轮' in name: return 8
    if '轴承座' in name and ('伸叉' in name or '驱动' in name): return 8
    # NEW
    if '内叉扣板' in name or '外叉板' in name: return 8
    if '差动' in name and ('带轮' in name or '轴' in name): return 8  # differential pulleys
    if '带轮固定座' in name or '带轮连轴座' in name: return 8
    if '灵动带轮轴' in name: return 8
    if '行走' in name and ('电机' in name or '带轮' in name or '传动' in name or '叉臂' in name or '橡胶垫' in name or '轴' in name): return 8
    if '花键' in name: return 8
    if '空心光轴' in name: return 8  # hollow shafts for fork mechanism
    if '法兰轴套' in name: return 8
    if '差动光带轮' in name: return 8

    # 机架类 (ID: 7)
    if '支腿' in name and '加强' not in name and '输送' not in name and '支撑' not in name: return 7
    if '输送横撑' in name: return 7
    if '支腿斜拉' in name or '支腿横撑' in name: return 7
    if '输送支腿' in name: return 7
    if '支腿安装块' in name or '支腿支撑条' in name or '支腿上支撑条' in name or '支腿侧装条' in name: return 7
    if '加强筋' in name: return 7
    if '立柱' in name or '层板' in name: return 7
    if name == '加强筋 (示例)': return 7
    if '输送地脚' in name: return 7
    if name == '支腿斜拉座': return 7
    # NEW
    if '横撑连接件' in name or '槽条连接件' in name: return 7

    # 辊道类 (ID: 6)
    if '辊筒' in name: return 6
    if '侧护板' in name: return 6
    if '导向杆' in name and '输送' not in name: return 6
    if '福来轮' in name: return 6
    if '圆带' in name: return 6
    if '多楔带' in name: return 6
    if '同步带' in name: return 6
    if '平皮带' in name: return 6
    if '通用站台衬板' in name: return 6
    if '直角对接' in name or '转弯辊道对接板' in name: return 6
    if '直线辊道' in name: return 6
    if '从动轮' in name or '从动轮支撑座' in name: return 8
    if '导向' in name and ('夹紧' in name or '支撑' in name or '轮' in name or '板' in name): return 6
    if '包胶' in name and ('斜轮' in name or '行走轮' in name or '轮' in name): return 6
    if '行走轮' in name and '包胶' not in name: return 15
    if '端盖' in name: return 6
    if '轴承座' in name: return 6
    if '隔套' in name or '套环' in name or '固定环' in name: return 6
    if '挡轴' in name: return 6
    if '防撞垫' in name: return 6
    if '导向板' in name: return 6
    if '外罩' in name: return 6
    if '对接衬板' in name: return 6
    if '张紧板' in name: return 6
    if '安装板' in name and '麦克' not in name and '驱动器' not in name and '从动' not in name and '扫码' not in name and '光电' not in name: return 6
    if '固定板' in name and '从动' not in name and '麦克' not in name and '光电' not in name and '驱动器' not in name: return 6
    if '安装座' in name and '扫码' not in name: return 6
    if '型材' in name: return 6
    if '底板' in name: return 6
    if '支撑' in name and '导向支撑杆' not in name: return 6
    if '支架' in name and '光电' not in name and '扫码' not in name: return 6
    # NEW
    if '斜轮' in name: return 6  # angled wheel parts
    if '辊道末端挡板' in name: return 6
    if '转弯辊道对接板' in name: return 6
    if '可调导向支座' in name or '固定导向支座' in name: return 6
    if '导入端头' in name or '导向对接接头' in name: return 6

    # 箱式输送物料 (ID: 15)
    if '弯侧边' in name or '内弯侧边' in name: return 15
    if '输送侧边' in name: return 15
    if '安邦得' in desc: return 15
    if '加强输送地脚' in name: return 15
    if '输送导向杆' in name or '输送通用导向杆' in name: return 15
    if '导向支撑杆' in name: return 15
    if '多层支腿支架' in name: return 15
    if '压块' in name or '压板' in name: return 15
    if '导向夹紧片' in name: return 15
    if '辊道固定板' in name or ('固定板' in name and '125' in name): return 15
    if ipn.startswith('10555') or '105550' in ipn: return 15
    if '125辊道固定板' in name or '125外弯' in name or '125内弯' in name: return 15
    if '从动安装板' in name: return 15
    if '六角端头安装座' in name: return 15
    # NEW
    if '斜口侧边' in name: return 15  # 斜口侧边 = angled side, similar to 弯侧边
    if '站台' in name: return 15  # platform/station parts for conveyor
    if '行走橡胶垫' in name: return 15

    return None

# Collect
uncat = list(Part.objects.filter(category__isnull=True).only('id', 'name', 'IPN', 'description'))
total = len(uncat)
print(f'剩余未分类: {total}')

part_cats = {}
unclassified = []
for p in uncat:
    cid = classify(p)
    if cid:
        part_cats[p.id] = cid
    else:
        unclassified.append((p.id, p.name, (p.IPN or '')))

print(f'本次已分类: {len(part_cats)}')
print(f'仍未分类: {len(unclassified)}')

# Bulk update
if part_cats:
    cases = " ".join([f"WHEN {pid} THEN {cid}" for pid, cid in part_cats.items()])
    ids = ",".join(str(pid) for pid in part_cats.keys())
    sql = f"UPDATE part_part SET category_id = CASE id {cases} END WHERE id IN ({ids})"
    with connection.cursor() as cursor:
        cursor.execute(sql)
    print('批量更新完成！')

remaining = Part.objects.filter(category__isnull=True).count()
print(f'\n最终剩余未分类: {remaining}')

# Final stats
from django.db.models import Count
cats = Part.objects.filter(category__isnull=False).values('category').annotate(cnt=Count('id')).order_by('-cnt')
print('\n=== 最终各分类零件数 ===')
total_parts = 0
for c in cats:
    cat = PartCategory.objects.filter(id=c['category']).first()
    cat_name = cat.name if cat else 'Unknown'
    print(f'  {cat_name} (ID:{c["category"]}): {c["cnt"]}')
    total_parts += c['cnt']
print(f'  总计: {total_parts}')

if unclassified:
    print(f'\n=== 仍未分类零件 ===')
    for pid, pname, pipn in unclassified:
        print(f'  ID:{pid} {pipn} {pname}')
