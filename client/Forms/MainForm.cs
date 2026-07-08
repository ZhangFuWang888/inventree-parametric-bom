using BomQueryClient.Api;
using BomQueryClient.Api.Models;
using BomQueryClient.Api.Services;
using BomQueryClient.Properties;

namespace BomQueryClient.Forms;

public partial class MainForm : Form
{
    private readonly InvenTreeClient _client;
    private readonly PartService _parts;
    private readonly BomService _bom;
    private readonly CategoryService _categories;

    private Part? _selectedPart;
    private int? _selectedCategoryId;

    public MainForm(string serverUrl, string token, Font? baseFont = null)
    {
        if (baseFont != null) Font = baseFont;

        InitializeComponent();
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);

        _client = new InvenTreeClient(serverUrl);
        _client.SetToken(token);
        _parts = new PartService(_client);
        _bom = new BomService(_client);
        _categories = new CategoryService(_client);

        // 绑定事件
        tvCategories.AfterSelect += TvCategories_AfterSelect;
        lvParts.SelectedIndexChanged += LvParts_SelectedIndexChanged;
        txtSearch.KeyDown += (_, e) => { if (e.KeyCode == Keys.Enter) DoSearch(); };
        btnSearch.Click += (_, _) => DoSearch();
        btnRefresh.Click += (_, _) => _ = RefreshAll();
        btnLogout.Click += (_, _) => DoLogout();
        btnExport.Click += BtnExport_Click;
        tvBom.NodeMouseDoubleClick += TvBom_NodeDoubleClick;
        tvBom.BeforeExpand += (_, e) =>
        {
            if (e.Node.Nodes.Count > 0 && e.Node.Nodes[0].Text == "加载中...")
                _ = LazyLoadBomChildren(e.Node);
        };
        lvWhereUsed.DoubleClick += LvWhereUsed_DoubleClick;
        cbFilter.SelectedIndexChanged += (_, _) => _ = RefreshPartsList();

        cbFilter.SelectedIndex = 0;

        // 加载数据
        _ = LoadCategories();
    }

    // ======================== 分类树 ========================

    private async Task LoadCategories()
    {
        tvCategories.Nodes.Clear();
        SetStatus("加载物料分类...");

        try
        {
            var allCats = await _categories.GetAllAsync();
            var roots = CategoryService.BuildTree(allCats);

            tvCategories.BeginUpdate();
            foreach (var node in roots)
                tvCategories.Nodes.Add(node);
            tvCategories.EndUpdate();

            // 默认选中"全部物料"
            if (tvCategories.Nodes.Count > 0)
                tvCategories.SelectedNode = tvCategories.Nodes[0];

            SetStatus($"已加载 {allCats.Count} 个分类");
        }
        catch (Exception ex)
        {
            SetStatus($"加载分类失败：{ex.Message}");
        }
    }

    private async void TvCategories_AfterSelect(object? sender, TreeViewEventArgs e)
    {
        _selectedCategoryId = e.Node?.Tag as int?;
        var catName = e.Node?.Text ?? "全部物料";
        partsHeader.Text = $"📦 物料列表 — {catName}";
        await RefreshPartsList();
    }

    // ======================== 物料列表 ========================

    private async Task RefreshPartsList()
    {
        lvParts.Items.Clear();
        _selectedPart = null;
        ClearDetail();

        var filter = cbFilter.SelectedItem?.ToString();
        var keyword = txtSearch.Text.Trim();

        SetStatus($"加载物料...");

        try
        {
            List<Part> results;

            if (!string.IsNullOrEmpty(keyword))
            {
                // 搜索模式：按关键词+分类+类型
                results = await _parts.GetPartsByCategoryAsync(
                    _selectedCategoryId, filter, keyword);
            }
            else
            {
                results = await _parts.GetPartsByCategoryAsync(
                    _selectedCategoryId, filter);
            }

            lvParts.BeginUpdate();
            foreach (var p in results.OrderBy(x => x.Name))
            {
                var typeText = GetPartTypeText(p);
                var icon = typeText switch
                {
                    "产品" => "🏭",
                    "部装" => "🔧",
                    _ => "⚙"
                };

                var item = new ListViewItem(p.IPN ?? "----");
                item.SubItems.Add(p.Name);
                item.SubItems.Add(typeText);
                item.SubItems.Add((p.TotalInStock ?? 0).ToString("N0"));
                item.SubItems.Add(p.Description ?? "");
                item.Tag = p;
                lvParts.Items.Add(item);
            }
            lvParts.EndUpdate();

            SetStatus($"共 {results.Count} 个物料");
        }
        catch (Exception ex)
        {
            SetStatus($"加载物料失败：{ex.Message}");
        }
    }

    private static string GetPartTypeText(Part p)
    {
        if (p.IsTemplate) return "产品";
        if (p.Assembly) return "部装";
        return "零件";
    }

    // ======================== 选中物料 → 加载详情+BOM ========================

    private async void LvParts_SelectedIndexChanged(object? sender, EventArgs e)
    {
        if (lvParts.SelectedItems.Count == 0) return;
        if (lvParts.SelectedItems[0].Tag is Part part)
        {
            _selectedPart = part;
            ShowPartDetail(part);
            await LoadBomTree(part.Pk);
            await LoadWhereUsed(part.Pk);
        }
    }

    private void ShowPartDetail(Part part)
    {
        lblPartName.Text = part.Name;
        lblPartIpn.Text = part.IPN ?? "-";
        lblPartType.Text = GetPartTypeText(part);
        lblPartStock.Text = (part.TotalInStock ?? 0).ToString("N0");
    }

    private void ClearDetail()
    {
        lblPartName.Text = "-";
        lblPartIpn.Text = "-";
        lblPartType.Text = "-";
        lblPartStock.Text = "-";
        tvBom.Nodes.Clear();
        lvWhereUsed.Items.Clear();
    }

    // ======================== BOM 树 ========================

    private async Task LoadBomTree(int partId)
    {
        tvBom.Nodes.Clear();
        SetStatus("展开 BOM 树...");

        try
        {
            var tree = await _bom.GetFullBomTreeAsync(partId);
            tvBom.BeginUpdate();
            tvBom.Nodes.Add(BuildBomNode(tree));
            tvBom.Nodes[0].Expand();
            tvBom.EndUpdate();
            SetStatus("BOM 展开完成");
        }
        catch (Exception ex)
        {
            SetStatus($"BOM 加载失败：{ex.Message}");
        }
    }

    private TreeNode BuildBomNode(BomTreeNode node)
    {
        var prefix = node.Quantity != 1 ? $" ×{node.Quantity}" : "";
        var text = $"{node.Part.Name}{prefix}   ({node.Part.IPN ?? "----"})";

        var tn = new TreeNode(text)
        {
            Tag = node.Part,
            ToolTipText = $"数量: {node.Quantity}\n" +
                          $"编码: {node.Part.IPN ?? "-"}\n" +
                          $"描述: {node.Part.Description ?? "-"}\n" +
                          $"类型: {GetPartTypeText(node.Part)}"
        };

        foreach (var child in node.Children)
            tn.Nodes.Add(BuildBomNode(child));

        return tn;
    }

    private async Task LazyLoadBomChildren(TreeNode parent)
    {
        if (parent.Tag is Part part && part.Assembly)
        {
            parent.Nodes.Clear();
            try
            {
                var tree = await _bom.GetFullBomTreeAsync(part.Pk);
                foreach (var child in tree.Children)
                    parent.Nodes.Add(BuildBomNode(child));
                parent.Expand();
            }
            catch { /* ignore */ }
        }
    }

    private async void TvBom_NodeDoubleClick(object? sender, TreeNodeMouseClickEventArgs e)
    {
        if (e.Node?.Tag is Part part && part.Assembly)
            await LazyLoadBomChildren(e.Node);
    }

    // ======================== Where Used ========================

    private async Task LoadWhereUsed(int partId)
    {
        lvWhereUsed.Items.Clear();
        try
        {
            var items = await _bom.WhereUsedAsync(partId);
            foreach (var item in items)
            {
                var lv = new ListViewItem(item.SubPartDetail?.IPN ?? "");
                lv.SubItems.Add(item.SubPartDetail?.Name ?? "");
                lv.SubItems.Add(item.SubPartDetail?.Description ?? "");
                lv.SubItems.Add(item.Quantity.ToString("0.##"));
                lv.Tag = item;
                lvWhereUsed.Items.Add(lv);
            }
        }
        catch { /* where-used may not work for all */ }
    }

    private async void LvWhereUsed_DoubleClick(object? sender, EventArgs e)
    {
        if (lvWhereUsed.SelectedItems.Count > 0 &&
            lvWhereUsed.SelectedItems[0].Tag is BomItem item &&
            item.SubPart.HasValue)
        {
            await LoadBomTree(item.SubPart.Value);
            rightTabs.SelectedIndex = 0;
        }
    }

    // ======================== 搜索 ========================

    private async void DoSearch()
    {
        var keyword = txtSearch.Text.Trim();
        if (string.IsNullOrEmpty(keyword))
        {
            await RefreshPartsList();
            return;
        }

        SetStatus($"搜索: {keyword}...");
        lvParts.Items.Clear();
        _selectedPart = null;
        ClearDetail();
        partsHeader.Text = $"🔍 搜索结果 — \"{keyword}\"";

        try
        {
            var filter = cbFilter.SelectedItem?.ToString();
            List<Part> results;

            if (!string.IsNullOrEmpty(filter) && filter != "全部")
            {
                results = filter switch
                {
                    "产品" => await _parts.GetProductsAsync(keyword),
                    "部装" => await _parts.GetSubassembliesAsync(keyword),
                    "零件" => (await _parts.GetPartsAsync(keyword)).ToList(),
                    _ => await _parts.SearchPartsAsync(keyword)
                };
            }
            else
            {
                results = await _parts.SearchPartsAsync(keyword);
            }

            lvParts.BeginUpdate();
            foreach (var p in results.OrderBy(x => x.Name))
            {
                var typeText = GetPartTypeText(p);
                var item = new ListViewItem(p.IPN ?? "----");
                item.SubItems.Add(p.Name);
                item.SubItems.Add(typeText);
                item.SubItems.Add((p.TotalInStock ?? 0).ToString("N0"));
                item.SubItems.Add(p.Description ?? "");
                item.Tag = p;
                lvParts.Items.Add(item);
            }
            lvParts.EndUpdate();

            SetStatus($"搜索完成 — {results.Count} 条结果");
        }
        catch (Exception ex)
        {
            SetStatus($"搜索失败：{ex.Message}");
        }
    }

    // ======================== 刷新 ========================

    private async Task RefreshAll()
    {
        await LoadCategories();
    }

    // ======================== 导出 ========================

    private async void BtnExport_Click(object? sender, EventArgs e)
    {
        if (_selectedPart == null) return;

        var sfd = new SaveFileDialog
        {
            Filter = "Excel 文件|*.xlsx",
            FileName = $"BOM_{_selectedPart.IPN ?? _selectedPart.Name}.xlsx"
        };
        if (sfd.ShowDialog() != DialogResult.OK) return;

        SetStatus("导出中...");
        try
        {
            var tree = await _bom.GetFullBomTreeAsync(_selectedPart.Pk);
            var flat = FlattenBom(tree);
            ExportToExcel(sfd.FileName, flat);

            SetStatus($"已导出: {sfd.FileName}");
            MessageBox.Show($"BOM 已导出到:\n{sfd.FileName}", "导出成功",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex)
        {
            SetStatus($"导出失败：{ex.Message}");
        }
    }

    private static List<(string Level, string Ipn, string Name, string Desc, decimal Qty, string Type)> FlattenBom(BomTreeNode node, int depth = 0)
    {
        var list = new List<(string, string, string, string, decimal, string)>();
        var indent = new string(' ', depth * 2);
        list.Add((indent, node.Part.IPN ?? "", node.Part.Name,
            node.Part.Description ?? "", node.Quantity,
            GetPartTypeText(node.Part)));

        foreach (var child in node.Children)
            list.AddRange(FlattenBom(child, depth + 1));

        return list;
    }

    private static void ExportToExcel(string path, List<(string Level, string Ipn, string Name, string Desc, decimal Qty, string Type)> rows)
    {
        using var workbook = new ClosedXML.Excel.XLWorkbook();
        var ws = workbook.Worksheets.Add("BOM");
        ws.Cell(1, 1).Value = "层级";
        ws.Cell(1, 2).Value = "物料编码";
        ws.Cell(1, 3).Value = "名称";
        ws.Cell(1, 4).Value = "描述";
        ws.Cell(1, 5).Value = "数量";
        ws.Cell(1, 6).Value = "类型";

        for (int i = 0; i < rows.Count; i++)
        {
            var r = rows[i];
            int row = i + 2;
            ws.Cell(row, 1).Value = r.Level;
            ws.Cell(row, 2).Value = r.Ipn;
            ws.Cell(row, 3).Value = r.Name;
            ws.Cell(row, 4).Value = r.Desc;
            ws.Cell(row, 5).Value = r.Qty;
            ws.Cell(row, 6).Value = r.Type;
        }

        ws.Columns().AdjustToContents();
        workbook.SaveAs(path);
    }

    // ======================== 通用 ========================

    private void DoLogout()
    {
        Settings.Default.ApiToken = "";
        Settings.Default.Save();

        using var login = new LoginForm(Font);
        if (login.ShowDialog() == DialogResult.OK)
        {
            _client.SetToken(login.Token!);
            _ = RefreshAll();
        }
        else
            Close();
    }

    private void SetStatus(string text)
    {
        if (lblStatus != null)
            lblStatus.Text = text;
    }
}
