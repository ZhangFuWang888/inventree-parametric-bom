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
    private BomEvalNode? _bomRoot;

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

        // Cell formatting for value column
        dgvParams.CellFormatting += (s, e) =>
        {
            if (e.ColumnIndex == 1 && e.Value is bool b)
                e.Value = b ? "是" : "否";
        };

        // 合计行单元格样式
        dgvBomPreview.CellFormatting += (s, e) =>
        {
            if (e.RowIndex >= 0 && dgvBomPreview.Rows[e.RowIndex].Tag is string tag && tag == "total")
            {
                e.CellStyle.Font = new Font(dgvBomPreview.Font, FontStyle.Bold);
                e.CellStyle.BackColor = Color.FromArgb(243, 244, 246);
            }
            // 排除行灰色
            if (e.RowIndex >= 0 && dgvBomPreview.Rows[e.RowIndex].Tag is string tag2 && tag2 == "excluded")
            {
                e.CellStyle.ForeColor = Color.FromArgb(156, 163, 175);
            }
        };

        // 双击单元格可看 tooltip（有额外信息时）
        dgvBomPreview.CellMouseEnter += (s, e) =>
        {
            if (e.RowIndex >= 0 && e.ColumnIndex >= 0)
            {
                var row = dgvBomPreview.Rows[e.RowIndex];
                if (row.Tag is string tag && tag != "total" && tag != "excluded" && tag != "normal" && tag.Length > 0)
                    dgvBomPreview.Rows[e.RowIndex].Cells[e.ColumnIndex].ToolTipText = tag;
            }
        };

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

    // ── BOM 预览（表格）────────────

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
            _bomRoot = result.BomTree;

            dgvBomPreview.Rows.Clear();

            if (result.BomTree != null)
            {
                var flatRows = new List<BomFlatRow>();
                FlattenTree(result.BomTree, 0, flatRows);

                foreach (var fr in flatRows)
                {
                    var nameDisplay = new string(' ', fr.Depth * 3) + fr.Name;
                    var tag = string.IsNullOrEmpty(fr.Tooltip) ? (fr.Excluded ? "excluded" : "normal") : fr.Tooltip;
                    var rowIdx = dgvBomPreview.Rows.Add(
                        fr.Badge,
                        nameDisplay,
                        string.IsNullOrEmpty(fr.Ipn) ? "—" : fr.Ipn,
                        fr.Quantity != 1 ? $"×{fr.Quantity}" : "",
                        fr.UnitPrice.HasValue ? fr.UnitPrice.Value : (object)"",
                        fr.TotalPrice.HasValue ? fr.TotalPrice.Value : (object)"");
                    dgvBomPreview.Rows[rowIdx].Tag = tag;

                    // 排除行灰色
                    if (fr.Excluded)
                    {
                        dgvBomPreview.Rows[rowIdx].DefaultCellStyle.ForeColor = Color.FromArgb(156, 163, 175);
                    }
                }

                // 合计行
                decimal totalCost = flatRows.Sum(r => r.TotalPrice ?? 0);
                var totalIdx = dgvBomPreview.Rows.Add("", "合计", "", "", "", totalCost);
                dgvBomPreview.Rows[totalIdx].Tag = "total";
                foreach (DataGridViewCell c in dgvBomPreview.Rows[totalIdx].Cells)
                {
                    c.Style.Font = new Font(dgvBomPreview.Font, FontStyle.Bold);
                    c.Style.BackColor = Color.FromArgb(243, 244, 246);
                }
                // 合计列水平对齐
                dgvBomPreview.Rows[totalIdx].Cells[5].Style.Alignment = DataGridViewContentAlignment.MiddleRight;
                dgvBomPreview.Rows[totalIdx].Cells[5].Style.Format = "¥0.00";

                dgvBomPreview.ClearSelection();
            }

            SetStatus($"BOM 评估完成 — {flatRows?.Count ?? 0} 行");
        }
        catch (Exception ex)
        {
            SetStatus($"评估失败：{ex.Message}");
        }
    }

    private static void FlattenTree(BomEvalNode node, int depth, List<BomFlatRow> rows)
    {
        // 类型标签
        var badge = node.Excluded ? "已排除" : "参数化";
        if (!node.Excluded && node.UnitPrice == null && node.TotalPrice == null)
            badge = "静态";
        if (node.Excluded && !string.IsNullOrEmpty(node.ExcludeReason))
            badge = "已排除";

        // 构建 tooltip
        var tooltipParts = new List<string>();
        if (node.CalculatedQuantity != node.Quantity && node.Quantity > 0)
            tooltipParts.Add($"BOM数量: {node.Quantity} → 公式计算: {node.CalculatedQuantity}");
        if (node.Excluded && !string.IsNullOrEmpty(node.ExcludeReason))
            tooltipParts.Add(node.ExcludeReason);

        var displayName = node.CalculatedName ?? node.PartName ?? "未知";
        var displayIpn = node.CalculatedIpn ?? node.PartIpn ?? "";

        var qty = node.CalculatedQuantity > 0 ? node.CalculatedQuantity : node.Quantity;

        rows.Add(new BomFlatRow
        {
            Depth = depth,
            Badge = badge,
            Name = displayName,
            Ipn = displayIpn,
            Quantity = qty,
            UnitPrice = node.UnitPrice,
            TotalPrice = node.TotalPrice,
            Excluded = node.Excluded,
            Tooltip = string.Join(" | ", tooltipParts),
        });

        foreach (var child in node.Children)
            FlattenTree(child, depth + 1, rows);
    }

    // ── 导出 BOM 到 Excel ─────────────────

    private void ExportBomAsync()
    {
        if (_bomRoot == null || dgvBomPreview.Rows.Count == 0)
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
            var flatRows = new List<BomFlatRow>();
            FlattenTree(_bomRoot, 0, flatRows);

            using var workbook = new ClosedXML.Excel.XLWorkbook();
            var ws = workbook.Worksheets.Add("BOM");
            ws.Cell(1, 1).Value = "类型";
            ws.Cell(1, 2).Value = "物料名称";
            ws.Cell(1, 3).Value = "产品型号";
            ws.Cell(1, 4).Value = "数量";
            ws.Cell(1, 5).Value = "单价";
            ws.Cell(1, 6).Value = "总价";
            ws.Cell(1, 7).Value = "说明";

            for (int i = 0; i < flatRows.Count; i++)
            {
                var r = flatRows[i];
                int row = i + 2;
                ws.Cell(row, 1).Value = r.Badge;
                ws.Cell(row, 2).Value = new string(' ', r.Depth * 2) + r.Name;
                ws.Cell(row, 3).Value = r.Ipn;
                ws.Cell(row, 4).Value = (double)r.Quantity;
                if (r.UnitPrice.HasValue)
                    ws.Cell(row, 5).Value = (double)r.UnitPrice.Value;
                if (r.TotalPrice.HasValue)
                    ws.Cell(row, 6).Value = (double)r.TotalPrice.Value;
                ws.Cell(row, 7).Value = r.Tooltip;
            }

            // 合计行
            int totalRow = flatRows.Count + 2;
            ws.Cell(totalRow, 2).Value = "合计";
            ws.Cell(totalRow, 5).FormulaA1 = $"=SUM(E2:E{totalRow - 1})";
            ws.Cell(totalRow, 6).FormulaA1 = $"=SUM(F2:F{totalRow - 1})";
            ws.Row(totalRow).Style.Font.Bold = true;

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

/// <summary>BOM 扁平行（用于表格显示+导出）</summary>
public class BomFlatRow
{
    public int Depth { get; set; }
    public string Badge { get; set; } = "";
    public string Name { get; set; } = "";
    public string Ipn { get; set; } = "";
    public decimal Quantity { get; set; }
    public decimal? UnitPrice { get; set; }
    public decimal? TotalPrice { get; set; }
    public bool Excluded { get; set; }
    public string Tooltip { get; set; } = "";
}
