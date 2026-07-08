namespace BomQueryClient.Forms;

partial class MainForm
{
    private System.ComponentModel.IContainer components = null;

    protected override void Dispose(bool disposing)
    {
        if (disposing && (components != null))
        {
            components.Dispose();
        }
        base.Dispose(disposing);
    }

    #region Windows 窗体设计器生成的代码

    private void InitializeComponent()
    {
        this.components = new System.ComponentModel.Container();
        this.topBar = new System.Windows.Forms.Panel();
        this.btnLogout = new System.Windows.Forms.Button();
        this.btnRefresh = new System.Windows.Forms.Button();
        this.cbFilter = new System.Windows.Forms.ComboBox();
        this.btnSearch = new System.Windows.Forms.Button();
        this.txtSearch = new System.Windows.Forms.TextBox();
        this.lblLogo = new System.Windows.Forms.Label();
        this.mainSplit = new System.Windows.Forms.SplitContainer();
        this.leftPanel = new System.Windows.Forms.Panel();
        this.tvCategories = new System.Windows.Forms.TreeView();
        this.leftHeader = new System.Windows.Forms.Label();
        this.rightPanel = new System.Windows.Forms.Panel();
        this.rightSplit = new System.Windows.Forms.SplitContainer();
        this.panelPartsList = new System.Windows.Forms.Panel();
        this.partsHeader = new System.Windows.Forms.Label();
        this.lvParts = new System.Windows.Forms.ListView();
        this.colPartIpn = new System.Windows.Forms.ColumnHeader();
        this.colPartName = new System.Windows.Forms.ColumnHeader();
        this.colPartType = new System.Windows.Forms.ColumnHeader();
        this.colPartStock = new System.Windows.Forms.ColumnHeader();
        this.colPartDesc = new System.Windows.Forms.ColumnHeader();
        this.panelBomDetail = new System.Windows.Forms.Panel();
        this.rightTabs = new System.Windows.Forms.TabControl();
        this.tabBom = new System.Windows.Forms.TabPage();
        this.tvBom = new System.Windows.Forms.TreeView();
        this.tabUsed = new System.Windows.Forms.TabPage();
        this.lvWhereUsed = new System.Windows.Forms.ListView();
        this.colWIpn = new System.Windows.Forms.ColumnHeader();
        this.colWName = new System.Windows.Forms.ColumnHeader();
        this.colWDesc = new System.Windows.Forms.ColumnHeader();
        this.colWQty = new System.Windows.Forms.ColumnHeader();
        this.detailPanel = new System.Windows.Forms.Panel();
        this.detailRight = new System.Windows.Forms.Panel();
        this.btnExport = new System.Windows.Forms.Button();
        this.tblDetail = new System.Windows.Forms.TableLayoutPanel();
        this.lblCapName = new System.Windows.Forms.Label();
        this.lblPartName = new System.Windows.Forms.Label();
        this.lblCapIpn = new System.Windows.Forms.Label();
        this.lblPartIpn = new System.Windows.Forms.Label();
        this.lblCapType = new System.Windows.Forms.Label();
        this.lblPartType = new System.Windows.Forms.Label();
        this.lblCapStock = new System.Windows.Forms.Label();
        this.lblPartStock = new System.Windows.Forms.Label();
        this.statusStrip = new System.Windows.Forms.StatusStrip();
        this.lblStatus = new System.Windows.Forms.ToolStripStatusLabel();
        this.topBar.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)(this.mainSplit)).BeginInit();
        this.mainSplit.Panel1.SuspendLayout();
        this.mainSplit.Panel2.SuspendLayout();
        this.mainSplit.SuspendLayout();
        this.leftPanel.SuspendLayout();
        this.rightPanel.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)(this.rightSplit)).BeginInit();
        this.rightSplit.Panel1.SuspendLayout();
        this.rightSplit.Panel2.SuspendLayout();
        this.rightSplit.SuspendLayout();
        this.panelPartsList.SuspendLayout();
        this.panelBomDetail.SuspendLayout();
        this.rightTabs.SuspendLayout();
        this.tabBom.SuspendLayout();
        this.tabUsed.SuspendLayout();
        this.detailPanel.SuspendLayout();
        this.detailRight.SuspendLayout();
        this.tblDetail.SuspendLayout();
        this.statusStrip.SuspendLayout();
        this.SuspendLayout();
        //
        // topBar
        //
        this.topBar.BackColor = Color.FromArgb(30, 58, 138);
        this.topBar.Controls.Add(this.btnLogout);
        this.topBar.Controls.Add(this.btnRefresh);
        this.topBar.Controls.Add(this.cbFilter);
        this.topBar.Controls.Add(this.btnSearch);
        this.topBar.Controls.Add(this.txtSearch);
        this.topBar.Controls.Add(this.lblLogo);
        this.topBar.Dock = System.Windows.Forms.DockStyle.Top;
        this.topBar.Location = new System.Drawing.Point(0, 0);
        this.topBar.Name = "topBar";
        this.topBar.Size = new System.Drawing.Size(1280, 40);
        this.topBar.TabIndex = 0;
        //
        // lblLogo
        //
        this.lblLogo.AutoSize = true;
        this.lblLogo.Font = new System.Drawing.Font("Microsoft YaHei UI", 11F, System.Drawing.FontStyle.Bold);
        this.lblLogo.ForeColor = Color.White;
        this.lblLogo.Location = new System.Drawing.Point(12, 9);
        this.lblLogo.Name = "lblLogo";
        this.lblLogo.Size = new System.Drawing.Size(174, 24);
        this.lblLogo.TabIndex = 0;
        this.lblLogo.Text = "📋 设备 BOM 查询系统";
        //
        // txtSearch
        //
        this.txtSearch.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left)
        | System.Windows.Forms.AnchorStyles.Right)));
        this.txtSearch.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.txtSearch.Location = new System.Drawing.Point(300, 8);
        this.txtSearch.Name = "txtSearch";
        this.txtSearch.PlaceholderText = "搜索物料编码 / 名称...";
        this.txtSearch.Size = new System.Drawing.Size(420, 25);
        this.txtSearch.TabIndex = 1;
        //
        // btnSearch
        //
        this.btnSearch.BackColor = Color.FromArgb(59, 130, 246);
        this.btnSearch.FlatAppearance.BorderSize = 0;
        this.btnSearch.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
        this.btnSearch.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.btnSearch.ForeColor = Color.White;
        this.btnSearch.Location = new System.Drawing.Point(728, 7);
        this.btnSearch.Name = "btnSearch";
        this.btnSearch.Size = new System.Drawing.Size(65, 26);
        this.btnSearch.TabIndex = 2;
        this.btnSearch.Text = "搜索";
        this.btnSearch.UseVisualStyleBackColor = false;
        //
        // cbFilter
        //
        this.cbFilter.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
        this.cbFilter.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
        this.cbFilter.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.cbFilter.Items.AddRange(new object[] { "全部", "产品", "部装", "零件" });
        this.cbFilter.Location = new System.Drawing.Point(800, 8);
        this.cbFilter.Name = "cbFilter";
        this.cbFilter.Size = new System.Drawing.Size(100, 26);
        this.cbFilter.TabIndex = 3;
        //
        // btnRefresh
        //
        this.btnRefresh.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
        this.btnRefresh.BackColor = Color.FromArgb(55, 65, 81);
        this.btnRefresh.FlatAppearance.BorderSize = 0;
        this.btnRefresh.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
        this.btnRefresh.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.btnRefresh.ForeColor = Color.White;
        this.btnRefresh.Location = new System.Drawing.Point(1040, 7);
        this.btnRefresh.Name = "btnRefresh";
        this.btnRefresh.Size = new System.Drawing.Size(65, 26);
        this.btnRefresh.TabIndex = 4;
        this.btnRefresh.Text = "刷新";
        this.btnRefresh.UseVisualStyleBackColor = false;
        //
        // btnLogout
        //
        this.btnLogout.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
        this.btnLogout.BackColor = Color.FromArgb(220, 38, 38);
        this.btnLogout.FlatAppearance.BorderSize = 0;
        this.btnLogout.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
        this.btnLogout.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.btnLogout.ForeColor = Color.White;
        this.btnLogout.Location = new System.Drawing.Point(1112, 7);
        this.btnLogout.Name = "btnLogout";
        this.btnLogout.Size = new System.Drawing.Size(75, 26);
        this.btnLogout.TabIndex = 5;
        this.btnLogout.Text = "退出登录";
        this.btnLogout.UseVisualStyleBackColor = false;
        //
        // mainSplit
        //
        this.mainSplit.Dock = System.Windows.Forms.DockStyle.Fill;
        this.mainSplit.FixedPanel = System.Windows.Forms.FixedPanel.Panel1;
        this.mainSplit.Location = new System.Drawing.Point(0, 40);
        this.mainSplit.Name = "mainSplit";
        //
        // mainSplit.Panel1
        //
        this.mainSplit.Panel1.Controls.Add(this.leftPanel);
        this.mainSplit.Panel1MinSize = 200;
        //
        // mainSplit.Panel2
        //
        this.mainSplit.Panel2.Controls.Add(this.rightPanel);
        this.mainSplit.Size = new System.Drawing.Size(1280, 734);
        this.mainSplit.SplitterDistance = 280;
        this.mainSplit.SplitterWidth = 5;
        this.mainSplit.TabIndex = 1;
        //
        // leftPanel
        //
        this.leftPanel.BackColor = Color.FromArgb(249, 250, 251);
        this.leftPanel.Controls.Add(this.tvCategories);
        this.leftPanel.Controls.Add(this.leftHeader);
        this.leftPanel.Dock = System.Windows.Forms.DockStyle.Fill;
        this.leftPanel.Location = new System.Drawing.Point(0, 0);
        this.leftPanel.Name = "leftPanel";
        this.leftPanel.Size = new System.Drawing.Size(280, 734);
        this.leftPanel.TabIndex = 0;
        //
        // leftHeader
        //
        this.leftHeader.BackColor = Color.FromArgb(243, 244, 246);
        this.leftHeader.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
        this.leftHeader.Dock = System.Windows.Forms.DockStyle.Top;
        this.leftHeader.Font = new System.Drawing.Font("Microsoft YaHei UI", 9.5F, System.Drawing.FontStyle.Bold);
        this.leftHeader.ForeColor = Color.FromArgb(30, 58, 138);
        this.leftHeader.Location = new System.Drawing.Point(0, 0);
        this.leftHeader.Name = "leftHeader";
        this.leftHeader.Padding = new System.Windows.Forms.Padding(10, 0, 0, 0);
        this.leftHeader.Size = new System.Drawing.Size(280, 32);
        this.leftHeader.TabIndex = 0;
        this.leftHeader.Text = "📂 物料分类";
        this.leftHeader.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // tvCategories
        //
        this.tvCategories.BorderStyle = System.Windows.Forms.BorderStyle.None;
        this.tvCategories.Dock = System.Windows.Forms.DockStyle.Fill;
        this.tvCategories.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.tvCategories.FullRowSelect = true;
        this.tvCategories.HideSelection = false;
        this.tvCategories.Indent = 18;
        this.tvCategories.ItemHeight = 24;
        this.tvCategories.Location = new System.Drawing.Point(0, 32);
        this.tvCategories.Name = "tvCategories";
        this.tvCategories.PathSeparator = " / ";
        this.tvCategories.ShowLines = true;
        this.tvCategories.ShowNodeToolTips = true;
        this.tvCategories.Size = new System.Drawing.Size(280, 702);
        this.tvCategories.TabIndex = 1;
        //
        // rightPanel
        //
        this.rightPanel.Controls.Add(this.rightSplit);
        this.rightPanel.Dock = System.Windows.Forms.DockStyle.Fill;
        this.rightPanel.Location = new System.Drawing.Point(0, 0);
        this.rightPanel.Name = "rightPanel";
        this.rightPanel.Size = new System.Drawing.Size(995, 734);
        this.rightPanel.TabIndex = 0;
        //
        // rightSplit
        //
        this.rightSplit.Dock = System.Windows.Forms.DockStyle.Fill;
        this.rightSplit.FixedPanel = System.Windows.Forms.FixedPanel.Panel2;
        this.rightSplit.Location = new System.Drawing.Point(0, 0);
        this.rightSplit.Name = "rightSplit";
        this.rightSplit.Orientation = System.Windows.Forms.Orientation.Horizontal;
        //
        // rightSplit.Panel1
        //
        this.rightSplit.Panel1.Controls.Add(this.panelPartsList);
        //
        // rightSplit.Panel2
        //
        this.rightSplit.Panel2.Controls.Add(this.panelBomDetail);
        this.rightSplit.Size = new System.Drawing.Size(995, 734);
        this.rightSplit.SplitterDistance = 320;
        this.rightSplit.SplitterWidth = 5;
        this.rightSplit.TabIndex = 0;
        //
        // panelPartsList
        //
        this.panelPartsList.Controls.Add(this.lvParts);
        this.panelPartsList.Controls.Add(this.partsHeader);
        this.panelPartsList.Dock = System.Windows.Forms.DockStyle.Fill;
        this.panelPartsList.Location = new System.Drawing.Point(0, 0);
        this.panelPartsList.Name = "panelPartsList";
        this.panelPartsList.Size = new System.Drawing.Size(995, 320);
        this.panelPartsList.TabIndex = 0;
        //
        // partsHeader
        //
        this.partsHeader.BackColor = Color.FromArgb(243, 244, 246);
        this.partsHeader.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
        this.partsHeader.Dock = System.Windows.Forms.DockStyle.Top;
        this.partsHeader.Font = new System.Drawing.Font("Microsoft YaHei UI", 9.5F, System.Drawing.FontStyle.Bold);
        this.partsHeader.ForeColor = Color.FromArgb(30, 58, 138);
        this.partsHeader.Location = new System.Drawing.Point(0, 0);
        this.partsHeader.Name = "partsHeader";
        this.partsHeader.Padding = new System.Windows.Forms.Padding(10, 0, 0, 0);
        this.partsHeader.Size = new System.Drawing.Size(995, 32);
        this.partsHeader.TabIndex = 0;
        this.partsHeader.Text = "📦 物料列表 — 请选择分类";
        this.partsHeader.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lvParts
        //
        this.lvParts.BorderStyle = System.Windows.Forms.BorderStyle.None;
        this.lvParts.Columns.AddRange(new System.Windows.Forms.ColumnHeader[] {
            this.colPartIpn,
            this.colPartName,
            this.colPartType,
            this.colPartStock,
            this.colPartDesc});
        this.lvParts.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lvParts.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.lvParts.FullRowSelect = true;
        this.lvParts.GridLines = true;
        this.lvParts.HideSelection = false;
        this.lvParts.Location = new System.Drawing.Point(0, 32);
        this.lvParts.MultiSelect = false;
        this.lvParts.Name = "lvParts";
        this.lvParts.Size = new System.Drawing.Size(995, 288);
        this.lvParts.TabIndex = 1;
        this.lvParts.UseCompatibleStateImageBehavior = false;
        this.lvParts.View = System.Windows.Forms.View.Details;
        //
        // colPartIpn
        //
        this.colPartIpn.Text = "物料编码";
        this.colPartIpn.Width = 120;
        //
        // colPartName
        //
        this.colPartName.Text = "名称";
        this.colPartName.Width = 180;
        //
        // colPartType
        //
        this.colPartType.Text = "类型";
        this.colPartType.Width = 70;
        //
        // colPartStock
        //
        this.colPartStock.Text = "库存";
        this.colPartStock.TextAlign = System.Windows.Forms.HorizontalAlignment.Right;
        this.colPartStock.Width = 80;
        //
        // colPartDesc
        //
        this.colPartDesc.Text = "描述";
        this.colPartDesc.Width = 300;
        //
        // panelBomDetail
        //
        this.panelBomDetail.Controls.Add(this.rightTabs);
        this.panelBomDetail.Controls.Add(this.detailPanel);
        this.panelBomDetail.Dock = System.Windows.Forms.DockStyle.Fill;
        this.panelBomDetail.Location = new System.Drawing.Point(0, 0);
        this.panelBomDetail.Name = "panelBomDetail";
        this.panelBomDetail.Size = new System.Drawing.Size(995, 409);
        this.panelBomDetail.TabIndex = 0;
        //
        // rightTabs
        //
        this.rightTabs.Controls.Add(this.tabBom);
        this.rightTabs.Controls.Add(this.tabUsed);
        this.rightTabs.Dock = System.Windows.Forms.DockStyle.Fill;
        this.rightTabs.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.rightTabs.Location = new System.Drawing.Point(0, 0);
        this.rightTabs.Name = "rightTabs";
        this.rightTabs.SelectedIndex = 0;
        this.rightTabs.Size = new System.Drawing.Size(995, 300);
        this.rightTabs.TabIndex = 0;
        //
        // tabBom
        //
        this.tabBom.Controls.Add(this.tvBom);
        this.tabBom.Location = new System.Drawing.Point(4, 26);
        this.tabBom.Name = "tabBom";
        this.tabBom.Padding = new System.Windows.Forms.Padding(3);
        this.tabBom.Size = new System.Drawing.Size(987, 270);
        this.tabBom.TabIndex = 0;
        this.tabBom.Text = "📐 BOM 结构";
        this.tabBom.UseVisualStyleBackColor = true;
        //
        // tvBom
        //
        this.tvBom.BorderStyle = System.Windows.Forms.BorderStyle.None;
        this.tvBom.Dock = System.Windows.Forms.DockStyle.Fill;
        this.tvBom.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.tvBom.FullRowSelect = true;
        this.tvBom.HideSelection = false;
        this.tvBom.Location = new System.Drawing.Point(3, 3);
        this.tvBom.Name = "tvBom";
        this.tvBom.ShowNodeToolTips = true;
        this.tvBom.Size = new System.Drawing.Size(981, 264);
        this.tvBom.TabIndex = 0;
        //
        // tabUsed
        //
        this.tabUsed.Controls.Add(this.lvWhereUsed);
        this.tabUsed.Location = new System.Drawing.Point(4, 26);
        this.tabUsed.Name = "tabUsed";
        this.tabUsed.Padding = new System.Windows.Forms.Padding(3);
        this.tabUsed.Size = new System.Drawing.Size(987, 270);
        this.tabUsed.TabIndex = 1;
        this.tabUsed.Text = "🔍 反向查询";
        this.tabUsed.UseVisualStyleBackColor = true;
        //
        // lvWhereUsed
        //
        this.lvWhereUsed.BorderStyle = System.Windows.Forms.BorderStyle.None;
        this.lvWhereUsed.Columns.AddRange(new System.Windows.Forms.ColumnHeader[] {
            this.colWIpn,
            this.colWName,
            this.colWDesc,
            this.colWQty});
        this.lvWhereUsed.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lvWhereUsed.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.lvWhereUsed.FullRowSelect = true;
        this.lvWhereUsed.GridLines = true;
        this.lvWhereUsed.HideSelection = false;
        this.lvWhereUsed.Location = new System.Drawing.Point(3, 3);
        this.lvWhereUsed.Name = "lvWhereUsed";
        this.lvWhereUsed.Size = new System.Drawing.Size(981, 264);
        this.lvWhereUsed.TabIndex = 0;
        this.lvWhereUsed.UseCompatibleStateImageBehavior = false;
        this.lvWhereUsed.View = System.Windows.Forms.View.Details;
        //
        // colWIpn
        //
        this.colWIpn.Text = "物料编码";
        this.colWIpn.Width = 110;
        //
        // colWName
        //
        this.colWName.Text = "名称";
        this.colWName.Width = 180;
        //
        // colWDesc
        //
        this.colWDesc.Text = "描述";
        this.colWDesc.Width = 280;
        //
        // colWQty
        //
        this.colWQty.Text = "数量";
        this.colWQty.TextAlign = System.Windows.Forms.HorizontalAlignment.Right;
        this.colWQty.Width = 70;
        //
        // detailPanel
        //
        this.detailPanel.BackColor = Color.FromArgb(249, 250, 251);
        this.detailPanel.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
        this.detailPanel.Controls.Add(this.detailRight);
        this.detailPanel.Controls.Add(this.tblDetail);
        this.detailPanel.Dock = System.Windows.Forms.DockStyle.Bottom;
        this.detailPanel.Location = new System.Drawing.Point(0, 300);
        this.detailPanel.Name = "detailPanel";
        this.detailPanel.Size = new System.Drawing.Size(995, 109);
        this.detailPanel.TabIndex = 1;
        //
        // detailRight
        //
        this.detailRight.Controls.Add(this.btnExport);
        this.detailRight.Dock = System.Windows.Forms.DockStyle.Right;
        this.detailRight.Location = new System.Drawing.Point(860, 0);
        this.detailRight.Name = "detailRight";
        this.detailRight.Size = new System.Drawing.Size(133, 107);
        this.detailRight.TabIndex = 1;
        //
        // btnExport
        //
        this.btnExport.BackColor = Color.FromArgb(16, 185, 129);
        this.btnExport.FlatAppearance.BorderSize = 0;
        this.btnExport.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
        this.btnExport.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.btnExport.ForeColor = Color.White;
        this.btnExport.Location = new System.Drawing.Point(18, 38);
        this.btnExport.Name = "btnExport";
        this.btnExport.Size = new System.Drawing.Size(100, 30);
        this.btnExport.TabIndex = 0;
        this.btnExport.Text = "📥 导出 Excel";
        this.btnExport.UseVisualStyleBackColor = false;
        //
        // tblDetail
        //
        this.tblDetail.ColumnCount = 4;
        this.tblDetail.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 60F));
        this.tblDetail.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 40F));
        this.tblDetail.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 60F));
        this.tblDetail.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 40F));
        this.tblDetail.Controls.Add(this.lblCapName, 0, 0);
        this.tblDetail.Controls.Add(this.lblPartName, 1, 0);
        this.tblDetail.Controls.Add(this.lblCapIpn, 2, 0);
        this.tblDetail.Controls.Add(this.lblPartIpn, 3, 0);
        this.tblDetail.Controls.Add(this.lblCapType, 0, 1);
        this.tblDetail.Controls.Add(this.lblPartType, 1, 1);
        this.tblDetail.Controls.Add(this.lblCapStock, 2, 1);
        this.tblDetail.Controls.Add(this.lblPartStock, 3, 1);
        this.tblDetail.Dock = System.Windows.Forms.DockStyle.Fill;
        this.tblDetail.Location = new System.Drawing.Point(0, 0);
        this.tblDetail.Name = "tblDetail";
        this.tblDetail.RowCount = 2;
        this.tblDetail.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 50F));
        this.tblDetail.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 50F));
        this.tblDetail.Size = new System.Drawing.Size(860, 107);
        this.tblDetail.TabIndex = 0;
        this.tblDetail.Padding = new System.Windows.Forms.Padding(10, 5, 10, 5);
        //
        // lblCapName
        //
        this.lblCapName.AutoSize = true;
        this.lblCapName.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblCapName.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F, System.Drawing.FontStyle.Bold);
        this.lblCapName.ForeColor = System.Drawing.SystemColors.GrayText;
        this.lblCapName.Location = new System.Drawing.Point(13, 5);
        this.lblCapName.Name = "lblCapName";
        this.lblCapName.Size = new System.Drawing.Size(54, 48);
        this.lblCapName.TabIndex = 0;
        this.lblCapName.Text = "名称";
        this.lblCapName.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblPartName
        //
        this.lblPartName.AutoEllipsis = true;
        this.lblPartName.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblPartName.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F, System.Drawing.FontStyle.Bold);
        this.lblPartName.Location = new System.Drawing.Point(73, 5);
        this.lblPartName.Name = "lblPartName";
        this.lblPartName.Size = new System.Drawing.Size(288, 48);
        this.lblPartName.TabIndex = 1;
        this.lblPartName.Text = "-";
        this.lblPartName.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblCapIpn
        //
        this.lblCapIpn.AutoSize = true;
        this.lblCapIpn.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblCapIpn.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F, System.Drawing.FontStyle.Bold);
        this.lblCapIpn.ForeColor = System.Drawing.SystemColors.GrayText;
        this.lblCapIpn.Location = new System.Drawing.Point(367, 5);
        this.lblCapIpn.Name = "lblCapIpn";
        this.lblCapIpn.Size = new System.Drawing.Size(54, 48);
        this.lblCapIpn.TabIndex = 2;
        this.lblCapIpn.Text = "编码";
        this.lblCapIpn.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblPartIpn
        //
        this.lblPartIpn.AutoEllipsis = true;
        this.lblPartIpn.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblPartIpn.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.lblPartIpn.Location = new System.Drawing.Point(427, 5);
        this.lblPartIpn.Name = "lblPartIpn";
        this.lblPartIpn.Size = new System.Drawing.Size(420, 48);
        this.lblPartIpn.TabIndex = 3;
        this.lblPartIpn.Text = "-";
        this.lblPartIpn.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblCapType
        //
        this.lblCapType.AutoSize = true;
        this.lblCapType.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblCapType.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F, System.Drawing.FontStyle.Bold);
        this.lblCapType.ForeColor = System.Drawing.SystemColors.GrayText;
        this.lblCapType.Location = new System.Drawing.Point(13, 53);
        this.lblCapType.Name = "lblCapType";
        this.lblCapType.Size = new System.Drawing.Size(54, 49);
        this.lblCapType.TabIndex = 4;
        this.lblCapType.Text = "类型";
        this.lblCapType.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblPartType
        //
        this.lblPartType.AutoEllipsis = true;
        this.lblPartType.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblPartType.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.lblPartType.Location = new System.Drawing.Point(73, 53);
        this.lblPartType.Name = "lblPartType";
        this.lblPartType.Size = new System.Drawing.Size(288, 49);
        this.lblPartType.TabIndex = 5;
        this.lblPartType.Text = "-";
        this.lblPartType.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblCapStock
        //
        this.lblCapStock.AutoSize = true;
        this.lblCapStock.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblCapStock.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F, System.Drawing.FontStyle.Bold);
        this.lblCapStock.ForeColor = System.Drawing.SystemColors.GrayText;
        this.lblCapStock.Location = new System.Drawing.Point(367, 53);
        this.lblCapStock.Name = "lblCapStock";
        this.lblCapStock.Size = new System.Drawing.Size(54, 49);
        this.lblCapStock.TabIndex = 6;
        this.lblCapStock.Text = "库存";
        this.lblCapStock.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblPartStock
        //
        this.lblPartStock.AutoEllipsis = true;
        this.lblPartStock.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblPartStock.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.lblPartStock.Location = new System.Drawing.Point(427, 53);
        this.lblPartStock.Name = "lblPartStock";
        this.lblPartStock.Size = new System.Drawing.Size(420, 49);
        this.lblPartStock.TabIndex = 7;
        this.lblPartStock.Text = "-";
        this.lblPartStock.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // statusStrip
        //
        this.statusStrip.Items.AddRange(new System.Windows.Forms.ToolStripItem[] { this.lblStatus });
        this.statusStrip.Location = new System.Drawing.Point(0, 774);
        this.statusStrip.Name = "statusStrip";
        this.statusStrip.Size = new System.Drawing.Size(1280, 26);
        this.statusStrip.SizingGrip = false;
        this.statusStrip.TabIndex = 2;
        //
        // lblStatus
        //
        this.lblStatus.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.lblStatus.Name = "lblStatus";
        this.lblStatus.Size = new System.Drawing.Size(32, 21);
        this.lblStatus.Text = "就绪";
        //
        // MainForm
        //
        this.AutoScaleDimensions = new System.Drawing.SizeF(9F, 18F);
        this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
        this.ClientSize = new System.Drawing.Size(1280, 800);
        this.Controls.Add(this.mainSplit);
        this.Controls.Add(this.topBar);
        this.Controls.Add(this.statusStrip);
        this.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.MinimumSize = new System.Drawing.Size(960, 600);
        this.Name = "MainForm";
        this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
        this.Text = "设备 BOM 查询系统";
        this.topBar.ResumeLayout(false);
        this.topBar.PerformLayout();
        this.mainSplit.Panel1.ResumeLayout(false);
        this.mainSplit.Panel2.ResumeLayout(false);
        ((System.ComponentModel.ISupportInitialize)(this.mainSplit)).EndInit();
        this.mainSplit.ResumeLayout(false);
        this.leftPanel.ResumeLayout(false);
        this.rightPanel.ResumeLayout(false);
        this.rightSplit.Panel1.ResumeLayout(false);
        this.rightSplit.Panel2.ResumeLayout(false);
        ((System.ComponentModel.ISupportInitialize)(this.rightSplit)).EndInit();
        this.rightSplit.ResumeLayout(false);
        this.panelPartsList.ResumeLayout(false);
        this.panelBomDetail.ResumeLayout(false);
        this.rightTabs.ResumeLayout(false);
        this.tabBom.ResumeLayout(false);
        this.tabUsed.ResumeLayout(false);
        this.detailPanel.ResumeLayout(false);
        this.detailRight.ResumeLayout(false);
        this.tblDetail.ResumeLayout(false);
        this.tblDetail.PerformLayout();
        this.statusStrip.ResumeLayout(false);
        this.statusStrip.PerformLayout();
        this.ResumeLayout(false);
        this.PerformLayout();
    }

    #endregion

    private System.Windows.Forms.Panel topBar;
    private System.Windows.Forms.Label lblLogo;
    private System.Windows.Forms.TextBox txtSearch;
    private System.Windows.Forms.Button btnSearch;
    private System.Windows.Forms.ComboBox cbFilter;
    private System.Windows.Forms.Button btnRefresh;
    private System.Windows.Forms.Button btnLogout;
    private System.Windows.Forms.SplitContainer mainSplit;
    private System.Windows.Forms.Panel leftPanel;
    private System.Windows.Forms.Label leftHeader;
    private System.Windows.Forms.TreeView tvCategories;
    private System.Windows.Forms.Panel rightPanel;
    private System.Windows.Forms.SplitContainer rightSplit;
    private System.Windows.Forms.Panel panelPartsList;
    private System.Windows.Forms.Label partsHeader;
    private System.Windows.Forms.ListView lvParts;
    private System.Windows.Forms.ColumnHeader colPartIpn;
    private System.Windows.Forms.ColumnHeader colPartName;
    private System.Windows.Forms.ColumnHeader colPartType;
    private System.Windows.Forms.ColumnHeader colPartStock;
    private System.Windows.Forms.ColumnHeader colPartDesc;
    private System.Windows.Forms.Panel panelBomDetail;
    private System.Windows.Forms.TabControl rightTabs;
    private System.Windows.Forms.TabPage tabBom;
    private System.Windows.Forms.TreeView tvBom;
    private System.Windows.Forms.TabPage tabUsed;
    private System.Windows.Forms.ListView lvWhereUsed;
    private System.Windows.Forms.ColumnHeader colWIpn;
    private System.Windows.Forms.ColumnHeader colWName;
    private System.Windows.Forms.ColumnHeader colWDesc;
    private System.Windows.Forms.ColumnHeader colWQty;
    private System.Windows.Forms.Panel detailPanel;
    private System.Windows.Forms.TableLayoutPanel tblDetail;
    private System.Windows.Forms.Label lblCapName;
    private System.Windows.Forms.Label lblPartName;
    private System.Windows.Forms.Label lblCapIpn;
    private System.Windows.Forms.Label lblPartIpn;
    private System.Windows.Forms.Label lblCapType;
    private System.Windows.Forms.Label lblPartType;
    private System.Windows.Forms.Label lblCapStock;
    private System.Windows.Forms.Label lblPartStock;
    private System.Windows.Forms.Panel detailRight;
    private System.Windows.Forms.Button btnExport;
    private System.Windows.Forms.StatusStrip statusStrip;
    private System.Windows.Forms.ToolStripStatusLabel lblStatus;
}
