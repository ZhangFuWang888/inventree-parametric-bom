"""Django views for the Parametric BOM configurator interface."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def configurator_view(request):
    """Render the comprehensive parametric BOM configurator single-page app.

    This view delivers a self-contained HTML page that acts as a full-featured
    product configurator frontend, communicating with the Parametric BOM REST
    API endpoints (/api/parametric-bom/*) via fetch() and Django session auth.
    """
    return render(request, 'parametric_bom/configurator.html')
