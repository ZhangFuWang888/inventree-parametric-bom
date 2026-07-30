/**
 * Cart - 全局购物车 (精简版)
 * 为 InvenTree 所有页面提供购物车浮动按钮和面板
 */

var CART_API_BASE = '/api/parametric-bom/cart';

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : '';
}

function csrfSafeMethod(method) {
  return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
}

async function cartApi(method, path, body, responseType) {
  const url = CART_API_BASE + path;
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (!csrfSafeMethod(method)) {
    opts.headers['X-CSRFToken'] = getCookie('csrftoken');
  }
  if (body && method !== 'GET') opts.body = JSON.stringify(body);
  try {
    if (responseType === 'blob') {
      delete opts.headers['Content-Type'];
      const resp = await fetch(url, opts);
      if (!resp.ok) return { ok: false, data: await resp.json().catch(() => ({})) };
      return { ok: true, data: await resp.blob() };
    }
    const resp = await fetch(url, opts);
    if (resp.status === 204) return { ok: true, data: null };
    const data = await resp.json();
    return { ok: resp.ok, data, status: resp.status };
  } catch (e) {
    return { ok: false, data: e.message };
  }
}

// ===== Count =====
async function loadCartCount() {
  const r = await cartApi('GET', '/count/');
  if (!r.ok) return;
  const c = r.data.count || 0;
  const els = document.querySelectorAll('.cart-badge, .sc-badge');
  els.forEach(el => { el.textContent = c; el.style.display = c > 0 ? '' : 'none'; });
}

// ===== Toggle =====
function cartToggle() {
  const panel = document.getElementById('cart-panel');
  const overlay = document.getElementById('cart-overlay');
  if (!panel) return;
  const open = panel.classList.contains('open');
  if (!open) {
    cartLoad();
    panel.classList.add('open');
    if (overlay) overlay.classList.add('show');
  } else {
    panel.classList.remove('open');
    if (overlay) overlay.classList.remove('show');
  }
}

function cartClose() {
  const panel = document.getElementById('cart-panel');
  const overlay = document.getElementById('cart-overlay');
  if (panel) panel.classList.remove('open');
  if (overlay) overlay.classList.remove('show');
}

// ===== Load =====
async function cartLoad() {
  const r = await cartApi('GET', '/');
  if (!r.ok) return;
  const items = r.data;
  const container = document.getElementById('cart-items');
  const footer = document.getElementById('cart-footer');
  if (!container) return;
  if (!items || items.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="icon">🛒</div><p>购物车是空的</p><p class="text-xs text-gray-400 mt-1">在产品页点击「加入购物车」添加物料</p></div>';
    if (footer) footer.style.display = 'none';
    return;
  }
  let html = '';
  let totalQty = 0;
  let totalAmount = 0;
  items.forEach(item => {
    totalQty += item.quantity || 1;
    const lineTotal = item.total_cost != null ? item.total_cost : (item.unit_price != null ? item.unit_price * (item.quantity || 1) : 0);
    totalAmount += lineTotal;
    html += renderCartItem(item);
  });
  container.innerHTML = html;
  const ti = document.getElementById('cart-total-items');
  if (ti) ti.textContent = totalQty + ' 件';
  const ta = document.getElementById('cart-total-amount');
  if (ta) ta.textContent = '¥' + totalAmount.toFixed(2);
  if (footer) footer.style.display = 'flex';
  loadCartCount();
}

function renderCartItem(item) {
  const isParametric = item.item_type === 'parametric';
  const icon = isParametric ? '📦' : '⚙️';
  const name = item.title || item.product_part_name || item.part_name || '未命名';
  const meta = isParametric
    ? `参数化产品 · ${item.product_part_ipn || ''}`
    : `静态零件 · ${item.part_ipn || ''} · ${item.part_unit || ''}`;
  const bomCount = item.bom_snapshot
    ? (Array.isArray(item.bom_snapshot) ? item.bom_snapshot.length : (item.bom_snapshot.bom_tree ? item.bom_snapshot.bom_tree.length : 0))
    : null;
  const bomInfo = bomCount ? ` · BOM: ${bomCount}项物料` : '';
  const unitPrice = item.unit_price != null ? parseFloat(item.unit_price) : null;
  const lineTotal = item.total_cost != null ? parseFloat(item.total_cost) : (unitPrice != null ? unitPrice * (item.quantity || 1) : null);
  const priceHtml = lineTotal != null
    ? `<div class="ci-price" style="color:#16a34a">¥${lineTotal.toFixed(2)} <span class="text-xs text-gray-400">× ${item.quantity || 1}</span></div>`
    : (unitPrice != null
      ? `<div class="ci-price" style="color:#16a34a">¥${(unitPrice * (item.quantity || 1)).toFixed(2)} <span class="text-xs text-gray-400">× ${item.quantity || 1}</span></div>`
      : '');
  return `<div class="cart-item" data-id="${item.id}">
    <div class="ci-icon">${icon}</div>
    <div class="ci-body">
      <div class="ci-title">${escHtml(name)}</div>
      <div class="ci-meta">${meta}${bomInfo}</div>
      ${priceHtml}
      <div class="ci-actions">
        <div class="ci-qty">
          <input type="number" min="1" max="9999" value="${item.quantity || 1}" onchange="cartUpdateQty(${item.id}, this.value)" onfocus="this.select()">
        </div>
        <button class="ci-del" onclick="cartDeleteItem(${item.id})">🗑️ 删除</button>
      </div>
    </div>
  </div>`;
}

function escHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ===== Item Actions =====
async function cartUpdateQty(id, qty) {
  qty = parseInt(qty) || 1;
  if (qty < 1) qty = 1;
  if (qty > 9999) qty = 9999;
  const r = await cartApi('PATCH', '/' + id + '/', { quantity: qty });
  if (r.ok) { loadCartCount(); cartLoad(); }
}

async function cartDeleteItem(id) {
  const r = await cartApi('DELETE', '/' + id + '/');
  if (r.ok) { loadCartCount(); cartLoad(); }
}

async function cartClear() {
  if (!confirm('确认清空购物车吗？')) return;
  const r = await cartApi('POST', '/clear/');
  if (r.ok) { loadCartCount(); cartLoad(); }
}

async function cartExportCSV() {
  const r = await cartApi('GET', '/export-csv/', null, 'blob');
  if (!r.ok) return;
  const blob = await r.data;
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '购物车订单_' + new Date().toISOString().slice(0, 10) + '.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function cartCreateOrder() {
  const totalEl = document.getElementById('cart-total-items');
  const qtyText = totalEl ? totalEl.textContent : '';
  if (!confirm('确认将购物车中的 ' + qtyText + ' 物料创建为销售订单吗？')) return;
  const r = await cartApi('POST', '/create-order/', { description: '参数化BOM购物车订单' });
  if (!r.ok) {
    const err = r.data?.error || '创建订单失败';
    alert('❌ ' + err);
    return;
  }
  const data = r.data;
  alert('✅ 销售订单已创建！\n订单号: ' + (data.order_reference || data.order_id) + '\n行项数: ' + data.line_items);
  cartClose();
  loadCartCount();
  cartLoad();
}

// ===== Init on Page Load =====
document.addEventListener('DOMContentLoaded', function () {
  loadCartCount();
  initPartPageAddToCart();
});

// ===== Part Detail Page: "Add to Cart" Button =====
var _partBtnObserver = null;

function initPartPageAddToCart() {
  // Only inject on part detail pages (not parametric BOM pages)
  if (window.location.pathname.includes('/parametric-bom/')) return;

  // Use MutationObserver to handle both direct loads and SPA navigation
  var lastUrl = window.location.pathname;
  if (_partBtnObserver) _partBtnObserver.disconnect();

  _partBtnObserver = new MutationObserver(function () {
    // Detect SPA route changes
    if (window.location.pathname !== lastUrl) {
      lastUrl = window.location.pathname;
      // Remove cart button when navigating away from part page
      var oldBtn = document.querySelector('.cart-add-btn-global');
      if (oldBtn) oldBtn.remove();
    }
    // Re-inject if React removed it (debounced via guard check)
    tryInjectPartButton();
  });

  _partBtnObserver.observe(document.body, { childList: true, subtree: true });

  // Also try immediately and on URL hash/state changes
  tryInjectPartButton();
  window.addEventListener('popstate', function () {
    setTimeout(tryInjectPartButton, 300);
  });
}

function tryInjectPartButton() {
  var m = window.location.pathname.match(/\/web\/part\/(\d+)/) || window.location.pathname.match(/\/part\/(\d+)/);
  if (!m) return;
  var partId = parseInt(m[1]);

  // Already added
  if (document.querySelector('.cart-add-btn-global')) return true;

  // Find the page header Paper (contains the part title + action buttons)
  var papers = document.querySelectorAll('[class*="mantine-Paper"]');
  var paper = null;
  for (var i = 0; i < papers.length; i++) {
    var p = papers[i];
    var btns = p.querySelectorAll('button');
    if (btns.length >= 2 && p.offsetHeight > 0) {
      paper = p;
      break;
    }
  }
  if (!paper) return false;

  // Find the right-side actions Group inside the Paper
  var groups = paper.querySelectorAll('[class*="mantine-Group"]');
  var actionGroup = null;
  for (var i = 0; i < groups.length; i++) {
    var g = groups[i];
    // The right-side action group has multiple buttons and is the last group
    if (g.querySelectorAll('button, a, [role="button"]').length >= 1 &&
        g.offsetHeight > 0 &&
        (i === groups.length - 1 || g.querySelectorAll('button').length >= 2)) {
      actionGroup = g;
      break;
    }
  }

  if (actionGroup) {
    // Wrapper to group qty input + add button together
    var wrapper = document.createElement('span');
    wrapper.className = 'cart-add-btn-global';
    wrapper.style.cssText = 'display:inline-flex;align-items:center;gap:2px;margin-left:6px';

    var qtyInput = document.createElement('input');
    qtyInput.type = 'number';
    qtyInput.min = 1;
    qtyInput.max = 9999;
    qtyInput.value = 1;
    qtyInput.id = 'cart-add-qty-' + partId;
    qtyInput.style.cssText = 'width:44px;height:36px;border:1px solid #d0d5dd;border-radius:4px;text-align:center;font-size:14px;padding:0;outline:none;box-sizing:border-box';
    qtyInput.onfocus = function () { this.select(); };

    var btn = document.createElement('button');
    btn.innerHTML = '🛒 加入购物车';
    btn.style.cssText = 'display:inline-flex;align-items:center;gap:4px;background:#228be6;color:#fff;border:none;border-radius:4px;padding:0 12px;font-size:14px;font-weight:500;cursor:pointer;white-space:nowrap;line-height:1;height:36px';
    btn.onmouseover = function () { this.style.background = '#1c7ed6'; };
    btn.onmouseout = function () { this.style.background = '#228be6'; };
    btn.onclick = function (e) {
      e.preventDefault();
      e.stopPropagation();
      var qty = parseInt(document.getElementById('cart-add-qty-' + partId).value) || 1;
      addPartToCart(partId, '', qty);
    };
    wrapper.appendChild(qtyInput);
    wrapper.appendChild(btn);
    actionGroup.appendChild(wrapper);
    return true;
  }

  return false;
}

async function addPartToCart(partId, partName, qty) {
  qty = qty || 1;

  // Fire all API calls in parallel, then decide
  var results = await Promise.allSettled([
    // [0] Part info
    fetch('/api/part/' + partId + '/', { credentials: 'same-origin' }).catch(function(){}),
    // [1] Pricing info
    fetch('/api/part/pricing/' + partId + '/', { credentials: 'same-origin' }).catch(function(){}),
    // [2] Current cart list (for dedup check)
    cartApi('GET', '/'),
    // [3] Check if part is parametric (has PartParameterConfig)
    fetch('/api/parametric-bom/part-config/?part=' + partId + '&is_driving=true', {
      credentials: 'same-origin',
      headers: {'X-CSRFToken': getCookie('csrftoken')}
    }).catch(function(){}),
  ]);

  // Resolve part info
  var displayName = partName || ('零件 #' + partId);
  if (results[0].status === 'fulfilled' && results[0].value && results[0].value.ok) {
    try {
      var pd = await results[0].value.json();
      if (pd.full_name) displayName = pd.full_name;
      else if (pd.name) displayName = pd.name;
      else if (pd.IPN) displayName = pd.IPN + ' - ' + (pd.name || '');
    } catch (e) {}
  }

  // Resolve pricing (optional)
  var unitPrice = null;
  if (results[1].status === 'fulfilled' && results[1].value && results[1].value.ok) {
    try {
      var pData = await results[1].value.json();
      unitPrice = parseFloat(pData.overall_min || pData.overall_max || pData.internal_cost_min || pData.bom_cost_min || 0) || null;
    } catch (e) {}
  }

  // ── Parametric detection ──
  var paramConfigs = [];
  if (results[3].status === 'fulfilled' && results[3].value && results[3].value.ok) {
    try {
      var pcfgJson = await results[3].value.json();
      paramConfigs = Array.isArray(pcfgJson) ? pcfgJson : (pcfgJson.results || []);
    } catch (e) {}
  }

  if (paramConfigs.length > 0) {
    // Part is parametric → show configurator modal
    showParametricModal(partId, displayName, paramConfigs, qty, unitPrice);
    return;
  }

  // ── Static part: add directly ──

  // Check if already in cart → increment
  if (results[2].status === 'fulfilled' && results[2].value && results[2].value.ok && Array.isArray(results[2].value.data)) {
    var existing = results[2].value.data.find(function (c) {
      return c.item_type === 'static' && c.part === partId;
    });
    if (existing) {
      var updRes = await cartApi('PATCH', '/' + existing.id + '/', { quantity: (existing.quantity || 1) + qty });
      if (updRes.ok) {
        loadCartCount();
        cartToggle();
        return;
      }
    }
  }

  // Add to cart
  var body = {
    item_type: 'static',
    part: partId,
    title: displayName,
    quantity: qty,
  };
  if (unitPrice !== null) body.unit_price = String(unitPrice);

  var r = await cartApi('POST', '/add/', body);
  if (r.ok) {
    loadCartCount();
    cartToggle();
  }
}


// ── Parametric configurator modal ──

function showParametricModal(partId, displayName, paramConfigs, qty, unitPrice) {
  // Build modal HTML
  var sorted = (paramConfigs || []).sort(function(a, b) { return (a.display_order || 0) - (b.display_order || 0); });

  // Params in double-column grid
  var inputsHtml = '';
  sorted.forEach(function(cfg) {
    var pname = cfg.template_name || cfg.name || ('param_' + cfg.id);
    var defVal = cfg.default_value != null ? cfg.default_value : '';
    inputsHtml += renderParamInput(cfg, pname, defVal);
  });

  var html = '<div id="pm-overlay" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.45);z-index:99999;display:flex;align-items:center;justify-content:center;" onclick="if(event.target===this)closeParamModal()">'
    + '<div style="background:#fff;border-radius:12px;width:960px;max-width:98vw;max-height:92vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,0.3);padding:24px;">'
    // ── Header ──
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
    + '<h3 style="font-size:18px;font-weight:700;margin:0;">🔧 配置参数</h3>'
    + '<button onclick="closeParamModal()" style="background:none;border:none;font-size:20px;cursor:pointer;color:#999;line-height:1;">×</button>'
    + '</div>'
    + '<p style="color:#6b7280;font-size:13px;margin:0 0 16px 0;">' + escHtml(displayName) + ' &nbsp;<span style="font-size:11px;color:#9ca3af;">×' + qty + '</span></p>'
    // ── Two-column body ──
    + '<div style="flex:1;overflow:hidden;display:flex;gap:20px;min-height:0;">'
    // LEFT column — BOM
    + '<div style="flex:1;min-width:260px;overflow:hidden;display:flex;flex-direction:column;">'
    + '<div id="pm-bom-result" style="flex:1;overflow-y:auto;font-size:12px;color:#9ca3af;padding-top:4px;min-height:0;">修改参数后自动展开BOM</div>'
    + '</div>'
    // RIGHT column — Parameters
    + '<div style="flex:0 0 300px;min-width:240px;display:flex;flex-direction:column;border-left:1px solid #e5e7eb;padding-left:16px;">'
    + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">' + inputsHtml + '</div>'
    + '<div style="margin-top:auto;padding-top:14px;">'
    + '<button id="pm-submit-btn" onclick="submitParametricCart(' + partId + ',\'' + escAttr(displayName) + '\',' + qty + ',' + (unitPrice !== null ? unitPrice : 'null') + ')" style="padding:6px 18px;background:#228be6;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600;">🛒 加入购物车</button>'
    + '</div>'
    + '</div>'
    + '</div>'
    + '</div></div>';

  document.body.insertAdjacentHTML('beforeend', html);

  // ── Auto-refresh BOM on parameter change (debounced 600ms) ──
  var _pmDebounce = null;
  document.querySelectorAll('#pm-overlay [data-pname]').forEach(function(el) {
    el.addEventListener('input', function() {
      clearTimeout(_pmDebounce);
      _pmDebounce = setTimeout(function() { expandParamBOM(partId, qty); }, 600);
    });
  });

  // Initial BOM expansion
  expandParamBOM(partId, qty);
}


function closeParamModal() {
  var el = document.getElementById('pm-overlay');
  if (el) el.remove();
}


function renderParamInput(cfg, paramName, defVal) {
  var type = cfg.parameter_type || 'number';
  var options = cfg.options;
  var hint = cfg.ui_hint ? '<span style="font-size:11px;color:#9ca3af;display:block;margin-top:2px;">' + escHtml(cfg.ui_hint) + '</span>' : '';
  var safeName = paramName.replace(/\\s+/g, '_').replace(/[^A-Za-z0-9_\\u4e00-\\u9fff]/g, '_');
  var inputId = 'pm-input-' + safeName;
  var labelHtml = '<label style="font-size:13px;font-weight:600;color:#374151;display:block;margin-bottom:4px;" for="' + inputId + '">' + escHtml(paramName) + '</label>';

  if (type === 'boolean') {
    var checked = defVal === 'true' || defVal === true ? ' checked' : '';
    return '<div>' + labelHtml + '<select id="' + inputId + '" data-pname="' + escAttr(paramName) + '" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:14px;">'
      + '<option value="true"' + (defVal === 'true' || defVal === true ? ' selected' : '') + '>是</option>'
      + '<option value="false"' + (defVal === 'false' || defVal === false ? ' selected' : '') + '>否</option>'
      + '</select>' + hint + '</div>';
  }

  if (type === 'option' || type === 'multi_option') {
    var opts = (options || '').toString().split(/[,;，；\\n]+/).filter(Boolean).map(function(s) { return s.trim(); });
    if (opts.length === 0) opts = [''];
    var selHtml = '<select id="' + inputId + '" data-pname="' + escAttr(paramName) + '" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:14px;">';
    opts.forEach(function(o) {
      selHtml += '<option value="' + escAttr(o) + '"' + (o === String(defVal) ? ' selected' : '') + '>' + escHtml(o) + '</option>';
    });
    selHtml += '</select>';
    return '<div>' + labelHtml + selHtml + hint + '</div>';
  }

  if (type === 'text' || type === 'long_text') {
    return '<div>' + labelHtml + '<input id="' + inputId + '" data-pname="' + escAttr(paramName) + '" type="text" value="' + escAttr(String(defVal)) + '" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:14px;" placeholder="请输入"/>' + hint + '</div>';
  }

  // number (default)
  return '<div>' + labelHtml + '<input id="' + inputId + '" data-pname="' + escAttr(paramName) + '" type="number" value="' + escAttr(String(defVal)) + '" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:14px;" step="any"/>' + hint + '</div>';
}


async function submitParametricCart(partId, displayName, qty, unitPrice) {
  var btn = document.getElementById('pm-submit-btn');
  if (btn) { btn.disabled = true; btn.textContent = '添加中...'; }

  // Collect parameter values from the modal
  var params = {};
  var inputs = document.querySelectorAll('#pm-overlay [data-pname]');
  inputs.forEach(function(el) {
    params[el.getAttribute('data-pname')] = el.value;
  });

  var body = {
    item_type: 'parametric',
    product_part: partId,
    title: displayName,
    quantity: qty,
    parameters: params,
  };
  if (unitPrice !== null) body.unit_price = String(unitPrice);

  var r = await cartApi('POST', '/add/', body);
  if (r.ok) {
    closeParamModal();
    loadCartCount();
    cartToggle();
  } else {
    if (btn) { btn.disabled = false; btn.textContent = '🛒 加入购物车'; }
    var errMsg = '添加失败';
    try {
      var errData = await r.data;
      if (errData && errData.error) errMsg = errData.error;
      else if (errData && errData.detail) errMsg = errData.detail;
    } catch(e) {}
    alert('❌ ' + errMsg);
  }
}


// ── BOM expansion in modal ──

async function expandParamBOM(partId, batchQty) {
  var btn = document.getElementById('pm-bom-btn');
  var resultDiv = document.getElementById('pm-bom-result');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ 计算中...'; }
  resultDiv.innerHTML = '<div style="color:#9ca3af;font-size:12px;padding:8px 0;">计算中...</div>';

  // Collect current param values
  var params = {};
  var inputs = document.querySelectorAll('#pm-overlay [data-pname]');
  inputs.forEach(function(el) {
    params[el.getAttribute('data-pname')] = el.value;
  });

  try {
    // Simultaneous BOM expand + cost estimate
    var [bomRes, costRes] = await Promise.all([
      fetch('/api/parametric-bom/evaluate/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')},
        credentials: 'same-origin',
        body: JSON.stringify({part_id: parseInt(partId), parameters: params}),
      }),
      fetch('/api/parametric-bom/estimate-cost/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')},
        credentials: 'same-origin',
        body: JSON.stringify({part_id: parseInt(partId), parameters: params}),
      }),
    ]);

    var bomData = bomRes.ok ? (await bomRes.json()) : null;
    var costData = costRes.ok ? (await costRes.json()) : null;

    if (!bomData) {
      resultDiv.innerHTML = '<div style="color:#dc2626;font-size:12px;padding:8px 0;">❌ BOM展开失败</div>';
      if (btn) { btn.disabled = false; btn.textContent = '📊 展开BOM & 成本'; }
      return;
    }

    var bomTree = bomData.bom_tree || {};
    var children = Array.isArray(bomTree) ? bomTree : (bomTree.children || []);

    // Flatten BOM tree
    var flatRows = [];
    function flatten(items, depth, parentQty) {
      items.forEach(function(child) {
        if (child.excluded) return;
        var name = child.calculated_name || child.variant_name || child.actual_part_name || child.part_name || '—';
        var ipn = child.calculated_ipn || child.variant_ipn || child.IPN || '';
        var unitQty = child.calculated_quantity || child.quantity || 1;
        var totalQty = unitQty * parentQty * batchQty;
        var unitP = child.unit_price != null ? parseFloat(child.unit_price) : null;
        var totalP = child.total_price != null ? parseFloat(child.total_price) : (unitP != null ? unitP * totalQty : null);
        flatRows.push({name: name, ipn: ipn, qty: totalQty, unitPrice: unitP, totalPrice: totalP, depth: depth});
        if (child.children && child.children.length > 0) {
          flatten(child.children, depth + 1, unitQty * parentQty);
        }
      });
    }
    flatten(children, 0, 1);

    // Render BOM table
    if (flatRows.length === 0) {
      resultDiv.innerHTML = '<div style="color:#9ca3af;font-size:12px;padding:8px 0;">BOM 展开为空</div>';
    } else {
      var totalCost = 0;
      var rowsHtml = '';
      flatRows.forEach(function(r) {
        var indent = '&nbsp;&nbsp;'.repeat(r.depth) + (r.depth > 0 ? '└ ' : '');
        var priceStr = r.totalPrice != null ? '¥' + r.totalPrice.toFixed(2) : '—';
        if (r.totalPrice != null && !isNaN(r.totalPrice)) totalCost += r.totalPrice;
        var qtyStr = (Math.round(r.qty * 100) / 100).toString();  // clean float
        rowsHtml += '<tr style="border-bottom:1px solid #f0f0f0;">'
          + '<td style="padding:4px 6px;white-space:nowrap;max-width:200px;overflow:hidden;text-overflow:ellipsis;">' + indent + escHtml(r.name) + '</td>'
          + '<td style="padding:4px 6px;color:#9ca3af;font-size:11px;white-space:nowrap;">' + escHtml(r.ipn) + '</td>'
          + '<td style="padding:4px 6px;text-align:right;white-space:nowrap;">' + qtyStr + '</td>'
          + '<td style="padding:4px 6px;text-align:right;white-space:nowrap;">' + priceStr + '</td>'
          + '</tr>';
      });

      var costSummary = '';
      if (costData) {
        costSummary = '<div style="margin-top:10px;padding:10px;background:#f0f9ff;border-radius:8px;">'
          + '<span style="font-weight:600;">💰 成本估算</span>'
          + '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:6px;font-size:12px;">'
          + '<div>材料: <strong>' + (costData.material_cost != null ? '¥' + costData.material_cost : '—') + '</strong></div>'
          + '<div>人工: <strong>' + (costData.labor_cost != null ? '¥' + costData.labor_cost : '—') + '</strong></div>'
          + '<div>合计: <strong style="color:#228be6;">' + (costData.total_cost != null ? '¥' + costData.total_cost : '—') + '</strong></div>'
          + '</div></div>';
      }

      resultDiv.innerHTML = '<div style="display:flex;flex-direction:column;height:100%;margin-top:4px;">'
        + '<div style="flex-shrink:0;color:#6b7280;font-size:11px;margin-bottom:4px;">共 ' + flatRows.length + ' 项</div>'
        + '<div style="flex:1;overflow-y:auto;min-height:0;">'
        + '<table style="width:100%;border-collapse:collapse;font-size:12px;">'
        + '<thead><tr style="background:#f9fafb;font-weight:600;text-align:left;border-bottom:2px solid #e5e7eb;position:sticky;top:0;z-index:1;">'
        + '<th style="padding:4px 6px;">物料</th><th style="padding:4px 6px;">型号</th><th style="padding:4px 6px;text-align:right;">数量</th><th style="padding:4px 6px;text-align:right;">总价</th>'
        + '</tr></thead><tbody>' + rowsHtml + '</tbody></table>'
        + '</div>'
        + (costSummary ? '<div style="flex-shrink:0;margin-top:8px;">' + costSummary + '</div>' : '')
        + '</div>';
    }
  } catch(e) {
    resultDiv.innerHTML = '<div style="color:#dc2626;font-size:12px;padding:8px 0;">❌ 展开出错: ' + escHtml(e.message) + '</div>';
  }

  if (btn) { btn.disabled = false; btn.textContent = '📊 展开BOM & 成本'; }
}


// ── Helpers ──

function escHtml(s) {
  var d = document.createElement('div');
  d.appendChild(document.createTextNode(String(s)));
  return d.innerHTML;
}

function escAttr(s) {
  return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
