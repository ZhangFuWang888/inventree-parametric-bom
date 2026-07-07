using BomQueryClient.Api;
using BomQueryClient.Api.Models;
using BomQueryClient.Api.Services;
using BomQueryClient.Properties;

namespace BomQueryClient.Forms;

public partial class MainForm : Form
{
    static readonly Color TitleBg = Color.FromArgb(30, 41, 59);     // slate-800
    static readonly Color SideBg = Color.FromArgb(249, 250, 251);    // gray-50
    static readonly Color AccentBlue = Color.FromArgb(37, 99, 235);
    static readonly Color AccentGreen = Color.FromArgb(22, 163, 74);
    static readonly Color AccentOrange = Color.FromArgb(245, 158, 11);
    static readonly Color HeaderBg = Color.FromArgb(243, 244, 246);

    private readonly InvenTreeClient _client;
    private readonly PartService _parts;
    private readonly BomService _bom;

    // Controls
    private readonly Panel _leftPanel;
    private readonly Panel _rightPanel;
    private readonly TreeView _tvProducts;
    private readonly TreeView _tvBom;
    private readonly TextBox _txtSearch;
    private readonly ComboBox _cbFilter;
    private readonly TableLayoutPanel _rightLayout;
    private readonly TabControl _rightTabs;
    private readonly ListView _lvWhereUsed;
    private readonly StatusStrip _status;
    private readonly ToolStripStatusLabel _lblStatus;
    private readonly Panel _detailPanel;
    private readonly Label _lblPartName;
    private readonly Label _lblPartIpn;
    private readonly Label _lblPartDesc;
    private readonly Label _lblPartType;
    private readonly Label _lblPartStock;
    private readonly Button _btnExport;

    private Part? _selectedPart;

    public MainForm(string serverUrl, string token, Font? baseFont = null)
    {
        if (baseFont != null) Font = baseFont;

        Text = "设备BOM查询系统";
        ClientSize = new Size(1280, 800);
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(960, 600);
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        BackColor = Color.White;

        _client = new InvenTreeClient(serverUrl);
        _client.SetToken(token);
        _parts = new PartService(_client);
        _bom = new BomService(_client);

        // ==================== 顶部栏 ====================
        var topBar = new Panel
        {
            Height = 52, Dock = DockStyle.Top,
            BackColor = TitleBg
        };

        var lblLogo = new Label
        {
            Text = "🔧  设备BOM查询系统",
            Font = new Font(Font.FontFamily, 14, FontStyle.Bold),
            ForeColor = Color.White,
            Location = new Point(16, 12), AutoSize = true
        };

        // 搜索框
        _txtSearch = new TextBox
        {
            Location = new Point(280, 12), Size = new Size(220, 28),
            BorderStyle = BorderStyle.FixedSingle,
            ForeColor = Color.FromArgb(55, 65, 81),
            Font = new Font(Font.FontFamily, 9.5f)
        };
        _txtSearch.KeyDown += (_, e) => { if (e.KeyCode == Keys.Enter) DoSearch(); };

        var btnSearch = new Button
        {
            Text = "🔍 搜索",
            Location = new Point(508, 11), Size = new Size(70, 28),
            BackColor = AccentBlue, ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat, Cursor = Cursors.Hand
        };
        btnSearch.Click += (_, _) => DoSearch();

        _cbFilter = new ComboBox
        {
            Location = new Point(588, 11), Size = new Size(100, 24),
            DropDownStyle = ComboBoxStyle.DropDownList, FlatStyle = FlatStyle.Flat,
            Items = { "全部", "产品", "部装", "零件" }, SelectedIndex = 0
        };

        var btnRefresh = new Button
        {
            Text = "🔄 刷新",
            Location = new Point(700, 11), Size = new Size(70, 28),
            FlatStyle = FlatStyle.Flat, Cursor = Cursors.Hand,
            BackColor = Color.Transparent, ForeColor = Color.White,
            FlatAppearance = { BorderColor = Color.White }
        };
        btnRefresh.Click += (_, _) => _ = LoadProducts();

        var btnLogout = new Button
        {
            Text = "退出",
            Location = new Point(780, 11), Size = new Size(60, 28),
            FlatStyle = FlatStyle.Flat, Cursor = Cursors.Hand,
            BackColor = Color.FromArgb(220, 38, 38), ForeColor = Color.White
        };
        btnLogout.Click += (_, _) => DoLogout();

        topBar.Controls.AddRange([lblLogo, _txtSearch, btnSearch, _cbFilter,
            btnRefresh, btnLogout]);

        // ==================== 主区域 ====================
        var mainSplit = new SplitContainer
        {
            Dock = DockStyle.Fill,
            SplitterDistance = 360,
            BackColor = BorderLight,
            Padding = new Padding(0, 4, 0, 0)
        };

        // -------- 左侧：产品列表 --------
        _leftPanel = CreateSidePanel("📦 产品列表");
        _tvProducts = new TreeView
        {
            Dock = DockStyle.Fill,
            ShowNodeToolTips = true,
            HideSelection = false,
            Font = new Font(Font.FontFamily, 9.5f),
            BorderStyle = BorderStyle.None,
            FullRowSelect = true,
            BackColor = Color.White
        };
        _tvProducts.AfterSelect += TvProducts_AfterSelect;
        _leftPanel.Controls.Add(_tvProducts);

        // -------- 右侧：详情+Tab --------
        _rightPanel = new Panel { Dock = DockStyle.Fill };

        // 详情面板
        _detailPanel = new Panel
        {
            Height = 90, Dock = DockStyle.Top,
            BackColor = Color.FromArgb(248, 250, 252),
            Padding = new Padding(12)
        };
        _detailPanel.Paint += (_, e) =>
        {
            using var pen = new Pen(BorderLight);
            e.Graphics.DrawLine(pen, 0, _detailPanel.Height - 1,
                _detailPanel.Width, _detailPanel.Height - 1);
        };

        var tblDetail = new TableLayoutPanel
        {
            ColumnCount = 4, RowCount = 2,
            Dock = DockStyle.Fill,
            Padding = new Padding(4)
        };
        tblDetail.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 60));
        tblDetail.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 40));
        tblDetail.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 60));
        tblDetail.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 40));

        _lblPartName = MakeDetailLabel("名称：", true);
        _lblPartIpn = MakeDetailLabel("物料编码：", false);
        _lblPartDesc = MakeDetailLabel("描述：", false);
        _lblPartType = MakeDetailLabel("类型：", false);
        _lblPartStock = MakeDetailLabel("库存：", false);
        _btnExport = new Button
        {
            Text = "📥 导出Excel",
            FlatStyle = FlatStyle.Flat, Cursor = Cursors.Hand,
            BackColor = AccentGreen, ForeColor = Color.White,
            Size = new Size(100, 26), TextAlign = ContentAlignment.MiddleCenter
        };
        _btnExport.Click += BtnExport_Click;

        // Row 0
        tblDetail.Controls.Add(MakeDetailCaption("名称"), 0, 0);
        tblDetail.Controls.Add(_lblPartName, 1, 0);
        tblDetail.Controls.Add(MakeDetailCaption("物料编码"), 2, 0);
        tblDetail.Controls.Add(_lblPartIpn, 3, 0);
        // Row 1
        tblDetail.Controls.Add(MakeDetailCaption("类型"), 0, 1);
        tblDetail.Controls.Add(_lblPartType, 1, 1);
        tblDetail.Controls.Add(MakeDetailCaption("库存"), 2, 1);
        tblDetail.Controls.Add(_lblPartStock, 3, 1);

        var detailRightPanel = new Panel { Dock = DockStyle.Right, Width = 120 };
        _btnExport.Location = new Point(10, 28);
        detailRightPanel.Controls.Add(_btnExport);

        _detailPanel.Controls.Add(detailRightPanel);
        _detailPanel.Controls.Add(tblDetail);

        // Tab
        _rightTabs = new TabControl
        {
            Dock = DockStyle.Fill, Padding = new Point(8, 4),
            Font = new Font(Font.FontFamily, 9.5f)
        };

        // Tab 1: BOM树
        var bomTab = new TabPage("📋 BOM结构");
        _tvBom = new TreeView
        {
            Dock = DockStyle.Fill,
            ShowNodeToolTips = true,
            HideSelection = false,
            Font = new Font("Consolas", 9.5f),
            BorderStyle = BorderStyle.None,
            FullRowSelect = true
        };
        _tvBom.NodeMouseDoubleClick += TvBom_NodeDoubleClick;
        _tvBom.BeforeExpand += (_, e) =>
        {
            if (e.Node.Nodes.Count > 0 && e.Node.Nodes[0].Text == "⏳ 加载中...")
                _ = LazyLoadBomChildren(e.Node);
        };
        _tvBom.DrawMode = TreeViewDrawMode.OwnerDrawText;
        _tvBom.DrawNode += (_, e) =>
        {
            e.DrawDefault = true;
        };
        bomTab.Controls.Add(_tvBom);

        // Tab 2: Where Used
        var usedTab = new TabPage("🔍 反向查询 (Where Used)");
        _lvWhereUsed = new ListView
        {
            Dock = DockStyle.Fill,
            View = View.Details,
            FullRowSelect = true,
            BorderStyle = BorderStyle.None,
            Font = new Font(Font.FontFamily, 9.5f),
            GridLines = true
        };
        _lvWhereUsed.Columns.Add("物料编码", 100);
        _lvWhereUsed.Columns.Add("名称", 160);
        _lvWhereUsed.Columns.Add("描述", 250);
        _lvWhereUsed.Columns.Add("数量", 60, HorizontalAlignment.Right);
        _lvWhereUsed.DoubleClick += LvWhereUsed_DoubleClick;
        usedTab.Controls.Add(_lvWhereUsed);

        _rightTabs.TabPages.AddRange([bomTab, usedTab]);

        _rightPanel.Controls.AddRange([_rightTabs, _detailPanel]);
        mainSplit.Panel1.Controls.Add(_leftPanel);
        mainSplit.Panel2.Controls.Add(_rightPanel);

        // ==================== 状态栏 ====================
        _status = new StatusStrip
        {
            BackColor = Color.FromArgb(248, 250, 252),
            SizingGrip = false
        };
        _lblStatus = new ToolStripStatusLabel("就绪 ✅");
        _status.Items.Add(_lblStatus);

        Controls.AddRange([mainSplit, topBar, _status]);

        // 加载数据
        _ = LoadProducts();
    }

    // ======================== 数据加载 ========================

    async Task LoadProducts()
    {
        _tvProducts.Nodes.Clear();
        SetStatus("⏳ 加载产品列表...");

        try
        {
            var products = await _parts.GetProductsAsync();

            _tvProducts.BeginUpdate();
            foreach (var p in products.OrderBy(x => x.Name))
            {
                var icon = p.IsTemplate ? "📦" : "🔧";
                var node = new TreeNode($"{icon}  {p.Name}")
                {
                    Tag = p,
                    ToolTipText = !string.IsNullOrEmpty(p.Description)
                        ? $"{p.Description}\nIPN: {p.IPN ?? "-"}"
                        : $"IPN: {p.IPN ?? "-"}"
                };
                _tvProducts.Nodes.Add(node);
            }
            _tvProducts.EndUpdate();
            SetStatus($"✅ 共 {products.Count} 个产品");
        }
        catch (Exception ex)
        {
            SetStatus($"❌ 加载失败：{ex.Message}");
            MessageBox.Show($"无法加载产品列表：{ex.Message}", "错误",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    async void TvProducts_AfterSelect(object? sender, TreeViewEventArgs e)
    {
        if (e.Node?.Tag is Part part)
        {
            _selectedPart = part;
            ShowPartDetail(part);
            _ = LoadBomTree(part.Pk);
            _ = LoadWhereUsed(part.Pk);
        }
    }

    void ShowPartDetail(Part part)
    {
        _lblPartName.Text = part.Name;
        _lblPartIpn.Text = part.IPN ?? "-";
        _lblPartDesc.Text = part.Description ?? "-";
        _lblPartType.Text = part.IsTemplate ? "📦 产品" : part.Assembly ? "🔧 部装" : "⚙ 零件";
        _lblPartStock.Text = (part.TotalInStock ?? 0).ToString("N0");
    }

    async Task LoadBomTree(int partId)
    {
        _tvBom.Nodes.Clear();
        SetStatus("⏳ 展开BOM树...");

        try
        {
            var tree = await _bom.GetFullBomTreeAsync(partId);
            _tvBom.BeginUpdate();
            _tvBom.Nodes.Add(BuildBomNode(tree));
            _tvBom.Nodes[0].Expand();
            _tvBom.EndUpdate();
            SetStatus("✅ BOM 展开完成");
        }
        catch (Exception ex)
        {
            SetStatus($"❌ BOM加载失败：{ex.Message}");
        }
    }

    TreeNode BuildBomNode(BomTreeNode node)
    {
        var prefix = node.Quantity != 1 ? $" ×{node.Quantity}" : "";
        var icon = node.Part.Assembly ? (node.Part.IsTemplate ? "📦" : "🔧") : "⚙";
        var text = $"{icon}  {node.Part.Name}{prefix}   ({node.Part.IPN ?? "----"})";

        var tn = new TreeNode(text)
        {
            Tag = node.Part,
            ToolTipText = $"数量: {node.Quantity}\n" +
                          $"编码: {node.Part.IPN ?? "-"}\n" +
                          $"描述: {node.Part.Description ?? "-"}\n" +
                          $"类型: {(node.Part.Assembly ? "组装件" : "零件")}"
        };

        foreach (var child in node.Children)
            tn.Nodes.Add(BuildBomNode(child));

        return tn;
    }

    async Task LazyLoadBomChildren(TreeNode parent)
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

    async Task LoadWhereUsed(int partId)
    {
        _lvWhereUsed.Items.Clear();

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
                _lvWhereUsed.Items.Add(lv);
            }
        }
        catch { /* where-used may not work for all */ }
    }

    async void TvBom_NodeDoubleClick(object? sender, TreeNodeMouseClickEventArgs e)
    {
        if (e.Node?.Tag is Part part && part.Assembly)
            await LazyLoadBomChildren(e.Node);
    }

    async void LvWhereUsed_DoubleClick(object? sender, EventArgs e)
    {
        if (_lvWhereUsed.SelectedItems.Count > 0 &&
            _lvWhereUsed.SelectedItems[0].Tag is BomItem item &&
            item.SubPart.HasValue)
        {
            await LoadBomTree(item.SubPart.Value);
            _rightTabs.SelectedIndex = 0;
        }
    }

    async void DoSearch()
    {
        var keyword = _txtSearch.Text.Trim();
        if (string.IsNullOrEmpty(keyword)) return;

        _tvProducts.Nodes.Clear();
        SetStatus($"⏳ 搜索: {keyword}...");

        try
        {
            List<Part> results;
            switch (_cbFilter.SelectedIndex)
            {
                case 1: results = await _parts.GetProductsAsync(keyword); break;
                case 2: results = await _parts.GetSubassembliesAsync(keyword); break;
                case 3: results = (await _parts.GetPartsAsync())
                        .Where(p => !p.Assembly).ToList(); break;
                default: results = await _parts.SearchPartsAsync(keyword); break;
            }

            _tvProducts.BeginUpdate();
            foreach (var p in results.OrderBy(x => x.Name))
            {
                var icon = p.IsTemplate ? "📦" : p.Assembly ? "🔧" : "⚙";
                var node = new TreeNode($"{icon}  {p.Name}")
                {
                    Tag = p,
                    ToolTipText = $"[{p.IPN ?? "----"}] {p.Description ?? ""}"
                };
                _tvProducts.Nodes.Add(node);
            }
            _tvProducts.EndUpdate();
            SetStatus($"✅ 搜索完成 — {results.Count} 条结果");
        }
        catch (Exception ex)
        {
            SetStatus($"❌ 搜索失败：{ex.Message}");
        }
    }

    async void BtnExport_Click(object? sender, EventArgs e)
    {
        if (_selectedPart == null) return;

        var sfd = new SaveFileDialog
        {
            Filter = "Excel 文件|*.xlsx",
            FileName = $"BOM_{_selectedPart.IPN ?? _selectedPart.Name}.xlsx"
        };
        if (sfd.ShowDialog() != DialogResult.OK) return;

        SetStatus("⏳ 导出中...");
        try
        {
            // 导出BOM到Excel
            var tree = await _bom.GetFullBomTreeAsync(_selectedPart.Pk);
            var flat = FlattenBom(tree);
            ExportToExcel(sfd.FileName, flat);

            SetStatus($"✅ 已导出: {sfd.FileName}");
            MessageBox.Show($"BOM 已导出到:\n{sfd.FileName}", "导出成功",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex)
        {
            SetStatus($"❌ 导出失败：{ex.Message}");
        }
    }

    static List<(string Level, string Ipn, string Name, string Desc, decimal Qty, string Type)> FlattenBom(BomTreeNode node, int depth = 0)
    {
        var list = new List<(string, string, string, string, decimal, string)>();
        var indent = new string('　', depth);
        list.Add((indent, node.Part.IPN ?? "", node.Part.Name,
            node.Part.Description ?? "", node.Quantity,
            node.Part.Assembly ? (node.Part.IsTemplate ? "产品" : "部装") : "零件"));

        foreach (var child in node.Children)
            list.AddRange(FlattenBom(child, depth + 1));

        return list;
    }

    static void ExportToExcel(string path, List<(string Level, string Ipn, string Name, string Desc, decimal Qty, string Type)> rows)
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

    void DoLogout()
    {
        Settings.Default.ApiToken = "";
        Settings.Default.Save();

        using var login = new LoginForm(Font);
        if (login.ShowDialog() == DialogResult.OK)
        {
            _client.SetToken(login.Token!);
            _ = LoadProducts();
        }
        else
            Close();
    }

    void SetStatus(string text)
    {
        if (_lblStatus != null)
            _lblStatus.Text = text;
    }

    static Label MakeDetailCaption(string text) => new()
    {
        Text = text,
        Font = new Font("Microsoft YaHei", 8.5f, FontStyle.Bold),
        ForeColor = Color.FromArgb(156, 163, 175),
        TextAlign = ContentAlignment.MiddleLeft,
        Dock = DockStyle.Fill
    };

    static Label MakeDetailLabel(string text, bool bold) => new()
    {
        Text = text,
        Font = new Font("Microsoft YaHei", bold ? 10 : 9f, bold ? FontStyle.Bold : FontStyle.Regular),
        ForeColor = Color.FromArgb(30, 41, 59),
        TextAlign = ContentAlignment.MiddleLeft,
        Dock = DockStyle.Fill,
        AutoEllipsis = true
    };

    static Panel CreateSidePanel(string title)
    {
        var panel = new Panel { Dock = DockStyle.Fill, BackColor = SideBg };

        var header = new Label
        {
            Text = title,
            Dock = DockStyle.Top,
            Height = 32,
            TextAlign = ContentAlignment.MiddleLeft,
            Padding = new Padding(12, 0, 0, 0),
            BackColor = HeaderBg,
            Font = new Font("Microsoft YaHei", 10, FontStyle.Bold),
            ForeColor = Color.FromArgb(55, 65, 81)
        };

        panel.Controls.Add(header);
        return panel;
    }

    // 默认边框色
    static readonly Color BorderLight = Color.FromArgb(229, 231, 235);
}
