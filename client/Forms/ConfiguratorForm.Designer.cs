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
        dgvBomPreview = new DataGridView();
        colBomCol1 = new DataGridViewTextBoxColumn();
        colBomCol2 = new DataGridViewTextBoxColumn();
        colBomCol3 = new DataGridViewTextBoxColumn();
        colBomCol4 = new DataGridViewTextBoxColumn();
        colBomCol5 = new DataGridViewTextBoxColumn();
        colBomCol6 = new DataGridViewTextBoxColumn();
        colBomCol7 = new DataGridViewTextBoxColumn();
        colBomCol8 = new DataGridViewTextBoxColumn();
        colBomCol9 = new DataGridViewTextBoxColumn();
        colBomCol10 = new DataGridViewTextBoxColumn();
        colBomCol11 = new DataGridViewTextBoxColumn();
        colBomCol12 = new DataGridViewTextBoxColumn();
        colBomCol13 = new DataGridViewTextBoxColumn();
        colBomCol14 = new DataGridViewTextBoxColumn();
        colBomCol15 = new DataGridViewTextBoxColumn();
        colBomCol16 = new DataGridViewTextBoxColumn();
        colBomCol17 = new DataGridViewTextBoxColumn();
        colBomCol18 = new DataGridViewTextBoxColumn();
        colBomCol19 = new DataGridViewTextBoxColumn();
        colBomCol20 = new DataGridViewTextBoxColumn();
        colBomCol21 = new DataGridViewTextBoxColumn();
        colBomCol22 = new DataGridViewTextBoxColumn();
        colBomCol23 = new DataGridViewTextBoxColumn();
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
        bomPanel.Controls.Add(dgvBomPreview);
        bomPanel.Controls.Add(bomPreviewHeader);
        bomPanel.Dock = DockStyle.Fill;
        bomPanel.Location = new Point(0, 0);
        bomPanel.Margin = new Padding(2, 3, 2, 3);
        bomPanel.Name = "bomPanel";
        bomPanel.Size = new Size(700, 308);
        bomPanel.TabIndex = 0;
        // 
        // dgvBomPreview
        // 
        dgvBomPreview.AllowUserToAddRows = false;
        dgvBomPreview.AllowUserToDeleteRows = false;
        dgvBomPreview.BackgroundColor = Color.White;
        dgvBomPreview.BorderStyle = BorderStyle.None;
        dgvBomPreview.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize;
        dgvBomPreview.Columns.AddRange(new DataGridViewColumn[] { colBomCol1, colBomCol2, colBomCol3, colBomCol4, colBomCol5, colBomCol6, colBomCol7, colBomCol8, colBomCol9, colBomCol10, colBomCol11, colBomCol12, colBomCol13, colBomCol14, colBomCol15, colBomCol16, colBomCol17, colBomCol18, colBomCol19, colBomCol20, colBomCol21, colBomCol22, colBomCol23 });
        dgvBomPreview.Dock = DockStyle.Fill;
        dgvBomPreview.Font = new Font("Microsoft YaHei UI", 9F);
        dgvBomPreview.GridColor = Color.FromArgb(229, 231, 235);
        dgvBomPreview.Location = new Point(0, 30);
        dgvBomPreview.Margin = new Padding(2, 3, 2, 3);
        dgvBomPreview.MultiSelect = false;
        dgvBomPreview.Name = "dgvBomPreview";
        dgvBomPreview.RowHeadersVisible = false;
        dgvBomPreview.RowTemplate.Height = 26;
        dgvBomPreview.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
        dgvBomPreview.Size = new Size(700, 278);
        dgvBomPreview.TabIndex = 1;
        // 
        // colBomCol1
        // 
        colBomCol1.HeaderText = "序号";
        colBomCol1.Name = "colBomCol1";
        colBomCol1.ReadOnly = true;
        colBomCol1.Width = 36;
        colBomCol1.DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
        // 
        // colBomCol2
        // 
        colBomCol2.HeaderText = "设备（大类）";
        colBomCol2.Name = "colBomCol2";
        colBomCol2.ReadOnly = true;
        colBomCol2.Width = 70;
        // 
        // colBomCol3
        // 
        colBomCol3.HeaderText = "部装";
        colBomCol3.Name = "colBomCol3";
        colBomCol3.ReadOnly = true;
        colBomCol3.Width = 70;
        // 
        // colBomCol4
        // 
        colBomCol4.HeaderText = "规格型号";
        colBomCol4.Name = "colBomCol4";
        colBomCol4.ReadOnly = true;
        colBomCol4.Width = 90;
        // 
        // colBomCol5
        // 
        colBomCol5.HeaderText = "品名";
        colBomCol5.Name = "colBomCol5";
        colBomCol5.ReadOnly = true;
        colBomCol5.Width = 130;
        // 
        // colBomCol6
        // 
        colBomCol6.HeaderText = "品牌";
        colBomCol6.Name = "colBomCol6";
        colBomCol6.ReadOnly = true;
        colBomCol6.Width = 50;
        // 
        // colBomCol7
        // 
        colBomCol7.HeaderText = "单位";
        colBomCol7.Name = "colBomCol7";
        colBomCol7.ReadOnly = true;
        colBomCol7.Width = 40;
        // 
        // colBomCol8
        // 
        colBomCol8.HeaderText = "应需数量";
        colBomCol8.Name = "colBomCol8";
        colBomCol8.ReadOnly = true;
        colBomCol8.Width = 60;
        colBomCol8.DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
        // 
        // colBomCol9
        // 
        colBomCol9.HeaderText = "预期到货";
        colBomCol9.Name = "colBomCol9";
        colBomCol9.ReadOnly = true;
        colBomCol9.Width = 60;
        // 
        // colBomCol10
        // 
        colBomCol10.HeaderText = "类别";
        colBomCol10.Name = "colBomCol10";
        colBomCol10.ReadOnly = true;
        colBomCol10.Width = 40;
        // 
        // colBomCol11
        // 
        colBomCol11.HeaderText = "材质（牌号）";
        colBomCol11.Name = "colBomCol11";
        colBomCol11.ReadOnly = true;
        colBomCol11.Width = 70;
        // 
        // colBomCol12
        // 
        colBomCol12.HeaderText = "表面处理方式";
        colBomCol12.Name = "colBomCol12";
        colBomCol12.ReadOnly = true;
        colBomCol12.Width = 70;
        // 
        // colBomCol13
        // 
        colBomCol13.HeaderText = "处理颜色";
        colBomCol13.Name = "colBomCol13";
        colBomCol13.ReadOnly = true;
        colBomCol13.Width = 60;
        // 
        // colBomCol14
        // 
        colBomCol14.HeaderText = "重量";
        colBomCol14.Name = "colBomCol14";
        colBomCol14.ReadOnly = true;
        colBomCol14.Width = 50;
        // 
        // colBomCol15
        // 
        colBomCol15.HeaderText = "备注";
        colBomCol15.Name = "colBomCol15";
        colBomCol15.ReadOnly = true;
        colBomCol15.Width = 100;
        // 
        // colBomCol16
        // 
        colBomCol16.HeaderText = "采购员";
        colBomCol16.Name = "colBomCol16";
        colBomCol16.ReadOnly = true;
        colBomCol16.Width = 50;
        // 
        // colBomCol17
        // 
        colBomCol17.HeaderText = "入库去向";
        colBomCol17.Name = "colBomCol17";
        colBomCol17.ReadOnly = true;
        colBomCol17.Width = 60;
        // 
        // colBomCol18
        // 
        colBomCol18.HeaderText = "制购类别";
        colBomCol18.Name = "colBomCol18";
        colBomCol18.ReadOnly = true;
        colBomCol18.Width = 60;
        // 
        // colBomCol19
        // 
        colBomCol19.HeaderText = "申请理由";
        colBomCol19.Name = "colBomCol19";
        colBomCol19.ReadOnly = true;
        colBomCol19.Width = 80;
        // 
        // colBomCol20
        // 
        colBomCol20.HeaderText = "附图";
        colBomCol20.Name = "colBomCol20";
        colBomCol20.ReadOnly = true;
        colBomCol20.Width = 40;
        // 
        // colBomCol21
        // 
        colBomCol21.HeaderText = "总数量";
        colBomCol21.Name = "colBomCol21";
        colBomCol21.ReadOnly = true;
        colBomCol21.Width = 50;
        colBomCol21.DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
        // 
        // colBomCol22
        // 
        colBomCol22.HeaderText = "问题环节";
        colBomCol22.Name = "colBomCol22";
        colBomCol22.ReadOnly = true;
        colBomCol22.Width = 60;
        // 
        // colBomCol23
        // 
        colBomCol23.HeaderText = "技改原因分类";
        colBomCol23.Name = "colBomCol23";
        colBomCol23.ReadOnly = true;
        colBomCol23.Width = 80;
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
    private System.Windows.Forms.DataGridView dgvBomPreview;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol1;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol2;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol3;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol4;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol5;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol6;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol7;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol8;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol9;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol10;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol11;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol12;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol13;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol14;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol15;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol16;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol17;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol18;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol19;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol20;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol21;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol22;
    private System.Windows.Forms.DataGridViewTextBoxColumn colBomCol23;
    private System.Windows.Forms.Button btnPreviewBom;
    private System.Windows.Forms.Button btnExportBom;
    private System.Windows.Forms.Panel buttonPanel;
    private System.Windows.Forms.StatusStrip statusStrip;
    private System.Windows.Forms.ToolStripStatusLabel lblStatus;
}
