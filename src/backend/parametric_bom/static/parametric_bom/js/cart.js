/**
 * Cart - 全局购物车 (精简版)
 * 为 InvenTree 所有页面提供购物车浮动按钮和面板
 */

const CART_API_BASE = '/api/parametric-bom/cart';

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
  const priceHtml = unitPrice != null
    ? `<div class="ci-price">¥${unitPrice.toFixed(2)} × ${item.quantity || 1} = <strong>¥${lineTotal.toFixed(2)}</strong></div>`
    : '';
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

// ===== Part Detail Page: Inject "Add to Cart" =====
function initPartPageAddToCart() {
  // Match /web/part/<id>/ or /part/<id>/
  var m = window.location.pathname.match(/\/web\/part\/(\d+)/) || window.location.pathname.match(/\/part\/(\d+)/);
  if (!m) return;
  var partId = parseInt(m[1]);

  // Wait for the Vue SPA to render the part name
  var observer = new MutationObserver(function () {
    // InvenTree renders part name in an h1 or inside a heading element
    var headings = document.querySelectorAll('h1, h2, h3, h4');
    var partTitle = null;
    for (var i = 0; i < headings.length; i++) {
      var h = headings[i];
      // Look for a heading that contains text (not just icons)
      var txt = h.textContent.trim();
      if (txt.length > 1 && !h.querySelector('.cart-add-btn')) {
        partTitle = h;
        break;
      }
    }
    if (!partTitle) return;

    // Already added
    if (partTitle.querySelector('.cart-add-btn')) return;

    // Get part name from the heading
    var partName = partTitle.textContent.trim().replace(/[🛒➕]/g, '').trim();

    // Inject "Add to Cart" button
    var btn = document.createElement('button');
    btn.className = 'cart-add-btn';
    btn.innerHTML = '🛒 加入购物车';
    btn.style.cssText = 'margin-left:0.75rem;background:#2563eb;color:#fff;border:none;border-radius:6px;padding:0.375rem 0.75rem;font-size:0.8125rem;font-weight:500;cursor:pointer;transition:all 0.15s;vertical-align:middle';
    btn.onmouseover = function () { this.style.background = '#1d4ed8'; };
    btn.onmouseout = function () { this.style.background = '#2563eb'; };
    btn.onclick = function (e) {
      e.stopPropagation();
      addPartToCart(partId, partName);
    };
    partTitle.appendChild(btn);
    observer.disconnect();
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Stop observing after 15 seconds to avoid memory leaks
  setTimeout(function () { observer.disconnect(); }, 15000);
}

async function addPartToCart(partId, partName) {
  // Get unit price from pricing API
  var unitPrice = null;
  try {
    var pr = await fetch('/api/part/pricing/' + partId + '/', { credentials: 'same-origin' });
    if (pr.ok) {
      var pData = await pr.json();
      unitPrice = parseFloat(pData.overall_min || pData.overall_max || pData.internal_cost_min || pData.bom_cost_min || 0) || null;
    }
  } catch (e) {}

  // Check if already in cart
  var listRes = await cartApi('GET', '/');
  if (listRes.ok && Array.isArray(listRes.data)) {
    var existing = listRes.data.find(function (c) {
      return c.item_type === 'static' && c.part === partId;
    });
    if (existing) {
      // Increment quantity
      var updRes = await cartApi('PATCH', '/' + existing.id + '/', { quantity: (existing.quantity || 1) + 1 });
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
    title: partName || ('零件 #' + partId),
    quantity: 1,
  };
  if (unitPrice !== null) body.unit_price = String(unitPrice);

  var r = await cartApi('POST', '/add/', body);
  if (r.ok) {
    loadCartCount();
    cartToggle();
  }
}
