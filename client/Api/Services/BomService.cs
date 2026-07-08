using BomQueryClient.Api.Models;

namespace BomQueryClient.Api.Services;

/// <summary>
/// BOM 查询服务 — 支持静态BOM递归展开
/// </summary>
public class BomService
{
    private readonly InvenTreeClient _client;

    public BomService(InvenTreeClient client)
    {
        _client = client;
    }

    /// <summary>
    /// 获取某物料的直接BOM子项（一级）
    /// </summary>
    public async Task<List<BomItem>> GetDirectBomAsync(int partId)
    {
        return await _client.GetListAsync<BomItem, BomListResponse>(
            $"/api/bom/?part={partId}&sub_part_detail=true");
    }

    /// <summary>
    /// 递归展开完整BOM树
    /// </summary>
    public async Task<BomTreeNode> GetFullBomTreeAsync(int partId,
        decimal quantity = 1, int level = 0, HashSet<int>? visited = null)
    {
        visited ??= new HashSet<int>();

        var part = await _client.GetAsync<Part>($"/api/part/{partId}/");
        var node = new BomTreeNode
        {
            Part = part,
            Quantity = quantity,
            Level = level
        };

        // 防止循环引用
        if (visited.Contains(partId))
            return node;

        visited.Add(partId);

        // 只有组装件才展开BOM
        if (part.Assembly)
        {
            var bomItems = await GetDirectBomAsync(partId);
            foreach (var item in bomItems)
            {
                if (item.SubPart == null) continue;

                var child = await GetFullBomTreeAsync(
                    item.SubPart.Value,
                    item.Quantity,
                    level + 1,
                    new HashSet<int>(visited));

                node.Children.Add(child);
            }
        }

        return node;
    }

    /// <summary>
    /// 反向查询：某零件被哪些产品使用（Where Used）
    /// </summary>
    public async Task<List<BomItem>> WhereUsedAsync(int partId)
    {
        return await _client.GetListAsync<BomItem, BomListResponse>(
            $"/api/bom/?sub_part={partId}&part_detail=true");
    }
}
