using BomQueryClient.Api;
using BomQueryClient.Api.Models;
using BomQueryClient.Api.Services;

namespace BomQueryClient.Forms;

public partial class ConfiguratorForm : Form
{
    private readonly InvenTreeClient _client;
    private readonly ConfiguratorService _cfgSvc;
    private readonly PartService _partSvc;

    private List<Part> _parametricParts = new();
    private List<ProductConfiguration> _configs = new();
    private List<ParamConfigEntry> _partParams = new();

    private int? _selectedConfigId;
    private int? _preselectPartId;

    public ConfiguratorForm(InvenTreeClient client, Font? baseFont = null)
        : this(client, null, baseFont) { }

    public ConfiguratorForm(InvenTreeClient client, Part? preselectedPart,
        Font? baseFont = null)
    {
        if (baseFont != null) Font = baseFont;
        InitializeComponent();
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);

        _client = client;
        _cfgSvc = new ConfiguratorService(client);
        _partSvc = new PartService(client);
        _preselectPartId = preselectedPart?.Pk;

        // 事件绑定
        cboProduct.SelectedIndexChanged += (_, _) => _ = OnProductChanged();
        lvConfigs.SelectedIndexChanged += (_, _) => OnConfigSelected();
        btnNewConfig.Click += (_, _) => _ = CreateConfigAsync();
        btnSave.Click += (_, _) => _ = SaveParamsAsync();
        btnPreviewBom.Click += (_, _) => _ = PreviewBomAsync();
        btnRelease.Click += (_, _) => _ = ReleaseConfigAsync();

        // 加载参数化产品
        _ = LoadParametricParts();
    }

    // ── 加载参数化产品 ─────────────────

    private async Task LoadParametricParts()
    {
        SetStatus("加载参数化产品...");
        try
        {
            var parametricSvc = new ParametricService(_client);
            var ids = await parametricSvc.GetParametricPartIdsAsync();

            // 获取每个参数化产品的详情用于下拉
            var allParts = new List<Part>();
            foreach (var id in ids)
            {
                try
                {
                    var part = await _partSvc.GetPartAsync(id);
                    allParts.Add(part);
                }
                catch { /* skip inaccessible */ }
            }

            _parametricParts = allParts.OrderBy(p => p.Name).ToList();

            cboProduct.BeginUpdate();
            cboProduct.Items.Clear();
            foreach (var p in _parametricParts)
                cboProduct.Items.Add($"{p.Name} ({p.IPN ?? "无编码"})");
            cboProduct.EndUpdate();

            if (_parametricParts.Count > 0)
            {
                // 如果有预选产品，自动选中
                if (_preselectPartId.HasValue)
                {
                    var idx = _parametricParts.FindIndex(p => p.Pk == _preselectPartId.Value);
                    if (idx >= 0)
                        cboProduct.SelectedIndex = idx;
                    else
                        cboProduct.SelectedIndex = 0;
                }
                else
                {
                    cboProduct.SelectedIndex = 0;
                }
            }

            SetStatus($"共 {_parametricParts.Count} 个参数化产品");
        }
        catch (Exception ex)
        {
            SetStatus($"加载失败：{ex.Message}");
        }
    }

    // ── 产品切换 ─────────────────

    private async Task OnProductChanged()
    {
        var part = GetSelectedPart();
        if (part == null) return;

        tvBomPreview.Nodes.Clear();
        dgvParams.Rows.Clear();
        lvConfigs.Items.Clear();
        _selectedConfigId = null;

        // 加载参数模板
        try
        {
            _partParams = await _cfgSvc.GetPartParamsAsync(part.Pk);
            dgvParams.Rows.Clear();
            foreach (var param in _partParams)
            {
                dgvParams.Rows.Add(
                    param.Name,
                    param.DefaultValue ?? "",
                    GetParamTypeDisplay(param.ParameterType));
            }
            paramHeader.Text = $"📐 参数值设置 — {part.Name}";
        }
        catch (Exception ex)
        {
            SetStatus($"加载参数失败：{ex.Message}");
        }

        // 加载已有配置
        await LoadConfigs(part.Pk);
        txtTitle.Text = $"{part.Name} 配置方案";
    }

    // ── 配置列表 ─────────────────

    private async Task LoadConfigs(int partId)
    {
        try
        {
            _configs = await _cfgSvc.GetConfigsAsync(partId);
            lvConfigs.BeginUpdate();
            lvConfigs.Items.Clear();
            foreach (var cfg in _configs)
            {
                var item = new ListViewItem(cfg.Title ?? "未命名");
                item.SubItems.Add(cfg.StatusDisplay);
                item.SubItems.Add(cfg.CreatedAt ?? "");
                item.Tag = cfg;
                lvConfigs.Items.Add(item);
            }
            lvConfigs.EndUpdate();
            configHeader.Text = $"📋 配置列表（{_configs.Count}）";
        }
        catch (Exception ex)
        {
            SetStatus($"加载配置列表失败：{ex.Message}");
        }
    }

    // ── 选择配置 ─────────────────

    private void OnConfigSelected()
    {
        if (lvConfigs.SelectedItems.Count == 0) return;
        if (lvConfigs.SelectedItems[0].Tag is ProductConfiguration cfg)
        {
            _selectedConfigId = cfg.Id;
            txtTitle.Text = cfg.Title ?? "";

            // 如果有参数快照，填充到表格
            if (cfg.ParamsSnapshot != null && cfg.ParamsSnapshot.Count > 0)
            {
                foreach (DataGridViewRow row in dgvParams.Rows)
                {
                    var paramName = row.Cells[0].Value?.ToString();
                    if (paramName != null && cfg.ParamsSnapshot.TryGetValue(paramName, out var val))
                        row.Cells[1].Value = val;
                }
            }

            SetStatus($"选中配置: {cfg.Title} (状态: {cfg.StatusDisplay})");
        }
    }

    // ── 新建配置 ─────────────────

    private async Task CreateConfigAsync()
    {
        var part = GetSelectedPart();
        if (part == null) { SetStatus("请先选择产品"); return; }

        var title = txtTitle.Text.Trim();
        if (string.IsNullOrEmpty(title)) { SetStatus("请输入配置名称"); return; }

        SetStatus("创建配置...");
        try
        {
            var cfg = await _cfgSvc.CreateConfigAsync(part.Pk, title);
            await LoadConfigs(part.Pk);

            // 选中新创建的配置
            foreach (ListViewItem item in lvConfigs.Items)
            {
                if (item.Tag is ProductConfiguration c && c.Id == cfg.Id)
                {
                    item.Selected = true;
                    break;
                }
            }

            SetStatus($"配置「{title}」创建成功");
        }
        catch (Exception ex)
        {
            SetStatus($"创建失败：{ex.Message}");
        }
    }

    // ── 保存参数 ─────────────────

    private async Task SaveParamsAsync()
    {
        if (_selectedConfigId == null) { SetStatus("请先选择或创建一个配置"); return; }

        // 收集参数值
        var paramValues = new Dictionary<string, string>();
        foreach (DataGridViewRow row in dgvParams.Rows)
        {
            var name = row.Cells[0].Value?.ToString();
            var val = row.Cells[1].Value?.ToString() ?? "";
            if (!string.IsNullOrEmpty(name))
                paramValues[name] = val;
        }

        SetStatus("保存参数...");
        try
        {
            // 调用 evaluate 接口保存参数并预览结果
            var part = GetSelectedPart();
            if (part == null) return;

            var result = await _cfgSvc.EvaluateBomAsync(part.Pk, paramValues);
            // 刷新配置列表以获取更新后的 params_snapshot
            await LoadConfigs(part.Pk);
            SetStatus("参数已保存，BOM 已评估");
        }
        catch (Exception ex)
        {
            SetStatus($"保存失败：{ex.Message}");
        }
    }

    // ── 预览 BOM ─────────────────

    private async Task PreviewBomAsync()
    {
        var part = GetSelectedPart();
        if (part == null) { SetStatus("请先选择产品"); return; }

        var paramValues = new Dictionary<string, string>();
        foreach (DataGridViewRow row in dgvParams.Rows)
        {
            var name = row.Cells[0].Value?.ToString();
            var val = row.Cells[1].Value?.ToString() ?? "";
            if (!string.IsNullOrEmpty(name))
                paramValues[name] = val;
        }

        SetStatus("评估 BOM...");
        try
        {
            var result = await _cfgSvc.EvaluateBomAsync(part.Pk, paramValues);
            tvBomPreview.BeginUpdate();
            tvBomPreview.Nodes.Clear();
            if (result.BomTree != null)
            {
                var root = BuildEvalNode(result.BomTree);
                tvBomPreview.Nodes.Add(root);
                root.Expand();
            }
            tvBomPreview.EndUpdate();
            SetStatus("BOM 评估完成");
        }
        catch (Exception ex)
        {
            SetStatus($"评估失败：{ex.Message}");
        }
    }

    private TreeNode BuildEvalNode(BomEvalNode node)
    {
        var qty = node.CalculatedQuantity > 0 ? node.CalculatedQuantity : node.Quantity;
        var prefix = qty != 1 ? $" ×{qty}" : "";
        var excl = node.Excluded ? " [🚫 已排除]" : "";

        var text = $"{node.PartName}{prefix}{excl}";
        var tn = new TreeNode(text)
        {
            ToolTipText = node.Excluded
                ? $"已排除: {node.ExcludeReason}"
                : $"数量: {qty}"
        };

        foreach (var child in node.Children)
            tn.Nodes.Add(BuildEvalNode(child));

        return tn;
    }

    // ── 发布配置 ─────────────────

    private async Task ReleaseConfigAsync()
    {
        if (_selectedConfigId == null) { SetStatus("请先选择配置"); return; }

        SetStatus("发布中...");
        try
        {
            var ok = await _cfgSvc.TransitionConfigAsync(_selectedConfigId.Value, "completed");
            if (ok)
            {
                SetStatus("配置已发布为「已完成」");
                var part = GetSelectedPart();
                if (part != null) await LoadConfigs(part.Pk);
            }
            else
            {
                SetStatus("发布失败，请检查状态是否允许转换");
            }
        }
        catch (Exception ex)
        {
            SetStatus($"发布失败：{ex.Message}");
        }
    }

    // ── 通用方法 ─────────────────

    private Part? GetSelectedPart()
    {
        if (cboProduct.SelectedIndex < 0 || cboProduct.SelectedIndex >= _parametricParts.Count)
            return null;
        return _parametricParts[cboProduct.SelectedIndex];
    }

    private static string GetParamTypeDisplay(string? type)
    {
        return type switch
        {
            "number" => "🔢 数值",
            "option" => "📋 选项",
            "multi_option" => "📋 多选",
            "boolean" => "✅ 布尔",
            "text" => "📝 文本",
            "file_ref" => "📎 文件",
            "part_ref" => "🔩 零件",
            _ => type ?? "未知"
        };
    }

    private void SetStatus(string text)
    {
        if (lblStatus != null)
            lblStatus.Text = text;
    }
}
