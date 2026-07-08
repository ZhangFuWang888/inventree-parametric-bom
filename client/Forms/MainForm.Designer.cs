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
        this.leftHeader = new System.Windows.Forms.Label();
        this.tvProducts = new System.Windows.Forms.TreeView();
        this.rightPanel = new System.Windows.Forms.Panel();
        this.rightTabs = new System.Windows.Forms.TabControl();
        this.tabBom = new System.Windows.Forms.TabPage();
        this.tvBom = new System.Windows.Forms.TreeView();
        this.tabUsed = new System.Windows.Forms.TabPage();
        this.lvWhereUsed = new System.Windows.Forms.ListView();
        this.colIpn = new System.Windows.Forms.ColumnHeader();
        this.colName = new System.Windows.Forms.ColumnHeader();
        this.colDesc = new System.Windows.Forms.ColumnHeader();
        this.colQty = new System.Windows.Forms.ColumnHeader();
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
        this.topBar.Controls.Add(this.btnLogout);
        this.topBar.Controls.Add(this.btnRefresh);
        this.topBar.Controls.Add(this.cbFilter);
        this.topBar.Controls.Add(this.btnSearch);
        this.topBar.Controls.Add(this.txtSearch);
        this.topBar.Controls.Add(this.lblLogo);
        this.topBar.Dock = System.Windows.Forms.DockStyle.Top;
        this.topBar.Location = new System.Drawing.Point(0, 0);
        this.topBar.Name = "topBar";
        this.topBar.Size = new System.Drawing.Size(1280, 36);
        this.topBar.TabIndex = 0;
        //
        // lblLogo
        //
        this.lblLogo.AutoSize = true;
        this.lblLogo.Font = new System.Drawing.Font("Microsoft YaHei UI", 10F, System.Drawing.FontStyle.Bold);
        this.lblLogo.Location = new System.Drawing.Point(8, 8);
        this.lblLogo.Name = "lblLogo";
        this.lblLogo.Size = new System.Drawing.Size(154, 22);
        this.lblLogo.TabIndex = 0;
        this.lblLogo.Text = "设备 BOM 查询系统";
        //
        // txtSearch
        //
        this.txtSearch.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left)
        | System.Windows.Forms.AnchorStyles.Right)));
        this.txtSearch.Location = new System.Drawing.Point(280, 6);
        this.txtSearch.Name = "txtSearch";
        this.txtSearch.PlaceholderText = "搜索物料编码 / 名称";
        this.txtSearch.Size = new System.Drawing.Size(560, 25);
        this.txtSearch.TabIndex = 1;
        //
        // btnSearch
        //
        this.btnSearch.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
        this.btnSearch.Location = new System.Drawing.Point(848, 5);
        this.btnSearch.Name = "btnSearch";
        this.btnSearch.Size = new System.Drawing.Size(75, 26);
        this.btnSearch.TabIndex = 2;
        this.btnSearch.Text = "搜索";
        this.btnSearch.UseVisualStyleBackColor = true;
        //
        // cbFilter
        //
        this.cbFilter.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
        this.cbFilter.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
        this.cbFilter.Items.AddRange(new object[] { "全部", "产品", "部装", "零件" });
        this.cbFilter.Location = new System.Drawing.Point(932, 6);
        this.cbFilter.Name = "cbFilter";
        this.cbFilter.Size = new System.Drawing.Size(120, 26);
        this.cbFilter.TabIndex = 3;
        //
        // btnRefresh
        //
        this.btnRefresh.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
        this.btnRefresh.Location = new System.Drawing.Point(1062, 5);
        this.btnRefresh.Name = "btnRefresh";
        this.btnRefresh.Size = new System.Drawing.Size(75, 26);
        this.btnRefresh.TabIndex = 4;
        this.btnRefresh.Text = "刷新";
        this.btnRefresh.UseVisualStyleBackColor = true;
        //
        // btnLogout
        //
        this.btnLogout.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
        this.btnLogout.Location = new System.Drawing.Point(1197, 5);
        this.btnLogout.Name = "btnLogout";
        this.btnLogout.Size = new System.Drawing.Size(75, 26);
        this.btnLogout.TabIndex = 5;
        this.btnLogout.Text = "退出登录";
        this.btnLogout.UseVisualStyleBackColor = true;
        //
        // mainSplit
        //
        this.mainSplit.Dock = System.Windows.Forms.DockStyle.Fill;
        this.mainSplit.FixedPanel = System.Windows.Forms.FixedPanel.Panel1;
        this.mainSplit.Location = new System.Drawing.Point(0, 36);
        this.mainSplit.Name = "mainSplit";
        //
        // mainSplit.Panel1
        //
        this.mainSplit.Panel1.Controls.Add(this.leftPanel);
        this.mainSplit.Panel1MinSize = 240;
        //
        // mainSplit.Panel2
        //
        this.mainSplit.Panel2.Controls.Add(this.rightPanel);
        this.mainSplit.Size = new System.Drawing.Size(1280, 738);
        this.mainSplit.SplitterDistance = 320;
        this.mainSplit.SplitterWidth = 5;
        this.mainSplit.TabIndex = 1;
        //
        // leftPanel
        //
        this.leftPanel.Controls.Add(this.tvProducts);
        this.leftPanel.Controls.Add(this.leftHeader);
        this.leftPanel.Dock = System.Windows.Forms.DockStyle.Fill;
        this.leftPanel.Location = new System.Drawing.Point(0, 0);
        this.leftPanel.Name = "leftPanel";
        this.leftPanel.Size = new System.Drawing.Size(320, 738);
        this.leftPanel.TabIndex = 0;
        //
        // leftHeader
        //
        this.leftHeader.Dock = System.Windows.Forms.DockStyle.Top;
        this.leftHeader.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F, System.Drawing.FontStyle.Bold);
        this.leftHeader.Location = new System.Drawing.Point(0, 0);
        this.leftHeader.Name = "leftHeader";
        this.leftHeader.Size = new System.Drawing.Size(320, 28);
        this.leftHeader.TabIndex = 0;
        this.leftHeader.Text = "  产品列表";
        this.leftHeader.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // tvProducts
        //
        this.tvProducts.Dock = System.Windows.Forms.DockStyle.Fill;
        this.tvProducts.FullRowSelect = true;
        this.tvProducts.HideSelection = false;
        this.tvProducts.Location = new System.Drawing.Point(0, 28);
        this.tvProducts.Name = "tvProducts";
        this.tvProducts.ShowNodeToolTips = true;
        this.tvProducts.Size = new System.Drawing.Size(320, 710);
        this.tvProducts.TabIndex = 1;
        //
        // rightPanel
        //
        this.rightPanel.Controls.Add(this.rightTabs);
        this.rightPanel.Controls.Add(this.detailPanel);
        this.rightPanel.Dock = System.Windows.Forms.DockStyle.Fill;
        this.rightPanel.Location = new System.Drawing.Point(0, 0);
        this.rightPanel.Name = "rightPanel";
        this.rightPanel.Size = new System.Drawing.Size(955, 738);
        this.rightPanel.TabIndex = 0;
        //
        // rightTabs
        //
        this.rightTabs.Controls.Add(this.tabBom);
        this.rightTabs.Controls.Add(this.tabUsed);
        this.rightTabs.Dock = System.Windows.Forms.DockStyle.Fill;
        this.rightTabs.Location = new System.Drawing.Point(0, 0);
        this.rightTabs.Name = "rightTabs";
        this.rightTabs.SelectedIndex = 0;
        this.rightTabs.Size = new System.Drawing.Size(955, 632);
        this.rightTabs.TabIndex = 0;
        //
        // tabBom
        //
        this.tabBom.Controls.Add(this.tvBom);
        this.tabBom.Location = new System.Drawing.Point(4, 25);
        this.tabBom.Name = "tabBom";
        this.tabBom.Padding = new System.Windows.Forms.Padding(3);
        this.tabBom.Size = new System.Drawing.Size(947, 603);
        this.tabBom.TabIndex = 0;
        this.tabBom.Text = "BOM 结构";
        this.tabBom.UseVisualStyleBackColor = true;
        //
        // tvBom
        //
        this.tvBom.Dock = System.Windows.Forms.DockStyle.Fill;
        this.tvBom.FullRowSelect = true;
        this.tvBom.HideSelection = false;
        this.tvBom.Location = new System.Drawing.Point(3, 3);
        this.tvBom.Name = "tvBom";
        this.tvBom.ShowNodeToolTips = true;
        this.tvBom.Size = new System.Drawing.Size(941, 597);
        this.tvBom.TabIndex = 0;
        //
        // tabUsed
        //
        this.tabUsed.Controls.Add(this.lvWhereUsed);
        this.tabUsed.Location = new System.Drawing.Point(4, 25);
        this.tabUsed.Name = "tabUsed";
        this.tabUsed.Padding = new System.Windows.Forms.Padding(3);
        this.tabUsed.Size = new System.Drawing.Size(947, 603);
        this.tabUsed.TabIndex = 1;
        this.tabUsed.Text = "反向查询 (Where Used)";
        this.tabUsed.UseVisualStyleBackColor = true;
        //
        // lvWhereUsed
        //
        this.lvWhereUsed.Columns.AddRange(new System.Windows.Forms.ColumnHeader[] {
            this.colIpn,
            this.colName,
            this.colDesc,
            this.colQty});
        this.lvWhereUsed.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lvWhereUsed.FullRowSelect = true;
        this.lvWhereUsed.GridLines = true;
        this.lvWhereUsed.Location = new System.Drawing.Point(3, 3);
        this.lvWhereUsed.Name = "lvWhereUsed";
        this.lvWhereUsed.Size = new System.Drawing.Size(941, 597);
        this.lvWhereUsed.TabIndex = 0;
        this.lvWhereUsed.UseCompatibleStateImageBehavior = false;
        this.lvWhereUsed.View = System.Windows.Forms.View.Details;
        //
        // colIpn
        //
        this.colIpn.Text = "物料编码";
        this.colIpn.Width = 110;
        //
        // colName
        //
        this.colName.Text = "名称";
        this.colName.Width = 180;
        //
        // colDesc
        //
        this.colDesc.Text = "描述";
        this.colDesc.Width = 280;
        //
        // colQty
        //
        this.colQty.Text = "数量";
        this.colQty.TextAlign = System.Windows.Forms.HorizontalAlignment.Right;
        this.colQty.Width = 70;
        //
        // detailPanel
        //
        this.detailPanel.Controls.Add(this.detailRight);
        this.detailPanel.Controls.Add(this.tblDetail);
        this.detailPanel.Dock = System.Windows.Forms.DockStyle.Bottom;
        this.detailPanel.Location = new System.Drawing.Point(0, 632);
        this.detailPanel.Name = "detailPanel";
        this.detailPanel.Size = new System.Drawing.Size(955, 106);
        this.detailPanel.TabIndex = 1;
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
        this.tblDetail.Size = new System.Drawing.Size(835, 106);
        this.tblDetail.TabIndex = 0;
        //
        // lblCapName
        //
        this.lblCapName.AutoSize = true;
        this.lblCapName.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblCapName.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F, System.Drawing.FontStyle.Bold);
        this.lblCapName.ForeColor = System.Drawing.SystemColors.GrayText;
        this.lblCapName.Location = new System.Drawing.Point(3, 0);
        this.lblCapName.Name = "lblCapName";
        this.lblCapName.Size = new System.Drawing.Size(54, 53);
        this.lblCapName.TabIndex = 0;
        this.lblCapName.Text = "名称";
        this.lblCapName.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblPartName
        //
        this.lblPartName.AutoEllipsis = true;
        this.lblPartName.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblPartName.Location = new System.Drawing.Point(63, 0);
        this.lblPartName.Name = "lblPartName";
        this.lblPartName.Size = new System.Drawing.Size(277, 53);
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
        this.lblCapIpn.Location = new System.Drawing.Point(346, 0);
        this.lblCapIpn.Name = "lblCapIpn";
        this.lblCapIpn.Size = new System.Drawing.Size(54, 53);
        this.lblCapIpn.TabIndex = 2;
        this.lblCapIpn.Text = "物料编码";
        this.lblCapIpn.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblPartIpn
        //
        this.lblPartIpn.AutoEllipsis = true;
        this.lblPartIpn.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblPartIpn.Location = new System.Drawing.Point(406, 0);
        this.lblPartIpn.Name = "lblPartIpn";
        this.lblPartIpn.Size = new System.Drawing.Size(276, 53);
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
        this.lblCapType.Location = new System.Drawing.Point(3, 53);
        this.lblCapType.Name = "lblCapType";
        this.lblCapType.Size = new System.Drawing.Size(54, 53);
        this.lblCapType.TabIndex = 4;
        this.lblCapType.Text = "类型";
        this.lblCapType.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblPartType
        //
        this.lblPartType.AutoEllipsis = true;
        this.lblPartType.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblPartType.Location = new System.Drawing.Point(63, 53);
        this.lblPartType.Name = "lblPartType";
        this.lblPartType.Size = new System.Drawing.Size(277, 53);
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
        this.lblCapStock.Location = new System.Drawing.Point(346, 53);
        this.lblCapStock.Name = "lblCapStock";
        this.lblCapStock.Size = new System.Drawing.Size(54, 53);
        this.lblCapStock.TabIndex = 6;
        this.lblCapStock.Text = "库存";
        this.lblCapStock.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lblPartStock
        //
        this.lblPartStock.AutoEllipsis = true;
        this.lblPartStock.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lblPartStock.Location = new System.Drawing.Point(406, 53);
        this.lblPartStock.Name = "lblPartStock";
        this.lblPartStock.Size = new System.Drawing.Size(276, 53);
        this.lblPartStock.TabIndex = 7;
        this.lblPartStock.Text = "-";
        this.lblPartStock.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // detailRight
        //
        this.detailRight.Controls.Add(this.btnExport);
        this.detailRight.Dock = System.Windows.Forms.DockStyle.Right;
        this.detailRight.Location = new System.Drawing.Point(835, 0);
        this.detailRight.Name = "detailRight";
        this.detailRight.Size = new System.Drawing.Size(120, 106);
        this.detailRight.TabIndex = 1;
        //
        // btnExport
        //
        this.btnExport.Location = new System.Drawing.Point(15, 38);
        this.btnExport.Name = "btnExport";
        this.btnExport.Size = new System.Drawing.Size(95, 30);
        this.btnExport.TabIndex = 0;
        this.btnExport.Text = "导出 Excel";
        this.btnExport.UseVisualStyleBackColor = true;
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
    private System.Windows.Forms.TreeView tvProducts;
    private System.Windows.Forms.Panel rightPanel;
    private System.Windows.Forms.TabControl rightTabs;
    private System.Windows.Forms.TabPage tabBom;
    private System.Windows.Forms.TreeView tvBom;
    private System.Windows.Forms.TabPage tabUsed;
    private System.Windows.Forms.ListView lvWhereUsed;
    private System.Windows.Forms.ColumnHeader colIpn;
    private System.Windows.Forms.ColumnHeader colName;
    private System.Windows.Forms.ColumnHeader colDesc;
    private System.Windows.Forms.ColumnHeader colQty;
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