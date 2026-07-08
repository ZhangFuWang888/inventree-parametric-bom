namespace BomQueryClient.Api.Models;

/// <summary>
/// 分页查询结果
/// </summary>
public class PagedResult<T>
{
    public List<T> Items { get; set; } = new();
    public int TotalCount { get; set; }
    public int PageIndex { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => PageSize > 0 ? (int)Math.Ceiling((double)TotalCount / PageSize) : 0;
    public bool HasPrev => PageIndex > 1;
    public bool HasNext => PageIndex < TotalPages;
}
