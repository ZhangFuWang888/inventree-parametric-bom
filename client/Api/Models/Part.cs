namespace BomQueryClient.Api.Models;

/// <summary>
/// InvenTree 物料/零件/产品
/// </summary>
public class Part
{
    public int Pk { get; set; }
    public string Name { get; set; } = "";
    public string? Description { get; set; }
    public string? IPN { get; set; }          // 物料编码/图号
    public string? Revision { get; set; }
    public string? Units { get; set; }
    public string? CategoryName { get; set; }
    public int? Category { get; set; }
    public bool Assembly { get; set; }        // true=部装/产品
    public bool IsTemplate { get; set; }      // true=产品模板
    public bool Virtual { get; set; }
    public bool Active { get; set; }
    public decimal? TotalInStock { get; set; }
    public string? Thumbnail { get; set; }
    public string? Image { get; set; }

    /// <summary>全名：IPN - Name</summary>
    public string FullName => string.IsNullOrEmpty(IPN) ? Name : $"[{IPN}] {Name}";
}

/// <summary>
/// InvenTree 物料列表 API 响应包装
/// </summary>
public class PartListResponse
{
    public int Count { get; set; }
    public string? Next { get; set; }
    public string? Previous { get; set; }
    public List<Part> Results { get; set; } = new();
}
