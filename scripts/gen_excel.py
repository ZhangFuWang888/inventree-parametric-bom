#!/usr/bin/env python3
"""Generate Excel task breakdown for Parametric BOM system."""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = openpyxl.Workbook()

# ============================================================
# Common styles
# ============================================================
header_font = Font(name='Microsoft YaHei', bold=True, size=11, color='FFFFFF')
header_fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
cat_fill_green = PatternFill(start_color='548235', end_color='548235', fill_type='solid')
cat_fill_yellow = PatternFill(start_color='BF8F00', end_color='BF8F00', fill_type='solid')
bold_font = Font(name='Microsoft YaHei', bold=True, size=10)
normal_font = Font(name='Microsoft YaHei', size=10)
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
wrap_align = Alignment(wrap_text=True, vertical='top')
center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

def set_header(ws, row, cols):
    for c in range(1, cols+1):
        cell = ws.cell(row=row, column=c)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

def set_row(ws, row, cols, font=normal_font):
    for c in range(1, cols+1):
        cell = ws.cell(row=row, column=c)
        cell.font = font
        cell.alignment = wrap_align
        cell.border = thin_border

# ============================================================
# Sheet 1: Summary
# ============================================================
ws1 = wb.active
ws1.title = "总览"

ws1.merge_cells('A1:G1')
ws1.cell(row=1, column=1, value='参数化BOM系统 — 全部工作任务分解').font = Font(name='Microsoft YaHei', bold=True, size=16, color='2F5496')
ws1.cell(row=1, column=1).alignment = Alignment(horizontal='center')

ws1.merge_cells('A2:G2')
ws1.cell(row=2, column=1, value='总开发量：~40.9天 | 已完成：~37.4天 | 未完成：~3.5天 | 任务总数：77个').font = Font(name='Microsoft YaHei', size=10, color='666666')
ws1.cell(row=2, column=1).alignment = Alignment(horizontal='center')

headers = ['层', '总天数', '已完成', '待完成', '任务数', '完成率', '状态']
for c, h in enumerate(headers, 1):
    ws1.cell(row=4, column=c, value=h)
set_header(ws1, 4, 7)

data = [
    ['数据模型层', 7.5, 7.5, 0, 11, '100%', '完成'],
    ['公式引擎层', 6.5, 6.5, 0, 11, '100%', '完成'],
    ['核心引擎层', 6.0, 6.0, 0, 15, '100%', '完成'],
    ['API层', 6.5, 6.5, 0, 23, '100%', '完成(带1个bug)'],
    ['前端层', 5.0, 5.0, 0, 12, '100%', '完成'],
    ['测试层', 3.9, 3.9, 0, 8, '100%', '完成(缺API测试)'],
    ['文档层', 5.5, 2.0, 3.5, 6, '36%', '进行中'],
    ['总计', 40.9, 37.4, 3.5, 77, '91%', '可上线'],
]

for i, d in enumerate(data):
    r = 5 + i
    for c, v in enumerate(d, 1):
        ws1.cell(row=r, column=c, value=v)
    set_row(ws1, r, 7, bold_font if i == 7 else normal_font)

for col, w in [('A',12),('B',10),('C',10),('D',10),('E',9),('F',9),('G',12)]:
    ws1.column_dimensions[col].width = w

# ============================================================
# Sheet 2: Full task list
# ============================================================
ws2 = wb.create_sheet("全部任务")
headers2 = ['层级', '编号', '任务名称', '天数', '文件', '说明']
for c, h in enumerate(headers2, 1):
    ws2.cell(row=1, column=c, value=h)
set_header(ws2, 1, 6)

categories = [
    ('数据模型层', '完成', [
        ('M01', 'PartParameterConfig 模型', 1, 'models.py', '参数配置：数据类型、默认值、范围、步长、is_driving、is_computed、公式字段、UI提示、排序、可见性控制'),
        ('M02', 'ParametricBomItem 模型', 1.5, 'models.py', 'BOM项配置：7个enable_*标志、数量公式、条件公式、候选零件关联、规格描述'),
        ('M03', 'ParametricRule 模型', 1, 'models.py', '规则引擎模型：约束/计算/可见性三种类型、触发条件、动作值、优先级'),
        ('M04', 'ProductConfiguration 模型', 0.5, 'models.py', '产品配置模型：状态机(草稿→已配置→已审核→已批准)、BOM快照JSON'),
        ('M05', 'ConfigParameterValue 模型', 0.5, 'models.py', '配置参数值快照：外键到配置、参数名/值/类型'),
        ('M06', 'BomCandidatePart 模型', 0.5, 'models.py', '候选零件：外键到BOM项、候选Part、匹配条件、优先级'),
        ('M07', 'VariantMapping 模型', 0.5, 'models.py', '变体映射：参数条件→目标变体Part、参数值映射JSON'),
        ('M08', 'BomSpecification 模型', 0.5, 'models.py', 'BOM规格：规格描述、单位、参考价格、供应商'),
        ('M09', 'SupplierSelectionRule 模型', 0.5, 'models.py', '供应商选择：条件公式→推荐供应商、优先级'),
        ('M10', 'InheritanceMapping 模型', 0.5, 'models.py', '参数继承映射：源→目标、改名映射、转换公式'),
        ('M11', 'PartAttributeFormula 模型', 0.5, 'models.py', '零件属性公式：外键到Part、计算公式、单位、分类标签'),
    ]),
    ('公式引擎层', '完成', [
        ('F01', '词法分析器(Tokenizer)', 0.5, 'parser.py', '公式→Token序列：数字/标识符/操作符/括号/函数名/param.xxx'),
        ('F02', '解析器(Parser)', 1, 'parser.py', '递归下降解析Token→AST语法树，操作符优先级、括号分组'),
        ('F03', '求值器(Evaluator)', 1, 'evaluator.py', '递归遍历AST求值，上下文字典传参，类型自动转换'),
        ('F04', '数学函数12个', 0.5, 'functions.py', 'ABS/CEIL/FLOOR/ROUND/SQRT/POW/LOG/MIN/MAX/AVG/SUM/PI'),
        ('F05', '条件函数4个', 0.5, 'functions.py', 'IF/SWITCH/AND/OR'),
        ('F06', '字符串函数6个', 0.5, 'functions.py', 'CONCAT/UPPER/LOWER/LEFT/RIGHT/TRIM'),
        ('F07', '类型函数3个', 0.5, 'functions.py', 'TOSTRING/TONUMBER/ISNULL'),
        ('F08', '业务函数3个', 1, 'functions.py', 'LOOKUP/MATCH/MAP'),
        ('F09', '沙箱保护机制', 0.5, 'evaluator.py', '500ms超时、20层递归、白名单函数、禁止eval/exec/import'),
        ('F10', '错误类型定义', 0.3, 'errors.py', 'ParseError/ReferenceError/EvaluationError/TimeoutError'),
        ('F11', '参数引用解析', 0.5, 'parser.py', 'param.xxx语法→引用节点，运行时从context查找'),
    ]),
    ('核心引擎层', '完成', [
        ('E01', 'compute_parameters函数', 1, 'bom_expander.py', '遍历参数配置计算参数：跳过用户提供、公式计算、默认值回退、继承应用'),
        ('E02', 'expand_bom函数', 1, 'bom_expander.py', '递归展开BOM树：条件/数量/候选/变体/供应商/规格/子项递归'),
        ('E03', 'evaluate入口函数', 0.5, 'bom_expander.py', '参数求值→BOM展开→结果组合，支持timeout/max_depth'),
        ('E04', 'BomTreeBuilder辅助类', 0.5, 'bom_expander.py', 'BOM树构建：节点ID、总量计算、树形扁平化、BOM hash'),
        ('E05', '规则引擎 evaluate_rules', 0.5, 'rule_engine.py', '规则遍历→条件求值→动作执行(设值/锁定/隐藏/警告)'),
        ('E06', '规则引擎 apply_rule_constraints', 0.5, 'rule_engine.py', '约束检查：不满足条件阻止提交，返回约束失败列表'),
        ('E07', '变体生成generate_variant', 0.5, 'variant_generator.py', '从参数配置生成变体Part：复制属性、映射匹配'),
        ('E08', '受影响变体查询', 0.3, 'variant_generator.py', '参数变更影响分析：列出受影响的已生成变体'),
        ('E09', '成本估算estimate_cost', 0.3, 'cost_estimator.py', 'BOM项×数量×单价→成本汇总'),
        ('E10', '成本构成分析', 0.2, 'cost_estimator.py', '按类别/层级/供应商分组统计成本'),
        ('E11', '参数继承inherit_parameters', 0.3, 'param_inheritance.py', '父→子：同名传递、改名映射、公式转换'),
        ('E12', '批量应用继承', 0.2, 'param_inheritance.py', '批量应用继承映射到子装配体所有参数配置'),
        ('E13', '配置工作流状态机', 0.5, 'config_workflow.py', '状态转换：草稿→已配置→已审核→已批准'),
        ('E14', '配置快照管理', 0.3, 'config_workflow.py', '快照生成(参数值+BOM树+时间戳)、快照恢复'),
        ('E15', '配置工作流校验器', 0.2, 'config_workflow.py', '状态转换前校验：参数必填/规则约束/BOM完整性'),
    ]),
    ('API层', '完成', [
        ('AP01', 'PartParameterConfigViewSet', 0.5, 'api.py+serializers.py', '参数配置CRUD，按part/分类过滤，排序'),
        ('AP02', 'ParametricBomItemViewSet', 0.5, 'api.py+serializers.py', 'BOM项配置CRUD、enable_*标志读写'),
        ('AP03', 'ParametricRuleViewSet', 0.5, 'api.py+serializers.py', '规则CRUD、按类型过滤、优先级排序'),
        ('AP04', 'ProductConfigurationViewSet', 0.3, 'api.py+serializers.py', '配置CRUD、按part/状态/用户过滤'),
        ('AP05', 'ConfigParameterValueViewSet', 0.3, 'api.py+serializers.py', '配置参数值CRUD、按配置过滤'),
        ('AP06', 'BomCandidatePartViewSet', 0.3, 'api.py+serializers.py', '候选零件CRUD'),
        ('AP07', 'VariantMappingViewSet', 0.3, 'api.py+serializers.py', '变体映射CRUD'),
        ('AP08', 'BomSpecificationViewSet', 0.3, 'api.py+serializers.py', 'BOM规格CRUD'),
        ('AP09', 'SupplierSelectionRuleViewSet', 0.3, 'api.py+serializers.py', '供应商规则CRUD'),
        ('AP10', 'InheritanceMappingViewSet', 0.3, 'api.py+serializers.py', '继承映射CRUD'),
        ('AP11', 'PartAttributeFormulaViewSet', 0.3, 'api.py+serializers.py', '属性公式CRUD、按分类过滤'),
        ('AP12', 'bom_evaluate端点', 0.5, 'api.py', '参数评估入口。BUG：cfg.template为空时500'),
        ('AP13', 'estimate_cost端点', 0.3, 'api.py', '成本估算'),
        ('AP14', 'formula_validate端点', 0.3, 'api.py', '公式验证'),
        ('AP15', 'formula_preview端点', 0.3, 'api.py', '公式预览'),
        ('AP16', 'rules_evaluate端点', 0.3, 'api.py', '规则评估'),
        ('AP17', 'generate_variant端点', 0.3, 'api.py', '生成变体'),
        ('AP18', 'inherit_params端点', 0.2, 'api.py', '参数继承'),
        ('AP19', 'affected_variants端点', 0.2, 'api.py', '受影响变体查询'),
        ('AP20', 'template_library端点', 0.5, 'api.py', '模板同步/分类/批量分配/自动同步'),
        ('AP21', 'config状态操作端点', 0.5, 'api.py', '配置工作流：transition/snapshot/detail/set-params'),
        ('AP22', 'admin.py管理界面', 0.2, 'admin.py', '所有模型注册Django admin'),
        ('AP23', 'urls.py路由注册', 0.1, 'urls.py', 'ViewSet+函数视图路由'),
    ]),
    ('前端层', '完成', [
        ('U01', '参数配置面板', 0.5, 'configurator.html', '列表表格、新建弹窗、编辑表单、删除确认、搜索过滤'),
        ('U02', '公式编辑器(CodeMirror5)', 1, 'configurator.html+codemirror-formula.js', '语法高亮、行号、参数引用插入、实时验证'),
        ('U03', 'BOM配置面板', 0.5, 'configurator.html', 'BOM项列表、enable_*标志、公式输入、候选选择'),
        ('U04', '参数调试面板', 0.5, 'configurator.html', '参数滑块输入、实时求值、BOM树可视化、自动刷新'),
        ('U05', '规则配置面板', 0.5, 'configurator.html', '规则列表、类型选择、公式编辑、动作配置、排序'),
        ('U06', '变体生成面板', 0.3, 'configurator.html', '一键生成、进度展示、变体列表'),
        ('U07', '成本概览面板', 0.3, 'configurator.html', '成本总计、饼图/条形图、按层级展开'),
        ('U08', '产品搜索面板', 0.3, 'configurator.html', '分类树、搜索框、自动补全、最近使用'),
        ('U09', '配置保存/加载', 0.3, 'configurator.html', '保存/加载/名称编辑/删除'),
        ('U10', '三步引导流程', 0.5, 'configurator.html', 'Step1调参→Step2预览→Step3生成，进度指示'),
        ('U11', '配置状态显示', 0.3, 'configurator.html', '状态标签、状态转换按钮'),
        ('U12', 'Stripe白色主题', 0.3, 'configurator.html', '白底#fff、深蓝字、紫强调#533afd、Source Sans 3、响应式'),
    ]),
    ('测试层', '完成', [
        ('T01', '公式引擎测试', 1, 'test_formula_engine.py', '45个测试：词法/解析/求值/28函数/沙箱'),
        ('T02', 'BOM展开测试', 0.5, 'test_bom_expander.py', '33个测试：compute_parameters/expand_bom/条件/数量公式'),
        ('T03', '规则引擎测试', 0.5, 'test_rule_engine.py', '28个测试：条件求值/动作执行/优先级/约束'),
        ('T04', '配置工作流测试', 0.5, 'test_config_workflow.py', '23个测试：状态转换/校验/快照'),
        ('T05', '成本估算测试', 0.5, 'test_cost_estimator.py', '21个测试：成本计算/汇总/构成分析'),
        ('T06', '模板库测试', 0.3, 'test_template_library.py', '14个测试：同步/分类/批量分配'),
        ('T07', '参数继承测试', 0.3, 'test_param_inheritance.py', '12个测试：传递/映射/公式转换'),
        ('T08', '变体生成测试', 0.3, 'test_variant_generator.py', '12个测试：创建/复制/映射/受影响查询'),
    ]),
    ('文档层(已完成)', '完成', [
        ('D01', '产品设计文档', 2, 'parametric-bom-design.md', '2260行：产品概述、12种场景、8种BOM模式、4种辅助、数据模型、API设计、公式规格'),
    ]),
    ('文档层(待完成)', '待完成', [
        ('D02', 'API文档OpenAPI', 0.5, 'api.py', '每个端点@extend_schema：请求/响应/错误码/示例'),
        ('D03', '用户手册-管理员', 1, 'user-guide-admin.md', '安装配置/模板管理/规则配置/权限/运维'),
        ('D04', '用户手册-工程师', 1, 'user-guide-engineer.md', '公式编写/28函数速查/10示例/BOM配置/故障排查'),
        ('D05', '部署检查清单', 0.5, 'deployment-checklist.md', '环境/安装/验证/nginx/生产配置'),
    ]),
]

row = 2
for cat_name, status, tasks in categories:
    ws2.merge_cells(f'A{row}:F{row}')
    cell = ws2.cell(row=row, column=1, value=cat_name)
    cell.font = Font(name='Microsoft YaHei', bold=True, size=11, color='FFFFFF')
    fill = cat_fill_green if status == '完成' else cat_fill_yellow
    cell.fill = fill
    cell.alignment = Alignment(horizontal='center', vertical='center')
    for c in range(1, 7):
        ws2.cell(row=row, column=c).border = thin_border
        ws2.cell(row=row, column=c).fill = fill
    row += 1

    for tid, tname, days, files, desc in tasks:
        ws2.cell(row=row, column=1, value=cat_name.split('(')[0].strip())
        ws2.cell(row=row, column=2, value=tid)
        ws2.cell(row=row, column=3, value=tname)
        ws2.cell(row=row, column=4, value=days)
        ws2.cell(row=row, column=5, value=files)
        ws2.cell(row=row, column=6, value=desc)
        set_row(ws2, row, 6)
        row += 1

ws2.column_dimensions['A'].width = 12
ws2.column_dimensions['B'].width = 8
ws2.column_dimensions['C'].width = 32
ws2.column_dimensions['D'].width = 8
ws2.column_dimensions['E'].width = 34
ws2.column_dimensions['F'].width = 68

# ============================================================
# Sheet 3: Todo
# ============================================================
ws3 = wb.create_sheet("待完成工作")
headers3 = ['优先级', '编号', '任务名称', '天数', '文件', '说明']
for c, h in enumerate(headers3, 1):
    ws3.cell(row=1, column=c, value=h)
set_header(ws3, 1, 6)

todo_list = [
    ('P0-紧急', 'T001', '修 evaluate 500 bug', 0.2, 'bom_expander.py', 'cfg.template为空时报AttributeError，加None判断'),
    ('P0-紧急', 'T002', '统一API错误响应', 0.3, 'api.py', '加@api_error_handler装饰器，统一JSON错误格式'),
    ('P0-紧急', 'T003', '空公式/边界处理', 0.3, 'evaluator.py', '空公式返回None、除零友好提示、未定义参数列表'),
    ('P1-重要', 'T004', 'API集成测试', 1.0, 'tests/test_api.py', '15+端点20+测试，覆盖核心流程和错误场景'),
    ('P1-重要', 'T005', '数据迁移验证', 0.3, 'migrations/', 'mode→enable_*迁移脚本验证+补充迁移测试'),
    ('P2-一般', 'T006', 'API文档OpenAPI', 0.5, 'api.py', '@extend_schema标注请求/响应/错误码/示例'),
    ('P2-一般', 'T007', '用户手册-管理员', 1.0, 'user-guide-admin.md', '安装配置、模板管理、规则配置、权限管理'),
    ('P2-一般', 'T008', '用户手册-工程师', 1.0, 'user-guide-engineer.md', '公式编写、28函数速查、10示例、故障排查'),
    ('P2-一般', 'T009', '部署检查清单', 0.5, 'deployment-checklist.md', '环境要求、安装步骤、验证检查、生产配置'),
    ('P3-增强', 'T010', '配置导出/导入', 0.5, 'api.py', '配置导出为JSON / 从JSON导入'),
    ('P3-增强', 'T011', '配置版本管理', 1.0, 'models.py+api.py', 'ConfigurationVersion模型、自动+1版本、历史回滚'),
    ('P3-增强', 'T012', '配置版本对比', 0.5, 'api.py+configurator.html', '两版本参数/BOM差异、红绿高亮'),
    ('P3-增强', 'T013', 'HTML文件拆分', 0.5, 'configurator.html', '6000行单文件→CSS/JS独立文件'),
]

for i, (pri, tid, name, days, files, desc) in enumerate(todo_list):
    r = 2 + i
    ws3.cell(row=r, column=1, value=pri)
    ws3.cell(row=r, column=2, value=tid)
    ws3.cell(row=r, column=3, value=name)
    ws3.cell(row=r, column=4, value=days)
    ws3.cell(row=r, column=5, value=files)
    ws3.cell(row=r, column=6, value=desc)
    set_row(ws3, r, 6)

ws3.column_dimensions['A'].width = 12
ws3.column_dimensions['B'].width = 8
ws3.column_dimensions['C'].width = 28
ws3.column_dimensions['D'].width = 8
ws3.column_dimensions['E'].width = 30
ws3.column_dimensions['F'].width = 68

output_path = '/root/inventree-source/InvenTree-master/docs/plans/parametric-bom-all-tasks.xlsx'
wb.save(output_path)
print(f'Saved: {output_path}')
