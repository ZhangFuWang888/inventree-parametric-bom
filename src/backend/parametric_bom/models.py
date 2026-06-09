"""Models for the Parametric BOM plugin.

Phase 1 — Parameter Enhancement Module.

All models use OneToOne/ForeignKey to link to InvenTree core models,
never modifying them directly. This ensures compatibility with upstream
InvenTree upgrades.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

import structlog

logger = structlog.get_logger('inventree')


# ──────────────────────────────────────────────
#  Choice / Enum Helpers
# ──────────────────────────────────────────────

class ParamTypeChoices(models.TextChoices):
    """Data types for parameter values."""

    NUMBER = 'number', _('数值')
    OPTION = 'option', _('选项')
    MULTI_OPTION = 'multi_option', _('多选项')
    BOOLEAN = 'boolean', _('布尔')
    TEXT = 'text', _('文本')
    LONG_TEXT = 'long_text', _('长文本')
    FILE_REF = 'file_ref', _('文件引用')
    PART_REF = 'part_ref', _('零件引用')


class RuleTypeChoices(models.TextChoices):
    """Types of parametric rules."""

    CONSTRAINT = 'constraint', _('Constraint')
    CALCULATION = 'calculation', _('Calculation')
    VISIBILITY = 'visibility', _('Visibility')


class RuleActionChoices(models.TextChoices):
    """Actions a parametric rule can perform."""

    SET_VALUE = 'set_value', _('Set value')
    SET_MIN = 'set_min', _('Set minimum')
    SET_MAX = 'set_max', _('Set maximum')
    SHOW = 'show', _('Show')
    HIDE = 'hide', _('Hide')
    REQUIRE = 'require', _('Require')


class ParamSourceChoices(models.TextChoices):
    """Source of a configuration parameter value."""

    MANUAL = 'manual', _('Manual input')
    COMPUTED = 'computed', _('Computed by formula')
    INHERITED = 'inherited', _('Inherited from parent')
    DEFAULT = 'default', _('Default value')


class BomItemModeChoices(models.TextChoices):
    """How a parametric BOM item resolves its sub-part."""

    STANDARD = 'standard', _('Standard')
    QTY_FORMULA = 'qty_formula', _('Qty formula')
    CONDITIONAL = 'conditional', _('Conditional include')
    CANDIDATE_SELECT = 'candidate', _('Select from candidates')
    VARIANT_GENERATE = 'variant', _('Generate variant from template')
    SPECIFICATION = 'specification', _('Outsource by specification')
    SUPPLIER_SELECT = 'supplier', _('Select supplier')
    STRUCTURE = 'structure', _('Structure control')


class ConfigStatusChoices(models.TextChoices):
    """Status of a product configuration."""

    DRAFT = 'draft', _('Draft')
    COMPLETED = 'completed', _('Completed')
    RELEASED = 'released', _('Released')
    OBSOLETE = 'obsolete', _('Obsolete')


# ──────────────────────────────────────────────
#  Part → Parameter Template Link
# ──────────────────────────────────────────────

class PartParameterConfig(models.Model):
    """Enhanced parameter configuration for a specific Part.

    Associates a Part with a ParameterTemplate and adds configuration
    metadata: default values, ranges, UI hints, and whether the parameter
    is user-driven or formula-computed.

    This extends InvenTree's existing PartParameter model without
    modifying it — it stores additional config attributes that the
    parametric BOM system needs.
    """

    part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='parametric_configs',
        verbose_name=_('Part'),
        help_text=_('The part this parameter configuration belongs to'),
    )
    template = models.ForeignKey(
        'common.ParameterTemplate',
        on_delete=models.CASCADE,
        related_name='parametric_configs',
        verbose_name=_('Parameter template'),
        help_text=_('The parameter template this config is based on'),
    )
    parameter_type = models.CharField(
        max_length=20,
        choices=ParamTypeChoices.choices,
        default=ParamTypeChoices.NUMBER,
        verbose_name=_('Parameter type'),
        help_text=_('Data type of this parameter'),
    )
    default_value = models.CharField(
        max_length=128,
        blank=True,
        default='',
        verbose_name=_('Default value'),
        help_text=_('Default value when the parameter is not explicitly set'),
    )
    min_value = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Minimum value'),
        help_text=_('Minimum allowed value (numeric parameters only)'),
    )
    max_value = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Maximum value'),
        help_text=_('Maximum allowed value (numeric parameters only)'),
    )
    options = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Options'),
        help_text=_('List of valid options for dropdown/select parameters'),
    )
    is_driving = models.BooleanField(
        default=True,
        verbose_name=_('Driving parameter'),
        help_text=_('User/customer provides this value during configuration'),
    )
    is_computed = models.BooleanField(
        default=False,
        verbose_name=_('Computed parameter'),
        help_text=_('Calculated automatically by a formula'),
    )
    computation_formula = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name=_('Computation formula'),
        help_text=_(
            'Formula for computing this parameter value. '
            'Example: param.载重 * param.速度 / 0.85'
        ),
    )
    ui_hint = models.CharField(
        max_length=256,
        blank=True,
        default='',
        verbose_name=_('UI hint'),
        help_text=_('Hint text shown to the user during configuration'),
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name=_('Display order'),
        help_text=_('Order in the configuration UI (lower = earlier)'),
    )
    visible_on_config = models.BooleanField(
        default=True,
        verbose_name=_('Visible on configurator'),
        help_text=_('Show this parameter on the product configurator page'),
    )

    class Meta:
        """Meta options for PartParameterConfig."""
        app_label = 'parametric_bom'
        verbose_name = _('Part parameter config')
        verbose_name_plural = _('Part parameter configs')
        unique_together = [('part', 'template')]
        ordering = ['display_order', 'template']

    def __str__(self):
        """Human-readable representation."""
        return f'{self.part} → {self.template}'


# ──────────────────────────────────────────────
#  Parametric BOM Item
# ──────────────────────────────────────────────

class ParametricBomItem(models.Model):
    """Extends BomItem with formula-driven behaviour.

    Each ParametricBomItem links one-to-one with a BomItem and adds
    formula fields that override the static BomItem values.

    The `mode` field defines which part-resolution strategy to use:
      - standard:       Static item, no formulas
      - qty_formula:    Dynamic quantity only
      - conditional:    Qty + condition formula
      - candidate:      Select from BomCandidatePart list
      - variant:        Generate variant from template (VariantMapping)
      - specification:  Outsource by spec (BomSpecification)
      - supplier:       Select supplier (SupplierSelectionRule)
      - structure:      Structural sub-assembly control
    """

    bom_item = models.OneToOneField(
        'part.BomItem',
        on_delete=models.CASCADE,
        related_name='parametric_config',
        verbose_name=_('BOM item'),
        help_text=_('The BOM item this parametric configuration extends'),
    )
    mode = models.CharField(
        max_length=32,
        choices=BomItemModeChoices.choices,
        default=BomItemModeChoices.QTY_FORMULA,
        verbose_name=_('Part mode'),
        help_text=_('How this BOM item resolves its sub-part'),
    )
    qty_formula = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name=_('Quantity formula'),
        help_text=_(
            'Formula for dynamic quantity. '
            'Example: CEIL(param.长度 / 500) * 2'
        ),
    )
    condition_formula = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name=_('Condition formula'),
        help_text=_(
            'Boolean formula that determines if this item is included. '
            'Empty = always included. Example: param.速度 > 15'
        ),
    )
    part_selector_formula = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name=_('Part selector formula'),
        help_text=_(
            'Formula to dynamically select which sub-part to use. '
            'Example: IF(param.speed>15, "MOTOR-A", "MOTOR-B")'
        ),
    )
    formular_hash = models.CharField(
        max_length=64,
        blank=True,
        default='',
        verbose_name=_('Formula hash'),
        help_text=_('SHA-256 hash of all three formulas for change detection'),
        editable=False,
    )

    class Meta:
        """Meta options for ParametricBomItem."""
        app_label = 'parametric_bom'
        verbose_name = _('Parametric BOM item')
        verbose_name_plural = _('Parametric BOM items')

    def __str__(self):
        """Human-readable representation."""
        return f'Parametric: {self.bom_item}'

    def has_formula(self) -> bool:
        """Check if any formula is defined."""
        return bool(self.qty_formula or self.condition_formula or self.part_selector_formula)

    def save(self, *args, **kwargs):
        """Auto-compute formula hash on save."""
        import hashlib

        raw = f'{self.qty_formula}|{self.condition_formula}|{self.part_selector_formula}'
        self.formular_hash = hashlib.sha256(raw.encode()).hexdigest()[:64]
        super().save(*args, **kwargs)


# ──────────────────────────────────────────────
#  Parametric Rule
# ──────────────────────────────────────────────

class ParametricRule(models.Model):
    """Business rule applied during product configuration.

    Rules can constrain parameter values, compute derived parameters,
    control visibility of options, or enforce prerequisites.

    Examples:
      - If length > 8000, require reinforced frame (constraint)
      - Motor power = load * speed / 0.85 (calculation)
      - If speed <= 10, hide high-speed option (visibility)
    """

    product_part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='parametric_rules',
        verbose_name=_('Product part'),
        help_text=_('The parametric product template this rule applies to'),
    )
    rule_type = models.CharField(
        max_length=32,
        choices=RuleTypeChoices.choices,
        default=RuleTypeChoices.CONSTRAINT,
        verbose_name=_('Rule type'),
    )
    condition_formula = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name=_('Condition formula'),
        help_text=_(
            'Formula that triggers this rule. '
            'Leave empty for always-active rules. '
            'Example: param.长度 > 8000'
        ),
    )
    target_param = models.ForeignKey(
        'common.ParameterTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parametric_rules',
        verbose_name=_('Target parameter'),
        help_text=_('Parameter this rule affects'),
    )
    action = models.CharField(
        max_length=32,
        choices=RuleActionChoices.choices,
        default=RuleActionChoices.SET_VALUE,
        verbose_name=_('Action'),
        help_text=_('What action to perform when the condition is met'),
    )
    value_formula = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name=_('Value formula'),
        help_text=_(
            'Formula computing the value for set_value / set_min / set_max actions'
        ),
    )
    error_message = models.CharField(
        max_length=256,
        blank=True,
        default='',
        verbose_name=_('Error message'),
        help_text=_(
            'User-facing message when a constraint rule is violated'
        ),
    )
    priority = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0)],
        verbose_name=_('Priority'),
        help_text=_('Rule evaluation priority (lower = evaluated first)'),
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name=_('Enabled'),
    )

    class Meta:
        """Meta options for ParametricRule."""
        app_label = 'parametric_bom'
        verbose_name = _('Parametric rule')
        verbose_name_plural = _('Parametric rules')
        ordering = ['product_part', 'priority']

    def __str__(self):
        """Human-readable representation."""
        return f'Rule[{self.get_rule_type_display()}] {self.condition_formula or "always"} → {self.action}'


# ──────────────────────────────────────────────
#  Product Configuration
# ──────────────────────────────────────────────

class ProductConfiguration(models.Model):
    """A complete product configuration record.

    Captures all parameter values, computed BOM, and cost for a single
    configured product instance. Each configuration is based on a
    parametric template part.
    """

    template_part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='product_configurations',
        verbose_name=_('Template part'),
        help_text=_('The parametric product template used for this configuration'),
    )
    title = models.CharField(
        max_length=128,
        verbose_name=_('Title'),
        help_text=_('Human-friendly name for this configuration'),
    )
    revision = models.CharField(
        max_length=32,
        blank=True,
        default='1.0',
        verbose_name=_('Revision'),
    )
    status = models.CharField(
        max_length=32,
        choices=ConfigStatusChoices.choices,
        default=ConfigStatusChoices.DRAFT,
        verbose_name=_('Status'),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parametric_configurations',
        verbose_name=_('Created by'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created at'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated at'),
    )
    params_snapshot = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Parameter snapshot'),
        help_text=_('Full parameter name-value map at configuration time'),
    )
    generated_bom = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Generated BOM'),
        help_text=_('Generated BOM snapshot after parameter evaluation'),
    )
    total_cost = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Total cost'),
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Notes'),
    )

    class Meta:
        """Meta options for ProductConfiguration."""
        app_label = 'parametric_bom'
        verbose_name = _('Product configuration')
        verbose_name_plural = _('Product configurations')
        ordering = ['-created_at']

    def __str__(self):
        """Human-readable representation."""
        return f'{self.title} (rev {self.revision})'


# ──────────────────────────────────────────────
#  Configuration Parameter Value
# ──────────────────────────────────────────────

class ConfigParameterValue(models.Model):
    """A single parameter value within a product configuration.

    Tracks the value, source (manual/computed/inherited/default), and
    computation timestamp for each parameter in a configuration.
    """

    config = models.ForeignKey(
        ProductConfiguration,
        on_delete=models.CASCADE,
        related_name='parameter_values',
        verbose_name=_('Configuration'),
    )
    template = models.ForeignKey(
        'common.ParameterTemplate',
        on_delete=models.CASCADE,
        verbose_name=_('Parameter template'),
    )
    value = models.CharField(
        max_length=128,
        blank=True,
        default='',
        verbose_name=_('Value'),
    )
    source = models.CharField(
        max_length=32,
        choices=ParamSourceChoices.choices,
        default=ParamSourceChoices.MANUAL,
        verbose_name=_('Source'),
        help_text=_('How this value was determined'),
    )
    computed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Computed at'),
    )

    class Meta:
        """Meta options for ConfigParameterValue."""
        app_label = 'parametric_bom'
        verbose_name = _('Configuration parameter value')
        verbose_name_plural = _('Configuration parameter values')
        unique_together = [('config', 'template')]

    def __str__(self):
        """Human-readable representation."""
        return f'{self.template.name} = {self.value} ({self.get_source_display()})'


# ──────────────────────────────────────────────
#  BomCandidatePart — 场景3: 候选零件选择
# ──────────────────────────────────────────────


class BomCandidatePart(models.Model):
    """A candidate sub-part that a parametric BOM item can select from.

    Multiple candidates can be linked to one ParametricBomItem. During
    configuration, the system evaluates each candidate's condition formula
    in priority order and selects the first match.

    This replaces the free-text part_selector_formula with an explicit
    list of valid choices, making the system easier to manage.
    """

    parametric_bom_item = models.ForeignKey(
        ParametricBomItem,
        on_delete=models.CASCADE,
        related_name='candidate_parts',
        verbose_name=_('Parametric BOM item'),
        help_text=_('The parametric BOM item this candidate belongs to'),
    )
    part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='bom_candidates',
        verbose_name=_('Candidate part'),
        help_text=_('The part to use when this candidate is selected'),
    )
    label = models.CharField(
        max_length=128,
        blank=True,
        default='',
        verbose_name=_('Label'),
        help_text=_('Short descriptive label shown in the UI (e.g. "小电机")'),
    )
    condition_formula = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name=_('Condition formula'),
        help_text=_(
            'Formula that determines if this candidate is selected. '
            'Leave empty for always-available. '
            'Example: param.载重 <= 1000'
        ),
    )
    priority = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0)],
        verbose_name=_('Priority'),
        help_text=_('Lower values are checked first (0 = highest priority)'),
    )

    class Meta:
        """Meta options for BomCandidatePart."""
        app_label = 'parametric_bom'
        verbose_name = _('Candidate part')
        verbose_name_plural = _('Candidate parts')
        ordering = ['parametric_bom_item', 'priority']

    def __str__(self):
        """Human-readable representation."""
        label = self.label or self.part.name
        return f'[{self.priority}] {label}'


# ──────────────────────────────────────────────
#  VariantMapping — 场景4: 动态生成变体
# ──────────────────────────────────────────────


class VariantMapping(models.Model):
    """Maps a parametric BOM item to a template part for variant generation.

    When a product is configured, the system:
    1. Evaluates each param_mapping formula to compute concrete values
    2. Looks for an existing variant with matching parameters
    3. Creates a new Part variant if none exists
    4. Links the generated variant into the expanded BOM

    This handles the "infinite specifications" use case — parts like
    arbitrarily long beams, custom-height columns, etc.
    """

    parametric_bom_item = models.OneToOneField(
        ParametricBomItem,
        on_delete=models.CASCADE,
        related_name='variant_mapping',
        verbose_name=_('Parametric BOM item'),
        help_text=_('The parametric BOM item this variant mapping belongs to'),
    )
    template_part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='variant_mappings',
        verbose_name=_('Template part'),
        help_text=_(
            'The parametric template part to generate variants from. '
            'This part should have is_template=True.'
        ),
    )
    param_mapping = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Parameter mapping'),
        help_text=_(
            'JSON dict mapping template parameter names → formulas. '
            'Example: {"高度": "parent.货架高度", "材质": "\'Q235\'"}'
        ),
    )
    variant_name_template = models.CharField(
        max_length=256,
        blank=True,
        default='',
        verbose_name=_('Variant name template'),
        help_text=_(
            'Template for the generated variant name. Use {param_name} '
            'syntax. Example: "立柱-H{高度}" → "立柱-H2800"'
        ),
    )
    auto_generate = models.BooleanField(
        default=True,
        verbose_name=_('Auto-generate'),
        help_text=_(
            'Automatically create the variant part when the configuration '
            'is completed. Disable for manual generation only.'
        ),
    )

    class Meta:
        """Meta options for VariantMapping."""
        app_label = 'parametric_bom'
        verbose_name = _('Variant mapping')
        verbose_name_plural = _('Variant mappings')

    def __str__(self):
        """Human-readable representation."""
        tmpl = self.variant_name_template or '(auto)'
        return f'{self.template_part.name} → {tmpl}'


# ──────────────────────────────────────────────
#  BomSpecification — 场景5: 规格描述(外协件)
# ──────────────────────────────────────────────


class BomSpecification(models.Model):
    """Describes a non-stocked / outsource part using parametric specs.

    Instead of linking to a concrete Part, the BOM item carries a set
    of parametric specification fields that tell the workshop or supplier
    exactly what to make. No Part record is created — the spec IS the part.
    """

    parametric_bom_item = models.OneToOneField(
        ParametricBomItem,
        on_delete=models.CASCADE,
        related_name='specification',
        verbose_name=_('Parametric BOM item'),
        help_text=_('The parametric BOM item this specification describes'),
    )
    spec_type = models.CharField(
        max_length=64,
        default='custom',
        verbose_name=_('Specification type'),
        help_text=_(
            'Type of specification (e.g. "outsource", "raw_material", "custom")'
        ),
    )
    spec_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Specification fields'),
        help_text=_(
            'List of {name, formula, unit} dicts defining the specs. '
            'Example: [{"name": "材质", "formula": "\'Q235\'"}, '
            '{"name": "长度", "formula": "parent.货架高度+100", "unit": "mm"}]'
        ),
    )
    drawing_ref_formula = models.CharField(
        max_length=256,
        blank=True,
        default='',
        verbose_name=_('Drawing reference formula'),
        help_text=_(
            'Formula for auto-generating the drawing number. '
            'Example: \'DWG-\' + param.订单号'
        ),
    )
    unit_cost_formula = models.CharField(
        max_length=256,
        blank=True,
        default='',
        verbose_name=_('Unit cost formula'),
        help_text=_(
            'Formula estimating the unit cost. '
            'Example: param.长度 * 0.035 + 25'
        ),
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Notes'),
        help_text=_('Additional processing notes for the workshop'),
    )

    class Meta:
        """Meta options for BomSpecification."""
        app_label = 'parametric_bom'
        verbose_name = _('BOM specification')
        verbose_name_plural = _('BOM specifications')

    def __str__(self):
        """Human-readable representation."""
        return f'Spec: {self.spec_type} ({len(self.spec_fields)} fields)'


# ──────────────────────────────────────────────
#  SupplierSelectionRule — 场景6: 供应商选择
# ──────────────────────────────────────────────


class SupplierSelectionRule(models.Model):
    """Defines which supplier to use based on configuration parameters.

    Multiple rules can exist per BOM item. During evaluation, the system
    checks rules in priority order and picks the first matching supplier.
    """

    parametric_bom_item = models.ForeignKey(
        ParametricBomItem,
        on_delete=models.CASCADE,
        related_name='supplier_rules',
        verbose_name=_('Parametric BOM item'),
        help_text=_('The parametric BOM item this rule applies to'),
    )
    supplier_part = models.ForeignKey(
        'company.SupplierPart',
        on_delete=models.CASCADE,
        related_name='parametric_rules',
        verbose_name=_('Supplier part'),
        help_text=_('The supplier part to use when this rule matches'),
    )
    condition_formula = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name=_('Condition formula'),
        help_text=_(
            'Formula that triggers this supplier selection. '
            'Empty = always use. Example: param.数量 > 1000'
        ),
    )
    priority = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0)],
        verbose_name=_('Priority'),
        help_text=_('Lower values are checked first (0 = highest priority)'),
    )
    label = models.CharField(
        max_length=128,
        blank=True,
        default='',
        verbose_name=_('Label'),
        help_text=_('Short label shown in UI (e.g. "批量价", "零售价")'),
    )

    class Meta:
        """Meta options for SupplierSelectionRule."""
        app_label = 'parametric_bom'
        verbose_name = _('Supplier selection rule')
        verbose_name_plural = _('Supplier selection rules')
        ordering = ['parametric_bom_item', 'priority']

    def __str__(self):
        """Human-readable representation."""
        return f'[{self.priority}] {self.label or self.supplier_part}'


# ──────────────────────────────────────────────
#  InheritanceMapping — 场景9: 参数继承配置
# ──────────────────────────────────────────────


class InheritanceMapping(models.Model):
    """Configures how a parameter flows from parent assembly to child part.

    During BOM expansion, the bom_expander evaluates inheritance mappings
    to pass relevant parameters from the parent context down to child parts.

    By default, parameters flow automatically via the `parent.*` context
    in the formula engine. This model allows explicit configuration of
    which parameters inherit, with optional transformation formulas.
    """

    target_part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='inheritance_mappings',
        verbose_name=_('Target part'),
        help_text=_('The child part that receives the inherited parameter'),
    )
    target_template = models.ForeignKey(
        'common.ParameterTemplate',
        on_delete=models.CASCADE,
        related_name='inheritance_targets',
        verbose_name=_('Target parameter'),
        help_text=_('The parameter on the target part to receive the value'),
    )
    source_template = models.ForeignKey(
        'common.ParameterTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inheritance_sources',
        verbose_name=_('Source parameter'),
        help_text=_(
            'The source parameter on the parent. Leave empty to use '
            'parent. source_template.name'
        ),
    )
    formula = models.CharField(
        max_length=256,
        blank=True,
        default='',
        verbose_name=_('Formula'),
        help_text=_(
            'Optional transformation formula. Use parent.xxx for parent '
            'params, param.xxx for own params. '
            'Default: parent.source_template.name'
        ),
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name=_('Enabled'),
    )

    class Meta:
        """Meta options for InheritanceMapping."""
        app_label = 'parametric_bom'
        verbose_name = _('Inheritance mapping')
        verbose_name_plural = _('Inheritance mappings')
        unique_together = [('target_part', 'target_template')]

    def __str__(self):
        """Human-readable representation."""
        source = self.source_template.name if self.source_template else '(auto)'
        return f'{source} → {self.target_part}.{self.target_template.name}'


# ──────────────────────────────────────────────
#  PartAttributeFormula — 场景11: 零件属性公式
# ──────────────────────────────────────────────


class PartAttributeFormula(models.Model):
    """Defines computed attributes on a part that vary with parameters.

    Attributes like weight, color code, inspection standard, or packaging
    spec that depend on configuration parameters. The system evaluates
    the formula for each attribute during BOM expansion and includes
    the results in the expanded BOM output.
    """

    part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='attribute_formulas',
        verbose_name=_('Part'),
        help_text=_('The part this attribute formula belongs to'),
    )
    attribute_name = models.CharField(
        max_length=64,
        verbose_name=_('Attribute name'),
        help_text=_(
            'Name of the attribute (e.g. "weight", "color_code", '
            '"inspection_standard")'
        ),
    )
    attribute_type = models.CharField(
        max_length=20,
        choices=ParamTypeChoices.choices,
        default=ParamTypeChoices.TEXT,
        verbose_name=_('Attribute type'),
        help_text=_('Data type of this attribute value'),
    )
    formula = models.CharField(
        max_length=512,
        verbose_name=_('Formula'),
        help_text=_(
            'Formula that computes this attribute. '
            'Example: param.长度 * param.宽度 * 5 * 7.85 / 1000000'
        ),
    )
    unit = models.CharField(
        max_length=32,
        blank=True,
        default='',
        verbose_name=_('Unit'),
        help_text=_('Unit of measurement (e.g. "kg", "mm", "pcs")'),
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name=_('Display order'),
        help_text=_('Order in the attribute list (lower = earlier)'),
    )

    class Meta:
        """Meta options for PartAttributeFormula."""
        app_label = 'parametric_bom'
        verbose_name = _('Part attribute formula')
        verbose_name_plural = _('Part attribute formulas')
        unique_together = [('part', 'attribute_name')]
        ordering = ['part', 'display_order']

    def __str__(self):
        """Human-readable representation."""
        return f'{self.part.name}.{self.attribute_name}'
