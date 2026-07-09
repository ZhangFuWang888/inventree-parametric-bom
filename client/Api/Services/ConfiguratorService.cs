using BomQueryClient.Api.Models;

namespace BomQueryClient.Api.Services;

/// <summary>
/// 参数化配置器服务 — 产品配置CRUD + BOM评估
/// </summary>
public class ConfiguratorService
{
    private readonly InvenTreeClient _client;

    public ConfiguratorService(InvenTreeClient client)
    {
        _client = client;
    }

    // ── 配置 CRUD ──────────────────────

    /// <summary>获取某个产品的所有配置</summary>
    public async Task<List<ProductConfiguration>> GetConfigsAsync(int partId)
    {
        return await _client.GetListAsync<ProductConfiguration, ConfigListResponse>(
            $"/api/parametric-bom/configurations/?template_part={partId}&limit=100");
    }

    /// <summary>创建新配置</summary>
    public async Task<ProductConfiguration> CreateConfigAsync(int partId, string title)
    {
        return await _client.PostAsync<ProductConfiguration>(
            "/api/parametric-bom/configurations/",
            new { template_part = partId, title });
    }

    /// <summary>获取配置详情</summary>
    public async Task<ProductConfiguration> GetConfigAsync(int configId)
    {
        return await _client.GetAsync<ProductConfiguration>(
            $"/api/parametric-bom/configurations/{configId}/");
    }

    /// <summary>变更配置状态</summary>
    public async Task<bool> TransitionConfigAsync(int configId, string targetStatus)
    {
        try
        {
            var result = await _client.PostAsync<Dictionary<string, object>>(
                $"/api/parametric-bom/configs/{configId}/transition/",
                new { status = targetStatus });
            return result.ContainsKey("success") && result["success"]?.ToString() == "True";
        }
        catch
        {
            return false;
        }
    }

    // ── 参数配置 ──────────────────────

    /// <summary>获取某产品的参数模板（PartParameterConfig）</summary>
    public async Task<List<ParamConfigEntry>> GetPartParamsAsync(int partId)
    {
        return await _client.GetListAsync<ParamConfigEntry, ParamConfigListResponse>(
            $"/api/parametric-bom/part-config/?part={partId}&limit=100");
    }

    // ── BOM 评估 ──────────────────────

    /// <summary>评估 BOM — 使用参数值计算</summary>
    public async Task<BomEvaluateResult> EvaluateBomAsync(int partId,
        Dictionary<string, string> paramValues)
    {
        try
        {
            return await _client.PostAsync<BomEvaluateResult>(
                "/api/parametric-bom/evaluate/",
                new { part_id = partId, @params = paramValues });
        }
        catch (Exception ex)
        {
            throw new Exception($"BOM 评估失败: {ex.Message}");
        }
    }
}
