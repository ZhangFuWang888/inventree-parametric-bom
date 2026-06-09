"""API serializers for Parametric BOM models."""

from rest_framework import serializers

from parametric_bom.models import (
    BomCandidatePart,
    BomItemModeChoices,
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


class PartParameterConfigSerializer(serializers.ModelSerializer):
    """Serializer for PartParameterConfig."""

    part_name = serializers.CharField(source='part.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)

    class Meta:
        """Meta options."""
        model = PartParameterConfig
        fields = [
            'id', 'part', 'part_name', 'template', 'template_name',
            'parameter_type', 'options',
            'default_value', 'min_value', 'max_value',
            'is_driving', 'is_computed', 'computation_formula',
            'ui_hint', 'display_order', 'visible_on_config',
        ]


class ParametricBomItemSerializer(serializers.ModelSerializer):
    """Serializer for ParametricBomItem."""

    part_name = serializers.CharField(
        source='bom_item.part.name', read_only=True
    )
    sub_part_name = serializers.CharField(
        source='bom_item.sub_part.name', read_only=True
    )
    has_formula = serializers.BooleanField(read_only=True)
    mode_display = serializers.CharField(
        source='get_mode_display', read_only=True
    )

    class Meta:
        """Meta options."""
        model = ParametricBomItem
        fields = [
            'id', 'bom_item', 'part_name', 'sub_part_name',
            'mode', 'mode_display',
            'qty_formula', 'condition_formula', 'part_selector_formula',
            'formular_hash', 'has_formula',
        ]


class ParametricRuleSerializer(serializers.ModelSerializer):
    """Serializer for ParametricRule."""

    product_part_name = serializers.CharField(
        source='product_part.name', read_only=True
    )
    target_param_name = serializers.CharField(
        source='target_param.name', read_only=True, allow_null=True
    )

    class Meta:
        """Meta options."""
        model = ParametricRule
        fields = [
            'id', 'product_part', 'product_part_name', 'rule_type',
            'condition_formula', 'target_param', 'target_param_name',
            'action', 'value_formula', 'error_message',
            'priority', 'enabled',
        ]


class ProductConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for ProductConfiguration."""

    template_part_name = serializers.CharField(
        source='template_part.name', read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.username', read_only=True, allow_null=True
    )
    parameter_count = serializers.SerializerMethodField()

    class Meta:
        """Meta options."""
        model = ProductConfiguration
        fields = [
            'id', 'template_part', 'template_part_name', 'title',
            'revision', 'status', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'params_snapshot',
            'generated_bom', 'total_cost', 'notes', 'parameter_count',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_parameter_count(self, obj) -> int:
        """Count parameter values for this configuration."""
        return obj.parameter_values.count()


class ConfigParameterValueSerializer(serializers.ModelSerializer):
    """Serializer for ConfigParameterValue."""

    template_name = serializers.CharField(
        source='template.name', read_only=True
    )

    class Meta:
        """Meta options."""
        model = ConfigParameterValue
        fields = [
            'id', 'config', 'template', 'template_name', 'value',
            'source', 'computed_at',
        ]
        read_only_fields = ['computed_at']


# ──────────────────────────────────────────────
#  New Model Serializers
# ──────────────────────────────────────────────


class BomCandidatePartSerializer(serializers.ModelSerializer):
    """Serializer for BomCandidatePart."""

    part_name = serializers.CharField(source='part.name', read_only=True)
    parametric_bom_item_part = serializers.CharField(
        source='parametric_bom_item.bom_item.part.name', read_only=True
    )

    class Meta:
        """Meta options."""
        model = BomCandidatePart
        fields = [
            'id', 'parametric_bom_item', 'parametric_bom_item_part',
            'part', 'part_name', 'label',
            'condition_formula', 'priority',
        ]


class VariantMappingSerializer(serializers.ModelSerializer):
    """Serializer for VariantMapping."""

    template_part_name = serializers.CharField(
        source='template_part.name', read_only=True
    )
    parametric_bom_item_part = serializers.CharField(
        source='parametric_bom_item.bom_item.part.name', read_only=True
    )

    class Meta:
        """Meta options."""
        model = VariantMapping
        fields = [
            'id', 'parametric_bom_item', 'parametric_bom_item_part',
            'template_part', 'template_part_name',
            'param_mapping', 'variant_name_template', 'auto_generate',
        ]


class BomSpecificationSerializer(serializers.ModelSerializer):
    """Serializer for BomSpecification."""

    parametric_bom_item_part = serializers.CharField(
        source='parametric_bom_item.bom_item.part.name', read_only=True
    )

    class Meta:
        """Meta options."""
        model = BomSpecification
        fields = [
            'id', 'parametric_bom_item', 'parametric_bom_item_part',
            'spec_type', 'spec_fields',
            'drawing_ref_formula', 'unit_cost_formula', 'notes',
        ]


class SupplierSelectionRuleSerializer(serializers.ModelSerializer):
    """Serializer for SupplierSelectionRule."""

    supplier_part_name = serializers.CharField(
        source='supplier_part.', read_only=True
    )
    parametric_bom_item_part = serializers.CharField(
        source='parametric_bom_item.bom_item.part.name', read_only=True
    )

    class Meta:
        """Meta options."""
        model = SupplierSelectionRule
        fields = [
            'id', 'parametric_bom_item', 'parametric_bom_item_part',
            'supplier_part', 'supplier_part_name',
            'condition_formula', 'priority', 'label',
        ]


class InheritanceMappingSerializer(serializers.ModelSerializer):
    """Serializer for InheritanceMapping."""

    target_part_name = serializers.CharField(
        source='target_part.name', read_only=True
    )
    target_template_name = serializers.CharField(
        source='target_template.name', read_only=True
    )
    source_template_name = serializers.CharField(
        source='source_template.name', read_only=True, allow_null=True
    )

    class Meta:
        """Meta options."""
        model = InheritanceMapping
        fields = [
            'id', 'target_part', 'target_part_name',
            'target_template', 'target_template_name',
            'source_template', 'source_template_name',
            'formula', 'enabled',
        ]


class PartAttributeFormulaSerializer(serializers.ModelSerializer):
    """Serializer for PartAttributeFormula."""

    part_name = serializers.CharField(source='part.name', read_only=True)

    class Meta:
        """Meta options."""
        model = PartAttributeFormula
        fields = [
            'id', 'part', 'part_name',
            'attribute_name', 'attribute_type',
            'formula', 'unit', 'display_order',
        ]
