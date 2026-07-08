namespace BomQueryClient.Api.Models;

/// <summary>产品配置</summary>
public class ProductConfiguration
{
    public int Id { get; set; }
    public int TemplatePart { get; set; }
    public string? TemplatePartName { get; set; }
    public string? Title { get; set; }
    public string? Revision { get; set; }
    public string? Status { get; set; }
    public string? CreatedAt { get; set; }
    public string? UpdatedAt { get; set; }
    public Dictionary<string, string>? ParamsSnapshot { get; set; }
    public object? GeneratedBom { get; set; }
    public string? Notes { get; set; }

    public string StatusDisplay => Status switch
    {
        "draft" => "📝 草稿",
        "completed" => "✅ 已完成",
        "released" => "🚀 已发布",
        "obsolete" => "🗑 已弃用",
        _ => Status ?? "未知"
    };
}

/// <summary>配置列表响应</summary>
public class ConfigListResponse
{
    public int Count { get; set; }
    public string? Next { get; set; }
    public List<ProductConfiguration> Results { get; set; } = new();
}

/// <summary>物料的参数配置（PartParameterConfig）</summary>
public class ParamConfigEntry
{
    public int Id { get; set; }
    public int Part { get; set; }
    public string? Name { get; set; }
    public string? ParameterType { get; set; }
    public string? DefaultValue { get; set; }
    public string? Options { get; set; }
}

public class ParamConfigListResponse
{
    public int Count { get; set; }
    public List<ParamConfigEntry> Results { get; set; } = new();
}

/// <summary>配置参数值</summary>
public class ConfigValueEntry
{
    public int Id { get; set; }
    public int Config { get; set; }
    public string? Parameter { get; set; }
    public string? Value { get; set; }
    public string? ParamType { get; set; }
}

public class ConfigValueListResponse
{
    public int Count { get; set; }
    public List<ConfigValueEntry> Results { get; set; } = new();
}

/// <summary>BOM 评估结果节点</summary>
public class BomEvalNode
{
    public int PartId { get; set; }
    public string? PartName { get; set; }
    public string? PartIpn { get; set; }
    public int Depth { get; set; }
    public decimal Quantity { get; set; }
    public decimal CalculatedQuantity { get; set; }
    public bool Excluded { get; set; }
    public string? ExcludeReason { get; set; }
    public List<BomEvalNode> Children { get; set; } = new();
}

/// <summary>BOM 评估结果</summary>
public class BomEvaluateResult
{
    public int PartId { get; set; }
    public string? PartName { get; set; }
    public BomEvalNode? BomTree { get; set; }
    public Dictionary<string, string>? Parameters { get; set; }
}
