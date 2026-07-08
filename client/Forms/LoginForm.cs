using BomQueryClient.Api;
using BomQueryClient.Api.Models;
using BomQueryClient.Properties;

namespace BomQueryClient.Forms;

public partial class LoginForm : Form
{
    private const string DefaultServer = "http://43.143.130.155:8581";

    private bool _useTokenMode;

    public string? Token { get; private set; }
    public string? ServerUrl { get; private set; }

    public LoginForm(Font? baseFont = null)
    {
        if (baseFont != null) Font = baseFont;

        InitializeComponent();

        // 从设置还原默认值
        var settings = Settings.Default;
        txtServer.Text = settings.ServerUrl ?? DefaultServer;
        if (settings.RememberMe && !string.IsNullOrEmpty(settings.SavedUsername))
            txtUsername.Text = settings.SavedUsername;
        chkRememberMe.Checked = settings.RememberMe;
        if (!string.IsNullOrEmpty(settings.ApiToken))
            txtToken.Text = settings.ApiToken;

        btnLogin.Click += BtnLogin_Click;
        btnConnect.Click += BtnConnect_Click;
        linkUseToken.LinkClicked += (_, _) => ToggleMode();

        AcceptButton = btnLogin;
    }

    private void ToggleMode()
    {
        _useTokenMode = !_useTokenMode;
        pnlPassword.Visible = !_useTokenMode;
        pnlToken.Visible = _useTokenMode;
        linkUseToken.Text = _useTokenMode ? "使用账号密码登录" : "使用 Token 登录";
        AcceptButton = _useTokenMode ? btnConnect : btnLogin;
    }

    private async void BtnLogin_Click(object? sender, EventArgs e)
    {
        var server = txtServer.Text.Trim();

        if (string.IsNullOrEmpty(server)) { ShowError("请输入服务器地址"); return; }
        if (string.IsNullOrEmpty(txtUsername.Text.Trim())) { ShowError("请输入用户名"); return; }
        if (string.IsNullOrEmpty(txtPassword.Text)) { ShowError("请输入密码"); return; }

        SetLoading(true, "登录中...");

        try
        {
            var client = new InvenTreeClient(server);
            var resp = await client.PostAsync<LoginResponse>(
                "/api/parametric-bom/client-login/",
                new { username = txtUsername.Text.Trim(), password = txtPassword.Text });

            var token = resp.Token ?? resp.Key;
            if (string.IsNullOrEmpty(token))
            { ShowError("登录响应中未包含 Token"); return; }

            Token = token;
            ServerUrl = server;

            // 保存
            Settings.Default.ServerUrl = server;
            Settings.Default.ApiToken = token;
            Settings.Default.RememberMe = chkRememberMe.Checked;
            Settings.Default.SavedUsername = chkRememberMe.Checked ? txtUsername.Text.Trim() : null;
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

    private async void BtnConnect_Click(object? sender, EventArgs e)
    {
        var server = txtServer.Text.Trim();
        var token = txtToken.Text.Trim();

        if (string.IsNullOrEmpty(server)) { ShowError("请输入服务器地址"); return; }
        if (string.IsNullOrEmpty(token)) { ShowError("请输入 API Token"); return; }

        SetLoading(true, "验证中...");

        try
        {
            var client = new InvenTreeClient(server);
            client.SetToken(token);

            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
            await client.GetAsync<object>("/api/");

            Token = token;
            ServerUrl = server;

            Settings.Default.ServerUrl = server;
            Settings.Default.ApiToken = token;
            Settings.Default.RememberMe = chkRememberMe.Checked;
            Settings.Default.SavedUsername = chkRememberMe.Checked ? txtUsername.Text.Trim() : null;
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

    private void ShowError(string msg)
    {
        lblStatus.Text = msg;
        lblStatus.ForeColor = Color.FromArgb(220, 38, 38);
    }

    private void SetLoading(bool loading, string? text = null)
    {
        btnLogin.Enabled = !loading;
        btnConnect.Enabled = !loading;
        lblStatus.Text = loading ? (text ?? "") : "";
        lblStatus.ForeColor = SystemColors.GrayText;
        Cursor = loading ? Cursors.WaitCursor : Cursors.Default;
    }
}