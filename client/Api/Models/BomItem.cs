namespace BomQueryClient.Api.Models;

/// <summary>
/// BOM 子项 — 一个物料下的子件
/// </summary>
public class BomItem
{
    public int Pk { get; set; }
    public int Part { get; set; }            // 父件 ID
    public int? SubPart { get; set; }        // 子件 ID
    public PartDetail? SubPartDetail { get; set; }
    public decimal Quantity { get; set; }
    public string? Reference { get; set; }
    public bool Optional { get; set; }
    public bool Override { get; set; }
    public string? Notes { get; set; }
    public bool Valid { get; set; }
    public bool Inherited { get; set; }
    public bool AllowVariants { get; set; }
    public int? GetsSourcedFrom { get; set; }

    /// <summary>直接可用的子件名</summary>
    public string SubPartName => SubPartDetail?.FullName ?? $"ID:{SubPart}";
}

/// <summary>
/// BOM 子件详情（嵌入在 BomItem 中）
/// </summary>
public class PartDetail
{
    public int Pk { get; set; }
    public string Name { get; set; } = "";
    public string? IPN { get; set; }
    public string? Description { get; set; }
    public string? Units { get; set; }
    public bool Assembly { get; set; }
    public bool IsTemplate { get; set; }
    public string? Thumbnail { get; set; }

    public string FullName => string.IsNullOrEmpty(IPN) ? Name : $"[{IPN}] {Name}";
}

/// <summary>
/// BOM 列表 API 响应
/// </summary>
public class BomListResponse
{
    public int Count { get; set; }
    public string? Next { get; set; }
    public string? Previous { get; set; }
    public List<BomItem> Results { get; set; } = new();
}

/// <summary>
/// 递归展开后的 BOM 树节点
/// </summary>
public class BomTreeNode
{
    public Part Part { get; set; } = null!;
    public decimal Quantity { get; set; }
    public int Level { get; set; }
    public List<BomTreeNode> Children { get; set; } = new();
}
