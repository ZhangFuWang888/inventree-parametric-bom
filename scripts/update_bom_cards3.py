#!/usr/bin/env python3
"""Replace only loadBomFormulaConfigs + loadAllBomFormulaConfigs with card version.
Does NOT touch loadPdBOMM or any other function."""
import re

path = '/root/inventree-source/InvenTree-master/src/backend/parametric_bom/templates/parametric_bom/configurator.html'
with open(path, 'r') as f:
    content = f.read()

# ==========================================================
# 1. Replace loadBomFormulaConfigs
# ==========================================================
old_func_start = content.find('async function loadBomFormulaConfigs(partId) {')
old_func_end = content.find('\n// ── 全部参数化BOM项一览', old_func_start)

if old_func_start < 0 or old_func_end < 0:
    print("ERROR: Could not find loadBomFormulaConfigs")
else:
    new_func = '''async function loadBomFormulaConfigs(partId) {
  if (!partId) { document.getElementById('bom-formula-list').innerHTML = '<div class="empty-state"><div class="icon">📋</div><p>请选择产品</p></div>'; return; }
  const container = document.getElementById('bom-formula-list');
  container.innerHTML = '<div class="flex items-center justify-center py-3"><span class="spinner mr-2"></span><span class="text-sm text-gray-400">加载中...</span></div>';

  // ── "全部" 模式 ──
  if (partId === '__all__') {
    return loadAllBomFormulaConfigs(container);
  }

  // ── 单个产品模式 - 卡片式 ──
  const pid = parseInt(partId);
  const [bomRes, pcfgRes] = await Promise.all([
    fetch('/api/bom/?part=' + pid + '&sub_part_detail=True&part_detail=True', {headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()}, credentials: 'same-origin'}),
    apiCall('GET', 'bom-item-config/?bom_item__part=' + pid),
  ]);

  const bomItems = bomRes.ok ? (await bomRes.json()) : [];
  const items = Array.isArray(bomItems) ? bomItems : (bomItems.results || []);
  const pcfgs = pcfgRes.error ? [] : (Array.isArray(pcfgRes.data) ? pcfgRes.data : (pcfgRes.data.results || []));
  const pcfgMap = {};
  pcfgs.forEach(function(c) { pcfgMap[c.bom_item] = c; });

  if (!items.length) {
    container.innerHTML = '<div class="empty-state"><div class="icon">📋</div><p>该产品暂无BOM项，先在InvenTree的<strong>产品→BOM标签页</strong>中添加子件</p></div>';
    return;
  }

  // Load part params for parameter pill buttons
  const paramsRes = await apiCall('GET', 'part-config/?part=' + pid);
  const partParams = paramsRes.error ? [] : (Array.isArray(paramsRes.data) ? paramsRes.data : (paramsRes.data.results || []));

  var modeMeta = [
    {flag:'enable_qty_formula', key:'qty_formula', icon:'📐', label:'数量公式', desc:'动态计算此BOM项的数量'},
    {flag:'enable_conditional', key:'conditional', icon:'⚡', label:'条件包含', desc:'由条件公式决定是否包含'},
    {flag:'enable_candidate', key:'candidate', icon:'🎯', label:'候选零件', desc:'从候选零件列表中动态选择'},
    {flag:'enable_variant', key:'variant', icon:'🧬', label:'变体生成', desc:'从模板生成变体零件'},
    {flag:'enable_specification', key:'specification', icon:'📝', label:'规格描述', desc:'通过规格文字描述外协'},
    {flag:'enable_supplier', key:'supplier', icon:'🏢', label:'供应商选择', desc:'动态选择供应商'},
    {flag:'enable_structure', key:'structure', icon:'🔗', label:'结构控制', desc:'控制子装配结构'},
  ];

  var html = '<div class="text-xs text-gray-500 mb-2">共 ' + items.length + ' 个BOM项</div><div class="space-y-1">';

  for (var ii = 0; ii < items.length; ii++) {
    var item = items[ii];
    var subPartName = item.sub_part_detail ? item.sub_part_detail.name : '#' + item.sub_part;
    var subPartRef = item.sub_part_detail ? (item.sub_part_detail.ipn || '') : '';
    var cfg = pcfgMap[item.pk];
    var hasCfg = !!cfg;

    // Read enable flags
    var enabledFlags = {};
    modeMeta.forEach(function(m) { enabledFlags[m.key] = cfg ? !!cfg[m.flag] : false; });

    // Build active badges for header
    var badgeHtml = '';
    modeMeta.forEach(function(m) {
      if (enabledFlags[m.key]) badgeHtml += '<span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 ml-1">' + m.icon + ' ' + m.label + '</span>';
    });
    if (!badgeHtml) badgeHtml = '<span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-400 ml-1">标准</span>';

    // Build checkbox toggles
    var toggleHtml = '';
    modeMeta.forEach(function(m) {
      toggleHtml += '<label class="bic-toggle">'
        + '<input type="checkbox" data-bom="' + item.pk + '" data-mode-key="' + m.key + '" ' + (enabledFlags[m.key] ? 'checked' : '') + ' onchange="onBomModeToggle(' + item.pk + ", '" + m.key + "', this.checked)\">"
        + '<span class="bic-toggle-box"></span>'
        + '<span class="bic-toggle-label">' + m.icon + ' ' + m.label + '</span>'
        + '<span class="bic-toggle-desc">' + m.desc + '</span>'
        + '</label>';
    });

    // Build formula fields
    var formulaFields = '';
    var qtyVal = hasCfg ? (cfg.qty_formula || '') : '';
    formulaFields += '<div class="bic-field" data-mode-field="qty_formula">'
      + '<label><span class="bic-icon-qty">📐</span> 数量公式</label>'
      + '<div class="bic-input-wrap">'
      + '<input type="text" class="bic-fmla-input" data-bom="' + item.pk + '" data-field="qty_formula" value="' + qtyVal.replace(/"/g,'&quot;') + '" placeholder="例: CEIL(param.长度 / 500) * 2">'
      + '<button class="bic-validate-btn" onclick="validateBomFormula(' + item.pk + ", 'qty_formula')\">✓验证</button>"
      + '</div></div>';

    var condVal = hasCfg ? (cfg.condition_formula || '') : '';
    formulaFields += '<div class="bic-field" data-mode-field="conditional">'
      + '<label><span class="bic-icon-cond">⚡</span> 条件公式</label>'
      + '<div class="bic-input-wrap">'
      + '<input type="text" class="bic-fmla-input" data-bom="' + item.pk + '" data-field="condition_formula" value="' + condVal.replace(/"/g,'&quot;') + '" placeholder="例: param.速度 > 15">'
      + '<button class="bic-validate-btn" onclick="validateBomFormula(' + item.pk + ", 'condition_formula')\">✓验证</button>"
      + '</div></div>';

    var selVal = hasCfg ? (cfg.part_selector_formula || '') : '';
    formulaFields += '<div class="bic-field" data-mode-field="candidate">'
      + '<label><span class="bic-icon-part">🎯</span> 选件/变体公式</label>'
      + '<div class="bic-input-wrap">'
      + '<input type="text" class="bic-fmla-input" data-bom="' + item.pk + '" data-field="part_selector_formula" value="' + selVal.replace(/"/g,'&quot;') + '" placeholder="例: IF(speed>15, MOTOR-A, MOTOR-B)">'
      + '<button class="bic-validate-btn" onclick="validateBomFormula(' + item.pk + ", 'part_selector_formula')\">✓验证</button>"
      + '</div></div>';

    formulaFields += '<div class="bic-field" data-mode-field="specification">'
      + '<div class="text-[11px] text-slate-400 italic p-2 bg-slate-50 rounded-lg">📝 规格描述模式：在下方配置规格参数</div></div>';
    formulaFields += '<div class="bic-field" data-mode-field="supplier">'
      + '<div class="text-[11px] text-slate-400 italic p-2 bg-slate-50 rounded-lg">🏢 供应商选择模式：在下方配置供应商规则</div></div>';
    formulaFields += '<div class="bic-field" data-mode-field="structure">'
      + '<div class="text-[11px] text-slate-400 italic p-2 bg-slate-50 rounded-lg">🔗 结构控制：此BOM项的子项结构由参数动态决定</div></div>';

    // Parameter pills
    var paramPills = '';
    partParams.forEach(function(p) {
      var pname = p.template_name || p.name || p.parameter_name || (p.parameter_template_detail ? p.parameter_template_detail.name : '') || '';
      if (pname) {
        var escaped = pname.replace(/'/g,"\\'");
        paramPills += '<span class="bic-param-pill" onclick="insertBomParam(' + item.pk + ", 'param." + escaped + "')\">" + pname + '</span>';
      }
    });

    // Function pills
    var mathFns = ['CEIL()','FLOOR()','ROUND()','IF()','AND()','OR()','MIN()','MAX()','SUM()','AVG()','POW()','SQRT()','MOD()','ABS()','COUNT()'];
    var strFns = ['CONCAT()','LEFT()','RIGHT()','MID()','LEN()','FIND()','UPPER()','LOWER()','TRIM()','REPLACE()','SUBSTITUTE()'];
    var trigFns = ['SIN()','COS()','TAN()','ASIN()','ACOS()','ATAN()','ATAN2()','DEGREES()','RADIANS()'];
    var otherFns = ['INT()','FLOAT()','STR()','BOOL()','LET()'];
    var fnPills = '';
    [['📐 数学',mathFns],['🔤 字符串',strFns],['📐 三角',trigFns],['🔀 转换',otherFns]].forEach(function(g) {
      var label = g[0], fnList = g[1];
      fnPills += '<span class="text-[10px] text-slate-400 mr-0.5" style="align-self:center">' + label + ':</span>';
      fnList.forEach(function(fn) {
        fnPills += '<span class="bic-fn-pill" onclick="insertBomParam(' + item.pk + ", '" + fn + "')\">" + fn + '</span>';
      });
    });

    var statusId = 'bic-status-' + item.pk;

    html += '<div class="bom-inline-card" id="bic-' + item.pk + '">'
      + '<div class="bic-header" onclick="toggleBomCard(' + item.pk + ')">'
      + '<span class="bic-name">' + subPartName + '</span>'
      + (subPartRef ? '<span class="bic-ref">' + subPartRef + '</span>' : '')
      + '<span class="bic-qty">×' + item.quantity + '</span>'
      + badgeHtml
      + '<span class="bic-expand" id="bic-expand-' + item.pk + '">▼</span>'
      + '</div>'
      + '<div class="bic-body" id="bic-body-' + item.pk + '">'
      + '<div class="bic-mode-row mb-1">'
      + '<label>参数化模式 <span class="text-[10px] text-slate-400 font-normal">(可多选)</span></label>'
      + '</div>'
      + '<div class="bic-toggles" id="bic-toggles-' + item.pk + '">' + toggleHtml + '</div>'
      + '<div id="bic-fields-' + item.pk + '">' + formulaFields + '</div>'
      + '<div class="bic-params" id="bic-params-' + item.pk + '">'
      + (paramPills ? '<span class="text-[10px] text-slate-400 mr-0.5" style="align-self:center">参数:</span>' + paramPills : '')
      + (fnPills ? '<span class="text-[10px] text-slate-400 mr-0.5" style="align-self:center">函数:</span>' + fnPills : '')
      + '</div>'
      + '<div class="bic-actions">'
      + '<button class="btn btn-primary" onclick="saveBomConfigInline(' + item.pk + ')">💾 保存</button>'
      + (hasCfg ? '<button class="btn btn-secondary" onclick="resetBomConfig(' + item.pk + ", '" + subPartName.replace(/'/g,"\\'") + "')\">↩️ 重置</button>" : '')
      + '<span class="bic-status" id="' + statusId + '"></span>'
      + '</div>'
      + '</div>'
      + '</div>';
  }
  html += '</div>';
  container.innerHTML = html;
}'''
    
    content = content[:old_func_start] + new_func + content[old_func_end:]
    print("loadBomFormulaConfigs replaced")

# ==========================================================
# 2. Replace loadAllBomFormulaConfigs
# ==========================================================
old_all_start = content.find('async function loadAllBomFormulaConfigs(container) {')
old_all_end = content.find('\n// ===== PAGE 4: RULES', old_all_start)

if old_all_start < 0 or old_all_end < 0:
    print("ERROR: Could not find loadAllBomFormulaConfigs")
else:
    new_all = '''async function loadAllBomFormulaConfigs(container) {
  // Fetch all parametric BOM configs
  const pcfgRes = await apiCall('GET', 'bom-item-config/');
  if (pcfgRes.error) { container.innerHTML = '<div class="text-red-500 text-sm">加载失败</div>'; return; }
  const pcfgs = Array.isArray(pcfgRes.data) ? pcfgRes.data : (pcfgRes.data.results || []);
  if (!pcfgs.length) {
    container.innerHTML = '<div class="empty-state"><div class="icon">📋</div><p>暂无参数化BOM配置</p></div>';
    return;
  }

  // Collect bom_item IDs
  const bomItemIds = pcfgs.map(function(c) { return c.bom_item; });
  const pcfgByBomId = {};
  pcfgs.forEach(function(c) { pcfgByBomId[c.bom_item] = c; });

  // Fetch BomItems
  const bomItemRes = await fetch('/api/bom/?id__in=' + bomItemIds.join(',') + '&limit=200&sub_part_detail=True&part_detail=True', {
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()}, credentials: 'same-origin'
  });
  const bomData = await bomItemRes.json();
  const bomItems = Array.isArray(bomData) ? bomData : (bomData.results || []);

  // Build info map
  const bomMap = {};
  bomItems.forEach(function(bi) {
    var productName = bi.part_detail ? (bi.part_detail.name || bi.part_detail.full_name || '#' + bi.part) : '#' + bi.part;
    var subPartName = bi.sub_part_detail ? bi.sub_part_detail.name : '#' + bi.sub_part;
    bomMap[bi.pk] = { productName: productName, subPartName: subPartName, quantity: bi.quantity };
  });

  var activeModes = [
    {flag:'enable_qty_formula', icon:'📐', label:'数量'},
    {flag:'enable_conditional', icon:'⚡', label:'条件'},
    {flag:'enable_candidate', icon:'🎯', label:'候选'},
    {flag:'enable_variant', icon:'🧬', label:'变体'},
    {flag:'enable_specification', icon:'📝', label:'规格'},
    {flag:'enable_supplier', icon:'🏢', label:'供应'},
    {flag:'enable_structure', icon:'🔗', label:'结构'},
  ];

  var html = '<div class="text-xs text-gray-500 mb-2">共 ' + pcfgs.length + ' 个参数化配置</div><div class="space-y-1">';
  for (var ci = 0; ci < pcfgs.length; ci++) {
    var cfg = pcfgs[ci];
    var bi = bomMap[cfg.bom_item] || {};
    var productName = bi.productName || '?';
    var subPartName = bi.subPartName || '?';

    // Build badges
    var badgeHtml = '';
    activeModes.forEach(function(m) {
      if (cfg[m.flag]) badgeHtml += '<span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 ml-1">' + m.icon + ' ' + m.label + '</span>';
    });
    if (!badgeHtml) badgeHtml = '<span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-400 ml-1">标准</span>';

    // Formula summary
    var formulas = [cfg.qty_formula || '', cfg.condition_formula || ''].filter(Boolean).join(' | ');
    var formulaSummary = formulas ? '<code class="text-blue-600 text-[10px]">' + formulas + '</code>' : '<span class="text-gray-400 text-[10px]">—</span>';

    html += '<div class="bom-inline-card">'
      + '<div class="bic-header" style="cursor:default">'
      + '<span class="bic-name text-blue-700 font-semibold">' + productName + '</span>'
      + '<span class="text-[10px] text-gray-400 mx-1">→</span>'
      + '<span class="bic-name">' + subPartName + '</span>'
      + '<span class="bic-qty">×' + (bi.quantity || '-') + '</span>'
      + badgeHtml
      + '</div>'
      + '</div>';
  }
  html += '</div>';
  container.innerHTML = html;
  // Update the "全部" option badge
  var countBadge = document.getElementById('bom-count-badge');
  if (countBadge) countBadge.textContent = pcfgs.length + ' 个配置';
}'''
    
    content = content[:old_all_start] + new_all + content[old_all_end:]
    print("loadAllBomFormulaConfigs replaced")
    
    with open(path, 'w') as f:
        f.write(content)
    print("SUCCESS")
