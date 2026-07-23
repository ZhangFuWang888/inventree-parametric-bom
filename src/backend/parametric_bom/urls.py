"""URL routing for the Parametric BOM plugin API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from parametric_bom.api import (
    BomCandidatePartViewSet,
    BomSpecificationViewSet,
    ConfigParameterValueViewSet,
    InheritanceMappingViewSet,
    ParameterChangeLogViewSet,
    ParametricBomItemViewSet,
    ParametricRuleViewSet,
    ParametricSnapshotViewSet,
    PartAttributeFormulaViewSet,
    PartImageViewSet,
    PartLiteViewSet,
    PartParameterConfigViewSet,
    PartVariableViewSet,
    ProductConfigurationViewSet,
    ProjectViewSet,
    VariantMappingViewSet,
    affected_variants,
    bom_evaluate,
    bom_subparts,
    cart_add,
    cart_clear,
    cart_count,
    cart_create_order,
    cart_export_csv,
    cart_item_detail,
    cart_list,
    check_param_status,
    client_login,
    config_detail,
    config_set_params,
    config_snapshot,
    config_transition,
    create_bom_item,
    create_bom_items_batch,
    create_bom_items_from_excel,
    download_bom_import_template,
    batch_delete_bom_items,
    estimate_cost,
    export_attachment_zip,
    export_bom_csv,
    export_bundle_zip,
    formula_preview,
    formula_validate,
    generate_variant,
    generate_variant_from_params,
    inherit_params,
    param_references,
    rules_evaluate,
    template_library_auto_sync,
    template_library_bulk_assign,
    template_library_category_detail,
    template_library_sync,
)
from parametric_bom.api_params_io import export_params_excel, import_params_excel

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
router.register(r'projects', ProjectViewSet)
router.register(r'parts-lite', PartLiteViewSet, basename='part-lite')
router.register(r'part-image', PartImageViewSet, basename='part-image')
router.register(r'param-logs', ParameterChangeLogViewSet)
router.register(r'parametric-snapshots', ParametricSnapshotViewSet)

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
    path('create-bom-items-batch/', create_bom_items_batch, name='create-bom-items-batch'),
    path('create-bom-items-excel/', create_bom_items_from_excel, name='create-bom-items-excel'),
    path('bom-import-template/', download_bom_import_template, name='bom-import-template'),
    path('batch-delete-bom-items/', batch_delete_bom_items, name='batch-delete-bom-items'),
    # Parameter inheritance
    path('inherit/', inherit_params, name='inherit-params'),
    path('inherit/affected/<int:part_config_id>/', affected_variants, name='affected-variants'),
    # References
    path('param-references/', param_references, name='param-references'),
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
    # Parameter import/export
    path('export-params/', export_params_excel, name='export-params'),
    path('import-params/', import_params_excel, name='import-params'),
    # Cart
    path('cart/', cart_list, name='cart-list'),
    path('cart/add/', cart_add, name='cart-add'),
    path('cart/count/', cart_count, name='cart-count'),
    path('cart/clear/', cart_clear, name='cart-clear'),
    path('cart/<int:item_id>/', cart_item_detail, name='cart-item-detail'),
    # Cart → Order
    path('cart/export-csv/', cart_export_csv, name='cart-export-csv'),
    path('cart/create-order/', cart_create_order, name='cart-create-order'),
    # C# WinForms 客户端
    path('client-login/', client_login, name='client-login'),
    path('check-param-status/', check_param_status, name='check-param-status'),
    # BOM sub-parts (reference parts for formula editor)
    path('bom-subparts/', bom_subparts, name='bom-subparts'),
] + router.urls
