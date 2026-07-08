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
