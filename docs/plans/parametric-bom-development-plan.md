# 参数化BOM系统 — 实时开发计划（含时间估算）

> **目标：** 从当前版本到可商用的参数化BOM系统
> **基于：** [parametric-bom-design.md](../parametric-bom-design.md)
> **当前状态：** 188/188 测试通过 ✅
> **总预计工时：** ~8.5 小时（集中开发）

## ⏱ 总览时间线

| 阶段 | 内容 | 预计工时 | 累计 |
|------|------|---------|------|
| 🔴 Phase 1 | Bug修复与稳定性 | ~50min | ~50min |
| 🟡 Phase 2 | 数据模型加固 | ~1h05min | ~2h |
| 🟡 Phase 3 | 测试覆盖 | ~2h | ~4h |
| 🔵 Phase 4 | 前端优化 | ~1h45min | ~5h45min |
| 🔵 Phase 5 | 功能补全 | ~1h55min | ~7h40min |
| 🟢 Phase 6 | 文档与部署 | ~55min | **~8.5h** |

---

## 当前已完成的模块

| 模块 | 状态 | 测试 | 说明 |
|------|------|------|------|
| Formula Engine | ✅ 完成 | 45/45 | 解析器+求值器+28函数+沙箱 |
| BOM Expander | ✅ 完成 | 集成测试 | 12种场景对应的enable_*标志 |
| Rule Engine | ✅ 完成 | 集成测试 | 约束/计算/可见性三类规则 |
| Variant Generator | ✅ 完成 | 集成测试 | 从参数模板生成变体 |
| Cost Estimator | ✅ 完成 | 集成测试 | 配置成本估算 |
| Param Inheritance | ✅ 完成 | 集成测试 | 父子参数传递 |
| Template Library | ✅ 完成 | 集成测试 | PartAttributeFormula |
| Configurator UI | ✅ 完成 | — | 6000行单文件HTML |
| Stripe 白色主题 | ✅ 完成 | — | CSS 美化 |

---

## Phase 1: Bug 修复与稳定性 🔴（~50min）

### Task 1.1: 修复 evaluate API 500错误（~15min）

**Bug:** `POST /api/parametric-bom/evaluate/` 在 `bom_expander.py:115` 抛出 `AttributeError: 'NoneType' object has no attribute 'name'` — `cfg.template` 为空时未做保护。

**文件:** `src/backend/parametric_bom/bom_expander.py`
**改动:** 在 `compute_parameters()` 函数中，访问 `cfg.template.name` 前检查 `cfg.template` 是否为 None
**步骤:**
1. 定位 `compute_parameters()` 中 `cfg.template.name` 行
2. 加 `if cfg.template is None: continue` 跳过
3. 重启服务器验证不再 500
**验证:** 对有 null template 的参数配置执行 evaluate，应返回友好错误而非 500

### Task 1.2: 统一错误处理（~15min）

**问题:** API 错误直接抛 500，前端收到 72 字节无意义响应。
**方案:** 给所有 API 端点加 try/except，返回 `{error: string, detail: string}` 格式的统一错误体
**文件:** `src/backend/parametric_bom/api.py`
**步骤:**
1. 定义 `APIError(Exception)` 基类
2. 给视图函数加 `@api_error_handler` 装饰器
3. 在 `api.py` 中已有的 `part_config`, `evaluate`, `validate` 等端点各加 try/except
4. 测试：模拟错误场景，确认返回 JSON 而非 500

### Task 1.3: 公式引擎边界处理（~20min）
- 空公式/空白公式的处理（应视为无公式，走默认值）→ 5min
- 公式中引用的参数在上下文中不存在时给出具体提示（如：参数"xyz"不存在，可用参数有：长度、宽度）→ 10min
- 除零错误友好提示 → 5min

---

## Phase 2: 数据模型加固 🟡（~1h05min）

### Task 2.1: 数据迁移 — mode → enable_* 标志（~30min）

**背景:** 旧代码用 `mode` 字段（单值），新代码改为 `enable_qty_formula/enable_conditional/enable_candidate/...` 多选标志
**文件:** `src/backend/parametric_bom/migrations/`
**动作:**
1. 用 `makemigrations` 生成空迁移 → 2min
2. 编写数据迁移函数：读取旧 `mode` 值映射到对应 `enable_*` → 15min
3. 正向迁移 + 逆向迁移（回滚支持）→ 5min
4. 运行迁移测试验证 → 5min
5. 在正式库执行 `migrate` → 3min

### Task 2.2: 模型约束与索引（~15min）

- 给 `PartParameterConfig` 加 `unique_together(part, template)` 约束 → 5min
- 给 `ParametricBomItem` 加 `unique_together(bom_item, part)` 约束 → 5min
- 给外键字段加 `db_index=True`（已有数据的表可能需要手动加索引）→ 5min
- 生成迁移 + 验证

### Task 2.3: 软删除支持（~20min）

- 在关键模型（ProductConfiguration、ParametricRule）添加 `is_active` 布尔字段 → 5min
- 默认 `is_active=True` → 2min
- 重写 `objects` 管理器默认过滤 `is_active=True` → 8min
- 生成迁移 → 5min

---

## Phase 3: 测试覆盖 🟡（~2h）

### Task 3.1: API 端点测试（~1h）

**文件:** `src/backend/parametric_bom/tests/`
**内容:** 为所有 15+ API 端点编写集成测试
- `GET /api/parametric-bom/part-config/` — 列表+过滤 → 8min
- `POST /api/parametric-bom/part-config/` — 创建+验证 → 8min
- `POST /api/parametric-bom/evaluate/` — 参数评估（含错误场景）→ 10min
- `POST /api/parametric-bom/validate/` — 参数验证 → 10min
- CRUD 配置、规则、BOM项配置等 → 24min

### Task 3.2: 边缘案例测试（~30min）

- 公式引擎：超大嵌套深度（>20层）、极端数字（1e308）、空参数上下文 → 10min
- BOM展开：循环引用检测、多级BOM树（>10层）→ 10min
- 规则引擎：多条规则优先级冲突、规则条件恒真/恒假 → 5min
- 变体生成：同名变体、无参数模板的 part → 5min

### Task 3.3: 前端 JS 基础测试（~30min，可选）

如果前端有模块化的 JS（codemirror-formula.js），可加 Jest 测试
主要测试：参数引用插入、公式验证调用、配置器状态管理

---

## Phase 4: 前端优化 🔵（~1h45min）

### Task 4.1: 拆分 configurator.html（~20min，可选）

**现状:** 6000+ 行单文件，包含全部 CSS+HTML+JS
**方案:** 将 CSS 提取到独立 .css 文件，JS 逻辑拆到独立 .js 文件
**注意:** Django 模板变量（`{% if %}`, `{{ }}`）必须在 .html 中保留

### Task 4.2: 公式编辑器体验提升（~30min）

- 参数自动补全从 CodeMirror 5 升级到更丰富的体验（如按类型分组显示）→ 15min
- 公式校验错误在行内显示（红色波浪线效果）→ 10min
- 公式测试面板可保存常用测试参数组合 → 5min

### Task 4.3: 产品配置器工作流优化（~40min）

- 三步引导（Step 1:参数→Step 2:BOM预览→Step 3:生成）+ 进度指示 → 15min
- 配置保存后可生成分享链接 → 15min
- 配置对比功能（两个配置的差异对比）→ 10min

### Task 4.4: 移动端兼容（~15min）

- 参数卡片在窄屏上折叠/展开 → 8min
- 侧栏在手机上的交互优化 → 7min

---

## Phase 5: 功能补全 🔵（~1h55min）

### Task 5.1: 配置导出/导入（~30min）

- 导出配置为 JSON/CSV → 10min
- 从 JSON 导入配置（含参数值+BOM快照）→ 10min
- 导出报价单（PDF）→ 10min

### Task 5.2: 配置版本管理（~30min）

- 配置修改时自动创建新版本（revision +1）→ 10min
- 版本历史查看与回滚 → 10min
- 版本对比差异展示 → 10min

### Task 5.3: BOM 生成后的库存对接（~25min）

- 配置生成 BOM 后，可选择「创建采购订单」或「创建生产订单」→ 10min
- 调用 InvenTree 标准 API 创建订单 → 15min

### Task 5.4: 参数模板市场（~30min）

- 预设参数模板（如辊道输送机、直线导轨模组等）→ 10min
- 模板导入/导出（JSON 格式）→ 10min
- 模板推荐系统：根据 Part 分类推荐模板 → 10min

---

## Phase 6: 文档与部署 🟢（~55min）

### Task 6.1: API 文档（~20min）

- 为每个端点编写 OpenAPI 文档（可在 `api.py` 用 `@extend_schema` 装饰器）→ 15min
- 生成 REST API 文档页面 → 5min

### Task 6.2: 用户手册（~25min）

- 参数化BOM系统管理员指南 → 10min
- 设计工程师快速上手手册 → 10min
- 常见问题 FAQ → 5min

### Task 6.3: 部署检查清单（~10min）

- 数据库迁移检查 → 2min
- Redis 缓存配置（如有）→ 2min
- Nginx 静态文件配置 → 2min
- DEBUG=False 模式下测试 → 2min
- 性能基准测试 → 2min

---

## 当前优先级建议

```
急需修复 → 1.1 (evaluate 500) → 1.2 (统一错误处理)
          → 2.1 (mode迁移)
          
稳步推进 → 3.1 (API测试) → 3.2 (边缘案例)
          → 4.2 (公式编辑器) → 4.3 (配置器工作流)
          
持续完善 → 5.1 (导出) → 5.2 (版本) → 5.3 (库存对接)
          → 6.1 (API文档) → 6.2 (用户手册)
```

**当前 bug 数：** 1 个已知（evaluate 500），先修这个
**测试通过率：** 188/188 ✅
**代码行数：** ~20,000 行后端 Python + ~6,000 行前端 HTML/JS/CSS
