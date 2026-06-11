"""Django views for the Parametric BOM configurator interface."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def configurator_view(request):
    """Render the comprehensive parametric BOM configurator single-page app.

    Supports ?product=<id> query parameter to auto-open a product detail page.
    """
    product_id = request.GET.get('product')
    context = {}
    if product_id:
        try:
            context['initial_product_id'] = int(product_id)
        except (ValueError, TypeError):
            pass
    return render(request, 'parametric_bom/configurator.html', context)
