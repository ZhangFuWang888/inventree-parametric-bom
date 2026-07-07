using BomQueryClient.Api.Models;

namespace BomQueryClient.Api.Services;

/// <summary>
/// 认证服务 — 登录获取 Token
/// </summary>
public class AuthService
{
    private readonly InvenTreeClient _client;

    public AuthService(InvenTreeClient client)
    {
        _client = client;
    }

    /// <summary>
    /// 使用用户名密码登录，获取 API Token
    /// </summary>
    public async Task<string> LoginAsync(string username, string password)
    {
        var form = new Dictionary<string, string>
        {
            ["username"] = username,
            ["password"] = password
        };

        var result = await _client.PostFormAsync<LoginResponse>(
            "/api/auth/login/", form);

        var token = result.Key ?? result.Token
                    ?? throw new Exception("登录响应中没有 Token");

        _client.SetToken(token);
        return token;
    }

    /// <summary>退出登录</summary>
    public void Logout()
    {
        _client.ClearToken();
    }
}
