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
        this.panelMain = new System.Windows.Forms.Panel();
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
        this.btnPreviewBom = new System.Windows.Forms.Button();
        this.btnExportBom = new System.Windows.Forms.Button();
        this.statusStrip = new System.Windows.Forms.StatusStrip();
        this.lblStatus = new System.Windows.Forms.ToolStripStatusLabel();
        this.topBar.SuspendLayout();
        this.panelMain.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)(this.rightSplit)).BeginInit();
        this.rightSplit.Panel1.SuspendLayout();
        this.rightSplit.Panel2.SuspendLayout();
        this.rightSplit.SuspendLayout();
        this.paramPanel.SuspendLayout();
        ((System.ComponentModel.ISupportInitialize)(this.dgvParams)).BeginInit();
        this.bomPanel.SuspendLayout();
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
        this.topBar.Size = new System.Drawing.Size(900, 40);
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
        // panelMain
        //
        this.panelMain.Controls.Add(this.rightSplit);
        this.panelMain.Controls.Add(this.btnPreviewBom);
        this.panelMain.Dock = System.Windows.Forms.DockStyle.Fill;
        this.panelMain.Location = new System.Drawing.Point(0, 40);
        this.panelMain.Name = "panelMain";
        this.panelMain.Size = new System.Drawing.Size(900, 734);
        this.panelMain.TabIndex = 1;
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
        this.rightSplit.Panel1.Controls.Add(this.paramPanel);
        //
        // rightSplit.Panel2
        //
        this.rightSplit.Panel2.Controls.Add(this.bomPanel);
        this.rightSplit.Size = new System.Drawing.Size(900, 660);
        this.rightSplit.SplitterDistance = 320;
        this.rightSplit.SplitterWidth = 5;
        this.rightSplit.TabIndex = 0;
        //
        // paramPanel
        //
        this.paramPanel.Controls.Add(this.dgvParams);
        this.paramPanel.Controls.Add(this.paramHeader);
        this.paramPanel.Dock = System.Windows.Forms.DockStyle.Fill;
        this.paramPanel.Location = new System.Drawing.Point(0, 0);
        this.paramPanel.Name = "paramPanel";
        this.paramPanel.Size = new System.Drawing.Size(900, 320);
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
        this.paramHeader.Size = new System.Drawing.Size(900, 32);
        this.paramHeader.TabIndex = 0;
        this.paramHeader.Text = "📐 参数值设置";
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
        this.dgvParams.Size = new System.Drawing.Size(900, 288);
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
        this.bomPanel.Size = new System.Drawing.Size(900, 335);
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
        this.bomPreviewHeader.Size = new System.Drawing.Size(900, 32);
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
        this.tvBomPreview.Size = new System.Drawing.Size(900, 303);
        this.tvBomPreview.TabIndex = 1;
        //
        // btnPreviewBom
        //
        this.btnPreviewBom.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
        this.btnPreviewBom.BackColor = Color.FromArgb(245, 158, 11);
        this.btnPreviewBom.FlatAppearance.BorderSize = 0;
        this.btnPreviewBom.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
        this.btnPreviewBom.Font = new System.Drawing.Font("Microsoft YaHei UI", 10F, System.Drawing.FontStyle.Bold);
        this.btnPreviewBom.ForeColor = Color.White;
        this.btnPreviewBom.Location = new System.Drawing.Point(618, 678);
        this.btnPreviewBom.Name = "btnPreviewBom";
        this.btnPreviewBom.Size = new System.Drawing.Size(120, 36);
        this.btnPreviewBom.TabIndex = 1;
        this.btnPreviewBom.Text = "📊 预览 BOM";
        this.btnPreviewBom.UseVisualStyleBackColor = false;
        //
        // btnExportBom
        //
        this.btnExportBom.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
        this.btnExportBom.BackColor = Color.FromArgb(16, 185, 129);
        this.btnExportBom.FlatAppearance.BorderSize = 0;
        this.btnExportBom.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
        this.btnExportBom.Font = new System.Drawing.Font("Microsoft YaHei UI", 10F, System.Drawing.FontStyle.Bold);
        this.btnExportBom.ForeColor = Color.White;
        this.btnExportBom.Location = new System.Drawing.Point(744, 678);
        this.btnExportBom.Name = "btnExportBom";
        this.btnExportBom.Size = new System.Drawing.Size(120, 36);
        this.btnExportBom.TabIndex = 2;
        this.btnExportBom.Text = "📥 导出 Excel";
        this.btnExportBom.UseVisualStyleBackColor = false;
        //
        // statusStrip
        //
        this.statusStrip.Items.AddRange(new System.Windows.Forms.ToolStripItem[] { this.lblStatus });
        this.statusStrip.Location = new System.Drawing.Point(0, 774);
        this.statusStrip.Name = "statusStrip";
        this.statusStrip.Size = new System.Drawing.Size(900, 26);
        this.statusStrip.SizingGrip = false;
        this.statusStrip.TabIndex = 2;
        //
        // lblStatus
        //
        this.lblStatus.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.lblStatus.Name = "lblStatus";
        this.lblStatus.Size = new System.Drawing.Size(68, 20);
        this.lblStatus.Text = "就绪";
        //
        // ConfiguratorForm
        //
        this.AutoScaleDimensions = new System.Drawing.SizeF(9F, 18F);
        this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
        this.ClientSize = new System.Drawing.Size(900, 800);
        this.Controls.Add(this.panelMain);
        this.Controls.Add(this.topBar);
        this.Controls.Add(this.statusStrip);
        this.Font = new System.Drawing.Font("Microsoft YaHei UI", 9F);
        this.MinimumSize = new System.Drawing.Size(700, 500);
        this.Name = "ConfiguratorForm";
        this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
        this.Text = "参数化配置器";
        this.topBar.ResumeLayout(false);
        this.topBar.PerformLayout();
        this.panelMain.ResumeLayout(false);
        this.rightSplit.Panel1.ResumeLayout(false);
        this.rightSplit.Panel2.ResumeLayout(false);
        ((System.ComponentModel.ISupportInitialize)(this.rightSplit)).EndInit();
        this.rightSplit.ResumeLayout(false);
        this.paramPanel.ResumeLayout(false);
        ((System.ComponentModel.ISupportInitialize)(this.dgvParams)).EndInit();
        this.bomPanel.ResumeLayout(false);
        this.statusStrip.ResumeLayout(false);
        this.statusStrip.PerformLayout();
        this.ResumeLayout(false);
        this.PerformLayout();
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
    private System.Windows.Forms.Panel bomPanel;
    private System.Windows.Forms.Label bomPreviewHeader;
    private System.Windows.Forms.TreeView tvBomPreview;
    private System.Windows.Forms.Button btnPreviewBom;
    private System.Windows.Forms.Button btnExportBom;
    private System.Windows.Forms.StatusStrip statusStrip;
    private System.Windows.Forms.ToolStripStatusLabel lblStatus;
}
