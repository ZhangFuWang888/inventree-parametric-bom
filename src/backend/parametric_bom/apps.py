"""App configuration for the Parametric BOM plugin."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ParametricBomConfig(AppConfig):
    """Configuration for the Parametric BOM app."""

    name = 'parametric_bom'
    label = 'parametric_bom'
    verbose_name = _('Parametric BOM')
