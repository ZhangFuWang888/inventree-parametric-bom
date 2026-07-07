using BomQueryClient.Api.Models;

namespace BomQueryClient.Api.Services;

/// <summary>
/// 物料/产品查询服务
/// </summary>
public class PartService
{
    private readonly InvenTreeClient _client;

    public PartService(InvenTreeClient client)
    {
        _client = client;
    }

    /// <summary>获取所有产品（assembly=true）</summary>
    public async Task<List<Part>> GetProductsAsync(string? search = null, int? category = null)
    {
        var query = "?assembly=true";
        if (!string.IsNullOrEmpty(search))
            query += $"&search={Uri.EscapeDataString(search)}";
        if (category.HasValue)
            query += $"&category={category.Value}";

        var response = await _client.GetAsync<PartListResponse>($"/api/part/{query}");
        return response.Results;
    }

    /// <summary>获取所有部装（assembly=true, is_template=false）</summary>
    public async Task<List<Part>> GetSubassembliesAsync(string? search = null)
    {
        var query = "?assembly=true&is_template=false";
        if (!string.IsNullOrEmpty(search))
            query += $"&search={Uri.EscapeDataString(search)}";

        var response = await _client.GetAsync<PartListResponse>($"/api/part/{query}");
        return response.Results;
    }

    /// <summary>获取所有零件（assembly=false）</summary>
    public async Task<List<Part>> GetPartsAsync(string? search = null)
    {
        var query = "?assembly=false";
        if (!string.IsNullOrEmpty(search))
            query += $"&search={Uri.EscapeDataString(search)}";

        var response = await _client.GetAsync<PartListResponse>($"/api/part/{query}");
        return response.Results;
    }

    /// <summary>根据关键词搜索物料</summary>
    public async Task<List<Part>> SearchPartsAsync(string keyword)
    {
        var query = $"?search={Uri.EscapeDataString(keyword)}&limit=50";
        var response = await _client.GetAsync<PartListResponse>($"/api/part/{query}");
        return response.Results;
    }

    /// <summary>获取单个物料详情</summary>
    public async Task<Part> GetPartAsync(int partId)
    {
        return await _client.GetAsync<Part>($"/api/part/{partId}/");
    }
}
