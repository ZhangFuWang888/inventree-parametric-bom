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
        btnExportBom.Click += (_, _) => ExportBomAsync();

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
                var rowIdx = dgvParams.Rows.Add(
                    param.Name,
                    param.DefaultValue ?? "",
                    GetParamTypeDisplay(param.ParameterType),
                    param.UiHint ?? "");

                // 按参数类型设置单元格控件
                var valueCell = dgvParams.Rows[rowIdx].Cells[1];

                if (param.ParameterType == "option" && param.Options != null && param.Options.Count > 0)
                {
                    var comboCell = new DataGridViewComboBoxCell();
                    foreach (var opt in param.Options)
                        comboCell.Items.Add(opt);
                    comboCell.Value = param.DefaultValue ?? param.Options[0];
                    dgvParams.Rows[rowIdx].Cells[1] = comboCell;
                }
                else if (param.ParameterType == "boolean")
                {
                    var checkCell = new DataGridViewCheckBoxCell();
                    checkCell.Value = param.DefaultValue?.Trim().ToLower() == "true"
                        || param.DefaultValue == "1";
                    checkCell.Style.NullValue = false;
                    dgvParams.Rows[rowIdx].Cells[1] = checkCell;
                }
                else if (param.ParameterType == "multi_option" && param.Options != null && param.Options.Count > 0)
                {
                    var comboCell = new DataGridViewComboBoxCell();
                    foreach (var opt in param.Options)
                        comboCell.Items.Add(opt);
                    comboCell.Value = param.DefaultValue?.Split(',').FirstOrDefault()?.Trim() ?? param.Options[0];
                    dgvParams.Rows[rowIdx].Cells[1] = comboCell;
                }
                // number / text / long_text 保持默认文本框
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
            var cell = row.Cells[1];

            string? val = null;
            if (cell is DataGridViewCheckBoxCell checkCell)
            {
                val = checkCell.Value is bool b && b ? "true" : "false";
            }
            else if (cell is DataGridViewComboBoxCell)
            {
                val = cell.Value?.ToString() ?? "";
            }
            else
            {
                val = cell.Value?.ToString() ?? "";
            }

            if (!string.IsNullOrEmpty(name))
                paramValues[name] = val ?? "";
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
        var formulaMark = node.CalculatedQuantity > 0 && node.CalculatedQuantity != node.Quantity ? " ⚡" : "";
        var prefix = qty != 1 ? $" ×{qty}{formulaMark}" : formulaMark;
        var excl = node.Excluded ? " [🚫 已排除]" : "";

        // 使用公式计算值(calculated_name/calculated_ipn)，回退到静态值
        var displayName = node.CalculatedName ?? node.PartName ?? "未知";
        var displayIpn = node.CalculatedIpn ?? node.PartIpn ?? "";
        var ipnPart = string.IsNullOrEmpty(displayIpn) ? "" : $" ({displayIpn})";

        var text = $"{displayName}{ipnPart}{prefix}{excl}";
        var tn = new TreeNode(text)
        {
            ToolTipText = node.Excluded
                ? $"已排除: {node.ExcludeReason}"
                : node.CalculatedQuantity != node.Quantity
                    ? $"BOM数量: {node.Quantity}\n公式计算: {node.CalculatedQuantity}"
                    : $"数量: {qty}"
        };

        foreach (var child in node.Children)
            tn.Nodes.Add(BuildEvalNode(child));

        return tn;
    }

    // ── 导出 BOM 到 Excel ─────────────────

    private void ExportBomAsync()
    {
        if (tvBomPreview.Nodes.Count == 0)
        {
            SetStatus("没有可导出的 BOM 数据，请先预览 BOM");
            return;
        }

        var sfd = new SaveFileDialog
        {
            Filter = "Excel 文件|*.xlsx",
            FileName = $"BOM_{_part.IPN ?? _part.Name}.xlsx"
        };
        if (sfd.ShowDialog() != DialogResult.OK) return;

        SetStatus("导出中...");
        try
        {
            var rows = new List<(string Level, string Name, string Ipn, string Desc, decimal Qty, string Excluded)>();
            foreach (TreeNode node in tvBomPreview.Nodes)
                FlattenTree(node, 0, rows);

            using var workbook = new ClosedXML.Excel.XLWorkbook();
            var ws = workbook.Worksheets.Add("BOM");
            ws.Cell(1, 1).Value = "层级";
            ws.Cell(1, 2).Value = "名称";
            ws.Cell(1, 3).Value = "产品型号";
            ws.Cell(1, 4).Value = "描述";
            ws.Cell(1, 5).Value = "数量";
            ws.Cell(1, 6).Value = "状态";

            for (int i = 0; i < rows.Count; i++)
            {
                var r = rows[i];
                int row = i + 2;
                ws.Cell(row, 1).Value = r.Level;
                ws.Cell(row, 2).Value = r.Name;
                ws.Cell(row, 3).Value = r.Ipn;
                ws.Cell(row, 4).Value = r.Desc;
                ws.Cell(row, 5).Value = (double)r.Qty;
                ws.Cell(row, 6).Value = r.Excluded;
            }

            ws.Columns().AdjustToContents();
            workbook.SaveAs(sfd.FileName);

            SetStatus($"已导出: {sfd.FileName}");
            MessageBox.Show($"BOM 已导出到:\n{sfd.FileName}", "导出成功",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex)
        {
            SetStatus($"导出失败：{ex.Message}");
        }
    }

    private static void FlattenTree(TreeNode node, int depth,
        List<(string Level, string Name, string Ipn, string Desc, decimal Qty, string Excluded)> rows)
    {
        var indent = new string(' ', depth * 2);

        // 从节点文本提取名称、型号和数量
        var text = node.Text;
        var excluded = text.Contains("🚫") ? "已排除" : "正常";
        // 尝试提取数量：格式 "名称 (型号) ×数量" 或 "名称 (型号)"
        decimal qty = 1;
        var xIdx = text.LastIndexOf(" ×");
        var nameAndIpn = text;
        if (xIdx > 0)
        {
            nameAndIpn = text[..xIdx];
            var qtyStr = text[(xIdx + 2)..];
            decimal.TryParse(qtyStr, out qty);
        }
        // 分离名称和型号
        var ipn = "";
        var name = nameAndIpn;
        if (nameAndIpn.EndsWith(")"))
        {
            var parenIdx = nameAndIpn.LastIndexOf(" (");
            if (parenIdx > 0)
            {
                name = nameAndIpn[..parenIdx];
                ipn = nameAndIpn[(parenIdx + 2)..^1];
            }
        }

        rows.Add((indent, name, ipn, node.ToolTipText ?? "", qty, excluded));

        foreach (TreeNode child in node.Nodes)
            FlattenTree(child, depth + 1, rows);
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
