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
        topBar = new Panel();
        lblTitle = new Label();
        panelMain = new Panel();
        rightSplit = new SplitContainer();
        paramPanel = new Panel();
        dgvParams = new DataGridView();
        colParamName = new DataGridViewTextBoxColumn();
        colParamValue = new DataGridViewTextBoxColumn();
        colParamType = new DataGridViewTextBoxColumn();
        colParamDesc = new DataGridViewTextBoxColumn();
        paramHeader = new Label();
        bomPanel = new Panel();
        tvBomPreview = new TreeView();
        bomPreviewHeader = new Label();
        buttonPanel = new Panel();
        btnPreviewBom = new Button();
        btnExportBom = new Button();
        statusStrip = new StatusStrip();
        lblStatus = new ToolStripStatusLabel();
        topBar.SuspendLayout();
        panelMain.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)rightSplit).BeginInit();
        rightSplit.Panel1.SuspendLayout();
        rightSplit.Panel2.SuspendLayout();
        rightSplit.SuspendLayout();
        paramPanel.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)dgvParams).BeginInit();
        bomPanel.SuspendLayout();
        buttonPanel.SuspendLayout();
        statusStrip.SuspendLayout();
        SuspendLayout();
        // 
        // topBar
        // 
        topBar.BackColor = Color.FromArgb(30, 58, 138);
        topBar.Controls.Add(lblTitle);
        topBar.Dock = DockStyle.Top;
        topBar.Location = new Point(0, 0);
        topBar.Margin = new Padding(2, 3, 2, 3);
        topBar.Name = "topBar";
        topBar.Size = new Size(700, 38);
        topBar.TabIndex = 0;
        // 
        // lblTitle
        // 
        lblTitle.AutoSize = true;
        lblTitle.Font = new Font("Microsoft YaHei UI", 11F, FontStyle.Bold);
        lblTitle.ForeColor = Color.White;
        lblTitle.Location = new Point(9, 8);
        lblTitle.Margin = new Padding(2, 0, 2, 0);
        lblTitle.Name = "lblTitle";
        lblTitle.Size = new Size(119, 19);
        lblTitle.TabIndex = 0;
        lblTitle.Text = "⚙ 参数化配置器";
        // 
        // panelMain
        // 
        panelMain.Controls.Add(rightSplit);
        panelMain.Controls.Add(buttonPanel);
        panelMain.Dock = DockStyle.Fill;
        panelMain.Location = new Point(0, 38);
        panelMain.Margin = new Padding(2, 3, 2, 3);
        panelMain.Name = "panelMain";
        panelMain.Size = new Size(700, 696);
        panelMain.TabIndex = 1;
        // 
        // rightSplit
        // 
        rightSplit.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
        rightSplit.FixedPanel = FixedPanel.Panel2;
        rightSplit.Location = new Point(0, 0);
        rightSplit.Margin = new Padding(2, 3, 2, 3);
        rightSplit.Name = "rightSplit";
        rightSplit.Orientation = Orientation.Horizontal;
        // 
        // rightSplit.Panel1
        // 
        rightSplit.Panel1.Controls.Add(paramPanel);
        // 
        // rightSplit.Panel2
        // 
        rightSplit.Panel2.Controls.Add(bomPanel);
        rightSplit.Size = new Size(700, 586);
        rightSplit.SplitterDistance = 273;
        rightSplit.SplitterWidth = 5;
        rightSplit.TabIndex = 0;
        // 
        // paramPanel
        // 
        paramPanel.Controls.Add(dgvParams);
        paramPanel.Controls.Add(paramHeader);
        paramPanel.Dock = DockStyle.Fill;
        paramPanel.Location = new Point(0, 0);
        paramPanel.Margin = new Padding(2, 3, 2, 3);
        paramPanel.Name = "paramPanel";
        paramPanel.Size = new Size(700, 273);
        paramPanel.TabIndex = 0;
        // 
        // dgvParams
        // 
        dgvParams.AllowUserToAddRows = false;
        dgvParams.AllowUserToDeleteRows = false;
        dgvParams.BackgroundColor = Color.White;
        dgvParams.BorderStyle = BorderStyle.None;
        dgvParams.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
        dgvParams.Columns.AddRange(new DataGridViewColumn[] { colParamName, colParamValue, colParamType, colParamDesc });
        dgvParams.Dock = DockStyle.Fill;
        dgvParams.Font = new Font("Microsoft YaHei UI", 9F);
        dgvParams.GridColor = Color.FromArgb(229, 231, 235);
        dgvParams.Location = new Point(0, 30);
        dgvParams.Margin = new Padding(2, 3, 2, 3);
        dgvParams.MultiSelect = false;
        dgvParams.Name = "dgvParams";
        dgvParams.RowHeadersVisible = false;
        dgvParams.RowTemplate.Height = 28;
        dgvParams.SelectionMode = DataGridViewSelectionMode.CellSelect;
        dgvParams.Size = new Size(700, 243);
        dgvParams.TabIndex = 1;
        // 
        // colParamName
        // 
        colParamName.HeaderText = "参数名";
        colParamName.Name = "colParamName";
        colParamName.ReadOnly = true;
        colParamName.Width = 160;
        // 
        // colParamValue
        // 
        colParamValue.HeaderText = "值";
        colParamValue.Name = "colParamValue";
        colParamValue.Width = 200;
        // 
        // colParamType
        // 
        colParamType.HeaderText = "类型";
        colParamType.Name = "colParamType";
        colParamType.ReadOnly = true;
        // 
        // colParamDesc
        // 
        colParamDesc.HeaderText = "描述";
        colParamDesc.Name = "colParamDesc";
        colParamDesc.ReadOnly = true;
        colParamDesc.Width = 180;
        // 
        // paramHeader
        // 
        paramHeader.BackColor = Color.FromArgb(243, 244, 246);
        paramHeader.BorderStyle = BorderStyle.FixedSingle;
        paramHeader.Dock = DockStyle.Top;
        paramHeader.Font = new Font("Microsoft YaHei UI", 9.5F, FontStyle.Bold);
        paramHeader.ForeColor = Color.FromArgb(30, 58, 138);
        paramHeader.Location = new Point(0, 0);
        paramHeader.Margin = new Padding(2, 0, 2, 0);
        paramHeader.Name = "paramHeader";
        paramHeader.Padding = new Padding(8, 0, 0, 0);
        paramHeader.Size = new Size(700, 30);
        paramHeader.TabIndex = 0;
        paramHeader.Text = "📐 参数值设置";
        paramHeader.TextAlign = ContentAlignment.MiddleLeft;
        // 
        // bomPanel
        // 
        bomPanel.Controls.Add(tvBomPreview);
        bomPanel.Controls.Add(bomPreviewHeader);
        bomPanel.Dock = DockStyle.Fill;
        bomPanel.Location = new Point(0, 0);
        bomPanel.Margin = new Padding(2, 3, 2, 3);
        bomPanel.Name = "bomPanel";
        bomPanel.Size = new Size(700, 308);
        bomPanel.TabIndex = 0;
        // 
        // tvBomPreview
        // 
        tvBomPreview.BorderStyle = BorderStyle.None;
        tvBomPreview.Dock = DockStyle.Fill;
        tvBomPreview.Font = new Font("Microsoft YaHei UI", 9F);
        tvBomPreview.FullRowSelect = true;
        tvBomPreview.HideSelection = false;
        tvBomPreview.Location = new Point(0, 30);
        tvBomPreview.Margin = new Padding(2, 3, 2, 3);
        tvBomPreview.Name = "tvBomPreview";
        tvBomPreview.ShowNodeToolTips = true;
        tvBomPreview.Size = new Size(700, 278);
        tvBomPreview.TabIndex = 1;
        // 
        // bomPreviewHeader
        // 
        bomPreviewHeader.BackColor = Color.FromArgb(243, 244, 246);
        bomPreviewHeader.BorderStyle = BorderStyle.FixedSingle;
        bomPreviewHeader.Dock = DockStyle.Top;
        bomPreviewHeader.Font = new Font("Microsoft YaHei UI", 9.5F, FontStyle.Bold);
        bomPreviewHeader.ForeColor = Color.FromArgb(30, 58, 138);
        bomPreviewHeader.Location = new Point(0, 0);
        bomPreviewHeader.Margin = new Padding(2, 0, 2, 0);
        bomPreviewHeader.Name = "bomPreviewHeader";
        bomPreviewHeader.Padding = new Padding(8, 0, 0, 0);
        bomPreviewHeader.Size = new Size(700, 30);
        bomPreviewHeader.TabIndex = 0;
        bomPreviewHeader.Text = "📊 BOM 预览（评估结果）";
        bomPreviewHeader.TextAlign = ContentAlignment.MiddleLeft;
        // 
        // buttonPanel
        // 
        buttonPanel.Controls.Add(btnPreviewBom);
        buttonPanel.Controls.Add(btnExportBom);
        buttonPanel.Dock = DockStyle.Bottom;
        buttonPanel.Location = new Point(0, 647);
        buttonPanel.Margin = new Padding(2, 3, 2, 3);
        buttonPanel.Name = "buttonPanel";
        buttonPanel.Size = new Size(700, 49);
        buttonPanel.TabIndex = 1;
        // 
        // btnPreviewBom
        // 
        btnPreviewBom.Anchor = AnchorStyles.Right;
        btnPreviewBom.BackColor = Color.FromArgb(245, 158, 11);
        btnPreviewBom.FlatAppearance.BorderSize = 0;
        btnPreviewBom.FlatStyle = FlatStyle.Flat;
        btnPreviewBom.Font = new Font("Microsoft YaHei UI", 10F, FontStyle.Bold);
        btnPreviewBom.ForeColor = Color.White;
        btnPreviewBom.Location = new Point(386, 3);
        btnPreviewBom.Margin = new Padding(2, 3, 2, 3);
        btnPreviewBom.Name = "btnPreviewBom";
        btnPreviewBom.Size = new Size(93, 34);
        btnPreviewBom.TabIndex = 1;
        btnPreviewBom.Text = "📊 预览 BOM";
        btnPreviewBom.UseVisualStyleBackColor = false;
        // 
        // btnExportBom
        // 
        btnExportBom.Anchor = AnchorStyles.Right;
        btnExportBom.BackColor = Color.FromArgb(16, 185, 129);
        btnExportBom.FlatAppearance.BorderSize = 0;
        btnExportBom.FlatStyle = FlatStyle.Flat;
        btnExportBom.Font = new Font("Microsoft YaHei UI", 10F, FontStyle.Bold);
        btnExportBom.ForeColor = Color.White;
        btnExportBom.Location = new Point(573, 3);
        btnExportBom.Margin = new Padding(2, 3, 2, 3);
        btnExportBom.Name = "btnExportBom";
        btnExportBom.Size = new Size(93, 34);
        btnExportBom.TabIndex = 2;
        btnExportBom.Text = "📥 导出 Excel";
        btnExportBom.UseVisualStyleBackColor = false;
        // 
        // statusStrip
        // 
        statusStrip.Items.AddRange(new ToolStripItem[] { lblStatus });
        statusStrip.Location = new Point(0, 734);
        statusStrip.Name = "statusStrip";
        statusStrip.Padding = new Padding(1, 0, 11, 0);
        statusStrip.Size = new Size(700, 22);
        statusStrip.SizingGrip = false;
        statusStrip.TabIndex = 2;
        // 
        // lblStatus
        // 
        lblStatus.Font = new Font("Microsoft YaHei UI", 9F);
        lblStatus.Name = "lblStatus";
        lblStatus.Size = new Size(32, 17);
        lblStatus.Text = "就绪";
        // 
        // ConfiguratorForm
        // 
        AutoScaleDimensions = new SizeF(7F, 17F);
        AutoScaleMode = AutoScaleMode.Font;
        ClientSize = new Size(700, 756);
        Controls.Add(panelMain);
        Controls.Add(topBar);
        Controls.Add(statusStrip);
        Font = new Font("Microsoft YaHei UI", 9F);
        Margin = new Padding(2, 3, 2, 3);
        MinimumSize = new Size(548, 474);
        Name = "ConfiguratorForm";
        StartPosition = FormStartPosition.CenterScreen;
        Text = "参数化配置器";
        topBar.ResumeLayout(false);
        topBar.PerformLayout();
        panelMain.ResumeLayout(false);
        rightSplit.Panel1.ResumeLayout(false);
        rightSplit.Panel2.ResumeLayout(false);
        ((System.ComponentModel.ISupportInitialize)rightSplit).EndInit();
        rightSplit.ResumeLayout(false);
        paramPanel.ResumeLayout(false);
        ((System.ComponentModel.ISupportInitialize)dgvParams).EndInit();
        bomPanel.ResumeLayout(false);
        buttonPanel.ResumeLayout(false);
        statusStrip.ResumeLayout(false);
        statusStrip.PerformLayout();
        ResumeLayout(false);
        PerformLayout();
    }

    #endregion

    private System.Windows.Forms.Panel topBar;
    private System.Windows.Forms.Label lblTitle;
    private System.Windows.Forms.Panel panelMain;
    private System.Windows.Forms.SplitContainer rightSplit;
    private System.Windows.Forms.Panel paramPanel;
    private System.Windows.Forms.Label paramHeader;
    private System.Windows.Forms.DataGridView dgvParams;
    private System.Windows.Forms.DataGridViewTextBoxColumn colParamName;
    private System.Windows.Forms.DataGridViewTextBoxColumn colParamValue;
    private System.Windows.Forms.DataGridViewTextBoxColumn colParamType;
    private System.Windows.Forms.DataGridViewTextBoxColumn colParamDesc;
    private System.Windows.Forms.Panel bomPanel;
    private System.Windows.Forms.Label bomPreviewHeader;
    private System.Windows.Forms.TreeView tvBomPreview;
    private System.Windows.Forms.Button btnPreviewBom;
    private System.Windows.Forms.Button btnExportBom;
    private System.Windows.Forms.Panel buttonPanel;
    private System.Windows.Forms.StatusStrip statusStrip;
    private System.Windows.Forms.ToolStripStatusLabel lblStatus;
}
