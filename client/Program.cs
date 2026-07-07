using BomQueryClient.Forms;
using BomQueryClient.Properties;

namespace BomQueryClient;

static class Program
{
    [STAThread]
    static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        // 全局默认字体 — 中文友好，统一风格
        var font = GetChineseFriendlyFont();

        var settings = Settings.Default;

        if (!string.IsNullOrEmpty(settings.ApiToken) && !string.IsNullOrEmpty(settings.ServerUrl))
        {
            try
            {
                Application.Run(new MainForm(settings.ServerUrl, settings.ApiToken, font));
                return;
            }
            catch
            {
                // Token 失效，走登录
            }
        }

        using var loginForm = new LoginForm(font);
        if (loginForm.ShowDialog() == DialogResult.OK)
        {
            Application.Run(new MainForm(loginForm.ServerUrl!, loginForm.Token!, font));
        }
    }

    /// <summary>获取系统上对中文友好的字体</summary>
    static Font GetChineseFriendlyFont()
    {
        string[] preferred = { "Microsoft YaHei UI", "Microsoft YaHei", "SimSun", "微软雅黑" };
        foreach (var name in preferred)
        {
            using var testFont = new Font(name, 9f, FontStyle.Regular, GraphicsUnit.Point);
            if (testFont.Name == name)
                return new Font(name, 9f, FontStyle.Regular, GraphicsUnit.Point);
        }
        // 兜底
        var installed = InstalledFontCollection();
        var chineseFont = installed.FirstOrDefault(f =>
            f.Name.Contains("YaHei") || f.Name.Contains("微软") || f.Name.Contains("SimSun"));
        return new Font(chineseFont?.Name ?? "Microsoft Sans Serif", 9f);
    }

    static FontFamily[] InstalledFontCollection()
    {
        using var col = new System.Drawing.Text.InstalledFontCollection();
        var result = new FontFamily[col.Families.Length];
        col.Families.CopyTo(result, 0);
        return result;
    }
}
