namespace BomQueryClient.Forms;

partial class ConfiguratorForm
{
    private System.ComponentModel.IContainer components = null;

    protected override void Dispose(bool disposing)
    {
        if (disposing && (components != null))
            components.Dispose();
        base.Dispose(disposing);
    }

    #region Windows 窗体设计器生成的代码

    private void InitializeComponent()
    {
        this.components = new System.ComponentModel.Container();
        this.topBar = new System.Windows.Forms.Panel();
        this.lblTitle = new System.Windows.Forms.Label();
        this.mainSplit = new System.Windows.Forms.SplitContainer();
        this.leftPanel = new System.Windows.Forms.Panel();
        this.lvConfigs = new System.Windows.Forms.ListView();
        this.colConfigTitle = new System.Windows.Forms.ColumnHeader();
        this.colConfigStatus = new System.Windows.Forms.ColumnHeader();
        this.colConfigDate = new System.Windows.Forms.ColumnHeader();
        this.configHeader = new System.Windows.Forms.Label();
        this.rightPanel = new System.Windows.Forms.Panel();
        this.rightSplit = new System.Windows.Forms.SplitContainer();
        this.paramPanel = new System.Windows.Forms.Panel();
        this.dgvParams = new System.Windows.Forms.DataGridView();
        this.colParamName = new System.Windows.Forms.DataGridViewTextBoxColumn();
        this.colParamValue = new System.Windows.Forms.DataGridViewTextBoxColumn();
        this.colParamType = new System.Windows.Forms.DataGridViewTextBoxColumn();
        this.paramHeader = new System.Windows.Forms.Label();
        this.bomPanel = new System.Windows.Forms.Panel();
        this.tvBomPreview = new System.Windows.Forms.TreeView();
        this.bomPreviewHeader = new System.Windows.Forms.Label();
        this.createPanel = new System.Windows.Forms.Panel();
        this.btnPreviewBom = new System.Windows.Forms.Button();
        this.btnRelease = new System.Windows.Forms.Button();
        this.btnSave = new System.Windows.Forms.Button();
        this.btnNewConfig = new System.Windows.Forms.Button();
        this.txtTitle = new System.Windows.Forms.TextBox();
        this.cboProduct = new System.Windows.Forms.ComboBox();
        this.lblProduct = new System.Windows.Forms.Label();
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
        this.paramPanel.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)(this.dgvParams)).BeginInit();
        this.bomPanel.SuspendLayout();
        this.createPanel.SuspendLayout();
        this.statusStrip.SuspendLayout();
        this.SuspendLayout();
        //
        // topBar
        //
        this.topBar.BackColor = Color.FromArgb(30, 58, 138);
        this.topBar.Controls.Add(this.lblTitle);
        this.topBar.Dock = System.Windows.Forms.DockStyle.Top;
        this.topBar.Location = new System.Drawing.Point(0, 0);
        this.topBar.Name = "topBar";
        this.topBar.Size = new System.Drawing.Size(1200, 40);
        this.topBar.TabIndex = 0;
        //
        // lblTitle
        //
        this.lblTitle.AutoSize = true;
        this.lblTitle.Font = new System.Drawing.Font("Microsoft YaHei UI", 11F, System.Drawing.FontStyle.Bold);
        this.lblTitle.ForeColor = Color.White;
        this.lblTitle.Location = new System.Drawing.Point(12, 9);
        this.lblTitle.Name = "lblTitle";
        this.lblTitle.Size = new System.Drawing.Size(206, 24);
        this.lblTitle.TabIndex = 0;
        this.lblTitle.Text = "⚙ 参数化配置器";
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
        this.mainSplit.Panel1MinSize = 220;
        //
        // mainSplit.Panel2
        //
        this.mainSplit.Panel2.Controls.Add(this.rightPanel);
        this.mainSplit.Size = new System.Drawing.Size(1200, 734);
        this.mainSplit.SplitterDistance = 320;
        this.mainSplit.SplitterWidth = 5;
        this.mainSplit.TabIndex = 1;
        //
        // leftPanel
        //
        this.leftPanel.Controls.Add(this.lvConfigs);
        this.leftPanel.Controls.Add(this.configHeader);
        this.leftPanel.Dock = System.Windows.Forms.DockStyle.Fill;
        this.leftPanel.Location = new System.Drawing.Point(0, 0);
        this.leftPanel.Name = "leftPanel";
        this.leftPanel.Size = new System.Drawing.Size(320, 734);
        this.leftPanel.TabIndex = 0;
        //
        // configHeader
        //
        this.configHeader.BackColor = Color.FromArgb(243, 244, 246);
        this.configHeader.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
        this.configHeader.Dock = System.Windows.Forms.DockStyle.Top;
        this.configHeader.Font = new System.Drawing.Font("Microsoft YaHei UI", 9.5F, System.Drawing.FontStyle.Bold);
        this.configHeader.ForeColor = Color.FromArgb(30, 58, 138);
        this.configHeader.Location = new System.Drawing.Point(0, 0);
        this.configHeader.Name = "configHeader";
        this.configHeader.Padding = new System.Windows.Forms.Padding(10, 0, 0, 0);
        this.configHeader.Size = new System.Drawing.Size(320, 32);
        this.configHeader.TabIndex = 0;
        this.configHeader.Text = "📋 配置列表";
        this.configHeader.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // lvConfigs
        //
        this.lvConfigs.BorderStyle = System.Windows.Forms.BorderStyle.None;
        this.lvConfigs.Columns.AddRange(new System.Windows.Forms.ColumnHeader[] {
            this.colConfigTitle,
            this.colConfigStatus,
            this.colConfigDate});
        this.lvConfigs.Dock = System.Windows.Forms.DockStyle.Fill;
        this.lvConfigs.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.lvConfigs.FullRowSelect = true;
        this.lvConfigs.GridLines = true;
        this.lvConfigs.HideSelection = false;
        this.lvConfigs.Location = new System.Drawing.Point(0, 32);
        this.lvConfigs.MultiSelect = false;
        this.lvConfigs.Name = "lvConfigs";
        this.lvConfigs.Size = new System.Drawing.Size(320, 702);
        this.lvConfigs.TabIndex = 1;
        this.lvConfigs.UseCompatibleStateImageBehavior = false;
        this.lvConfigs.View = System.Windows.Forms.View.Details;
        //
        // colConfigTitle
        //
        this.colConfigTitle.Text = "标题";
        this.colConfigTitle.Width = 140;
        //
        // colConfigStatus
        //
        this.colConfigStatus.Text = "状态";
        this.colConfigStatus.Width = 80;
        //
        // colConfigDate
        //
        this.colConfigDate.Text = "日期";
        this.colConfigDate.Width = 80;
        //
        // rightPanel
        //
        this.rightPanel.Controls.Add(this.rightSplit);
        this.rightPanel.Controls.Add(this.createPanel);
        this.rightPanel.Dock = System.Windows.Forms.DockStyle.Fill;
        this.rightPanel.Location = new System.Drawing.Point(0, 0);
        this.rightPanel.Name = "rightPanel";
        this.rightPanel.Size = new System.Drawing.Size(875, 734);
        this.rightPanel.TabIndex = 0;
        //
        // rightSplit
        //
        this.rightSplit.Dock = System.Windows.Forms.DockStyle.Fill;
        this.rightSplit.FixedPanel = System.Windows.Forms.FixedPanel.Panel2;
        this.rightSplit.Location = new System.Drawing.Point(0, 70);
        this.rightSplit.Name = "rightSplit";
        this.rightSplit.Orientation = System.Windows.Forms.Orientation.Horizontal;
        //
        // rightSplit.Panel1
        //
        this.rightSplit.Panel1.Controls.Add(this.paramPanel);
        //
        // rightSplit.Panel2
        //
        this.rightSplit.Panel2.Controls.Add(this.bomPanel);
        this.rightSplit.Size = new System.Drawing.Size(875, 664);
        this.rightSplit.SplitterDistance = 300;
        this.rightSplit.SplitterWidth = 5;
        this.rightSplit.TabIndex = 1;
        //
        // paramPanel
        //
        this.paramPanel.Controls.Add(this.dgvParams);
        this.paramPanel.Controls.Add(this.paramHeader);
        this.paramPanel.Dock = System.Windows.Forms.DockStyle.Fill;
        this.paramPanel.Location = new System.Drawing.Point(0, 0);
        this.paramPanel.Name = "paramPanel";
        this.paramPanel.Size = new System.Drawing.Size(875, 300);
        this.paramPanel.TabIndex = 0;
        //
        // paramHeader
        //
        this.paramHeader.BackColor = Color.FromArgb(243, 244, 246);
        this.paramHeader.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
        this.paramHeader.Dock = System.Windows.Forms.DockStyle.Top;
        this.paramHeader.Font = new System.Drawing.Font("Microsoft YaHei UI", 9.5F, System.Drawing.FontStyle.Bold);
        this.paramHeader.ForeColor = Color.FromArgb(30, 58, 138);
        this.paramHeader.Location = new System.Drawing.Point(0, 0);
        this.paramHeader.Name = "paramHeader";
        this.paramHeader.Padding = new System.Windows.Forms.Padding(10, 0, 0, 0);
        this.paramHeader.Size = new System.Drawing.Size(875, 32);
        this.paramHeader.TabIndex = 0;
        this.paramHeader.Text = "📐 参数值设置 — 选择产品或配置后编辑";
        this.paramHeader.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // dgvParams
        //
        this.dgvParams.AllowUserToAddRows = false;
        this.dgvParams.AllowUserToDeleteRows = false;
        this.dgvParams.BackgroundColor = Color.White;
        this.dgvParams.BorderStyle = System.Windows.Forms.BorderStyle.None;
        this.dgvParams.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
        this.dgvParams.Columns.AddRange(new System.Windows.Forms.DataGridViewColumn[] {
            this.colParamName,
            this.colParamValue,
            this.colParamType});
        this.dgvParams.Dock = System.Windows.Forms.DockStyle.Fill;
        this.dgvParams.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.dgvParams.GridColor = System.Drawing.Color.FromArgb(229, 231, 235);
        this.dgvParams.Location = new System.Drawing.Point(0, 32);
        this.dgvParams.MultiSelect = false;
        this.dgvParams.Name = "dgvParams";
        this.dgvParams.RowHeadersVisible = false;
        this.dgvParams.RowTemplate.Height = 28;
        this.dgvParams.SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.CellSelect;
        this.dgvParams.Size = new System.Drawing.Size(875, 268);
        this.dgvParams.TabIndex = 1;
        //
        // colParamName
        //
        this.colParamName.HeaderText = "参数名";
        this.colParamName.Name = "colParamName";
        this.colParamName.ReadOnly = true;
        this.colParamName.Width = 160;
        //
        // colParamValue
        //
        this.colParamValue.HeaderText = "值";
        this.colParamValue.Name = "colParamValue";
        this.colParamValue.Width = 200;
        //
        // colParamType
        //
        this.colParamType.HeaderText = "类型";
        this.colParamType.Name = "colParamType";
        this.colParamType.ReadOnly = true;
        this.colParamType.Width = 100;
        //
        // bomPanel
        //
        this.bomPanel.Controls.Add(this.tvBomPreview);
        this.bomPanel.Controls.Add(this.bomPreviewHeader);
        this.bomPanel.Dock = System.Windows.Forms.DockStyle.Fill;
        this.bomPanel.Location = new System.Drawing.Point(0, 0);
        this.bomPanel.Name = "bomPanel";
        this.bomPanel.Size = new System.Drawing.Size(875, 359);
        this.bomPanel.TabIndex = 0;
        //
        // bomPreviewHeader
        //
        this.bomPreviewHeader.BackColor = Color.FromArgb(243, 244, 246);
        this.bomPreviewHeader.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
        this.bomPreviewHeader.Dock = System.Windows.Forms.DockStyle.Top;
        this.bomPreviewHeader.Font = new System.Drawing.Font("Microsoft YaHei UI", 9.5F, System.Drawing.FontStyle.Bold);
        this.bomPreviewHeader.ForeColor = Color.FromArgb(30, 58, 138);
        this.bomPreviewHeader.Location = new System.Drawing.Point(0, 0);
        this.bomPreviewHeader.Name = "bomPreviewHeader";
        this.bomPreviewHeader.Padding = new System.Windows.Forms.Padding(10, 0, 0, 0);
        this.bomPreviewHeader.Size = new System.Drawing.Size(875, 32);
        this.bomPreviewHeader.TabIndex = 0;
        this.bomPreviewHeader.Text = "📊 BOM 预览（评估结果）";
        this.bomPreviewHeader.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
        //
        // tvBomPreview
        //
        this.tvBomPreview.BorderStyle = System.Windows.Forms.BorderStyle.None;
        this.tvBomPreview.Dock = System.Windows.Forms.DockStyle.Fill;
        this.tvBomPreview.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.tvBomPreview.FullRowSelect = true;
        this.tvBomPreview.HideSelection = false;
        this.tvBomPreview.Location = new System.Drawing.Point(0, 32);
        this.tvBomPreview.Name = "tvBomPreview";
        this.tvBomPreview.ShowNodeToolTips = true;
        this.tvBomPreview.Size = new System.Drawing.Size(875, 327);
        this.tvBomPreview.TabIndex = 1;
        //
        // createPanel
        //
        this.createPanel.BackColor = Color.FromArgb(249, 250, 251);
        this.createPanel.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
        this.createPanel.Controls.Add(this.btnPreviewBom);
        this.createPanel.Controls.Add(this.btnRelease);
        this.createPanel.Controls.Add(this.btnSave);
        this.createPanel.Controls.Add(this.btnNewConfig);
        this.createPanel.Controls.Add(this.txtTitle);
        this.createPanel.Controls.Add(this.cboProduct);
        this.createPanel.Controls.Add(this.lblProduct);
        this.createPanel.Dock = System.Windows.Forms.DockStyle.Top;
        this.createPanel.Location = new System.Drawing.Point(0, 0);
        this.createPanel.Name = "createPanel";
        this.createPanel.Size = new System.Drawing.Size(875, 70);
        this.createPanel.TabIndex = 0;
        //
        // lblProduct
        //
        this.lblProduct.AutoSize = true;
        this.lblProduct.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F, System.Drawing.FontStyle.Bold);
        this.lblProduct.Location = new System.Drawing.Point(12, 12);
        this.lblProduct.Name = "lblProduct";
        this.lblProduct.Size = new System.Drawing.Size(57, 20);
        this.lblProduct.TabIndex = 0;
        this.lblProduct.Text = "产品：";
        //
        // cboProduct
        //
        this.cboProduct.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
        this.cboProduct.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.cboProduct.Location = new System.Drawing.Point(72, 9);
        this.cboProduct.Name = "cboProduct";
        this.cboProduct.Size = new System.Drawing.Size(260, 26);
        this.cboProduct.TabIndex = 1;
        //
        // txtTitle
        //
        this.txtTitle.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.txtTitle.Location = new System.Drawing.Point(72, 38);
        this.txtTitle.Name = "txtTitle";
        this.txtTitle.PlaceholderText = "配置名称（如：客户A方案）";
        this.txtTitle.Size = new System.Drawing.Size(260, 25);
        this.txtTitle.TabIndex = 2;
        //
        // btnNewConfig
        //
        this.btnNewConfig.BackColor = Color.FromArgb(59, 130, 246);
        this.btnNewConfig.FlatAppearance.BorderSize = 0;
        this.btnNewConfig.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
        this.btnNewConfig.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.btnNewConfig.ForeColor = Color.White;
        this.btnNewConfig.Location = new System.Drawing.Point(340, 38);
        this.btnNewConfig.Name = "btnNewConfig";
        this.btnNewConfig.Size = new System.Drawing.Size(90, 26);
        this.btnNewConfig.TabIndex = 3;
        this.btnNewConfig.Text = "➕ 新建";
        this.btnNewConfig.UseVisualStyleBackColor = false;
        //
        // btnSave
        //
        this.btnSave.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
        this.btnSave.BackColor = Color.FromArgb(16, 185, 129);
        this.btnSave.FlatAppearance.BorderSize = 0;
        this.btnSave.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
        this.btnSave.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.btnSave.ForeColor = Color.White;
        this.btnSave.Location = new System.Drawing.Point(680, 8);
        this.btnSave.Name = "btnSave";
        this.btnSave.Size = new System.Drawing.Size(90, 26);
        this.btnSave.TabIndex = 4;
        this.btnSave.Text = "💾 保存";
        this.btnSave.UseVisualStyleBackColor = false;
        //
        // btnRelease
        //
        this.btnRelease.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
        this.btnRelease.BackColor = Color.FromArgb(139, 92, 246);
        this.btnRelease.FlatAppearance.BorderSize = 0;
        this.btnRelease.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
        this.btnRelease.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.btnRelease.ForeColor = Color.White;
        this.btnRelease.Location = new System.Drawing.Point(776, 8);
        this.btnRelease.Name = "btnRelease";
        this.btnRelease.Size = new System.Drawing.Size(90, 26);
        this.btnRelease.TabIndex = 5;
        this.btnRelease.Text = "✅ 发布";
        this.btnRelease.UseVisualStyleBackColor = false;
        //
        // btnPreviewBom
        //
        this.btnPreviewBom.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
        this.btnPreviewBom.BackColor = Color.FromArgb(245, 158, 11);
        this.btnPreviewBom.FlatAppearance.BorderSize = 0;
        this.btnPreviewBom.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
        this.btnPreviewBom.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.btnPreviewBom.ForeColor = Color.White;
        this.btnPreviewBom.Location = new System.Drawing.Point(584, 8);
        this.btnPreviewBom.Name = "btnPreviewBom";
        this.btnPreviewBom.Size = new System.Drawing.Size(90, 26);
        this.btnPreviewBom.TabIndex = 6;
        this.btnPreviewBom.Text = "📊 预览BOM";
        this.btnPreviewBom.UseVisualStyleBackColor = false;
        //
        // statusStrip
        //
        this.statusStrip.Items.AddRange(new System.Windows.Forms.ToolStripItem[] { this.lblStatus });
        this.statusStrip.Location = new System.Drawing.Point(0, 774);
        this.statusStrip.Name = "statusStrip";
        this.statusStrip.Size = new System.Drawing.Size(1200, 26);
        this.statusStrip.SizingGrip = false;
        this.statusStrip.TabIndex = 2;
        //
        // lblStatus
        //
        this.lblStatus.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.lblStatus.Name = "lblStatus";
        this.lblStatus.Size = new System.Drawing.Size(68, 20);
        this.lblStatus.Text = "选择产品...";
        //
        // ConfiguratorForm
        //
        this.AutoScaleDimensions = new System.Drawing.SizeF(9F, 18F);
        this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
        this.ClientSize = new System.Drawing.Size(1200, 800);
        this.Controls.Add(this.mainSplit);
        this.Controls.Add(this.topBar);
        this.Controls.Add(this.statusStrip);
        this.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.MinimumSize = new System.Drawing.Size(900, 600);
        this.Name = "ConfiguratorForm";
        this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
        this.Text = "参数化配置器";
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
        this.paramPanel.ResumeLayout(false);
        ((System.ComponentModel.ISupportInitialize)(this.dgvParams)).EndInit();
        this.bomPanel.ResumeLayout(false);
        this.createPanel.ResumeLayout(false);
        this.createPanel.PerformLayout();
        this.statusStrip.ResumeLayout(false);
        this.statusStrip.PerformLayout();
        this.ResumeLayout(false);
        this.PerformLayout();
    }

    #endregion

    private System.Windows.Forms.Panel topBar;
    private System.Windows.Forms.Label lblTitle;
    private System.Windows.Forms.SplitContainer mainSplit;
    private System.Windows.Forms.Panel leftPanel;
    private System.Windows.Forms.Label configHeader;
    private System.Windows.Forms.ListView lvConfigs;
    private System.Windows.Forms.ColumnHeader colConfigTitle;
    private System.Windows.Forms.ColumnHeader colConfigStatus;
    private System.Windows.Forms.ColumnHeader colConfigDate;
    private System.Windows.Forms.Panel rightPanel;
    private System.Windows.Forms.SplitContainer rightSplit;
    private System.Windows.Forms.Panel paramPanel;
    private System.Windows.Forms.Label paramHeader;
    private System.Windows.Forms.DataGridView dgvParams;
    private System.Windows.Forms.DataGridViewTextBoxColumn colParamName;
    private System.Windows.Forms.DataGridViewTextBoxColumn colParamValue;
    private System.Windows.Forms.DataGridViewTextBoxColumn colParamType;
    private System.Windows.Forms.Panel bomPanel;
    private System.Windows.Forms.Label bomPreviewHeader;
    private System.Windows.Forms.TreeView tvBomPreview;
    private System.Windows.Forms.Panel createPanel;
    private System.Windows.Forms.Label lblProduct;
    private System.Windows.Forms.ComboBox cboProduct;
    private System.Windows.Forms.TextBox txtTitle;
    private System.Windows.Forms.Button btnNewConfig;
    private System.Windows.Forms.Button btnSave;
    private System.Windows.Forms.Button btnPreviewBom;
    private System.Windows.Forms.Button btnRelease;
    private System.Windows.Forms.StatusStrip statusStrip;
    private System.Windows.Forms.ToolStripStatusLabel lblStatus;
}
