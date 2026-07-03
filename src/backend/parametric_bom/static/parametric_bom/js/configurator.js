// ===== API HELPER =====
async function apiCall(method, endpoint, body, opts = {}) {
  // Add cache busting for GET requests
  let url = `/api/parametric-bom/${endpoint}`;
  if (method === 'GET') {
    const separator = url.includes('?') ? '&' : '?';
    url += `${separator}_t=${Date.now()}`;
  }
  const options = {
    method,
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
    credentials: 'same-origin',
    ...opts,
  };
  if (body && method !== 'GET') options.body = JSON.stringify(body);
  setStatus('loading', '请求中...');
  try {
    const resp = await fetch(url, options);
    // Handle 204 No Content (e.g. DELETE) — no body to parse
    let data = {};
    if (resp.status !== 204) {
      try {
        data = await resp.json();
      } catch (parseErr) {
        // Non-JSON response, keep data as empty object
      }
    }
    if (!resp.ok) {
      const errMsg = data.error || data.detail || (typeof data === 'object' ? JSON.stringify(data).substring(0,120) : String(data));
      setStatus('error', `错误 ${resp.status}: ${errMsg}`);
      return {error: true, status: resp.status, data};
    }
    setStatus('success', '请求成功');
    return {error: false, data};
  } catch (err) {
    setStatus('error', `网络错误: ${err.message}`);
    return {error: true, data: {error: err.message}};
  }
}

function getCsrfToken() {
  const name = 'csrftoken';
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : '';
}

function setStatus(type, msg) {
  // 状态栏已移除
}

// ===== SIDEBAR NAVIGATION =====
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;
  const mainContent = document.getElementById('main-content');
  if (!mainContent) return;
  if (window.innerWidth <= 768) {
    sidebar.classList.toggle('mobile-open');
  } else {
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('sidebar-collapsed');
  }
}

function goBackFromProduct() {
  if (!confirmDiscardChanges()) return;
  // Check if we're in standalone/embedded mode
  const standalone = document.querySelector('.main-content.standalone');
  const embedded = document.querySelector('.main-content.embedded');
  if (standalone || embedded) {
    // Navigate back to the product list by reloading without the product param
    const url = new URL(window.location);
    url.searchParams.delete('product');
    window.location.href = url.toString();
  } else {
    switchPage('products');
  }
}

function switchPage(page) {
  // Warn before switching pages if there are unsaved changes
  if (isAnyDirty()) {
    const summary = getDirtySummary();
    if (!confirm(`有未保存的修改（${summary}），切换页面将丢弃这些修改。确定吗？`)) {
      return;
    }
  }
  // Hide all pages
  document.querySelectorAll('.page-panel').forEach(el => el.classList.remove('active'));
  // Show target
  const target = document.getElementById('page-' + page);
  if (target) target.classList.add('active');
  // Update sidebar
  document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
  const item = document.querySelector(`.sidebar-item[data-page="${page}"]`);
  if (item) item.classList.add('active');
  // Close mobile sidebar
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.classList.remove('mobile-open');
  // Scroll top
  window.scrollTo({top: 0, behavior: 'smooth'});
  
  // Auto-load data if a product is active and we navigated to a product-specific page
  if (configuratorPartId) {
    if (page === 'param-types') loadParamConfigs(configuratorPartId);
    else if (page === 'bom-formula') loadBomFormulaConfigs(configuratorPartId);
    else if (page === 'inheritance') loadInheritanceMappings(configuratorPartId);
    else if (page === 'attributes') loadAttributeFormulas(configuratorPartId);
    else if (page === 'configurator') onGlobalPartChange(configuratorPartId);
    else if (page === 'product-detail') { 
      if (configuratorPartId && !document.querySelector('#pd-product-name')?.textContent?.trim()?.length > 1) 
        loadProductDetail(configuratorPartId); 
      else if (!document.querySelector('#page-product-detail .pd-tab-content.active')) 
        switchProductTab('params'); 
    }
  }
}

function toggleGroup(header) {
  const body = header.nextElementSibling;
  if (body) body.style.display = body.style.display === 'none' ? 'block' : 'none';
  const arrow = header.querySelector('span:last-child');
  if (arrow) arrow.textContent = body.style.display === 'none' ? '▸' : '▾';
}

// ===== CONFIGURATOR STEP NAVIGATION =====
function goConfigStep(step) {
  currentStep = step;
  document.querySelectorAll('#page-configurator .step-panel').forEach(el => el.classList.remove('active'));
  document.getElementById(`cfg-step-${step}`).classList.add('active');
  for (let i = 1; i <= 3; i++) {
    const circle = document.getElementById(`cfg-step-circle-${i}`);
    const label = document.getElementById(`cfg-step-label-${i}`);
    const line = document.getElementById(`cfg-step-line-${i}`);
    if (i < step) {
      circle.className = 'step-circle completed';
      label.className = 'step-label completed';
      if (line) line.className = 'step-line completed';
    } else if (i === step) {
      circle.className = 'step-circle active';
      label.className = 'step-label active';
      if (line) line.className = 'step-line';
    } else {
      circle.className = 'step-circle pending';
      label.className = 'step-label pending';
      if (line) line.className = 'step-line';
    }
  }
  if (step === 3) buildParamSummary();
  window.scrollTo({top: 0, behavior: 'smooth'});
}

// ===== PART LOADING =====
async function loadParts() {
  try {
    const resp = await fetch('/api/part/?limit=5000&ordering=-creation_date', {credentials: 'same-origin'});
    if (resp.ok) {
      const data = await resp.json();
      parts = Array.isArray(data) ? data : (data.results || []);
    } else {
      parts = [];
    }
  } catch(e) {
    parts = [];
  }
  // Populate part selects
  const selects = ['cfg-part-select', 'pm-part-select', 'tpl-sync-part', 'bom-part-select', 'ap-part'];
  const templateSelects = ['ap-template'];
  
  selects.forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">-- 请选择 --</option>';
    parts.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.pk;
      opt.textContent = `${p.name || p.full_name || 'Unnamed'} (ID:${p.pk})`;
      sel.appendChild(opt);
    });
    if (currentVal) sel.value = currentVal;
  });
  
  // Load parameter templates
  try {
    const tmplResp = await fetch('/api/parameter/template/', {
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()}, credentials: 'same-origin'
    });
    if (tmplResp.ok) {
      const tmplData = await tmplResp.json();
      templates = Array.isArray(tmplData) ? tmplData : (tmplData.results || []);
    }
  } catch(e) {}
  
  templateSelects.forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">-- 请选择 --</option>';
    templates.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.pk;
      opt.textContent = `${t.name}${t.units ? ' ('+t.units+')' : ''}`;
      sel.appendChild(opt);
    });
    if (currentVal) sel.value = currentVal;
  });
  // Render product management grid
  renderProductGrid();
}

// ===== PRODUCT MANAGEMENT =====
let _productPage = 1;
let _productPageSize = 24;
let _filteredParts = [];
let _paramFilter = 'all';

function setParamFilter(val) {
  _paramFilter = val;
  document.querySelectorAll('.param-filter-pill').forEach(el => {
    el.classList.toggle('active', el.dataset.filter === val);
  });
  _productPage = 1;
  renderProductGrid();
}

async function renderProductGrid() {
  const grid = document.getElementById('product-grid');
  if (!grid) return;
  
  if (!parts || parts.length === 0) {
    grid.innerHTML = '<div class="empty-state"><div class="icon">📦</div><p>暂无产品</p></div>';
    document.getElementById('product-count-badge').textContent = '';
    document.getElementById('product-pagination-bar').style.display = 'none';
    return;
  }
  
  // Populate category filter on first load
  const catFilter = document.getElementById('product-category-filter');
  if (catFilter && catFilter.options.length <= 1) {
    const cats = {};
    parts.forEach(p => { if (p.category_detail) cats[p.category_detail.name] = p.category_detail.pk; });
    const sorted = Object.entries(cats).sort((a,b) => a[0].localeCompare(b[0]));
    sorted.forEach(([name, pk]) => {
      const opt = document.createElement('option');
      opt.value = pk;
      opt.textContent = name;
      catFilter.appendChild(opt);
    });
  }
  
  // Fetch parametric config data
  const [paramRes] = await Promise.all([
    apiCall('GET', 'part-config/'),
  ]);
  
  const configMap = {};
  const paramCfgs = paramRes.error ? [] : (paramRes.data.results || paramRes.data || []);
  paramCfgs.forEach(c => {
    if (!configMap[c.part]) configMap[c.part] = { paramCount: 0 };
    configMap[c.part].paramCount = (configMap[c.part].paramCount || 0) + 1;
  });
  
  // Apply search & filter
  const searchQ = (document.getElementById('product-search-input').value || '').toLowerCase().trim();
  const catPk = document.getElementById('product-category-filter').value;
  
  _filteredParts = parts.filter(p => {
    if (catPk && p.category != parseInt(catPk)) return false;
    if (searchQ) {
      const name = (p.name || p.full_name || '').toLowerCase();
      const ipn = (p.IPN || p.ipn || '').toLowerCase();
      if (!name.includes(searchQ) && !ipn.includes(searchQ)) return false;
    }
    return true;
  });
  
  // Apply parametric filter
  if (_paramFilter !== 'all') {
    _filteredParts = _filteredParts.filter(p => {
      const cfg = configMap[p.pk];
      const isPara = cfg && cfg.paramCount > 0;
      return _paramFilter === 'parametric' ? isPara : !isPara;
    });
  }
  
  let withConfigCount = 0;
  _filteredParts.forEach(p => {
    const cfg = configMap[p.pk];
    if (cfg && cfg.paramCount > 0) withConfigCount++;
  });
  
  // Update counts
  const totalParts = parts.length;
  const filteredCount = _filteredParts.length;
  document.getElementById('product-count-badge').textContent = `共 ${totalParts} 个产品（${withConfigCount} 个已参数化）`;
  document.getElementById('product-filter-count').textContent = searchQ || catPk ? `筛选: ${filteredCount} / ${totalParts}` : '';
  
  // Paginate
  const totalPages = Math.max(1, Math.ceil(_filteredParts.length / _productPageSize));
  if (_productPage > totalPages) _productPage = totalPages;
  const start = (_productPage - 1) * _productPageSize;
  const end = Math.min(start + _productPageSize, _filteredParts.length);
  const pageItems = _filteredParts.slice(start, end);
  
  // Show/hide pagination bar
  const pagBar = document.getElementById('product-pagination-bar');
  if (_filteredParts.length > _productPageSize) {
    pagBar.style.display = 'flex';
    document.getElementById('product-page-info').textContent = `第 ${start+1}-${end} / 共 ${_filteredParts.length} 个`;
    // Page numbers
    let pageNums = '';
    const maxVisible = 5;
    let pStart = Math.max(1, _productPage - Math.floor(maxVisible/2));
    let pEnd = Math.min(totalPages, pStart + maxVisible - 1);
    if (pEnd - pStart < maxVisible - 1) pStart = Math.max(1, pEnd - maxVisible + 1);
    for (let i = pStart; i <= pEnd; i++) {
      pageNums += i === _productPage
        ? `<span class="text-xs font-bold text-blue-600 mx-1">${i}</span>`
        : `<span class="text-xs text-gray-500 mx-1 cursor-pointer hover:text-blue-500" onclick="goProductPage(${i})">${i}</span>`;
    }
    document.getElementById('product-page-nums').innerHTML = pageNums;
    document.getElementById('pg-first').disabled = _productPage <= 1;
    document.getElementById('pg-prev').disabled = _productPage <= 1;
    document.getElementById('pg-next').disabled = _productPage >= totalPages;
    document.getElementById('pg-last').disabled = _productPage >= totalPages;
  } else {
    pagBar.style.display = 'none';
  }
  
  // Render grid
  if (pageItems.length === 0) {
    grid.innerHTML = '<div class="empty-state"><div class="icon">🔍</div><p>没有匹配的产品</p></div>';
    return;
  }
  
  let html = '<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">';
  pageItems.forEach(p => {
    const name = p.name || p.full_name || 'Unnamed';
    const cfg = configMap[p.pk] || { paramCount: 0 };
    const isParametric = cfg.paramCount > 0;
    const ipn = p.IPN || p.ipn || '';
    const description = p.description || '';
    
    html += `<div class="product-card ${isParametric ? 'is-parametric' : ''}" onclick="window.open('/parametric-bom/product/${p.pk}/', '_blank')">
      <div class="flex items-start gap-3">
        <div class="product-icon ${isParametric ? 'parametric-icon' : ''}">
          <span class="icon-main">${isParametric ? '🔧' : '⚙️'}</span>
          ${isParametric ? '<span class="icon-lightning">⚡</span>' : ''}
        </div>
        <div class="flex-1 min-w-0">
          <div class="product-name">${name}</div>
          ${ipn ? `<div class="product-ipn">${ipn}</div>` : ''}
          ${description ? `<div class="product-desc">${description.substring(0, 60)}${description.length > 60 ? '...' : ''}</div>` : ''}
        </div>
        ${isParametric ? '<div class="parametric-badge">参数化</div>' : ''}
      </div>
      <div class="product-meta">
        <span class="product-stat">📐 ${cfg.paramCount} 参数</span>
        <span class="product-type-badge ${p.assembly ? 'is-assembly' : 'is-part'}">${p.assembly ? '部装' : '零件'}</span>
        <span class="product-date">${p.creation_date || ''}</span>
      </div>
    </div>`;
  });
  html += '</div>';
  grid.innerHTML = html;
}

function filterProductGrid() {
  _productPage = 1;
  renderProductGrid();
}

function goProductPage(dir) {
  if (typeof dir === 'number') { _productPage = dir; }
  else if (dir === 'first') { _productPage = 1; }
  else if (dir === 'prev') { _productPage = Math.max(1, _productPage - 1); }
  else if (dir === 'next') { _productPage = Math.min(Math.ceil(_filteredParts.length / _productPageSize), _productPage + 1); }
  else if (dir === 'last') { _productPage = Math.ceil(_filteredParts.length / _productPageSize); }
  renderProductGrid();
}

function changeProductPageSize(size) {
  _productPageSize = parseInt(size);
  _productPage = 1;
  renderProductGrid();
}

// Search on Enter key
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('product-search-input');
  if (searchInput) {
    searchInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') filterProductGrid();
    });
  }
});

function selectActiveProduct(partId, partName) {
  if (configuratorPartId === partId) {
    // Already selected, just open detail page
    loadProductDetail(partId);
    switchPage('product-detail');
    return;
  }
  
  configuratorPartId = partId;
  
  // Update part selectors on all pages
  const selectors = ['cfg-part-select', 'pm-part-select', 'bom-part-select'];
  selectors.forEach(id => {
    const sel = document.getElementById(id);
    if (sel) { sel.value = partId; }
  });
  
  // Open product detail page
  renderProductGrid();
  loadProductDetail(partId);
  switchPage('product-detail');
  setStatus('success', `已打开: ${partName}`);
}

// ── Part Detail navigation ──
function openPartDetail(partId) {
  if (!partId) return;
  // Open in InvenTree standard part detail (new tab)
  window.open('/part/' + partId + '/', '_blank');
}

// ===== PRODUCT DETAIL PAGE =====
function switchProductTab(tab) {
  // Warn before switching if there are unsaved changes
  if (isAnyDirty()) {
    const summary = getDirtySummary();
    if (!confirm(`有未保存的修改（${summary}），切换标签将丢弃这些修改。确定吗？`)) {
      return; // Cancel the tab switch
    }
  }
  // Update tab buttons
  document.querySelectorAll('.pd-tab').forEach(el => el.classList.remove('active'));
  document.querySelector(`.pd-tab[data-tab="${tab}"]`)?.classList.add('active');
  // Update content
  document.querySelectorAll('.pd-tab-content').forEach(el => el.classList.remove('active'));
  document.getElementById(`pd-tab-${tab}`)?.classList.add('active');
  // Load data for this tab
  if (!configuratorPartId) return;
  if (tab === 'params') loadPdParams();
  else if (tab === 'bom') loadPdBOMM();
  else if (tab === 'configurator') loadPdConfigurator();
  else if (tab === 'variables') loadPdVariables();
}

async function loadProductDetail(partId) {
  if (!partId) return;
  const part = parts.find(p => p.pk == partId);
  if (part) {
    document.getElementById('pd-product-name').textContent = part.name || part.full_name || '—';
    document.getElementById('pd-product-ipn').textContent = part.IPN || part.ipn || '';
    document.getElementById('pd-product-desc').textContent = part.description || '';
  }
  // Load first tab
  switchProductTab('params');
}

// ── Dirty tracking for Save/Cancel ──
let __dirtyUpdates = {}; // {configId: {field: newValue, ...}}
let __hasDirty = false;
let __dirtyAreas = new Set(); // tracks which tabs have unsaved changes

function markDirty(cfgId, updates) {
  if (!__dirtyUpdates[cfgId]) __dirtyUpdates[cfgId] = {};
  Object.assign(__dirtyUpdates[cfgId], updates);
  __hasDirty = true;
  __dirtyAreas.add('params');
  showDirtyButtons();
}

function clearDirty() {
  __dirtyUpdates = {};
  __hasDirty = false;
  __dirtyAreas.clear();
  showDirtyButtons();
}

function markAreaDirty(area) {
  __dirtyAreas.add(area);
}

function clearAreaDirty(area) {
  __dirtyAreas.delete(area);
  if (__dirtyAreas.size === 0) __hasDirty = false;
}

function isAnyDirty() {
  return __dirtyAreas.size > 0 || __hasDirty;
}

function getDirtySummary() {
  const areas = Array.from(__dirtyAreas);
  const labels = {params:'参数配置', bom:'BOM列表', variables:'变量', configurator:'配置器'};
  return areas.map(a => labels[a] || a).join('、');
}

function showDirtyButtons() {
  // Save button is always visible, no show/hide needed
}

// Prompt user if there are unsaved changes before navigating away
function confirmDiscardChanges(message) {
  if (!isAnyDirty()) return true;
  const summary = getDirtySummary();
  return confirm(message || `有未保存的修改（${summary}），确定要离开吗？`);
}

async function saveAllParams() {
  const entries = Object.entries(__dirtyUpdates);
  if (!entries.length) {
    setStatus('info', '💡 当前没有需要保存的修改');
    return;
  }

  const btn = document.getElementById('btn-save-params');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ 保存中...'; }

  setStatus('loading', `正在保存 ${entries.length} 项修改...`);
  let success = 0, fail = 0;

  for (const [cfgId, updates] of entries) {
    const res = await apiCall('PATCH', `part-config/${cfgId}/`, updates);
    if (!res.error) success++;
    else fail++;
  }

  if (btn) { btn.disabled = false; btn.textContent = '💾 保存修改'; }

  if (fail === 0) {
    setStatus('success', `✅ 全部 ${success} 项修改已保存`);
  } else {
    setStatus('warning', `已保存 ${success} 项，${fail} 项失败`);
  }

  clearDirty();
  // Wait a moment then reload data
  await new Promise(r => setTimeout(r, 100));
  await loadPdParams();
}

function cancelAllParams() {
  if (__hasDirty && !confirm('有未保存的修改，确定要取消吗？')) return;
  clearDirty();
  loadPdParams();
}

async function loadPdParams() {
  const pid = configuratorPartId;
  if (!pid) return;
  const container = document.getElementById('pd-params-canvas');
  const countBadge = document.getElementById('pd-param-count');
  container.innerHTML = '<div class="flex items-center justify-center py-3"><span class="spinner mr-2"></span><span class="text-sm text-gray-400">加载中...</span></div>';

  const res = await apiCall('GET', `part-config/?part=${parseInt(pid)}`);
  if (res.error) { container.innerHTML = '<div class="text-red-500 text-sm p-3">❌ 加载失败</div>'; return; }
  const configs = res.data.results || (Array.isArray(res.data) ? res.data : []);
  
  window.__paramConfigs = configs;
  window.__currentPartId = pid;
  
  const sorted = (configs || []).sort((a,b) => (a.display_order||0) - (b.display_order||0));
  
  if (!sorted.length) {
    if (countBadge) countBadge.textContent = '0 个参数';
    container.innerHTML = `<div class="pc-empty-state">
      <div class="pc-empty-icon">🎨</div>
      <div class="pc-empty-title">画布为空</div>
      <div class="pc-empty-desc">从左栏组件库单击或拖拽添加参数</div>
    </div>`;
    renderPdTemplateList();
    return;
  }
  
  if (countBadge) countBadge.textContent = `${sorted.length} 个参数`;
  
  let html = '';
  sorted.forEach((cfg, idx) => {
    html += renderParamCard(cfg, idx);
  });
  container.innerHTML = html;
  
  // No template list needed — types are static
}

// Template list rendering is replaced by type buttons
function renderPdTemplateList() {}

function renderParamCard(cfg, idx) {
  const type = cfg.parameter_type || 'number';
  const safeName = (cfg.name||'参数').replace(/'/g, "\\'");
  const cfgId = cfg.id;
  const typeLabels = {number:'数值', option:'选项', multi_option:'多选', boolean:'布尔', text:'文本', long_text:'长文本'};
  const typeLabel = typeLabels[type] || type;
  const defVal = cfg.default_value != null ? cfg.default_value : '';
  
  const typeIconMap = {number:'🔢', option:'🔘', multi_option:'☑️', boolean:'☑️', text:'📝', long_text:'📄'};
  const icon = typeIconMap[type] || '🔢';
  
  // ── Input control (row 1: default value) ──
  let inputHtml = '';
  
  if (type === 'number') {
    const min = cfg.min_value != null ? parseFloat(cfg.min_value) : 0;
    const max = cfg.max_value != null ? parseFloat(cfg.max_value) : 10000;
    const step = cfg.step_value != null ? parseFloat(cfg.step_value) : (max - min > 100 ? 1 : 0.1);
    const val = defVal || min;
    inputHtml = `<div class="pc-value">
      <div class="pc-slider-row">
        <input type="range" min="${min}" max="${max}" step="${step}" value="${val}"
          oninput="document.getElementById('pc-slider-val-${cfgId}').textContent=this.value; markDirty(${cfgId},{default_value:String(this.value)})"
          onchange="markDirty(${cfgId},{default_value:String(this.value)})">
        <span class="pc-slider-val" id="pc-slider-val-${cfgId}">${val}</span>
      </div>
      <div class="pc-range-inline">
        <span>范围</span>
        <input type="number" value="${min}" placeholder="最小值"
          onchange="markDirty(${cfgId},{min_value:this.value}); showDirtyButtons()">
        <span>~</span>
        <input type="number" value="${max}" placeholder="最大值"
          onchange="markDirty(${cfgId},{max_value:this.value}); showDirtyButtons()">
        <span class="ml-1">步长</span>
        <input type="number" value="${cfg.step_value != null ? cfg.step_value : ''}" step="0.01" placeholder="自动"
          style="width:60px;padding:0.125rem 0.25rem;font-size:0.65rem"
          onchange="var s=parseFloat(this.value);if(s>0){var pc=this.closest('.pc-value');var slider=pc?pc.querySelector('input[type=range]'):null;var cur=slider?parseFloat(slider.value):0;var m=slider?parseFloat(slider.min):0;var snap=m+Math.round((cur-m)/s)*s;if(slider){slider.step=s;slider.value=snap;}if(pc){var valSpan=pc.querySelector('.pc-slider-val');if(valSpan)valSpan.textContent=snap;}markDirty(${cfgId},{step_value:s,default_value:String(snap)});}else{markDirty(${cfgId},{step_value:this.value||null});}showDirtyButtons()">
      </div>
    </div>`;
    
  } else if (type === 'option') {
    const opts = cfg.options ? (Array.isArray(cfg.options) ? cfg.options : []) : [];
    inputHtml = `<div class="pc-value">
      <select onchange="markDirty(${cfgId},{default_value:this.value}); showDirtyButtons()">
        <option value="">-- 请选择 --</option>
        ${opts.map(o => `<option value="${o}"${o === defVal ? ' selected' : ''}>${o}</option>`).join('')}
      </select>
      <div class="pc-opts-editor" id="pc-opts-${cfgId}">
        ${opts.map(o => `<span class="pc-opt-tag">${o}<span class="pc-opt-del" onclick="removeOption(${cfgId},'${o.replace(/'/g,"\\'")}')">✕</span></span>`).join('')}
        <span class="pc-opt-add-inline" onclick="startAddOption(${cfgId})">➕ 选项</span>
      </div>
    </div>`;
    
  } else if (type === 'multi_option') {
    const opts = cfg.options ? (Array.isArray(cfg.options) ? cfg.options : []) : [];
    const selected = defVal ? defVal.split(',') : [];
    inputHtml = `<div class="pc-value">
      <div class="pc-opts-editor" style="margin-bottom:0.25rem">
        ${opts.map(o => `<label class="flex items-center gap-1 text-xs cursor-pointer" style="padding:2px 6px;border:1px solid #e2e8f0;border-radius:4px;background:${selected.includes(o)?'#dbeafe':'#fff'}">
          <input type="checkbox" value="${o}" ${selected.includes(o)?'checked':''}
            onchange="updateMultiDefault(${cfgId}, '${cfgId}')" data-multi-${cfgId}>
          <span>${o}</span>
        </label>`).join('')}
      </div>
      <div class="pc-opts-editor">
        ${opts.map(o => `<span class="pc-opt-tag">${o}<span class="pc-opt-del" onclick="removeOption(${cfgId},'${o.replace(/'/g,"\\'")}')">✕</span></span>`).join('')}
        <span class="pc-opt-add-inline" onclick="startAddOption(${cfgId})">➕ 选项</span>
      </div>
    </div>`;
    
  } else if (type === 'boolean') {
    const isTrue = defVal === 'true' || defVal === true || defVal === '1';
    inputHtml = `<div class="pc-value">
      <div class="flex items-center gap-2">
        <div class="toggle-switch ${isTrue ? 'on' : ''}"
          onclick="toggleBooleanParam(${cfgId}, this)">
          <div class="toggle-knob"></div>
        </div>
        <span class="text-xs bool-label" style="color:#64748b">${isTrue ? '是' : '否'}</span>
      </div>
    </div>`;
    
  } else if (type === 'long_text') {
    inputHtml = `<div class="pc-value">
      <textarea class="input-field" rows="2" placeholder="输入${safeName}"
        onchange="markDirty(${cfgId},{default_value:this.value}); showDirtyButtons()"
        style="font-size:0.7rem;padding:0.3125rem 0.5rem;min-height:2.5rem">${defVal}</textarea>
    </div>`;
    
  } else {
    // text
    inputHtml = `<div class="pc-value">
      <input type="text" value="${defVal}" placeholder="输入${safeName}"
        onchange="markDirty(${cfgId},{default_value:this.value}); showDirtyButtons()">
    </div>`;
  }
  
  // ── Description (uses ui_hint field) ──
  const desc = cfg.ui_hint || '';
  const descHtml = desc
    ? `<div class="pc-desc-editor" onclick="startEditDesc(${cfgId}, this)">
        📝 <span class="pc-desc-text">${desc}</span>
       </div>`
    : `<div class="pc-desc-editor" onclick="startEditDesc(${cfgId}, this)" style="color:#cbd5e1">
        ➕ 添加描述
       </div>`;
  
  // ── Footer toggles ──
  const isDriving = cfg.is_driving;
  const isComputed = cfg.is_computed;
  
  return `<div class="param-card type-${type}"
    data-config-id="${cfgId}" data-display-order="${cfg.display_order||0}"
    ondragover="onCardDragOver(event)"
    ondrop="onCardDrop(event, ${cfgId})"
    ondragend="onCardDragEnd(event)">
    <div class="param-card-header">
      <span class="pc-drag-handle" draggable="true" ondragstart="onCardDragStart(event, ${cfgId})">⠿</span>
      <span class="pc-type-icon type-${type}">${icon}</span>
      <span class="pc-name" id="pc-name-${cfgId}" onclick="startRenameParam(${cfgId})" title="单击重命名">${safeName}</span>
      <span class="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-medium">${typeLabel}</span>
    </div>
    <div class="param-card-body">
      <div class="pc-row">
        <span class="pc-label">默认值</span>
        ${inputHtml}
      </div>
      ${descHtml}
    </div>
    <div class="param-card-footer">
      <div class="flex items-center gap-1.5">
        <div class="toggle-switch ${isDriving ? 'on' : ''}" onclick="this.classList.toggle('on'); markDirty(${cfgId},{is_driving:this.classList.contains('on')}); showDirtyButtons()"><div class="toggle-knob"></div></div>
        <span class="pc-toggle-label">驱动</span>
      </div>
      <div class="flex items-center gap-1.5">
        <div class="toggle-switch ${isComputed ? 'on' : ''}" onclick="this.classList.toggle('on'); markDirty(${cfgId},{is_computed:this.classList.contains('on')}); showDirtyButtons()"><div class="toggle-knob"></div></div>
        <span class="pc-toggle-label">计算</span>
      </div>
      <div style="flex:1"></div>
      <button class="pc-action-btn danger" onclick="deleteParamConfig(${cfgId}, '${safeName}')" title="删除">🗑️ 删除</button>
    </div>
  </div>`;
}

// ── Boolean toggle helper ──
function toggleBooleanParam(cfgId, el) {
  try {
    el.classList.toggle('on');
    const isOn = el.classList.contains('on');
    const label = el.parentElement.querySelector('.bool-label');
    if (label) label.textContent = isOn ? '是' : '否';
    markDirty(cfgId, {default_value: isOn ? 'true' : 'false'});
    showDirtyButtons();
  } catch(e) {
    console.error('toggleBooleanParam error:', e);
  }
}

// ── Options editor helpers ──
function startAddOption(cfgId) {
  console.log('startAddOption called', cfgId);
  const editor = document.getElementById(`pc-opts-${cfgId}`);
  if (!editor) { console.warn('startAddOption: editor not found', cfgId); return; }

  // If there's already an input, auto-submit its value before creating a new one
  const existingInput = editor.querySelector('.pc-opt-input');
  if (existingInput) {
    const val = existingInput.value.trim();
    console.log('startAddOption: existing input value:', val);
    if (val) {
      existingInput.onblur = null;
      addOption(cfgId, val);
    }
    existingInput.remove();
  }

  console.log('startAddOption: creating new input');
  const input = document.createElement('input');
  input.className = 'pc-opt-input';
  input.placeholder = '输入...';
  input.onkeydown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const val = input.value.trim();
      input.onblur = null;
      if (val) addOption(cfgId, val);
      if (input.parentNode) input.remove();
    }
    if (e.key === 'Escape') input.remove();
  };
  // No onblur auto-remove — let next startAddOption call handle cleanup
  const addBtn = editor.querySelector('.pc-opt-add-inline');
  if (addBtn) editor.insertBefore(input, addBtn);
  input.focus();
}

async function addOption(cfgId, newOption) {
  try {
    console.log('addOption called', {cfgId, newOption});
    const cfg = window.__paramConfigs.find(c => c.id === cfgId);
    if (!cfg) { console.warn('addOption: cfg not found', cfgId); return; }
    console.log('addOption: cfg found', {id: cfg.id, currentOptions: cfg.options});
    const opts = cfg.options ? (Array.isArray(cfg.options) ? [...cfg.options] : []) : [];
    if (opts.includes(newOption)) { setStatus('error', '选项已存在'); return; }
    opts.push(newOption);
    markDirty(cfgId, {options: opts});
    cfg.options = opts;
    showDirtyButtons();
    const sel = document.querySelector(`#pd-params-canvas .param-card[data-config-id="${cfgId}"] select`);
    console.log('addOption: select found:', !!sel);
    if (sel) {
      const opt = document.createElement('option');
      opt.value = newOption;
      opt.textContent = newOption;
      sel.appendChild(opt);
      sel.value = '';
    }
    const editor = document.getElementById(`pc-opts-${cfgId}`);
    console.log('addOption: editor found:', !!editor);
    if (editor) {
      const addBtn = editor.querySelector('.pc-opt-add-inline');
      console.log('addOption: addBtn found:', !!addBtn);
      const tag = document.createElement('span');
      tag.className = 'pc-opt-tag';
      tag.innerHTML = `${newOption}<span class="pc-opt-del" onclick="removeOption(${cfgId},'${newOption.replace(/'/g,"\\'")}')">✕</span>`;
      editor.insertBefore(tag, addBtn);
      console.log('addOption: tag inserted successfully');
    }
  } catch(e) {
    console.error('addOption error:', e, {cfgId, newOption});
  }
}

function removeOption(cfgId, opt) {
  const cfg = window.__paramConfigs.find(c => c.id === cfgId);
  if (!cfg) return;
  const opts = cfg.options ? (Array.isArray(cfg.options) ? [...cfg.options] : []) : [];
  const idx = opts.indexOf(opt);
  if (idx === -1) return;
  opts.splice(idx, 1);
  markDirty(cfgId, {options: opts});
  cfg.options = opts;
  showDirtyButtons();
  // ── Direct DOM removal ──
  // 1) Remove option from select
  const sel = document.querySelector(`#pd-params-canvas .param-card[data-config-id="${cfgId}"] select`);
  if (sel) {
    const optEl = Array.from(sel.options).find(o => o.value === opt);
    if (optEl) optEl.remove();
  }
  // 2) Remove option tag from editor
  const editor = document.getElementById(`pc-opts-${cfgId}`);
  if (editor) {
    const tags = editor.querySelectorAll('.pc-opt-tag');
    for (const tag of tags) {
      if (tag.textContent.replace('✕','').trim() === opt) {
        tag.remove();
        break;
      }
    }
  }
}

function updateMultiDefault(cfgId, mark) {
  const checkboxes = document.querySelectorAll(`input[data-multi-${cfgId}]:checked`);
  const vals = Array.from(checkboxes).map(cb => cb.value).join(',');
  markDirty(cfgId, {default_value: vals});
  showDirtyButtons();
}

// ── Description editor ──
function startEditDesc(cfgId, el) {
  const textEl = el.querySelector('.pc-desc-text');
  const currentText = textEl ? textEl.textContent : '';
  el.innerHTML = `<span class="pc-label" style="min-width:0;margin-right:0.25rem">📝</span>
    <input class="pc-desc-input" type="text" value="${currentText}" placeholder="添加描述..."
      onblur="finishEditDesc(${cfgId}, this)"
      onkeydown="if(event.key==='Enter')this.blur();if(event.key==='Escape'){this.value='${currentText.replace(/'/g,"\\'")}';this.blur()}">`;
  const input = el.querySelector('input');
  if (input) input.focus();
}

function finishEditDesc(cfgId, input) {
  const val = input.value.trim();
  const parent = input.parentElement;
  if (val) {
    markDirty(cfgId, {ui_hint: val});
    showDirtyButtons();
    parent.innerHTML = `📝 <span class="pc-desc-text">${val}</span>`;
    parent.onclick = () => startEditDesc(cfgId, parent);
    parent.style.color = '#94a3b8';
  } else {
    parent.innerHTML = `➕ 添加描述`;
    parent.onclick = () => startEditDesc(cfgId, parent);
    parent.style.color = '#cbd5e1';
  }
}

// ── Append new param card without full reload ──
function appendParamCard(config) {
  if (!window.__paramConfigs) window.__paramConfigs = [];
  window.__paramConfigs.push(config);
  const sorted = window.__paramConfigs.sort((a,b)=>(a.display_order||0)-(b.display_order||0));
  const canvas = document.getElementById('pd-params-canvas');
  const countBadge = document.getElementById('pd-param-count');
  canvas.innerHTML = sorted.map((c,i)=>renderParamCard(c,i)).join('');
  if (countBadge) countBadge.textContent = `${sorted.length} 个参数`;
  // Scroll to bottom to show new card
  canvas.scrollTop = canvas.scrollHeight;
}

async function loadPdBOMM() {
  const pid = configuratorPartId;
  if (!pid) return;
  const container = document.getElementById('pd-bom-list');
  const countBadge = document.getElementById('bom-count-badge');
  container.innerHTML = '<div class="flex items-center justify-center py-6"><span class="spinner mr-2"></span><span class="text-sm text-gray-400">加载中...</span></div>';
  
  const [bomRes, pcfgRes, vmRes] = await Promise.all([
    fetch('/api/bom/?part=' + pid + '&sub_part_detail=True&part_detail=True', {headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()}, credentials: 'same-origin'}),
    apiCall('GET', 'bom-item-config/?bom_item__part=' + pid),
    apiCall('GET', 'variant-mappings/'),
  ]);
  
  const bomItems = bomRes.ok ? (await bomRes.json()) : [];
  const items = Array.isArray(bomItems) ? bomItems : (bomItems.results || []);
  const pcfgs = pcfgRes.error ? [] : (Array.isArray(pcfgRes.data) ? pcfgRes.data : (pcfgRes.data.results || []));
  const pcfgMap = {};
  pcfgs.forEach(function(c) { pcfgMap[c.bom_item] = c; });
  
  // Build variant mapping lookup by parametric_bom_item
  var vmData = vmRes.error ? [] : (Array.isArray(vmRes.data) ? vmRes.data : (vmRes.data.results || []));
  var vmByPbi = {};
  vmData.forEach(function(v) { vmByPbi[v.parametric_bom_item] = v; });
  
  // Store globally for search filtering
  window.__bomItems = items;
  window.__bomPcfgMap = pcfgMap;
  window.__bomVmByPbi = vmByPbi;
  
  // Clear search input on fresh load
  const searchInput = document.getElementById('bom-search-input');
  if (searchInput) searchInput.value = '';
  
  renderBOMTable(items, pcfgMap, vmByPbi);
  if (countBadge) countBadge.textContent = '共 ' + items.length + ' 项';
}

function filterBOMList() {
  const q = (document.getElementById('bom-search-input').value || '').toLowerCase().trim();
  const items = window.__bomItems || [];
  const pcfgMap = window.__bomPcfgMap || {};
  const vmByPbi = window.__bomVmByPbi || {};
  const countBadge = document.getElementById('bom-count-badge');
  const filterCount = document.getElementById('bom-filter-count');
  
  let filtered;
  if (!q) {
    filtered = items;
    if (filterCount) filterCount.textContent = '';
  } else {
    filtered = items.filter(function(item) {
      const subPartDetail = item.sub_part_detail || {};
      const name = (subPartDetail.name || '').toLowerCase();
      const ipn = (subPartDetail.ipn || '').toLowerCase();
      // Also search in variant mapping template names
      const cfg = pcfgMap[item.pk];
      var vm = null;
      if (cfg && cfg.enable_variant) vm = vmByPbi[cfg.id];
      const tplName = vm ? (vm.template_part_name || '').toLowerCase() : '';
      const tplIpn = vm ? (vm.template_part_ipn || '').toLowerCase() : '';
      return name.indexOf(q) !== -1 || ipn.indexOf(q) !== -1 || tplName.indexOf(q) !== -1 || tplIpn.indexOf(q) !== -1;
    });
    if (filterCount) filterCount.textContent = filtered.length + '/' + items.length;
  }
  
  renderBOMTable(filtered, pcfgMap, vmByPbi);
  if (countBadge) countBadge.textContent = '共 ' + items.length + ' 项' + (q ? '（显示 ' + filtered.length + ' 项）' : '');
}

function renderBOMTable(items, pcfgMap, vmByPbi) {
  const container = document.getElementById('pd-bom-list');
  if (!items.length) {
    const q = (document.getElementById('bom-search-input').value || '').trim();
    container.innerHTML = q
      ? '<div class="bom-empty-state"><div class="bom-empty-icon">🔍</div><p>没有匹配的BOM项</p></div>'
      : '<div class="bom-empty-state"><div class="bom-empty-icon">📋</div><p>该产品暂无BOM项</p></div>';
    return;
  }

  const formulaCols = [
    {key:'qty_formula', icon:'📐', label:'数量/公式', isQty:true},
    {key:'condition_formula', icon:'⚡', label:'条件公式'},
    {key:'reference_formula', icon:'📝', label:'备注公式'},
    {key:'price_formula', icon:'💰', label:'价格公式'},
  ];

  let colHeaders = '<th style="width:15%">物料名称</th><th style="width:12%">内部编码</th>';
  formulaCols.forEach(function(c) {
    colHeaders += '<th style="width:13%"><span class="col-icon">' + c.icon + '</span>' + c.label + '</th>';
  });
  colHeaders += '<th style="width:4%"></th><th style="width:2.5rem"></th>';

  let html = '<table class="pd-bom-spreadsheet"><thead><tr>' + colHeaders + '</tr></thead><tbody>';

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const subPartDetail = item.sub_part_detail || {};
    const subPartName = subPartDetail.name || '#' + item.sub_part;
    const subPartRef = subPartDetail.ipn || '';
    const cfg = pcfgMap[item.pk];
    const hasCfg = !!cfg;
    const staticQty = item.quantity;
    const isVariant = hasCfg && cfg.enable_variant;
    const vm = isVariant ? vmByPbi[cfg.id] : null;
    const rowBgClass = isVariant ? ' class="bg-purple-50/50"' : '';

    let nameCell, ipnCell, tplRef, tplIpn;
    if (isVariant && vm) {
      var escNameVal = (vm.variant_name_template || '').replace(/'/g,"\\'").replace(/"/g,'&quot;');
      var escIpnVal = (vm.variant_ipn_template || '').replace(/'/g,"\\'").replace(/"/g,'&quot;');
      var mappingId = vm.id;
      var tplId = vm.template_part || 0;
      var tplName = vm.template_part_name || '#部件';
      tplRef = '<div class="text-[9px] text-purple-400 mt-0.5">🧬参考: <span class="cursor-pointer hover:text-purple-600 underline decoration-dotted" onclick="openPartDetail(' + tplId + ')">' + tplName + '</span></div>';
      tplIpn = '<div class="text-[9px] text-purple-400 mt-0.5">IPN: ' + (vm.template_part_ipn || '—') + '</div>';
      nameCell = '<td><div class="pbs-formula-cell" ondblclick="openCellEditor(' + item.pk + ",'variant_name','" + escNameVal + "',false," + mappingId + ')" title="双击编辑动态名称">'
        + (vm.variant_name_template ? '<span class="fmla-text">' + escHtml(vm.variant_name_template) + '</span>' : '<span class="fmla-empty">—</span>')
        + '<span class="fmla-hint">双击编辑</span>'
        + tplRef
        + '</div></td>';
      ipnCell = '<td class="pbs-ipn"><div class="pbs-formula-cell" ondblclick="openCellEditor(' + item.pk + ",'variant_ipn','" + escIpnVal + "',false," + mappingId + ')" title="双击编辑动态编码">'
        + (vm.variant_ipn_template ? '<span class="fmla-text">' + escHtml(vm.variant_ipn_template) + '</span>' : '<span class="fmla-empty">—</span>')
        + '<span class="fmla-hint">双击编辑</span>'
        + tplIpn
        + '</div></td>';
    } else {
      nameCell = '<td><span class="pbs-name clickable-part" onclick="openPartDetail(' + item.sub_part + ')" title="点击查看零件详情">' + subPartName + '</span></td>';
      ipnCell = '<td class="pbs-ipn">' + (subPartRef || '<span class="text-gray-300">—</span>') + '</td>';
    }
    let rowHtml = '<tr' + rowBgClass + '>' + nameCell + ipnCell;

    for (let j = 0; j < formulaCols.length; j++) {
      const c = formulaCols[j];
      const val = hasCfg ? (cfg[c.key] || '') : '';
      let display;
      if (c.isQty) {
        if (val) {
          display = '<span class="fmla-text" title="' + val.replace(/"/g,'&quot;') + '">×' + staticQty + ' → 📐 ' + val + '</span>';
        } else {
          display = '<span class="pbs-qty">×' + staticQty + '</span>';
        }
      } else {
        display = val ? '<span class="fmla-text" title="' + val.replace(/"/g,'&quot;') + '">' + val + '</span>' : '<span class="fmla-empty">—</span>';
      }
      const hint = val ? '双击编辑' : '双击添加公式';
      const escVal = val.replace(/'/g,"\\'").replace(/"/g,'&quot;');
      rowHtml += '<td><div class="pbs-formula-cell" ondblclick="openCellEditor(' + item.pk + ",'" + c.key + "','" + escVal + "'," + (c.isQty ? 'true' : 'false') + ',' + (c.isQty ? staticQty : '0') + ')" title="' + hint + '">' + display + '<span class="fmla-hint">' + hint + '</span></div></td>';
    }

    const escName = subPartName.replace(/'/g,"\\'");
    const escIpn = (subPartRef || '').replace(/'/g,"\\'");
    rowHtml += '<td class="text-center"><button class="text-red-400 hover:text-red-600 text-xs p-1 rounded hover:bg-red-50" onclick="resetBomConfig(' + item.pk + ",'" + escName + "')" + '" title="从BOM移除">✕</button></td>';
    rowHtml += '<td class="text-center"><button class="text-blue-400 hover:text-blue-600 text-xs p-1 rounded hover:bg-blue-50" onclick="cartAddStaticPart(' + item.sub_part + ",'" + escName + "','" + escIpn + "')" + '" title="加入购物车">🛒</button></td></tr>';
    html += rowHtml;
  }
  html += '</tbody></table>';
  container.innerHTML = html;
}

// ===== CELL EDITOR =====
let _ceState = { itemPk: null, field: null };
let _cePreviewTimer = null;

function ceTogglePills() {
  const area = document.getElementById('ce-pills-area');
  const icon = document.getElementById('ce-pills-toggle-icon');
  if (!area || !icon) return;
  if (area.style.display === 'none') {
    area.style.display = '';
    icon.textContent = '▾';
  } else {
    area.style.display = 'none';
    icon.textContent = '▸';
  }
}

function ceToggleTemplates() {
  const area = document.getElementById('ce-template-area');
  const icon = document.getElementById('ce-tpl-toggle-icon');
  if (!area || !icon) return;
  if (area.style.display === 'none') {
    area.style.display = '';
    icon.textContent = '▾';
    // Re-render when first opened
    FormulaTemplates.renderInto('ce-template-area', {
      onApply: function(f) {
        const inp = document.getElementById('pbs-ce-input');
        inp.value = f;
        // If CM is active, update it too
        if (window.CmFormulaEditor) {
          const inst = window.CmFormulaEditor.getCmInstance(inp);
          if (inst && inst.editor) { inst.editor.setValue(f); }
        }
        ceSchedulePreview();
      }
    });
  } else {
    area.style.display = 'none';
    icon.textContent = '▸';
  }
}

// ===== DOWNLOAD: BOM CSV =====
async function downloadBomCsv() {
  const pid = configuratorPartId;
  if (!pid) { setStatus('error', '请先选择产品'); return; }
  window.open('/api/parametric-bom/export/bom-csv/?part_id=' + pid, '_blank');
}

// ===== DOWNLOAD: Attachment ZIP =====
async function downloadAttachmentsZip() {
  const pid = configuratorPartId;
  if (!pid) { setStatus('error', '请先选择产品'); return; }
  setStatus('loading', '正在打包附件...');
  try {
    const a = document.createElement('a');
    a.href = '/api/parametric-bom/export/attachment-zip/?part_id=' + pid;
    a.download = '';
    a.click();
    setStatus('success', '附件下载已开始');
  } catch (e) {
    setStatus('error', '下载失败: ' + e.message);
  }
}

// ===== DOWNLOAD: Bundle ZIP =====
async function downloadBundleZip() {
  const pid = configuratorPartId;
  if (!pid) { setStatus('error', '请先选择产品'); return; }
  window.open('/api/parametric-bom/export/bundle-zip/?part_id=' + pid, '_blank');
}

function ceInsertText(text) {
  const ta = document.getElementById('pbs-ce-input');
  if (!ta) return;
  // Try CM insert first
  if (window.CmFormulaEditor) {
    const el = ta;
    if (window.CmFormulaEditor.insertAtCursor(el, text)) {
      ceSchedulePreview();
      return;
    }
  }
  const start = ta.selectionStart;
  const end = ta.selectionEnd;
  ta.value = ta.value.substring(0, start) + text + ta.value.substring(end);
  const newPos = start + text.length;
  ta.selectionStart = ta.selectionEnd = newPos;
  ta.focus();
  ceSchedulePreview();
}

function ceSchedulePreview() {
  clearTimeout(_cePreviewTimer);
  _cePreviewTimer = setTimeout(ceDoPreview, 400);
}

async function ceDoPreview() {
  const formula = document.getElementById('pbs-ce-input').value.trim();
  const statusEl = document.getElementById('pbs-ce-status');
  if (!formula) { statusEl.innerHTML = '<span class="text-gray-400">输入公式</span>'; return; }
  statusEl.innerHTML = '<span class="text-gray-400">⏳ 计算中...</span>';
  const ctx = window.__ceParamContext || {};
  const res = await apiCall('POST', 'formula/preview/', { formula, context: { param: ctx } });
  const data = res.data || {};
  if (data.success === false || data.error) {
    const errMsg = data.error || '未知错误';
    statusEl.innerHTML = `<span class="text-red-500">❌ ${escHtml(errMsg)}</span>`;
    return;
  }
  const val = data.result !== undefined ? data.result : (data.value || '');
  statusEl.innerHTML = `📐 结果: <strong class="text-green-600 font-mono">${escHtml(String(val))}</strong>`;
}

function ceLoadPills(pid) {
  const pillsEl = document.getElementById('ce-param-pills');
  if (!pid || !pillsEl) { pillsEl.innerHTML = '<span class="text-[10px] text-gray-400">请先选择产品</span>'; return; }
  pillsEl.innerHTML = '<span class="text-[10px] text-gray-400">加载中...</span>';
  Promise.all([
    apiCall('GET', `part-config/?part=${pid}`),
    apiCall('GET', `part-variables/?part=${pid}&limit=9999`),
  ]).then(([paramRes, varRes]) => {
    const configs = paramRes.error ? [] : (Array.isArray(paramRes.data) ? paramRes.data : (paramRes.data.results || []));
    const vars = varRes.error ? [] : (Array.isArray(varRes.data) ? varRes.data : (varRes.data.results || []));
    let html = '';
    const ctx = {};
    // Function pills — grouped in two columns like variable dialog
    html += '<div class="grid grid-cols-2 gap-x-2 gap-y-0.5 mb-1">';
    html += '<div><label class="text-[9px] text-gray-400 mb-0.5 block">🔢 数学:</label><div class="flex flex-wrap gap-1">';
    ['CEIL','FLOOR','ROUND','IF','AND','OR','NOT','MIN','MAX','ABS','SQRT','POW','MOD','SUM','AVG','COUNT'].forEach(function(fn) {
      const sigs = {CEIL:'(x)',FLOOR:'(x)',ROUND:'(x,[n])',IF:'(c,t,f)',AND:'(...)',OR:'(...)',NOT:'(x)',MIN:'(a,b)',MAX:'(a,b)',ABS:'(x)',SQRT:'(x)',POW:'(base,exp)',MOD:'(a,b)',SUM:'(...)',AVG:'(...)',COUNT:'(...)'};
      const titles = {CEIL:'向上取整',FLOOR:'向下取整',ROUND:'四舍五入',IF:'条件判断',AND:'逻辑与',OR:'逻辑或',NOT:'逻辑非',MIN:'取最小值',MAX:'取最大值',ABS:'绝对值',SQRT:'平方根',POW:'幂运算',MOD:'取余数',SUM:'求和',AVG:'平均值',COUNT:'计数'};
      html += `<span class="fe-fn-pill text-[10px] px-1.5 py-0.5" onclick="ceInsertText('${fn}${sigs[fn]||'()'}')" title="${fn}${sigs[fn]||'()'} — ${titles[fn]||''}">${fn}</span>`;
    });
    html += '</div></div><div><label class="text-[9px] text-gray-400 mb-0.5 block">🔤 字符串/类型:</label><div class="flex flex-wrap gap-1">';
    ['CONCAT','LEN','UPPER','LOWER','TRIM','INT','FLOAT','STR','BOOL'].forEach(function(fn) {
      const sigs = {CONCAT:'(...)',LEN:'(s)',UPPER:'(s)',LOWER:'(s)',TRIM:'(s)',INT:'(x)',FLOAT:'(x)',STR:'(x)',BOOL:'(x)'};
      const titles = {CONCAT:'拼接字符串',LEN:'字符串长度',UPPER:'转大写',LOWER:'转小写',TRIM:'去除首尾空格',INT:'取整',FLOAT:'转浮点数',STR:'转字符串',BOOL:'转布尔值'};
      html += `<span class="fe-fn-pill text-[10px] px-1.5 py-0.5" onclick="ceInsertText('${fn}${sigs[fn]||'()'}')" title="${fn}${sigs[fn]||'()'} — ${titles[fn]||''}">${fn}</span>`;
    });
    html += '</div></div></div>';
    // Params
    if (configs.length) {
      html += '<div class="flex flex-wrap gap-1 mb-1">';
      configs.forEach(c => {
        const paramName = c.name || c.template_name || 'unknown';
        const defVal = c.default_value;
        ctx[paramName] = defVal;
        html += `<span class="fe-param-pill text-[10px] px-1.5 py-0.5" onclick="ceInsertText('param.${paramName.replace(/'/g, "\\'")}')">${paramName}${defVal ? '=' + defVal : ''}</span>`;
      });
      html += '</div>';
    }
    // Variables
    if (vars.length) {
      html += '<div class="flex flex-wrap gap-1">';
      vars.forEach(v => {
        const vName = v.name || 'unknown';
        const vVal = v.computed_value;
        if (vVal != null) ctx[vName] = vVal;
        html += `<span class="fe-param-pill text-[10px] px-1.5 py-0.5" style="background:#eff6ff;border-color:#bfdbfe;color:#1d4ed8" onclick="ceInsertText('param.${vName.replace(/'/g, "\\'")}')">${vName}${vVal != null ? '=' + escHtml(String(vVal)) : ''}</span>`;
      });
      html += '</div>';
    }
    pillsEl.innerHTML = html;
    window.__ceParamContext = ctx;
    ceSchedulePreview();
  }).catch(() => {
    pillsEl.innerHTML = '<span class="text-[10px] text-gray-400">加载失败</span>';
  });
}

// ── Formula Templates Library (localStorage-based MVP) ──
window.FormulaTemplates = {
  STORAGE_KEY: '_ft_lib',

  getAll() {
    try {
      return JSON.parse(localStorage.getItem(this.STORAGE_KEY)) || [];
    } catch(e) { return []; }
  },

  save(name, formula, category) {
    if (!name || !formula) return false;
    const list = this.getAll();
    // Check duplicate name — overwrite
    const idx = list.findIndex(t => t.name === name);
    const entry = { name, formula, category: category || '通用', created_at: Date.now() };
    if (idx >= 0) list[idx] = entry;
    else list.push(entry);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(list));
    return true;
  },

  remove(name) {
    const list = this.getAll().filter(t => t.name !== name);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(list));
  },

  getCategories() {
    const cats = new Set();
    this.getAll().forEach(t => cats.add(t.category || '通用'));
    return Array.from(cats).sort();
  },

  // Render a template list into a container and wire up interactions
  renderInto(containerId, opts = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const onApply = opts.onApply || function(f) { document.getElementById(opts.targetInput || 'pbs-ce-input').value = f; };
    const onSave = opts.onSave || function() {};
    const templates = this.getAll();
    const cats = this.getCategories();

    let html = '<div class="ft-container">';
    if (!templates.length) {
      html += '<div class="text-[10px] text-gray-400 py-1">暂无模板，先保存一个</div>';
    } else {
      cats.forEach(cat => {
        const items = templates.filter(t => (t.category || '通用') === cat);
        html += `<div class="ft-cat mb-1"><div class="text-[10px] font-medium text-gray-500 mb-0.5">${escHtml(cat)}</div>`;
        items.forEach(t => {
          const short = (t.formula || '').length > 40 ? escHtml(t.formula.substring(0, 40) + '…') : escHtml(t.formula);
          html += `<div class="ft-item" data-name="${escHtml(t.name)}" data-formula="${escHtml(t.formula).replace(/"/g,'&quot;')}">
            <span class="ft-item-name">${escHtml(t.name)}</span>
            <span class="ft-item-fmla">${short}</span>
            <span class="ft-item-apply" title="应用模板">📋</span>
            <span class="ft-item-del" title="删除">🗑️</span>
          </div>`;
        });
        html += '</div>';
      });
    }
    html += '<div class="ft-actions mt-1 pt-1 border-t border-gray-100">';
    html += '<button class="ft-btn-save text-[10px] text-blue-600 hover:text-blue-800 cursor-pointer" onclick="FormulaTemplates.promptSave(\'' + containerId + '\')">💾 保存当前公式为模板</button>';
    html += '</div></div>';
    container.innerHTML = html;

    // Wire apply/del
    container.querySelectorAll('.ft-item').forEach(el => {
      el.querySelector('.ft-item-apply').addEventListener('click', function(e) {
        e.stopPropagation();
        onApply(el.dataset.formula);
      });
      el.querySelector('.ft-item-del').addEventListener('click', function(e) {
        e.stopPropagation();
        if (confirm(`删除模板「${el.dataset.name}」？`)) {
          FormulaTemplates.remove(el.dataset.name);
          FormulaTemplates.renderInto(containerId, opts);
        }
      });
      // Click on item = apply
      el.addEventListener('click', function() {
        onApply(this.dataset.formula);
      });
    });
  },

  promptSave(containerId) {
    const currentFormula = (document.getElementById('pbs-ce-input')?.value || document.getElementById('av-formula')?.value || '').trim();
    if (!currentFormula) { alert('公式为空，无法保存'); return; }
    const name = prompt('请输入模板名称（例如：标准数量公式）', '');
    if (!name) return;
    const cat = prompt('分类（例如：数量、条件、选件、自定义）', '通用');
    this.save(name, currentFormula, cat || '通用');
    this.renderInto(containerId);
  }
};

function openCellEditor(itemPk, field, currentVal, isQty, mappingId) {
  _ceState = { itemPk: itemPk, field: field, isQty: !!isQty, staticQty: mappingId || 1, mappingId: mappingId || null };
  const overlay = document.getElementById('pbs-ce-overlay');
  const input = document.getElementById('pbs-ce-input');
  const title = document.getElementById('pbs-ce-title');
  const statusEl = document.getElementById('pbs-ce-status');
  statusEl.innerHTML = '';
  statusEl.className = 'flex items-center gap-2 text-xs mt-0.5 min-h-[1.5em] text-gray-500';

  if (field === 'variant_name' || field === 'variant_ipn') {
    const labels = {variant_name:'🧬 动态名称模板', variant_ipn:'🧬 动态编码模板'};
    const placeholders = {variant_name:'立柱-H{高度}', variant_ipn:'COL-{高度}-{宽度}'};
    title.textContent = labels[field] || '🧬 编辑动态模板';
    input.value = currentVal || '';
    input.placeholder = placeholders[field] || '输入模板，用{参数名}引用...';
  } else if (isQty) {
    const qtyText = currentVal ? ('当前: ×' + _ceState.staticQty + ' + 公式「' + currentVal + '」') : ('当前: ×' + _ceState.staticQty + '（静态数量）');
    title.textContent = '📐 ' + qtyText;
    input.value = currentVal || '';
    input.placeholder = '输入纯数字=改静态数量，输入公式=动态计算';
  } else {
    const labels = {qty_formula:'数量/公式', condition_formula:'条件公式', reference_formula:'备注公式', price_formula:'价格公式'};
    const placeholders = {qty_formula:'CEIL(长度/500)*2', condition_formula:'param.速度 > 15', reference_formula:"CONCAT('定制-',长度,'mm')", price_formula:"子件单价 * CEIL(param.长度 / 1000)"};
    const iconMap = {qty_formula:'📐', condition_formula:'⚡', reference_formula:'📝', price_formula:'💰'};
    title.textContent = (iconMap[field] || '✏️') + ' ' + (labels[field] || '编辑');
    input.value = currentVal || '';
    input.placeholder = placeholders[field] || '输入公式...';
  }

  overlay.classList.add('open');
  // Load pills for the current product
  const pid = configuratorPartId;
  ceLoadPills(pid);
  // Destroy old CM if any, then attach fresh
  setTimeout(function() {
    const el = document.getElementById('pbs-ce-input');
    if (!el) return;
    // Destroy existing CM instance
    if (el.dataset.cmInit && window.CmFormulaEditor) {
      const inst = window.CmFormulaEditor.getCmInstance(el);
      if (inst) {
        const wrap = inst.editor.getWrapperElement();
        if (wrap && wrap.parentNode) wrap.parentNode.remove();
        el.style.display = '';
        delete el.dataset.cmInit;
      }
    }
    // Attach fresh CM
    if (window.CmFormulaEditor) {
      window.CmFormulaEditor.attachCmToInput(el, { inline: false, minHeight: 50 });
    }
    el.focus();
  }, 100);
}

function closeCellEditor(evt) {
  if (evt && evt.target !== document.getElementById('pbs-ce-overlay')) {
    const box = document.getElementById('pbs-ce-box');
    if (box && box.contains(evt.target)) return;
  }
  document.getElementById('pbs-ce-overlay').classList.remove('open');
  _ceState = { itemPk: null, field: null };
}

async function saveCellFormula() {
  const st = _ceState;
  if (!st.itemPk || !st.field) return;
  const input = document.getElementById('pbs-ce-input');
  const statusEl = document.getElementById('pbs-ce-status');
  const formula = input.value.trim();

  statusEl.innerHTML = '<span class="text-gray-400">⏳ 保存中...</span>';

  // Variant name/ipn template: save to VariantMapping
  if (st.field === 'variant_name' || st.field === 'variant_ipn') {
    if (!st.mappingId) {
      statusEl.innerHTML = '<span class="text-red-500">❌ 找不到动态映射ID</span>';
      return;
    }
    var fieldKey = st.field === 'variant_name' ? 'variant_name_template' : 'variant_ipn_template';
    var patchData = {};
    patchData[fieldKey] = formula;
    const res = await apiCall('PATCH', 'variant-mappings/' + st.mappingId + '/', patchData);
    if (res.error) {
      statusEl.innerHTML = '<span class="text-red-500">❌ ' + escHtml(res.data?.error || res.data?.detail || '保存失败') + '</span>';
    } else {
      statusEl.innerHTML = '<span class="text-green-600">✅ 已保存</span>';
      clearAreaDirty('bom');
      setTimeout(function() { document.getElementById('pbs-ce-overlay').classList.remove('open'); loadPdBOMM(); }, 600);
    }
    return;
  }

  // Qty: plain number -> update BomItem
  if (st.isQty && /^\d+(\.\d+)?$/.test(formula)) {
    const num = parseFloat(formula);
    const res = await fetch('/api/bom/' + st.itemPk + '/', {
      method: 'PATCH',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
      credentials: 'same-origin',
      body: JSON.stringify({ quantity: num }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(function() { return {}; });
      statusEl.innerHTML = '<span class="text-red-500">❌ ' + escHtml(errData.error || errData.detail || '保存失败') + '</span>';
    } else {
      statusEl.innerHTML = '<span class="text-green-600">✅ 数量已更新</span>';
      clearAreaDirty('bom');
      const exRes = await apiCall('GET', 'bom-item-config/?bom_item=' + st.itemPk);
      const exList = exRes.data && !exRes.error ? (Array.isArray(exRes.data) ? exRes.data : (exRes.data.results || [])) : [];
      if (exList[0] && exList[0].qty_formula) {
        await apiCall('PATCH', 'bom-item-config/' + exList[0].id + '/', { qty_formula: '' });
      }
      setTimeout(function() { document.getElementById('pbs-ce-overlay').classList.remove('open'); loadPdBOMM(); }, 600);
    }
    return;
  }

  // Formula save
  const exRes = await apiCall('GET', 'bom-item-config/?bom_item=' + st.itemPk);
  const exList = exRes.data && !exRes.error ? (Array.isArray(exRes.data) ? exRes.data : (exRes.data.results || [])) : [];
  const exCfg = exList[0];
  const data = {};
  data[st.field] = formula;
  if (exCfg) {
    ['qty_formula','condition_formula','reference_formula','price_formula'].forEach(function(f) {
      if (f !== st.field && exCfg[f]) data[f] = exCfg[f];
    });
  } else {
    data.bom_item = st.itemPk;
  }
  let res = exCfg ? await apiCall('PATCH', 'bom-item-config/' + exCfg.id + '/', data) : await apiCall('POST', 'bom-item-config/', data);
  if (res.error) {
    const errMsg = res.data?.error || res.data?.detail || (typeof res.data === 'object' ? JSON.stringify(res.data).substring(0,120) : '保存失败');
    statusEl.innerHTML = '<span class="text-red-500">❌ ' + escHtml(errMsg) + '</span>';
  } else {
    statusEl.innerHTML = '<span class="text-green-600">✅ 已保存</span>';
    clearAreaDirty('bom');
    setTimeout(function() { document.getElementById('pbs-ce-overlay').classList.remove('open'); loadPdBOMM(); }, 600);
  }
}

function resetBomConfig(bomItemId, name) {
  // 1) Delete VariantMapping if exists (dynamic item)
  apiCall('GET', 'variant-mappings/?parametric_bom_item__bom_item=' + bomItemId).then(function(vmRes) {
    if (!vmRes.error) {
      var vms = Array.isArray(vmRes.data) ? vmRes.data : (vmRes.data.results || []);
      if (vms.length) {
        apiCall('DELETE', 'variant-mappings/' + vms[0].id + '/');
      }
    }
  });
  // 2) Delete ParametricBomItem config if exists
  apiCall('GET', `bom-item-config/?bom_item=${bomItemId}`).then(res => {
    if (!res.error) {
      const configs = Array.isArray(res.data) ? res.data : (res.data.results || []);
      if (configs.length) {
        apiCall('DELETE', `bom-item-config/${configs[0].id}/`);
      }
    }
  });
  // 2) Delete the BomItem itself
  fetch(`/api/bom/${bomItemId}/`, {
    method: 'DELETE',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
    credentials: 'same-origin',
  }).then(res => {
    if (res.ok || res.status === 204) {
      setStatus('success', `✅ 已移除「${name}」`);
      loadPdBOMM();
    } else {
      setStatus('error', '删除BOM项失败');
    }
  }).catch(() => {
    setStatus('error', '网络错误');
  });
}

// ── Add BOM Item ──
let _allPartsCache = null;
let _abAllParts = []; // full list for filtering

// ── Unified Add BOM Item Modal ──
let _abItemType = 'static';
let _abParamMapping = {};

function abSetType(type) {
  _abItemType = type;
  document.querySelectorAll('.ab-type-btn').forEach(function(btn) {
    btn.classList.toggle('selected', btn.dataset.type === type);
  });
  var label = document.getElementById('ab-part-label');
  if (label) label.textContent = type === 'dynamic' ? '选择模板零件' : '选择子件';
  var hint = document.getElementById('ab-dynamic-hint');
  if (hint) hint.classList.toggle('hidden', type !== 'dynamic');
  updateAbMappingCount();
}

function updateAbMappingCount() {
  var countEl = document.getElementById('ab-mapping-count');
  if (!countEl) return;
  var keys = Object.keys(_abParamMapping);
  countEl.textContent = keys.length ? '已配置 ' + keys.length + ' 条映射' : '未配置';
}

function abEditParamMapping() {
  var current = JSON.stringify(_abParamMapping, null, 2);
  var input = prompt('编辑参数映射 (JSON格式，如 {"载重": "parent.载重"}):', current === '{}' ? '' : current);
  if (input === null) return;
  try {
    var parsed = input.trim() ? JSON.parse(input.trim()) : {};
    if (typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error();
    _abParamMapping = parsed;
    updateAbMappingCount();
  } catch(e) { alert('JSON格式无效，请检查'); }
}

async function openAddBomItemModal() {
  const pid = configuratorPartId;
  if (!pid) { setStatus('error', '请先选择产品'); return; }
  // Reset
  _abItemType = 'static';
  _abParamMapping = {};
  document.querySelectorAll('.ab-type-btn').forEach(function(btn) {
    btn.classList.toggle('selected', btn.dataset.type === 'static');
  });
  var hint = document.getElementById('ab-dynamic-hint');
  if (hint) hint.classList.add('hidden');
  var label = document.getElementById('ab-part-label');
  if (label) label.textContent = '选择子件';
  updateAbMappingCount();

  const product = parts.find(p => p.pk == pid);
  document.getElementById('ab-product-name').textContent = product ? (product.name || '#' + pid) : '#' + pid;
  _allPartsCache = null;
  _abAllParts = [];
  document.getElementById('ab-search').value = '';
  renderAbPartList();
  openModal('modal-add-bom');
  const countEl = document.getElementById('ab-search-count');
  if (countEl) countEl.textContent = '加载零件库中...';
  try {
    const res = await fetch('/api/part/?limit=10000&ordering=-creation_date', {
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()}, credentials: 'same-origin'
    });
    const data = res.ok ? (await res.json()) : [];
    const all = Array.isArray(data) ? data : (data.results || []);
    _allPartsCache = all.filter(function(p) { return p.pk != pid; });
    // Auto-retry search if user already typed something while loading
    const searchVal = (document.getElementById('ab-search').value || '').trim();
    if (searchVal) {
      doAbFilter(searchVal);
    } else {
      _abAllParts = _allPartsCache.slice(0, 200);
      renderAbPartList();
      if (countEl) countEl.textContent = '共 ' + _allPartsCache.length + ' 个零件';
    }
  } catch(e) {
    if (countEl) countEl.textContent = '加载失败';
  }
}

let _abSearchTimer = null;
function filterAbParts(value) {
  clearTimeout(_abSearchTimer);
  _abSearchTimer = setTimeout(function() { doAbFilter(value); }, 100);
}

function doAbFilter(value) {
  const q = (value || '').trim().toLowerCase();
  const countEl = document.getElementById('ab-search-count');
  
  if (!_allPartsCache) {
    if (countEl) countEl.textContent = '零件库加载中，请稍候...';
    return;
  }
  
  if (!q) {
    _abAllParts = _allPartsCache.slice(0, 200);
    renderAbPartList();
    if (countEl) countEl.textContent = `共 ${_allPartsCache.length} 个零件`;
    return;
  }
  
  const matched = _allPartsCache.filter(p =>
    (p.name || p.full_name || '').toLowerCase().includes(q) ||
    (p.ipn || p.IPN || '').toLowerCase().includes(q) ||
    (p.description || '').toLowerCase().includes(q)
  );
  _abAllParts = matched.slice(0, 200);
  renderAbPartList();
  if (countEl) countEl.textContent = matched.length > 200
    ? `找到 ${matched.length}+ 个零件，显示前 200`
    : `找到 ${matched.length} 个零件`;
}

function renderAbPartList() {
  const sel = document.getElementById('ab-sub-part');
  sel.innerHTML = '<option value="">-- 请选择零件 --</option>';
  _abAllParts.forEach(p => {
    const ipn = p.ipn || p.IPN || '';
    const label = `${p.name || p.full_name || `#${p.pk}`}${ipn ? ` (${ipn})` : ''}`;
    sel.innerHTML += `<option value="${p.pk}">${label}</option>`;
  });
}

async function createBomItem() {
  const pid = configuratorPartId;
  const subPartId = document.getElementById('ab-sub-part').value;
  const qty = parseFloat(document.getElementById('ab-qty').value);
  const isDynamic = _abItemType === 'dynamic';
  
  if (!pid || !subPartId) { setStatus('error', isDynamic ? '请选择模板零件' : '请选择子件'); return; }
  if (!qty || qty <= 0) { setStatus('error', '请输入有效数量'); return; }
  
  // Check for duplicate sub_part in current BOM
  const existingRes = await fetch('/api/bom/?part=' + pid + '&sub_part_detail=True', {headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()}, credentials: 'same-origin'});
  const existingData = existingRes.ok ? (await existingRes.json()) : [];
  const existingItems = Array.isArray(existingData) ? existingData : (existingData.results || []);
  const dup = existingItems.find(function(i) { return String(i.sub_part) === String(subPartId); });
  if (dup) {
    const dupName = dup.sub_part_detail?.name || '#' + subPartId;
    setStatus('error', '❌ 「' + dupName + '」已在BOM中，不能重复添加');
    return;
  }
  
  setStatus('loading', isDynamic ? '正在添加动态项目...' : '正在添加静态项目...');
  
  try {
    const res = await fetch('/api/parametric-bom/create-bom-item/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
      credentials: 'same-origin',
      body: JSON.stringify({
        parent_part_id: pid,
        sub_part_id: parseInt(subPartId),
        quantity: qty,
        is_dynamic: isDynamic,
        param_mappings: _abParamMapping,
      }),
    });
    
    if (res.ok) {
      setStatus('success', '✅ BOM项已添加');
      closeModal('modal-add-bom');
      loadPdBOMM();
    } else {
      const err = await res.json();
      setStatus('error', '添加失败: ' + (err.message || JSON.stringify(err)));
    }
  } catch(e) {
    setStatus('error', '网络错误: ' + e.message);
  }
}

// ── Configurator: State ──
let cfgParams = []; // full sorted param configs
let cfgParamValues = {}; // {configId: value}
let cfgBOMItems = [];

async function loadPdConfigurator() {
  const pid = configuratorPartId;
  if (!pid) return;
  const container = document.getElementById('cfg-params-container');
  container.innerHTML = '<div class="cfg-empty"><div class="cfg-empty-icon">⏳</div>加载参数中...</div>';
  
  const res = await apiCall('GET', `part-config/?part=${parseInt(pid)}`);
  if (res.error) { container.innerHTML = '<div class="cfg-empty" style="color:#dc2626">❌ 加载失败</div>'; return; }
  const configs = res.data.results || (Array.isArray(res.data) ? res.data : []);
  
  cfgParams = configs.sort((a,b) => (a.display_order||0) - (b.display_order||0));
  cfgParamValues = {};
  cfgParams.forEach(c => { cfgParamValues[c.id] = c.default_value != null ? c.default_value : ''; });
  
  renderCfgParams();
  document.getElementById('cfg-param-count').textContent = `${cfgParams.length} 个参数`;
  
  // Auto-expand BOM
  await cfgExpandBOM();
  await cfgLoadConfigs();
}

function renderCfgParams() {
  const container = document.getElementById('cfg-params-container');
  const computedCard = document.getElementById('cfg-computed-card');
  const computedList = document.getElementById('cfg-computed-list');
  
  const drivingParams = cfgParams.filter(c => c.is_driving);
  const computedParams = cfgParams.filter(c => c.is_computed);
  
  if (!drivingParams.length && !computedParams.length) {
    container.innerHTML = '<div class="cfg-empty"><div class="cfg-empty-icon">🔧</div>该产品没有参数，先在参数Tab中添加</div>';
    return;
  }
  
  // Driving params
  let html = '';
  drivingParams.forEach(cfg => {
    const name = cfg.name || '参数';
    const type = cfg.parameter_type || 'number';
    const val = cfgParamValues[cfg.id] != null ? cfgParamValues[cfg.id] : '';
    
    html += renderCfgParamControl(cfg, name, type, val);
  });
  container.innerHTML = html;
  
  // Computed params
  if (computedParams.length) {
    computedCard.style.display = 'block';
    let ch = '';
    computedParams.forEach(cfg => {
      const name = cfg.name || '计算参数';
      const val = cfg.default_value || '—';
      ch += `<div class="cfg-computed-row">
        <span>${name}</span>
        <span class="cfg-cr-value" id="cfg-comp-${cfg.id}">${val}</span>
      </div>`;
    });
    computedList.innerHTML = ch;
  } else {
    computedCard.style.display = 'none';
  }
}

function renderCfgParamControl(cfg, name, type, val) {
  const cid = cfg.id;
  const safeName = name.replace(/'/g, "\\'");
  const typeLabels = {number:'🔢 数值', option:'🔘 选项', boolean:'☑️ 布尔', text:'📝 文本', multi_option:'多选', long_text:'长文本'};
  const tlabel = typeLabels[type] || type;
  const changeFn = `cfgOnParamChange(${cid}, this)`;
  
  let controlHtml = '';
  
  if (type === 'number') {
    const min = cfg.min_value != null ? parseFloat(cfg.min_value) : 0;
    const max = cfg.max_value != null ? parseFloat(cfg.max_value) : 10000;
    const step = cfg.step_value != null ? parseFloat(cfg.step_value) : (max - min > 100 ? 1 : 0.1);
    const v = val !== '' ? parseFloat(val) : min;
    // Values must be v + step*N within [min, max]
    const effMin = min >= v ? min : (v + Math.ceil((min - v) / step) * step);
    const effMax = max <= v ? max : (v + Math.floor((max - v) / step) * step);
    controlHtml = `<div class="cfg-pg-slider">
      <input type="range" min="${effMin}" max="${effMax}" step="${step}" value="${v}" data-cfg-id="${cid}"
        oninput="cfgSliderInput(this, ${cid})" onchange="${changeFn}">
      <span class="cfg-pg-val" id="cfg-val-${cid}">${v}</span>
    </div>
    <div class="cfg-pg-hint"><span>${min}</span><span>${max}</span></div>`;
    
  } else if (type === 'option') {
    const opts = cfg.options ? (Array.isArray(cfg.options) ? cfg.options : []) : [];
    controlHtml = `<select class="cfg-pg-select" onchange="${changeFn}">
      <option value="">-- 请选择 --</option>
      ${opts.map(o => `<option value="${o}"${o === val ? ' selected' : ''}>${o}</option>`).join('')}
    </select>`;
    
  } else if (type === 'multi_option') {
    const opts = cfg.options ? (Array.isArray(cfg.options) ? cfg.options : []) : [];
    const selected = val ? val.split(',') : [];
    controlHtml = `<div class="flex flex-wrap gap-1">
      ${opts.map(o => `<label class="flex items-center gap-1 text-xs cursor-pointer px-2 py-1 rounded border ${selected.includes(o)?'bg-blue-50 border-blue-300 text-blue-700':'bg-white border-slate-200 text-slate-600'}" style="transition:all 0.1s">
        <input type="checkbox" value="${o}" ${selected.includes(o)?'checked':''}
          onchange="cfgOnMultiChange(${cid})" data-cfg-multi-${cid}>
        <span>${o}</span>
      </label>`).join('')}
    </div>`;
    
  } else if (type === 'boolean') {
    const isTrue = val === 'true' || val === true || val === '1';
    controlHtml = `<div class="cfg-pg-bool">
      <div class="toggle-switch ${isTrue ? 'on' : ''}"
        onclick="this.classList.toggle('on'); this.nextElementSibling.textContent=this.classList.contains('on')?'是':'否'; cfgOnParamChange(${cid}, {value: this.classList.contains('on')?'true':'false'})">
        <div class="toggle-knob"></div>
      </div>
      <span class="text-xs text-slate-500">${isTrue ? '是' : '否'}</span>
    </div>`;
    
  } else if (type === 'long_text') {
    controlHtml = `<textarea class="cfg-pg-textarea" rows="3" placeholder="输入${safeName}" onchange="${changeFn}">${val}</textarea>`;

  } else {
    controlHtml = `<input class="cfg-pg-text" type="text" value="${val}" placeholder="输入${safeName}"
      onchange="${changeFn}">`;
  }
  
  return `<div class="cfg-param-group">
    <div class="cfg-pg-header">
      <span class="cfg-pg-name">${name}</span>
      <span class="cfg-pg-type">${tlabel}</span>
    </div>
    ${controlHtml}
  </div>`;
}

function cfgSliderInput(input, cid) {
  const valSpan = document.getElementById(`cfg-val-${cid}`);
  if (valSpan) valSpan.textContent = input.value;
}

function cfgOnParamChange(cid, el) {
  let val;
  if (el.value !== undefined) val = el.value;
  else if (el.dataset && el.dataset.value) val = el.dataset.value;
  else if (typeof el === 'object' && el.value) val = el.value;
  else if (typeof el === 'string') val = el;
  
  if (val === undefined && el && el.classList) {
    val = el.classList.contains('on') ? 'true' : 'false';
  }
  
  cfgParamValues[cid] = val != null ? String(val) : '';
  document.getElementById('cfg-status-dot').textContent = '● 已修改';
  
  // Debounced BOM refresh
  clearTimeout(window.__cfgDebounce);
  window.__cfgDebounce = setTimeout(() => cfgExpandBOM(), 500);
}

function cfgOnMultiChange(cid) {
  const checked = document.querySelectorAll(`input[data-cfg-multi-${cid}]:checked`);
  const vals = Array.from(checked).map(cb => cb.value).join(',');
  cfgParamValues[cid] = vals;
  document.getElementById('cfg-status-dot').textContent = '● 已修改';
  clearTimeout(window.__cfgDebounce);
  window.__cfgDebounce = setTimeout(() => cfgExpandBOM(), 500);
}

function cfgGetParamContext() {
  const ctx = {};
  cfgParams.forEach(c => {
    const name = c.name || `param_${c.id}`;
    ctx[name] = cfgParamValues[c.id] != null ? cfgParamValues[c.id] : '';
  });
  return ctx;
}

async function cfgExpandBOM() {
  const pid = configuratorPartId;
  if (!pid) return;
  const container = document.getElementById('cfg-bom-preview');
  container.innerHTML = '<div class="cfg-empty"><span class="spinner inline-block mr-1"></span>计算中...</div>';
  
  const ctx = cfgGetParamContext();
  try {
    const res = await apiCall('POST', 'evaluate/', {part_id: parseInt(pid), parameters: ctx});
    if (res.error) { container.innerHTML = '<div class="cfg-empty" style="color:#dc2626">❌ BOM展开失败</div>'; return; }
    const bomTree = res.data.bom_tree || [];
    cfgBOMItems = Array.isArray(bomTree) ? bomTree : (bomTree.children || []);
    renderCfgBOM();
    document.getElementById('cfg-status-dot').textContent = '● 就绪';
    // Also estimate cost
    await cfgEstimateCost();
    // Show cart button
    var cartBtn = document.getElementById('cfg-add-cart-btn');
    if (cartBtn) cartBtn.style.display = '';
  } catch(e) {
    container.innerHTML = '<div class="cfg-empty" style="color:#dc2626">❌ 展开出错</div>';
  }
}

function renderCfgBOM() {
  const container = document.getElementById('cfg-bom-preview');
  if (!cfgBOMItems.length) {
    container.innerHTML = '<div class="cfg-empty"><div class="cfg-empty-icon">📋</div>BOM展开为空</div>';
    return;
  }
  
  let html = '';
  // Helper to render tree
  function renderTree(items, depth) {
    if (!items || !items.length) return '';
    let h = '';
    items.forEach(item => {
      const isVariant = item.mode === 'variant';
      const hasDynamicName = isVariant && !!item.variant_name;
      const icon = isVariant ? '🧬' : '📦';
      const name = hasDynamicName ? item.variant_name : (item.part_name || item.name || '未知');
      const qty = item.calculated_quantity != null ? item.calculated_quantity : (item.quantity != null ? item.quantity : (item.required_quantity || 1));
      const code = hasDynamicName ? (item.variant_ipn || item.ipn || item.part_ipn || '') : (item.ipn || item.part_ipn || '');
      const partId = item.actual_part_id || item.part_id;
      
      const variantClass = isVariant ? ' variant-item' : '';
      const codeInfo = code ? `<span class="cfg-bi-code">(${code})</span>` : '';
      const templateInfo = isVariant && item.template_part_name ? `<span class="cfg-bi-template">← ${item.template_part_name}</span>` : '';
      
      h += `<div class="cfg-bom-item cfg-bom-depth-${Math.min(depth,3)}${variantClass}">
        <span class="cfg-bi-icon${isVariant ? ' variant-icon' : ''}">${icon}</span>
        <span class="cfg-bi-name${partId ? ' clickable-part' : ''}${isVariant ? ' variant-name' : ''}"${partId ? ` onclick="openPartDetail(${partId})" title="点击查看零件详情"` : ''}>${name}${codeInfo}</span>
        ${templateInfo}
        <span class="cfg-bi-qty">×${qty}</span>
        ${item.unit_price != null ? `<span class="cfg-bi-price">¥${Number(item.unit_price).toFixed(2)}</span>` : ''}
      </div>`;
      if (item.children && item.children.length) {
        h += renderTree(item.children, depth + 1);
      }
    });
    return h;
  }
  html = renderTree(cfgBOMItems, 0);
  
  // Add total at bottom if prices exist
  var totalPrice = 0;
  var hasPrice = false;
  (function sumPrices(items) {
    items.forEach(function(it) {
      if (it.total_price != null) { totalPrice += Number(it.total_price); hasPrice = true; }
      if (it.children && it.children.length) sumPrices(it.children);
    });
  })(cfgBOMItems);
  if (hasPrice) {
    html += '<div class="cfg-bom-total"><span>合计</span><span class="cfg-bom-total-price">¥' + totalPrice.toFixed(2) + '</span></div>';
  }
  
  container.innerHTML = html;
}

// ===== DOWNLOAD from Configurator Step =====
async function cfgDownloadBom() {
  const pid = configuratorPartId;
  if (!pid) { setStatus('error', '请先选择产品'); return; }
  const ctx = cfgGetParamContext();
  try {
    const res = await fetch('/api/parametric-bom/export/bom-csv/', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
      credentials: 'same-origin',
      body: JSON.stringify({part_id: pid, parameters: ctx}),
    });
    if (!res.ok) { setStatus('error', '导出失败'); return; }
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'BOM清单.xlsx';
    a.click();
    URL.revokeObjectURL(a.href);
    setStatus('success', 'BOM清单已下载');
  } catch (e) { setStatus('error', '导出失败: ' + (e.message || e)); }
}

async function cfgDownloadAttachments() {
  const pid = configuratorPartId;
  if (!pid) { setStatus('error', '请先选择产品'); return; }
  const ctx = cfgGetParamContext();
  setStatus('loading', '正在打包附件...');
  try {
    const res = await fetch('/api/parametric-bom/export/attachment-zip/', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
      credentials: 'same-origin',
      body: JSON.stringify({part_id: pid, parameters: ctx}),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      setStatus('error', errData.error || '打包失败');
      return;
    }
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'attachments.zip';
    a.click();
    URL.revokeObjectURL(a.href);
    setStatus('success', '附件包已下载');
  } catch (e) { setStatus('error', '打包失败: ' + (e.message || e)); }
}

async function cfgDownloadBundle() {
  const pid = configuratorPartId;
  if (!pid) { setStatus('error', '请先选择产品'); return; }
  const ctx = cfgGetParamContext();
  setStatus('loading', '正在生成完整包...');
  try {
    const res = await fetch('/api/parametric-bom/export/bundle-zip/', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
      credentials: 'same-origin',
      body: JSON.stringify({part_id: pid, parameters: ctx}),
    });
    if (!res.ok) { setStatus('error', '打包失败'); return; }
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'BOM完整包.zip';
    a.click();
    URL.revokeObjectURL(a.href);
    setStatus('success', '完整包已下载');
  } catch (e) { setStatus('error', '打包失败: ' + (e.message || e)); }
}

async function cfgEstimateCost() {
  const pid = configuratorPartId;
  if (!pid) return;
  const costCard = document.getElementById('cfg-cost-card');
  costCard.style.display = 'block';
  
  const ctx = cfgGetParamContext();
  try {
    const res = await apiCall('POST', 'estimate-cost/', {part_id: parseInt(pid), parameters: ctx});
    if (res.error) return;
    const data = res.data;
    document.getElementById('cfg-cost-material').textContent = data.material_cost != null ? `¥${data.material_cost}` : '—';
    document.getElementById('cfg-cost-labor').textContent = data.labor_cost != null ? `¥${data.labor_cost}` : '—';
    document.getElementById('cfg-cost-total').textContent = data.total_cost != null ? `¥${data.total_cost}` : '—';
  } catch(e) {}
}

async function cfgSaveConfig() {
  const pid = configuratorPartId;
  if (!pid) { setStatus('error', '请先选择产品'); return; }
  const name = prompt('配置名称（可选）:', `配置 ${new Date().toLocaleString('zh-CN')}`);
  if (name === null) return;
  
  setStatus('loading', '保存配置...');
  const ctx = cfgGetParamContext();
  const res = await apiCall('POST', 'configurations/', {
    template_part: parseInt(pid),
    title: name || `配置 ${Date.now()}`,
    params_snapshot: ctx,
  });
  if (!res.error) {
    setStatus('success', `✅ 配置「${name}」已保存`);
    await cfgLoadConfigs();
  } else {
    const detail = res.data ? (res.data.error || res.data.detail || JSON.stringify(res.data).substring(0,100)) : '未知错误';
    setStatus('error', `保存失败: ${detail}`);
  }
}

async function cfgGenerateVariant() {
  const pid = configuratorPartId;
  if (!pid) { setStatus('error', '请先选择产品'); return; }
  const name = prompt('变体名称（可选）:', `变体 ${new Date().toLocaleString('zh-CN')}`);
  if (name === null) return;
  
  setStatus('loading', '正在生成变体...');
  const ctx = cfgGetParamContext();
  const res = await apiCall('POST', 'generate-variant/', {
    part_id: parseInt(pid),
    variant_name: name || `变体 ${Date.now()}`,
    param_context: ctx,
  });
  if (!res.error) {
    setStatus('success', `✅ 变体「${name}」已生成`);
  } else {
    setStatus('error', `生成失败: ${res.error}`);
  }
}

function cfgResetParams() {
  if (!confirm('重置所有参数为默认值？')) return;
  cfgParams.forEach(c => {
    cfgParamValues[c.id] = c.default_value != null ? c.default_value : '';
  });
  renderCfgParams();
  cfgExpandBOM();
  document.getElementById('cfg-status-dot').textContent = '● 就绪';
}

// ===== VARIABLES (场景12: 中间变量) =====
function avDestroyCm() {
  const el = document.getElementById('av-formula');
  if (!el || !el.dataset.cmInit || !window.CmFormulaEditor) return;
  const inst = window.CmFormulaEditor.getCmInstance(el);
  if (inst) {
    const wrap = inst.editor.getWrapperElement();
    if (wrap && wrap.parentNode) wrap.parentNode.remove();
    el.style.display = '';
    delete el.dataset.cmInit;
  }
}

function openAddVariableModal() {
  closeModal('modal-add-variable');
  avDestroyCm();
  document.getElementById('av-editing-id').value = '';
  document.querySelector('#modal-add-variable h3').textContent = '📐 新建中间变量';
  document.querySelector('#modal-add-variable .btn-primary').innerHTML = '✅ 创建变量';
  document.getElementById('av-name').value = '';
  document.getElementById('av-formula').value = '';
  document.getElementById('av-description').value = '';
  document.getElementById('av-formula-status').innerHTML = '';
  avLoadPillsAndVars(null);
  openModal('modal-add-variable');
  setTimeout(() => {
    const el = document.getElementById('av-formula');
    if (el && window.CmFormulaEditor) {
      window.CmFormulaEditor.attachCmToInput(el, { inline: false, minHeight: 64 });
      avAttachCmListener();
    }
  }, 150);
}

function openEditVariableModal(vid, name, formula, desc) {
  closeModal('modal-add-variable');
  avDestroyCm();
  document.getElementById('av-editing-id').value = vid;
  document.querySelector('#modal-add-variable h3').textContent = '✏️ 编辑变量';
  document.querySelector('#modal-add-variable .btn-primary').innerHTML = '💾 保存修改';
  document.getElementById('av-name').value = name || '';
  document.getElementById('av-formula').value = formula || '';
  document.getElementById('av-description').value = desc || '';
  document.getElementById('av-formula-status').innerHTML = '';
  avLoadPillsAndVars(vid);
  openModal('modal-add-variable');
  setTimeout(() => {
    const el = document.getElementById('av-formula');
    if (el && window.CmFormulaEditor) {
      window.CmFormulaEditor.attachCmToInput(el, { inline: false, minHeight: 64 });
      avAttachCmListener();
    }
  }, 150);
}

function avLoadPillsAndVars(editingVid) {
  const pid = configuratorPartId;
  const pillsEl = document.getElementById('av-param-pills');
  if (!pid) { pillsEl.innerHTML = '<span class="text-[10px] text-gray-400">请先选择产品</span>'; return; }
  pillsEl.innerHTML = '<span class="text-[10px] text-gray-400">加载中...</span>';
  // Load both params and variables in parallel
  Promise.all([
    apiCall('GET', `part-config/?part=${pid}`),
    apiCall('GET', `part-variables/?part=${pid}&limit=9999`),
  ]).then(([paramRes, varRes]) => {
    const configs = paramRes.error ? [] : (Array.isArray(paramRes.data) ? paramRes.data : (paramRes.data.results || []));
    const vars = varRes.error ? [] : (Array.isArray(varRes.data) ? varRes.data : (varRes.data.results || []));
    let html = '';
    const ctx = {};
    // Params
    if (configs.length) {
      html += '<div class="mb-1"><label class="text-[9px] text-gray-400 mb-0.5 block">📌 参数 (点击插入):</label><div class="flex flex-wrap gap-1">';
      configs.forEach(c => {
        const paramName = c.name || c.template_name || 'unknown';
        const defVal = c.default_value;
        ctx[paramName] = defVal;
        const display = defVal ? `${paramName} <span class="text-[9px] text-gray-400 ml-0.5">=${defVal}</span>` : paramName;
        html += `<span class="fe-param-pill" onclick="avInsertText('param.${paramName.replace(/'/g, "\\'")}')">${display}</span>`;
      });
      html += '</div></div>';
    }
    // Variables (skip the one being edited)
    const otherVars = vars.filter(v => v.id !== editingVid);
    if (otherVars.length) {
      html += '<div><label class="text-[9px] text-gray-400 mb-0.5 block">📐 其他变量 (点击插入):</label><div class="flex flex-wrap gap-1">';
      otherVars.forEach(v => {
        const vName = v.name || 'unknown';
        const vVal = v.computed_value;
        if (vVal != null) ctx[vName] = vVal;
        const display = vVal != null ? `${vName} <span class="text-[9px] text-gray-400 ml-0.5">=${escHtml(String(vVal))}</span>` : vName;
        html += `<span class="fe-param-pill" style="background:#eff6ff;border-color:#bfdbfe;color:#1d4ed8" onclick="avInsertText('param.${vName.replace(/'/g, "\\'")}')">${display}</span>`;
      });
      html += '</div></div>';
    }
    if (!configs.length && !otherVars.length) {
      html = '<span class="text-[10px] text-gray-400">该零件未配置参数和变量</span>';
    }
    pillsEl.innerHTML = html;
    window.__avParamContext = ctx;
    avSchedulePreview();
  }).catch(() => {
    pillsEl.innerHTML = '<span class="text-[10px] text-red-400">加载失败</span>';
  });
}

function avTogglePills() {
  const area = document.getElementById('av-pills-area');
  const icon = document.getElementById('av-pills-toggle-icon');
  if (area.style.display === 'none') {
    area.style.display = '';
    icon.textContent = '▾';
  } else {
    area.style.display = 'none';
    icon.textContent = '▸';
  }
}

function avToggleTemplates() {
  const area = document.getElementById('av-template-area');
  const icon = document.getElementById('av-tpl-toggle-icon');
  if (!area || !icon) return;
  if (area.style.display === 'none') {
    area.style.display = '';
    icon.textContent = '▾';
    FormulaTemplates.renderInto('av-template-area', {
      onApply: function(f) {
        const inp = document.getElementById('av-formula');
        inp.value = f;
        if (window.CmFormulaEditor) {
          const inst = window.CmFormulaEditor.getCmInstance(inp);
          if (inst && inst.editor) { inst.editor.setValue(f); }
        }
        avSchedulePreview();
      }
    });
  } else {
    area.style.display = 'none';
    icon.textContent = '▸';
  }
}

function avInsertText(text) {
  // Try CodeMirror insert first
  if (window.CmFormulaEditor) {
    const el = document.getElementById('av-formula');
    if (el && window.CmFormulaEditor.insertAtCursor(el, text)) {
      avSchedulePreview();
      return;
    }
  }
  // Fallback to textarea manipulation
  const ta = document.getElementById('av-formula');
  if (!ta) return;
  const start = ta.selectionStart;
  const end = ta.selectionEnd;
  const val = ta.value;
  ta.value = val.substring(0, start) + text + val.substring(end);
  const newPos = start + text.length;
  ta.selectionStart = ta.selectionEnd = newPos;
  ta.focus();
  avSchedulePreview();
}

let _avPreviewTimer = null;

function avSchedulePreview() {
  clearTimeout(_avPreviewTimer);
  _avPreviewTimer = setTimeout(avDoPreview, 400);
}

function avAttachCmListener() {
  const el = document.getElementById('av-formula');
  if (!el || !el.dataset.cmInit || !window.CmFormulaEditor) return;
  const inst = window.CmFormulaEditor.getCmInstance(el);
  if (!inst || inst._avListener) return;
  inst._avListener = true;
  inst.editor.on('change', function() { avSchedulePreview(); });
}

async function avDoPreview() {
  const formula = document.getElementById('av-formula').value.trim();
  const statusEl = document.getElementById('av-formula-status');
  if (!formula) { statusEl.innerHTML = '<span class="text-gray-400">请输入公式</span>'; return; }
  statusEl.innerHTML = '<span class="text-gray-400">⏳ 计算中...</span>';
  const ctx = window.__avParamContext || {};
  const res = await apiCall('POST', 'formula/preview/', { formula, context: { param: ctx } });
  // API returns HTTP 200 even on error, check body.success
  const data = res.data || {};
  if (data.success === false || data.error) {
    const errMsg = data.error || '未知错误';
    statusEl.innerHTML = `<span class="text-red-500">❌ ${escHtml(errMsg)}</span>`;
    return;
  }
  const val = data.result !== undefined ? data.result : (data.value || '');
  statusEl.innerHTML = `<span>📐 结果: <strong class="text-green-600 font-mono">${escHtml(String(val))}</strong></span>
    <span class="text-[10px] text-gray-400 ml-auto">基于默认参数值计算</span>`;
}

async function addVariable() {
  openAddVariableModal();
}

async function confirmAddVariable() {
  const pid = configuratorPartId;
  if (!pid) { alert('请先选择一个产品'); return; }
  const editId = document.getElementById('av-editing-id').value;
  const name = document.getElementById('av-name').value.trim();
  const formula = document.getElementById('av-formula').value.trim();
  const description = document.getElementById('av-description').value.trim();
  if (!name) { alert('请输入变量名'); return; }
  if (!formula) { alert('请输入公式'); return; }
  if (!editId) {
    // Create mode: check duplicate name
    const checkRes = await apiCall('GET', `part-variables/?part=${pid}&limit=9999`);
    const existing = checkRes.error ? [] : (Array.isArray(checkRes.data) ? checkRes.data : (checkRes.data.results || []));
    if (existing.some(v => v.name === name)) {
      alert(`变量名「${name}」已存在，请使用不同的名称`);
      return;
    }
    const res = await apiCall('POST', 'part-variables/', {
      part: pid, name, formula, description
    });
    if (res.error) { alert('创建失败: ' + res.error); return; }
  } else {
    // Edit mode
    const res = await apiCall('PATCH', `part-variables/${editId}/`, { name, formula, description });
    if (res.error) { alert('保存失败: ' + res.error); return; }
  }
  clearAreaDirty('variables');
  closeModal('modal-add-variable');
  loadPdVariables();
}
async function loadPdVariables() {
  const pid = configuratorPartId;
  const listEl = document.getElementById('pd-variables-list');
  if (!listEl || !pid) return;
  listEl.innerHTML = '<div class="empty-state"><div class="icon">⏳</div><p>加载变量列表...</p></div>';

  const res = await apiCall('GET', `part-variables/?part=${pid}`);
  const vars = res.error ? [] : (Array.isArray(res.data) ? res.data : (res.data.results || []));

  if (!vars.length) {
    listEl.innerHTML = '<div class="empty-state"><div class="icon">📐</div><p>暂未定义变量，点击上方"新建变量"添加</p></div>';
    return;
  }

  let html = `<table class="pd-bom-spreadsheet">
    <thead>
      <tr>
        <th style="width:22%"><span class="col-icon">📛</span>变量名</th>
        <th style="width:30%"><span class="col-icon">📐</span>公式</th>
        <th style="width:16%"><span class="col-icon">🔢</span>默认值</th>
        <th style="width:20%"><span class="col-icon">📝</span>描述</th>
        <th style="width:12%"><span class="col-icon">⚙️</span>操作</th>
      </tr>
    </thead>
    <tbody id="pv-tbody">`;
  vars.forEach((v, i) => {
    const escName = escHtml(v.name);
    const escFmla = escHtml(v.formula || '');
    const escDesc = escHtml(v.description || '');
    const computedVal = v.computed_value;
    const fmlaShort = (v.formula || '').length > 30 ? escHtml(v.formula.substring(0, 30) + '…') : escFmla;
    html += `<tr id="pv-row-${v.id}">
      <td ondblclick="pvEditCell(this, 'name')"><span class="pbs-name">${escName}</span></td>
      <td ondblclick="pvEditCell(this, 'formula')" title="双击编辑公式"><div class="pbs-formula-cell">${fmlaShort ? `<span class="fmla-text">${fmlaShort}</span>` : '<span class="fmla-empty">双击编辑公式</span>'}</div></td>
      <td><span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-xs font-mono font-medium ${computedVal != null ? 'bg-green-50 text-green-700 border border-green-200' : 'text-gray-400'}">${computedVal != null ? escHtml(String(computedVal)) : '—'}</span></td>
      <td ondblclick="pvEditCell(this, 'description')"><span class="pbs-ref">${escDesc || '<span class="text-gray-300 italic">—</span>'}</span></td>
      <td><button class="btn-ghost text-red-500 text-xs" onclick="pvDelete(${v.id}, '${escName.replace(/'/g, "\\'")}')" title="删除">🗑️</button></td>
    </tr>`;
  });
  html += '</tbody></table>';
  listEl.innerHTML = html;
}

function escHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

async function pvEditCell(td, field) {
  if (field === 'formula') {
    // Open modal for formula editing
    const vid = td.closest('tr')?.id?.replace('pv-row-', '');
    if (!vid) return;
    // Load variable data from API
    const res = await apiCall('GET', `part-variables/${vid}/`);
    if (res.error) return;
    const v = res.data;
    openEditVariableModal(v.id, v.name, v.formula || '', v.description || '');
    return;
  }
  // Inline editing for name and description
  if (td.querySelector('input')) return; // already editing
  const vid = td.closest('tr')?.id?.replace('pv-row-', '');
  if (!vid) return;
  // Get current value based on field
  let currentVal = '';
  if (field === 'name') {
    currentVal = td.textContent.trim();
  } else if (field === 'formula') {
    currentVal = td.querySelector('.fmla-text')?.textContent || '';
  } else {
    currentVal = td.textContent.replace(/[—\s]/g, '').trim();
  }
  // Create input
  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'input-field text-xs py-0.5 px-1 w-full';
  input.style.minWidth = '60px';
  input.value = currentVal;
  td.innerHTML = '';
  td.appendChild(input);
  input.focus();
  input.select();
  
  // Save on enter or blur
  const save = async () => {
    const val = input.value.trim();
    if (input.dataset.saving) return;
    // Get all current values for this variable
    const row = document.getElementById('pv-row-' + vid);
    const cells = row ? row.querySelectorAll('td') : [];
    let nameVal, fmlaVal, descVal;
    if (field === 'name') { nameVal = val; fmlaVal = cells[1]?.querySelector('input')?.value || cells[1]?.textContent.trim(); descVal = cells[3]?.querySelector('input')?.value || cells[3]?.textContent.trim(); }
    else if (field === 'formula') { nameVal = cells[0]?.querySelector('input')?.value || cells[0]?.textContent.trim(); fmlaVal = val; descVal = cells[3]?.querySelector('input')?.value || cells[3]?.textContent.trim(); }
    else { nameVal = cells[0]?.querySelector('input')?.value || cells[0]?.textContent.trim(); fmlaVal = cells[1]?.querySelector('input')?.value || cells[1]?.textContent.trim(); descVal = val; }
    // Check duplicate name
    const nameCheck = nameVal.trim();
    if (nameCheck) {
      const rowEls = document.querySelectorAll(`#pv-tbody tr`);
      for (const row of rowEls) {
        if (row.id === 'pv-row-' + vid) continue;
        const otherTds = row.querySelectorAll('td');
        const otherName = otherTds[0]?.textContent?.trim();
        if (otherName === nameCheck) {
          alert(`变量名「${nameCheck}」已存在，请使用不同的名称`);
          pvRestoreRow(vid, nameVal, fmlaVal, descVal);
          return;
        }
      }
    }
    input.dataset.saving = '1';
    // Restore display
    pvRestoreRow(vid, nameVal, fmlaVal, descVal);
    // Save to API
    const res = await apiCall('PATCH', `part-variables/${vid}/`, { name: nameVal, formula: fmlaVal, description: descVal });
    if (res.error) { alert('保存失败: ' + res.error); loadPdVariables(); return; }
    clearAreaDirty('variables');
  };
  input.addEventListener('blur', save);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { input.blur(); }
    if (e.key === 'Escape') { loadPdVariables(); }
  });
}

function pvRestoreRow(vid, name, formula, desc) {
  const row = document.getElementById('pv-row-' + vid);
  if (!row) return;
  const cells = row.querySelectorAll('td');
  if (cells.length >= 4) {
    // td0=name, td1=formula, td2=computed_value, td3=description, td4=actions
    cells[0].innerHTML = `<span class="pbs-name">${escHtml(name)}</span>`;
    const short = formula.length > 30 ? escHtml(formula.substring(0, 30) + '…') : escHtml(formula);
    if (formula) {
      cells[1].innerHTML = `<div class="pbs-formula-cell"><span class="fmla-text">${short}</span></div>`;
    } else {
      cells[1].innerHTML = '<div class="pbs-formula-cell"><span class="fmla-empty">双击编辑公式</span></div>';
    }
    // td2 (computed_value) is read-only — leave as-is after inline save
    cells[3].innerHTML = `<span class="pbs-ref">${escHtml(desc) || '<span class="text-gray-300 italic">—</span>'}</span>`;
  }
}

async function pvDelete(varId, varName) {
  if (!confirm(`确定删除变量「${varName}」？`)) return;
  const res = await apiCall('DELETE', `part-variables/${varId}/`);
  if (res.error) { alert('删除失败: ' + res.error); return; }
  loadPdVariables();
}

async function cfgLoadConfigs() {
  const pid = configuratorPartId;
  if (!pid) return;
  const listEl = document.getElementById('cfg-configs-list');
  const countEl = document.getElementById('cfg-config-count');
  const res = await apiCall('GET', `configurations/?part=${pid}`);
  if (res.error) return;
  const configs = res.data.results || (Array.isArray(res.data) ? res.data : []);
  if (countEl) countEl.textContent = configs.length;
  if (!configs.length) {
    listEl.innerHTML = '<div class="cfg-empty"><div class="cfg-empty-icon">📁</div>暂无保存的配置</div>';
    return;
  }
  let html = '';
  configs.forEach(c => {
    html += `<div class="cfg-saved-item" onclick="loadConfigParams(${c.id})" title="点击加载此配置">
      <div class="flex items-center justify-between">
        <span class="cfg-si-name">${c.title || c.name || `配置 #${c.id}`}</span>
        <button class="text-red-400 hover:text-red-600 text-xs p-1 rounded hover:bg-red-50 ml-2" onclick="event.stopPropagation();cfgDeleteConfig(${c.id})" title="删除此配置">✕</button>
      </div>
      <div class="cfg-si-meta">
        <span>${new Date(c.created_at || c.created || Date.now()).toLocaleDateString('zh-CN')}</span>
        <span>${Object.keys(c.parameters || {}).length} 个参数</span>
      </div>
    </div>`;
  });
  listEl.innerHTML = html;
}

async function cfgDeleteConfig(configId) {
  if (!confirm('确定删除此配置？')) return;
  const res = await apiCall('DELETE', `configurations/${configId}/`);
  if (!res.error) {
    setStatus('success', '✅ 配置已删除');
    await cfgLoadConfigs();
  } else {
    setStatus('error', `删除失败: ${res.data ? (res.data.error || res.data.detail || '未知错误') : '未知错误'}`);
  }
}

function loadConfigParams(configId) {
  // Load a saved config's parameters
  apiCall('GET', `configurations/${configId}/`).then(res => {
    if (res.error || !res.data) return;
    const params = res.data.parameters || {};
    cfgParams.forEach(c => {
      const name = c.name || `param_${c.id}`;
      if (params[name] !== undefined) {
        cfgParamValues[c.id] = String(params[name]);
      }
    });
    renderCfgParams();
    cfgExpandBOM();
    document.getElementById('cfg-status-dot').textContent = '● 已加载配置';
    setStatus('success', `✅ 已加载配置「${res.data.name || configId}」`);
  });
}

function pdTestFormula() {
  const formula = document.getElementById('pd-formula').value;
  const ctxRaw = document.getElementById('pd-fm-context').value;
  const resultDiv = document.getElementById('pd-fm-result');
  resultDiv.style.display = 'block';
  
  let context = {};
  try { context = ctxRaw ? JSON.parse(ctxRaw) : {}; } catch(e) { resultDiv.innerHTML = '<div class="action-result error">JSON 格式错误</div>'; return; }
  if (!formula.trim()) { resultDiv.innerHTML = '<div class="action-result error">请输入公式</div>'; return; }
  
  fetch('/api/parametric-bom/formula/preview/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
    credentials: 'same-origin',
    body: JSON.stringify({formula, context}),
  }).then(r => r.json()).then(data => {
    resultDiv.innerHTML = data.success
      ? `<div class="action-result success">✅ 结果: ${data.result}</div>`
      : `<div class="action-result error">❌ ${data.error}</div>`;
  }).catch(e => {
    resultDiv.innerHTML = `<div class="action-result error">网络错误: ${e.message}</div>`;
  });
}

function pdValidateFormula() {
  const formula = document.getElementById('pd-formula').value;
  const resultDiv = document.getElementById('pd-fm-result');
  resultDiv.style.display = 'block';
  if (!formula.trim()) { resultDiv.innerHTML = '<div class="action-result error">请输入公式</div>'; return; }
  
  fetch('/api/parametric-bom/formula/validate/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
    credentials: 'same-origin',
    body: JSON.stringify({formula}),
  }).then(r => r.json()).then(data => {
    resultDiv.innerHTML = data.valid
      ? '<div class="action-result success">✅ 公式语法正确</div>'
      : `<div class="action-result error">❌ ${data.error || '语法错误'}</div>`;
  }).catch(e => {
    resultDiv.innerHTML = `<div class="action-result error">网络错误: ${e.message}</div>`;
  });
}

// ===== PRODUCT DETAIL: Template List =====
// ── Category filter state ──
let _tplCategoryFilter = 'all';

// Infer template category from name + units
function inferTplCategory(tpl) {
  const name = (tpl.name || '').toLowerCase();
  const units = (tpl.units || '').toLowerCase();
  // Common (常用) patterns
  const commonNames = ['长度','宽度','高度','厚度','直径','材质','颜色','数量','重量','型号','规格'];
  if (commonNames.some(k => name.includes(k))) return '常用';
  // Numeric patterns
  const numUnits = ['mm','cm','m','kg','g','n','kn','mpa','hz','rpm','°','℃','l','ml','㎡','m³'];
  if (numUnits.some(u => units.includes(u))) return '数值';
  if (['长度','宽度','高度','厚度','直径','数量','重量','面积','体积','密度','功率','速度','压力','温度','角度'].some(k => name.includes(k))) return '数值';
  // Option patterns
  if (['材质','颜色','型号','规格','类型','等级','状态','方式','方向','位置'].some(k => name.includes(k))) return '选项';
  // Boolean patterns
  if (['是否','有无','需要','启用','允许','包含'].some(k => name.includes(k))) return '布尔';
  // Text patterns
  if (['备注','说明','描述','名称','编号','编码','注释'].some(k => name.includes(k))) return '文本';
  return '数值'; // default
}

function onTplCategoryFilter(cat) {
  _tplCategoryFilter = cat;
  document.querySelectorAll('#pd-tpl-categories .tpl-cat-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.cat === cat);
  });
}

// Template list rendering is no longer used — replaced by type buttons
function renderPdTemplateList() {}

let _quickAddTplId = null;

async function quickAddTemplate(tplId, tplName) {
  const partId = configuratorPartId;
  if (!partId) { setStatus('error', '请先选择产品'); return; }
  
  // Check duplicate
  const configs = window.__paramConfigs || [];
  if (configs.some(c => c.template === tplId)) {
    setStatus('error', `❌ 「${tplName}」已存在`);
    return;
  }
  
  // Smart default type based on name keywords
  const name = (tplName || '').toLowerCase();
  let defaultType = 'number';
  if (name.includes('颜色') || name.includes('材质') || name.includes('型号') || name.includes('规格')) {
    defaultType = 'option';
  } else if (name.includes('布尔') || name.includes('是否') || name.includes('有无') || name.includes('需要')) {
    defaultType = 'boolean';
  }
  
  setStatus('loading', `正在添加「${tplName}」...`);
  
  const body = {
    part: parseInt(partId),
    template: tplId,
    parameter_type: defaultType,
    is_driving: true,
    is_computed: false,
    display_order: 100,
  };
  
  const res = await apiCall('POST', 'part-config/', body);
  if (!res.error) {
    setStatus('success', `✅ 已添加「${tplName}」`);
    loadPdParams();
  } else {
    setStatus('error', `添加失败: ${res.error}`);
  }
}

function onQuickParamTypeChange() {
  const type = document.getElementById('qp-type').value;
  document.getElementById('qp-num-fields').style.display = (type === 'number') ? 'grid' : 'none';
  document.getElementById('qp-options-group').style.display = (type === 'option' || type === 'multi_option') ? 'block' : 'none';
  document.getElementById('qp-boolean-group').style.display = (type === 'boolean') ? 'block' : 'none';
}

async function quickAddParam() {
  const tplId = _quickAddTplId;
  const partId = configuratorPartId;
  if (!partId || !tplId) { setStatus('error', '参数错误'); return; }
  
  const type = document.getElementById('qp-type').value;
  const body = {
    part: parseInt(partId),
    template: tplId,
    parameter_type: type,
    default_value: type === 'boolean' ? document.getElementById('qp-boolean-default').value : document.getElementById('qp-default').value,
    min_value: (type === 'number' && document.getElementById('qp-min').value) ? parseFloat(document.getElementById('qp-min').value) : null,
    max_value: (type === 'number' && document.getElementById('qp-max').value) ? parseFloat(document.getElementById('qp-max').value) : null,
    step_value: (type === 'number' && document.getElementById('qp-step').value) ? parseFloat(document.getElementById('qp-step').value) : null,
    options: (type === 'option' || type === 'multi_option') ? document.getElementById('qp-options').value.split(',').map(s=>s.trim()).filter(Boolean) : null,
    is_driving: document.getElementById('qp-driving').checked,
    is_computed: document.getElementById('qp-computed').checked,
    computation_formula: document.getElementById('qp-formula').value || '',
    display_order: 100,
  };
  
  const tpl = templates.find(t => t.pk == tplId);
  const tplName = tpl ? tpl.name : '';
  setStatus('loading', `正在添加「${tplName}」...`);
  
  const res = await apiCall('POST', 'part-config/', body);
  if (!res.error) {
    setStatus('success', `✅ 已添加「${tplName}」`);
    closeModal('modal-quick-param');
    _quickAddTplId = null;
    loadPdParams();
  } else {
    setStatus('error', `添加失败: ${res.error}`);
  }
}

async function addTemplateToProduct(templateId, templateName) {
  const partId = configuratorPartId;
  if (!partId) { setStatus('error', '请先选择产品'); return; }
  
  // Check for duplicates using current config list
  const configs = window.__paramConfigs || [];
  const isDuplicate = configs.some(c => c.template === templateId);
  if (isDuplicate) {
    setStatus('error', `❌ 「${templateName}」已存在，不能重复添加`);
    return;
  }
  
  setStatus('loading', `正在添加「${templateName}」...`);
  const body = {
    part: parseInt(partId),
    template: templateId,
    parameter_type: 'number',
    is_driving: true,
    is_computed: false,
    display_order: 100,
  };
  
  const res = await apiCall('POST', 'part-config/', body);
  if (!res.error) {
    setStatus('success', `✅ 已添加「${templateName}」`);
    loadPdParams();
  } else {
    setStatus('error', `添加失败: ${res.error}`);
  }
}

function onTplDragStart(event, tplId, tplName) {
  event.dataTransfer.setData('text/plain', JSON.stringify({tplId, tplName}));
  event.dataTransfer.effectAllowed = 'copy';
}

// Set up drop target on canvas for type drag
document.addEventListener('DOMContentLoaded', function() {
  const canvasDrop = document.getElementById('pd-params-canvas');
  if (canvasDrop) {
    let ghostEl = null; // floating badge
    let typeLabels = {number:'🔢数值', option:'🔘选项', boolean:'☑️布尔', text:'📝文本', multi_option:'☑️多选', long_text:'📄长文本'};

    canvasDrop.addEventListener('dragover', function(e) {
      e.preventDefault();
      if (!e.dataTransfer.types) return;

      // Add visual hover state to canvas
      this.classList.add('drag-hover', 'drag-active');

      // Create or reposition floating ghost badge
      if (!ghostEl) {
        ghostEl = document.createElement('div');
        ghostEl.className = 'drag-ghost';
        document.body.appendChild(ghostEl);
      }
      try {
        const raw = e.dataTransfer.getData('text/plain');
        const data = JSON.parse(raw);
        const type = data.type || data.tplType;
        if (type && typeLabels[type]) {
          ghostEl.textContent = typeLabels[type];
          ghostEl.className = 'drag-ghost type-' + type;
        } else if (type) {
          ghostEl.textContent = '➕' + type;
          ghostEl.className = 'drag-ghost';
        } else {
          ghostEl.textContent = '➕新建';
        }
      } catch(e) {
        ghostEl.textContent = '➕新建';
      }
      ghostEl.style.left = e.clientX + 'px';
      ghostEl.style.top = e.clientY + 'px';
      ghostEl.style.display = 'flex';

      // Show insert indicator + card highlighting
      const indicator = document.getElementById('drop-indicator') || (() => {
        const el = document.createElement('div');
        el.id = 'drop-indicator';
        this.appendChild(el);
        return el;
      })();
      const cards = this.querySelectorAll('.param-card');
      let found = false;
      cards.forEach(c => c.classList.remove('drop-before', 'drop-after'));
      for (const card of cards) {
        const rect = card.getBoundingClientRect();
        const mid = rect.top + rect.height / 2;
        if (e.clientY < mid) {
          card.classList.add('drop-before');
          card.before(indicator);
          found = true;
          break;
        }
      }
      if (!found) {
        this.appendChild(indicator);
        const lastCard = cards[cards.length - 1];
        if (lastCard) lastCard.classList.add('drop-after');
      }
      indicator.style.display = 'flex';
    });

    canvasDrop.addEventListener('dragleave', function(e) {
      // Only clear if actually leaving the canvas (not entering a child)
      if (!this.contains(e.relatedTarget)) {
        this.classList.remove('drag-hover', 'drag-type-hover', 'drag-active');
        if (ghostEl) { ghostEl.style.display = 'none'; }
        const ind = document.getElementById('drop-indicator');
        if (ind) ind.style.display = 'none';
        this.querySelectorAll('.param-card').forEach(c =>
          c.classList.remove('drop-before', 'drop-after'));
      }
    });

    canvasDrop.addEventListener('drop', async function(e) {
      e.preventDefault();
      this.classList.remove('drag-hover', 'drag-active');
      if (ghostEl) { ghostEl.style.display = 'none'; }
      this.querySelectorAll('.param-card').forEach(c =>
        c.classList.remove('drop-before', 'drop-after'));

      const ind = document.getElementById('drop-indicator');
      if (ind) ind.remove();

      try {
        const data = JSON.parse(e.dataTransfer.getData('text/plain'));
        if (data && data.tplId) {
          quickAddTemplate(data.tplId, data.tplName);
        } else if (data && data.type) {
          const insertBeforeId = getInsertPosition(e.clientY);
          addIndependentParam(data.type, insertBeforeId);
        }
      } catch(err) {}
    });

    // Global mouse move to update ghost position even when not over canvas
    document.addEventListener('dragover', function(e) {
      if (ghostEl && ghostEl.style.display !== 'none') {
        ghostEl.style.left = e.clientX + 'px';
        ghostEl.style.top = e.clientY + 'px';
      }
    });

    // Clean up ghost on drag end
    document.addEventListener('dragend', function() {
      if (ghostEl) { ghostEl.remove(); ghostEl = null; }
      const ind = document.getElementById('drop-indicator');
      if (ind) ind.style.display = 'none';
      if (canvasDrop) {
        canvasDrop.classList.remove('drag-hover', 'drag-active');
        canvasDrop.querySelectorAll('.param-card').forEach(c =>
          c.classList.remove('drop-before', 'drop-after'));
      }
    });
  }
});

/**
 * Determine where to insert a new param based on mouse Y position
 * Returns: config ID to insert before, or null to append at end
 */
function getInsertPosition(mouseY) {
  const cards = document.querySelectorAll('#pd-params-canvas .param-card');
  if (!cards.length) return null;
  
  const canvas = document.getElementById('pd-params-canvas');
  const canvasRect = canvas.getBoundingClientRect();
  const relY = mouseY - canvasRect.top;
  
  for (const card of cards) {
    const rect = card.getBoundingClientRect();
    const cardTop = rect.top - canvasRect.top;
    const cardMid = cardTop + rect.height / 2;
    if (relY < cardMid) {
      return parseInt(card.dataset.configId);
    }
  }
  return null; // append at end
}

// ── Independent Param: create template + config in one shot ──
let _paramCounter = {};

async function addIndependentParam(type, insertBeforeId) {
  const partId = configuratorPartId;
  if (!partId) { setStatus('error', '请先选择产品'); return; }

  // Generate unique name
  if (!_paramCounter[type]) _paramCounter[type] = 0;
  _paramCounter[type]++;
  const typeLabels = {number:'数值', option:'选项', boolean:'布尔', text:'文本', multi_option:'多选', long_text:'长文本'};
  const label = typeLabels[type] || type;
  const paramName = `${label}参数${_paramCounter[type]}`;

  // Calculate display_order based on insert position
  let displayOrder = 100;
  if (insertBeforeId && window.__paramConfigs) {
    const configs = window.__paramConfigs.sort((a,b)=>(a.display_order||0)-(b.display_order||0));
    const idx = configs.findIndex(c => c.id === insertBeforeId);
    if (idx > 0) {
      // Between previous and target
      const prev = configs[idx - 1].display_order || 0;
      const next = configs[idx].display_order || 100;
      displayOrder = Math.round((prev + next) / 2);
      // If no space, re-number
      if (displayOrder <= prev) displayOrder = prev + 5;
    } else if (idx === 0) {
      // Insert before first
      displayOrder = Math.round((configs[0].display_order || 100) / 2) - 5;
      if (displayOrder < 0) displayOrder = 5;
    }
    // else idx === -1, append at end (default 100)
  }

  setStatus('loading', `正在创建「${paramName}」...`);

  const body = {
    part: parseInt(partId),
    name: paramName,
    parameter_type: type,
    is_driving: true,
    is_computed: false,
    display_order: displayOrder,
  };

  const res = await apiCall('POST', 'part-config/', body);
  if (!res.error) {
    setStatus('success', `✅ 已创建「${paramName}」`);
    // Insert at correct position in local array
    if (window.__paramConfigs && insertBeforeId) {
      const idx = window.__paramConfigs.findIndex(c => c.id === insertBeforeId);
      if (idx >= 0) {
        window.__paramConfigs.splice(idx, 0, res.data);
      } else {
        window.__paramConfigs.push(res.data);
      }
    } else {
      if (!window.__paramConfigs) window.__paramConfigs = [];
      window.__paramConfigs.push(res.data);
    }
    // Re-sort and re-render
    const sorted = window.__paramConfigs.sort((a,b)=>(a.display_order||0)-(b.display_order||0));
    const canvas = document.getElementById('pd-params-canvas');
    const countBadge = document.getElementById('pd-param-count');
    canvas.innerHTML = sorted.map((c,i)=>renderParamCard(c,i)).join('');
    if (countBadge) countBadge.textContent = `${sorted.length} 个参数`;
  } else {
    setStatus('error', `创建失败: ${res.error}`);
    _paramCounter[type]--;
  }
}

function onTypeDragStart(event, type) {
  event.dataTransfer.setData('text/plain', JSON.stringify({type}));
  event.dataTransfer.effectAllowed = 'copy';
}

// ── Rename parameter name inline ──
function startRenameParam(cfgId) {
  const nameEl = document.getElementById(`pc-name-${cfgId}`);
  if (!nameEl) return;
  const currentName = nameEl.textContent.trim();
  
  nameEl.contentEditable = true;
  nameEl.focus();
  
  const range = document.createRange();
  range.selectNodeContents(nameEl);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  
  nameEl.onblur = () => finishRename(cfgId, nameEl);
  nameEl.onkeydown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); nameEl.blur(); }
    if (e.key === 'Escape') { nameEl.textContent = currentName; nameEl.blur(); }
  };
}

async function finishRename(cfgId, el) {
  el.contentEditable = false;
  el.onblur = null;
  el.onkeydown = null;
  
  const newName = el.textContent.trim();
  if (!newName) return;
  
  markDirty(cfgId, {name: newName});
  setStatus('success', `✏️ 已记录重命名为「${newName}」，点击「💾 保存」提交`);
}

function clearActiveProduct() {
  configuratorPartId = null;
  
  // Update selectors
  const selectors = ['cfg-part-select', 'pm-part-select', 'bom-part-select'];
  selectors.forEach(id => {
    const sel = document.getElementById(id);
    if (sel) sel.value = '';
  });
  
  // Re-render grid
  renderProductGrid();
  
  switchPage('products');
  setStatus('success', '已取消产品选择');
}

// ===== TYPE BADGE HELPER =====
function typeBadge(type) {
  const labels = {number:'数值', option:'选项', boolean:'布尔', text:'文本', multi_option:'多选项', long_text:'长文本', file_ref:'文件', part_ref:'零件'};
  return `<span class="type-badge type-${type}">${labels[type]||type}</span>`;
}

// ===== PARAM TYPE-AWARE INPUT RENDER =====
function renderTypeAwareInput(cfg, paramName, defVal) {
  const type = cfg.parameter_type || 'number';
  const options = cfg.options;
  const minVal = cfg.min_value != null ? cfg.min_value : 0;
  const maxVal = cfg.max_value != null ? cfg.max_value : 100;
  const hint = cfg.ui_hint ? `<span class="text-xs text-gray-400 block mt-0.5">${cfg.ui_hint}</span>` : '';

  switch(type) {
    case 'number':
      const sliderId = `cfg-slider-${paramName.replace(/\\s+/g,'_')}`;
      const numId = `cfg-num-${paramName.replace(/\\s+/g,'_')}`;
      const step = cfg.step_value != null ? cfg.step_value : ((maxVal - minVal) > 100 ? 'any' : '1');
      return `<div class="param-group">
        <div class="param-label">
          <span>${paramName} ${typeBadge(type)}</span>
          <span class="param-value-display" id="${sliderId}-val">${defVal}</span>
        </div>
        <div class="slider-row">
          <input type="range" id="${sliderId}" min="${minVal}" max="${maxVal}" step="${step}" value="${defVal}"
            oninput="syncCfgSlider('${sliderId}','${numId}','${paramName}')">
          <input type="number" id="${numId}" min="${minVal}" max="${maxVal}" step="${step}" value="${defVal}"
            oninput="syncCfgNum('${sliderId}','${numId}','${paramName}')">
        </div>
        <div class="param-range-hint">
          <span>最小: ${minVal}</span>
          <span>步长: ${cfg.step_value != null ? cfg.step_value : ((maxVal - minVal) > 100 ? '自动' : '1')}</span>
          <span>最大: ${maxVal}</span>
        </div>
        ${hint}
      </div>`;

    case 'option':
      let opts = options;
      if (typeof opts === 'string') { try { opts = JSON.parse(opts); } catch(e) { opts = opts.split(',').map(s=>s.trim()); } }
      if (!Array.isArray(opts)) opts = [];
      return `<div class="param-group">
        <div class="param-label">
          <span>${paramName} ${typeBadge(type)}</span>
        </div>
        <select class="input-field" data-param="${paramName}" onchange="updateCfgParam(this)">
          ${opts.map(opt => `<option value="${opt}"${opt===defVal?' selected':''}>${opt}</option>`).join('')}
        </select>
        ${hint}
      </div>`;

    case 'multi_option':
      let mopts = options;
      if (typeof mopts === 'string') { try { mopts = JSON.parse(mopts); } catch(e) { mopts = mopts.split(',').map(s=>s.trim()); } }
      if (!Array.isArray(mopts)) mopts = [];
      const selected = defVal ? defVal.split(',').map(s=>s.trim()) : [];
      return `<div class="param-group">
        <div class="param-label">
          <span>${paramName} ${typeBadge(type)}</span>
          <span class="text-xs text-gray-400" id="cfg-multi-${paramName}-count">${selected.length} 已选</span>
        </div>
        <div class="checkbox-grid" data-param="${paramName}">
          ${mopts.map(opt => `<label class="${selected.includes(opt)?'checked':''}" onclick="toggleCfgMultiOption(this,'${paramName}')">
            <input type="checkbox" ${selected.includes(opt)?'checked':''} style="display:none"> ${opt}
          </label>`).join('')}
        </div>
        ${hint}
      </div>`;

    case 'boolean':
      const isTrue = defVal === 'true' || defVal === true || defVal === '1' || defVal === 1 || defVal === '是';
      return `<div class="param-group">
        <div class="param-label">
          <span>${paramName} ${typeBadge(type)}</span>
        </div>
        <div class="toggle-wrap" onclick="toggleCfgBoolean(this,'${paramName}')">
          <div class="toggle-track ${isTrue?'on':''}"><div class="toggle-thumb"></div></div>
          <span class="toggle-label" id="cfg-bool-${paramName}-label">${isTrue ? 'ON' : 'OFF'}</span>
        </div>
        ${hint}
      </div>`;

    case 'text':
      return `<div class="param-group">
        <div class="param-label">
          <span>${paramName} ${typeBadge(type)}</span>
        </div>
        <input class="input-field" data-param="${paramName}" value="${defVal||''}" onchange="updateCfgParam(this)" placeholder="输入文本...">
        ${hint}
      </div>`;

    case 'long_text':
      return `<div class="param-group">
        <div class="param-label">
          <span>${paramName} ${typeBadge(type)}</span>
        </div>
        <textarea class="input-field" data-param="${paramName}" onchange="updateCfgParam(this)" rows="3" placeholder="输入长文本...">${defVal||''}</textarea>
        ${hint}
      </div>`;

    case 'file_ref':
      return `<div class="param-group">
        <div class="param-label">
          <span>${paramName} ${typeBadge(type)}</span>
          <span class="text-xs text-gray-400" id="cfg-file-${paramName}-name">${defVal||'未选择'}</span>
        </div>
        <div class="flex gap-2">
          <input type="file" class="input-field" data-param="${paramName}" style="padding:0.25rem" onchange="updateCfgFileParam(this,'${paramName}')">
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('cfg-file-${paramName}-name').textContent='未选择';currentParams['${paramName}'].value=''">清除</button>
        </div>
        ${hint}
      </div>`;

    case 'part_ref':
      return `<div class="param-group">
        <div class="param-label">
          <span>${paramName} ${typeBadge(type)}</span>
        </div>
        <select class="input-field" data-param="${paramName}" onchange="updateCfgParam(this)">
          <option value="">-- 选择零件 --</option>
          ${parts.map(p => `<option value="${p.pk}"${String(p.pk)===String(defVal)?' selected':''}>${p.name||'Unnamed'} (ID:${p.pk})</option>`).join('')}
        </select>
        ${hint}
      </div>`;

    default:
      return `<div class="param-group">
        <div class="param-label">
          <span>${paramName} ${typeBadge(type)}</span>
        </div>
        <input class="input-field" data-param="${paramName}" value="${defVal||''}" onchange="updateCfgParam(this)">
        ${hint}
      </div>`;
  }
}

// ===== CONFIGURATOR PARAM HANDLERS =====
function syncCfgSlider(sliderId, numId, paramName) {
  const slider = document.getElementById(sliderId);
  const num = document.getElementById(numId);
  if (!slider || !num) return;
  num.value = slider.value;
  const valEl = document.getElementById(`${sliderId}-val`);
  if (valEl) valEl.textContent = slider.value;
  if (currentParams[paramName]) currentParams[paramName].value = slider.value;
}

function syncCfgNum(sliderId, numId, paramName) {
  const slider = document.getElementById(sliderId);
  const num = document.getElementById(numId);
  if (!slider || !num) return;
  slider.value = num.value;
  const valEl = document.getElementById(`${sliderId}-val`);
  if (valEl) valEl.textContent = num.value;
  if (currentParams[paramName]) currentParams[paramName].value = num.value;
}

function updateCfgParam(el) {
  const name = el.dataset.param;
  if (currentParams[name]) currentParams[name].value = el.value;
}

function updateCfgFileParam(el, name) {
  const file = el.files[0];
  if (file) {
    document.getElementById(`cfg-file-${name}-name`).textContent = file.name;
    if (currentParams[name]) currentParams[name].value = file.name;
  }
}

function toggleCfgMultiOption(label, paramName) {
  label.classList.toggle('checked');
  const cb = label.querySelector('input[type="checkbox"]');
  if (cb) cb.checked = !cb.checked;
  // Collect selected values
  const grid = label.closest('.checkbox-grid');
  const selected = Array.from(grid.querySelectorAll('label.checked')).map(l => l.textContent.trim());
  document.getElementById(`cfg-multi-${paramName}-count`).textContent = selected.length + ' 已选';
  if (currentParams[paramName]) currentParams[paramName].value = selected.join(',');
}

function toggleCfgBoolean(wrap, paramName) {
  const track = wrap.querySelector('.toggle-track');
  const label = wrap.querySelector('.toggle-label');
  track.classList.toggle('on');
  const isOn = track.classList.contains('on');
  label.textContent = isOn ? 'ON' : 'OFF';
  if (currentParams[paramName]) currentParams[paramName].value = isOn ? 'true' : 'false';
}

// ===== CONFIGURATOR: Select Part =====
async function onConfigPartChange(partId) {
  if (!partId) {
    document.getElementById('cfg-params-card').style.display = 'none';
    document.getElementById('cfg-part-info').innerHTML = '';
    document.getElementById('cfg-to-step2').disabled = true;
    configuratorPartId = null;
    currentPartInfo = null;
    document.getElementById('cfg-part-name-bar').textContent = '';
    return;
  }
  configuratorPartId = parseInt(partId);
  document.getElementById('cfg-to-step2').disabled = true;
  
  const part = parts.find(p => p.pk == partId);
  currentPartInfo = part;
  if (part) {
    document.getElementById('cfg-part-name-bar').textContent = part.name || '';
    document.getElementById('cfg-part-info').innerHTML = `
      <div class="part-info">
        <div class="icon">📦</div>
        <div class="info-text">
          <div class="name">${part.name || '未命名产品'}</div>
          ${part.description ? `<div class="desc">${part.description}</div>` : ''}
          <div class="meta">ID: ${part.pk} ${part.category_name ? '· ' + part.category_name : ''}</div>
        </div>
      </div>`;
  }
  await loadConfiguratorParams(configuratorPartId);
}

async function loadConfiguratorParams(partId) {
  const container = document.getElementById('cfg-param-fields');
  const computedArea = document.getElementById('cfg-computed-area');
  container.innerHTML = '<div class="flex items-center justify-center py-6"><span class="spinner mr-2"></span><span class="text-sm text-gray-400">加载参数中...</span></div>';
  computedArea.style.display = 'none';
  computedArea.innerHTML = '';
  
  const res = await apiCall('GET', `part-config/?part=${partId}`);
  if (res.error) {
    container.innerHTML = '<div class="text-red-500 text-sm p-3">❌ 加载参数失败</div>';
    return;
  }
  
  const configs = res.data.results || (Array.isArray(res.data) ? res.data : []);
  currentParams = {};
  currentParamConfigs = configs;
  
  const sorted = (configs || []).sort((a,b) => (a.display_order||0) - (b.display_order||0));
  let drivingHtml = '';
  let computedHtml = '';
  let hasDriving = false;
  let hasComputed = false;
  
  sorted.forEach(cfg => {
    const tplName = cfg.template_name || `param_${cfg.template}`;
    
    if (cfg.is_computed) {
      hasComputed = true;
      const val = cfg.default_value || '';
      computedHtml += `<div class="computed-item">
        <div>
          <span>${tplName}</span>
          ${cfg.computation_formula ? `<span class="formula">${cfg.computation_formula}</span>` : ''}
        </div>
        <span class="value">${val}</span>
      </div>`;
      currentParams[tplName] = {value: val, isComputed: true, config: cfg};
    } else if (cfg.is_driving || cfg.is_driving === undefined) {
      hasDriving = true;
      const defVal = cfg.default_value != null ? cfg.default_value : '';
      
      // Render type-aware input
      drivingHtml += renderTypeAwareInput(cfg, tplName, defVal);
      currentParams[tplName] = {value: defVal, isComputed: false, config: cfg};
    }
  });
  
  if (hasDriving) {
    document.getElementById('cfg-params-card').style.display = 'block';
    container.innerHTML = drivingHtml;
    document.getElementById('cfg-to-step2').disabled = false;
  } else {
    document.getElementById('cfg-params-card').style.display = 'block';
    container.innerHTML = '<div class="empty-state"><div class="icon">📝</div><p>该产品没有可配置的驱动参数</p></div>';
    document.getElementById('cfg-to-step2').disabled = true;
  }
  
  if (hasComputed) {
    computedArea.style.display = 'block';
    computedArea.innerHTML = `<div class="computed-section">
      <div class="section-title">🔢 自动计算 <span class="text-xs text-gray-400 font-normal">(只读)</span></div>
      ${computedHtml}
    </div>`;
  }
}

// ===== CONFIGURATOR: BOM Expand & Cost =====
async function expandConfigBOM() {
  if (!configuratorPartId) { setStatus('error', '请先选择产品'); return; }
  
  const btn = document.getElementById('cfg-to-step2');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner mr-1"></span>计算中...';
  
  const params = {};
  Object.entries(currentParams).forEach(([k,v]) => { if (!v.isComputed) params[k] = v.value; });
  
  const res = await apiCall('POST', 'evaluate/', {part_id: configuratorPartId, parameters: params});
  
  btn.disabled = false;
  btn.innerHTML = '展开BOM →';
  
  if (res.error) {
    document.getElementById('cfg-bom-results').innerHTML = `<div class="text-red-500 text-sm p-4 bg-red-50 rounded-lg">❌ BOM展开失败: ${JSON.stringify(res.data).substring(0,200)}</div>`;
    return;
  }
  
  currentBOMResult = res.data;
  renderBOMTree(res.data, 'cfg-bom-results');
  document.getElementById('cfg-cost-card').style.display = 'block';
  await estimateConfigCost(false);
  goConfigStep(2);
  document.getElementById('cfg-to-step3').disabled = false;
  // Show cart button
  var cartBtn = document.getElementById('cfg-cart-btn');
  if (cartBtn) cartBtn.style.display = '';
}

function renderBOMTree(data, containerId) {
  const container = document.getElementById(containerId);
  if (!data || (!data.bom_tree && !data.items && !Array.isArray(data))) {
    container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>无BOM数据</p></div>';
    return;
  }
  const tree = data.bom_tree || data.items || data;
  let html = '';
  if (data.part_name) {
    html += `<div class="flex items-center gap-2 pb-2 mb-2 border-b border-gray-100">
      <span class="text-lg">📦</span>
      <span class="font-semibold text-sm text-gray-800">${data.part_name}</span>
      ${data.total_qty != null ? `<span class="text-xs text-gray-400">×${data.total_qty}</span>` : ''}
    </div>`;
  }
  if (Array.isArray(tree)) {
    tree.forEach(item => renderTreeItem(item, 0, (h) => { html += h; }));
  } else if (typeof tree === 'object') {
    renderTreeItem(tree, 0, (h) => { html += h; });
  }
  container.innerHTML = html || '<div class="empty-state"><div class="icon">📭</div><p>无BOM数据</p></div>';
}

function renderTreeItem(item, depth, push) {
  const isExcluded = item.excluded || item.condition_met === false;
  const hasError = item.error || (item.errors && item.errors.length > 0);
  const mode = item.mode || 'standard';
  const isParametric = item.parametric || mode !== 'standard' || item.qty_formula || item.condition_formula;
  const depthClass = `tree-depth-${Math.min(depth, 9)}`;
  let badgeClass = isExcluded ? 'badge-red' : (hasError ? 'badge-yellow' : (isParametric ? 'badge-blue' : 'badge-gray'));
  let badgeText = isExcluded ? '已排除' : (hasError ? '错误' : (isParametric ? '参数化' : '静态'));
  const qty = item.calculated_quantity != null ? item.calculated_quantity : (item.quantity != null ? item.quantity : '');
  const partName = item.actual_part_name || item.selected_candidate_part_name || item.variant_part_name || item.part_name || item.sub_part_name || item.name || '未知部件';
  let extraHtml = '';

  // Mode-specific display
  const modeLabels = {standard:'标准', qty_formula:'数量公式', conditional:'条件包含', candidate:'🎯候选', variant:'🧬动态', specification:'📝规格', structure:'结构'};
  if (mode !== 'standard') {
    extraHtml += `<span class="text-[10px] px-1 py-0.5 rounded bg-gray-100 text-gray-600 ml-1">${modeLabels[mode]||mode}</span>`;
  }

  // Candidate mode: show selection
  if (mode === 'candidate' && item.candidates_considered) {
    const matched = item.candidates_considered.filter(c => c.matched).map(c => c.part_name);
    extraHtml += `<span class="text-xs text-emerald-600 ml-1">候选: ${item.selected_candidate_part_name || '无匹配'}</span>`;
  }

  // Variant mode: show generated variant
  if (mode === 'variant') {
    if (item.variant_part_name) {
      extraHtml += `<span class="text-xs text-indigo-600 ml-1">→ ${item.variant_part_name}${item.variant_generated ? ' 🆕' : ''}</span>`;
    } else if (item.variant_computed_name) {
      extraHtml += `<span class="text-xs text-indigo-400 ml-1">→ ${item.variant_computed_name}</span>`;
    }
  }

  // Specification mode: show fields
  if (mode === 'specification' && item.spec_fields_evaluated) {
    const specs = item.spec_fields_evaluated.map(f => `${f.name}=${f.value}${f.unit||''}`).join(', ');
    extraHtml += `<span class="text-xs text-amber-600 ml-1">${specs}</span>`;
    if (item.unit_cost != null) {
      extraHtml += `<span class="text-xs text-gray-500 ml-1">¥${item.unit_cost}</span>`;
    }
  }



  // Errors
  if (item.errors && item.errors.length > 0) {
    extraHtml += `<span class="text-red-500 text-[10px] ml-1" title="${item.errors.join('; ')}">⚠️</span>`;
  }

  const partId = item.actual_part_id || item.part_id;

  push(`<div class="tree-item ${depthClass}">
    <span class="qty-badge ${badgeClass}">${badgeText}</span>
    <span class="qty-badge bg-gray-100 text-gray-700" style="min-width:auto">×${qty}</span>
    <span class="part-name${partId ? ' clickable-part' : ''}"${partId ? ` onclick="openPartDetail(${partId})" title="点击查看零件详情"` : ''}>${depth > 0 ? '└ ' : ''}${partName}</span>
    ${extraHtml}
    ${item.qty_formula ? `<span class="formula-text">数量:${item.qty_formula}</span>` : ''}
    ${item.condition_formula ? `<span class="formula-text">条件:${item.condition_formula}</span>` : ''}
    ${item.unit_price != null ? `<span class="text-[10px] text-emerald-600 ml-1">¥${Number(item.unit_price).toFixed(2)}/个</span>` : ''}
    ${item.total_price != null ? `<span class="text-[10px] text-emerald-700 font-medium ml-1">=¥${Number(item.total_price).toFixed(2)}</span>` : ''}
    ${isExcluded ? `<span class="excluded-label">已排除</span>` : ''}
  </div>`);
  if (item.children && Array.isArray(item.children)) {
    item.children.forEach(child => renderTreeItem(child, depth + 1, push));
  }
  if (item.sub_items && Array.isArray(item.sub_items)) {
    item.sub_items.forEach(child => renderTreeItem(child, depth + 1, push));
  }
}

async function estimateConfigCost(withMarkup) {
  if (!configuratorPartId) { setStatus('error', '请先选择产品'); return; }
  const params = {};
  Object.entries(currentParams).forEach(([k,v]) => { if (!v.isComputed) params[k] = v.value; });
  const body = {part_id: configuratorPartId, parameters: params};
  if (withMarkup) body.markup_pct = 15;
  const res = await apiCall('POST', 'estimate-cost/', body);
  if (res.error) {
    document.getElementById('cfg-cost-results').innerHTML = '<div class="text-red-500 text-sm">❌ 成本估算失败</div>';
    return;
  }
  currentCostResult = res.data;
  renderCostSummary(res.data, 'cfg-cost-results');
}

function renderCostSummary(data, containerId) {
  const container = document.getElementById(containerId);
  let html = `<div class="cost-summary">
    <div class="cost-card total">
      <div class="label">总成本</div>
      <div class="value">¥${Number(data.total_cost||0).toFixed(2)}</div>
    </div>
    <div class="cost-card">
      <div class="label">基础成本</div>
      <div class="value">¥${Number(data.total_cost_before_markup||0).toFixed(2)}</div>
    </div>
    <div class="cost-card">
      <div class="label">加价率</div>
      <div class="value">${data.markup_pct||0}%</div>
    </div>
    <div class="cost-card">
      <div class="label">部件数</div>
      <div class="value">${data.item_count||0}</div>
    </div>
  </div>`;
  html += `<div class="flex justify-end mt-2">
    <button class="btn btn-secondary btn-sm" onclick="showCostDetail()">查看明细</button>
  </div>`;
  container.innerHTML = html;
}

function showCostDetail() {
  const data = currentCostResult;
  if (!data) { setStatus('error', '无成本数据'); return; }
  const container = document.getElementById('cost-detail-content');
  let html = '<div class="cost-summary">';
  html += `<div class="cost-card total"><div class="label">总成本</div><div class="value">¥${Number(data.total_cost||0).toFixed(2)}</div></div>`;
  html += `<div class="cost-card"><div class="label">基础成本</div><div class="value">¥${Number(data.total_cost_before_markup||0).toFixed(2)}</div></div>`;
  html += `<div class="cost-card"><div class="label">加价率</div><div class="value">${data.markup_pct||0}%</div></div>`;
  html += `<div class="cost-card"><div class="label">部件数</div><div class="value">${data.item_count||0}</div></div>`;
  html += '</div>';
  if (data.items && data.items.length > 0) {
    html += '<div class="overflow-x-auto mt-3"><table class="w-full text-xs border-collapse"><thead><tr class="bg-gray-50"><th class="p-2 text-left font-semibold text-gray-600 border-b">部件</th><th class="p-2 text-right font-semibold text-gray-600 border-b">数量</th><th class="p-2 text-right font-semibold text-gray-600 border-b">单价</th><th class="p-2 text-right font-semibold text-gray-600 border-b">小计</th></tr></thead><tbody>';
    data.items.forEach(item => {
      html += `<tr class="border-b border-gray-50"><td class="p-2">${item.part_name||'未知'}</td><td class="p-2 text-right">${item.quantity||0}</td><td class="p-2 text-right">¥${Number(item.unit_cost||0).toFixed(2)}</td><td class="p-2 text-right font-medium">¥${Number(item.subtotal||0).toFixed(2)}</td></tr>`;
    });
    html += '</tbody></table></div>';
  }
  if (data.errors && data.errors.length > 0) {
    html += '<div class="mt-2 p-2 bg-red-50 rounded text-xs text-red-600">';
    data.errors.forEach(e => { html += `<div>⚠ ${e}</div>`; });
    html += '</div>';
  }
  container.innerHTML = html;
  openModal('modal-cost');
}

// ===== CONFIGURATOR: Save & Generate =====
function buildParamSummary() {
  const container = document.getElementById('cfg-param-summary');
  let html = '';
  Object.entries(currentParams).forEach(([k,v]) => {
    if (!v.isComputed) {
      html += `<div class="flex justify-between py-1 border-b border-gray-50 last:border-b-0">
        <span class="text-gray-600">${k}</span>
        <span class="font-medium text-gray-800">${v.value}</span>
      </div>`;
    }
  });
  container.innerHTML = html || '<p class="text-gray-400">请先在步骤1中设置参数</p>';
}

async function saveConfig() {
  const title = document.getElementById('cfg-name-input').value.trim();
  if (!title) { setStatus('error', '请输入配置名称'); showCfgResult('请输入配置名称', false); return; }
  const body = {title, template_part: configuratorPartId};
  const res = await apiCall('POST', 'configurations/', body);
  if (res.error) { showCfgResult(`保存失败: ${JSON.stringify(res.data).substring(0,150)}`, false); return; }
  savedConfigId = res.data.id;
  clearAreaDirty('configurator');
  showCfgResult(`✅ 配置 "${title}" 保存成功! (ID: ${savedConfigId})`, true);
  setStatus('success', '配置已保存');
  await setConfigParams();
  await loadConfigList();
}

async function setConfigParams() {
  if (!savedConfigId) {
    const existing = configs.find(c => c.template_part === configuratorPartId && c.status === 'draft');
    if (existing) savedConfigId = existing.id;
    else { setStatus('error', '请先保存配置'); return; }
  }
  const params = {};
  Object.entries(currentParams).forEach(([k,v]) => { if (!v.isComputed) params[k] = v.value; });
  const res = await apiCall('POST', `configs/${savedConfigId}/params/`, {parameters: params});
  if (res.error) { showCfgResult(`设置参数失败: ${JSON.stringify(res.data).substring(0,150)}`, false); return; }
  showCfgResult(`✅ 参数已设置到配置 #${savedConfigId}`, true);
  setStatus('success', '参数已设置');
  await loadConfigList();
}

async function transitionConfig() {
  if (!savedConfigId) {
    const existing = configs.find(c => c.template_part === configuratorPartId);
    if (existing) savedConfigId = existing.id;
    else { setStatus('error', '请先保存配置'); return; }
  }
  const cfg = configs.find(c => c.id === savedConfigId);
  const transitions = {draft: 'completed', completed: 'released'};
  const nextStatus = transitions[cfg ? cfg.status : 'draft'] || 'completed';
  const res = await apiCall('POST', `configs/${savedConfigId}/transition/`, {status: nextStatus});
  if (res.error) { showCfgResult(`过渡失败: ${JSON.stringify(res.data).substring(0,150)}`, false); return; }
  showCfgResult(`✅ 状态已切换为: ${nextStatus}`, true);
  setStatus('success', `状态: ${nextStatus}`);
  await loadConfigList();
}

async function generateVariant() {
  if (!savedConfigId) {
    const existing = configs.find(c => c.template_part === configuratorPartId);
    if (existing) savedConfigId = existing.id;
    else { setStatus('error', '请先保存配置'); return; }
  }
  const res = await apiCall('POST', 'generate-variant/', {config_id: savedConfigId});
  if (res.error) { showCfgResult(`生成变体失败: ${JSON.stringify(res.data).substring(0,150)}`, false); return; }
  const msg = `变体已生成: ${res.data.variant_part_name||''} (ID: ${res.data.variant_part_id||''})`;
  showCfgResult(`✅ ${msg}`, true);
  setStatus('success', msg);
  await loadConfigList();
}

async function finishConfig() {
  const name = document.getElementById('cfg-name-input').value.trim();
  if (name && !savedConfigId) await saveConfig();
  showCfgResult('✅ 配置流程已完成!', true);
  setStatus('success', '配置完成');
}

function showCfgResult(msg, isSuccess) {
  const el = document.getElementById('cfg-save-result');
  el.innerHTML = `<div class="action-result ${isSuccess ? 'success' : 'error'}">${msg}</div>`;
  setTimeout(() => { el.innerHTML = ''; }, 6000);
}

// ===== CONFIG LIST =====
async function loadConfigList() {
  const res = await apiCall('GET', 'configurations/');
  if (res.error) return;
  const data = res.data;
  configs = data.results || (Array.isArray(data) ? data : []);
  renderConfigSidebar();
}

function renderConfigSidebar() {
  const container = document.getElementById('cfg-config-list');
  document.getElementById('cfg-config-count').textContent = configs.length;
  if (!configs || configs.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="icon">📁</div><p>暂无配置</p></div>';
    return;
  }
  let html = '';
  configs.forEach(cfg => {
    const sel = selectedConfigId === cfg.id ? ' selected' : '';
    const statusClass = 'status-' + (cfg.status || 'draft');
    html += `<div class="config-card${sel}" onclick="selectSidebarConfig(${cfg.id})">
      <div class="flex justify-between items-center">
        <strong class="text-xs font-semibold text-gray-700">${cfg.title||'未命名'}</strong>
        <span class="status-badge ${statusClass} text-xs">${cfg.status||'draft'}</span>
      </div>
      <div class="text-xs text-gray-400 mt-0.5">${cfg.template_part_name||''} · rev ${cfg.revision||'1.0'}</div>
      <div class="text-xs text-gray-400">参数: ${cfg.parameter_count||0} · ${cfg.created_by_name||'system'}</div>
    </div>`;
  });
  container.innerHTML = html;
}

function selectSidebarConfig(id) {
  selectedConfigId = id;
  savedConfigId = id;
  renderConfigSidebar();
  const cfg = configs.find(c => c.id === id);
  if (cfg) {
    document.getElementById('cfg-name-input').value = cfg.title || '';
    showCfgResult(`已选择配置: ${cfg.title} (ID: ${id})`, true);
  }
}

// ===== PAGE 2: PARAM MANAGEMENT =====
async function loadParamConfigs(partId) {
  if (!partId) { document.getElementById('pm-config-list').innerHTML = '<div class="text-gray-400 text-sm p-2">请选择产品</div>'; return; }
  const container = document.getElementById('pm-config-list');
  container.innerHTML = '<div class="flex items-center justify-center py-3"><span class="spinner mr-2"></span><span class="text-sm text-gray-400">加载中...</span></div>';
  const res = await apiCall('GET', `part-config/?part=${parseInt(partId)}`);
  if (res.error) { container.innerHTML = '<div class="text-red-500 text-sm">加载失败</div>'; return; }
  const configs = res.data.results || (Array.isArray(res.data) ? res.data : []);
  let html = `<div class="flex items-center gap-2 mb-2">
    <span class="text-xs text-gray-400">共 ${configs.length} 个参数</span>
    <span class="text-xs text-gray-300">|</span>
    <span class="text-xs text-gray-400">💡 拖拽行头 <span class="text-gray-300">⠿</span> 可调整排序</span>
  </div>`;
  html += '<div class="overflow-x-auto"><table class="w-full text-xs border-collapse" id="param-config-table"><thead><tr class="bg-gray-50"><th class="p-2 text-center font-semibold text-gray-600 border-b w-8">#</th><th class="p-2 text-left font-semibold text-gray-600 border-b">参数</th><th class="p-2 text-center font-semibold text-gray-600 border-b">类型</th><th class="p-2 text-center font-semibold text-gray-600 border-b">驱动</th><th class="p-2 text-center font-semibold text-gray-600 border-b">计算</th><th class="p-2 text-right font-semibold text-gray-600 border-b">默认值</th><th class="p-2 text-right font-semibold text-gray-600 border-b">最小</th><th class="p-2 text-right font-semibold text-gray-600 border-b">最大</th><th class="p-2 text-right font-semibold text-gray-600 border-b">步长</th><th class="p-2 text-left font-semibold text-gray-600 border-b">选项</th><th class="p-2 text-left font-semibold text-gray-600 border-b">公式</th><th class="p-2 text-center font-semibold text-gray-600 border-b w-20">操作</th></tr></thead><tbody>';
  const sorted = (configs || []).sort((a,b) => (a.display_order||0) - (b.display_order||0));
  sorted.forEach((cfg, idx) => {
    const type = cfg.parameter_type || 'number';
    const optStr = cfg.options ? (Array.isArray(cfg.options) ? cfg.options.join(', ') : (typeof cfg.options === 'string' ? cfg.options : JSON.stringify(cfg.options))) : '-';
    html += `<tr class="border-b border-gray-50 hover:bg-gray-50/50" draggable="true"
      data-config-id="${cfg.id}" data-display-order="${cfg.display_order||0}"
      ondragstart="onParamDragStart(event, ${cfg.id})"
      ondragover="onParamDragOver(event)"
      ondrop="onParamDrop(event, ${cfg.id})"
      ondragend="onParamDragEnd(event)">
      <td class="p-2 text-center cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500 select-none" title="拖拽排序">⠿</td>
      <td class="p-2 font-medium">${cfg.template_name||''}</td>
      <td class="p-2 text-center">${typeBadge(type)}</td>
      <td class="p-2 text-center">${cfg.is_driving ? '✅' : '❌'}</td>
      <td class="p-2 text-center">${cfg.is_computed ? '✅' : '❌'}</td>
      <td class="p-2 text-right">${cfg.default_value||'-'}</td>
      <td class="p-2 text-right text-gray-500">${cfg.min_value != null ? cfg.min_value : '-'}</td>
      <td class="p-2 text-right text-gray-500">${cfg.max_value != null ? cfg.max_value : '-'}</td>
      <td class="p-2 text-right text-gray-500">${cfg.step_value != null ? cfg.step_value : '-'}</td>
      <td class="p-2 text-gray-500 max-w-[100px] truncate" title="${optStr}">${optStr}</td>
      <td class="p-2 text-gray-500 max-w-[120px] truncate" title="${cfg.computation_formula||''}">${cfg.computation_formula||'-'}</td>
      <td class="p-2 text-center">
        <div class="flex items-center justify-center gap-1">
          <button class="btn btn-sm text-[11px] px-1.5 py-0.5 bg-transparent text-blue-500 hover:text-blue-700 hover:bg-blue-50 border-0" onclick="openEditParamModal(${cfg.id})" title="编辑">✏️</button>
          <button class="btn btn-sm text-[11px] px-1.5 py-0.5 bg-transparent text-red-400 hover:text-red-600 hover:bg-red-50 border-0" onclick="deleteParamConfig(${cfg.id}, '${(cfg.template_name||'').replace(/'/g, "\\'")}')" title="删除">🗑️</button>
        </div>
      </td>
    </tr>`;
  });
  html += '</tbody></table></div>';
  container.innerHTML = html;
  // Store for drag-and-drop reordering
  window.__paramConfigs = configs;
  window.__currentPartId = partId;
}

// ── Card Drag & Drop Reorder ──
let _dragCardSourceId = null;

function onCardDragStart(event, configId) {
  _dragCardSourceId = configId;
  event.dataTransfer.effectAllowed = 'move';
  event.dataTransfer.setData('text/plain', String(configId));
  const card = event.target.closest('.param-card');
  if (card) card.classList.add('dragging');
}

function onCardDragOver(event) {
  event.preventDefault();
  const isTypeDrag = event.dataTransfer.effectAllowed === 'copy';
  event.dataTransfer.dropEffect = isTypeDrag ? 'copy' : 'move';
  const targetCard = event.target.closest('.param-card');
  if (targetCard) {
    document.querySelectorAll('#pd-params-canvas .param-card').forEach(c => c.classList.remove('drag-over'));
    targetCard.classList.add('drag-over');
  }
}

async function onCardDrop(event, targetId) {
  event.preventDefault();
  _dragCardSourceId = null;
  document.querySelectorAll('#pd-params-canvas .param-card').forEach(c => {
    c.classList.remove('drag-over', 'dragging');
  });

  const rawData = event.dataTransfer.getData('text/plain');
  if (!rawData) return;

  // Case 1: Type library drop onto a card → create before this card
  try {
    const parsed = JSON.parse(rawData);
    if (parsed && parsed.type) {
      await addIndependentParam(parsed.type, targetId);
      return;
    }
  } catch(e) {
    // Not JSON — treat as reorder
  }

  // Case 2: Card reorder
  const sourceId = parseInt(rawData);
  if (!sourceId || isNaN(sourceId) || sourceId === targetId) return;
  await reorderParams(sourceId, targetId);
}

function onCardDragEnd(event) {
  _dragCardSourceId = null;
  document.querySelectorAll('#pd-params-canvas .param-card').forEach(c => {
    c.classList.remove('drag-over', 'dragging');
  });
}

// ── Canvas-level Drop (user drops between/surrounding cards) ──
function onCanvasDragOver(event) {
  event.preventDefault();
  const isTypeDrag = event.dataTransfer.effectAllowed === 'copy';
  event.dataTransfer.dropEffect = isTypeDrag ? 'copy' : 'move';
  const canvas = document.getElementById('pd-params-canvas');
  canvas?.classList.add('drag-hover');
  if (isTypeDrag) {
    canvas?.classList.add('drag-type-hover');
  } else {
    canvas?.classList.remove('drag-type-hover');
  }
}

async function onCanvasDrop(event) {
  event.preventDefault();
  const canvas = document.getElementById('pd-params-canvas');
  canvas?.classList.remove('drag-hover', 'drag-type-hover');
  document.querySelectorAll('#pd-params-canvas .param-card').forEach(c => {
    c.classList.remove('drag-over', 'dragging');
  });

  const rawData = event.dataTransfer.getData('text/plain');
  if (!rawData) return;

  // ── Case 1: Type library drag → create new parameter ──
  try {
    const parsed = JSON.parse(rawData);
    if (parsed && parsed.type) {
      await addIndependentParam(parsed.type);
      return;
    }
  } catch(e) {
    // Not JSON — treat as reorder
  }

  // ── Case 2: Card reorder ──
  const sourceId = _dragCardSourceId !== null ? _dragCardSourceId : parseInt(rawData);
  _dragCardSourceId = null;
  if (!sourceId || isNaN(sourceId)) return;

  const cards = Array.from(document.querySelectorAll('#pd-params-canvas .param-card'));
  if (!cards.length) return;

  const dropY = event.clientY;
  let targetIdx = cards.length;

  for (let i = 0; i < cards.length; i++) {
    const rect = cards[i].getBoundingClientRect();
    const midY = rect.top + rect.height / 2;
    if (dropY < midY) {
      targetIdx = i;
      break;
    }
  }

  const targetCard = cards[Math.min(targetIdx, cards.length - 1)];
  const targetId = parseInt(targetCard?.dataset.configId);
  if (!targetId || sourceId === targetId) return;
  await reorderParams(sourceId, targetId);
}

async function reorderParams(sourceId, targetId) {
  const configs = window.__paramConfigs;
  if (!configs || !configs.length) return;

  const srcIdx = configs.findIndex(c => c.id === sourceId);
  const tgtIdx = configs.findIndex(c => c.id === targetId);
  if (srcIdx === -1 || tgtIdx === -1) return;

  // Move source to target position in array
  const [moved] = configs.splice(srcIdx, 1);
  const newIdx = tgtIdx > srcIdx ? tgtIdx - 1 : tgtIdx;
  configs.splice(newIdx, 0, moved);

  // Re-assign display_order
  const updates = configs.map((cfg, i) => ({
    id: cfg.id,
    display_order: (i + 1) * 10,
  }));

  setStatus('loading', '正在更新排序...');
  let errors = 0;
  for (const upd of updates) {
    const res = await apiCall('PATCH', `part-config/${upd.id}/`, { display_order: upd.display_order });
    if (res.error) errors++;
  }

  if (errors) {
    setStatus('error', `${errors} 个参数排序更新失败`);
  } else {
    setStatus('success', '排序已更新 ✅');
    if (window.__currentPartId) loadPdParams();
  }
}

// ── Delete ────────────────────────────────────────────────
async function deleteParamConfig(configId, paramName) {
  if (!confirm(`确定要删除参数「${paramName}」吗？此操作不可撤销。`)) return;
  setStatus('loading', `正在删除「${paramName}」...`);
  const res = await apiCall('DELETE', `part-config/${configId}/`);
  if (res.error) {
    if (res.status === 404) {
      // 参数已被删除，从本地清理 + 全量刷新
      setStatus('warning', `「${paramName}」不存在，正在刷新数据...`);
      await loadPdParams(); // 全量重新加载，保证同步
    } else {
      setStatus('error', `删除失败: ${res.status} - ${JSON.stringify(res.data).substring(0,100)}`);
    }
    return;
  }
  setStatus('success', `「${paramName}」已删除 ✅`);
  // Remove from local array and re-render
  if (window.__paramConfigs) {
    window.__paramConfigs = window.__paramConfigs.filter(c => c.id !== configId);
    const sorted = window.__paramConfigs.sort((a,b)=>(a.display_order||0)-(b.display_order||0));
    const canvas = document.getElementById('pd-params-canvas');
    const countBadge = document.getElementById('pd-param-count');
    if (sorted.length === 0) {
      canvas.innerHTML = `<div class=\"pc-empty-state\">
        <div class=\"pc-empty-icon\">🎨</div>
        <div class=\"pc-empty-title\">画布为空</div>
        <div class=\"pc-empty-desc\">从左栏组件库单击或拖拽添加参数</div>
      </div>`;
    } else {
      canvas.innerHTML = sorted.map((c,i)=>renderParamCard(c,i)).join('');
    }
    if (countBadge) countBadge.textContent = `${sorted.length} 个参数`;
  }
}

// ── Edit Param Modal ──
let _editingConfigId = null;

async function openEditParamModal(configId) {
  _editingConfigId = configId;
  
  // Fetch the config data
  const res = await apiCall('GET', `part-config/${configId}/`);
  if (res.error) { setStatus('error', '加载参数配置失败'); return; }
  const cfg = res.data;
  
  // Populate form
  if (document.getElementById('ap-part')) {
    // Set hidden field to existing part
    document.getElementById('ap-part').value = cfg.part;
    const part = parts.find(p => p.pk == cfg.part);
    document.getElementById('ap-product-name-display').textContent = part ? (part.name || part.full_name || '—') : `#${cfg.part}`;
  }
  
  // Template selector — show all for editing, filter out used ones for create
  const tmplSel = document.getElementById('ap-template');
  tmplSel.innerHTML = '<option value="">-- 请选择 --</option>';
  const currentConfigs = window.__paramConfigs || [];
  const existingIds = new Set();
  currentConfigs.forEach(c => { if (c.id !== configId) existingIds.add(c.template); });
  templates.forEach(t => {
    if (existingIds.has(t.pk) && t.pk !== cfg.template) return;
    const opt = document.createElement('option');
    opt.value = t.pk;
    opt.textContent = `${t.name}${t.units ? ' ('+t.units+')' : ''}`;
    if (t.pk === cfg.template) opt.selected = true;
    tmplSel.appendChild(opt);
  });
  
  // Fill in values
  document.getElementById('ap-type').value = cfg.parameter_type || 'number';
  document.getElementById('ap-default').value = cfg.default_value || '';
  document.getElementById('ap-min').value = cfg.min_value != null ? cfg.min_value : '';
  document.getElementById('ap-max').value = cfg.max_value != null ? cfg.max_value : '';
  document.getElementById('ap-step').value = cfg.step_value != null ? cfg.step_value : '';
  document.getElementById('ap-options').value = cfg.options ? (Array.isArray(cfg.options) ? cfg.options.join(', ') : cfg.options) : '';
  document.getElementById('ap-driving').checked = cfg.is_driving;
  document.getElementById('ap-computed').checked = cfg.is_computed;
  document.getElementById('ap-formula').value = cfg.computation_formula || '';
  document.getElementById('ap-order').value = cfg.display_order || 100;
  
  // Show/hide conditional sections
  onAddParamTypeChange();
  document.getElementById('ap-formula-group').style.display = cfg.is_computed ? 'block' : 'none';
  
  // Change modal title and button
  document.querySelector('#modal-add-param h3').textContent = `✏️ 编辑参数配置: ${cfg.template_name || ''}`;
  const btn = document.querySelector('#modal-add-param .btn-primary');
  btn.textContent = '保存修改';
  btn.onclick = updateParamConfig;
  
  openModal('modal-add-param');
}

async function updateParamConfig() {
  const configId = _editingConfigId;
  if (!configId) return;
  
  const type = document.getElementById('ap-type').value;
  const body = {
    parameter_type: type,
    default_value: type === 'boolean' ? document.getElementById('ap-boolean-default').value : document.getElementById('ap-default').value,
    min_value: (type === 'number' && document.getElementById('ap-min').value) ? parseFloat(document.getElementById('ap-min').value) : null,
    max_value: (type === 'number' && document.getElementById('ap-max').value) ? parseFloat(document.getElementById('ap-max').value) : null,
    step_value: (type === 'number' && document.getElementById('ap-step').value) ? parseFloat(document.getElementById('ap-step').value) : null,
    options: (type === 'option' || type === 'multi_option') ? document.getElementById('ap-options').value.split(',').map(s=>s.trim()).filter(Boolean) : null,
    is_driving: document.getElementById('ap-driving').checked,
    is_computed: document.getElementById('ap-computed').checked,
    computation_formula: document.getElementById('ap-formula').value || '',
    display_order: parseInt(document.getElementById('ap-order').value) || 100,
  };

  const res = await apiCall('PATCH', `part-config/${configId}/`, body);
  if (!res.error) {
    setStatus('success', '参数配置已更新 ✅');
    closeModal('modal-add-param');
    // Reset edit state
    _editingConfigId = null;
    document.querySelector('#modal-add-param h3').textContent = '➕ 新增参数配置';
    document.querySelector('#modal-add-param .btn-primary').textContent = '创建';
    document.querySelector('#modal-add-param .btn-primary').onclick = createParamConfig;
    // Reload
    if (window.__currentPartId) loadParamConfigs(window.__currentPartId);
  } else {
    setStatus('error', `更新失败: ${res.error}`);
  }
}

function openAddParamModal() {
  // Reset edit state
  _editingConfigId = null;
  document.querySelector('#modal-add-param h3').textContent = '➕ 新增参数配置';
  const btn = document.querySelector('#modal-add-param .btn-primary');
  btn.textContent = '创建';
  btn.onclick = createParamConfig;

  // Auto-set current product
  const partId = configuratorPartId;
  const part = parts.find(p => p.pk == partId);
  document.getElementById('ap-part').value = partId || '';
  document.getElementById('ap-product-name-display').textContent = part ? (part.name || part.full_name || '—') : '—';
  
  const tmplSel = document.getElementById('ap-template');
  tmplSel.innerHTML = '<option value="">-- 请选择 --</option>';
  const configs = window.__paramConfigs || [];
  const existingTemplateIds = new Set(configs.map(c => c.template));
  templates.forEach(t => {
    if (existingTemplateIds.has(t.pk)) return; // skip already added
    const opt = document.createElement('option');
    opt.value = t.pk;
    opt.textContent = `${t.name}${t.units ? ' ('+t.units+')' : ''}`;
    tmplSel.appendChild(opt);
  });
  
  // Reset form
  document.getElementById('ap-type').value = 'number';
  document.getElementById('ap-default').value = '';
  document.getElementById('ap-min').value = '';
  document.getElementById('ap-max').value = '';
  document.getElementById('ap-step').value = '';
  document.getElementById('ap-options').value = '';
  document.getElementById('ap-driving').checked = true;
  document.getElementById('ap-computed').checked = false;
  document.getElementById('ap-formula').value = '';
  document.getElementById('ap-order').value = '100';
  document.getElementById('ap-formula-group').style.display = 'none';
  onAddParamTypeChange();
  
  openModal('modal-add-param');
}

function cancelAddParamModal() {
  _editingConfigId = null;
  document.querySelector('#modal-add-param h3').textContent = '➕ 新增参数配置';
  const btn = document.querySelector('#modal-add-param .btn-primary');
  if (btn) { btn.textContent = '创建'; btn.onclick = createParamConfig; }
  closeModal('modal-add-param');
}

function onAddParamTemplateChange() {
  // Could auto-detect type from template if we had that data
}

function onAddParamTypeChange() {
  const type = document.getElementById('ap-type').value;
  const defaultGroup = document.getElementById('ap-type-fields');
  const optionsGroup = document.getElementById('ap-options-group');
  const booleanGroup = document.getElementById('ap-boolean-group');
  
  // Show/hide conditional sections
  if (type === 'option' || type === 'multi_option') {
    optionsGroup.style.display = 'block';
  } else {
    optionsGroup.style.display = 'none';
  }
  
  if (type === 'boolean') {
    booleanGroup.style.display = 'block';
  } else {
    booleanGroup.style.display = 'none';
  }
  
  // Show/hide min/max/step for number
  const minField = document.getElementById('ap-min').closest('.grid');
  if (minField) {
    const numberFields = minField.querySelectorAll('div');
    if (numberFields.length >= 4) {
      numberFields[1].style.display = (type === 'number') ? 'block' : 'none';
      numberFields[2].style.display = (type === 'number') ? 'block' : 'none';
      numberFields[3].style.display = (type === 'number') ? 'block' : 'none';
    }
  }
}

async function createParamConfig() {
  const partId = document.getElementById('ap-part').value;
  const templateId = document.getElementById('ap-template').value;
  if (!partId || !templateId) { setStatus('error', '请选择零件和参数模板'); return; }
  
  // Check for duplicates
  const configs = window.__paramConfigs || [];
  if (configs.some(c => c.template == templateId)) {
    const tpl = templates.find(t => t.pk == templateId);
    setStatus('error', `❌ 「${tpl ? tpl.name : '该参数'}」已存在，不能重复添加`);
    return;
  }
  
  const type = document.getElementById('ap-type').value;
  const body = {
    part: parseInt(partId),
    template: parseInt(templateId),
    parameter_type: type,
    default_value: type === 'boolean' ? document.getElementById('ap-boolean-default').value : document.getElementById('ap-default').value,
    min_value: (type === 'number' && document.getElementById('ap-min').value) ? parseFloat(document.getElementById('ap-min').value) : null,
    max_value: (type === 'number' && document.getElementById('ap-max').value) ? parseFloat(document.getElementById('ap-max').value) : null,
    step_value: (type === 'number' && document.getElementById('ap-step').value) ? parseFloat(document.getElementById('ap-step').value) : null,
    options: (type === 'option' || type === 'multi_option') ? document.getElementById('ap-options').value.split(',').map(s=>s.trim()).filter(Boolean) : null,
    is_driving: document.getElementById('ap-driving').checked,
    is_computed: document.getElementById('ap-computed').checked,
    computation_formula: document.getElementById('ap-formula').value || '',
    display_order: parseInt(document.getElementById('ap-order').value) || 100,
  };
  
  const res = await apiCall('POST', 'part-config/', body);
  if (!res.error) {
    setStatus('success', `参数配置已创建 (ID: ${res.data.id || res.data.pk})`);
    closeModal('modal-add-param');
    // Reload param configs if on param management page
    const partSelect = document.getElementById('pm-part-select');
    if (partSelect.value) loadParamConfigs(partSelect.value);
  }
}

// ===== PAGE 3: BOM FORMULA =====
async function loadBomFormulaConfigs(partId) {
  if (!partId) { document.getElementById('bom-formula-list').innerHTML = '<div class="empty-state"><div class="icon">📋</div><p>请选择产品</p></div>'; return; }
  const container = document.getElementById('bom-formula-list');
  container.innerHTML = '<div class="flex items-center justify-center py-3"><span class="spinner mr-2"></span><span class="text-sm text-gray-400">加载中...</span></div>';

  // ── "全部" 模式 ──────────────────────────────────────────
  if (partId === '__all__') {
    return loadAllBomFormulaConfigs(container);
  }

  // ── 单个产品模式 ────────────────────────────────────────
  const bomItemsRes = await fetch(`/api/bom/?part=${partId}&sub_part_detail=True&part_detail=True`, {headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()}, credentials: 'same-origin'});
  const bomItems = await bomItemsRes.json();
  const items = Array.isArray(bomItems) ? bomItems : (bomItems.results || []);

  const pcfgRes = await apiCall('GET', `bom-item-config/?bom_item__part=${partId}`);
  const pcfgs = pcfgRes.error ? [] : (Array.isArray(pcfgRes.data) ? pcfgRes.data : (pcfgRes.data.results || []));
  const pcfgMap = {};
  pcfgs.forEach(c => { pcfgMap[c.bom_item] = c; });
  
  let html = `<div class="text-xs text-gray-500 mb-2">共 ${items.length} 个BOM项</div>
  <table class="w-full text-xs border-collapse">
    <thead><tr class="bg-gray-50"><th class="text-left p-2 border-b font-semibold text-gray-600">物料</th><th class="text-left p-2 border-b font-semibold text-gray-600">数量</th><th class="text-center p-2 border-b font-semibold text-gray-600">模式</th><th class="text-left p-2 border-b font-semibold text-gray-600">公式</th><th class="text-center p-2 border-b font-semibold text-gray-600 w-20">操作</th></tr></thead><tbody>`;
  for (const item of items) {
    const subPartId = item.sub_part_detail ? item.sub_part_detail.pk : item.sub_part;
    const subPartName = item.sub_part_detail ? item.sub_part_detail.name : `#${item.sub_part}`;
    const cfg = pcfgMap[item.pk];
    const qtyFormula = cfg ? (cfg.qty_formula || '') : '';
    const condFormula = cfg ? (cfg.condition_formula || '') : '';
    const priceFormula = cfg ? (cfg.price_formula || '') : '';
    const formulaSummary = [qtyFormula && ('数量:'+qtyFormula), condFormula && ('条件:'+condFormula), priceFormula && ('价格:'+priceFormula)].filter(Boolean).join(' | ') || '<span class="text-gray-400">-</span>';
    // Build mode badges from enable flags
    let modeBadges = '';
    if (cfg) {
      if (cfg.enable_qty_formula) modeBadges += '📐';
      if (cfg.enable_conditional) modeBadges += '⚡';
      if (cfg.enable_candidate) modeBadges += '🎯';
      if (cfg.enable_variant) modeBadges += '🧬';
      if (cfg.enable_specification) modeBadges += '📝';

      if (cfg.enable_structure) modeBadges += '🔗';
    }
    if (!modeBadges) modeBadges = '<span class="text-gray-400">—</span>';
    html += `<tr class="border-b hover:bg-gray-50">
      <td class="p-2 font-medium">${subPartName}</td>
      <td class="p-2">${item.quantity}</td>
      <td class="p-2 text-center">
        <select class="text-[10px] border border-gray-200 rounded px-1 py-0.5" onchange="updateBomItemMode(${item.pk}, this.value)">
          <option value="standard">— 标准</option>
          <option value="qty_formula">📐 数量公式</option>
          <option value="conditional">📐⚡ 数量+条件</option>
          <option value="candidate">🎯 候选零件</option>
          <option value="variant">🧬 动态项目</option>
          <option value="specification">📝 规格描述</option>

          <option value="structure">🔗 结构控制</option>
        </select>
        <span class="text-[10px] ml-1">${modeBadges}</span>
      </td>
      <td class="p-2">${formulaSummary}</td>
      <td class="p-2 text-center"><button class="btn btn-sm btn-outline-primary text-[10px] px-2 py-0.5" onclick="openFormulaEditor(${item.pk}, ${subPartId}, '${subPartName.replace(/'/g, "\\'")}')">配置</button></td>
    </tr>`;
  }
  html += '</tbody></table>';
  container.innerHTML = html;
}

// ── 全部参数化BOM项一览 ──────────────────────────────────
async function loadAllBomFormulaConfigs(container) {
  // Fetch all parametric BOM configs
  const pcfgRes = await apiCall('GET', 'bom-item-config/');
  if (pcfgRes.error) { container.innerHTML = '<div class="text-red-500 text-sm">加载失败</div>'; return; }
  const pcfgs = Array.isArray(pcfgRes.data) ? pcfgRes.data : (pcfgRes.data.results || []);
  if (!pcfgs.length) {
    container.innerHTML = '<div class="empty-state"><div class="icon">📋</div><p>暂无参数化BOM配置</p></div>';
    return;
  }

  // Build bom_item_id → config map, collect bom_item IDs
  const bomItemIds = pcfgs.map(c => c.bom_item);
  const pcfgByBomId = {};
  pcfgs.forEach(c => { pcfgByBomId[c.bom_item] = c; });

  // Fetch BomItems in batch (use query params)
  const bomItemRes = await fetch(`/api/bom/?id__in=${bomItemIds.join(',')}&limit=200&sub_part_detail=True&part_detail=True`, {
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()}, credentials: 'same-origin'
  });
  const bomData = await bomItemRes.json();
  const bomItems = Array.isArray(bomData) ? bomData : (bomData.results || []);

  // Build bom_item_id → {bom_item, product_name, sub_part_name}
  const bomMap = {};
  bomItems.forEach(bi => {
    const productName = bi.part_detail?.name || bi.part_detail?.full_name || `#${bi.part}`;
    const subPartName = bi.sub_part_detail?.name || `#${bi.sub_part}`;
    bomMap[bi.pk] = { productName, subPartName, quantity: bi.quantity };
  });

  const activeModeMapping = [
    {flag:'enable_qty_formula', icon:'📐', label:'数量'},
    {flag:'enable_conditional', icon:'⚡', label:'条件'},
    {flag:'enable_candidate', icon:'🎯', label:'候选'},
    {flag:'enable_variant', icon:'🧬', label:'动态'},
    {flag:'enable_specification', icon:'📝', label:'规格'},

    {flag:'enable_structure', icon:'🔗', label:'结构'},
  ];

  let html = `<div class="text-xs text-gray-500 mb-2">共 ${pcfgs.length} 个参数化配置</div>
  <div class="overflow-x-auto"><table class="w-full text-xs border-collapse">
    <thead><tr class="bg-gray-50"><th class="p-2 text-left border-b font-semibold text-gray-600">所属产品</th><th class="p-2 text-left border-b font-semibold text-gray-600">物料</th><th class="p-2 text-left border-b font-semibold text-gray-600">数量</th><th class="p-2 text-left border-b font-semibold text-gray-600">模式</th><th class="p-2 text-left border-b font-semibold text-gray-600">公式摘要</th><th class="p-2 text-center border-b font-semibold text-gray-600 w-16">配置</th></tr></thead><tbody>`;
  for (const cfg of pcfgs) {
    const bi = bomMap[cfg.bom_item] || {};
    // Build mode badges from enable flags
    let modeBadges = '';
    activeModeMapping.forEach(m => {
      if (cfg[m.flag]) modeBadges += `<span class="inline-block px-1 py-0.5 rounded bg-gray-100 text-gray-700 text-[10px] mr-0.5">${m.icon} ${m.label}</span>`;
    });
    if (!modeBadges) modeBadges = '<span class="text-[10px] text-gray-400">标准</span>';
    const formulas = [cfg.qty_formula, cfg.condition_formula, cfg.price_formula].filter(Boolean).join(' | ');
    html += `<tr class="border-b hover:bg-gray-50">
      <td class="p-2 font-medium text-blue-700">${bi.productName || '?'}</td>
      <td class="p-2">${bi.subPartName || '?'}</td>
      <td class="p-2">${bi.quantity || '-'}</td>
      <td class="p-2">${modeBadges}</td>
      <td class="p-2 max-w-[200px]"><code class="text-blue-600 text-[10px] truncate block" title="${formulas}">${formulas || '<span class="text-gray-400">-</span>'}</code></td>
      <td class="p-2 text-center"><button class="btn btn-sm btn-outline-primary text-[10px] px-2 py-0.5" onclick="openFormulaEditor(${cfg.bom_item}, 0, '${(bi.subPartName||'').replace(/'/g, "\\'")}')">编辑</button></td>
    </tr>`;
  }
  html += '</tbody></table></div>';
  container.innerHTML = html;
}


// ===== FORMULA EDITOR STATE =====
let feState = {
  bomItemId: null,
  partId: null,
  partName: '',
  activeField: 'qty',
  existingConfigId: null,
  paramContext: {},
  variantMappingId: null,
  specId: null,
  currentMode: 'qty_formula'
};

function openFormulaEditor(bomItemId, partId, partName) {
  feState.bomItemId = bomItemId;
  feState.partId = partId;
  feState.partName = partName;
  feState.activeField = 'qty';
  feState.existingConfigId = null;
  feState.paramContext = {};
  feState.variantMappingId = null;
  feState.specId = null;

  document.getElementById('fe-part-name').textContent = partName;

  // Clear fields
  document.getElementById('fe-qty-formula').value = '';
  document.getElementById('fe-condition-formula').value = '';
  document.getElementById('fe-price-formula').value = '';
  document.getElementById('fe-qty-result').innerHTML = '';
  document.getElementById('fe-condition-result').innerHTML = '';
  document.getElementById('fe-price-result').innerHTML = '';
  document.getElementById('fe-preview-all').innerHTML = '<p class="text-xs text-gray-400">点击"预览全部"查看结果</p>';
  document.getElementById('fe-mode-config').innerHTML = '';

  // Load existing config for this bom_item
  loadExistingBomItemConfig(bomItemId);
  // Load available params
  loadFormulaEditorParams(partId);
  // Get current mode and set visibility
  getCurrentModeAndRender(bomItemId);

  openModal('modal-formula-editor');
}

async function getCurrentModeAndRender(bomItemId) {
  const res = await apiCall('GET', `bom-item-config/?bom_item=${bomItemId}`);
  if (res.error) return;
  const items = Array.isArray(res.data) ? res.data : (res.data.results || []);
  const cfg = items.length > 0 ? items[0] : null;

  // Determine active modes from enable flags
  const activeModes = [];
  if (cfg) {
    if (cfg.enable_qty_formula) activeModes.push('qty_formula');
    if (cfg.enable_conditional) activeModes.push('conditional');
    if (cfg.enable_candidate) activeModes.push('candidate');
    if (cfg.enable_variant) activeModes.push('variant');
    if (cfg.enable_specification) activeModes.push('specification');

    if (cfg.enable_structure) activeModes.push('structure');
  }
  const primaryMode = activeModes.length > 0 ? activeModes[0] : 'standard';
  feState.currentMode = primaryMode;
  feState.activeModes = activeModes;

  // Show/hide condition formula group
  const condGroup = document.getElementById('fe-condition-group');
  if (condGroup) {
    condGroup.style.display = activeModes.includes('conditional') || activeModes.includes('candidate') ? '' : 'none';
  }
  // Add mode selector to editor header
  const headerDiv = document.querySelector('#modal-formula-editor .flex.items-center');
  if (headerDiv) {
    let modeSel = document.getElementById('fe-mode-select');
    if (!modeSel) {
      modeSel = document.createElement('select');
      modeSel.id = 'fe-mode-select';
      modeSel.className = 'text-[10px] border border-gray-200 rounded px-1 py-0.5 ml-2';
      modeSel.innerHTML = `<option value="standard">— 标准</option><option value="qty_formula">📐 数量公式</option><option value="conditional">📐⚡ 数量+条件</option><option value="candidate">🎯 候选零件</option><option value="variant">🧬 动态项目</option><option value="specification">📝 规格描述</option><option value="structure">🔗 结构控制</option>`;
      modeSel.onchange = function() { renderModeConfig(); };
      headerDiv.appendChild(modeSel);
    }
    modeSel.value = primaryMode;
  }
  renderModeConfig();
}

function closeFormulaEditor() {
  closeModal('modal-formula-editor');
}

async function loadExistingBomItemConfig(bomItemId) {
  const res = await apiCall('GET', `bom-item-config/?bom_item=${bomItemId}`);
  if (res.error) return;
  const items = Array.isArray(res.data) ? res.data : (res.data.results || []);
  if (items.length > 0) {
    const cfg = items[0];
    feState.existingConfigId = cfg.id;
    if (cfg.qty_formula) document.getElementById('fe-qty-formula').value = cfg.qty_formula;
    if (cfg.condition_formula) document.getElementById('fe-condition-formula').value = cfg.condition_formula;
    if (cfg.price_formula) document.getElementById('fe-price-formula').value = cfg.price_formula;
  }
}

async function loadFormulaEditorParams(partId) {
  const container = document.getElementById('fe-param-pills');
  container.innerHTML = '<span class="text-xs text-gray-400">加载中...</span>';
  const res = await apiCall('GET', `part-config/?part=${partId}`);
  if (res.error) {
    container.innerHTML = '<span class="text-xs text-red-400">加载参数失败</span>';
    return;
  }
  const configs = Array.isArray(res.data) ? res.data : (res.data.results || []);
  if (!configs.length) {
    container.innerHTML = '<span class="text-xs text-gray-400">该零件未配置参数</span>';
    return;
  }

  // Build param context map for preview
  configs.forEach(c => {
    feState.paramContext[c.param_name] = c.default_value;
  });

  let html = '';
  configs.forEach(c => {
    const paramName = c.param_name || c.param_template_detail?.name || 'unknown';
    html += `<span class="fe-param-pill" onclick="insertParam('${paramName.replace(/'/g, "\\'")}')">${paramName}</span>`;
  });
  container.innerHTML = html;
}

function activateFormulaField(fieldName) {
  feState.activeField = fieldName;
}

function getActiveTextarea() {
  const map = { qty: 'fe-qty-formula', condition: 'fe-condition-formula', price: 'fe-price-formula' };
  return document.getElementById(map[feState.activeField]);
}

function insertParam(paramName) {
  const ta = getActiveTextarea();
  if (!ta) return;
  const insertText = `param.${paramName}`;
  const start = ta.selectionStart;
  const end = ta.selectionEnd;
  const val = ta.value;
  ta.value = val.substring(0, start) + insertText + val.substring(end);
  const newPos = start + insertText.length;
  ta.selectionStart = ta.selectionEnd = newPos;
  ta.focus();
}

function insertFunction(funcName) {
  const ta = getActiveTextarea();
  if (!ta) return;
  const start = ta.selectionStart;
  const end = ta.selectionEnd;
  const val = ta.value;
  const insertText = funcName;
  ta.value = val.substring(0, start) + insertText + val.substring(end);
  const newPos = start + insertText.length;
  ta.selectionStart = ta.selectionEnd = newPos;
  ta.focus();
}

async function validateSingleFormula(fieldName) {
  const map = { qty: 'fe-qty-formula', condition: 'fe-condition-formula', price: 'fe-price-formula' };
  const resultMap = { qty: 'fe-qty-result', condition: 'fe-condition-result', price: 'fe-price-result' };
  const formula = document.getElementById(map[fieldName]).value.trim();
  const resultContainer = document.getElementById(resultMap[fieldName]);

  if (!formula) {
    resultContainer.innerHTML = '<span class="text-gray-400">公式为空，跳过验证</span>';
    return;
  }

  resultContainer.innerHTML = '<span class="text-blue-500"><span class="spinner inline-block mr-1"></span>验证中...</span>';
  const res = await apiCall('POST', 'formula/validate/', {formula});
  if (res.error) {
    resultContainer.innerHTML = `<span class="text-red-600">❌ 验证失败: ${res.data?.error || JSON.stringify(res.data).substring(0, 80)}</span>`;
  } else {
    const valid = res.data.valid !== false;
    resultContainer.innerHTML = valid
      ? '<span class="text-green-600">✅ 有效</span>'
      : `<span class="text-red-600">❌ 无效: ${(res.data.errors || []).join('; ') || '未知错误'}</span>`;
  }
}

async function previewSingleFormula(fieldName) {
  const map = { qty: 'fe-qty-formula', condition: 'fe-condition-formula', price: 'fe-price-formula' };
  const resultMap = { qty: 'fe-qty-result', condition: 'fe-condition-result', price: 'fe-price-result' };
  const formula = document.getElementById(map[fieldName]).value.trim();
  const resultContainer = document.getElementById(resultMap[fieldName]);

  if (!formula) {
    resultContainer.innerHTML = '<span class="text-gray-400">公式为空</span>';
    return;
  }

  resultContainer.innerHTML = '<span class="text-blue-500"><span class="spinner inline-block mr-1"></span>计算中...</span>';
  const res = await apiCall('POST', 'formula/preview/', {
    formula,
    context: feState.paramContext
  });
  if (res.error) {
    resultContainer.innerHTML = `<span class="text-red-600">❌ 错误: ${res.data?.error || JSON.stringify(res.data).substring(0, 80)}</span>`;
  } else {
    const result = res.data.result;
    resultContainer.innerHTML = `<span class="text-green-700">✅ 结果: <strong>${result != null ? result : '(空)'}</strong></span>`;
  }
}

async function previewAllFormulas() {
  const qty = document.getElementById('fe-qty-formula').value.trim();
  const cond = document.getElementById('fe-condition-formula').value.trim();
  const container = document.getElementById('fe-preview-all');

  if (!qty && !cond) {
    container.innerHTML = '<p class="text-xs text-gray-400">所有公式为空</p>';
    return;
  }

  container.innerHTML = '<span class="text-blue-500"><span class="spinner inline-block mr-1"></span>计算全部...</span>';

  let output = '';
  // Preview each formula
  const formulas = [
    { key: 'qty_formula', label: '数量公式', value: qty },
    { key: 'condition_formula', label: '条件公式', value: cond }
  ];

  for (const f of formulas) {
    if (!f.value) {
      output += `<div class="flex justify-between py-0.5"><span class="text-gray-500">${f.label}:</span><span class="text-gray-400">(空)</span></div>`;
      continue;
    }
    const res = await apiCall('POST', 'formula/preview/', {formula: f.value, context: feState.paramContext});
    if (res.error) {
      output += `<div class="flex justify-between py-0.5"><span class="text-gray-500">${f.label}:</span><span class="text-red-500">❌ ${res.data?.error || '错误'}</span></div>`;
    } else {
      const result = res.data.result;
      output += `<div class="flex justify-between py-0.5"><span class="text-gray-500">${f.label}:</span><span class="font-mono font-semibold text-blue-700">${result != null ? result : '(空)'}</span></div>`;
    }
  }

  // Show context params used
  output += `<div class="mt-1 pt-1 border-t border-gray-100 text-[10px] text-gray-400">当前参数: ${JSON.stringify(feState.paramContext)}</div>`;

  container.innerHTML = output;
}

async function saveBomFormula() {
  const qtyFormula = document.getElementById('fe-qty-formula').value.trim();
  const conditionFormula = document.getElementById('fe-condition-formula').value.trim();
  const priceFormula = document.getElementById('fe-price-formula').value.trim();
  const mode = document.getElementById('fe-mode-select')?.value || 'qty_formula';

  if (!qtyFormula && !conditionFormula && !priceFormula && mode === 'qty_formula') {
    setStatus('error', '请至少输入一个公式');
    return;
  }

  const body = {
    bom_item: feState.bomItemId,
    mode: mode,
    qty_formula: qtyFormula || '',
    condition_formula: conditionFormula || '',
    price_formula: priceFormula || '',
  };

  let res;
  if (feState.existingConfigId) {
    res = await apiCall('PATCH', `bom-item-config/${feState.existingConfigId}/`, body);
  } else {
    res = await apiCall('POST', 'bom-item-config/', body);
  }

  if (!res.error) {
    setStatus('success', '公式保存成功 ✅');
    clearAreaDirty('bom');
    feState.existingConfigId = res.data.id;
    closeFormulaEditor();
    // Reload the BOM formula list
    const partSelect = document.getElementById('bom-part-select');
    if (partSelect.value) loadBomFormulaConfigs(partSelect.value);
  } else {
    setStatus('error', `保存失败: ${res.data?.error || JSON.stringify(res.data).substring(0, 100)}`);
  }
}

// ===== FORMULA TEST =====
async function testFormula() {
  const formula = document.getElementById('fm-formula').value.trim();
  let context = {};
  try { context = JSON.parse(document.getElementById('fm-context').value || '{}'); } catch(e) { setStatus('error', 'JSON格式错误'); return; }
  if (!formula) { setStatus('error', '请输入公式'); return; }
  const res = await apiCall('POST', 'formula/preview/', {formula, context});
  const container = document.getElementById('fm-result');
  container.style.display = 'block';
  if (res.error) {
    container.innerHTML = `<div class="text-red-600">❌ 错误: ${JSON.stringify(res.data.error||res.data)}</div>`;
  } else {
    container.innerHTML = `<div class="text-green-700">✅ 结果: ${res.data.result != null ? res.data.result : 'ok'}</div>`;
  }
}

async function validateFormula() {
  const formula = document.getElementById('fm-formula').value.trim();
  if (!formula) { setStatus('error', '请输入公式'); return; }
  const res = await apiCall('POST', 'formula/validate/', {formula});
  const container = document.getElementById('fm-result');
  container.style.display = 'block';
  if (res.error) {
    container.innerHTML = `<div class="text-red-600">❌ 验证失败</div>`;
  } else {
    const valid = res.data.valid !== false;
    container.innerHTML = `<div class="${valid ? 'text-green-700' : 'text-red-600'}">${valid ? '✅ 公式有效' : '❌ 公式无效'}${res.data.errors && res.data.errors.length ? '<br>' + res.data.errors.join('; ') : ''}</div>`;
  }
}

// ===== MODAL HELPERS =====
function openModal(id) {
  document.getElementById(id).classList.add('show');
  document.body.style.overflow = 'hidden';
}
function closeModal(id) {
  document.getElementById(id).classList.remove('show');
  document.body.style.overflow = '';
}
document.querySelectorAll('.modal-overlay').forEach(m => {
  m.addEventListener('click', function(e) {
    if (e.target === this) {
      // 所有弹窗都不能点击空白处关闭，必须通过按钮关闭
      return;
      // Reset param modal state if closing it
      if (this.id === 'modal-add-param') {
        _editingConfigId = null;
        document.querySelector('#modal-add-param h3').textContent = '➕ 新增参数配置';
        const btn = document.querySelector('#modal-add-param .btn-primary');
        if (btn) { btn.textContent = '创建'; btn.onclick = createParamConfig; }
      }
    }
  });
});

// ===== INLINE MODE CONFIG RENDER =====
function renderModeConfig() {
  const zone = document.getElementById('fe-mode-config');
  const mode = document.getElementById('fe-mode-select')?.value || 'qty_formula';
  const bomItemId = feState.bomItemId;
  if (!bomItemId) { zone.innerHTML = ''; return; }
  if (mode === 'candidate') {
    zone.innerHTML = `
      <div class="card p-3 mb-3">
        <div class="flex items-center justify-between mb-2"><span class="text-xs font-semibold text-gray-700">🎯 候选零件列表</span><button class="btn btn-sm btn-primary text-[10px] px-2 py-0.5" onclick="addCandidatePart(${bomItemId})">+ 添加候选</button></div>
        <div id="fe-candidate-list" class="space-y-1"><span class="text-xs text-gray-400">加载中...</span></div>
      </div>`;
    loadCandidateParts(bomItemId);
  } else if (mode === 'variant') {
    zone.innerHTML = `
      <div class="card p-3 mb-3">
        <div class="text-xs font-semibold text-gray-700 mb-2">🧬 动态映射配置</div>
        <div class="space-y-2" id="fe-variant-form">
          <div><label class="text-[10px] text-gray-500">模板零件</label><select class="input-field text-xs" id="fe-variant-template"><option value="">-- 选择 --</option></select></div>
          <div><label class="text-[10px] text-gray-500">参数映射 (JSON)</label><textarea class="input-field font-mono text-xs" id="fe-variant-params" rows="3" placeholder='{"高度": "parent.货架高度", "材质": "\\'Q235\\'", "表面处理": "\\'喷塑\\'"}'>{"height": "parent.货架高度"}</textarea></div>
          <div><label class="text-[10px] text-gray-500">动态名称模板</label><input class="input-field text-xs" id="fe-variant-name" placeholder='立柱-H{高度}'></div>
          <div class="flex items-center gap-2"><label class="toggle-wrap"><span class="toggle-track" id="fe-variant-auto"><span class="toggle-thumb"></span></span><span class="toggle-label text-[10px]">自动生成</span></label></div>
          <button class="btn btn-sm btn-primary text-[10px] px-2 py-0.5" onclick="saveVariantMapping(${bomItemId})">💾 保存动态映射</button>
          <div id="fe-variant-result" class="text-xs mt-1"></div>
        </div>
      </div>`;
    loadVariantMapping(bomItemId);
    loadVariantPartSelect();
  } else if (mode === 'specification') {
    zone.innerHTML = `
      <div class="card p-3 mb-3">
        <div class="text-xs font-semibold text-gray-700 mb-2">📝 规格描述配置</div>
        <div class="space-y-2" id="fe-spec-form">
          <div><label class="text-[10px] text-gray-500">规格类型</label><input class="input-field text-xs" id="fe-spec-type" placeholder="outsource / raw_material / custom" value="custom"></div>
          <div><label class="text-[10px] text-gray-500">规格字段 (JSON 数组)</label><textarea class="input-field font-mono text-xs" id="fe-spec-fields" rows="4" placeholder='[{"name":"材质","formula":"\\'Q235\\'"},{"name":"长度","formula":"parent.货架高度+100","unit":"mm"}]'>[{"name":"材质","formula":"'Q235'"},{"name":"长度","formula":"parent.货架高度+100","unit":"mm"}]</textarea></div>
          <div><label class="text-[10px] text-gray-500">图纸号公式</label><input class="input-field text-xs" id="fe-spec-drawing" placeholder="'DWG-' + param.订单号"></div>
          <div><label class="text-[10px] text-gray-500">单价公式</label><input class="input-field text-xs" id="fe-spec-cost" placeholder="param.长度 * 0.035 + 25"></div>
          <button class="btn btn-sm btn-primary text-[10px] px-2 py-0.5" onclick="saveSpecification(${bomItemId})">💾 保存规格描述</button>
          <div id="fe-spec-result" class="text-xs mt-1"></div>
        </div>
      </div>`;
    loadSpecification(bomItemId);
  } else {
    zone.innerHTML = '';
  }
}

// ===== MODE HELPERS =====
async function updateBomItemMode(bomItemId, mode) {
  // Map selected mode to enable_* flags
  const modeToFlags = {
    standard:       {},
    qty_formula:    {enable_qty_formula: true},
    conditional:    {enable_qty_formula: true, enable_conditional: true},
    candidate:      {enable_candidate: true},
    variant:        {enable_variant: true},
    specification:  {enable_specification: true},

    structure:      {enable_structure: true},
  };
  const extraFields = {enable_qty_formula:false, enable_conditional:false,
    enable_candidate:false, enable_variant:false, enable_specification:false,
    enable_structure:false};
  const data = {...extraFields, ...(modeToFlags[mode] || {})};
  const res = await apiCall('GET', `bom-item-config/?bom_item=${bomItemId}`);
  if (res.error) return;
  const items = Array.isArray(res.data) ? res.data : (res.data.results || []);
  if (items.length > 0) {
    await apiCall('PATCH', `bom-item-config/${items[0].id}/`, data);
  } else {
    await apiCall('POST', 'bom-item-config/', {bom_item: bomItemId, ...data});
  }
  const ps = document.getElementById('bom-part-select');
  if (ps.value) loadBomFormulaConfigs(ps.value);
}

// ===== CANDIDATE PARTS (场景3) =====
async function loadCandidateParts(bomItemId) {
  const container = document.getElementById('fe-candidate-list');
  const res = await apiCall('GET', `candidate-parts/?parametric_bom_item=${bomItemId}`);
  if (res.error) { container.innerHTML = '<span class="text-xs text-red-400">加载失败</span>'; return; }
  const items = Array.isArray(res.data) ? res.data : (res.data.results || []);
  if (!items.length) { container.innerHTML = '<span class="text-xs text-gray-400">暂无候选零件，点击上方按钮添加</span>'; return; }
  let html = '';
  items.forEach(c => {
    html += `<div class="flex items-center gap-2 p-1.5 bg-gray-50 rounded text-[10px]">
      <span class="font-medium w-4 text-center">${c.priority}</span>
      <span class="flex-1">${c.part_name}${c.label?' <span class="text-gray-400">('+c.label+')</span>':''}</span>
      <code class="text-purple-600 flex-1 truncate" title="${c.condition_formula||''}">${c.condition_formula||'<span class="text-gray-400">always</span>'}</code>
      <button class="text-red-500 hover:text-red-700" onclick="deleteCandidatePart(${c.id})">✕</button>
    </div>`;
  });
  container.innerHTML = html;
}
async function addCandidatePart(bomItemId) {
  const partName = prompt('请输入候选零件名称或ID:');
  if (!partName) return;
  const condition = prompt('条件公式 (留空=始终可用):', '');
  const label = prompt('显示标签 (选填):', '');
  const priority = parseInt(prompt('优先级 (0=最高):', '100')) || 100;
  // Try to find the part by name
  const partsRes = await fetch(`/api/part/?search=${encodeURIComponent(partName)}&limit=5`, {headers:{'Content-Type':'application/json','X-CSRFToken':getCsrfToken()}, credentials:'same-origin'});
  const partsData = await partsRes.json();
  const parts = partsData.results || partsData || [];
  let partId = null;
  if (parts.length === 1) {
    partId = parts[0].pk;
    if (!confirm(`使用零件: ${parts[0].name} (ID: ${partId})?`)) return;
  } else if (parts.length > 1) {
    const choice = prompt(`找到多个零件，请输入正确ID:\n${parts.map(p=>p.pk+': '+p.name).join('\n')}`);
    if (!choice) return;
    partId = parseInt(choice);
  } else {
    partId = parseInt(partName);
    if (isNaN(partId)) { alert('未找到零件'); return; }
  }
  const res = await apiCall('POST', 'candidate-parts/', {parametric_bom_item: bomItemId, part: partId, label, condition_formula: condition, priority});
  if (!res.error) loadCandidateParts(bomItemId);
}
async function deleteCandidatePart(id) {
  if (!confirm('删除此候选零件?')) return;
  const res = await apiCall('DELETE', `candidate-parts/${id}/`);
  if (!res.error) {
    const bomItemId = feState.bomItemId;
    if (bomItemId) loadCandidateParts(bomItemId);
  }
}

// ===== VARIANT MAPPING (场景4) =====
async function loadVariantPartSelect() {
  const sel = document.getElementById('fe-variant-template');
  if (!sel) return;
  const res = await fetch('/api/part/?is_template=True&limit=100', {headers:{'Content-Type':'application/json','X-CSRFToken':getCsrfToken()}, credentials:'same-origin'});
  const data = await res.json();
  const parts = data.results || data || [];
  sel.innerHTML = '<option value="">-- 选择模板 --</option>';
  parts.forEach(p => { const opt = document.createElement('option'); opt.value=p.pk; opt.textContent=`${p.full_name||p.name} (ID:${p.pk})`; sel.appendChild(opt); });
}
async function loadVariantMapping(bomItemId) {
  const res = await apiCall('GET', `variant-mappings/?parametric_bom_item=${bomItemId}`);
  if (res.error) return;
  const items = Array.isArray(res.data) ? res.data : (res.data.results || []);
  if (!items.length) return;
  const vm = items[0];
  const sel = document.getElementById('fe-variant-template');
  if (sel) { sel.value = vm.template_part; }
  const paramsEl = document.getElementById('fe-variant-params');
  if (paramsEl) paramsEl.value = JSON.stringify(vm.param_mapping || {}, null, 2);
  const nameEl = document.getElementById('fe-variant-name');
  if (nameEl) nameEl.value = vm.variant_name_template || '';
  const auto = document.getElementById('fe-variant-auto');
  if (auto) auto.classList.toggle('on', vm.auto_generate !== false);
  feState.variantMappingId = vm.id;
}
async function saveVariantMapping(bomItemId) {
  const templatePart = parseInt(document.getElementById('fe-variant-template').value);
  if (!templatePart) { setStatus('error', '请选择模板零件'); return; }
  let paramMapping = {};
  try { paramMapping = JSON.parse(document.getElementById('fe-variant-params').value); } catch(e) { setStatus('error', '参数映射JSON格式错误'); return; }
  const nameTemplate = document.getElementById('fe-variant-name').value;
  const autoGen = document.getElementById('fe-variant-auto').classList.contains('on');
  const body = {parametric_bom_item: bomItemId, template_part: templatePart, param_mapping: paramMapping, variant_name_template: nameTemplate, auto_generate: autoGen};
  let res;
  if (feState.variantMappingId) {
    res = await apiCall('PATCH', `variant-mappings/${feState.variantMappingId}/`, body);
  } else {
    res = await apiCall('POST', 'variant-mappings/', body);
  }
  if (!res.error) {
    feState.variantMappingId = res.data.id;
    document.getElementById('fe-variant-result').innerHTML = '<span class="text-green-600">✅ 已保存</span>';
  }
}

// ===== SPECIFICATION (场景5) =====
async function loadSpecification(bomItemId) {
  const res = await apiCall('GET', `specifications/?parametric_bom_item=${bomItemId}`);
  if (res.error) return;
  const items = Array.isArray(res.data) ? res.data : (res.data.results || []);
  if (!items.length) return;
  const s = items[0];
  document.getElementById('fe-spec-type').value = s.spec_type || 'custom';
  document.getElementById('fe-spec-fields').value = JSON.stringify(s.spec_fields || [], null, 2);
  document.getElementById('fe-spec-drawing').value = s.drawing_ref_formula || '';
  document.getElementById('fe-spec-cost').value = s.unit_cost_formula || '';
  feState.specId = s.id;
}
async function saveSpecification(bomItemId) {
  const specType = document.getElementById('fe-spec-type').value || 'custom';
  let specFields = [];
  try { specFields = JSON.parse(document.getElementById('fe-spec-fields').value); } catch(e) { setStatus('error', '规格字段JSON格式错误'); return; }
  const drawingRef = document.getElementById('fe-spec-drawing').value;
  const unitCost = document.getElementById('fe-spec-cost').value;
  const body = {parametric_bom_item: bomItemId, spec_type: specType, spec_fields: specFields, drawing_ref_formula: drawingRef, unit_cost_formula: unitCost};
  let res;
  if (feState.specId) {
    res = await apiCall('PATCH', `specifications/${feState.specId}/`, body);
  } else {
    res = await apiCall('POST', 'specifications/', body);
  }
  if (!res.error) {
    feState.specId = res.data.id;
    document.getElementById('fe-spec-result').innerHTML = '<span class="text-green-600">✅ 已保存</span>';
  }
}

// ===== INHERITANCE (场景9) =====
async function loadInheritanceMappings(partId) {
  const container = document.getElementById('inheritance-list');
  let url = 'inheritance/';
  if (partId) url += `?target_part=${parseInt(partId)}`;
  const res = await apiCall('GET', url);
  if (res.error) { container.innerHTML = '<span class="text-red-500 text-sm">加载失败</span>'; return; }
  const items = Array.isArray(res.data) ? res.data : (res.data.results || []);
  if (!items.length) { container.innerHTML = '<div class="empty-state"><div class="icon">⬇️</div><p>暂无继承映射</p></div>'; return; }
  let html = '<div class="overflow-x-auto"><table class="w-full text-xs border-collapse"><thead><tr class="bg-gray-50"><th class="p-2 text-left border-b font-semibold">目标零件</th><th class="p-2 text-left border-b font-semibold">目标参数</th><th class="p-2 text-left border-b font-semibold">源参数</th><th class="p-2 text-left border-b font-semibold">公式</th><th class="p-2 text-center border-b font-semibold">启用</th></tr></thead><tbody>';
  items.forEach(m => {
    html += `<tr class="border-b hover:bg-gray-50">
      <td class="p-2">${m.target_part_name}</td>
      <td class="p-2 font-medium">${m.target_template_name}</td>
      <td class="p-2 text-gray-500">${m.source_template_name||'(同名)'}</td>
      <td class="p-2"><code class="text-blue-600">${m.formula||'-'}</code></td>
      <td class="p-2 text-center">${m.enabled!==false?'✅':'❌'}</td>
    </tr>`;
  });
  html += '</tbody></table></div>';
  container.innerHTML = html;
}
async function openAddInheritanceModal() {
  const targetPart = prompt('目标零件 ID (接收参数的子零件):');
  if (!targetPart) return;
  const targetParam = prompt('目标参数名 (子零件上的参数名):');
  if (!targetParam) return;
  const sourceParam = prompt('源参数名 (父级参数，留空=同名):', targetParam);
  const formula = prompt('转换公式 (留空=直接传递):', '');

  // Find target template by name
  const templateRes = await fetch(`/api/parameter/template/?search=${encodeURIComponent(targetParam)}&limit=5`, {headers:{'Content-Type':'application/json','X-CSRFToken':getCsrfToken()}, credentials:'same-origin'});
  const tmplData = await templateRes.json();
  const tmpls = tmplData.results || tmplData || [];
  let targetTmplId = null;
  if (tmpls.length === 1) targetTmplId = tmpls[0].pk;
  else if (tmpls.length > 1) targetTmplId = parseInt(prompt(`找到多个参数模板:\n${tmpls.map(t=>t.pk+': '+t.name).join('\n')}\n输入ID:`));
  if (!targetTmplId) { alert('参数模板未找到，请在参数管理页先创建'); return; }

  let sourceTmplId = null;
  if (sourceParam && sourceParam !== targetParam) {
    const sRes = await fetch(`/api/parameter/template/?search=${encodeURIComponent(sourceParam)}&limit=5`, {headers:{'Content-Type':'application/json','X-CSRFToken':getCsrfToken()}, credentials:'same-origin'});
    const sData = await sRes.json();
    const sTmpls = sData.results || sData || [];
    if (sTmpls.length === 1) sourceTmplId = sTmpls[0].pk;
    else if (sTmpls.length > 1) sourceTmplId = parseInt(prompt(`找到多个源参数模板:\n${sTmpls.map(t=>t.pk+': '+t.name).join('\n')}\n输入ID:`));
  }

  const body = {target_part: parseInt(targetPart), target_template: targetTmplId, source_template: sourceTmplId, formula: formula || '', enabled: true};
  const saveRes = await apiCall('POST', 'inheritance/', body);
  if (!saveRes.error) {
    const sel = document.getElementById('inh-part-select');
    loadInheritanceMappings(sel?.value || '');
  }
}

// ===== ATTRIBUTE FORMULAS (场景11) =====
async function loadAttributeFormulas(partId) {
  const container = document.getElementById('attribute-list');
  let url = 'attributes/';
  if (partId) url += `?part=${parseInt(partId)}`;
  const res = await apiCall('GET', url);
  if (res.error) { container.innerHTML = '<span class="text-red-500 text-sm">加载失败</span>'; return; }
  const items = Array.isArray(res.data) ? res.data : (res.data.results || []);
  if (!items.length) { container.innerHTML = '<div class="empty-state"><div class="icon">🏷️</div><p>暂无属性公式</p></div>'; return; }
  let html = '<div class="overflow-x-auto"><table class="w-full text-xs border-collapse"><thead><tr class="bg-gray-50"><th class="p-2 text-left border-b font-semibold">零件</th><th class="p-2 text-left border-b font-semibold">属性</th><th class="p-2 text-left border-b font-semibold">类型</th><th class="p-2 text-left border-b font-semibold">公式</th><th class="p-2 text-left border-b font-semibold">单位</th></tr></thead><tbody>';
  items.forEach(a => {
    const typeLabels = {number:'数值', option:'选项', boolean:'布尔', text:'文本', multi_option:'多选项', long_text:'长文本', file_ref:'文件', part_ref:'零件'};
    html += `<tr class="border-b hover:bg-gray-50">
      <td class="p-2">${a.part_name}</td>
      <td class="p-2 font-medium">${a.attribute_name}</td>
      <td class="p-2"><span class="type-badge type-${a.attribute_type||'text'}">${typeLabels[a.attribute_type]||a.attribute_type}</span></td>
      <td class="p-2"><code class="text-blue-600 text-[10px]">${a.formula}</code></td>
      <td class="p-2 text-gray-500">${a.unit||'-'}</td>
    </tr>`;
  });
  html += '</tbody></table></div>';
  container.innerHTML = html;
}
async function openAddAttributeModal() {
  const partId = prompt('零件 ID:');
  if (!partId) return;
  const attrName = prompt('属性名称 (如: weight, color_code):');
  if (!attrName) return;
  const attrType = prompt('属性类型 (number/boolean/text/option):', 'text') || 'text';
  const formula = prompt('计算公式 (如: param.长度 * param.宽度 * 5 * 7.85 / 1000000):');
  if (!formula) return;
  const unit = prompt('单位 (如: kg, mm):', '');
  const body = {part: parseInt(partId), attribute_name: attrName, attribute_type: attrType, formula, unit};
  const res = await apiCall('POST', 'attributes/', body);
  if (!res.error) {
    const sel = document.getElementById('attr-part-select');
    loadAttributeFormulas(sel?.value || '');
  }
}

// ===== GLOBAL PRODUCT CONTEXT =====
let globalPartId = null;
let globalPartName = '';

function onGlobalPartChange(partId) {
  globalPartId = partId || null;
  const part = parts.find(p => p.pk == partId);
  globalPartName = part ? (part.name || part.full_name || '') : '';
  // Sync with product management state
  if (partId) {
    configuratorPartId = parseInt(partId);
    renderProductGrid();
  }
  // Auto-refresh current page if it depends on product
  const activePage = document.querySelector('.page-panel.active')?.id?.replace('page-', '');
  if (activePage === 'bom-formula') loadBomFormulaConfigs(partId || '');
  else if (activePage === 'param-types') loadParamConfigs(partId || '');
}

// ===== DASHBOARD =====
async function renderDashboard() {
  const container = document.getElementById('dashboard-content');
  if (!container) return;
  // Load stats
  const [cfgRes, bomRes, configRes] = await Promise.all([
    apiCall('GET', 'part-config/'),
    apiCall('GET', 'bom-item-config/'),
    apiCall('GET', 'configurations/'),
  ]);
  const pcfgs = !cfgRes.error ? (cfgRes.data.results || cfgRes.data || []) : [];
  const boms = !bomRes.error ? (bomRes.data.results || bomRes.data || []) : [];
  const configs = !configRes.error ? (configRes.data.results || configRes.data || []) : [];
  const products = parts || [];

  // Count products with parametric configs
  const partIds = new Set(pcfgs.map(c => c.part));
  const productsWithParams = partIds.size;
  const modeCounts = {};
  boms.forEach(b => {
    // Derive primary mode from enable flags
    let primary = 'standard';
    if (b.enable_structure) primary = 'structure';
    
    else if (b.enable_specification) primary = 'specification';
    else if (b.enable_variant) primary = 'variant';
    else if (b.enable_candidate) primary = 'candidate';
    else if (b.enable_conditional) primary = 'conditional';
    else if (b.enable_qty_formula) primary = 'qty_formula';
    modeCounts[primary] = (modeCounts[primary] || 0) + 1;
  });

  const modeLabels = {standard:'标准', qty_formula:'📐数量公式', conditional:'⚡条件包含', candidate:'🎯候选零件', variant:'🧬动态项目', specification:'📝规格描述', structure:'🏗️结构'};

  let html = `
  <!-- Quick Stats -->
  <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
      <div class="text-2xl font-bold text-blue-700">${productsWithParams}</div>
      <div class="text-[10px] text-blue-600 mt-0.5">已配参数的产品</div>
    </div>
    <div class="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-center">
      <div class="text-2xl font-bold text-emerald-700">${boms.length}</div>
      <div class="text-[10px] text-emerald-600 mt-0.5">参数化BOM项</div>
    </div>
    <div class="bg-purple-50 border border-purple-200 rounded-lg p-3 text-center">
      <div class="text-2xl font-bold text-purple-700">${configs.length}</div>
      <div class="text-[10px] text-purple-600 mt-0.5">已完成配置</div>
    </div>
  </div>

  <!-- Quick Start Guide -->
  <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-4">
    <div class="text-sm font-semibold text-gray-800 mb-3">🚀 快速开始 — 3步上手</div>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div class="bg-white rounded-lg p-3 border border-gray-100">
        <div class="flex items-center gap-2 mb-1.5"><span class="w-6 h-6 rounded-full bg-blue-600 text-white text-[10px] flex items-center justify-center font-bold">1</span><span class="text-xs font-semibold">配置参数</span></div>
        <p class="text-[10px] text-gray-500">选择产品 → 在「参数管理」绑定参数模板，设默认值</p>
      </div>
      <div class="bg-white rounded-lg p-3 border border-gray-100">
        <div class="flex items-center gap-2 mb-1.5"><span class="w-6 h-6 rounded-full bg-emerald-600 text-white text-[10px] flex items-center justify-center font-bold">2</span><span class="text-xs font-semibold">设BOM列表</span></div>
        <p class="text-[10px] text-gray-500">在「BOM列表」为各物料选择模式，编写公式</p>
      </div>
      <div class="bg-white rounded-lg p-3 border border-gray-100">
        <div class="flex items-center gap-2 mb-1.5"><span class="w-6 h-6 rounded-full bg-amber-600 text-white text-[10px] flex items-center justify-center font-bold">3</span><span class="text-xs font-semibold">测试配置器</span></div>
        <p class="text-[10px] text-gray-500">在「产品配置器」调参数 → 实时看BOM → 保存配置</p>
      </div>
    </div>
  </div>

  <!-- Mode Distribution -->
  <div class="bg-white border border-gray-100 rounded-lg p-3 mb-4">
    <div class="text-xs font-semibold text-gray-700 mb-2">📊 BOM模式分布</div>
    <div class="flex flex-wrap gap-1.5">
      ${Object.entries(modeCounts).map(([m, c]) =>
        `<span class="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">${modeLabels[m]||m}: ${c}</span>`
      ).join('') || '<span class="text-[10px] text-gray-400">暂无数据，先创建示例产品试试</span>'}
    </div>
  </div>

  <!-- Quick Actions -->
  <div class="flex flex-wrap gap-2">
    <button class="btn btn-primary btn-sm" onclick="switchPage('products')">🏷️ 产品管理</button>
    <button class="btn btn-secondary btn-sm" onclick="switchPage('products')" style="font-size:0.7rem">💡 点击产品卡片进入参数化配置</button>
  </div>`;

  container.innerHTML = html;
}

// ===== INIT ENHANCEMENT (overrides previous) =====
document.addEventListener('DOMContentLoaded', async function() {
  await loadParts();
  
  // Auto-load product from URL query parameter
  if (initialProductId) {
    const product = parts.find(p => p.pk == initialProductId);
    if (product) {
      // Switch to product detail page
      document.querySelectorAll('.page-panel').forEach(el => el.classList.remove('active'));
      document.getElementById('page-product-detail')?.classList.add('active');
      try { document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active')); } catch(e) {}
      
      configuratorPartId = parseInt(initialProductId);
      loadProductDetail(configuratorPartId);
    }
  }
  
  // Auto-switch to initial page (from URL ?page=...)
  // Only in non-standalone mode, and only if we didn't already switch to a product detail
  if (!standalone && initialPage && initialPage !== 'home' && !initialProductId) {
    try { switchPage(initialPage); } catch(e) {}
  }
  
  try { await loadConfigList(); } catch(e) {}

  // Override goConfigStep(2) to auto-expand BOM
  const origGoStep = goConfigStep;
  goConfigStep = function(step) {
    if (step === 2) { expandConfigBOM(); return; }
    origGoStep.call(this, step);
  };
  document.querySelector('[onclick="goConfigStep(2)"]')?.addEventListener('click', function(e) {
    e.preventDefault(); expandConfigBOM();
  });

  // Populate global part select
  // Populate other selects
  ['inh-part-select', 'attr-part-select'].forEach(id => {
    const sel = document.getElementById(id);
    if (sel && typeof parts !== 'undefined') {
      parts.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.pk; opt.textContent = `${p.name || p.full_name || 'Unnamed'} (ID:${p.pk})`;
        sel.appendChild(opt);
      });
    }
  });

  setStatus('idle', '就绪');
  try { renderDashboard(); } catch(e) {}

  // ── Unsaved changes warning on browser close/refresh ──
  window.addEventListener('beforeunload', function(e) {
    if (isAnyDirty()) {
      e.preventDefault();
      e.returnValue = '有未保存的修改，确定要离开吗？';
    }
  });
});

// ── Create Demo Product ──
async function createDemoProduct() {
  const btn = document.getElementById('btn-demo');
  if (!btn || btn.disabled) return;
  btn.disabled = true;
  btn.textContent = '⏳ 创建中...';
  setStatus('loading', '正在创建示例产品...');
  
  try {
    const productRes = await fetch('/api/part/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
      credentials: 'same-origin',
      body: JSON.stringify({name: '货架系统 (示例)'}),
    });
    if (!productRes.ok) {
      const errText = await productRes.text();
      let errMsg = errText;
      try { const j = JSON.parse(errText); errMsg = JSON.stringify(j).substring(0,300); } catch(e){}
      throw new Error(`创建产品失败: ${errMsg}`);
    }
    const product = await productRes.json();
    const productId = product.pk || product.id;
    
    const params = [
      {name:'总长度', type:'number', driving:true, comp:false, def:'3000', extra:{min_value:1000,max_value:6000}, order:10},
      {name:'总宽度', type:'number', driving:true, comp:false, def:'800', extra:{min_value:400,max_value:1500}, order:20},
      {name:'总高度', type:'number', driving:true, comp:false, def:'2000', extra:{min_value:1000,max_value:3000}, order:30},
      {name:'层数', type:'option', driving:true, comp:false, def:'3', extra:{options:['1','2','3','4','5']}, order:40},
      {name:'材质', type:'option', driving:true, comp:false, def:'钢', extra:{options:['钢','不锈钢','铝合金']}, order:50},
      {name:'颜色', type:'option', driving:true, comp:false, def:'白色', extra:{options:['白色','灰色','蓝色','定制']}, order:60},
      {name:'加强筋', type:'boolean', driving:true, comp:false, def:'true', extra:{}, order:70},
    ];
    
    for (const p of params) {
      await apiCall('POST', 'part-config/', {
        part: productId, name: p.name, parameter_type: p.type,
        is_driving: p.driving, is_computed: p.comp,
        default_value: p.def, display_order: p.order,
        ...p.extra,
      });
    }
    
    // Create sub-parts
    const subPartNames = ['立柱 (示例)','横梁 (示例)','层板 (示例)','加强筋 (示例)'];
    const qtys = [4, 4, 3, 1];
    const subParts = await Promise.all(subPartNames.map(name =>
      fetch('/api/part/', {method:'POST',
        headers:{'Content-Type':'application/json','X-CSRFToken':getCsrfToken()},
        credentials:'same-origin',
        body:JSON.stringify({name, description:`示例: ${name}`,
          component:true, assembly:false, active:true})
      }).then(async r => {
        if (!r.ok) { const t=await r.text(); console.warn(`创建子件 ${name} 失败:`, t); return null; }
        return r.json();
      })
    ));
    
    for (let i = 0; i < subParts.length; i++) {
      if (!subParts[i]) continue;
      await fetch('/api/bom/', {method:'POST',
        headers:{'Content-Type':'application/json','X-CSRFToken':getCsrfToken()},
        credentials:'same-origin',
        body:JSON.stringify({part:productId, sub_part:subParts[i].pk||subParts[i].id, quantity:qtys[i]})
      });
    }
    
    setStatus('success', `✅ 示例产品「${product.name}」已创建！`);
    btn.textContent = '✅ 已创建';
    setTimeout(() => window.location.reload(), 1500);
  } catch(e) {
    setStatus('error', `创建失败: ${e.message}`);
    btn.disabled = false;
    btn.textContent = '🚀 一键创建示例产品';
  }
}


// ── Cart: Add Static Part ──

async function cartAddStaticPart(partId, partName, partIpn) {
  if (!partId) { setStatus('error', '无效零件'); return; }
  const name = partName || '零件 #' + partId;
  const ipn = partIpn || '';
  const title = name + (ipn ? ' (' + ipn + ')' : '');
  
  // Check if already in cart
  const listRes = await fetch('/api/parametric-bom/cart/', {credentials: 'same-origin'});
  if (listRes.ok) {
    const items = await listRes.json();
    const existing = items.find(function(it) {
      return it.item_type === 'static' && it.part === partId;
    });
    if (existing) {
      // Increment quantity
      await fetch('/api/parametric-bom/cart/' + existing.id + '/', {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
        credentials: 'same-origin',
        body: JSON.stringify({quantity: (existing.quantity || 1) + 1})
      });
      setStatus('success', '✅ 数量+1: ' + name);
      return;
    }
  }

  const res = await fetch('/api/parametric-bom/cart/add/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
    credentials: 'same-origin',
    body: JSON.stringify({
      item_type: 'static',
      part: partId,
      title: title,
      quantity: 1
    })
  });
  if (res.ok) {
    setStatus('success', '✅ 已加入购物车: ' + name);
    // Update badge
    try {
      var cntRes = await fetch('/api/parametric-bom/cart/count/', {credentials: 'same-origin'});
      if (cntRes.ok) {
        var cntData = await cntRes.json();
        var cnt = cntData.count || 0;
        var badge = document.getElementById('cart-fab-count');
        if (badge) badge.textContent = cnt;
      }
    } catch(e) {}
  }
}

// ── Cart: Add from BOM configurator (cfgAddToCart) ──
// ── Cart: Add from product detail configurator tab ──

async function cfgAddToCart() {
  const pid = configuratorPartId;
  if (!pid) { setStatus('error', '请先选择产品'); return; }
  if (!cfgBOMItems || !cfgBOMItems.length) { setStatus('error', '请先展开BOM'); return; }

  const ctx = cfgGetParamContext();
  const partName = document.querySelector('#pd-product-name')?.textContent?.trim() || '参数化产品';

  // Build title from params
  const paramEntries = Object.entries(ctx || {}).slice(0, 3);
  const paramStr = paramEntries.map(function(kv) { return kv[0] + '=' + kv[1]; }).join(', ');
  const hasMore = Object.keys(ctx || {}).length > 3;
  const title = partName + (paramStr ? ' (' + paramStr + (hasMore ? '...' : '') + ')' : '');

  const res = await fetch('/api/parametric-bom/cart/add/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
    credentials: 'same-origin',
    body: JSON.stringify({
      item_type: 'parametric',
      product_part: pid,
      parameters: ctx,
      bom_snapshot: {bom_tree: cfgBOMItems, part_name: partName},
      title: title,
      quantity: 1
    })
  });
  if (res.ok) {
    setStatus('success', '✅ 已加入购物车');
    // Update badges
    try {
      var cntRes = await fetch('/api/parametric-bom/cart/count/', {credentials: 'same-origin'});
      if (cntRes.ok) {
        var cntData = await cntRes.json();
        var cnt = cntData.count || 0;
        var badge = document.getElementById('cart-fab-count');
        if (badge) badge.textContent = cnt;
        var panel = document.getElementById('cart-panel');
        var overlay = document.getElementById('cart-overlay');
        if (panel) panel.classList.add('open');
        if (overlay) overlay.classList.add('show');
      }
    } catch(e) {}
  } else {
    var err = await res.json();
    setStatus('error', '加入购物车失败: ' + JSON.stringify(err));
  }
}
