// projects.js — 项目管理页面

const PROJECT_API = '/api/parametric-bom/projects';

// ── API helper ──
async function projectApi(method, path, data) {
  try {
    const opts = {
      method,
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
    };
    if (data) opts.body = JSON.stringify(data);
    const resp = await fetch(PROJECT_API + path, opts);
    const body = resp.status === 204 ? {} : await resp.json();
    return { data: body, status: resp.status, ok: resp.ok };
  } catch (e) {
    return { error: e.message };
  }
}

// ── Status badge ──
function projectStatusBadge(status) {
  const m = {
    draft: { label: 'Draft', cls: 'bg-gray-100 text-gray-600' },
    active: { label: 'Active', cls: 'bg-blue-100 text-blue-700' },
    purchasing: { label: '采购中', cls: 'bg-yellow-100 text-yellow-700' },
    production: { label: '生产中', cls: 'bg-orange-100 text-orange-700' },
    delivery: { label: '交付中', cls: 'bg-purple-100 text-purple-700' },
    completed: { label: '已完成', cls: 'bg-green-100 text-green-700' },
    cancelled: { label: '已取消', cls: 'bg-red-100 text-red-600' },
    archived: { label: '已归档', cls: 'bg-slate-100 text-slate-500' },
  };
  const s = m[status] || { label: status, cls: 'bg-gray-100 text-gray-600' };
  return `<span class="inline-block px-2 py-0.5 rounded text-xs font-medium ${s.cls}">${s.label}</span>`;
}

// ── Render project list ──
async function renderProjectList() {
  const container = document.getElementById('projects-content');
  if (!container) return;

  const page = window._projectPage || 1;
  const limit = 20;

  // Build query params
  const params = new URLSearchParams();
  params.set('inactive', '0');
  params.set('limit', limit);
  params.set('offset', (page - 1) * limit);

  const search = window._projectSearch || '';
  if (search) params.set('search', search);

  const order = window._projectOrder || '-created_at';
  params.set('ordering', order);

  const result = await projectApi('GET', `/?${params.toString()}`);
  const data = result.data;
  const projects = result.ok ? (data.results || data || []) : [];
  const total = data.count || projects.length;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  let html = `
  <div class="card mb-3">
    <div class="card-header flex items-center justify-between flex-wrap gap-2">
      <span>📋 项目管理 <span class="text-xs text-gray-400 font-normal">(共 ${total} 个)</span></span>
      <button class="btn btn-sm btn-secondary" onclick="showNewProjectDialog()">新建项目</button>
    </div>
    <div class="p-2 border-b border-gray-100 flex items-center gap-2 flex-wrap">
      <input class="input-field flex-1 min-w-[180px]" id="project-search-input"
             placeholder="🔍 搜索项目名称/编号..."
             value="${escHtml(search)}"
             oninput="debounceProjectSearch()">
      <select class="input-field w-auto text-xs" id="project-order-select"
              onchange="changeProjectOrder(this.value)">
        <option value="-created_at" ${order === '-created_at' ? 'selected' : ''}>最新创建</option>
        <option value="created_at" ${order === 'created_at' ? 'selected' : ''}>最早创建</option>
        <option value="name" ${order === 'name' ? 'selected' : ''}>名称 A-Z</option>
        <option value="-name" ${order === '-name' ? 'selected' : ''}>名称 Z-A</option>
        <option value="-project_code" ${order === '-project_code' ? 'selected' : ''}>编号降序</option>
        <option value="project_code" ${order === 'project_code' ? 'selected' : ''}>编号升序</option>
      </select>
      ${search ? `<button class="btn btn-sm btn-ghost text-gray-400" onclick="clearProjectSearch()">✕ 清除</button>` : ''}
    </div>
    ${projects.length === 0 ? `
    <div class="empty-state p-8 text-center">
      <div class="icon text-3xl mb-2">📦</div>
      <p class="text-gray-500 text-sm">${search ? '未找到匹配项目' : '暂无项目，点击"新建项目"或从购物车提交项目'}</p>
    </div>` : `
    <div class="overflow-x-auto">
      <table class="w-full text-xs">
        <thead>
          <tr class="border-b border-gray-200 text-gray-500 uppercase tracking-wider">
            <th class="p-2 text-left">项目编号</th>
            <th class="p-2 text-left">名称</th>
            <th class="p-2 text-left">客户</th>
            <th class="p-2 text-left">状态</th>
            <th class="p-2 text-left">负责</th>
            <th class="p-2 text-right">条目</th>
            <th class="p-2 text-left">截止</th>
            <th class="p-2 text-left">操作</th>
          </tr>
        </thead>
        <tbody id="project-list-body">
          ${renderProjectRows(projects)}
        </tbody>
      </table>
      ${renderPagination(page, totalPages, total)}
    </div>`}
  </div>`;

  container.innerHTML = html;
}

function changeProjectOrder(value) {
  window._projectOrder = value;
  window._projectPage = 1;
  renderProjectList();
}

let _searchTimer = null;
function debounceProjectSearch() {
  clearTimeout(_searchTimer);
  _searchTimer = setTimeout(() => {
    const val = document.getElementById('project-search-input')?.value?.trim() || '';
    window._projectSearch = val;
    window._projectPage = 1;
    renderProjectList();
  }, 300);
}

function clearProjectSearch() {
  window._projectSearch = '';
  window._projectPage = 1;
  const inp = document.getElementById('project-search-input');
  if (inp) inp.value = '';
  renderProjectList();
}

function renderProjectRows(projects) {
  return projects.map(p => `
  <tr class="border-b border-gray-100 hover:bg-gray-50 cursor-pointer" onclick="showProjectDetail(${p.id})">
    <td class="p-2 font-mono text-blue-600">${p.project_code}</td>
    <td class="p-2 font-medium">${escHtml(p.name)}</td>
    <td class="p-2 text-gray-500">${p.customer_name || '-'}</td>
    <td class="p-2">${projectStatusBadge(p.status)}</td>
    <td class="p-2 text-gray-500">${p.owner_name || '-'}</td>
    <td class="p-2 text-right">${p.item_count}</td>
    <td class="p-2 text-gray-400">${p.deadline || '-'}</td>
    <td class="p-2">
      <button class="text-blue-500 hover:text-blue-700" onclick="event.stopPropagation(); showProjectDetail(${p.id})">查看</button>
      ${p.user_role === 'owner' || p.user_permissions?.includes('delete_project') ? `
      <button class="text-red-500 hover:text-red-700 ml-2" onclick="event.stopPropagation(); deleteProject(${p.id})">删除</button>` : ''}
    </td>
  </tr>`).join('');
}

function goToProjectPage(page) {
  window._projectPage = page;
  renderProjectList();
}

function renderPagination(page, totalPages, total) {
  if (totalPages <= 1) return '';

  let pages = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, page + 2);
  for (let i = start; i <= end; i++) pages.push(i);

  let html = `<div class="flex items-center justify-center gap-1 py-3 text-xs">`;

  // Prev
  html += page > 1
    ? `<button class="px-2 py-1 border rounded hover:bg-gray-100" onclick="goToProjectPage(${page - 1})">‹</button>`
    : `<span class="px-2 py-1 border rounded text-gray-300">‹</span>`;

  // First page + ellipsis
  if (start > 1) {
    html += `<button class="px-2 py-1 border rounded hover:bg-gray-100" onclick="goToProjectPage(1)">1</button>`;
    if (start > 2) html += `<span class="px-1 text-gray-400">…</span>`;
  }

  // Page numbers
  pages.forEach(i => {
    html += i === page
      ? `<span class="px-2 py-1 border rounded bg-blue-600 text-white font-medium">${i}</span>`
      : `<button class="px-2 py-1 border rounded hover:bg-gray-100" onclick="goToProjectPage(${i})">${i}</button>`;
  });

  // Last page + ellipsis
  if (end < totalPages) {
    if (end < totalPages - 1) html += `<span class="px-1 text-gray-400">…</span>`;
    html += `<button class="px-2 py-1 border rounded hover:bg-gray-100" onclick="goToProjectPage(${totalPages})">${totalPages}</button>`;
  }

  // Next
  html += page < totalPages
    ? `<button class="px-2 py-1 border rounded hover:bg-gray-100" onclick="goToProjectPage(${page + 1})">›</button>`
    : `<span class="px-2 py-1 border rounded text-gray-300">›</span>`;

  html += ` <span class="text-gray-400 ml-2">${page}/${totalPages}</span></div>`;
  return html;
}

// ── Show project detail ──
async function showProjectDetail(projectId) {
  const result = await projectApi('GET', `/${projectId}/`);
  if (!result.ok) { setStatus('error', '加载项目失败'); return; }
  const p = result.data;
  window._currentProjectId = projectId;

  const container = document.getElementById('project-detail-content');
  if (!container) { switchPage('project-detail'); await delay(50); return showProjectDetail(projectId); }

  // Switch to detail page
  switchPage('project-detail');

  const canEdit = p.user_role === 'owner' || p.user_permissions?.includes('edit_project');
  const canManageMembers = p.user_role === 'owner' || p.user_permissions?.includes('manage_members');

  let html = `
  <div class="card mb-3">
    <div class="card-header flex items-center justify-between flex-wrap gap-2">
      <div class="flex items-center gap-2">
        <span>${p.is_template ? '📌' : '📋'}</span>
        <span class="text-lg font-semibold">${escHtml(p.project_code)}</span>
        <span class="text-base text-gray-700 ml-1">${escHtml(p.name)}</span>
        ${p.is_template ? '<span class="inline-block px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700">模板</span>' : ''}
        ${projectStatusBadge(p.status)}
      </div>
      <div class="flex items-center gap-2">
        ${canEdit ? `
        <button class="btn btn-sm btn-secondary" onclick="editProjectField('name')">编辑</button>
        <button class="btn btn-sm btn-secondary" onclick="confirmDeleteProject(${p.id})">删除</button>` : ''}
        ${!p.is_template ? `<button class="btn btn-sm btn-secondary" onclick="saveAsTemplate(${p.id})">存为模板</button>` : ''}
        ${p.is_template ? `<button class="btn btn-sm btn-secondary" onclick="createFromTemplate(${p.id})">从模板创建</button>` : ''}
        <button class="btn btn-sm btn-secondary" onclick="downloadProjectCsv(${p.id})">导出</button>
        <button class="btn btn-sm btn-secondary" onclick="switchPage('projects')">返回</button>
      </div>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3 text-xs">
      <div><span class="text-gray-400">客户</span><br><span class="font-medium">${p.customer_name || '-'}</span></div>
      <div><span class="text-gray-400">负责人</span><br><span class="font-medium">${p.owner_name || '-'}</span></div>
      <div><span class="text-gray-400">截止日期</span><br><span class="font-medium">${p.deadline || '-'}</span></div>
      <div><span class="text-gray-400">创建时间</span><br><span class="font-medium">${new Date(p.created_at).toLocaleDateString('zh-CN')}</span></div>
    </div>
    ${p.description ? `<div class="text-xs text-gray-600 mb-3 p-2 bg-gray-50 rounded">${escHtml(p.description)}</div>` : ''}
  </div>

  <!-- Tabs -->
  <div class="flex gap-0 border-b border-gray-200 mb-3">
    <button class="pd-tab active" data-proj-tab="items" onclick="switchProjectTab('items')">产品/零件</button>
    <button class="pd-tab" data-proj-tab="cost" onclick="switchProjectTab('cost')">成本</button>
    <button class="pd-tab" data-proj-tab="orders" onclick="switchProjectTab('orders')">订单</button>
    <button class="pd-tab" data-proj-tab="logs" onclick="switchProjectTab('logs')">日志</button>
    <button class="pd-tab" data-proj-tab="attachments" onclick="switchProjectTab('attachments')">附件</button>
    <button class="pd-tab" data-proj-tab="members" onclick="switchProjectTab('members')">成员</button>
  </div>

  <div id="project-tab-items" class="proj-tab-panel">
    ${p.items && p.items.length ? `
    <div class="card">
      <div class="card-header flex items-center justify-between">
        <span>项目条目</span>
        ${canEdit ? `<button class="btn btn-sm btn-secondary" onclick="showAddItemDialog(${p.id})">添加</button>` : ''}
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-gray-200 text-gray-500">
              <th class="p-2 text-left">名称</th>
              <th class="p-2 text-left">类型</th>
              <th class="p-2 text-right">数量</th>
              <th class="p-2 text-right">单价</th>
              <th class="p-2 text-right">小计</th>
              ${canEdit ? '<th class="p-2 text-center">操作</th>' : ''}
            </tr>
          </thead>
          <tbody>
            ${p.items.map(item => {
              const subtotal = (parseFloat(item.unit_price || 0) * item.quantity).toFixed(2);
              return `<tr class="border-b border-gray-100">
                <td class="p-2 font-medium">${escHtml(item.title)}${item.bom_snapshot ? ' <span class="text-[10px] text-gray-400">(含BOM)</span>' : ''}</td>
                <td class="p-2">${item.item_type === 'configuration' ? '🔧 参数化配置' : '⚙️ 静态零件'}</td>
                <td class="p-2 text-right">×${item.quantity}</td>
                <td class="p-2 text-right">¥${(item.unit_price || 0).toFixed(2)}</td>
                <td class="p-2 text-right font-medium">¥${subtotal}</td>
                ${canEdit ? `<td class="p-2 text-center"><button class="text-red-500 hover:text-red-700" onclick="removeProjectItem(${p.id}, ${item.id})">✕</button></td>` : ''}
              </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>` : `<div class="card"><div class="empty-state p-4 text-center text-gray-400 text-sm">暂无项目条目</div></div>`}

    ${canEdit ? `
    <div class="flex items-center gap-2 mt-3">
      <button class="btn btn-sm btn-secondary" onclick="generatePurchaseOrders(${p.id})">生成采购订单</button>
      <button class="btn btn-sm btn-secondary" onclick="generateSalesOrder(${p.id})">生成销售订单</button>
    </div>` : ''}
  </div>

  <div id="project-tab-cost" class="proj-tab-panel" style="display:none">
    <div class="card" id="project-cost-content">
      <div class="empty-state p-4 text-center text-gray-400 text-sm">⏳ 加载成本数据...</div>
    </div>
  </div>

  <div id="project-tab-orders" class="proj-tab-panel" style="display:none">
    <div class="card" id="project-orders-content">
      <div class="empty-state p-4 text-center text-gray-400 text-sm">⏳ 加载关联订单...</div>
    </div>
  </div>

  <div id="project-tab-logs" class="proj-tab-panel" style="display:none">
    <div class="card" id="project-logs-content">
      <div class="empty-state p-4 text-center text-gray-400 text-sm">📝 加载变更日志...</div>
    </div>
  </div>

  <!-- Attachments tab -->
  <div id="project-tab-attachments" class="proj-tab-panel" style="display:none">
    <div class="card" id="project-attachments-content">
      <div class="empty-state p-4 text-center text-gray-400 text-sm">${'📎 加载附件列表...'}</div>
    </div>
  </div>

  <!-- Members tab -->
  <div id="project-tab-members" class="proj-tab-panel" style="display:none">
    <div class="card" id="project-members-content">
      <div class="empty-state p-4 text-center text-gray-400 text-sm">${'👥 加载成员列表...'}</div>
    </div>
  </div>`;

  container.innerHTML = html;
  window._projectData = p;
  loadProjectCost(projectId);
}

// ── Project tabs ──
function switchProjectTab(tab) {
  document.querySelectorAll('.proj-tab-panel').forEach(el => el.style.display = 'none');
  document.querySelectorAll('[data-proj-tab]').forEach(el => el.classList.remove('active'));
  const panel = document.getElementById('project-tab-' + tab);
  if (panel) panel.style.display = '';
  const btn = document.querySelector(`[data-proj-tab="${tab}"]`);
  if (btn) btn.classList.add('active');
  if (tab === 'logs') loadProjectLogs(window._currentProjectId);
  if (tab === 'attachments') loadProjectAttachments(window._currentProjectId);
  if (tab === 'members') loadProjectMembers(window._currentProjectId);
  if (tab === 'orders') loadProjectOrders(window._currentProjectId);
}

// ── Load cost data ──
async function loadProjectCost(projectId) {
  const result = await projectApi('GET', `/${projectId}/cost_summary/`);
  const container = document.getElementById('project-cost-content');
  if (!container) return;
  if (!result.ok) { container.innerHTML = `<div class="empty-state p-4 text-center text-red-400 text-sm">加载失败</div>`; return; }
  const c = result.data;
  container.innerHTML = `
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
      <div class="bg-white border rounded-lg p-3 text-center">
        <div class="text-xs text-gray-400">总成本</div>
        <div class="text-lg font-bold text-red-500">¥${c.total_cost.toFixed(2)}</div>
      </div>
      <div class="bg-white border rounded-lg p-3 text-center">
        <div class="text-xs text-gray-400">总售价</div>
        <div class="text-lg font-bold text-green-600">¥${c.total_price.toFixed(2)}</div>
      </div>
      <div class="bg-white border rounded-lg p-3 text-center">
        <div class="text-xs text-gray-400">利润</div>
        <div class="text-lg font-bold ${c.profit >= 0 ? 'text-green-600' : 'text-red-500'}">¥${c.profit.toFixed(2)}</div>
      </div>
      <div class="bg-white border rounded-lg p-3 text-center">
        <div class="text-xs text-gray-400">毛利率</div>
        <div class="text-lg font-bold ${c.margin_pct >= 0 ? 'text-green-600' : 'text-red-500'}">${c.margin_pct.toFixed(1)}%</div>
      </div>
    </div>
    ${c.breakdown && c.breakdown.length ? `
    <table class="w-full text-xs">
      <thead><tr class="border-b border-gray-200 text-gray-500">
        <th class="p-2 text-left">名称</th>
        <th class="p-2 text-right">数量</th>
        <th class="p-2 text-right">单位成本</th>
        <th class="p-2 text-right">单位售价</th>
        <th class="p-2 text-right">成本小计</th>
        <th class="p-2 text-right">售价小计</th>
      </tr></thead>
      <tbody>
        ${c.breakdown.map(b => `<tr class="border-b border-gray-100">
          <td class="p-2">${escHtml(b.title)}</td>
          <td class="p-2 text-right">×${b.quantity}</td>
          <td class="p-2 text-right">¥${b.unit_cost.toFixed(2)}</td>
          <td class="p-2 text-right">¥${b.unit_price.toFixed(2)}</td>
          <td class="p-2 text-right">¥${b.subtotal_cost.toFixed(2)}</td>
          <td class="p-2 text-right">¥${b.subtotal_price.toFixed(2)}</td>
        </tr>`).join('')}
      </tbody>
    </table>` : '<div class="text-xs text-gray-400 text-center py-2">暂无成本明细</div>'}`;
}

// ── New project dialog ──
function showNewProjectDialog() {
  showModal('新建项目', `
    <div class="flex flex-col gap-3">
      <div>
        <label class="text-xs text-gray-500">项目名称 *</label>
        <input class="input-field w-full" id="np-name" placeholder="如：XX客户货架项目">
      </div>
      <div>
        <label class="text-xs text-gray-500">客户</label>
        <input class="input-field w-full" id="np-customer" placeholder="客户公司名称">
      </div>
      <div>
        <label class="text-xs text-gray-500">截止日期</label>
        <input class="input-field w-full" id="np-deadline" type="date">
      </div>
      <div>
        <label class="text-xs text-gray-500">描述</label>
        <textarea class="input-field w-full" id="np-desc" rows="3" placeholder="项目描述"></textarea>
      </div>
    </div>`, [
    { text: '取消', cls: 'btn btn-sm btn-secondary', action: closeModal },
    { text: '创建', cls: 'btn btn-sm btn-success', action: async () => {
      const name = document.getElementById('np-name').value.trim();
      if (!name) { setStatus('error', '请输入项目名称'); return; }
      const result = await projectApi('POST', '/', {
        name,
        description: document.getElementById('np-desc').value,
        deadline: document.getElementById('np-deadline').value || null,
      });
      if (result.ok) {
        closeModal();
        setStatus('success', `项目 ${result.data.project_code} 创建成功`);
        renderProjectList();
      } else {
        setStatus('error', result.data?.detail || '创建失败');
      }
    }},
  ]);
}

// ── Edit project field ──
function editProjectField(field) {
  const p = window._projectData;
  if (!p) return;

  if (field === 'name') {
    showModal('编辑项目', `
      <div class="flex flex-col gap-3">
        <div>
          <label class="text-xs text-gray-500">项目名称 *</label>
          <input class="input-field w-full" id="ep-name" value="${escHtml(p.name)}">
        </div>
        <div>
          <label class="text-xs text-gray-500">描述</label>
          <textarea class="input-field w-full" id="ep-desc" rows="3">${escHtml(p.description || '')}</textarea>
        </div>
        <div>
          <label class="text-xs text-gray-500">截止日期</label>
          <input class="input-field w-full" id="ep-deadline" type="date" value="${p.deadline || ''}">
        </div>
      </div>`, [
      { text: '取消', cls: 'btn btn-sm btn-secondary', action: closeModal },
      { text: '保存', cls: 'btn btn-sm btn-primary', action: async () => {
        const name = document.getElementById('ep-name').value.trim();
        if (!name) { setStatus('error', '项目名称不能为空'); return; }
        const result = await projectApi('PATCH', `/${p.id}/`, {
          name,
          description: document.getElementById('ep-desc').value,
          deadline: document.getElementById('ep-deadline').value || null,
        });
        if (result.ok) {
          closeModal();
          setStatus('success', '项目已更新');
          showProjectDetail(p.id);
        } else {
          setStatus('error', result.data?.detail || '更新失败');
        }
      }},
    ]);
  }
}

// ── Delete project ──
function confirmDeleteProject(id) {
  if (confirm('确定删除此项目？')) {
    deleteProject(id);
  }
}
async function deleteProject(id) {
  const result = await projectApi('DELETE', `/${id}/`);
  if (result.ok) {
    setStatus('success', '项目已删除');
    switchPage('projects');
  } else {
    setStatus('error', '删除失败');
  }
}

// ── Add item to project dialog ──
function showAddItemDialog(projectId) {
  showModal('添加条目', `
    <div class="flex flex-col gap-3">
      <div>
        <label class="text-xs text-gray-500">类型</label>
        <select class="input-field w-full" id="ai-type" onchange="document.getElementById('ai-part-group').style.display=this.value==='part'?'':'none'">
          <option value="configuration">参数化配置</option>
          <option value="part">静态零件</option>
        </select>
      </div>
      <div>
        <label class="text-xs text-gray-500">标题</label>
        <input class="input-field w-full" id="ai-title" placeholder="条目名称">
      </div>
      <div>
        <label class="text-xs text-gray-500">数量</label>
        <input class="input-field w-full" id="ai-qty" type="number" value="1" min="1">
      </div>
      <div id="ai-part-group" style="display:none">
        <label class="text-xs text-gray-500">搜索零件</label>
        <input class="input-field w-full" id="ai-part-search" placeholder="输入零件名称/IPN搜索..." oninput="searchPartsForItem()">
        <div id="ai-part-results" class="mt-1 max-h-[200px] overflow-y-auto"></div>
        <input type="hidden" id="ai-part-id" value="">
        <div id="ai-part-selected" class="text-xs text-green-600 mt-1" style="display:none"></div>
      </div>
      <div>
        <label class="text-xs text-gray-500">单价</label>
        <input class="input-field w-full" id="ai-price" type="number" step="0.01" placeholder="0.00">
      </div>
    </div>`, [
    { text: '取消', cls: 'btn btn-sm btn-secondary', action: closeModal },
    { text: '添加', cls: 'btn btn-sm btn-success', action: async () => {
      const data = {
        item_type: document.getElementById('ai-type').value,
        title: document.getElementById('ai-title').value,
        quantity: parseInt(document.getElementById('ai-qty').value) || 1,
        unit_price: parseFloat(document.getElementById('ai-price').value) || null,
      };
      if (data.item_type === 'part') {
        const partId = document.getElementById('ai-part-id').value;
        if (!partId) { setStatus('error', '请先搜索并选择一个零件'); return; }
        data.part = parseInt(partId);
      }
      const result = await projectApi('POST', `/${projectId}/add_item/`, data);
      if (result.ok) {
        closeModal();
        setStatus('success', '条目已添加');
        showProjectDetail(projectId);
      } else {
        setStatus('error', '添加失败');
      }
    }},
  ]);
}

// ── Remove item ──
async function removeProjectItem(projectId, itemId) {
  if (!confirm('确定移除该条目？')) return;
  const result = await projectApi('DELETE', `/${projectId}/items/${itemId}/`);
  if (result.ok) {
    setStatus('success', '条目已移除');
    showProjectDetail(projectId);
  } else {
    setStatus('error', '移除失败');
  }
}

// ── Generate purchase orders ──
async function generatePurchaseOrders(projectId) {
  if (!confirm('将从项目BOM零件生成采购订单（按供应商分组），确定吗？')) return;
  const result = await projectApi('POST', `/${projectId}/create_purchase_orders/`);
  if (result.ok) {
    const orders = result.data.orders || [];
    const msg = orders.filter(o => o.order_id).map(o => `${o.reference}(${o.supplier})`).join(', ');
    setStatus('success', `已生成 ${orders.filter(o => o.order_id).length} 个采购订单：${msg}`);
    if (orders.some(o => !o.supplier)) {
      setStatus('info', '部分零件未关联供应商，请在InvenTree中补充供应商信息');
    }
  } else {
    setStatus('error', result.data?.error || '生成采购订单失败');
  }
}

// ── Generate sales order ──
async function generateSalesOrder(projectId) {
  if (!confirm('将为项目生成销售订单，确定吗？')) return;
  const result = await projectApi('POST', `/${projectId}/create_sales_order/`);
  if (result.ok) {
    setStatus('success', `销售订单 ${result.data.reference} 已创建（${result.data.line_items} 条明细）`);
  } else {
    setStatus('error', result.data?.error || '生成销售订单失败');
  }
}

// ── Cart → Project ──
async function submitCartAsProject() {
  const r = await fetch('/api/parametric-bom/cart/', { credentials: 'same-origin' });
  if (!r.ok) { setStatus('error', '获取购物车失败'); return; }
  const cartItems = await r.json();
  const ids = Array.isArray(cartItems) ? cartItems.map(i => i.id) : (cartItems.results || []).map(i => i.id);
  if (!ids.length) {
    setStatus('error', '购物车为空，请先添加产品');
    return;
  }

  showModal('提交项目', `
    <div class="flex flex-col gap-3">
      <p class="text-xs text-gray-500">将 ${ids.length} 个购物车条目打包为项目</p>
      <div>
        <label class="text-xs text-gray-500">项目名称 *</label>
        <input class="input-field w-full" id="cp-name" placeholder="如：XX客户货架项目">
      </div>
      <div>
        <label class="text-xs text-gray-500">客户</label>
        <input class="input-field w-full" id="cp-customer" placeholder="客户公司名称">
      </div>
      <div>
        <label class="text-xs text-gray-500">截止日期</label>
        <input class="input-field w-full" id="cp-deadline" type="date">
      </div>
      <div>
        <label class="text-xs text-gray-500">描述</label>
        <textarea class="input-field w-full" id="cp-desc" rows="2" placeholder="项目描述"></textarea>
      </div>
    </div>`, [
    { text: '取消', cls: 'btn btn-sm btn-secondary', action: closeModal },
    { text: '提交项目', cls: 'btn btn-sm btn-success', action: async () => {
      const name = document.getElementById('cp-name').value.trim();
      if (!name) { setStatus('error', '请输入项目名称'); return; }
      const result = await projectApi('POST', '/from_cart/', {
        name,
        description: document.getElementById('cp-desc').value,
        deadline: document.getElementById('cp-deadline').value || null,
        cart_item_ids: ids,
      });
      if (result.ok) {
        closeModal();
        setStatus('success', `项目 ${result.data.project_code} 创建成功`);
        // Reload cart (should be empty now)
        const cartEvt = new CustomEvent('cart-changed');
        document.dispatchEvent(cartEvt);
        renderProjectList();
        switchPage('projects');
      } else {
        setStatus('error', result.data?.error || '创建项目失败');
      }
    }},
  ]);
}

// ── Helper ──
function escHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ── Modal utils ──
let _modalContainer = null;
function showModal(title, bodyHtml, buttons) {
  // Close any existing modal overlay directly
  const existing = document.getElementById('hermes-modal-overlay');
  if (existing) existing.remove();
  const overlay = document.createElement('div');
  overlay.id = 'hermes-modal-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:9999;display:flex;align-items:center;justify-content:center';
  const modal = document.createElement('div');
  modal.style.cssText = 'background:#fff;border-radius:12px;padding:1.25rem;max-width:480px;width:90%;max-height:80vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,0.15)';
  modal.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <span class="font-semibold text-sm">${escHtml(title)}</span>
      <button onclick="document.getElementById('hermes-modal-overlay')?.remove()" style="border:none;background:none;font-size:1.2rem;cursor:pointer;color:#999">✕</button>
    </div>
    <div>${bodyHtml}</div>
    ${buttons && buttons.length ? `<div class="flex justify-end gap-2 mt-4">${buttons.map(b => `<button class="${b.cls || 'btn btn-sm'}" id="modal-btn-${b.text}">${b.text}</button>`).join('')}</div>` : ''}`;
  overlay.appendChild(modal);
  document.body.appendChild(overlay);
  _modalContainer = { overlay, modal };
  if (buttons) {
    buttons.forEach(b => {
      const btn = document.getElementById('modal-btn-' + b.text);
      if (btn) btn.onclick = b.action;
    });
  }
}
function closeModal(id) {
  if (id) {
    // formula-pages.js style: close by element id
    const el = document.getElementById(id);
    if (el) { el.classList.remove('show'); document.body.style.overflow = ''; }
    return;
  }
  // projects.js style: close overlay by id
  const overlay = document.getElementById('hermes-modal-overlay');
  if (overlay) overlay.remove();
}

function toggleAddMember() {
  const section = document.getElementById('member-add-section');
  if (section) {
    section.style.display = section.style.display === 'none' ? '' : 'none';
  }
}

// ── Expose to window ──
window.showNewProjectDialog = showNewProjectDialog;
window.showProjectDetail = showProjectDetail;
window.switchProjectTab = switchProjectTab;
window.confirmDeleteProject = confirmDeleteProject;
window.deleteProject = deleteProject;
window.showAddItemDialog = showAddItemDialog;
window.removeProjectItem = removeProjectItem;
window.searchUsersForMembership = searchUsersForMembership;
window.addMembership = addMembership;
window.removeMembership = removeMembership;
window.changeMemberRole = changeMemberRole;
window.toggleRolePermission = toggleRolePermission;
window.deleteRole = deleteRole;
window.showCreateRoleDialog = showCreateRoleDialog;
window.toggleAddMember = toggleAddMember;
window.showPermissionEditor = showPermissionEditor;
window.generatePurchaseOrders = generatePurchaseOrders;
window.generateSalesOrder = generateSalesOrder;
window.submitCartAsProject = submitCartAsProject;
window.showModal = showModal;
window.closeModal = closeModal;
window.downloadProjectCsv = downloadProjectCsv;
window.saveAsTemplate = saveAsTemplate;
window.createFromTemplate = createFromTemplate;
window.loadProjectLogs = loadProjectLogs;
window.loadMoreProjects = loadMoreProjects;

// ── Download CSV ──
async function downloadProjectCsv(id) {
  const a = document.createElement('a');
  a.href = '/api/parametric-bom/projects/' + id + '/export/';
  a.download = 'project.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setStatus('success', '正在下载项目报告...');
}

// ── Template functions ──
async function saveAsTemplate(id) {
  const name = prompt('保存为模板名称：', '');
  if (!name) return;
  const r = await projectApi('POST', `/${id}/save_as_template/`, { template_name: name });
  if (r.ok) {
    setStatus('success', `模板 "${r.data.template_name}" 已保存`);
    showProjectDetail(id);
  } else {
    setStatus('error', '保存模板失败');
  }
}

async function createFromTemplate(id) {
  const name = prompt('新项目名称：', '');
  if (!name) return;
  const r = await projectApi('POST', `/${id}/create_from_template/`, { name });
  if (r.ok) {
    setStatus('success', `项目 ${r.data.project_code} 已从模板创建`);
    renderProjectList();
    switchPage('projects');
  } else {
    setStatus('error', r.data?.error || '创建失败');
  }
}

// ── Search parts for add item dialog ──
let _partSearchTimer = null;
async function searchPartsForItem() {
  clearTimeout(_partSearchTimer);
  const input = document.getElementById('ai-part-search');
  if (!input) return;
  const q = input.value.trim();
  const results = document.getElementById('ai-part-results');
  if (!results) return;
  if (q.length < 2) { results.innerHTML = ''; return; }

  _partSearchTimer = setTimeout(async () => {
    try {
      const resp = await fetch('/api/part/?search=' + encodeURIComponent(q) + '&limit=15', { credentials: 'same-origin' });
      const data = await resp.json();
      const parts = data.results || data || [];
      if (!parts.length) { results.innerHTML = '<div class="text-xs text-gray-400 py-1">未找到零件</div>'; return; }
      results.innerHTML = parts.map(p =>
        '<div class="flex items-center justify-between py-1 px-2 text-xs border border-gray-200 rounded hover:bg-gray-50 cursor-pointer" onclick="selectPartForItem(' + p.pk + ', \'' + escHtml(p.name).replace(/'/g, "\\'") + '\')">' +
        '<span class="font-medium">' + escHtml(p.name) + '</span>' +
        '<span class="text-gray-400">' + escHtml(p.IPN || '') + '</span>' +
        '</div>'
      ).join('');
    } catch(e) { results.innerHTML = '<div class="text-xs text-red-400 py-1">搜索失败</div>'; }
  }, 300);
}

function selectPartForItem(partId, partName) {
  document.getElementById('ai-part-id').value = partId;
  document.getElementById('ai-part-search').value = partName;
  document.getElementById('ai-part-results').innerHTML = '';
  const selected = document.getElementById('ai-part-selected');
  if (selected) {
    selected.style.display = '';
    selected.textContent = '✅ 已选择: ' + partName;
  }
}

// ── Load project orders ──
async function loadProjectOrders(projectId) {
  const container = document.getElementById('project-orders-content');
  if (!container) return;
  const r = await projectApi('GET', `/${projectId}/orders/`);
  if (!r.ok) { container.innerHTML = '<div class="empty-state p-4 text-center text-red-400 text-sm">加载订单失败</div>'; return; }
  const data = r.data;
  let html = '';
  const pos = data.purchase_orders || [];
  const sos = data.sales_orders || [];

  if (!pos.length && !sos.length) {
    container.innerHTML = '<div class="empty-state p-4 text-center text-gray-400 text-sm">暂无关联订单，在"产品/零件"Tab中生成</div>';
    return;
  }

  if (sos.length) {
    html += '<div class="text-xs text-gray-500 font-medium mb-2">💰 销售订单</div>';
    html += '<table class="w-full text-xs mb-4"><thead><tr class="border-b border-gray-200 text-gray-500">';
    html += '<th class="p-2 text-left">单号</th><th class="p-2 text-left">客户</th><th class="p-2 text-right">明细</th><th class="p-2 text-left">创建时间</th></tr></thead><tbody>';
    sos.forEach(so => {
      html += `<tr class="border-b border-gray-100"><td class="p-2 font-medium">${escHtml(so.reference)}</td>`;
      html += `<td class="p-2">${escHtml(so.customer)}</td>`;
      html += `<td class="p-2 text-right">${so.line_items}</td>`;
      html += `<td class="p-2 text-gray-400">${so.created ? new Date(so.created).toLocaleDateString('zh-CN') : '-'}</td></tr>`;
    });
    html += '</tbody></table>';
  }

  if (pos.length) {
    html += '<div class="text-xs text-gray-500 font-medium mb-2">📥 采购订单</div>';
    html += '<table class="w-full text-xs"><thead><tr class="border-b border-gray-200 text-gray-500">';
    html += '<th class="p-2 text-left">单号</th><th class="p-2 text-left">供应商</th><th class="p-2 text-right">明细</th><th class="p-2 text-left">创建时间</th></tr></thead><tbody>';
    pos.forEach(po => {
      html += `<tr class="border-b border-gray-100"><td class="p-2 font-medium">${escHtml(po.reference)}</td>`;
      html += `<td class="p-2">${escHtml(po.supplier)}</td>`;
      html += `<td class="p-2 text-right">${po.line_items}</td>`;
      html += `<td class="p-2 text-gray-400">${po.created ? new Date(po.created).toLocaleDateString('zh-CN') : '-'}</td></tr>`;
    });
    html += '</tbody></table>';
  }

  container.innerHTML = html;
}

// ── Load change logs ──
async function loadProjectLogs(projectId) {
  const container = document.getElementById('project-logs-content');
  if (!container) return;
  const r = await projectApi('GET', `/${projectId}/logs/`);
  if (!r.ok) { container.innerHTML = '<div class="empty-state p-4 text-center text-red-400 text-sm">加载日志失败</div>'; return; }
  const logs = r.data;
  if (!logs || !logs.length) {
    container.innerHTML = '<div class="empty-state p-4 text-center text-gray-400 text-sm">暂无变更记录</div>';
    return;
  }
  container.innerHTML = `
    <div class="text-xs text-gray-500 mb-2 font-medium">变更历史（最近50条）</div>
    <div class="space-y-1 max-h-[400px] overflow-y-auto">
      ${logs.map(l => `
      <div class="flex items-start gap-2 p-1.5 border-b border-gray-100 last:border-0">
        <span class="text-gray-400 shrink-0 mt-0.5">${getLogIcon(l.action)}</span>
        <div class="flex-1 min-w-0">
          <span class="text-gray-700">${escHtml(l.description || l.action)}</span>
          <span class="text-gray-400 ml-1 text-[10px]">— ${escHtml(l.user)}</span>
        </div>
        <span class="text-gray-400 text-[10px] shrink-0">${formatTime(l.created_at)}</span>
      </div>`).join('')}
    </div>`;
}

function getLogIcon(action) {
  const icons = {
    created: '✅', updated: '✏️', from_cart: '📦',
    item_added: '➕', item_removed: '➖',
    purchase_orders_created: '📥', sales_order_created: '💰',
    saved_as_template: '📌',
    attachment_uploaded: '📎', attachment_removed: '🗑️',
  };
  return icons[action] || '📝';
}

function formatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = n => String(n).padStart(2, '0');
  return `${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ── Load attachments ──
async function loadProjectAttachments(projectId) {
  const container = document.getElementById('project-attachments-content');
  if (!container) return;
  const r = await projectApi('GET', `/${projectId}/attachments/`);
  if (!r.ok) { container.innerHTML = '<div class="empty-state p-4 text-center text-red-400 text-sm">加载附件失败</div>'; return; }
  const atts = r.data;
  const canEdit = window._projectData?.user_role === 'owner' || window._projectData?.user_permissions?.includes('manage_attachments');

  // Upload form
  let html = '';

  // Separate file attachments and links
  const files = atts.filter(a => a.attachment);
  const links = atts.filter(a => !a.attachment && a.link);

  html += `<div class="text-xs text-gray-500 mb-2 font-medium">共 ${atts.length} 个附件</div>`;

  if (canEdit) {
    html += `
    <div class="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-3 mb-3">
      <div class="text-xs text-gray-500 mb-2">📤 上传文件或添加链接</div>
      <div class="flex flex-wrap gap-2 items-end">
        <div class="flex-1 min-w-[180px]">
          <label class="text-[10px] text-gray-400 block mb-0.5">选择文件</label>
          <input type="file" id="att-upload-input" class="input-field w-full text-xs py-1">
        </div>
        <div class="flex-1 min-w-[150px]">
          <label class="text-[10px] text-gray-400 block mb-0.5">或外部链接</label>
          <input type="text" id="att-link-input" class="input-field w-full text-xs py-1" placeholder="https://...">
        </div>
        <div class="flex-1 min-w-[120px]">
          <label class="text-[10px] text-gray-400 block mb-0.5">备注</label>
          <input type="text" id="att-comment-input" class="input-field w-full text-xs py-1" placeholder="附件说明">
        </div>
        <button class="btn btn-sm btn-secondary mt-1" onclick="uploadProjectAttachment(${projectId})">上传</button>
      </div>
    </div>`;
  }

  // File attachments
  if (files.length) {
    html += '<div class="text-xs text-gray-400 font-medium mb-1">📄 文件</div>';
    html += files.map(a => `
      <div class="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0 text-xs">
        <div class="flex items-center gap-2 min-w-0 flex-1">
          ${a.is_image ? '🖼️' : '📄'}
          <a href="${a.attachment}" target="_blank" class="truncate text-blue-600 hover:underline">${a.filename || '附件'}</a>
          ${a.comment ? `<span class="text-gray-400 truncate max-w-[200px]">— ${escHtml(a.comment)}</span>` : ''}
        </div>
        <div class="flex items-center gap-2 shrink-0">
          ${a.file_size ? `<span class="text-gray-400 text-[10px]">${formatFileSize(a.file_size)}</span>` : ''}
          <span class="text-gray-400 text-[10px]">${a.upload_date || ''}</span>
          ${canEdit ? `<button class="text-red-400 hover:text-red-600 text-xs" onclick="deleteProjectAttachment(${projectId}, ${a.pk})">✕</button>` : ''}
        </div>
      </div>
    `).join('');
  }

  // Links
  if (links.length) {
    html += '<div class="text-xs text-gray-400 font-medium mb-1 mt-2">🔗 链接</div>';
    html += links.map(a => `
      <div class="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0 text-xs">
        <div class="flex items-center gap-2 min-w-0 flex-1">
          🔗
          <a href="${a.link}" target="_blank" class="truncate text-blue-600 hover:underline">${a.comment || a.link}</a>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          ${a.upload_date ? `<span class="text-gray-400 text-[10px]">${a.upload_date}</span>` : ''}
          ${canEdit ? `<button class="text-red-400 hover:text-red-600 text-xs" onclick="deleteProjectAttachment(${projectId}, ${a.pk})">✕</button>` : ''}
        </div>
      </div>
    `).join('');
  }

  if (!atts.length) {
    html += '<div class="empty-state p-4 text-center text-gray-400 text-sm">暂无附件，点击上方按钮上传</div>';
  }

  container.innerHTML = html;
}

// ---- Load project members (RBAC) ----
async function loadProjectMembers(projectId) {
  const container = document.getElementById('project-members-content');
  if (!container) return;

  const p = window._projectData;
  const myRole = p?.user_role || 'none';
  const myPerms = p?.user_permissions || [];
  const canManage = myRole === 'owner' || myRole === 'admin' || myPerms.includes('manage_members');

  const [rolesRes, membersRes] = await Promise.all([
    projectApi('GET', '/' + projectId + '/roles/'),
    projectApi('GET', '/' + projectId + '/members_list/'),
  ]);

  if (!rolesRes.ok) { container.innerHTML = '<div class="empty-state p-4 text-center text-red-400 text-sm">加载角色失败</div>'; return; }
  if (!membersRes.ok) { container.innerHTML = '<div class="empty-state p-4 text-center text-red-400 text-sm">加载成员失败</div>'; return; }

  const roles = rolesRes.data;
  const memberships = membersRes.data;
  const ownerName = p?.owner_name || 'Owner';

  // Build a lookup: roleId -> role
  const roleMap = {};
  roles.forEach(r => roleMap[r.id] = r);

  // Collect all people: owner + memberships
  const allPeople = [{ id: 'owner', name: ownerName, roleId: null, roleName: 'Owner', isOwner: true }];
  memberships.forEach(m => {
    const r = roleMap[m.role] || { name: m.role_name || '?', permissions: [] };
    allPeople.push({ id: m.id, userId: m.user, name: m.user_name, email: m.user_email, roleId: m.role, roleName: r.name, perms: r.permissions || [], isOwner: false });
  });

  let html = '';

  // ── Stats header ──
  const memberCount = memberships.length;
  html += '<div class="flex items-center justify-between mb-3">';
  html += '<span class="text-sm font-medium text-gray-700">👥 项目成员 <span class="text-xs text-gray-400 font-normal">(' + (memberCount + 1) + ' 人)</span></span>';
  if (canManage) {
    html += '<button class="btn btn-sm btn-secondary text-xs py-1 px-2" onclick="toggleAddMember()">添加成员</button>';
  }
  html += '</div>';

  // ── Compact member list ──
  html += '<div class="flex flex-col gap-px bg-gray-100 rounded-lg overflow-hidden">';

  allPeople.forEach(person => {
    const initial = person.name.charAt(0).toUpperCase();
    const bgColor = person.isOwner ? 'bg-amber-50' : 'bg-white';
    html += '<div class="flex items-center justify-between px-3 py-2.5 ' + bgColor + ' hover:bg-gray-50 transition-colors">';
    
    // Left: avatar + name
    html += '<div class="flex items-center gap-2.5 min-w-0 flex-1">';
    const avatarBg = person.isOwner ? 'bg-amber-200 text-amber-800' : 'bg-blue-100 text-blue-700';
    html += '<span class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ' + avatarBg + '">' + initial + '</span>';
    html += '<div class="min-w-0">';
    html += '<div class="text-xs font-medium text-gray-800 truncate">' + escHtml(person.name) + '</div>';
    if (!person.isOwner && person.email) {
      html += '<div class="text-[10px] text-gray-400 truncate">' + escHtml(person.email) + '</div>';
    }
    html += '</div></div>';

    // Right: role badge + actions
    html += '<div class="flex items-center gap-1.5 shrink-0">';
    if (person.isOwner) {
      html += '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-700 border border-amber-200">👑 所有者</span>';
    } else {
      html += '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-50 text-blue-600 border border-blue-100">' + escHtml(person.roleName) + '</span>';
      if (canManage) {
        // Tiny role switcher
        html += '<select class="text-[10px] border border-gray-200 rounded px-1 py-0.5 bg-white cursor-pointer hover:border-blue-300 focus:border-blue-400 focus:ring-1 focus:ring-blue-200 outline-none" onchange="changeMemberRole(' + projectId + ', ' + person.id + ', this.value)">';
        roles.forEach(r => {
          html += '<option value="' + r.id + '"' + (r.id === person.roleId ? ' selected' : '') + '>' + escHtml(r.name) + '</option>';
        });
        html += '</select>';
        html += '<button class="text-red-300 hover:text-red-500 transition-colors text-xs p-0.5" onclick="removeMembership(' + projectId + ', ' + person.id + ')" title="移除">✕</button>';
      }
    }
    html += '</div></div>';
  });

  html += '</div>';

  // ── Add member (collapsed by default) ──
  if (canManage) {
    html += '<div id="member-add-section" class="mt-3 bg-blue-50 border border-blue-100 rounded-lg p-3" style="display:none">';
    html += '<div class="flex items-center justify-between mb-2">';
    html += '<span class="text-xs font-medium text-blue-700">➕ 添加成员</span>';
    html += '<button class="text-gray-400 hover:text-gray-600 text-xs" onclick="toggleAddMember()">✕</button>';
    html += '</div>';
    html += '<div class="flex gap-2">';
    html += '<div class="flex-1 relative">';
    html += '<input type="text" id="member-search-input" class="w-full text-xs border border-blue-200 rounded-lg px-2.5 py-1.5 outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-200 bg-white placeholder-gray-400" placeholder="搜索用户名..." onfocus="searchUsersForMembership(' + projectId + ')" oninput="searchUsersForMembership(' + projectId + ')" autocomplete="off">';
    html += '<div id="member-search-results" class="absolute left-0 right-0 top-full mt-1 z-10 bg-white border border-gray-200 rounded-lg shadow-lg max-h-[240px] overflow-y-auto"></div>';
    html += '</div>';
    html += '<select id="member-role-select" class="text-xs border border-blue-200 rounded-lg px-2 py-1.5 outline-none focus:border-blue-400 bg-white w-[90px]">';
    roles.forEach(r => {
      html += '<option value="' + r.id + '">' + escHtml(r.name) + '</option>';
    });
    html += '</select>';
    html += '</div>';
    html += '</div>';

    // ── Permission editor ──
    if (myRole === 'owner' || myRole === 'admin') {
      html += '<div class="mt-3 pt-2 border-t border-gray-100">';
      html += '<button class="text-xs text-gray-500 hover:text-blue-600 transition-colors flex items-center gap-1.5 py-1" onclick="showPermissionEditor(' + projectId + ')">';
      html += '⚙️ 权限设置 <span class="text-[10px] text-gray-400 font-normal">' + roles.length + ' 个角色</span>';
      html += '</button>';
      html += '</div>';
    }
  }

  container.innerHTML = html;
}

// ---- Permission editor (modal with save) ----
async function showPermissionEditor(projectId) {
  const [rolesRes, defRes] = await Promise.all([
    projectApi('GET', '/' + projectId + '/roles/'),
    projectApi('GET', '/permissions_def/'),
  ]);
  if (!rolesRes.ok || !defRes.ok) { setStatus('error', '加载权限数据失败'); return; }

  const roles = rolesRes.data;
  const allPerms = defRes.data;

  // Store initial state for change tracking
  window._permEditorState = roles.map(r => ({ id: r.id, name: r.name, perms: [...(r.permissions || [])] }));

  let bodyHtml = '<div class="space-y-2" id="perm-editor-body">';
  roles.forEach((role, idx) => {
    const permCount = (role.permissions || []).length;
    bodyHtml += '<div class="border border-gray-200 rounded-lg overflow-hidden">';
    bodyHtml += '<div class="flex items-center justify-between px-3 py-2 bg-gray-50 border-b border-gray-200">';
    bodyHtml += '<div class="flex items-center gap-2">';
    bodyHtml += '<span class="text-xs font-medium text-gray-700">' + escHtml(role.name) + '</span>';
    bodyHtml += '<span class="text-[10px] text-gray-400">' + permCount + '/' + allPerms.length + '</span>';
    bodyHtml += '</div>';
    if (!role.is_preset) {
      bodyHtml += '<button class="text-red-300 hover:text-red-500 text-[10px]" onclick="closeModal(); deleteRole(' + projectId + ', ' + role.id + ')">删除</button>';
    }
    bodyHtml += '</div>';
    bodyHtml += '<div class="grid grid-cols-2 sm:grid-cols-3 gap-1 p-2.5">';
    allPerms.forEach(p => {
      const checked = (role.permissions || []).includes(p.code);
      bodyHtml += '<label class="flex items-center gap-1.5 text-xs cursor-pointer px-2 py-1 rounded transition-colors ' + (checked ? 'bg-blue-50 text-blue-700' : 'text-gray-500 hover:bg-gray-50') + '">';
      bodyHtml += '<input type="checkbox" class="accent-blue-500 w-3 h-3 perm-checkbox" data-role-idx="' + idx + '" data-code="' + p.code + '" ' + (checked ? 'checked' : '') + '>';
      bodyHtml += escHtml(p.label);
      bodyHtml += '</label>';
    });
    bodyHtml += '</div></div>';
  });
  bodyHtml += '<button class="btn btn-sm btn-secondary text-xs w-full mt-2 py-1.5" onclick="closeModal(); showCreateRoleDialog(' + projectId + ')">新建角色</button>';
  bodyHtml += '</div>';

  showModal('⚙️ 权限设置', bodyHtml, [
    { text: '取消', cls: 'btn btn-sm btn-secondary', action: closeModal },
    { text: '保存', cls: 'btn btn-sm btn-primary', action: async () => {
      // Collect changes from checkboxes
      const checkboxes = document.querySelectorAll('.perm-checkbox');
      const newState = JSON.parse(JSON.stringify(window._permEditorState));
      checkboxes.forEach(cb => {
        const idx = parseInt(cb.dataset.roleIdx);
        const code = cb.dataset.code;
        if (cb.checked && !newState[idx].perms.includes(code)) {
          newState[idx].perms.push(code);
        } else if (!cb.checked && newState[idx].perms.includes(code)) {
          newState[idx].perms = newState[idx].perms.filter(p => p !== code);
        }
      });

      // Save all changed roles
      let saved = 0;
      for (const s of newState) {
        const old = window._permEditorState.find(o => o.id === s.id);
        if (JSON.stringify(old.perms.sort()) !== JSON.stringify(s.perms.sort())) {
          const r = await projectApi('PATCH', '/' + projectId + '/roles/' + s.id + '/', { permissions: s.perms });
          if (r.ok) saved++;
        }
      }
      closeModal();
      setStatus('success', '已保存 ' + saved + ' 个角色的权限');
      // Reload to refresh counts
      loadProjectMembers(projectId);
    }},
  ]);
}

// ---- Toggle role permission ----
async function toggleRolePermission(projectId, roleId, permCode, enabled) {
  // First get current role permissions
  const roleRes = await projectApi('GET', '/' + projectId + '/roles/');
  if (!roleRes.ok) return;
  const roles = roleRes.data;
  const role = roles.find(r => r.id === roleId);
  if (!role) return;

  let perms = [...(role.permissions || [])];
  if (enabled) {
    if (!perms.includes(permCode)) perms.push(permCode);
  } else {
    perms = perms.filter(p => p !== permCode);
  }

  await projectApi('PATCH', '/' + projectId + '/roles/' + roleId + '/', { permissions: perms });
  setStatus('success', '权限已更新');
}

// ---- Change member role ----
async function changeMemberRole(projectId, memberId, roleId) {
  const r = await projectApi('POST', '/' + projectId + '/memberships/' + memberId + '/change_role/', { role_id: parseInt(roleId) });
  if (r.ok) {
    setStatus('success', '角色已更改');
    loadProjectMembers(projectId);
  } else {
    setStatus('error', r.data?.error || '更改失败');
  }
}

// ---- Remove membership ----
async function removeMembership(projectId, memberId) {
  if (!confirm('确定移除此成员？')) return;
  const r = await projectApi('DELETE', '/' + projectId + '/memberships/' + memberId + '/');
  if (r.ok) {
    setStatus('success', '成员已移除');
    loadProjectMembers(projectId);
  } else {
    setStatus('error', r.data?.error || '移除失败');
  }
}

// ---- Delete custom role ----
async function deleteRole(projectId, roleId) {
  if (!confirm('确定删除此角色？（已有成员的关联会解除）')) return;
  const r = await projectApi('DELETE', '/' + projectId + '/roles/' + roleId + '/');
  if (r.ok) {
    setStatus('success', '角色已删除');
    closeModal();
    loadProjectMembers(projectId);
  } else {
    setStatus('error', r.data?.error || '删除失败');
  }
}

// ---- Create role dialog ----
function showCreateRoleDialog(projectId) {
  showModal('新建角色', `
    <div class="flex flex-col gap-3">
      <div>
        <label class="text-xs text-gray-500">角色名称</label>
        <input class="input-field w-full" id="cr-name" placeholder="如: 审核员">
      </div>
    </div>`, [
    { text: '取消', cls: 'btn btn-sm btn-secondary', action: closeModal },
    { text: '创建', cls: 'btn btn-sm btn-success', action: async () => {
      const name = document.getElementById('cr-name').value.trim();
      if (!name) { setStatus('error', '请输入角色名称'); return; }
      const r = await projectApi('POST', '/' + projectId + '/create_role/', { name, permissions: ['view_project'] });
      if (r.ok) {
        closeModal();
        setStatus('success', '角色已创建，请在权限设置中配置');
        loadProjectMembers(projectId);
      } else {
        setStatus('error', r.data?.name?.[0] || '创建失败');
      }
    }},
  ]);
}

// ---- Search users for membership ----
let _memberSearchTimer = null;
async function searchUsersForMembership(projectId) {
  clearTimeout(_memberSearchTimer);
  const input = document.getElementById('member-search-input');
  if (!input) return;
  const q = input.value.trim();
  const results = document.getElementById('member-search-results');
  if (!results) return;

  _memberSearchTimer = setTimeout(async () => {
    try {
      // Get existing memberships and owner to exclude
      const [memRes, pRes] = await Promise.all([
        projectApi('GET', '/' + projectId + '/members_list/'),
        projectApi('GET', '/' + projectId + '/'),
      ]);
      const existingUserIds = new Set();
      if (memRes.ok) memRes.data.forEach(m => existingUserIds.add(m.user));
      if (pRes.ok) existingUserIds.add(pRes.data.owner);

      let url;
      if (q.length < 1) {
        url = '/api/parametric-bom/projects/search_users/?q=a&limit=50';
      } else {
        url = '/api/parametric-bom/projects/search_users/?q=' + encodeURIComponent(q) + '&limit=50';
      }
      const resp = await fetch(url, { credentials: 'same-origin' });
      const users = await resp.json();
      const filtered = users.filter(u => !existingUserIds.has(u.id));

      if (!filtered.length) {
        results.innerHTML = '<div class="text-xs text-gray-400 py-1">' + (q.length < 1 ? '所有用户都已是成员' : '未找到用户') + '</div>';
        return;
      }
      const roleSelect = document.getElementById('member-role-select');
      const defaultRoleId = roleSelect ? roleSelect.value : '';

      results.innerHTML = '<div class="flex flex-col gap-0.5 mt-1 max-h-[200px] overflow-y-auto">' +
        filtered.map(u =>
          '<div class="flex items-center justify-between py-1 px-2 text-xs border border-gray-200 rounded hover:bg-gray-50 cursor-pointer" onclick="addMembership(' + projectId + ', ' + u.id + ')">' +
          '<span class="font-medium">' + escHtml(u.name) + '</span>' +
          '<span class="text-gray-400">' + escHtml(u.username) + '</span>' +
          '<button class="text-blue-500 text-xs">➕ 添加</button>' +
          '</div>'
        ).join('') +
        '</div>';
    } catch(e) { results.innerHTML = '<div class="text-xs text-red-400 py-1">搜索失败</div>'; }
  }, q.length < 1 ? 0 : 300);
}

// ---- Add membership ----
async function addMembership(projectId, userId) {
  const roleSelect = document.getElementById('member-role-select');
  const roleId = roleSelect ? roleSelect.value : '';
  if (!roleId) { setStatus('error', '请选择角色'); return; }

  const r = await projectApi('POST', '/' + projectId + '/add_membership/', { user_id: userId, role_id: parseInt(roleId) });
  if (r.ok) {
    setStatus('success', '成员已添加');
    const input = document.getElementById('member-search-input');
    if (input) input.value = '';
    const results = document.getElementById('member-search-results');
    if (results) results.innerHTML = '';
    loadProjectMembers(projectId);
  } else {
    setStatus('error', r.data?.error || '添加失败');
  }
}

// ── Upload attachment ──
async function uploadProjectAttachment(projectId) {
  const fileInput = document.getElementById('att-upload-input');
  const linkInput = document.getElementById('att-link-input');
  const commentInput = document.getElementById('att-comment-input');
  const file = fileInput?.files?.[0];
  const link = linkInput?.value?.trim();
  const comment = commentInput?.value?.trim() || '';

  if (!file && !link) {
    setStatus('error', '请选择文件或输入链接');
    return;
  }

  const formData = new FormData();
  if (file) formData.append('attachment', file);
  if (link) formData.append('link', link);
  if (comment) formData.append('comment', comment);

  try {
    const res = await fetch(PROJECT_API + '/' + projectId + '/attachments/', {
      method: 'POST',
      headers: getHeaders(false),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      setStatus('error', err.detail || '上传失败');
      return;
    }
    setStatus('success', '附件已上传');
    // Clear inputs
    if (fileInput) fileInput.value = '';
    if (linkInput) linkInput.value = '';
    if (commentInput) commentInput.value = '';
    loadProjectAttachments(projectId);
  } catch (e) {
    setStatus('error', '上传失败: ' + e.message);
  }
}

// ── Delete attachment ──
async function deleteProjectAttachment(projectId, attId) {
  if (!confirm('确定删除此附件？')) return;
  const r = await projectApi('DELETE', `/${projectId}/attachments/${attId}/`);
  if (r.ok) {
    setStatus('success', '附件已删除');
    loadProjectAttachments(projectId);
  } else {
    setStatus('error', '删除失败');
  }
}

// ── Helpers ──
function formatFileSize(bytes) {
  if (!bytes) return '';
  if (bytes < 1024) return bytes + 'B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB';
  return (bytes / 1024 / 1024).toFixed(1) + 'MB';
}

function getHeaders(json) {
  const h = {};
  const csrf = getCookie('csrftoken');
  if (csrf) h['X-CSRFToken'] = csrf;
  if (json !== false) {
    h['Content-Type'] = 'application/json';
  }
  return h;
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}
