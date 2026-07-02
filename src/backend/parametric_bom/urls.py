"""URL routing for the Parametric BOM plugin API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from parametric_bom.api import (
    BomCandidatePartViewSet,
    BomSpecificationViewSet,
    ConfigParameterValueViewSet,
    InheritanceMappingViewSet,
    ParametricBomItemViewSet,
    ParametricRuleViewSet,
    PartAttributeFormulaViewSet,
    PartParameterConfigViewSet,
    PartVariableViewSet,
    ProductConfigurationViewSet,
    VariantMappingViewSet,
    affected_variants,
    bom_evaluate,
    config_detail,
    config_set_params,
    config_snapshot,
    config_transition,
    create_bom_item,
    estimate_cost,
    export_attachment_zip,
    export_bom_csv,
    export_bundle_zip,
    formula_preview,
    formula_validate,
    generate_variant,
    generate_variant_from_params,
    inherit_params,
    rules_evaluate,
    template_library_auto_sync,
    template_library_bulk_assign,
    template_library_category_detail,
    template_library_sync,
)

router = DefaultRouter()
router.register(r'part-config', PartParameterConfigViewSet)
router.register(r'bom-item-config', ParametricBomItemViewSet)
router.register(r'rules', ParametricRuleViewSet)
router.register(r'configurations', ProductConfigurationViewSet)
router.register(r'config-values', ConfigParameterValueViewSet)
# New models
router.register(r'candidate-parts', BomCandidatePartViewSet)
router.register(r'variant-mappings', VariantMappingViewSet)
router.register(r'specifications', BomSpecificationViewSet)
router.register(r'inheritance', InheritanceMappingViewSet)
router.register(r'attributes', PartAttributeFormulaViewSet)
router.register(r'part-variables', PartVariableViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]

# Used by InvenTree's main urls.py: mounted under api/parametric-bom/
parametric_api_urls = [
    # Formula engine
    path('evaluate/', bom_evaluate, name='bom-evaluate'),
    path('estimate-cost/', estimate_cost, name='estimate-cost'),
    path('formula/validate/', formula_validate, name='formula-validate'),
    path('formula/preview/', formula_preview, name='formula-preview'),
    # Rules
    path('rules/evaluate/', rules_evaluate, name='rules-evaluate'),
    # Variant generator
    path('generate-variant/', generate_variant, name='generate-variant'),
    path('generate-variant-from-params/', generate_variant_from_params, name='generate-variant-from-params'),
    path('create-bom-item/', create_bom_item, name='create-bom-item'),
    # Parameter inheritance
    path('inherit/', inherit_params, name='inherit-params'),
    path('inherit/affected/<int:part_config_id>/', affected_variants, name='affected-variants'),
    # Template library
    path('template-library/sync/', template_library_sync, name='template-library-sync'),
    path('template-library/category/<int:category_id>/', template_library_category_detail, name='template-library-category-detail'),
    path('template-library/bulk-assign/', template_library_bulk_assign, name='template-library-bulk-assign'),
    path('template-library/auto-sync/', template_library_auto_sync, name='template-library-auto-sync'),
    # Configuration workflow
    path('configs/<int:config_id>/transition/', config_transition, name='config-transition'),
    path('configs/<int:config_id>/params/', config_set_params, name='config-set-params'),
    path('configs/<int:config_id>/snapshot/', config_snapshot, name='config-snapshot'),
    path('configs/<int:config_id>/detail/', config_detail, name='config-detail'),
    # Export
    path('export/bom-csv/', export_bom_csv, name='export-bom-csv'),
    path('export/attachment-zip/', export_attachment_zip, name='export-attachment-zip'),
    path('export/bundle-zip/', export_bundle_zip, name='export-bundle-zip'),
] + router.urls
