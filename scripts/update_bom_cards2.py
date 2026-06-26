#!/usr/bin/env python3
"""Replace loadAllBomFormulaConfigs with card version, and hide modal."""
import re

path = '/root/inventree-source/InvenTree-master/src/backend/parametric_bom/templates/parametric_bom/configurator.html'
with open(path, 'r') as f:
    content = f.read()

# 1. Replace loadAllBomFormulaConfigs
old_all_start = content.find('async function loadAllBomFormulaConfigs(container) {')
old_all_end = content.find('\n// ===== PAGE 4: RULES', old_all_start)
if old_all_start < 0 or old_all_end < 0:
    print("ERROR: Could not find loadAllBomFormulaConfigs")
else:
    new_all_func = '''async function loadAllBomFormulaConfigs(container) {
  // Fetch all parametric BOM configs
  const pcfgRes = await apiCall('GET', 'bom-item-config/');
  if (pcfgRes.error) { container.innerHTML = '<div class="text-red-500 text-sm">加载失败</div>'; return; }
  const pcfgs = Array.isArray(pcfgRes.data) ? pcfgRes.data : (pcfgRes.data.results || []);
  if (!pcfgs.length) {
    container.innerHTML = '<div class="empty-state"><div class="icon">📋</div><p>暂无参数化BOM配置</p></div>';
    return;
  }

  // Collect bom_item IDs
  const bomItemIds = pcfgs.map(c => c.bom_item);
  const pcfgByBomId = {};
  pcfgs.forEach(c => { pcfgByBomId[c.bom_item] = c; });

  // Fetch BomItems
  const bomItemRes = await fetch('/api/bom/?id__in=' + bomItemIds.join(',') + '&limit=200&sub_part_detail=True&part_detail=True', {
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()}, credentials: 'same-origin'
  });
  const bomData = await bomItemRes.json();
  const bomItems = Array.isArray(bomData) ? bomData : (bomData.results || []);

  // Build bom_item_id info map
  const bomMap = {};
  bomItems.forEach(function(bi) {
    var productName = bi.part_detail?.name || bi.part_detail?.full_name || '#' + bi.part;
    var subPartName = bi.sub_part_detail?.name || '#' + bi.sub_part;
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
    var qty = bi.quantity || '-';

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
      + '<span class="bic-qty">×' + qty + '</span>'
      + badgeHtml
      + '</div>'
      + '</div>';
  }
  html += '</div>';
  container.innerHTML = html;
}'''
    
    content = content[:old_all_start] + new_all_func + content[old_all_end:]
    print("loadAllBomFormulaConfigs replaced")

    # 2. Hide the modal formula editor by commenting out its overlay
    modal_start = content.find('<!-- ===== MODAL: Formula Editor ===== -->')
    modal_end = content.find('\n    <!-- ===== PAGE 4: 规则', modal_start)
    if modal_start < 0 or modal_end < 0:
        print("ERROR: Could not find modal")
    else:
        # Replace the modal with a comment
        modal_replacement = '<!-- MODAL FORMULA EDITOR REMOVED (replaced by inline card editing) -->'
        content = content[:modal_start] + modal_replacement + content[modal_end:]
        print("Modal hidden")

    # 3. Update page help text
    help_start = content.find('核心配置页。为每个BOM项选择<strong>模式</strong>')
    if help_start >= 0:
        help_end = content.find('。</span>', help_start) + 5
        new_help = '点击卡片展开编辑。选择<strong>模式</strong>：📐数量公式 | ⚡条件包含 | 🎯候选零件 | 🧬变体生成 | 📝规格描述 | 🏢供应商选择。多模式可组合使用。</span>'
        content = content[:help_start] + new_help + content[help_end:]
        print("Help text updated")
    
    # 4. Remove the old openFormulaEditor when it's no longer called from cards
    # (but keep it for backward compat - other code may call it)
    
    with open(path, 'w') as f:
        f.write(content)
    print("SUCCESS: All changes applied")
