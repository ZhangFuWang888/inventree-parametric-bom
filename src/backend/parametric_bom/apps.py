"""App configuration for the Parametric BOM plugin."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ParametricBomConfig(AppConfig):
    """Configuration for the Parametric BOM app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'parametric_bom'
    label = 'parametric_bom'
    verbose_name = _('Parametric BOM')

    def ready(self):
        """Import signal handlers when the app is ready."""
        from parametric_bom.signals import connect_signals
        connect_signals()
