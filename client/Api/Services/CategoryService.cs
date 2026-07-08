using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace BomQueryClient.Api.Services;

/// <summary>
/// 物料分类查询服务
/// </summary>
public class CategoryService
{
    private readonly InvenTreeClient _client;

    public CategoryService(InvenTreeClient client)
    {
        _client = client;
    }

    /// <summary>获取全部分类（扁平列表）</summary>
    public async Task<List<PartCategory>> GetAllAsync()
    {
        return await _client.GetListAsync<PartCategory, PartCategoryListResponse>(
            "/api/part/category/?limit=200");
    }

    /// <summary>将扁平分类列表构建为父子树并返回根节点</summary>
    public static List<TreeNode> BuildTree(List<PartCategory> categories)
    {
        var dict = categories.ToDictionary(c => c.Pk);
        var roots = new List<TreeNode>();

        // 添加"全部物料"根节点
        var allNode = new TreeNode("📁 全部物料")
        {
            Tag = null, // null = 全部
            ToolTipText = "显示所有物料"
        };
        roots.Add(allNode);

        // 顶级分类（parent==null）
        foreach (var cat in categories.Where(c => c.Parent == null)
                     .OrderBy(c => c.Name))
        {
            var node = BuildCategoryNode(cat, dict);
            roots.Add(node);
        }

        return roots;
    }

    private static TreeNode BuildCategoryNode(PartCategory cat,
        Dictionary<int, PartCategory> allCats)
    {
        var partCount = cat.PartCount > 0 ? $" ({cat.PartCount})" : "";
        var node = new TreeNode($"📂 {cat.Name}{partCount}")
        {
            Tag = cat.Pk,
            ToolTipText = !string.IsNullOrEmpty(cat.Description)
                ? $"{cat.Description}\n物料数: {cat.PartCount}"
                : $"物料数: {cat.PartCount}"
        };

        // 递归添加子分类
        foreach (var child in allCats.Values
                     .Where(c => c.Parent == cat.Pk)
                     .OrderBy(c => c.Name))
        {
            node.Nodes.Add(BuildCategoryNode(child, allCats));
        }

        return node;
    }
}

/// <summary>
/// InvenTree 物料分类
/// </summary>
public class PartCategory
{
    public int Pk { get; set; }
    public string Name { get; set; } = "";
    public string? Description { get; set; }
    public int? Parent { get; set; }
    public int Level { get; set; }
    public string? PathString { get; set; }
    public int PartCount { get; set; }
    public int Subcategories { get; set; }
}

public class PartCategoryListResponse
{
    public int Count { get; set; }
    public string? Next { get; set; }
    public string? Previous { get; set; }
    public List<PartCategory> Results { get; set; } = new();
}
