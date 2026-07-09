using BomQueryClient.Api.Models;

namespace BomQueryClient.Api.Services;

/// <summary>
/// 参数化 BOM 查询服务 — 识别哪些物料是参数化的
/// </summary>
public class ParametricService
{
    private readonly InvenTreeClient _client;
    private HashSet<int>? _parametricPartIds;
    private bool _loaded;

    public ParametricService(InvenTreeClient client)
    {
        _client = client;
    }

    /// <summary>获取所有参数化物料的 Part ID 集合</summary>
    public async Task<HashSet<int>> GetParametricPartIdsAsync()
    {
        if (_loaded && _parametricPartIds != null)
            return _parametricPartIds;

        var ids = new HashSet<int>();

        try
        {
            // 1. 从 part-config 获取配置了参数的物料
            var partConfigs = await _client.GetAllPagesAsync<PartConfigEntry, PartConfigListResponse>(
                "/api/parametric-bom/part-config/?limit=200");
            foreach (var cfg in partConfigs)
                ids.Add(cfg.Part);

            _parametricPartIds = ids;
            _loaded = true;
        }
        catch
        {
            // 如果 API 不可用，返回空集合
            _parametricPartIds = new HashSet<int>();
        }

        return _parametricPartIds;
    }

    /// <summary>判断指定物料是否为参数化物料</summary>
    public bool IsParametric(int partId)
    {
        return _parametricPartIds?.Contains(partId) ?? false;
    }

    /// <summary>在线检查单个物料是否为参数化（走 check-param-status 接口）</summary>
    public async Task<ParamStatusResponse> CheckParamStatusAsync(int partId)
    {
        return await _client.GetAsync<ParamStatusResponse>(
            $"/api/parametric-bom/check-param-status/?part_id={partId}");
    }

    /// <summary>按型号(IPN)+名称查询参数化状态</summary>
    public async Task<ParamStatusResponse> CheckParamStatusByInfoAsync(string ipn, string? name = null)
    {
        var query = $"/api/parametric-bom/check-param-status/?ipn={Uri.EscapeDataString(ipn)}";
        if (!string.IsNullOrEmpty(name))
            query += $"&name={Uri.EscapeDataString(name)}";
        return await _client.GetAsync<ParamStatusResponse>(query);
    }
}

// ── 内部 DTO ──────────────────────────────

internal class PartConfigEntry
{
    public int Id { get; set; }
    public int Part { get; set; }
}

internal class PartConfigListResponse
{
    public int Count { get; set; }
    public List<PartConfigEntry> Results { get; set; } = new();
}

/// <summary>check-param-status 接口返回</summary>
public class ParamStatusResponse
{
    public int PartId { get; set; }
    public string Ipn { get; set; } = "";
    public string Name { get; set; } = "";
    public bool IsParametric { get; set; }
    public int ParamCount { get; set; }
}
