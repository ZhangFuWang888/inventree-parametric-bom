"""Admin registration for Parametric BOM models."""

from django.contrib import admin

from parametric_bom.models import (
    BomCandidatePart,
    BomSpecification,
    ConfigParameterValue,
    InheritanceMapping,
    ParametricBomItem,
    ParametricRule,
    PartAttributeFormula,
    PartParameterConfig,
    ProductConfiguration,
    Project,
    ProjectItem,
    VariantMapping,
)


@admin.register(PartParameterConfig)
class PartParameterConfigAdmin(admin.ModelAdmin):
    """Admin for PartParameterConfig."""
    list_display = ['part', 'template', 'parameter_type', 'is_driving', 'is_computed']
    list_filter = ['parameter_type', 'is_driving', 'is_computed']
    search_fields = ['part__name', 'template__name']


@admin.register(ParametricBomItem)
class ParametricBomItemAdmin(admin.ModelAdmin):
    """Admin for ParametricBomItem."""
    list_display = ['bom_item', 'active_flags', 'has_formula']
    list_filter = ['enable_qty_formula', 'enable_conditional', 'enable_candidate',
                   'enable_variant', 'enable_specification',
                   'enable_structure']

    def active_flags(self, obj):
        """Show which flags are enabled as a compact string."""
        flags = []
        mapping = [
            ('enable_qty_formula', 'Q'),
            ('enable_conditional', 'C'),
            ('enable_candidate', '🎯'),
            ('enable_variant', '🧬'),
            ('enable_specification', '📝'),
            ('enable_structure', '🔗'),
        ]
        for field, label in mapping:
            if getattr(obj, field, False):
                flags.append(label)
        return ' '.join(flags) if flags else '—'
    active_flags.short_description = '模式'


@admin.register(ParametricRule)
class ParametricRuleAdmin(admin.ModelAdmin):
    """Admin for ParametricRule."""
    list_display = ['product_part', 'rule_type', 'action', 'enabled', 'priority']
    list_filter = ['rule_type', 'action', 'enabled']


@admin.register(ProductConfiguration)
class ProductConfigurationAdmin(admin.ModelAdmin):
    """Admin for ProductConfiguration."""
    list_display = ['title', 'template_part', 'status', 'revision', 'created_at']
    list_filter = ['status']


@admin.register(ConfigParameterValue)
class ConfigParameterValueAdmin(admin.ModelAdmin):
    """Admin for ConfigParameterValue."""
    list_display = ['config', 'template', 'value', 'source']


# ── New Models ──────────────────────────────


@admin.register(BomCandidatePart)
class BomCandidatePartAdmin(admin.ModelAdmin):
    """Admin for BomCandidatePart."""
    list_display = ['parametric_bom_item', 'part', 'label', 'priority']
    list_filter = ['parametric_bom_item']


@admin.register(VariantMapping)
class VariantMappingAdmin(admin.ModelAdmin):
    """Admin for VariantMapping."""
    list_display = ['parametric_bom_item', 'template_part', 'variant_name_template']


@admin.register(BomSpecification)
class BomSpecificationAdmin(admin.ModelAdmin):
    """Admin for BomSpecification."""
    list_display = ['parametric_bom_item', 'spec_type']


@admin.register(InheritanceMapping)
class InheritanceMappingAdmin(admin.ModelAdmin):
    """Admin for InheritanceMapping."""
    list_display = ['target_part', 'target_template', 'source_template', 'enabled']
    list_filter = ['enabled']


@admin.register(PartAttributeFormula)
class PartAttributeFormulaAdmin(admin.ModelAdmin):
    """Admin for PartAttributeFormula."""
    list_display = ['part', 'attribute_name', 'attribute_type', 'unit']
    list_filter = ['attribute_type']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin for Project."""
    list_display = ['project_code', 'name', 'customer', 'status', 'owner', 'created_at']
    list_filter = ['status', 'is_active']
    search_fields = ['name', 'project_code', 'description']
    readonly_fields = ['project_code', 'created_at', 'updated_at']


@admin.register(ProjectItem)
class ProjectItemAdmin(admin.ModelAdmin):
    """Admin for ProjectItem."""
    list_display = ['title', 'project', 'item_type', 'quantity', 'created_at']
    list_filter = ['item_type']
    search_fields = ['title']
