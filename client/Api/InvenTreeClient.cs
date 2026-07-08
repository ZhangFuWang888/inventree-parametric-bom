using System.Net.Http.Headers;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json.Serialization;

namespace BomQueryClient.Api;

/// <summary>
/// InvenTree REST API 客户端 — 处理认证和 HTTP 请求
/// </summary>
public class InvenTreeClient
{
    private readonly HttpClient _http;
    private string? _token;

    private static readonly JsonSerializerSettings JsonSettings = new()
    {
        ContractResolver = new DefaultContractResolver
        {
            NamingStrategy = new SnakeCaseNamingStrategy()
        },
        NullValueHandling = NullValueHandling.Ignore
    };

    public InvenTreeClient(string baseUrl)
    {
        BaseUrl = baseUrl.TrimEnd('/');
        _http = new HttpClient
        {
            BaseAddress = new Uri(BaseUrl),
            Timeout = TimeSpan.FromSeconds(30)
        };
    }

    public string BaseUrl { get; }
    public bool IsAuthenticated => !string.IsNullOrEmpty(_token);

    #region 认证

    /// <summary>设置已有 Token</summary>
    public void SetToken(string token)
    {
        _token = token;
        _http.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Token", token);
    }

    /// <summary>清除 Token</summary>
    public void ClearToken()
    {
        _token = null;
        _http.DefaultRequestHeaders.Authorization = null;
    }

    #endregion

    #region HTTP 方法

    /// <summary>GET 请求</summary>
    public async Task<T> GetAsync<T>(string endpoint)
    {
        var response = await _http.GetAsync(endpoint);
        response.EnsureSuccessStatusCode();
        var json = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<T>(json, JsonSettings)
               ?? throw new Exception($"反序列化失败: {endpoint}");
    }

    /// <summary>GET 物料列表，自动兼容数组与 {results:[...]} 两种返回格式</summary>
    public async Task<List<TItem>> GetListAsync<TItem, TWrapped>(string endpoint)
        where TWrapped : class
    {
        var response = await _http.GetAsync(endpoint);
        response.EnsureSuccessStatusCode();
        var json = await response.Content.ReadAsStringAsync();

        var token = JToken.Parse(json);
        if (token is JArray arr)
        {
            return arr.ToObject<List<TItem>>(JsonSerializer.Create(JsonSettings))
                   ?? new List<TItem>();
        }

        var wrapped = token.ToObject<TWrapped>(JsonSerializer.Create(JsonSettings));
        var resultsProp = wrapped?.GetType().GetProperty("Results");
        if (resultsProp?.GetValue(wrapped) is IEnumerable<TItem> list)
            return list.ToList();
        return new List<TItem>();
    }

    /// <summary>GET 全部分页物料 — 自动跟随 next 链接遍历所有页</summary>
    public async Task<List<TItem>> GetAllPagesAsync<TItem, TWrapped>(string endpoint)
        where TWrapped : class
    {
        var allItems = new List<TItem>();
        var nextUrl = endpoint;

        while (!string.IsNullOrEmpty(nextUrl))
        {
            var response = await _http.GetAsync(nextUrl);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            var token = JToken.Parse(json);

            List<TItem>? pageItems = null;

            if (token is JArray arr)
            {
                pageItems = arr.ToObject<List<TItem>>(JsonSerializer.Create(JsonSettings));
                nextUrl = null; // 数组格式不支持分页
            }
            else
            {
                var wrapped = token.ToObject<TWrapped>(
                    JsonSerializer.Create(JsonSettings));
                var resultsProp = wrapped?.GetType().GetProperty("Results");
                if (resultsProp?.GetValue(wrapped) is IEnumerable<TItem> list)
                    pageItems = list.ToList();

                var nextProp = wrapped?.GetType().GetProperty("Next");
                nextUrl = nextProp?.GetValue(wrapped) as string;
            }

            if (pageItems != null)
                allItems.AddRange(pageItems);
        }

        return allItems;
    }

    /// <summary>POST 请求（JSON body）</summary>
    public async Task<T> PostAsync<T>(string endpoint, object? body = null)
    {
        var content = body != null
            ? new StringContent(JsonConvert.SerializeObject(body, JsonSettings),
                Encoding.UTF8, "application/json")
            : null;

        var response = await _http.PostAsync(endpoint, content);
        response.EnsureSuccessStatusCode();
        var json = await response.Content.ReadAsStringAsync();

        if (typeof(T) == typeof(string))
            return (T)(object)json;

        return JsonConvert.DeserializeObject<T>(json, JsonSettings)
               ?? throw new Exception($"反序列化失败: {endpoint}");
    }

    /// <summary>POST 表单（登录用）</summary>
    public async Task<T> PostFormAsync<T>(string endpoint,
        Dictionary<string, string> formData)
    {
        var content = new FormUrlEncodedContent(formData);
        var response = await _http.PostAsync(endpoint, content);
        response.EnsureSuccessStatusCode();
        var json = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<T>(json, JsonSettings)
               ?? throw new Exception($"反序列化失败: {endpoint}");
    }

    #endregion
}
