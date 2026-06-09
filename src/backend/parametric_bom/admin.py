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
    SupplierSelectionRule,
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
    list_display = ['bom_item', 'mode', 'has_formula']
    list_filter = ['mode']


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
    list_display = ['parametric_bom_item', 'template_part', 'auto_generate']


@admin.register(BomSpecification)
class BomSpecificationAdmin(admin.ModelAdmin):
    """Admin for BomSpecification."""
    list_display = ['parametric_bom_item', 'spec_type']


@admin.register(SupplierSelectionRule)
class SupplierSelectionRuleAdmin(admin.ModelAdmin):
    """Admin for SupplierSelectionRule."""
    list_display = ['parametric_bom_item', 'supplier_part', 'priority', 'label']
    list_filter = ['parametric_bom_item']


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
