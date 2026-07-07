using BomQueryClient.Api;
using BomQueryClient.Api.Services;
using BomQueryClient.Properties;

namespace BomQueryClient.Forms;

public partial class LoginForm : Form
{
    // 颜色方案
    static readonly Color PrimaryBlue = Color.FromArgb(37, 99, 235);
    static readonly Color PrimaryGreen = Color.FromArgb(22, 163, 74);
    static readonly Color BgGray = Color.FromArgb(249, 250, 251);
    static readonly Color BorderLight = Color.FromArgb(229, 231, 235);

    private readonly TextBox _txtServer;
    private readonly TextBox _txtUser;
    private readonly TextBox _txtPwd;
    private readonly TextBox _txtToken;
    private readonly Button _btnLogin;
    private readonly Button _btnToken;
    private readonly Label _lblStatus;
    private readonly Panel _card;
    private bool _useTokenMode;

    public string? Token { get; private set; }
    public string? ServerUrl { get; private set; }

    public LoginForm(Font? baseFont = null)
    {
        if (baseFont != null) Font = baseFont;

        Text = "设备BOM查询系统 — 登录";
        ClientSize = new Size(440, 480);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        BackColor = Color.FromArgb(239, 246, 255); // 浅蓝背景

        // === 居中卡片 ===
        _card = new Panel
        {
            Size = new Size(380, 400),
            Location = new Point(30, 40),
            BackColor = Color.White,
            Padding = new Padding(24),
        };
        _card.Paint += (_, e) =>
        {
            // 圆角阴影效果
            ControlPaint.DrawBorder(e.Graphics, _card.ClientRectangle,
                BorderLight, 1, ButtonBorderStyle.Solid,
                BorderLight, 1, ButtonBorderStyle.Solid,
                BorderLight, 1, ButtonBorderStyle.Solid,
                BorderLight, 1, ButtonBorderStyle.Solid);
        };

        // === 标题 ===
        var lblTitle = new Label
        {
            Text = "🔧 设备BOM查询系统",
            Font = new Font(Font.FontFamily, 16, FontStyle.Bold),
            ForeColor = Color.FromArgb(30, 41, 59),
            AutoSize = false,
            Size = new Size(332, 36),
            TextAlign = ContentAlignment.MiddleCenter,
            Location = new Point(0, 8)
        };

        var lblSub = new Label
        {
            Text = "InvenTree 参数化BOM 客户端",
            Font = new Font(Font.FontFamily, 9),
            ForeColor = Color.FromArgb(148, 163, 184),
            AutoSize = false,
            Size = new Size(332, 20),
            TextAlign = ContentAlignment.MiddleCenter,
            Location = new Point(0, 44)
        };

        // === 服务器地址 ===
        int y = 80;
        AddLabel("服务器地址", 0, ref y);
        _txtServer = new TextBox
        {
            Text = Settings.Default.ServerUrl ?? "http://43.143.130.155:8581",
            Location = new Point(0, y), Size = new Size(332, 30),
            BorderStyle = BorderStyle.FixedSingle,
        };
        y += 36;

        // === 切换登录模式 ===
        var linkToggle = new LinkLabel
        {
            Text = _useTokenMode ? "← 使用账号密码登录" : "使用已有 Token 登录 →",
            Location = new Point(0, y), Size = new Size(332, 24),
            TextAlign = ContentAlignment.MiddleRight,
            LinkColor = PrimaryBlue
        };
        y += 28;
        linkToggle.LinkClicked += (_, _) =>
        {
            _useTokenMode = !_useTokenMode;
            linkToggle.Text = _useTokenMode ? "← 使用账号密码登录" : "使用已有 Token 登录 →";
            ToggleMode();
        };

        // === 账号密码面板 ===
        var pnlPwd = new Panel { Location = new Point(0, y), Size = new Size(332, 160) };
        int py = 0;
        AddLabel("用户名", 0, ref py);
        _txtUser = new TextBox
        {
            Location = new Point(0, py), Size = new Size(332, 30),
            BorderStyle = BorderStyle.FixedSingle, PlaceholderText = "admin"
        };
        py += 36;
        AddLabel("密码", 0, ref py);
        _txtPwd = new TextBox
        {
            Location = new Point(0, py), Size = new Size(332, 30),
            BorderStyle = BorderStyle.FixedSingle, UseSystemPasswordChar = true,
            PlaceholderText = "••••••••"
        };
        py += 42;
        _btnLogin = new Button
        {
            Text = "登 录 获 取 Token",
            Location = new Point(0, py), Size = new Size(332, 38),
            BackColor = PrimaryBlue, ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat, Cursor = Cursors.Hand,
            Font = new Font(Font.FontFamily, 10, FontStyle.Bold)
        };
        _btnLogin.Click += BtnLogin_Click;
        pnlPwd.Controls.AddRange([_txtUser, _txtPwd, _btnLogin]);

        // === Token面板 ===
        var pnlToken = new Panel
        {
            Location = new Point(0, y), Size = new Size(332, 120),
            Visible = false
        };
        int ty = 0;
        AddLabel("API Token", 0, ref ty);
        _txtToken = new TextBox
        {
            Location = new Point(0, ty), Size = new Size(332, 30),
            BorderStyle = BorderStyle.FixedSingle,
            Text = Settings.Default.ApiToken ?? "",
            PlaceholderText = "inv-xxxxxxxx..."
        };
        ty += 42;
        _btnToken = new Button
        {
            Text = "连 接 服 务 器",
            Location = new Point(0, ty), Size = new Size(332, 38),
            BackColor = PrimaryGreen, ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat, Cursor = Cursors.Hand,
            Font = new Font(Font.FontFamily, 10, FontStyle.Bold)
        };
        _btnToken.Click += BtnToken_Click;
        pnlToken.Controls.AddRange([_txtToken, _btnToken]);

        // === 状态栏 ===
        _lblStatus = new Label
        {
            Text = "",
            Location = new Point(0, 350), Size = new Size(332, 30),
            ForeColor = Color.Red, TextAlign = ContentAlignment.MiddleCenter
        };

        _card.Controls.AddRange([lblTitle, lblSub, _txtServer, linkToggle,
            pnlPwd, pnlToken, _lblStatus]);
        Controls.Add(_card);

        // 回车登录
        AcceptButton = _btnLogin;
    }

    void AddLabel(string text, int x, ref int y)
    {
        var lbl = new Label
        {
            Text = text,
            Location = new Point(x, y),
            Size = new Size(332, 18),
            ForeColor = Color.FromArgb(107, 114, 128),
            Font = new Font(Font.FontFamily, 8.5f)
        };
        y += 20;
        _card.Controls.Add(lbl);
    }

    void ToggleMode()
    {
        // 切换面板
        var pnlPwd = _card.Controls.OfType<Panel>().First();
        var pnlToken = _card.Controls.OfType<Panel>().Skip(1).First();
        pnlPwd.Visible = !_useTokenMode;
        pnlToken.Visible = _useTokenMode;
        AcceptButton = _useTokenMode ? _btnToken : _btnLogin;
    }

    async void BtnLogin_Click(object? sender, EventArgs e)
    {
        var server = _txtServer.Text.Trim();

        if (string.IsNullOrEmpty(server))
        { ShowError("请输入服务器地址"); return; }
        if (string.IsNullOrEmpty(_txtUser.Text.Trim()))
        { ShowError("请输入用户名"); return; }
        if (string.IsNullOrEmpty(_txtPwd.Text))
        { ShowError("请输入密码"); return; }

        SetLoading(true, "登录中...");

        try
        {
            var client = new InvenTreeClient(server);
            var resp = await client.PostAsync<LoginResponse>(
                "/api/parametric-bom/client-login/",
                new { username = _txtUser.Text.Trim(), password = _txtPwd.Text });

            var token = resp.Token ?? resp.Key;
            if (string.IsNullOrEmpty(token))
            { ShowError("登录响应中未包含 Token"); return; }

            Token = token;
            ServerUrl = server;

            // 保存
            Settings.Default.ServerUrl = server;
            Settings.Default.ApiToken = token;
            Settings.Default.Save();

            DialogResult = DialogResult.OK;
            Close();
        }
        catch (Exception ex)
        {
            ShowError($"登录失败：{ex.Message}");
        }
        finally { SetLoading(false); }
    }

    async void BtnToken_Click(object? sender, EventArgs e)
    {
        var server = _txtServer.Text.Trim();
        var token = _txtToken.Text.Trim();

        if (string.IsNullOrEmpty(server))
        { ShowError("请输入服务器地址"); return; }
        if (string.IsNullOrEmpty(token))
        { ShowError("请输入 API Token"); return; }

        SetLoading(true, "验证中...");

        try
        {
            var client = new InvenTreeClient(server);
            client.SetToken(token);

            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
            await client.GetAsync<object>("/api/");
            // 成功
            Token = token;
            ServerUrl = server;

            Settings.Default.ServerUrl = server;
            Settings.Default.ApiToken = token;
            Settings.Default.Save();

            DialogResult = DialogResult.OK;
            Close();
        }
        catch (OperationCanceledException)
        {
            ShowError("连接超时，请检查服务器地址");
        }
        catch (Exception ex)
        {
            ShowError($"连接失败：{ex.Message}");
        }
        finally { SetLoading(false); }
    }

    void ShowError(string msg)
    {
        _lblStatus.Text = "⚠ " + msg;
        _lblStatus.ForeColor = Color.Red;
    }

    void SetLoading(bool loading, string? text = null)
    {
        _btnLogin.Enabled = !loading;
        _btnToken.Enabled = !loading;
        _lblStatus.Text = loading ? "⏳ " + (text ?? "") : "";
        _lblStatus.ForeColor = Color.Gray;
        Cursor = loading ? Cursors.WaitCursor : Cursors.Default;
    }
}
