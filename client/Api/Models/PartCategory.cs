namespace BomQueryClient.Api.Models;

/// <summary>
/// InvenTree 物料分类
/// </summary>
public class PartCategory
{
    public int Pk { get; set; }
    public string Name { get; set; } = "";
    public string? Description { get; set; }
    public int? Parent { get; set; }
    public string? PathString { get; set; }
    public int? Level { get; set; }

    public string DisplayName => string.IsNullOrEmpty(Description)
        ? Name
        : $"{Name} ({Description})";
}

public class PartCategoryListResponse
{
    public int Count { get; set; }
    public string? Next { get; set; }
    public string? Previous { get; set; }
    public List<PartCategory> Results { get; set; } = new();
}
