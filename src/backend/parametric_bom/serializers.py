"""API serializers for Parametric BOM models."""

from rest_framework import serializers

from parametric_bom.formula_engine import evaluate as evaluate_formula
from parametric_bom.formula_engine.errors import EvaluationError, ParseError, ReferenceError
from parametric_bom.models import (
    BomCandidatePart,
    BomItemModeChoices,
    BomSpecification,
    CartItem,
    ConfigParameterValue,
    InheritanceMapping,
    ParametricBomItem,
    ParametricRule,
    PartAttributeFormula,
    PartParameterConfig,
    PartVariable,
    ProductConfiguration,
    PROJECT_PERMISSIONS,
    Project,
    ProjectItem,
    ProjectMembership,
    ProjectRole,
    VariantMapping,
    get_user_role_info,
)


class PartParameterConfigSerializer(serializers.ModelSerializer):
    """Serializer for PartParameterConfig."""

    part_name = serializers.CharField(source='part.name', read_only=True)
    template_name = serializers.SerializerMethodField()

    def get_template_name(self, obj):
        if obj.name:
            return obj.name
        if obj.template:
            return obj.template.name
        return ''

    class Meta:
        """Meta options."""
        model = PartParameterConfig
        fields = [
            'id', 'part', 'part_name', 'template', 'template_name',
            'name', 'parameter_type', 'options',
            'default_value', 'min_value', 'max_value', 'step_value',
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
    active_modes = serializers.SerializerMethodField()

    def get_active_modes(self, obj):
        """Return a list of enabled mode names."""
        modes = []
        mapping = [
            ('enable_qty_formula', 'qty_formula'),
            ('enable_conditional', 'conditional'),
            ('enable_candidate', 'candidate'),
            ('enable_variant', 'variant'),
            ('enable_specification', 'specification'),
            ('enable_structure', 'structure'),
        ]
        for field, mode_name in mapping:
            if getattr(obj, field, False):
                modes.append(mode_name)
        return modes

    class Meta:
        """Meta options."""
        model = ParametricBomItem
        fields = [
            'id', 'bom_item', 'part_name', 'sub_part_name',
            'enable_qty_formula', 'enable_conditional', 'enable_candidate',
            'enable_variant',
            'enable_specification', 'enable_structure',
            'has_formula', 'active_modes',
            'name_formula', 'qty_formula', 'condition_formula',
            'reference_formula', 'price_formula', 'param_mapping',
            'formular_hash', 'has_formula', 'active_modes',
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
    template_part_ipn = serializers.CharField(
        source='template_part.IPN', read_only=True
    )
    parametric_bom_item_part = serializers.CharField(
        source='parametric_bom_item.bom_item.part.name', read_only=True
    )

    class Meta:
        """Meta options."""
        model = VariantMapping
        fields = [
            'id', 'parametric_bom_item', 'parametric_bom_item_part',
            'template_part', 'template_part_name', 'template_part_ipn',
            'param_mapping', 'variant_name_template', 'variant_ipn_template',
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


class PartVariableSerializer(serializers.ModelSerializer):
    """Serializer for PartVariable."""

    part_name = serializers.CharField(source='part.name', read_only=True)
    computed_value = serializers.SerializerMethodField()

    class Meta:
        """Meta options."""
        model = PartVariable
        fields = [
            'id', 'part', 'part_name',
            'name', 'formula', 'description',
            'display_order', 'created_at', 'updated_at',
            'computed_value',
        ]

    def get_computed_value(self, obj):
        """Evaluate the variable's formula with default parameter values."""
        if not obj.formula:
            return None
        try:
            # Build default parameter context for the part
            configs = PartParameterConfig.objects.filter(part=obj.part)
            param_ctx = {}
            for cfg in configs:
                param_name = cfg.name or (cfg.template.name if cfg.template else '')
                if param_name and cfg.default_value:
                    val = cfg.default_value
                    # Try numeric conversion
                    try:
                        if '.' in val:
                            val = float(val)
                        else:
                            val = int(val)
                    except (ValueError, TypeError):
                        pass
                    param_ctx[param_name] = val
            result = evaluate_formula(obj.formula, {'param': param_ctx})
            return str(result) if result is not None else None
        except (EvaluationError, ParseError, ReferenceError, Exception):
            return None


# ── Cart Serializers ─────────────────────────


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for CartItem."""

    product_part_name = serializers.CharField(
        source='product_part.name', read_only=True, default=None
    )
    product_part_ipn = serializers.CharField(
        source='product_part.IPN', read_only=True, default=None
    )
    part_name = serializers.CharField(
        source='part.name', read_only=True, default=None
    )
    part_ipn = serializers.CharField(
        source='part.IPN', read_only=True, default=None
    )
    part_unit = serializers.CharField(
        source='part.units', read_only=True, default=None
    )
    total_cost = serializers.SerializerMethodField(read_only=True)

    def get_total_cost(self, obj):
        # For parametric items with BOM snapshot, calculate from tree × quantity
        if obj.item_type == 'parametric' and obj.bom_snapshot:
            try:
                return _sum_tree_prices(obj.bom_snapshot) * (obj.quantity or 1)
            except Exception:
                pass
        # Fallback: unit_price * quantity
        if obj.unit_price is not None:
            return float(obj.unit_price) * (obj.quantity or 1)
        return None


    class Meta:
        model = CartItem
        fields = [
            'id', 'user', 'session_key', 'item_type',
            'product_part', 'product_part_name', 'product_part_ipn',
            'parameters', 'bom_snapshot',
            'part', 'part_name', 'part_ipn', 'part_unit',
            'title', 'quantity', 'unit_price', 'total_cost', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'total_cost', 'created_at', 'updated_at']


def _sum_tree_prices(node) -> float:
    """Recursively sum total_price from a BOM expansion tree."""
    total = float(node.get('total_price') or 0)
    for child in node.get('children', []):
        total += _sum_tree_prices(child)
    return total


# ── Project Serializers ──────────────────────

class ProjectItemSerializer(serializers.ModelSerializer):
    """Serializer for ProjectItem."""

    part_name = serializers.CharField(source='part.name', read_only=True, default=None)
    part_ipn = serializers.CharField(source='part.IPN', read_only=True, default=None)
    config_title = serializers.CharField(
        source='product_config.title', read_only=True, default=None
    )
    created_by_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.get_full_name() or obj.created_by.username

    def get_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return 'none'
        return get_user_role_info(obj.project, request.user).get('role', 'none')

    class Meta:
        model = ProjectItem
        fields = [
            'id', 'project', 'item_type',
            'product_config', 'config_title',
            'part', 'part_name', 'part_ipn',
            'title', 'quantity', 'bom_snapshot',
            'unit_cost', 'unit_price', 'notes',
            'sort_order', 'batch_name', 'created_by_name',
            'created_at', 'user_role',
        ]
        read_only_fields = ['created_at']


class ProjectListSerializer(serializers.ModelSerializer):
    """Compact serializer for project list views."""

    customer_name = serializers.CharField(
        source='customer.name', read_only=True, default=None
    )
    owner_name = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()

    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username if obj.owner else None

    def get_item_count(self, obj):
        return obj.items.count()

    def get_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return 'none'
        return get_user_role_info(obj, request.user).get('role', 'none')

    def get_user_permissions(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return []
        return get_user_role_info(obj, request.user).get('permissions', [])

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'project_code', 'customer', 'customer_name',
            'status', 'owner', 'owner_name', 'manager', 'deadline',
            'is_public', 'item_count', 'user_role', 'user_permissions',
            'created_at', 'updated_at', 'is_active',
        ]
        read_only_fields = ['project_code', 'created_at', 'updated_at', 'is_active']


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Full serializer for project detail views."""

    customer_name = serializers.CharField(
        source='customer.name', read_only=True, default=None
    )
    owner_name = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    items = ProjectItemSerializer(many=True, read_only=True)
    user_role = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()

    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username if obj.owner else None

    def get_manager_name(self, obj):
        return obj.manager.get_full_name() or obj.manager.username if obj.manager else None

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username if obj.created_by else None

    def get_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return 'none'
        return get_user_role_info(obj, request.user).get('role', 'none')

    def get_user_permissions(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return []
        return get_user_role_info(obj, request.user).get('permissions', [])

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'project_code', 'customer', 'customer_name',
            'status', 'description',
            'owner', 'owner_name', 'members', 'is_public',
            'manager', 'manager_name', 'deadline',
            'created_by', 'created_by_name',
            'created_at', 'updated_at', 'is_active',
            'items', 'user_role', 'user_permissions',
        ]
        read_only_fields = [
            'project_code', 'created_by', 'created_at',
            'updated_at', 'items', 'user_role',
        ]


class FromCartSerializer(serializers.Serializer):
    """Serializer for converting cart items into a project."""

    name = serializers.CharField(max_length=256)
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    cart_item_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
    deadline = serializers.DateField(required=False, allow_null=True)


# ── RBAC Serializers ─────────────────────────

class ProjectRoleSerializer(serializers.ModelSerializer):
    """Serializer for ProjectRole."""

    permission_labels = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectRole
        fields = [
            'id', 'project', 'name', 'permissions', 'permission_labels',
            'is_preset', 'member_count',
        ]
        read_only_fields = ['project', 'is_preset']

    def get_permission_labels(self, obj):
        from parametric_bom.models import PROJECT_PERMISSIONS
        perm_dict = dict(PROJECT_PERMISSIONS)
        return {p: perm_dict.get(p, p) for p in obj.permissions}

    def get_member_count(self, obj):
        return obj.memberships.count()


class ProjectMembershipSerializer(serializers.ModelSerializer):
    """Serializer for ProjectMembership."""

    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    role_name = serializers.CharField(source='role.name', read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMembership
        fields = [
            'id', 'project', 'user', 'user_name', 'user_email',
            'role', 'role_name', 'permissions', 'created_at',
        ]
        read_only_fields = ['project', 'created_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_email(self, obj):
        return obj.user.email

    def get_permissions(self, obj):
        return obj.role.permissions
