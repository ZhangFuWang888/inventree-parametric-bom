# 参数化BOM系统 — 全部工作任务分解

---

## 一、数据模型层（7.5天 ✅ 完成）

| # | 任务 | 天数 | 文件 | 说明 |
|---|------|------|------|------|
| M01 | PartParameterConfig 模型定义 | 1 | `models.py` | 参数配置模型：外键到Part和模板、数据类型、默认值、范围、步长、选项、is_driving、is_computed、公式字段、UI提示、排序、可见性控制 |
| M02 | ParametricBomItem 模型定义 | 1.5 | `models.py` | BOM项配置：7个enable_*布尔标志替代旧mode字段、数量公式、条件公式、候选零件关联、规格描述、引用排序 |
| M03 | ParametricRule 模型定义 | 1 | `models.py` | 规则引擎模型：规则类型（约束/计算/可见性）、触发条件公式、动作值、优先级、生效日期 |
| M04 | ProductConfiguration 模型定义 | 0.5 | `models.py` | 产品配置模型：状态机（草稿→已配置→已审核→已批准）、关联Part、BOM快照JSON、参数快照、备注 |
| M05 | ConfigParameterValue 模型定义 | 0.5 | `models.py` | 配置参数值快照：外键到配置、参数名、参数值、值类型 |
| M06 | BomCandidatePart 模型定义 | 0.5 | `models.py` | 候选零件：外键到BOM项、候选Part、匹配条件公式、优先级、默认选中 |
| M07 | VariantMapping 模型定义 | 0.5 | `models.py` | 变体映射：外键到BOM项、参数条件→目标变体Part、参数值映射JSON |
| M08 | BomSpecification 模型定义 | 0.5 | `models.py` | BOM规格：不指向具体Part，而是规格描述文本、单位、参考价格、供应商 |
| M09 | SupplierSelectionRule 模型定义 | 0.5 | `models.py` | 供应商选择规则：外键到BOM项、条件公式→推荐供应商、优先级 |
| M10 | InheritanceMapping 模型定义 | 0.5 | `models.py` | 参数继承映射：源Part→目标Part、源参数名→目标参数名、转换公式、传递方向 |
| M11 | PartAttributeFormula 模型定义 | 0.5 | `models.py` | 零件属性公式：外键到Part和属性定义、计算公式、单位、分类标签 |

---

## 二、公式引擎层（6.5天 ✅ 完成）

| # | 任务 | 天数 | 文件 | 说明 |
|---|------|------|------|------|
| F01 | 词法分析器（Tokenizer） | 0.5 | `formula_engine/parser.py` | 将公式字符串拆分为Token序列：数字、标识符、操作符（+-*/%^）、括号、函数名、参数引用（param.xxx）、逗号、比较符（><=）、逻辑符 |
| F02 | 解析器（Parser） | 1 | `formula_engine/parser.py` | 递归下降解析Token序列→AST语法树。处理操作符优先级（乘除>加减）、括号分组、函数调用参数列表 |
| F03 | 求值器（Evaluator） | 1 | `formula_engine/evaluator.py` | 递归遍历AST求值。上下文字典传参、类型自动转换（字符串→数字）、结果类型保 |
| F04 | 数学函数（ABS/CEIL/FLOOR/ROUND/SQRT/POW/LOG/MIN/MAX/AVG/SUM/PI） | 0.5 | `formula_engine/functions.py` | 12个数学函数注册到函数表，支持大小写不敏感调用 |
| F05 | 条件函数（IF/SWITCH/AND/OR） | 0.5 | `formula_engine/functions.py` | IF(条件, 真值, 假值)、SWITCH(表达式, 值1, 结果1, 默认)、AND/OR多条件 |
| F06 | 字符串函数（CONCAT/UPPER/LOWER/LEFT/RIGHT/TRIM） | 0.5 | `formula_engine/functions.py` | 6个字符串函数，支持数字→字符串隐式转换 |
| F07 | 类型函数（TOSTRING/TONUMBER/ISNULL） | 0.5 | `formula_engine/functions.py` | 显式类型转换、空值判断 |
| F08 | 业务函数（LOOKUP/MATCH/MAP） | 1 | `formula_engine/functions.py` | LOOKUP(参数名, 映射表)—查参数映射值；MATCH(值, 列表)—匹配候选；MAP(值, 键值对JSON)—字典映射 |
| F09 | 沙箱保护机制 | 0.5 | `formula_engine/evaluator.py` | 500ms超时（signal.alarm）、20层递归深度限制、白名单函数检查、禁止eval/exec/import、限制数学精度 |
| F10 | 错误类型定义 | 0.3 | `formula_engine/errors.py` | ParseError/ReferenceError/EvaluationError/TimeoutError 自定义异常层次结构 |
| F11 | 参数引用解析 | 0.5 | `formula_engine/parser.py` | `param.xxx` 语法解析为参数引用节点，求值时从上下文字典查找 |

---

## 三、核心业务引擎层（6天 ✅ 完成）

| # | 任务 | 天数 | 文件 | 说明 |
|---|------|------|------|------|
| E01 | compute_parameters 函数 | 1 | `bom_expander.py` | 遍历PartParameterConfig，按display_order计算每个参数。user_params跳过、公式计算、默认值回退、继承应用、属性公式计算、参数名去重、错误收集 |
| E02 | expand_bom 函数 | 1 | `bom_expander.py` | 递归展开BOM树。对每个BOM项检查enable_*标志执行对应逻辑。条件判断→排除/保留、数量公式→计算qty、候选零件匹配、变体生成触发、供应商选择、规格处理、子项递归 |
| E03 | evaluate_part / evaluate_configuration 入口 | 0.5 | `bom_expander.py` | 顶层入口：参数求值→BOM展开→结果组合。支持timeout_ms和max_depth参数 |
| E04 | BomTreeBuilder 辅助类 | 0.5 | `bom_expander.py` | BOM树构建与展示：节点ID生成、层级维护、Part显示名、总量计算（compute_total_quantity）、树形扁平化（flatten_bom）、BOM hash计算 |
| E05 | 规则引擎 evaluate_rules | 0.5 | `rule_engine.py` | 规则遍历→条件公式求值→动作执行（设值/锁定/隐藏/警告/禁用），结果收集 |
| E06 | 规则引擎 apply_rule_constraints | 0.5 | `rule_engine.py` | 约束规则检查：不满足条件时阻止配置提交，返回约束失败列表 |
| E07 | 变体生成器 generate_variant | 0.5 | `variant_generator.py` | 从参数配置生成变体Part：复制模板Part属性、按VariantMapping映射参数值→具体零件、创建Part+关联参数 |
| E08 | 变体生成器 affected_variants | 0.3 | `variant_generator.py` | 参数变更影响分析：找出受参数修改影响的所有已生成变体，标记待更新 |
| E09 | 成本估算器 estimate_cost | 0.3 | `cost_estimator.py` | 根据BOM展开结果计算成本：遍历BOM项×数量×单位价格、汇总成本、区分材料/人工/外协 |
| E10 | 成本估算器 cost_breakdown | 0.2 | `cost_estimator.py` | 成本构成分析：按类别/层级/供应商分组统计 |
| E11 | 参数继承器 inherit_parameters | 0.3 | `param_inheritance.py` | 父→子参数传递：同名直接传递、改名映射、公式转换 |
| E12 | 参数继承器 apply_inheritance | 0.2 | `param_inheritance.py` | 批量应用继承映射到子装配体的所有参数配置 |
| E13 | 配置工作流状态机 transitions | 0.5 | `config_workflow.py` | 状态转换逻辑：草稿→已配置（参数完整校验）、已配置→已审核（审核校验）、已审核→已批准（终审） |
| E14 | 配置工作流 snapshot 管理 | 0.3 | `config_workflow.py` | 配置快照生成（参数值+BOM树+时间戳）、快照恢复 |
| E15 | 配置工作流校验器 | 0.2 | `config_workflow.py` | 每个状态转换前的校验：参数必填检查、规则约束检查、BOM完整性检查 |

---

## 四、API层（6.5天 ✅ 完成，带1个bug）

| # | 任务 | 天数 | 文件 | 说明 |
|---|------|------|------|------|
| AP01 | PartParameterConfigViewSet CRUD | 0.5 | `api.py` + `serializers.py` | 参数配置的增删改查、按part过滤、按分类过滤、排序 |
| AP02 | ParametricBomItemViewSet CRUD | 0.5 | `api.py` + `serializers.py` | BOM项配置CRUD、按BOM项过滤、enable_*标志读写 |
| AP03 | ParametricRuleViewSet CRUD | 0.5 | `api.py` + `serializers.py` | 规则CRUD、按类型过滤、优先级排序 |
| AP04 | ProductConfigurationViewSet CRUD | 0.3 | `api.py` + `serializers.py` | 配置CRUD、按part/状态/用户过滤 |
| AP05 | ConfigParameterValueViewSet CRUD | 0.3 | `api.py` + `serializers.py` | 配置参数值CRUD、按配置过滤 |
| AP06 | BomCandidatePartViewSet CRUD | 0.3 | `api.py` + `serializers.py` | 候选零件CRUD |
| AP07 | VariantMappingViewSet CRUD | 0.3 | `api.py` + `serializers.py` | 变体映射CRUD |
| AP08 | BomSpecificationViewSet CRUD | 0.3 | `api.py` + `serializers.py` | BOM规格CRUD |
| AP09 | SupplierSelectionRuleViewSet CRUD | 0.3 | `api.py` + `serializers.py` | 供应商规则CRUD |
| AP10 | InheritanceMappingViewSet CRUD | 0.3 | `api.py` + `serializers.py` | 继承映射CRUD |
| AP11 | PartAttributeFormulaViewSet CRUD | 0.3 | `api.py` + `serializers.py` | 属性公式CRUD、按分类过滤 |
| AP12 | bom_evaluate 端点 | 0.5 | `api.py` | 参数评估入口：接收config_id或part_id+user_params→调用bom_expander→返回参数值+BOM展开树。**存在bug：cfg.template为空时500** |
| AP13 | estimate_cost 端点 | 0.3 | `api.py` | 成本估算：接收config_id→计算BOM成本→返回成本明细+总计 |
| AP14 | formula_validate 端点 | 0.3 | `api.py` | 公式验证：接收公式字符串+参数列表→语法检查→返回合法/错误信息 |
| AP15 | formula_preview 端点 | 0.3 | `api.py` | 公式预览：接收公式+上下文示例值→返回计算结果预览 |
| AP16 | rules_evaluate 端点 | 0.3 | `api.py` | 规则评估：接收config_id→执行所有规则→返回规则触发结果列表 |
| AP17 | generate_variant 端点 | 0.3 | `api.py` + `variant_generator.py` | 生成变体：接收config_id→创建变体Part→返回新Part信息 |
| AP18 | inherit_params 端点 | 0.2 | `api.py` | 参数继承：接收part_id→从父Part继承参数→返回继承结果 |
| AP19 | affected_variants 端点 | 0.2 | `api.py` | 受影响变体查询：接收part_config_id→列出受影响的所有变体 |
| AP20 | template_library 相关端点（sync/category/bulk-assign/auto-sync） | 0.5 | `api.py` + `template_library.py` | 模板库同步（从PartAttributeFormula→PartParameterConfig）、分类查询、批量分配、自动同步 |
| AP21 | config 状态操作端点（transition/snapshot/detail/set-params） | 0.5 | `api.py` | 配置工作流：状态转换、快照生成、配置详情、参数设置 |
| AP22 | admin.py 管理界面注册 | 0.2 | `admin.py` | Django admin 注册所有模型，配置列表显示字段、搜索、过滤 |
| AP23 | urls.py 路由注册 | 0.1 | `urls.py` | 所有ViewSet和函数视图的路由注册 |

---

## 五、前端层（5天 ✅ 完成）

| # | 任务 | 天数 | 文件 | 说明 |
|---|------|------|------|------|
| U01 | 参数配置面板（列表+增删改查） | 0.5 | `configurator.html` | 参数列表表格、新建参数弹窗、编辑参数表单、删除确认、搜索/过滤 |
| U02 | 公式编辑器（CodeMirror 5） | 1 | `configurator.html` + `codemirror-formula.js` | CodeMirror 5 集成、公式语法高亮、行号、参数引用插入按钮、公式验证实时反馈 |
| U03 | BOM配置面板 | 0.5 | `configurator.html` | BOM项列表、enable_*标志开关、数量公式输入、条件公式输入、候选零件选择 |
| U04 | 参数调式面板（实时BOM预览） | 0.5 | `configurator.html` | 参数滑块/输入框、实时求值、BOM展开树可视化、参数值变化时BOM自动刷新 |
| U05 | 规则配置面板 | 0.5 | `configurator.html` | 规则列表、规则类型选择、条件公式编辑、动作值配置、优先级排序 |
| U06 | 变体生成面板 | 0.3 | `configurator.html` | 一键生成变体按钮、生成进度、结果展示、变体列表 |
| U07 | 成本概览面板 | 0.3 | `configurator.html` | 成本总计显示、成本构成饼图/条形图、按类别/层级展开成本明细 |
| U08 | 产品选择/搜索 | 0.3 | `configurator.html` | 产品分类树、产品搜索框、搜索自动补全、最近使用列表 |
| U09 | 配置保存/加载 | 0.3 | `configurator.html` | 保存配置按钮、加载历史配置列表、配置名称编辑、删除配置 |
| U10 | 三步引导流程 | 0.5 | `configurator.html` | Step 1调参数→Step 2预览BOM→Step 3生成，步骤切换、进度指示、上一步/下一步 |
| U11 | 配置状态显示 | 0.3 | `configurator.html` | 状态标签（草稿/已配置/已审核/已批准）、状态转换按钮、审核操作 |
| U12 | Stripe白色主题 | 0.3 | `configurator.html` | 全页面CSS改版：白底#ffffff、深蓝字#061b31、紫强调#533afd、Source Sans 3字体、圆角卡片、阴影、响应式布局 |

---

## 六、测试层（3.9天 ✅ 完成）

| # | 任务 | 天数 | 文件 | 测试数 | 说明 |
|---|------|------|------|--------|------|
| T01 | 公式引擎测试 | 1 | `test_formula_engine.py` | 45 | 词法分析、解析、求值、28个函数、沙箱超时、递归深度、错误传播 |
| T02 | BOM展开测试 | 0.5 | `test_bom_expander.py` | 33 | compute_parameters、expand_bom、evaluate_part、条件排除/包含、数量公式、树结构、总量计算、hash计算 |
| T03 | 规则引擎测试 | 0.5 | `test_rule_engine.py` | 28 | 规则条件求值、动作执行、优先级、冲突处理、约束检查 |
| T04 | 配置工作流测试 | 0.5 | `test_config_workflow.py` | 23 | 状态转换、参数校验、快照、权限检查、非法转换拒绝 |
| T05 | 成本估算测试 | 0.5 | `test_cost_estimator.py` | 21 | 成本计算、数量×单价、多层汇总、成本构成分析 |
| T06 | 模板库测试 | 0.3 | `test_template_library.py` | 14 | 模板同步、分类管理、批量分配、自动同步逻辑 |
| T07 | 参数继承测试 | 0.3 | `test_param_inheritance.py` | 12 | 同名传递、改名映射、公式转换、多层继承 |
| T08 | 变体生成测试 | 0.3 | `test_variant_generator.py` | 12 | 变体创建、属性复制、映射匹配、受影响变体查询 |

---

## 七、文档层（5.5天：已做2天，剩3.5天）

### 已完成（2天 ✅）

| # | 任务 | 天数 | 文件 | 说明 |
|---|------|------|------|------|
| D01 | 产品设计文档 | 2 | `docs/parametric-bom-design.md` | 2260行完整设计文档：产品概述、12种参数化场景、8种BOM项模式、4种辅助能力、数据模型详解、API设计、公式引擎规格、用户故事、决策树 |

### 待完成（3.5天 ⬜）

| # | 任务 | 天数 | 文件 | 说明 |
|---|------|------|------|------|
| D02 | API文档（OpenAPI） | 0.5 | `api.py` + `parametric_bom/__init__.py` | 每个端点加@extend_schema，标注请求参数、响应结构、错误码、示例 |
| D03 | 用户手册-管理员 | 1 | `docs/user-guide-admin.md` | 安装配置、参数模板管理、规则配置、权限管理、部署运维 |
| D04 | 用户手册-工程师 | 1 | `docs/user-guide-engineer.md` | 公式编写指南、28函数速查表、10个常见公式示例、BOM配置操作、故障排查 |
| D05 | 部署检查清单 | 0.5 | `docs/deployment-checklist.md` | 环境要求、安装步骤、验证检查、Nginx配置、生产优化 |
| D06 | 开发计划 | 0.5 | `docs/plans/` | 本系列多份计划文档 |

---

## 八、总计

| 层 | 总天数 | 已完成 | 待完成 |
|----|--------|--------|--------|
| 📦 数据模型 | 7.5 | 7.5 | 0 |
| ⚙️ 公式引擎 | 6.5 | 6.5 | 0 |
| 🧠 核心引擎 | 6 | 6 | 0 |
| 🔌 API层 | 6.5 | 6.5 | 0（带1个bug） |
| 🎨 前端 | 5 | 5 | 0 |
| 🧪 测试 | 3.9 | 3.9 | 0（缺API测试） |
| 📝 文档 | 5.5 | 2 | **3.5** |
| **总计** | **40.9** | **37.4** | **3.5** |

### 待完成明细（共3.5天）

| 优先级 | 任务 | 天数 | 类型 |
|--------|------|------|------|
| 🔴 P0 | 修 evaluate 500 bug（cfg.template为空） | 0.2 | bug |
| 🟡 P1 | 补充API集成测试（15+端点覆盖） | 1 | 测试 |
| 🟡 P1 | 数据迁移脚本验证（mode→enable_*） | 0.3 | 运维 |
| 🟢 P2 | API文档 OpenAPI | 0.5 | 文档 |
| 🟢 P2 | 用户手册-管理员 | 1 | 文档 |
| 🟢 P2 | 用户手册-工程师 | 1 | 文档 |
| 🟢 P2 | 部署检查清单 | 0.3 | 文档 |
| 🔵 P3 | 配置导出/导入 | 0.5 | 功能增强 |
| 🔵 P3 | 配置版本管理 | 1 | 功能增强 |
| 🔵 P3 | 配置对比 | 0.5 | 功能增强 |
| 🔵 P3 | HTML文件拆分 | 0.5 | 代码重构 |
