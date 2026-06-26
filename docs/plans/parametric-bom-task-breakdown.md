# 参数化BOM系统 — 详细工作任务拆分

> **适用说明：** 每个任务都是一个可独立执行的单元，包含文件路径、具体改动、验收标准
> **总剩余工作量：** ~3.5天
> **整体完成度：** 37/40.5 天 ✅

---

## 📋 任务看板

```
┌────────────────────────────────────────────────┐
│ 🔴 P0 阻塞项（0.5天）                           │
│  T001 修evaluate 500 bug                       │
│  T002 统一API错误响应                           │
├────────────────────────────────────────────────┤
│ 🟡 P1 质量项（1.3天）                           │
│  T003 空公式/边界处理                            │
│  T004 API集成测试                                │
│  T005 数据迁移脚本验证                            │
├────────────────────────────────────────────────┤
│ 🟢 P2 文档（2.5天）                              │
│  T006 API文档（OpenAPI）                         │
│  T007 用户手册-管理员                             │
│  T008 用户手册-工程师                             │
│  T009 部署检查清单                                │
├────────────────────────────────────────────────┤
│ 🔵 P3 增强（2.5天）                              │
│  T010 配置导出/导入                               │
│  T011 配置版本管理                                │
│  T012 配置对比                                    │
│  T013 前端HTML文件拆分                             │
└────────────────────────────────────────────────┘
```

---

## 🔴 T001 — 修 evaluate API 500 bug（~0.2天）

### 文件
`src/backend/parametric_bom/bom_expander.py` 第114-115行

### 当前代码
```python
for cfg in configs:
    param_name = cfg.template.name  # ← 如果 template=None，这里炸
    if param_name in user_params:
        continue
```

### 问题
`PartParameterConfig.template` 是 `ForeignKey(PartAttributeFormula, on_delete=SET_NULL)`，如果模板被删了，`cfg.template` 就是 None，访问 `.name` 时抛出 `AttributeError`。

### 改动方案
```python
for cfg in configs:
    if cfg.template is None:
        # Template was deleted — skip or use cfg.name fallback
        param_name = cfg.name  # PartParameterConfig 有独立的 name 字段
    else:
        param_name = cfg.template.name
    if param_name in user_params:
        continue
```

### 验收
1. 创建一条 PartParameterConfig，不绑定 template（留空）
2. `POST /api/parametric-bom/evaluate/` 返回正常结果而非500
3. 已有正常数据不受影响，188测试仍然通过

### 风险
- 无。`cfg.name` 字段在 models.py 第124行定义，默认为空字符串，完全安全

---

## 🔴 T002 — 统一API错误响应（~0.3天）

### 文件
`src/backend/parametric_bom/api.py`

### 现状
目前每个视图函数各自 try/except，错误格式不统一，有些场景直接裸抛500。

### 改动
1. 在 `api.py` 顶部新增装饰器（或在文件末尾新增工具函数）：

```python
from functools import wraps
from rest_framework.response import Response

def api_error_handler(view_func):
    """Wrap API view function with standardized error response."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except ProductConfiguration.DoesNotExist as e:
            return Response({'error': 'Not found', 'detail': str(e)}, status=404)
        except Part.DoesNotExist as e:
            return Response({'error': 'Not found', 'detail': str(e)}, status=404)
        except (ParseError, ReferenceError, EvaluationError, TimeoutError) as e:
            return Response({'error': 'Formula error', 'detail': str(e)}, status=400)
        except Exception as e:
            # Log full traceback server-side, return sanitized message
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Unhandled error in {view_func.__name__}")
            return Response({'error': 'Internal error', 'detail': str(e)}, status=500)
    return wrapper
```

2. 给 `bom_evaluate`, `estimate_cost`, `formula_validate`, `formula_preview`, `rules_evaluate`, `generate_variant`, `inherit_params` 加上 `@api_error_handler` 装饰器。

### 验收
1. 传入非法 config_id → 返回 `{error: "Not found", detail: "..."}` 而非 HTML 500
2. 传入错误公式 → 返回 `{error: "Formula error", detail: "..."}` 而非 HTML 500
3. 正常请求不受影响

---

## 🟡 T003 — 空公式/边界处理（~0.3天）

### 文件
`src/backend/parametric_bom/formula_engine/evaluator.py`

### 改动点

| 场景 | 处理方式 | 位置 |
|------|---------|------|
| 空公式字符串 `""` | 视为无公式，返回 None | evaluate() 入口 |
| 空白公式 `"   "` | 同上，strip 后判空 | evaluate() 入口 |
| 公式引用的参数不在上下文中 | 返回友好提示 + 列出可用参数 | ReferenceError 信息增强 |
| 除零错误 | 返回 Infinity 或 None + 警告 | 除法运算处 |

### 具体代码修改

**evaluator.py 入口处：**
```python
def evaluate(expression, context=None, timeout_ms=500, max_depth=20):
    if not expression or not expression.strip():
        return None
    # ... 原有逻辑
```

**ReferenceError 消息增强（parser.py 或 evaluator.py）：**
```python
# 在引用解析处，当参数名不在 context 中时：
available = [k for k in context.keys() if isinstance(k, str)]
raise ReferenceError(
    f"参数 '{ref_name}' 不存在。可用参数：{', '.join(sorted(available[:20]))}"
)
```

### 验收
1. `evaluate("")` → None，不抛错
2. `evaluate("  ")` → None，不抛错
3. 引用不存在的参数时报错信息包含可用参数列表
4. 原有45个公式测试全部通过

---

## 🟡 T004 — API 集成测试（~1天）

### 文件（新建）
`src/backend/parametric_bom/tests/test_api.py`

### 测试用例（15个端点）

按优先级排序：

#### 第一组（核心流程，必须覆盖）
```python
class TestPartConfigAPI(TestCase):
    def test_list_part_configs(self): ...
    def test_create_part_config(self): ...
    def test_create_part_config_with_invalid_data(self): ...

class TestEvaluateAPI(TestCase):
    def test_evaluate_with_config_id(self): ...
    def test_evaluate_with_part_id(self): ...
    def test_evaluate_missing_params(self): ...
    def test_evaluate_with_null_template(self): ...  # 回归 T001

class TestFormulaValidateAPI(TestCase):
    def test_validate_valid_formula(self): ...
    def test_validate_invalid_formula(self): ...
```

#### 第二组（业务功能）
```python
class TestCostEstimateAPI(TestCase):
    def test_estimate_cost_for_config(self): ...

class TestRulesEvaluateAPI(TestCase):
    def test_rules_evaluate_basic(self): ...

class TestGenerateVariantAPI(TestCase):
    def test_generate_variant(self): ...

class TestInheritParamsAPI(TestCase):
    def test_inherit_params(self): ...
```

#### 第三组（CRUD）
```python
class TestBomItemConfigAPI(TestCase):
    def test_crud_bom_item_config(self): ...

class TestConfigurationsAPI(TestCase):
    def test_config_status_transition(self): ...
    def test_config_snapshot(self): ...
```

### 技术方案
1. 继承 `django.test.TestCase`（使用测试数据库）
2. 用 `setUpTestData` 创建测试 fixture（Part、PartAttributeFormula、PartParameterConfig 等）
3. 用 `self.client.post/GET` 调用 API
4. 断言 HTTP 状态码和响应体结构

### 验收
- 新增测试 ≥ 20个
- 全部通过，不破坏原有188个测试
- `python manage.py test parametric_bom.tests.test_api` 全部绿色

---

## 🟡 T005 — 数据迁移脚本验证（~0.3天）

### 背景
`0006_remove_mode_add_enable_flags.py` 已有数据迁移代码，但从未在生产库上实际跑过。

### 任务
1. 在 MySQL 测试库上先跑迁移，验证转换逻辑正确
2. 确保逆向迁移（enable_*→mode）也能恢复
3. 补充单元测试验证正向/逆向迁移

### 测试方法
在 `parametric_bom/tests/` 下新增迁移测试：
```python
class TestModeMigration(TestCase):
    def test_forward_migration(self):
        """Verify mode='qty_formula' → enable_qty_formula=True"""
        ...

    def test_reverse_migration(self):
        """Verify reverse migration restores mode value"""
        ...
```

### 验收
- 正向逆向迁移可成功回滚
- 迁移前后数据一致

---

## 🟢 T006 — API 文档（OpenAPI）（~0.5天）

### 文件
`src/backend/parametric_bom/api.py`

### 改动
给每个视图函数加 `@extend_schema` 装饰器，标注：
- 请求参数（request body）
- 响应结构
- 错误码

### 示例
```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

@extend_schema(
    summary='Evaluate parametric BOM',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'config_id': {'type': 'integer', 'description': 'ProductConfiguration ID'},
                'part_id': {'type': 'integer', 'description': 'Part ID'},
                'parameters': {
                    'type': 'object',
                    'description': 'User-provided parameter overrides',
                    'example': {'长度': 5000, '宽度': 800},
                },
            },
        },
    },
    responses={
        200: {'description': 'Evaluated parameters and BOM tree'},
        400: {'description': 'Missing or invalid parameters'},
        404: {'description': 'Config/Part not found'},
    },
)
def bom_evaluate(request):
    ...
```

### 验收
- 打开 InvenTree 的 Swagger UI 能看到完整的参数化 BOM API 文档
- 每个端点的请求/响应都有示例

---

## 🟢 T007 — 用户手册-管理员（~1天）

### 文件
`docs/user-guide-admin.md`（新建）

### 内容大纲

```markdown
# 参数化BOM系统 — 管理员指南

## 1. 安装与配置
- 插件安装（Python包安装方式）
- 启用插件（InvenTree插件面板）
- 数据库迁移
- 权限设置（parameter-admin / parameter-viewer）

## 2. 参数模板管理
- 创建参数模板（PartAttributeFormula）
- 模板分类管理
- 批量分配模板到产品分类

## 3. 参数配置管理
- 为产品配置参数
- 数据类型与取值范围
- 参数排序与显示控制

## 4. 规则引擎管理
- 约束规则配置
- 计算规则配置
- 可见性规则配置

## 5. 权限与安全
- 角色权限说明
- 多用户协作注意事项
```

### 验收
- 一个新手管理员按照指南能独立完成全部配置
- 每个步骤配截图（可选）

---

## 🟢 T008 — 用户手册-工程师（~1天）

### 文件
`docs/user-guide-engineer.md`（新建）

### 内容大纲

```markdown
# 参数化BOM系统 — 设计工程师指南

## 1. 快速上手
- 什么是参数化BOM
- 三种入门场景

## 2. 公式编写指南
- 语法速查（支持的操作符）
- 28个函数速查表（按类别分组）
- 参数引用语法 `param.参数名`
- 10个常用公式示例

## 3. BOM配置
- 8种参数化模式详解
- 模式组合使用（如 qty_formula + conditional）
- 候选零件配置
- 变体生成

## 4. 产品配置操作
- 三步配置引导
- 参数调整与实时预览
- BOM生成与导出

## 5. 常见问题
- 公式报错怎么办
- 参数值不生效
- BOM展开异常排查
```

### 验收
- 工程师看完能独立编写复杂公式
- 包含完整函数速查表和示例

---

## 🟢 T009 — 部署检查清单（~0.3天）

### 文件
`docs/deployment-checklist.md`（新建）

### 内容

```markdown
# 参数化BOM系统 — 部署检查清单

## 预部署
- [ ] Python 3.10+ / 3.11+
- [ ] Django 4.2+
- [ ] InvenTree 0.16+
- [ ] MySQL 8.0+ 或 PostgreSQL 14+

## 部署步骤
- [ ] `pip install -e .` 安装插件
- [ ] `python manage.py migrate parametric_bom` 数据库迁移
- [ ] `python manage.py collectstatic` 静态文件
- [ ] 重启 InvenTree server

## 验证
- [ ] 访问 /parametric-bom/ 正常加载
- [ ] 创建参数模板正常
- [ ] 配置BOM展开正常
- [ ] 测试 188/188 通过

## 生产环境
- [ ] DEBUG=False
- [ ] Nginx 静态文件服务配置
- [ ] Redis 缓存（可选）
- [ ] 数据库备份策略
```

---

## 🔵 T010 — 配置导出/导入（~0.5天）

### 文件
- `src/backend/parametric_bom/api.py` — 新增导出/导入端点
- `src/backend/parametric_bom/urls.py` — 注册路由

### 新增API

```python
@extend_schema(summary='Export configuration as JSON')
@api_view(['GET'])
@api_error_handler
def config_export(request, config_id):
    """Export a ProductConfiguration as a portable JSON object."""
    config = ProductConfiguration.objects.get(pk=config_id)
    data = {
        'version': 1,
        'exported_at': datetime.now().isoformat(),
        'part': {
            'id': config.part.pk,
            'name': config.part.name,
            'ipn': config.part.IPN,
        },
        'parameters': {
            pv.parameter_name: pv.value
            for pv in config.parameter_values.all()
        },
        'status': config.status,
        'bom_snapshot': config.bom_snapshot,
    }
    return Response(data)


@extend_schema(summary='Import configuration from JSON')
@api_view(['POST'])
@api_error_handler
def config_import(request):
    """Import a ProductConfiguration from a JSON object."""
    data = request.data
    # ... 创建配置并填充参数
```

### route
```python
path('configs/<int:config_id>/export/', config_export, name='config-export'),
path('configs/import/', config_import, name='config-import'),
```

### 验收
1. 导出一个配置 → 下载JSON文件
2. 导入该JSON → 新配置与原配置参数一致
3. 导入无效JSON → 友好错误提示

---

## 🔵 T011 — 配置版本管理（~1天）

### 文件
- `src/backend/parametric_bom/models.py` — 新增 ConfigurationVersion 模型
- `src/backend/parametric_bom/api.py` — 新增版本相关端点
- `src/backend/parametric_bom/urls.py` — 注册路由

### 新增模型
```python
class ConfigurationVersion(models.Model):
    """Auto-created version when a ProductConfiguration is modified."""
    config = models.ForeignKey(
        ProductConfiguration, on_delete=models.CASCADE,
        related_name='versions',
    )
    revision = models.PositiveIntegerField()
    parameter_snapshot = models.JSONField()
    bom_snapshot = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    change_note = models.TextField(blank=True)

    class Meta:
        unique_together = ('config', 'revision')
        ordering = ['-revision']
```

### 自动版本创建
在 `config_set_params` 视图中，修改参数前自动创建新版本：
```python
# 在 config_set_params 中
current_revision = config.versions.first()
next_revision = (current_revision.revision + 1) if current_revision else 1
ConfigurationVersion.objects.create(
    config=config,
    revision=next_revision,
    parameter_snapshot={pv.parameter_name: pv.value for pv in config.parameter_values.all()},
    bom_snapshot=config.bom_snapshot,
    created_by=request.user,
)
```

### 验收
1. 修改配置参数后自动+1版本
2. 查看版本历史能列出所有版本
3. 回滚到旧版本后参数恢复

---

## 🔵 T012 — 配置对比（~0.5天）

### 文件
- `src/backend/parametric_bom/api.py` — 新增对比端点
- `configurator.html` — 前端对比展示

### 新增API
```python
@extend_schema(summary='Compare two configuration versions')
@api_view(['GET'])
@api_error_handler
def config_compare(request, config_id):
    """Compare the latest version with a specific revision."""
    version_a_id = request.GET.get('v1')
    version_b_id = request.GET.get('v2')
    v1 = ConfigurationVersion.objects.get(pk=version_a_id)
    v2 = ConfigurationVersion.objects.get(pk=version_b_id)

    diff = {
        'parameters': _dict_diff(v1.parameter_snapshot, v2.parameter_snapshot),
        'bom': _bom_diff(v1.bom_snapshot, v2.bom_snapshot),
    }
    return Response(diff)
```

### 前端展示
在 configurator.html 新增对比面板，用绿色/红色高亮显示差异。

### 验收
1. 选择两个版本 → 显示参数值差异
2. BOM项数量/条件差异清晰可见

---

## 🔵 T013 — 前端HTML文件拆分（~0.5天）

### 文件
- `src/backend/parametric_bom/static/parametric_bom/css/configurator.css`（新建）
- `src/backend/parametric_bom/static/parametric_bom/js/configurator.js`（新建）
- `src/backend/parametric_bom/templates/parametric_bom/configurator.html`（修改）

### 方案
1. 从 `configurator.html` 中提取全部 `<style>` 内容到 `configurator.css`
2. 从 `configurator.html` 中提取全部 `<script>` 内容到 `configurator.js`
3. 在 `configurator.html` 中用 `{% static %}` 引用这两个文件
4. 保留 Django 模板变量部分（`{% if %}`, `{{ }}`）在 .html 中

⚠️ **注意**
- Django 模板变量（`{% url %}`, `{% csrf_token %}`, `{{ initial_page }}` 等）必须在 .html 中保留
- JS 中如果有通过模板变量注入的数据（如 `window.initialPage = '{{ initial_page|escapejs }}'`），需在 .html 中留一个内联 `<script>` 块

### 验收
1. 页面功能完全不变
2. CSS/JS 被浏览器正确以独立文件加载
3. 6000行单文件 → ~200行html + ~3000行css + ~2700行js

---

## 附录：已完成功能清单（37天工作量，参考）

| 大模块 | 天数 | 子模块数 |
|--------|------|---------|
| 数据模型（11个模型） | 7.5 | 11 |
| 公式引擎（词法/解析/求值/28函数/沙箱） | 6.5 | 11 |
| 核心引擎（BOM展开/规则/变体/成本/继承/工作流） | 6 | 6 |
| API层（20个端点） | 6.5 | 20 |
| 前端（11个界面模块） | 5 | 11 |
| 测试（188个测试用例） | 3.9 | 8组 |
| 设计文档（2260行） | 2 | 1 |
| **合计** | **~37.4** | **68** |
