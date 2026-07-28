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

// ── Copy to clipboard helper ──
function copyText(text, label) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      setStatus('success', `已复制${label || '内容'}`);
    }).catch(() => {
      fallbackCopy(text, label);
    });
  } else {
    fallbackCopy(text, label);
  }
}
function fallbackCopy(text, label) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed'; ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); setStatus('success', `已复制${label || '内容'}`); } catch (e) {}
  document.body.removeChild(ta);
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
  const showArchived = window._projectShowArchived || false;

  // Build query params
  const params = new URLSearchParams();
  params.set('inactive', showArchived ? '1' : '0');
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
      <span>📋 项目管理 <span class="text-xs text-gray-400 font-normal">(${showArchived ? `已归档 ${total} 个` : `活跃 ${total} 个`})</span></span>
      <button class="btn btn-sm btn-secondary" onclick="showNewProjectDialog()">新建项目</button>
    </div>
    <div class="p-2 border-b border-gray-100 flex items-center gap-2 flex-wrap">
      <input class="input-field flex-1 min-w-[180px]" id="project-search-input"
             placeholder="🔍 搜索项目名称/编号..."
             value="${escHtml(search)}"
             oninput="debounceProjectSearch()">
      <div class="flex items-center gap-0.5 border rounded text-xs">
        <button class="px-2 py-1 ${showArchived ? 'text-gray-400' : 'bg-blue-600 text-white font-medium rounded'}" onclick="toggleProjectArchive(false)">活跃</button>
        <button class="px-2 py-1 ${showArchived ? 'bg-blue-600 text-white font-medium rounded' : 'text-gray-400'}" onclick="toggleProjectArchive(true)">已归档</button>
      </div>
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
      <p class="text-gray-500 text-sm">${search ? '未找到匹配项目' : (showArchived ? '暂无已归档项目' : '暂无项目，点击"新建项目"或从购物车提交项目')}</p>
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

function toggleProjectArchive(show) {
  window._projectShowArchived = show;
  window._projectPage = 1;
  renderProjectList();
}

function renderProjectRows(projects) {
  return projects.map(p => `
  <tr class="border-b border-gray-100 hover:bg-gray-50 cursor-pointer${p.is_active ? '' : ' opacity-60'}" onclick="showProjectDetail(${p.id})">
    <td class="p-2 font-mono text-blue-600">${p.project_code}<button class="copy-btn ml-1" onclick="event.stopPropagation(); copyText('${escHtml(p.project_code)}', '项目编号')" title="复制编号"></button></td>
    <td class="p-2 font-medium">${p.is_active ? '' : '<span class="mr-1">📦</span>'}${escHtml(p.name)}<button class="copy-btn ml-1" onclick="event.stopPropagation(); copyText('${escHtml(p.name)}', '项目名称')" title="复制名称"></button></td>
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
  const container = document.getElementById('project-detail-content');
  if (!container) { switchPage('project-detail'); await delay(50); return showProjectDetail(projectId); }
  // Set current project BEFORE switchPage so its handler doesn't redirect back to projects
  window._currentProjectId = projectId;
  // Show loading state
  switchPage('project-detail');
  container.innerHTML = '<div class="flex items-center justify-center py-12"><div class="text-gray-400 text-sm flex items-center gap-3"><span class="inline-block w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></span>加载中...</div></div>';

  const result = await projectApi('GET', `/${projectId}/`);
  if (!result.ok) {
    container.innerHTML = '<div class="card"><div class="empty-state p-4 text-center text-red-400 text-sm">❌ 加载项目失败 <button class="btn btn-sm btn-secondary ml-2" onclick="showProjectDetail(' + projectId + ')">重试</button></div></div>';
    return;
  }
  const p = result.data;
  window._currentProjectId = projectId;
  // Update URL to clean path (/parametric-bom/projects/<id>/)
  const cleanUrl = '/parametric-bom/projects/' + projectId + '/';
  const currentUrl = window.location.pathname;
  if (currentUrl === cleanUrl) {
    window.history.replaceState({page: 'project-detail', projectId}, '', cleanUrl);
  } else {
    window.history.pushState({page: 'project-detail', projectId}, '', cleanUrl);
  }

  const canEdit = (p.user_role === 'owner' || p.user_permissions?.includes('edit_project')) && p.is_active;
  const canManageMembers = p.user_role === 'owner' || p.user_permissions?.includes('manage_members');

  let html = `
  <div class="card mb-3">
    <div class="card-header flex items-center justify-between flex-wrap gap-2">
      <div class="flex items-center gap-2">
        <span>${p.is_template ? '📌' : '📋'}</span>
        <span class="text-lg font-semibold">${escHtml(p.project_code)}<button class="copy-btn ml-1" onclick="event.stopPropagation(); copyText('${escHtml(p.project_code)}', '项目编号')" title="复制编号"></button></span>
        <span class="text-base text-gray-700 ml-1">${escHtml(p.name)}<button class="copy-btn ml-1" onclick="event.stopPropagation(); copyText('${escHtml(p.name)}', '项目名称')" title="复制名称"></button></span>
        ${p.is_template ? '<span class="inline-block px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700">模板</span>' : ''}
        ${!p.is_active ? '<span class="inline-block px-2 py-0.5 rounded text-xs font-medium bg-gray-200 text-gray-600">📦 已归档</span>' : ''}
        ${projectStatusBadge(p.status)}
      </div>
      <div class="flex items-center gap-2">
        ${canEdit ? `
        <button class="btn btn-sm btn-secondary" onclick="editProjectField('name')">编辑</button>
        <button class="btn btn-sm btn-secondary" onclick="confirmArchiveProject(${p.id}, ${p.is_active})">${p.is_active ? '归档' : '恢复'}</button>
        ${p.is_active ? '' : `<button class="btn btn-sm btn-secondary text-red-600" onclick="confirmHardDelete(${p.id})">永久删除</button>`}` : ''}
        ${!p.is_template ? `<button class="btn btn-sm btn-secondary" onclick="saveAsTemplate(${p.id})">存为模板</button>` : ''}
        ${p.is_template ? `<button class="btn btn-sm btn-secondary" onclick="createFromTemplate(${p.id})">从模板创建</button>` : ''}
        <button class="btn btn-sm btn-secondary" onclick="downloadProjectCsv(${p.id})">导出</button>
        <button class="btn btn-sm btn-secondary" onclick="switchPage('projects')">返回</button>
      </div>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3 text-xs">
      <div><span class="text-gray-400">客户</span><br><span class="font-medium">${p.customer_name || '-'}${p.customer_name ? `<button class="copy-btn ml-1" onclick="event.stopPropagation(); copyText('${escHtml(p.customer_name)}', '客户名称')" title="复制客户名"></button>` : ''}</span></div>
      <div><span class="text-gray-400">负责人</span><br><span class="font-medium">${p.owner_name || '-'}${p.owner_name ? `<button class="copy-btn ml-1" onclick="event.stopPropagation(); copyText('${escHtml(p.owner_name)}', '负责人')" title="复制负责人"></button>` : ''}</span></div>
      <div><span class="text-gray-400">截止日期</span><br><span class="font-medium">${p.deadline || '-'}${p.deadline ? `<button class="copy-btn ml-1" onclick="event.stopPropagation(); copyText('${p.deadline}', '截止日期')" title="复制日期"></button>` : ''}</span></div>
      <div><span class="text-gray-400">创建时间</span><br><span class="font-medium">${new Date(p.created_at).toLocaleDateString('zh-CN')}<button class="copy-btn ml-1" onclick="event.stopPropagation(); copyText('${new Date(p.created_at).toISOString().split('T')[0]}', '创建日期')" title="复制日期"></button></span></div>
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
    ${p.items && p.items.length ? (() => {
      // Group items by batch_name
      const groups = {};
      p.items.forEach(item => {
        const key = item.batch_name || '未分组';
        if (!groups[key]) groups[key] = [];
        groups[key].push(item);
      });
      // Define display order
      // Sort: newest batch first, "未分组" always last
      const sortedKeys = Object.keys(groups).sort((a, b) => {
        if (a === '未分组') return 1;
        if (b === '未分组') return -1;
        // By batch number if it's "第N批" format
        const ma = a.match(/^第(\d+)批$/);
        const mb = b.match(/^第(\d+)批$/);
        if (ma && mb) return parseInt(mb[1]) - parseInt(ma[1]);
        if (ma) return -1;
        if (mb) return 1;
        // Fallback: by latest item created_at
        const ta = Math.max(...groups[a].map(it => new Date(it.created_at).getTime()));
        const tb = Math.max(...groups[b].map(it => new Date(it.created_at).getTime()));
        return tb - ta;
      });

      let html = '';
      // Add-item button at the top of batches
      html += `<div class="flex items-center gap-2 mb-3 flex-wrap">
        ${canEdit ? `<button class="btn btn-sm btn-secondary" onclick="showAddItemToProject(${p.id})">添加条目到项目</button>` : ''}
      </div>`;
      sortedKeys.forEach(batchName => {
        const items = groups[batchName];
        const totalQty = items.reduce((s, it) => s + it.quantity, 0);
        const totalAmt = items.reduce((s, it) => s + parseFloat(it.unit_price || 0) * it.quantity, 0);
        // Find earliest created_at and creator
        const times = items.map(it => it.created_at).filter(Boolean).sort();
        const batchTime = times.length ? new Date(times[0]).toLocaleString('zh-CN', {year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}) : '';
        const creator = items.find(it => it.created_by_name)?.created_by_name || '';
        const status = (batchName === '未分组') ? 'editing' : ((p.batch_statuses && p.batch_statuses[batchName]) || 'editing');
        const meta = (p.batch_meta && p.batch_meta[batchName]) || {};
        const storageDest = meta.storage_dest || '入仓库';
        const makeBuy = meta.make_buy || '采购';
        const reason = meta.reason || '按合同下单';
        const safeBatch = encodeURIComponent(batchName);
        const statusBadge = batchName === '未分组' ? '' :
          (status === 'editing' ? '<span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-600 border border-blue-100">✏️ 编辑中</span>' :
           status === 'locked' ? '<span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-600 border border-gray-200">🔒 已锁定</span>' :
           '<span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-50 text-green-600 border border-green-100">✅ 已完成</span>');
        const canEditBatch = canEdit && status === 'editing';
        const isEditable = canEdit && (batchName === '未分组' || status === 'editing');

        html += `
        <div class="card mb-3 batch-card${status === 'locked' || status === 'completed' ? ' batch-locked' : ''}">
          <div class="card-header flex items-center justify-between flex-wrap gap-2">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-semibold text-sm">📦 ${escHtml(batchName)}</span>
              ${statusBadge}
              <span class="text-xs text-gray-400">${items.length} 项 · ${totalQty} 件 · ¥${totalAmt.toFixed(2)}</span>
              ${batchTime ? `<span class="text-xs text-gray-400">🕐 ${batchTime}</span>` : ''}
              ${creator ? `<span class="text-xs text-gray-400">👤 ${escHtml(creator)}</span>` : ''}
            </div>
            <div class="flex items-center gap-1.5">${batchName === '未分组' ? '' : `
              <span class="text-[10px] bg-purple-50 text-purple-600 px-1.5 py-0.5 rounded border border-purple-100 ${isEditable ? 'cursor-pointer' : 'opacity-60'}" ${isEditable ? `onclick="editBatchMeta(${p.id}, '${safeBatch}', 'storage_dest', '${escHtml(storageDest)}', this)" title="入库去向"` : ''}>📥 ${escHtml(storageDest)}</span>
              <span class="text-[10px] bg-amber-50 text-amber-600 px-1.5 py-0.5 rounded border border-amber-100 ${isEditable ? 'cursor-pointer' : 'opacity-60'}" ${isEditable ? `onclick="editBatchMeta(${p.id}, '${safeBatch}', 'make_buy', '${escHtml(makeBuy)}', this)" title="制购类别"` : ''}>🏭 ${escHtml(makeBuy)}</span>
              <span class="text-[10px] bg-green-50 text-green-600 px-1.5 py-0.5 rounded border border-green-100 ${isEditable ? 'cursor-pointer' : 'opacity-60'}" ${isEditable ? `onclick="editBatchMeta(${p.id}, '${safeBatch}', 'reason', '${escHtml(reason)}', this)" title="申请理由"` : ''}>📝 ${escHtml(reason)}</span>
            `}
            </div>
            <div class="flex items-center gap-1.5">
              ${canEditBatch ? `<button class="btn btn-sm btn-secondary" onclick="showAddItemDialog(${p.id}, '${escHtml(batchName)}')">添加</button>` : ''}
              ${status === 'editing' && batchName !== '未分组' ? `<button class="btn btn-sm btn-secondary text-blue-600" onclick="lockBatch(${p.id}, '${safeBatch}')">锁定</button>` : ''}
              ${status === 'locked' ? `<button class="btn btn-sm btn-secondary" onclick="unlockBatch(${p.id}, '${safeBatch}')">反审</button>` : ''}
              ${status === 'locked' || status === 'editing' ? `<button class="btn btn-sm btn-secondary text-green-600" onclick="completeBatch(${p.id}, '${safeBatch}')">✅ 完成</button>` : ''}
              <button class="btn btn-sm btn-secondary batch-export-btn" onclick="exportBatchCsv(${p.id}, '${safeBatch}')" title="导出 XLSX 订单表">
                <span class="batch-export-icon"></span> XLSX
              </button>
              <button class="btn btn-sm btn-secondary batch-export-btn" onclick="exportBatchZip(${p.id}, '${safeBatch}')" title="导出 ZIP（订单表+BOM表）">
                <span class="batch-export-icon"></span> ZIP
              </button>
              ${status !== 'completed' ? `<button class="btn btn-sm btn-secondary text-orange-600" onclick="batchToCart(${p.id}, '${safeBatch}')" title="还原到购物车">
                🛒
              </button>` : ''}
              ${batchName !== '未分组' && status !== 'completed' ? `<button class="btn btn-sm btn-secondary text-red-500" onclick="deleteBatch(${p.id}, '${safeBatch}')" title="删除批次">🗑️</button>` : ''}
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-xs batch-table">
              <colgroup>
                <col style="width:18%">
                <col style="width:11%">
                <col style="width:11%">
                <col style="width:7%">
                <col style="width:9%">
                <col style="width:9%">
                <col style="width:7%">
                <col style="width:7%">
                <col style="width:6%">
                ${isEditable ? '<col style="width:15%">' : ''}
              </colgroup>
              <thead>
                <tr class="border-b border-gray-200 text-gray-500">
                  <th class="p-2 text-left">名称</th>
                  <th class="p-2 text-left">型号</th>
                  <th class="p-2 text-left">类型</th>
                  <th class="p-2 text-right">数量</th>
                  <th class="p-2 text-right">单价</th>
                  <th class="p-2 text-right">小计</th>
                  <th class="p-2 text-center">📎附件</th>
                  <th class="p-2 text-center">📊参数</th>
                  <th class="p-2 text-left">📝备注</th>
                  ${isEditable ? '<th class="p-2 text-center">操作</th>' : ''}
                </tr>
              </thead>
              <tbody>
                ${items.map(item => {
                  const subtotal = (parseFloat(item.unit_price || 0) * item.quantity).toFixed(2);
                  const hasBom = !!item.bom_snapshot;
                  const snapParams = item.part_snapshot?.parameters || [];
                  const snapAtts = item.part_snapshot?.attachments || [];
                  const snapDesc = item.part_snapshot?.description || '';
                  const hasPartSnap = !!(snapParams.length || snapAtts.length || snapDesc);
                  const snapAttrCount = snapAtts.length;
                  const snapParamCount = snapParams.length;
                  const colCount = isEditable ? 10 : 9;
                  const baseTotalCols = 9;
                  return `<tr class="border-b border-gray-100${hasBom ? ' bom-parent-row' : ''}">
                    <td class="p-2 font-medium">
                      ${hasBom ? `<span id="bom-toggle-${item.id}" class="bom-toggle-icon" onclick="toggleBomTree(${item.id})">▶</span> ` : ''}
                      ${escHtml(item.title)}
                      ${hasBom ? ' <span class="text-[10px] text-blue-400 cursor-pointer bom-expand-hint" onclick="toggleBomTree(' + item.id + ')">(展开BOM)</span>' : ''}
                    </td>
                    <td class="p-2 text-gray-500">${item.part_ipn ? escHtml(item.part_ipn) : '<span class="text-gray-300">—</span>'}</td>
                    <td class="p-2">${item.item_type === 'configuration' ? '🔧 参数化配置' : '⚙️ 静态零件'}</td>
                    <td class="p-2 text-right">×${item.quantity}</td>
                    <td class="p-2 text-right">¥${parseFloat(item.unit_price || 0).toFixed(2)}</td>
                    <td class="p-2 text-right font-medium">¥${subtotal}</td>
                    <td class="p-2 text-center">
                      ${snapAttrCount ? `<span class="cursor-pointer text-blue-500 hover:underline text-[11px]" onclick="togglePartSnapshot(${item.id})" title="查看附件详情">${snapAttrCount}</span>` : '<span class="text-gray-300">—</span>'}
                    </td>
                    <td class="p-2 text-center">
                      ${snapParamCount ? `<span class="cursor-pointer text-blue-500 hover:underline text-[11px]" onclick="togglePartSnapshot(${item.id})" title="查看参数详情">${snapParamCount}</span>` : '<span class="text-gray-300">—</span>'}
                    </td>
                    <td class="p-2 text-gray-500 text-[11px] max-w-[80px] truncate" title="${escHtml(snapDesc)}">${snapDesc ? escHtml(snapDesc).substring(0, 12) + (snapDesc.length > 12 ? '…' : '') : '<span class="text-gray-300">—</span>'}</td>
                    ${isEditable ? `<td class="p-2 text-center whitespace-nowrap">
                      <input type="checkbox" class="batch-item-cb" data-item-id="${item.id}" onchange="updateBatchActions()" style="vertical-align:middle;cursor:pointer">
                      <button class="text-blue-500 hover:text-blue-700 ml-1" onclick="event.stopPropagation(); editProjectItem(${p.id}, ${item.id})" title="编辑">✏️</button>
                      <button class="text-red-500 hover:text-red-700" onclick="event.stopPropagation(); removeProjectItem(${p.id}, ${item.id})" title="删除">✕</button>
                    </td>` : ''}
                  </tr>
                  ${hasBom ? `<tr id="bom-tree-${item.id}" class="bom-tree-container" style="display:none">
                    <td colspan="${baseTotalCols}" style="padding:0;background:#fafafa">
                      <table class="w-full bom-sub-table">
                        <thead>
                          <tr class="text-gray-400 text-[10px]">
                            <th style="padding:4px 8px;text-align:left">名称</th>
                            <th style="padding:4px 8px;text-align:left">型号</th>
                            <th style="padding:4px 8px;text-align:right">数量</th>
                            <th style="padding:4px 8px;text-align:right">单价</th>
                            <th style="padding:4px 8px;text-align:right">小计</th>
                          </tr>
                        </thead>
                        <tbody>
                          ${renderBomSnapshot(item.bom_snapshot, item.quantity || 1)}
                        </tbody>
                      </table>
                    </td>
                  </tr>` : ''}
                  ${hasPartSnap ? `<tr id="snap-tree-${item.id}" class="bom-tree-container" style="display:none">
                    <td colspan="${baseTotalCols}" style="padding:0;background:#f0fdf4">
                      ${renderPartSnapshot(item.part_snapshot)}
                    </td>
                  </tr>` : ''}`;
                }).join('')}
              </tbody>
              <tfoot>
                <tr class="bg-gray-50 font-medium text-xs">
                  <td class="p-2" colspan="3">批次合计</td>
                  <td class="p-2 text-right">×${totalQty}</td>
                  <td class="p-2 text-right"></td>
                  <td class="p-2 text-right font-semibold text-blue-600">¥${totalAmt.toFixed(2)}</td>
                  <td class="p-2"></td>
                  <td class="p-2"></td>
                  <td class="p-2"></td>
                  ${isEditable ? '<td class="p-2"></td>' : ''}
                </tr>
              </tfoot>
            </table>
          </div>
        </div>`;
      });

      html += `
      <div class="flex items-center gap-2 mt-2 flex-wrap" id="batch-actions-${p.id}">
        <span id="batch-bar-${p.id}" class="batch-action-bar" style="display:none;margin-left:8px;padding-left:8px;border-left:1px solid #d1d5db">
          <span id="batch-count-${p.id}" class="text-xs text-gray-500 mr-2">已选 0 项</span>
          <button class="btn btn-sm btn-secondary text-red-600" onclick="batchDeleteItems(${p.id})" id="batch-del-btn-${p.id}">批量删除</button>
          <button class="btn btn-sm btn-secondary" onclick="batchChangeBatch(${p.id})">改批次</button>
        </span>
      </div>`;

      return html;
    })() : `<div class="card"><div class="empty-state p-4 text-center text-gray-400 text-sm">暂无项目条目${canEdit ? `<br><button class="btn btn-sm btn-secondary mt-3" onclick="showAddItemToProject(${p.id})">添加条目到项目</button>` : ''}</div></div>`}
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
  const batches = c.batch_breakdown || [];

  // ── Bar chart SVG ──
  function renderBarChart(batches) {
    if (!batches.length) return '';
    const maxVal = Math.max(...batches.map(b => Math.max(b.total_cost, b.total_price)), 1);
    const barW = 28, gap = 12, chartH = 180, padL = 40, padR = 10, padT = 20, padB = 40;
    const groupW = barW * 2 + gap;
    const totalW = padL + batches.length * groupW + padR;

    let bars = '', labels = '';
    batches.forEach((b, i) => {
      const x = padL + i * groupW;
      const costH = (b.total_cost / maxVal) * (chartH - padT - padB);
      const priceH = (b.total_price / maxVal) * (chartH - padT - padB);
      const costY = chartH - padB - costH;
      const priceY = chartH - padB - priceH;
      const label = b.batch_name.length > 6 ? b.batch_name.slice(0, 6) + '..' : b.batch_name;
      bars += `<rect x="${x}" y="${costY}" width="${barW}" height="${costH}" fill="#ef4444" opacity="0.8" rx="2">
        <title>${b.batch_name} 成本: ¥${b.total_cost.toFixed(2)}</title></rect>`;
      bars += `<rect x="${x + barW + gap}" y="${priceY}" width="${barW}" height="${priceH}" fill="#22c55e" opacity="0.8" rx="2">
        <title>${b.batch_name} 售价: ¥${b.total_price.toFixed(2)}</title></rect>`;
      labels += `<text x="${x + barW + gap/2}" y="${chartH + 14}" text-anchor="middle" font-size="10" fill="#888">${label}</text>`;
    });

    // Y axis
    let yAxis = '';
    const steps = 4;
    for (let i = 0; i <= steps; i++) {
      const val = (maxVal / steps) * i;
      const y = chartH - padB - (val / maxVal) * (chartH - padT - padB);
      yAxis += `<text x="${padL - 4}" y="${y + 3}" text-anchor="end" font-size="9" fill="#aaa">¥${val >= 1000 ? (val/1000).toFixed(0) + 'k' : val.toFixed(0)}</text>`;
      yAxis += `<line x1="${padL}" y1="${y}" x2="${totalW}" y2="${y}" stroke="#eee" stroke-width="0.5"/>`;
    }

    return `<svg width="${totalW}" height="${chartH}" viewBox="0 0 ${totalW} ${chartH}" style="max-width:100%">
      ${yAxis}${bars}${labels}
      <rect x="${padL}" y="${padT}" width="${totalW-padR-padL}" height="${chartH-padT-padB}" fill="none" stroke="#e5e7eb" stroke-width="1"/>
      <text x="${padL}" y="${12}" font-size="10" fill="#666">金额 (¥)</text>
    </svg>`;
  }

  // ── Pie chart SVG ──
  function renderPieChart(batches) {
    if (!batches.length) return '';
    const total = batches.reduce((s, b) => s + b.total_cost, 0);
    if (total <= 0) return '<div class="text-xs text-gray-400 text-center py-4">无成本数据</div>';
    const cx = 110, cy = 110, r = 80, ir = 50; // donut
    const colors = ['#3b82f6','#ef4444','#f59e0b','#22c55e','#8b5cf6','#ec4899','#14b8a6','#f97316','#6366f1','#84cc16'];
    let cumulative = 0;
    let slices = '';
    let legend = '';

    batches.forEach((b, i) => {
      const angle = (b.total_cost / total) * 360;
      const startAngle = cumulative;
      const endAngle = cumulative + angle;
      cumulative = endAngle;

      const sr = ((startAngle - 90) * Math.PI) / 180;
      const er = ((endAngle - 90) * Math.PI) / 180;
      const x1 = cx + r * Math.cos(sr);
      const y1 = cy + r * Math.sin(sr);
      const x2 = cx + r * Math.cos(er);
      const y2 = cy + r * Math.sin(er);
      const large = angle > 180 ? 1 : 0;
      const color = colors[i % colors.length];

      slices += `<path d="M${cx} ${cy} L${x1} ${y1} A${r} ${r} 0 ${large} 1 ${x2} ${y2} Z" fill="${color}">
        <title>${b.batch_name}: ¥${b.total_cost.toFixed(2)} (${(b.total_cost/total*100).toFixed(1)}%)</title></path>`;

      // Legend
      const pct = (b.total_cost / total * 100).toFixed(1);
      legend += `<div class="flex items-center gap-1.5 text-xs mt-1">
        <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${color}"></span>
        <span class="text-gray-600">${escHtml(b.batch_name)}</span>
        <span class="text-gray-400 ml-auto">¥${b.total_cost.toFixed(2)} (${pct}%)</span>
      </div>`;
    });

    // Donut hole
    slices += `<circle cx="${cx}" cy="${cy}" r="${ir}" fill="white"/>`;
    slices += `<text x="${cx}" y="${cy - 6}" text-anchor="middle" font-size="16" font-weight="bold" fill="#333">¥${total.toFixed(0)}</text>`;
    slices += `<text x="${cx}" y="${cy + 10}" text-anchor="middle" font-size="9" fill="#999">总成本</text>`;

    return `<div class="flex flex-col sm:flex-row items-center gap-4">
      <svg width="220" height="220" viewBox="0 0 220 220">${slices}</svg>
      <div class="flex-1 min-w-0">${legend}</div>
    </div>`;
  }

  // ── Build page ──
  let batchTableHtml = '';
  if (batches.length > 0) {
    batchTableHtml = `
    <div class="card mb-3">
      <div class="text-sm font-medium text-gray-700 mb-2">📊 按批次统计</div>
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead><tr class="border-b border-gray-200 text-gray-500">
            <th class="p-2 text-left">批次</th>
            <th class="p-2 text-right">项目数</th>
            <th class="p-2 text-right">总数量</th>
            <th class="p-2 text-right">成本小计</th>
            <th class="p-2 text-right">售价小计</th>
            <th class="p-2 text-right">利润</th>
            <th class="p-2 text-right">毛利率</th>
          </tr></thead>
          <tbody>
            ${batches.map(b => {
              const profit = b.total_price - b.total_cost;
              const margin = b.total_price > 0 ? (profit / b.total_price * 100).toFixed(1) : '0.0';
              return `<tr class="border-b border-gray-100">
                <td class="p-2 font-medium">${escHtml(b.batch_name)}</td>
                <td class="p-2 text-right">${b.item_count}</td>
                <td class="p-2 text-right">×${b.total_qty}</td>
                <td class="p-2 text-right text-red-600">¥${b.total_cost.toFixed(2)}</td>
                <td class="p-2 text-right text-green-600">¥${b.total_price.toFixed(2)}</td>
                <td class="p-2 text-right ${profit >= 0 ? 'text-green-600' : 'text-red-500'}">¥${profit.toFixed(2)}</td>
                <td class="p-2 text-right">${margin}%</td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>`;
  }

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
    ${batches.length > 0 ? `
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-3">
      <div class="card">
        <div class="text-sm font-medium text-gray-700 mb-2 cursor-pointer select-none" onclick="toggleCostSection('bar-${c.project_id}')">
          <span id="cost-toggle-bar-${c.project_id}" class="inline-block w-4 text-center text-gray-400">▶</span> 📊 各批次成本/售价对比
        </div>
        <div id="cost-section-bar-${c.project_id}" style="display:none">
          ${renderBarChart(batches)}
        </div>
      </div>
      <div class="card">
        <div class="text-sm font-medium text-gray-700 mb-2 cursor-pointer select-none" onclick="toggleCostSection('pie-${c.project_id}')">
          <span id="cost-toggle-pie-${c.project_id}" class="inline-block w-4 text-center text-gray-400">▶</span> 🥧 成本占比
        </div>
        <div id="cost-section-pie-${c.project_id}" style="display:none">
          ${renderPieChart(batches)}
        </div>
      </div>
    </div>
    ${batchTableHtml.replace(
      '<div class="text-sm font-medium text-gray-700 mb-2">📊 按批次统计</div>',
      `<div class="text-sm font-medium text-gray-700 mb-2 cursor-pointer select-none" onclick="toggleCostSection('batch-${c.project_id}')">
        <span id="cost-toggle-batch-${c.project_id}" class="inline-block w-4 text-center text-gray-400">▶</span> 📊 按批次统计
      </div>
      <div id="cost-section-batch-${c.project_id}" style="display:none">`
    ) + (batches.length > 0 ? '</div>' : '')}
    ${(() => {
      const cats = c.category_breakdown || [];
      if (!cats.length) return '';
      const colors = ['#3b82f6','#ef4444','#f59e0b','#22c55e','#8b5cf6','#ec4899','#14b8a6','#f97316','#6366f1','#84cc16'];
      return `
    <div class="card mb-3">
      <div class="text-sm font-medium text-gray-700 mb-2 cursor-pointer select-none" onclick="toggleCostSection('cat-${c.project_id}')">
        <span id="cost-toggle-cat-${c.project_id}" class="inline-block w-4 text-center text-gray-400">▶</span> 🏷️ 按物料类别统计
      </div>
      <div id="cost-section-cat-${c.project_id}" style="display:none">
        <div class="flex flex-col sm:flex-row items-start gap-4 mb-4">
          <div class="flex flex-col items-center">
            <span class="text-xs text-gray-400 mb-1">💰 成本占比</span>
            <svg width="220" height="200" viewBox="0 0 220 200">
              ${(() => {
                const ctotal = cats.reduce((s, t) => s + t.total_cost, 0);
                if (ctotal <= 0) return '';
                const cx = 100, cy = 100, r = 75, ir = 45;
                let cumul = 0, slices = '';
                cats.forEach((t, i) => {
                  const angle = (t.total_cost / ctotal) * 360;
                  const sa = cumul; cumul += angle; const ea = cumul;
                  const sr = ((sa - 90) * Math.PI) / 180;
                  const er = ((ea - 90) * Math.PI) / 180;
                  const x1 = cx + r * Math.cos(sr), y1 = cy + r * Math.sin(sr);
                  const x2 = cx + r * Math.cos(er), y2 = cy + r * Math.sin(er);
                  const large = angle > 180 ? 1 : 0;
                  const color = colors[i % colors.length];
                  slices += `<path d="M${cx} ${cy} L${x1} ${y1} A${r} ${r} 0 ${large} 1 ${x2} ${y2} Z" fill="${color}"><title>${escHtml(t.category)}: ¥${t.total_cost.toFixed(2)} (${(t.total_cost/ctotal*100).toFixed(1)}%)</title></path>`;
                });
                slices += `<circle cx="${cx}" cy="${cy}" r="${ir}" fill="white"/>`;
                slices += `<text x="${cx}" y="${cy - 6}" text-anchor="middle" font-size="14" font-weight="bold" fill="#333">¥${ctotal.toFixed(0)}</text>`;
                slices += `<text x="${cx}" y="${cy + 10}" text-anchor="middle" font-size="8" fill="#999">总成本</text>`;
                return slices;
              })()}
            </svg>
          </div>
          <div class="flex flex-col items-center">
            <span class="text-xs text-gray-400 mb-1">📦 物料数量占比</span>
            <svg width="220" height="200" viewBox="0 0 220 200">
              ${(() => {
                const ntotal = cats.reduce((s, t) => s + t.count, 0);
                if (ntotal <= 0) return '';
                const cx = 100, cy = 100, r = 75;
                let cumul = 0, slices = '';
                cats.forEach((t, i) => {
                  const angle = (t.count / ntotal) * 360;
                  const sa = cumul; cumul += angle; const ea = cumul;
                  const sr = ((sa - 90) * Math.PI) / 180;
                  const er = ((ea - 90) * Math.PI) / 180;
                  const x1 = cx + r * Math.cos(sr), y1 = cy + r * Math.sin(sr);
                  const x2 = cx + r * Math.cos(er), y2 = cy + r * Math.sin(er);
                  const large = angle > 180 ? 1 : 0;
                  const color = colors[i % colors.length];
                  slices += `<path d="M${cx} ${cy} L${x1} ${y1} A${r} ${r} 0 ${large} 1 ${x2} ${y2} Z" fill="${color}"><title>${escHtml(t.category)}: ${t.count} 件 (${(t.count/ntotal*100).toFixed(1)}%)</title></path>`;
                });
                slices += `<circle cx="${cx}" cy="${cy}" r="30" fill="white"/>`;
                slices += `<text x="${cx}" y="${cy - 5}" text-anchor="middle" font-size="16" font-weight="bold" fill="#333">${ntotal}</text>`;
                slices += `<text x="${cx}" y="${cy + 10}" text-anchor="middle" font-size="8" fill="#999">总件数</text>`;
                return slices;
              })()}
            </svg>
          </div>
          <div class="flex-1 min-w-0 text-xs space-y-1.5">
            <span class="text-xs text-gray-400 block mb-1">🎨 图例</span>
            ${cats.map((t, i) => {
              const cpct = c.total_cost > 0 ? (t.total_cost / c.total_cost * 100).toFixed(1) : '0';
              const npct = cats.reduce((s, x) => s + x.count, 0) > 0 ? (t.count / cats.reduce((s, x) => s + x.count, 0) * 100).toFixed(1) : '0';
              const color = colors[i % colors.length];
              return `<div class="flex items-center gap-2">
                <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${color}"></span>
                <span class="text-gray-600">${escHtml(t.category)}</span>
                <span class="text-gray-400 ml-auto">${t.count}件 ¥${t.total_cost.toFixed(2)} (成本${cpct}%)</span>
              </div>`;
            }).join('')}
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          ${cats.map((t, i) => {
            const pct = c.total_cost > 0 ? (t.total_cost / c.total_cost * 100).toFixed(1) : '0';
            const profit = t.total_price - t.total_cost;
            const color = colors[i % colors.length];
            const barW = Math.max(4, parseFloat(pct));
            return `<div class="border rounded-lg p-3">
              <div class="flex items-center gap-2 mb-2">
                <span class="font-medium text-sm">${escHtml(t.category)}</span>
                <span class="text-xs text-gray-400">${t.count} 条</span>
              </div>
              <div class="flex items-center gap-3 mb-1">
                <span class="text-xs text-gray-500 w-14">成本</span>
                <div class="flex-1 h-4 bg-gray-100 rounded overflow-hidden">
                  <div style="width:${barW}%;height:100%;background:${color};border-radius:3px;min-width:4px"></div>
                </div>
                <span class="text-xs font-medium text-red-600 w-20 text-right">¥${t.total_cost.toFixed(2)}</span>
              </div>
              <div class="flex items-center gap-3 mb-1">
                <span class="text-xs text-gray-500 w-14">售价</span>
                <div class="flex-1 h-4 bg-gray-100 rounded overflow-hidden">
                  <div style="width:${c.total_price > 0 ? Math.max(4, t.total_price / c.total_price * 100).toFixed(0) : 0}%;height:100%;background:#22c55e;border-radius:3px;min-width:4px"></div>
                </div>
                <span class="text-xs font-medium text-green-600 w-20 text-right">¥${t.total_price.toFixed(2)}</span>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-xs text-gray-500 w-14">利润</span>
                <span class="text-xs font-medium ${profit >= 0 ? 'text-green-600' : 'text-red-500'}">¥${profit.toFixed(2)}</span>
              </div>
            </div>`;
          }).join('')}
        </div>
      </div>
    </div>`;})()}` : ''}
    ${c.breakdown && c.breakdown.length ? `
    <div class="card">
      <div class="text-sm font-medium text-gray-700 mb-2 cursor-pointer select-none" onclick="toggleCostSection('detail-${c.project_id}')">
        <span id="cost-toggle-detail-${c.project_id}" class="inline-block w-4 text-center text-gray-400">▶</span> 📋 明细清单
      </div>
      <div id="cost-section-detail-${c.project_id}" style="display:none">
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
          <td class="p-2">${escHtml(b.title)} <span class="text-gray-400">${escHtml(b.batch_name || '')}</span></td>
          <td class="p-2 text-right">×${b.quantity}</td>
          <td class="p-2 text-right">¥${b.unit_cost.toFixed(2)}</td>
          <td class="p-2 text-right">¥${b.unit_price.toFixed(2)}</td>
          <td class="p-2 text-right">¥${b.subtotal_cost.toFixed(2)}</td>
          <td class="p-2 text-right">¥${b.subtotal_price.toFixed(2)}</td>
        </tr>`).join('')}
      </tbody>
    </table></div></div>` : '<div class="text-xs text-gray-400 text-center py-2">暂无成本明细</div>'}`;
}

// ── Toggle cost section ──
function toggleCostSection(id) {
  const section = document.getElementById("cost-section-" + id);
  const toggle = document.getElementById("cost-toggle-" + id);
  if (!section || !toggle) return;
  const isHidden = section.style.display === "none";
  section.style.display = isHidden ? "" : "none";
  toggle.textContent = isHidden ? "▼" : "▶";
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

// ── Archive / Restore / Hard Delete ──
async function confirmArchiveProject(id, isActive) {
  const action = isActive ? '归档' : '恢复';
  if (!confirm(`确定${action}此项目？${isActive ? '归档后项目将不再显示在列表中，可在URL加?inactive=1查看' : ''}`)) return;
  const endpoint = isActive ? 'archive' : 'restore';
  const r = await projectApi('POST', `/${id}/${endpoint}/`);
  if (r.ok) {
    setStatus('success', `项目已${action}`);
    showProjectDetail(id);
  } else {
    setStatus('error', `${action}失败`);
  }
}
async function confirmHardDelete(id) {
  if (!confirm('⚠️ 确定永久删除此项目？该操作不可恢复，所有条目和日志将被彻底清除！')) return;
  if (!confirm('再次确认：此操作不可撤销！')) return;
  const r = await projectApi('POST', `/${id}/hard_delete/`);
  if (r.ok) {
    setStatus('success', `项目已永久删除: ${r.data?.deleted || ''}`);
    switchPage('projects');
  } else {
    setStatus('error', '删除失败');
  }
}

// ── Add item to project dialog ──
let _addItemSelectedParts = []; // {id, name, ipn, qty, price, unit}

function showAddItemDialog(projectId, batchName) {
  window._addItemBatchName = batchName || '';
  _addItemSelectedParts = [];

  showModal('批量添加物料', `
    <div class="flex flex-col gap-3">
      <div>
        <label class="text-xs text-gray-500">搜索零件（点击添加到列表）</label>
        <input class="input-field w-full" id="ai-part-search" placeholder="输入零件名称/IPN搜索..." oninput="searchPartsForBatchAdd()">
        <div id="ai-part-results" class="mt-1 max-h-[200px] overflow-y-auto"></div>
      </div>
      <div id="ai-selected-area" style="display:none">
        <label class="text-xs text-gray-500 font-medium">已选物料 <span id="ai-selected-count" class="text-blue-600">0</span> 项</label>
        <div class="border border-gray-200 rounded max-h-[300px] overflow-y-auto" id="ai-selected-table-wrap">
          <table class="w-full text-xs">
            <thead><tr class="border-b border-gray-200 bg-gray-50 text-gray-500">
              <th class="p-2 text-left">物料名称</th>
              <th class="p-2 text-center w-[60px]">数量</th>
              <th class="p-2 text-right w-[100px]">单价 (¥)</th>
              <th class="p-2 text-center w-[50px]">操作</th>
            </tr></thead>
            <tbody id="ai-selected-tbody"></tbody>
          </table>
        </div>
      </div>
      <div class="text-xs text-gray-400">提示：搜索后点击零件即可添加到列表，支持批量添加</div>
    </div>`, [
    { text: '取消', cls: 'btn btn-sm btn-secondary', action: closeModal },
    { text: '确认添加', cls: 'btn btn-sm btn-success', action: async () => {
      if (!_addItemSelectedParts.length) { setStatus('error', '请先搜索并添加物料'); return; }
      let ok = 0, fail = 0;
      for (const sp of _addItemSelectedParts) {
        const data = {
          item_type: 'part',
          part: sp.id,
          title: sp.name,
          quantity: sp.qty || 1,
          unit_price: sp.price || null,
        };
        if (window._addItemBatchName) data.batch_name = window._addItemBatchName;
        const result = await projectApi('POST', `/${projectId}/add_item/`, data);
        if (result.ok) ok++; else fail++;
      }
      closeModal();
      if (ok > 0) setStatus('success', `成功添加 ${ok} 个物料${fail > 0 ? '，' + fail + ' 个失败' : ''}`);
      else setStatus('error', '添加失败');
      showProjectDetail(projectId);
    }},
  ]);
}

function searchPartsForBatchAdd() {
  clearTimeout(_partSearchTimer);
  const input = document.getElementById('ai-part-search');
  if (!input) return;
  const q = input.value.trim();
  const results = document.getElementById('ai-part-results');
  if (!results) return;
  if (q.length < 2) { results.innerHTML = ''; return; }

  _partSearchTimer = setTimeout(async () => {
    try {
      const basePath = window._inventreeApiBase || '/api';
      const resp = await fetch(basePath + '/part/?search=' + encodeURIComponent(q) + '&limit=15', { credentials: 'same-origin' });
      const data = await resp.json();
      const parts = data.results || data || [];
      if (!parts.length) { results.innerHTML = '<div class="text-xs text-gray-400 py-1">未找到零件</div>'; return; }
      results.innerHTML = parts.map(p =>
        '<div class="flex items-center justify-between py-1.5 px-2 text-xs border border-gray-200 rounded hover:bg-gray-50 cursor-pointer"' +
        ' onclick="addToSelectedList(' + p.pk + ', \'' + escHtml(p.name).replace(/'/g, "\\'") + '\', \'' + escHtml(p.IPN || '').replace(/'/g, "\\'") + '\')">' +
        '<div><span class="font-medium">' + escHtml(p.name) + '</span> ' +
        '<span class="text-gray-400 ml-1">' + escHtml(p.IPN || '') + '</span></div>' +
        '<span class="text-blue-500 font-medium text-[11px]">+ 添加</span>' +
        '</div>'
      ).join('');
    } catch(e) { results.innerHTML = '<div class="text-xs text-red-400 py-1">搜索失败</div>'; }
  }, 300);
}

async function addToSelectedList(partId, partName, partIpn) {
  // Check if already selected
  if (_addItemSelectedParts.find(p => p.id === partId)) {
    setStatus('info', '该物料已在列表中');
    return;
  }

  // Fetch pricing
  let price = null;
  try {
    const basePath = window._inventreeApiBase || '/api';
    const pResp = await fetch(basePath + '/part/' + partId + '/pricing/', { credentials: 'same-origin' });
    if (pResp.ok) {
      const pData = await pResp.json();
      price = parseFloat(pData.overall_min || pData.overall_max || pData.internal_cost_min || pData.bom_cost_min || 0) || null;
      if (price !== null) price = Math.round(price * 100) / 100;
    }
  } catch(e) {}

  _addItemSelectedParts.push({ id: partId, name: partName, ipn: partIpn, qty: 1, price: price });
  renderSelectedList();
  document.getElementById('ai-part-search').value = '';
  document.getElementById('ai-part-results').innerHTML = '';
}

function renderSelectedList() {
  const area = document.getElementById('ai-selected-area');
  const tbody = document.getElementById('ai-selected-tbody');
  const count = document.getElementById('ai-selected-count');
  if (!area || !tbody) return;

  if (!_addItemSelectedParts.length) {
    area.style.display = 'none';
    return;
  }

  area.style.display = '';
  if (count) count.textContent = _addItemSelectedParts.length;

  tbody.innerHTML = _addItemSelectedParts.map((sp, idx) =>
    '<tr class="border-b border-gray-100">' +
    '<td class="p-2"><span class="font-medium">' + escHtml(sp.name) + '</span>' +
    (sp.ipn ? ' <span class="text-gray-400">' + escHtml(sp.ipn) + '</span>' : '') + '</td>' +
    '<td class="p-2 text-center"><input type="number" min="1" max="9999" value="' + sp.qty + '"' +
    ' onchange="updateSelectedQty(' + idx + ', this.value)"' +
    ' style="width:50px;text-align:center;border:1px solid #d0d5dd;border-radius:3px;padding:2px 4px;font-size:12px"></td>' +
    '<td class="p-2 text-right">' + (sp.price !== null ? '<span class="text-gray-700">¥' + sp.price.toFixed(2) : '<span class="text-gray-300">自动</span>') + '</td>' +
    '<td class="p-2 text-center"><span class="text-red-500 cursor-pointer text-[13px]" onclick="removeSelectedItem(' + idx + ')">✕</span></td>' +
    '</tr>'
  ).join('');
}

function updateSelectedQty(idx, val) {
  const qty = parseInt(val) || 1;
  if (idx >= 0 && idx < _addItemSelectedParts.length) {
    _addItemSelectedParts[idx].qty = Math.max(1, Math.min(9999, qty));
  }
}

function removeSelectedItem(idx) {
  if (idx >= 0 && idx < _addItemSelectedParts.length) {
    _addItemSelectedParts.splice(idx, 1);
    renderSelectedList();
  }
}

function showAddItemToProject(projectId) {
  const p = window._projectData;
  if (!p || !p.items) { showAddItemDialog(projectId, ''); return; }
  const batches = new Set();
  p.items.forEach(it => { if (it.batch_name) batches.add(it.batch_name); });
  let nextNum = 1;
  for (let n = 1; n <= 20; n++) {
    if (!batches.has('第' + n + '批')) { nextNum = n; break; }
  }
  showAddItemDialog(projectId, '第' + nextNum + '批');
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

async function editProjectItem(projectId, itemId) {
  // Fetch current item data from the detail view's rendered table
  const projectData = window._projectData;
  if (!projectData) return;
  const allItems = (projectData.items || []).filter(Boolean);
  // If items is not populated (e.g., loaded via detail endpoint), fetch directly
  let item = allItems.find(i => i.id === itemId);
  if (!item) {
    const resp = await fetch(`/api/parametric-bom/projects/${projectId}/`);
    if (resp.ok) {
      const data = await resp.json();
      window._projectData = data;
      item = (data.items || []).find(i => i.id === itemId);
    }
  }
  if (!item) { setStatus('error', '找不到条目数据'); return; }

  const bodyHtml = `
    <div class="space-y-3">
      <div>
        <label class="block text-xs text-gray-500 mb-1">名称</label>
        <input id="edit-item-title" class="w-full border border-gray-300 rounded px-3 py-2 text-sm" value="${escHtml(item.title)}">
      </div>
      <div class="flex gap-3">
        <div class="flex-1">
          <label class="block text-xs text-gray-500 mb-1">数量</label>
          <input id="edit-item-qty" type="number" min="1" class="w-full border border-gray-300 rounded px-3 py-2 text-sm" value="${item.quantity}">
        </div>
        <div class="flex-1">
          <label class="block text-xs text-gray-500 mb-1">单价 (¥)</label>
          <input id="edit-item-price" type="number" step="0.0001" min="0" class="w-full border border-gray-300 rounded px-3 py-2 text-sm" value="${parseFloat(item.unit_price || 0).toFixed(4)}">
        </div>
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">备注</label>
        <input id="edit-item-notes" class="w-full border border-gray-300 rounded px-3 py-2 text-sm" value="${escHtml(item.notes || '')}">
      </div>
    </div>`;
  const buttons = [
    { text: '取消', cls: 'btn btn-sm btn-secondary', action: () => document.getElementById('hermes-modal-overlay')?.remove() },
    { text: '保存', cls: 'btn btn-sm btn-primary bg-blue-500 text-white', action: async () => {
      const title = document.getElementById('edit-item-title')?.value?.trim();
      const qty = parseInt(document.getElementById('edit-item-qty')?.value);
      const price = parseFloat(document.getElementById('edit-item-price')?.value);
      const notes = document.getElementById('edit-item-notes')?.value?.trim();
      if (!title || !qty || qty < 1) { setStatus('error', '名称和数量不能为空'); return; }
      const payload = { title, quantity: qty };
      if (price >= 0) payload.unit_price = String(price);
      payload.notes = notes || '';
      const result = await projectApi('PATCH', `/${projectId}/items/${itemId}/`, payload);
      if (result.ok) {
        document.getElementById('hermes-modal-overlay')?.remove();
        setStatus('success', '条目已更新');
        showProjectDetail(projectId);
      } else {
        setStatus('error', result.data?.error || '更新失败');
      }
    }},
  ];
  showModal('编辑条目', bodyHtml, buttons);
}

// ── Batch operations ──
function updateBatchActions() {
  const cbs = document.querySelectorAll('.batch-item-cb:checked');
  const checked = Array.from(cbs).map(cb => cb.dataset.itemId);
  const bar = document.querySelector('[id^="batch-bar-"]');
  if (!bar) return;
  const pid = bar.id.replace('batch-bar-', '');
  const countEl = document.getElementById('batch-count-' + pid);
  const barEl = document.getElementById('batch-bar-' + pid);
  if (countEl) countEl.textContent = `已选 ${checked.length} 项`;
  if (barEl) barEl.style.display = checked.length > 0 ? 'inline' : 'none';
}
async function batchDeleteItems(projectId) {
  const cbs = document.querySelectorAll('.batch-item-cb:checked');
  const ids = Array.from(cbs).map(cb => cb.dataset.itemId);
  if (!ids.length) return;
  if (!confirm(`确定删除选中的 ${ids.length} 个条目？`)) return;
  let ok = 0, fail = 0;
  for (const id of ids) {
    const r = await projectApi('DELETE', `/${projectId}/items/${id}/`);
    if (r.ok) ok++; else fail++;
  }
  setStatus(ok > 0 ? 'success' : 'error', `批量删除完成: ${ok} 成功, ${fail} 失败`);
  showProjectDetail(projectId);
}
async function batchChangeBatch(projectId) {
  const cbs = document.querySelectorAll('.batch-item-cb:checked');
  const ids = Array.from(cbs).map(cb => cb.dataset.itemId);
  if (!ids.length) return;
  const newBatch = prompt('请输入新的批次名称：');
  if (!newBatch || !newBatch.trim()) return;
  let ok = 0, fail = 0;
  for (const id of ids) {
    const r = await projectApi('PATCH', `/${projectId}/items/${id}/`, { batch_name: newBatch.trim() });
    if (r.ok) ok++; else fail++;
  }
  setStatus(ok > 0 ? 'success' : 'error', `批次修改完成: ${ok} 成功, ${fail} 失败`);
  showProjectDetail(projectId);
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

// ── BOM Tree expand ──
function renderBomSnapshot(snapshot, multiplier) {
  // Handle flat format: {bom_tree: [{part_name, quantity, unit_price, IPN, ...}], part_name: "..."}
  if (!snapshot) return '';
  const m = multiplier || 1;

  // Flat format (ProjectItem storage)
  const bomTree = snapshot.bom_tree;
  if (Array.isArray(bomTree)) {
    let html = '';
    for (const item of bomTree) {
      const qty = (item.quantity || 1) * m;
      const up = item.unit_price != null ? parseFloat(item.unit_price) : null;
      const tp = up != null ? up * qty : null;
      html += `<tr class="bom-tree-row" style="font-size:11px">
        <td style="padding:3px 6px;padding-left:16px">${escHtml(item.part_name || '')}</td>
        <td style="padding:3px 6px;color:#6b7280">${item.IPN ? escHtml(item.IPN) : '<span style="color:#d1d5db">—</span>'}</td>
        <td style="padding:3px 6px;text-align:right">×${qty.toFixed(2)}</td>
        <td style="padding:3px 6px;text-align:right">${up != null ? '¥' + up.toFixed(2) : '—'}</td>
        <td style="padding:3px 6px;text-align:right;font-weight:500">${tp != null ? '¥' + tp.toFixed(2) : '—'}</td>
      </tr>`;
    }
    return html;
  }

  // Tree format (recursive BomTreeNode)
  return renderBomTreeNode(snapshot, 0, m);
}

function renderBomTreeNode(node, depth, multiplier) {
  if (!node) return '';
  const m = multiplier || 1;
  const qty = (node.calculated_quantity || node.quantity || 1) * m;
  const name = node.calculated_name || node.part_name || '';
  const ipn = node.calculated_ipn || node.static_ipn || '';
  const unitPrice = node.unit_price != null ? parseFloat(node.unit_price) : null;
  const totalPrice = node.total_price != null ? parseFloat(node.total_price) : (unitPrice != null ? unitPrice * qty : null);
  const hasChildren = node.children && node.children.length > 0;
  const excluded = node.excluded;
  const childId = Math.random().toString(36).slice(2, 7);
  let html = '';
  const indent = depth * 20;
  const rowClass = excluded ? 'bom-tree-excluded' : (depth === 0 ? 'bom-tree-root' : '');
  const toggleBtn = hasChildren
    ? `<span class="bom-tree-toggle" onclick="toggleBomSubTree('${childId}')" style="cursor:pointer;margin-right:4px;font-size:10px;user-select:none">▶</span>`
    : '<span style="display:inline-block;width:12px"></span>';
  html += `<tr class="bom-tree-row ${rowClass}" style="font-size:11px">
    <td style="padding:3px 6px;padding-left:${12 + indent}px">
      ${toggleBtn}${escHtml(name)}
      ${excluded ? ' <span class="text-red-400 text-[10px]">(已排除)</span>' : ''}
    </td>
    <td style="padding:3px 6px;color:#6b7280">${ipn ? escHtml(ipn) : '<span style="color:#d1d5db">—</span>'}</td>
    <td style="padding:3px 6px;text-align:right">×${qty.toFixed(2)}</td>
    <td style="padding:3px 6px;text-align:right">${unitPrice != null ? '¥' + unitPrice.toFixed(2) : '—'}</td>
    <td style="padding:3px 6px;text-align:right;font-weight:500">${totalPrice != null ? '¥' + totalPrice.toFixed(2) : '—'}</td>
  </tr>`;
  if (hasChildren) {
    html += `<tbody id="bom-sub-${childId}" style="display:none">`;
    for (const child of node.children) {
      html += renderBomTreeNode(child, depth + 1, m * qty);
    }
    html += '</tbody>';
  }
  return html;
}

function toggleBomTree(itemId) {
  const row = document.getElementById('bom-tree-' + itemId);
  const toggle = document.getElementById('bom-toggle-' + itemId);
  if (!row) return;
  const expanded = row.style.display !== 'none';
  row.style.display = expanded ? 'none' : '';
  if (toggle) toggle.textContent = expanded ? '▶' : '▼';
}

function toggleBomSubTree(childId) {
  const tbody = document.getElementById('bom-sub-' + childId);
  const toggle = tbody?.previousElementSibling?.querySelector('.bom-tree-toggle');
  if (!tbody) return;
  const expanded = tbody.style.display !== 'none';
  tbody.style.display = expanded ? 'none' : '';
  if (toggle) toggle.textContent = expanded ? '▶' : '▼';
}

function togglePartSnapshot(itemId) {
  const row = document.getElementById('snap-tree-' + itemId);
  const toggle = document.getElementById('snap-toggle-' + itemId);
  if (!row) return;
  const expanded = row.style.display !== 'none';
  row.style.display = expanded ? 'none' : '';
  if (toggle) toggle.textContent = expanded ? '📋' : '📋';
}

function renderPartSnapshot(snapshot) {
  if (!snapshot) return '';

  let html = '<div style="padding:8px 12px;font-size:11px">';

  // Description
  if (snapshot.description) {
    html += '<div class="mb-2"><span class="text-gray-400 text-[10px]">📝 备注：</span>';
    html += '<span class="text-gray-700">' + escHtml(snapshot.description) + '</span></div>';
  }

  // Parameters table
  if (snapshot.parameters && snapshot.parameters.length) {
    html += '<div class="mb-2"><span class="text-gray-400 text-[10px] font-medium">📊 参数（快照）：</span>';
    html += '<table class="w-full text-[11px] mt-1" style="border-collapse:collapse">';
    html += '<thead><tr class="text-gray-400 text-[10px]">';
    html += '<th style="padding:2px 6px;text-align:left;border-bottom:1px solid #d1fae5">名称</th>';
    html += '<th style="padding:2px 6px;text-align:left;border-bottom:1px solid #d1fae5">值</th>';
    html += '<th style="padding:2px 6px;text-align:left;border-bottom:1px solid #d1fae5">单位</th>';
    html += '</tr></thead><tbody>';
    snapshot.parameters.forEach(p => {
      html += '<tr>';
      html += '<td style="padding:2px 6px;border-bottom:1px solid #ecfdf5">' + escHtml(p.name) + '</td>';
      html += '<td style="padding:2px 6px;border-bottom:1px solid #ecfdf5;font-medium">' + escHtml(p.value) + '</td>';
      html += '<td style="padding:2px 6px;border-bottom:1px solid #ecfdf5;color:#9ca3af">' + escHtml(p.unit || '—') + '</td>';
      html += '</tr>';
    });
    html += '</tbody></table></div>';
  }

  // Attachments list
  if (snapshot.attachments && snapshot.attachments.length) {
    html += '<div><span class="text-gray-400 text-[10px] font-medium">📎 附件（快照）：</span>';
    html += '<div class="mt-1">';
    snapshot.attachments.forEach(att => {
      html += '<div class="flex items-center gap-2 py-1 text-[11px]">';
      html += '<span class="text-gray-600">📄 ' + escHtml(att.filename) + '</span>';
      if (att.comment) {
        html += '<span class="text-gray-400 text-[10px]">' + escHtml(att.comment) + '</span>';
      }
      if (att.url) {
        html += '<a href="' + att.url + '" target="_blank" class="text-blue-500 hover:underline text-[10px]">查看</a>';
      }
      html += '</div>';
    });
    html += '</div></div>';
  }

  html += '</div>';
  return html;
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
    if (el) { el.style.setProperty('display', 'none', 'important'); document.body.style.overflow = ''; }
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

// ── Batch export ──
function exportBatchCsv(projectId, batchName) {
  const url = `/api/parametric-bom/projects/${projectId}/export-batch-csv/?batch_name=${batchName}`;
  const a = document.createElement('a');
  a.href = url;
  a.download = '';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setStatus('success', '正在下载 XLSX 订单表...');
}

function exportBatchZip(projectId, batchName) {
  const url = `/api/parametric-bom/projects/${projectId}/export-batch-zip/?batch_name=${batchName}`;
  const a = document.createElement('a');
  a.href = url;
  a.download = '';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setStatus('success', '正在下载 ZIP 订单包...');
}

async function batchToCart(projectId, batchName) {
  const name = decodeURIComponent(batchName);
  if (!confirm(`确定将批次「${name}」的所有条目还原到购物车？项目中的这些条目将被删除。`)) return;
  const result = await projectApi('POST', `/${projectId}/batch-to-cart/`, { batch_name: name });
  if (result.ok) {
    setStatus('success', result.data.message || '已还原到购物车');
    showProjectDetail(projectId);
  } else {
    setStatus('error', result.data?.error || '还原失败');
  }
}

function showInputDialog(title, currentValue) {
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'fixed inset-0 bg-black/30 z-[9999] flex items-center justify-center';
    overlay.onclick = (e) => { if (e.target === overlay) { overlay.remove(); resolve(null); } };
    
    overlay.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl p-5 w-96" onclick="event.stopPropagation()">
        <div class="text-sm font-semibold text-gray-700 mb-3">${title}</div>
        <input id="_batchInp" type="text" value="${(currentValue||'').replace(/"/g,'&quot;')}" 
          class="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-4 focus:ring-2 focus:ring-blue-300 outline-none">
        <div class="flex justify-end gap-2">
          <button id="_batchCancel" class="px-3 py-1.5 text-xs border border-gray-300 rounded hover:bg-gray-50">取消</button>
          <button id="_batchConfirm" class="px-3 py-1.5 text-xs bg-blue-500 text-white rounded hover:bg-blue-600">确定</button>
        </div>
      </div>`;
    
    document.body.appendChild(overlay);
    const inp = overlay.querySelector('#_batchInp');
    overlay.querySelector('#_batchCancel').onclick = () => { overlay.remove(); resolve(null); };
    overlay.querySelector('#_batchConfirm').onclick = () => { overlay.remove(); resolve(inp.value); };
    inp.focus();
    inp.select();
    inp.addEventListener('keydown', (e) => { if (e.key === 'Enter') { overlay.remove(); resolve(inp.value); } });
  });
}

function showSelectDialog(title, options, currentValue) {
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'fixed inset-0 bg-black/30 z-[9999] flex items-center justify-center';
    overlay.onclick = (e) => { if (e.target === overlay) { overlay.remove(); resolve(null); } };
    
    const optionsHtml = options.map(o => 
      `<option value="${o}" ${o === currentValue ? 'selected' : ''}>${o}</option>`
    ).join('');
    
    overlay.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl p-5 w-80" onclick="event.stopPropagation()">
        <div class="text-sm font-semibold text-gray-700 mb-3">${title}</div>
        <select id="_batchSel" class="w-full border border-gray-300 rounded px-3 py-2 text-sm mb-4 focus:ring-2 focus:ring-blue-300 outline-none">
          ${optionsHtml}
        </select>
        <div class="flex justify-end gap-2">
          <button id="_batchCancel" class="px-3 py-1.5 text-xs border border-gray-300 rounded hover:bg-gray-50">取消</button>
          <button id="_batchConfirm" class="px-3 py-1.5 text-xs bg-blue-500 text-white rounded hover:bg-blue-600">确定</button>
        </div>
      </div>`;
    
    document.body.appendChild(overlay);
    const sel = overlay.querySelector('#_batchSel');
    overlay.querySelector('#_batchCancel').onclick = () => { overlay.remove(); resolve(null); };
    overlay.querySelector('#_batchConfirm').onclick = () => { overlay.remove(); resolve(sel.value); };
    sel.focus();
  });
}

async function editBatchMeta(projectId, batchName, field, currentValue, el) {
  const name = decodeURIComponent(batchName);
  let newValue;
  
  if (field === 'storage_dest') {
    newValue = await showSelectDialog(
      `批次「${name}」- 入库去向`,
      ['入仓库', '车间领用', '入仓库，车间领用', '现场安装'],
      currentValue || '入仓库，车间领用'
    );
  } else if (field === 'make_buy') {
    newValue = await showSelectDialog(
      `批次「${name}」- 制购类别`,
      ['采购', '自制', '外协', '利旧'],
      currentValue || '采购'
    );
  } else {
    newValue = await showInputDialog(`批次「${name}」- 申请理由`, currentValue);
  }
  
  if (newValue === null || newValue === currentValue) return;
  
  const body = { batch_name: name };
  body[field] = newValue.trim();
  const result = await projectApi('POST', `/${projectId}/batch-update-meta/`, body);
  if (result.error) {
    setStatus('error', result.error);
  } else {
    setStatus('success', `${field === 'storage_dest' ? '入库去向' : field === 'make_buy' ? '制购类别' : '申请理由'} 已更新`);
    // Update the clicked span directly
    if (el) {
      const emojiMap = {storage_dest:'📥', make_buy:'🏭', reason:'📝'};
      el.textContent = (emojiMap[field] || '') + ' ' + newValue;
    }
  }
}

async function deleteBatch(projectId, batchName) {
  const name = decodeURIComponent(batchName);
  if (!confirm(`确认删除批次「${name}」？将删除该批次所有条目。`)) return;
  const result = await projectApi('POST', `/${projectId}/delete-batch/`, { batch_name: name });
  if (result.ok) {
    setStatus('success', result.data.message || '批次已删除');
    showProjectDetail(projectId);
  } else {
    setStatus('error', result.data?.error || '删除失败');
  }
}

async function lockBatch(projectId, batchName) {
  const name = decodeURIComponent(batchName);
  const result = await projectApi('POST', `/${projectId}/batch-lock/`, { batch_name: name });
  if (result.ok) {
    setStatus('success', result.data.message || '批次已锁定');
    showProjectDetail(projectId);
  } else {
    setStatus('error', result.data?.error || '锁定失败');
  }
}

async function unlockBatch(projectId, batchName) {
  const name = decodeURIComponent(batchName);
  if (!confirm(`确认反审解锁批次「${name}」？解锁后可以编辑。`)) return;
  const result = await projectApi('POST', `/${projectId}/batch-unlock/`, { batch_name: name });
  if (result.ok) {
    setStatus('success', result.data.message || '批次已解锁');
    showProjectDetail(projectId);
  } else {
    setStatus('error', result.data?.error || '解锁失败');
  }
}

async function completeBatch(projectId, batchName) {
  const name = decodeURIComponent(batchName);
  if (!confirm(`确认完成批次「${name}」？将自动生成采购订单并锁定该批次。`)) return;
  const result = await projectApi('POST', `/${projectId}/batch-complete/`, { batch_name: name });
  if (result.ok) {
    const msg = result.data.message || '批次已完成';
    const orders = result.data.orders || [];
    if (orders.length) {
      const orderInfo = orders.map(o => o.reference).join(', ');
      setStatus('success', msg + ' — 采购单: ' + orderInfo);
    } else {
      setStatus('success', msg);
    }
    showProjectDetail(projectId);
  } else {
    setStatus('error', result.data?.error || '操作失败');
  }
}

// ── Expose to window ──
window.copyText = copyText;
window.showNewProjectDialog = showNewProjectDialog;
window.showProjectDetail = showProjectDetail;
window.switchProjectTab = switchProjectTab;
window.confirmDeleteProject = confirmDeleteProject;
window.deleteProject = deleteProject;
window.showAddItemDialog = showAddItemDialog;
window.showAddItemToProject = showAddItemToProject;
window.searchProductsForItem = searchProductsForItem;
window.selectProductForItem = selectProductForItem;
window.removeProjectItem = removeProjectItem;
window.searchUsersForMembership = searchUsersForMembership;
window.addMembership = addMembership;
window.removeMembership = removeMembership;
window.deleteBatch = deleteBatch;
window.lockBatch = lockBatch;
window.unlockBatch = unlockBatch;
window.completeBatch = completeBatch;
window.changeMemberRole = changeMemberRole;
window.toggleRolePermission = toggleRolePermission;
window.deleteRole = deleteRole;
window.showCreateRoleDialog = showCreateRoleDialog;
window.toggleAddMember = toggleAddMember;
window.showPermissionEditor = showPermissionEditor;
window.exportBatchCsv = exportBatchCsv;
window.exportBatchZip = exportBatchZip;
window.batchToCart = batchToCart;
window.generatePurchaseOrders = generatePurchaseOrders;
window.generateSalesOrder = generateSalesOrder;
window.submitCartAsProject = submitCartAsProject;
window.showModal = showModal;
window.closeModal = closeModal;
window.downloadProjectCsv = downloadProjectCsv;
window.saveAsTemplate = saveAsTemplate;
window.createFromTemplate = createFromTemplate;
window.loadProjectLogs = loadProjectLogs;
// (removed: loadMoreProjects was replaced by pagination)

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
      // Use dynamic API base path
      const basePath = window._inventreeApiBase || '/api';
      const resp = await fetch(basePath + '/part/?search=' + encodeURIComponent(q) + '&limit=15', { credentials: 'same-origin' });
      const data = await resp.json();
      const parts = data.results || data || [];
      if (!parts.length) { results.innerHTML = '<div class="text-xs text-gray-400 py-1">未找到零件</div>'; return; }
      results.innerHTML = parts.map(p =>
        '<div class="flex items-center justify-between py-1 px-2 text-xs border border-gray-200 rounded hover:bg-gray-50 cursor-pointer" data-part-id="' + p.pk + '" data-part-name="' + escHtml(p.name).replace(/"/g, '&quot;') + '" onclick="selectPartForItem(this.dataset.partId, this.dataset.partName)">' +
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

let _productSearchTimer = null;
async function searchProductsForItem() {
  clearTimeout(_productSearchTimer);
  const input = document.getElementById('ai-product-search');
  if (!input) return;
  const q = input.value.trim();
  const results = document.getElementById('ai-product-results');
  if (!results) return;
  if (q.length < 2) { results.innerHTML = ''; return; }

  _productSearchTimer = setTimeout(async () => {
    try {
      const basePath = window._inventreeApiBase || '/api';
      const resp = await fetch(basePath + '/part/?search=' + encodeURIComponent(q) + '&limit=15', { credentials: 'same-origin' });
      const data = await resp.json();
      const parts = data.results || data || [];
      if (!parts.length) { results.innerHTML = '<div class="text-xs text-gray-400 py-1">未找到产品</div>'; return; }
      results.innerHTML = parts.map(p =>
        '<div class="flex items-center justify-between py-1 px-2 text-xs border border-gray-200 rounded hover:bg-gray-50 cursor-pointer" data-product-id="' + p.pk + '" data-product-name="' + escHtml(p.name).replace(/"/g, '&quot;') + '" onclick="selectProductForItem(this.dataset.productId, this.dataset.productName)">' +
        '<span class="font-medium">' + escHtml(p.name) + '</span>' +
        '<span class="text-gray-400">' + escHtml(p.IPN || '') + '</span>' +
        '</div>'
      ).join('');
    } catch(e) { results.innerHTML = '<div class="text-xs text-red-400 py-1">搜索失败</div>'; }
  }, 300);
}

function selectProductForItem(productId, productName) {
  document.getElementById('ai-product-id').value = productId;
  document.getElementById('ai-product-search').value = productName;
  document.getElementById('ai-product-results').innerHTML = '';
  const selected = document.getElementById('ai-product-selected');
  if (selected) {
    selected.style.display = '';
    selected.textContent = '✅ 已选择: ' + productName;
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
    container.innerHTML = '<div class="empty-state p-4 text-center text-gray-400 text-sm">暂无关联订单</div>';
    return;
  }

  if (sos.length) {
    html += '<div class="text-xs text-gray-500 font-medium mb-2">💰 销售订单</div>';
    html += '<table class="w-full text-xs mb-4"><thead><tr class="border-b border-gray-200 text-gray-500">';
    html += '<th class="p-2 text-left">单号</th><th class="p-2 text-left">客户</th><th class="p-2 text-right">明细</th><th class="p-2 text-left">创建时间</th></tr></thead><tbody>';
    sos.forEach(so => {
      const link = so.url ? `<a href="${so.url}" target="_blank" class="text-blue-600 hover:text-blue-800 hover:underline">${escHtml(so.reference)} ↗</a>` : escHtml(so.reference);
      html += `<tr class="border-b border-gray-100"><td class="p-2 font-medium">${link}</td>`;
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
      const link = po.url ? `<a href="${po.url}" target="_blank" class="text-blue-600 hover:text-blue-800 hover:underline">${escHtml(po.reference)} ↗</a>` : escHtml(po.reference);
      html += `<tr class="border-b border-gray-100"><td class="p-2 font-medium">${link}</td>`;
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
    <div class="log-list space-y-1">
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

// ── Browser back/forward navigation for projects ──
window.addEventListener('popstate', function(e) {
  const path = window.location.pathname;
  const params = new URLSearchParams(window.location.search);
  const page = params.get('page');
  const projectId = params.get('project');
  
  // Handle new clean URL format: /parametric-bom/projects/<id>/
  const projectMatch = path.match(/^\/parametric-bom\/projects\/(\d+)\/?$/);
  if (projectMatch) {
    showProjectDetail(parseInt(projectMatch[1]));
    return;
  }
  
  // Handle old query param format (backward compatible)
  // Handle returning to project list
  if (path === '/parametric-bom/projects/' || path === '/parametric-bom/projects') {
    switchPage('projects');
    return;
  }
  if (!page || page === 'projects' || page === 'home') {
    switchPage('projects');
    return;
  }
  
  // Handle project detail from URL
  if (page === 'project-detail' && projectId && !isNaN(parseInt(projectId))) {
    showProjectDetail(parseInt(projectId));
  } else if (page) {
    switchPage(page);
  }
});

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}
