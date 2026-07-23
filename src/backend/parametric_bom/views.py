"""Django views for the Parametric BOM configurator interface.

Supports multiple URL entry points via the ``page`` query parameter,
allowing the single-page app to open on the correct tab.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_sameorigin

# Valid page values and their human labels
VALID_PAGES = {
    'home': '首页',
    'products': '产品管理',
    'params': '参数设置',
    'bom': 'BOM公式',
    'config': '产品配置器',
    'projects': '项目管理',
    'project-detail': '项目详情',
}

# Map URL path names to page values
PATH_TO_PAGE = {
    'parametric-home': 'home',
    'parametric-products': 'products',
    'parametric-params': 'params',
    'parametric-bom': 'bom',
    'parametric-config': 'config',
}


@xframe_options_sameorigin
def configurator_view(request, page='home'):
    """Render the comprehensive parametric BOM configurator single-page app.

    Args:
        request: Django HTTP request
        page: Initial page/tab to display (default: 'home')

    Note: Does NOT use @login_required (which would 302-redirect in iframe).
    Returns a minimal placeholder if not authenticated — the SPA handles auth.
    """
    if not request.user.is_authenticated:
        return HttpResponse(
            '<div style="padding:2rem;text-align:center;color:#94a3b8">'
            '请先登录</div>'
        )

    product_id = request.GET.get('product')

    # Allow ?page= override in query string
    page = request.GET.get('page', page)

    # Embedded mode: hide own nav/sidebar (displayed inside InvenTree SPA iframe)
    embedded = request.GET.get('embedded', '0') == '1'

    if page not in VALID_PAGES:
        page = 'home'

    context = {
        'initial_page': page,
        'page_title': VALID_PAGES[page],
        'embedded': embedded,
    }

    if product_id:
        try:
            context['initial_product_id'] = int(product_id)
        except (ValueError, TypeError):
            pass

    return render(request, 'parametric_bom/configurator.html', context)


@xframe_options_sameorigin
def project_detail_view(request, project_id):
    """Render project detail page with independent URL.

    Args:
        request: Django HTTP request
        project_id: Project primary key

    Note: Does NOT use @login_required (which would 302-redirect in iframe).
    Returns a minimal placeholder if not authenticated — the SPA handles auth.
    """
    if not request.user.is_authenticated:
        return HttpResponse(
            '<div style="padding:2rem;text-align:center;color:#94a3b8">'
            '请先登录</div>'
        )
    embedded = request.GET.get('embedded', '0') == '1'
    context = {
        'initial_page': 'project-detail',
        'page_title': '项目详情',
        'initial_project_id': int(project_id),
        'embedded': embedded,
    }
    return render(request, 'parametric_bom/configurator.html', context)


@login_required
def product_standalone_view(request, pk):
    """Render a standalone product configuration page (no sidebar, no full layout).

    Used when clicking a product card opens in a new window/tab.

    Args:
        request: Django HTTP request
        pk: Product (Part) primary key
    """
    from part.models import Part
    from django.shortcuts import get_object_or_404
    part = get_object_or_404(Part, pk=pk)
    context = {
        'initial_page': 'products',
        'page_title': '产品配置',
        'initial_product_id': int(pk),
        'standalone': True,
        'product_image_url': '/api/parametric-bom/part-image/' + str(pk) + '/' if part.image else None,
    }
    return render(request, 'parametric_bom/configurator.html', context)

from django.http import JsonResponse

def parametric_bom_navigation(request):
    """Return navigation items for InvenTree web UI sidebar."""
    items = [
        {
            'key': 'parametric-bom',
            'title': '参数化BOM',
            'icon': 'ti:clipboard-data:outline',
            'options': {'url': '/parametric-bom/'},
            'feature_type': 'navigation',
            'plugin_name': 'parametric_bom',
        },
        {
            'key': 'parametric-bom-bom',
            'title': '  BOM公式',
            'icon': 'ti:function:outline',
            'options': {'url': '/parametric-bom/bom/'},
            'feature_type': 'navigation',
            'plugin_name': 'parametric_bom',
        },
        {
            'key': 'parametric-bom-params',
            'title': '  参数设置',
            'icon': 'ti:settings:outline',
            'options': {'url': '/parametric-bom/params/'},
            'feature_type': 'navigation',
            'plugin_name': 'parametric_bom',
        },
        {
            'key': 'parametric-bom-products',
            'title': '  产品管理',
            'icon': 'ti:package:outline',
            'options': {'url': '/parametric-bom/products/'},
            'feature_type': 'navigation',
            'plugin_name': 'parametric_bom',
        },
    ]
    return JsonResponse(items, safe=False)
