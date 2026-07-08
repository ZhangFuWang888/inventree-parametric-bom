namespace BomQueryClient.Forms;

partial class LoginForm
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
        tableLayoutMain = new TableLayoutPanel();
        lblTitle = new Label();
        lblSubtitle = new Label();
        lblServer = new Label();
        txtServer = new TextBox();
        pnlPassword = new Panel();
        lblUsername = new Label();
        txtUsername = new TextBox();
        lblPassword = new Label();
        txtPassword = new TextBox();
        chkRememberMe = new CheckBox();
        btnLogin = new Button();
        pnlToken = new Panel();
        lblToken = new Label();
        txtToken = new TextBox();
        btnConnect = new Button();
        linkUseToken = new LinkLabel();
        lblStatus = new Label();
        tableLayoutMain.SuspendLayout();
        pnlPassword.SuspendLayout();
        pnlToken.SuspendLayout();
        SuspendLayout();
        // 
        // tableLayoutMain
        // 
        tableLayoutMain.ColumnCount = 1;
        tableLayoutMain.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));
        tableLayoutMain.Controls.Add(lblTitle, 0, 0);
        tableLayoutMain.Controls.Add(lblSubtitle, 0, 1);
        tableLayoutMain.Controls.Add(lblServer, 0, 2);
        tableLayoutMain.Controls.Add(txtServer, 0, 3);
        tableLayoutMain.Controls.Add(pnlPassword, 0, 4);
        tableLayoutMain.Controls.Add(pnlToken, 0, 5);
        tableLayoutMain.Controls.Add(linkUseToken, 0, 6);
        tableLayoutMain.Controls.Add(lblStatus, 0, 7);
        tableLayoutMain.Dock = DockStyle.Fill;
        tableLayoutMain.Location = new Point(0, 0);
        tableLayoutMain.Margin = new Padding(2, 3, 2, 3);
        tableLayoutMain.Name = "tableLayoutMain";
        tableLayoutMain.RowCount = 8;
        tableLayoutMain.RowStyles.Add(new RowStyle(SizeType.Absolute, 30F));
        tableLayoutMain.RowStyles.Add(new RowStyle(SizeType.Absolute, 19F));
        tableLayoutMain.RowStyles.Add(new RowStyle(SizeType.Absolute, 17F));
        tableLayoutMain.RowStyles.Add(new RowStyle(SizeType.Absolute, 26F));
        tableLayoutMain.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
        tableLayoutMain.RowStyles.Add(new RowStyle(SizeType.Absolute, 85F));
        tableLayoutMain.RowStyles.Add(new RowStyle(SizeType.Absolute, 21F));
        tableLayoutMain.RowStyles.Add(new RowStyle(SizeType.Absolute, 23F));
        tableLayoutMain.Size = new Size(327, 408);
        tableLayoutMain.TabIndex = 0;
        // 
        // lblTitle
        // 
        lblTitle.Dock = DockStyle.Fill;
        lblTitle.Font = new Font("Microsoft YaHei UI", 14F, FontStyle.Bold);
        lblTitle.Location = new Point(2, 0);
        lblTitle.Margin = new Padding(2, 0, 2, 0);
        lblTitle.Name = "lblTitle";
        lblTitle.Size = new Size(323, 30);
        lblTitle.TabIndex = 0;
        lblTitle.Text = "设备 BOM 查询系统";
        lblTitle.TextAlign = ContentAlignment.MiddleCenter;
        // 
        // lblSubtitle
        // 
        lblSubtitle.Dock = DockStyle.Fill;
        lblSubtitle.Font = new Font("Microsoft YaHei UI", 9F);
        lblSubtitle.ForeColor = SystemColors.GrayText;
        lblSubtitle.Location = new Point(2, 30);
        lblSubtitle.Margin = new Padding(2, 0, 2, 0);
        lblSubtitle.Name = "lblSubtitle";
        lblSubtitle.Size = new Size(323, 19);
        lblSubtitle.TabIndex = 1;
        lblSubtitle.Text = "InvenTree 参数化 BOM 客户端";
        lblSubtitle.TextAlign = ContentAlignment.MiddleCenter;
        // 
        // lblServer
        // 
        lblServer.AutoSize = true;
        lblServer.Location = new Point(2, 49);
        lblServer.Margin = new Padding(2, 0, 2, 0);
        lblServer.Name = "lblServer";
        lblServer.Size = new Size(80, 17);
        lblServer.TabIndex = 2;
        lblServer.Text = "服务器地址：";
        // 
        // txtServer
        // 
        txtServer.Dock = DockStyle.Fill;
        txtServer.Location = new Point(2, 69);
        txtServer.Margin = new Padding(2, 3, 2, 3);
        txtServer.Name = "txtServer";
        txtServer.Size = new Size(323, 23);
        txtServer.TabIndex = 0;
        // 
        // pnlPassword
        // 
        pnlPassword.Controls.Add(lblUsername);
        pnlPassword.Controls.Add(txtUsername);
        pnlPassword.Controls.Add(lblPassword);
        pnlPassword.Controls.Add(txtPassword);
        pnlPassword.Controls.Add(chkRememberMe);
        pnlPassword.Controls.Add(btnLogin);
        pnlPassword.Dock = DockStyle.Fill;
        pnlPassword.Location = new Point(0, 92);
        pnlPassword.Margin = new Padding(0);
        pnlPassword.Name = "pnlPassword";
        pnlPassword.Size = new Size(327, 187);
        pnlPassword.TabIndex = 4;
        // 
        // lblUsername
        // 
        lblUsername.AutoSize = true;
        lblUsername.Location = new Point(2, 0);
        lblUsername.Margin = new Padding(2, 0, 2, 0);
        lblUsername.Name = "lblUsername";
        lblUsername.Size = new Size(56, 17);
        lblUsername.TabIndex = 0;
        lblUsername.Text = "用户名：";
        // 
        // txtUsername
        // 
        txtUsername.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
        txtUsername.Location = new Point(2, 20);
        txtUsername.Margin = new Padding(2, 3, 2, 3);
        txtUsername.Name = "txtUsername";
        txtUsername.PlaceholderText = "请输入用户名";
        txtUsername.Size = new Size(323, 23);
        txtUsername.TabIndex = 1;
        // 
        // lblPassword
        // 
        lblPassword.AutoSize = true;
        lblPassword.Location = new Point(2, 49);
        lblPassword.Margin = new Padding(2, 0, 2, 0);
        lblPassword.Name = "lblPassword";
        lblPassword.Size = new Size(44, 17);
        lblPassword.TabIndex = 2;
        lblPassword.Text = "密码：";
        // 
        // txtPassword
        // 
        txtPassword.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
        txtPassword.Location = new Point(2, 69);
        txtPassword.Margin = new Padding(2, 3, 2, 3);
        txtPassword.Name = "txtPassword";
        txtPassword.PlaceholderText = "请输入密码";
        txtPassword.Size = new Size(323, 23);
        txtPassword.TabIndex = 3;
        txtPassword.UseSystemPasswordChar = true;
        // 
        // chkRememberMe
        // 
        chkRememberMe.AutoSize = true;
        chkRememberMe.Location = new Point(2, 98);
        chkRememberMe.Margin = new Padding(2, 3, 2, 3);
        chkRememberMe.Name = "chkRememberMe";
        chkRememberMe.Size = new Size(87, 21);
        chkRememberMe.TabIndex = 4;
        chkRememberMe.Text = "记住用户名";
        // 
        // btnLogin
        // 
        btnLogin.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
        btnLogin.Location = new Point(2, 124);
        btnLogin.Margin = new Padding(2, 3, 2, 3);
        btnLogin.Name = "btnLogin";
        btnLogin.Size = new Size(322, 30);
        btnLogin.TabIndex = 5;
        btnLogin.Text = "登 录";
        btnLogin.UseVisualStyleBackColor = true;
        // 
        // pnlToken
        // 
        pnlToken.Controls.Add(lblToken);
        pnlToken.Controls.Add(txtToken);
        pnlToken.Controls.Add(btnConnect);
        pnlToken.Dock = DockStyle.Fill;
        pnlToken.Location = new Point(0, 279);
        pnlToken.Margin = new Padding(0);
        pnlToken.Name = "pnlToken";
        pnlToken.Size = new Size(327, 85);
        pnlToken.TabIndex = 5;
        pnlToken.Visible = false;
        // 
        // lblToken
        // 
        lblToken.AutoSize = true;
        lblToken.Location = new Point(2, 4);
        lblToken.Margin = new Padding(2, 0, 2, 0);
        lblToken.Name = "lblToken";
        lblToken.Size = new Size(79, 17);
        lblToken.TabIndex = 0;
        lblToken.Text = "API Token：";
        // 
        // txtToken
        // 
        txtToken.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
        txtToken.Location = new Point(2, 24);
        txtToken.Margin = new Padding(2, 3, 2, 3);
        txtToken.Name = "txtToken";
        txtToken.PlaceholderText = "inv-xxxxxxxx...";
        txtToken.Size = new Size(323, 23);
        txtToken.TabIndex = 1;
        // 
        // btnConnect
        // 
        btnConnect.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
        btnConnect.Location = new Point(2, 52);
        btnConnect.Margin = new Padding(2, 3, 2, 3);
        btnConnect.Name = "btnConnect";
        btnConnect.Size = new Size(322, 30);
        btnConnect.TabIndex = 2;
        btnConnect.Text = "连 接 服 务 器";
        btnConnect.UseVisualStyleBackColor = true;
        // 
        // linkUseToken
        // 
        linkUseToken.Dock = DockStyle.Fill;
        linkUseToken.LinkBehavior = LinkBehavior.HoverUnderline;
        linkUseToken.Location = new Point(0, 364);
        linkUseToken.Margin = new Padding(0);
        linkUseToken.Name = "linkUseToken";
        linkUseToken.Size = new Size(327, 21);
        linkUseToken.TabIndex = 6;
        linkUseToken.TabStop = true;
        linkUseToken.Text = "使用 Token 登录";
        linkUseToken.TextAlign = ContentAlignment.MiddleRight;
        // 
        // lblStatus
        // 
        lblStatus.Dock = DockStyle.Fill;
        lblStatus.ForeColor = Color.FromArgb(220, 38, 38);
        lblStatus.Location = new Point(2, 388);
        lblStatus.Margin = new Padding(2, 3, 2, 3);
        lblStatus.Name = "lblStatus";
        lblStatus.Size = new Size(323, 17);
        lblStatus.TabIndex = 7;
        lblStatus.TextAlign = ContentAlignment.MiddleCenter;
        // 
        // LoginForm
        // 
        AutoScaleDimensions = new SizeF(7F, 17F);
        AutoScaleMode = AutoScaleMode.Font;
        ClientSize = new Size(327, 408);
        Controls.Add(tableLayoutMain);
        Font = new Font("Microsoft YaHei UI", 9F);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        Margin = new Padding(2, 3, 2, 3);
        MaximizeBox = false;
        MinimizeBox = false;
        Name = "LoginForm";
        StartPosition = FormStartPosition.CenterScreen;
        Text = "设备 BOM 查询系统 — 登录";
        tableLayoutMain.ResumeLayout(false);
        tableLayoutMain.PerformLayout();
        pnlPassword.ResumeLayout(false);
        pnlPassword.PerformLayout();
        pnlToken.ResumeLayout(false);
        pnlToken.PerformLayout();
        ResumeLayout(false);
    }

    #endregion

    private System.Windows.Forms.TableLayoutPanel tableLayoutMain;
    private System.Windows.Forms.Label lblTitle;
    private System.Windows.Forms.Label lblSubtitle;
    private System.Windows.Forms.Label lblServer;
    private System.Windows.Forms.TextBox txtServer;
    private System.Windows.Forms.Panel pnlPassword;
    private System.Windows.Forms.Label lblUsername;
    private System.Windows.Forms.TextBox txtUsername;
    private System.Windows.Forms.Label lblPassword;
    private System.Windows.Forms.TextBox txtPassword;
    private System.Windows.Forms.CheckBox chkRememberMe;
    private System.Windows.Forms.Button btnLogin;
    private System.Windows.Forms.LinkLabel linkUseToken;
    private System.Windows.Forms.Panel pnlToken;
    private System.Windows.Forms.Label lblToken;
    private System.Windows.Forms.TextBox txtToken;
    private System.Windows.Forms.Button btnConnect;
    private System.Windows.Forms.Label lblStatus;
}