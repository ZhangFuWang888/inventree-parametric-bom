# 项目（Project）模块 — 开发文档

## 1. 概述

在 InvenTree 参数化BOM 系统中增加 **项目（Project）** 概念，将"设计→采购→销售"流程串联起来。项目是一个客户订单落地后的正式追踪单元，管理从 BOM 配置到零件采购再到成品交付的全链路。

### 核心流程

```
购物车（缓存池）            ← 参数配置、加零件
     │
     ▼ 确认下单
项目（正式落地）
     ├── 产品配置快照        ← 参数化BOM+展开的零件清单
     ├── 静态零件
     ├── 采购订单             ← 从零件清单生成（向供应商买料）
     └── 销售订单             ← 向客户收费
```

---

## 2. 数据模型

### 2.1 Project（项目）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | AutoField | 主键 |
| name | CharField(256) | 项目名称（必填） |
| project_code | CharField(64) | 自动生成的项目编号，格式 `PRJ-YYYYMMDD-XXXX` |
| customer | FK → Company | InvenTree 客户公司（可空） |
| status | CharField(32) | 状态：draft/active/purchasing/production/delivery/completed/cancelled |
| description | TextField | 项目描述 |
| manager | FK → User | 项目负责人（可空） |
| deadline | DateField | 截止日期（可空） |
| created_by | FK → User | 创建人 |
| created_at | DateTimeField | 创建时间 |
| updated_at | DateTimeField | 最后更新时间 |
| total_cost | DecimalField | 项目总成本（自动汇总） |
| total_price | DecimalField | 项目总售价（自动汇总） |
| notes | TextField | 内部备注 |

### 2.2 ProjectItem（项目条目）

项目里的每一项，可以是参数化产品配置快照，也可以是静态零件。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | AutoField | 主键 |
| project | FK → Project | 所属项目 |
| item_type | CharField(20) | 类型：`configuration` / `part` |
| product_config | FK → ProductConfiguration | 参数化配置快照（可空） |
| part | FK → Part | 静态零件（可空） |
| title | CharField(256) | 显示名称 |
| quantity | PositiveIntegerField | 数量，默认 1 |
| bom_snapshot | JSONField | BOM 展开结果快照（configuration 类型用） |
| unit_cost | DecimalField | 单位成本 |
| unit_price | DecimalField | 单位售价 |
| notes | TextField | 备注 |
| sort_order | IntegerField | 排序 |
| created_at | DateTimeField | 创建时间 |

### 2.3 关联关系

```
Project ──1:N──→ ProjectItem
  │                  ├── config: ProductConfiguration（参数化配置快照）
  │                  └── part: Part（静态零件）
  │
  ├── customer: Company（InvenTree客户）
  ├── manager: User
  ├── purchase_orders: PurchaseOrder（关联采购订单）
  └── sales_orders: SalesOrder（关联销售订单）
```

### 2.4 状态机

```
draft ─→ active ─→ purchasing ─→ production ─→ delivery ─→ completed
  │         │                                              │
  └── cancelled                                            └── archived
```

- **draft**: 草稿，刚创建未开始
- **active**: 进行中
- **purchasing**: 采购中（有关联的采购订单）
- **production**: 生产中
- **delivery**: 交付中
draft ─→ active ─→ purchasing ─→ production ─→ delivery ─→ completed
  │         │                                              │
  └── cancelled                                            └── archived

---

## 3. 权限系统

### 3.1 现有权限现状

当前参数化BOM模块的所有 API 只用了 `permissions.IsAuthenticated`——**任何登录用户拥有完全相同的权限**，没有区分管理员/普通用户，也没有数据级权限。

### 3.2 项目权限层级

项目模块引入**三级权限**，在现有 `IsAuthenticated` 基础上叠加：

```
第一层：站点级别（Django is_staff）
  ├── 管理员（is_staff=True）→ 所有项目读/写
  └── 普通用户（is_staff=False）→ 仅自己的项目

第二层：项目级别（Owner/Member）
  ├── Owner（创建者）→ 编辑/删除/管理项目
  ├── Member（成员）→ 查看项目内容
  └── 非成员→ 不可见（公共项目除外）

第三层：操作级别（细粒度）
  ├── 查看项目 → 管理员/Owner/Member
  ├── 编辑项目 → 管理员/Owner
  ├── 删除项目 → 管理员/Owner
  ├── 生成采购单 → 管理员/Owner
  └── 生成销售单 → 管理员/Owner
```

### 3.3 权限模型设计

在 `Project` 模型中添加权限相关字段：

```python
class Project(models.Model):
    # ... 已有字段 ...
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_projects',
        verbose_name=_('Owner'),
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('Public'),
        help_text=_('Non-members can view this project'),
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='project_memberships',
        verbose_name=_('Members'),
    )
```

### 3.4 API 权限控制

自定义权限类 `ProjectPermission`：

```python
class ProjectPermission(permissions.BasePermission):
    """Three-tier project permission check."""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Tier 1: Staff → full access
        if user.is_staff:
            return True
        
        # Tier 2: Owner → full access
        if obj.owner == user:
            return True
        
        # Safe methods (GET/HEAD/OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            # Member or public project → can view
            if obj.is_public or obj.members.filter(id=user.id).exists():
                return True
            return False
        
        # Write methods → owner only
        return False
```

### 3.5 自动设置 Owner

- 创建项目时自动将当前用户设为 `owner`
- `from-cart` 端点的 `perform_create` 中自动赋值 `owner=request.user`

### 3.6 列表级过滤

重写 ViewSet 的 `get_queryset`：

```python
def get_queryset(self):
    user = self.request.user
    if user.is_staff:
        return Project.objects.all()
    return Project.objects.filter(
        models.Q(owner=user) | 
        models.Q(members=user) | 
        models.Q(is_public=True)
    ).distinct()
```

### 3.7 前端权限处理

| 角色 | 项目列表 | 项目详情 | 编辑/删除 | 操作按钮 |
|------|----------|----------|-----------|----------|
| 管理员 | 全部可见 | 全部 | 可编辑/删除 | 全部显示 |
| Owner | 自己的 | 自己的 | 可编辑/删除 | 全部显示 |
| Member | 自己的+加入的 | 可查看 | 不可编辑 | 隐藏编辑/操作按钮 |
| 非成员 | 仅公开项目 | 仅公开项目 | 不可操作 | 全部隐藏 |

前端通过 API 返回的 `user_role` 字段（`admin`/`owner`/`member`/`none`）控制按钮显隐。

### 3.8 与 InvenTree 原生权限的关系

InvenTree 本身的权限系统（Django Group + Permission）仍然有效：
- 只有 `is_staff=True` 的用户被视为管理员
- 普通用户的 Django Model Permissions 由 InvenTree 原生控制
- 项目权限是**叠加在 Django 认证之上**的额外一层

> **简化设计**：不引入复杂的 RBAC 表、不依赖 InvenTree 的 Group 系统。三级权限清晰且与现有代码兼容，迁移成本低。

---

## 4. API 接口

### 4.1 项目管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/parametric-bom/projects/` | 项目列表（分页、搜索、筛选） |
| POST | `/api/parametric-bom/projects/` | 创建项目 |
| GET | `/api/parametric-bom/projects/{id}/` | 项目详情 |
| PATCH | `/api/parametric-bom/projects/{id}/` | 更新项目 |
| DELETE | `/api/parametric-bom/projects/{id}/` | 删除项目 |
| GET | `/api/parametric-bom/projects/{id}/items/` | 项目条目列表 |
| POST | `/api/parametric-bom/projects/{id}/items/` | 添加条目 |
| DELETE | `/api/parametric-bom/projects/{id}/items/{item_id}/` | 移除条目 |

### 4.2 购物车→项目流转

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/parametric-bom/projects/from-cart/` | 将购物车内容打包成项目 |

Request:
```json
{
  "name": "XX客户货架项目-202605",
  "customer_id": 5,
  "description": "...",
  "cart_item_ids": [1, 2, 3]
}
```

### 4.3 采购/销售订单生成

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/parametric-bom/projects/{id}/create-purchase-orders/` | 从项目零件清单生成采购订单 |
| POST | `/api/parametric-bom/projects/{id}/create-sales-order/` | 从项目生成销售订单 |

### 4.4 成本/统计

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/parametric-bom/projects/{id}/cost-summary/` | 项目成本汇总 |
| GET | `/api/parametric-bom/projects/{id}/export/` | 导出项目报告（CSV） |

---

## 5. 前端页面

### 5.1 项目列表页

路径: `/parametric-bom/projects/`

功能：
- 卡片或表格视图展示所有项目
- 搜索（名称/编号/客户）
- 状态筛选
- 新建按钮
- 点击进入详情

### 5.2 项目详情页

路径: `/parametric-bom/projects/{id}/`

功能：
- 项目基本信息
- 状态切换（下拉选择）
- Tab 切换：
  - **产品/零件** — 项目条目列表（参数化配置+静态零件），可添加/移除
  - **采购订单** — 关联的采购订单列表，点击"生成采购订单"按钮
  - **销售订单** — 关联的销售订单列表
  - **成本** — 成本汇总表
- 编辑/删除按钮

### 5.3 新建/编辑页

路径: `/parametric-bom/projects/new/` 或弹窗

表单：
- 项目名称（必填）
- 客户（下拉选择 InvenTree Company）
- 负责人（下拉选择用户）
- 截止日期
- 描述

### 5.4 购物车→项目按钮

购物车页面增加"提交项目"按钮，弹窗选择/输入：
- 项目名称
- 客户
- 确认后打包生成项目，清空购物车

---

## 6. 工作流集成

### 6.1 购物车→项目

```
购物车 → 点击"提交项目" → 填写项目信息 → 确认
  ↓
创建 Project（status=draft）
  ↓
为每个 CartItem 创建 ProjectItem
  ├── parametric → 复制 ProductConfiguration + bom_snapshot
  └── static → 关联 Part
  ↓
清空购物车
  ↓
跳转到项目详情页
```

### 6.2 项目→采购订单

```
项目详情 → 点击"生成采购订单"
  ↓
汇总所有 ProjectItem 的 BOM 展开零件 → 去重+合并数量
  ↓
按供应商分组 → 生成多个 PurchaseOrder
  ↓
跳转到采购订单列表
```

### 6.3 项目→销售订单

```
项目详情 → 点击"生成销售订单"
  ↓
汇总所有 ProjectItem → 生成 SalesOrderLineItem
  ↓
创建 SalesOrder（关联 customer）
  ↓
跳转到销售订单详情
```

---

## 7. 涉及文件

### 后端（src/backend/parametric_bom/）

| 文件 | 改动 |
|------|------|
| `models.py` | 新增 Project、ProjectItem 模型 |
| `serializers.py` | 新增 ProjectSerializer、ProjectItemSerializer |
| `api.py` | 新增 ProjectViewSet、ProjectItemViewSet |
| `urls.py` | 注册新的 router |
| `views.py` | 新增项目页面视图（如需） |
| `admin.py` | 注册到 Django admin |

### 前端（src/backend/parametric_bom/static/parametric_bom/js/）

| 文件 | 改动 |
|------|------|
| `products.js` | 新增项目列表/详情/编辑渲染函数 |
| `configurator.js` | 购物车添加"提交项目"按钮 |
| `init.js` | 新增项目路由和初始化 |

### 模板（templates/parametric_bom/）

| 文件 | 改动 |
|------|------|
| `projects.html` | 项目列表页模板（新增） |
| `project_detail.html` | 项目详情页模板（新增） |
| `configurator_cart_modals.html` | 添加"提交项目"弹窗 |

---

## 8. 实现步骤

### Phase 1：数据模型 + API（后端核心）

1. 在 `models.py` 新增 `ProjectChoices`（状态枚举）、`ProjectItemTypeChoices`
2. 新增 `Project` 模型（含 project_code 自动生成逻辑）
3. 新增 `ProjectItem` 模型
4. 运行 `makemigrations` + `migrate`
5. 在 `serializers.py` 新增序列化器
6. 在 `api.py` 新增 ViewSet + `from-cart` 自定义端点
7. 生成采购订单和销售订单的端点
8. 注册 URL
9. 在 `admin.py` 注册新的 ModelAdmin

### Phase 2：前端页面

1. 新建 `templates/parametric_bom/projects.html` 模板
2. 新建 `templates/parametric_bom/project_detail.html` 模板
3. 在 `products.js` 或新文件 `projects.js` 添加前端渲染函数
4. 购物车添加"提交项目"按钮和相关弹窗
5. 注册前端路由（`init.js`）

### Phase 3：工作流集成

1. 购物车→项目打包逻辑
2. 项目→采购订单生成逻辑
3. 项目→销售订单生成逻辑
4. 成本汇总计算

### Phase 4：报表+增强

1. 项目导出 CSV ✅
2. 项目模板功能 ✅
3. 变更日志 ✅
4. 附件上传 ✅（InvenTreeAttachmentMixin + API + 前端Tab）

---

## 9. 测试计划

| 测试项 | 说明 |
|--------|------|
| 创建项目 | 正常创建/缺少必填/重复编号 |
| 添加项目条目 | 添加配置/零件/混合 |
| 购物车→项目 | 全流程测试 |
| 生成采购订单 | 正确按供应商分组 |
| 生成销售订单 | 正确汇总条目 |
| 状态流转 | 每个状态转换的权限和约束 |
| 权限 | 普通用户/管理员/超管 |
| 成本汇总 | 单价×数量 计算正确 |

---

## 10. 未决问题

> 以下问题请在开发前确认

| # | 问题 | 选项 |
|---|------|------|
| 1 | 项目编号格式 | `PRJ-YYYYMMDD-XXXX` 还是纯数字自增？ |
| 2 | 采购订单是否需要手动确认再创建？ | 一键生成 vs 预览确认 |
| 3 | 一个零件在多个项目中的库存预留 | 当前不做 vs 简单标记 |
| 4 | 项目删除行为 | 软删除（保留数据） vs 硬删除 |
| 5 | 项目模板功能 | 第一期做 vs 后续迭代 |
