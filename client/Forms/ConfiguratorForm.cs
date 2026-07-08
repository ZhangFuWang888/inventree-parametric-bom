using BomQueryClient.Api;
using BomQueryClient.Api.Models;
using BomQueryClient.Api.Services;

namespace BomQueryClient.Forms;

public partial class ConfiguratorForm : Form
{
    private readonly InvenTreeClient _client;
    private readonly ConfiguratorService _cfgSvc;
    private readonly Part _part;
    private List<ParamConfigEntry> _partParams = new();

    public ConfiguratorForm(InvenTreeClient client, Part part, Font? baseFont = null)
    {
        if (baseFont != null) Font = baseFont;
        InitializeComponent();
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);

        _client = client;
        _cfgSvc = new ConfiguratorService(client);
        _part = part;

        lblTitle.Text = $"⚙ {part.Name}";
        paramHeader.Text = $"📐 参数值设置 — {part.Name}";

        btnPreviewBom.Click += (_, _) => _ = PreviewBomAsync();

        _ = LoadParamsAsync();
    }

    // ── 加载参数模板 ─────────────────

    private async Task LoadParamsAsync()
    {
        SetStatus("加载参数...");
        try
        {
            _partParams = await _cfgSvc.GetPartParamsAsync(_part.Pk);
            dgvParams.Rows.Clear();
            foreach (var param in _partParams)
            {
                dgvParams.Rows.Add(
                    param.Name,
                    param.DefaultValue ?? "",
                    GetParamTypeDisplay(param.ParameterType));
            }
            SetStatus($"共 {_partParams.Count} 个参数，编辑后点击「预览 BOM」");
        }
        catch (Exception ex)
        {
            SetStatus($"加载参数失败：{ex.Message}");
        }
    }

    // ── 预览 BOM ─────────────────

    private async Task PreviewBomAsync()
    {
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
            var result = await _cfgSvc.EvaluateBomAsync(_part.Pk, paramValues);
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

    private static TreeNode BuildEvalNode(BomEvalNode node)
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

    // ── 通用 ─────────────────

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
