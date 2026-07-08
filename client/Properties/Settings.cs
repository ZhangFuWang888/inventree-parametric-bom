namespace BomQueryClient.Properties;

/// <summary>
/// 应用程序设置
/// </summary>
internal sealed class Settings
{
    private static readonly string ConfigPath =
        Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "config.ini");

    public string? ServerUrl { get; set; }
    public string? ApiToken { get; set; }
    public bool RememberMe { get; set; }
    public string? SavedUsername { get; set; }

    private static Settings? _default;

    public static Settings Default
    {
        get
        {
            if (_default == null)
            {
                _default = new Settings();
                _default.Load();
            }
            return _default;
        }
    }

    public void Save()
    {
        var lines = new List<string>();
        if (!string.IsNullOrEmpty(ServerUrl))
            lines.Add($"ServerUrl={ServerUrl}");
        if (!string.IsNullOrEmpty(ApiToken))
            lines.Add($"ApiToken={ApiToken}");
        lines.Add($"RememberMe={RememberMe}");
        if (!string.IsNullOrEmpty(SavedUsername))
            lines.Add($"Username={SavedUsername}");
        File.WriteAllLines(ConfigPath, lines);
    }

    private void Load()
    {
        if (!File.Exists(ConfigPath)) return;
        foreach (var line in File.ReadAllLines(ConfigPath))
        {
            var parts = line.Split('=', 2);
            if (parts.Length != 2) continue;

            switch (parts[0])
            {
                case "ServerUrl": ServerUrl = parts[1]; break;
                case "ApiToken": ApiToken = parts[1]; break;
                case "RememberMe":
                    bool.TryParse(parts[1], out var rm);
                    RememberMe = rm;
                    break;
                case "Username": SavedUsername = parts[1]; break;
            }
        }
    }
}