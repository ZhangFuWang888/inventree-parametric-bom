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

        return await _client.GetListAsync<Part, PartListResponse>($"/api/part/{query}");
    }

    /// <summary>获取所有部装（assembly=true, is_template=false）</summary>
    public async Task<List<Part>> GetSubassembliesAsync(string? search = null)
    {
        var query = "?assembly=true&is_template=false";
        if (!string.IsNullOrEmpty(search))
            query += $"&search={Uri.EscapeDataString(search)}";

        return await _client.GetListAsync<Part, PartListResponse>($"/api/part/{query}");
    }

    /// <summary>获取所有零件（assembly=false）</summary>
    public async Task<List<Part>> GetPartsAsync(string? search = null)
    {
        var query = "?assembly=false";
        if (!string.IsNullOrEmpty(search))
            query += $"&search={Uri.EscapeDataString(search)}";

        return await _client.GetListAsync<Part, PartListResponse>($"/api/part/{query}");
    }

    /// <summary>获取指定分类下的物料（支持类型过滤）— 自动分页获取全部</summary>
    public async Task<List<Part>> GetPartsByCategoryAsync(int? categoryId,
        string? typeFilter = null, string? search = null)
    {
        var query = BuildPartQuery(categoryId, typeFilter, search, limit: 1000);
        return await _client.GetAllPagesAsync<Part, PartListResponse>($"/api/part/{query}");
    }

    /// <summary>获取指定分类下的物料（分页版）</summary>
    public async Task<PagedResult<Part>> GetPartsByCategoryPagedAsync(
        int? categoryId, int page, int pageSize = 100,
        string? typeFilter = null, string? search = null)
    {
        var offset = (page - 1) * pageSize;
        var query = BuildPartQuery(categoryId, typeFilter, search, pageSize, offset);

        var response = await _client.GetAsync<PartListResponse>($"/api/part/{query}");

        return new PagedResult<Part>
        {
            Items = response.Results,
            TotalCount = response.Count,
            PageIndex = page,
            PageSize = pageSize
        };
    }

    private static string BuildPartQuery(int? categoryId,
        string? typeFilter, string? search,
        int limit = 100, int offset = 0)
    {
        var query = $"?limit={limit}&offset={offset}";
        if (categoryId.HasValue)
            query += $"&category={categoryId.Value}";
        if (!string.IsNullOrEmpty(typeFilter))
        {
            query += typeFilter switch
            {
                "产品" => "&assembly=true&is_template=true",
                "部装" => "&assembly=true&is_template=false",
                "零件" => "&assembly=false",
                _ => ""
            };
        }
        if (!string.IsNullOrEmpty(search))
            query += $"&search={Uri.EscapeDataString(search)}";

        return query;
    }

    /// <summary>根据关键词搜索物料 — 自动分页获取全部</summary>
    public async Task<List<Part>> SearchPartsAsync(string keyword)
    {
        var query = $"?search={Uri.EscapeDataString(keyword)}&limit=1000";
        return await _client.GetAllPagesAsync<Part, PartListResponse>($"/api/part/{query}");
    }

    /// <summary>获取单个物料详情</summary>
    public async Task<Part> GetPartAsync(int partId)
    {
        return await _client.GetAsync<Part>($"/api/part/{partId}/");
    }
}
