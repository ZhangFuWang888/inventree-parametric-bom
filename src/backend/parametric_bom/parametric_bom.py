"""Main plugin class for Parametric BOM.

Uses AppMixin to register as a full Django app with its own models,
URLs, settings, and navigation.
"""

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import AppMixin, SettingsMixin, UrlsMixin


class ParametricBomPlugin(AppMixin, SettingsMixin, UrlsMixin, InvenTreePlugin):
    """Parametric BOM plugin for InvenTree.

    Adds formula-driven BOM items, product configuration, parameter
    templates, and rule engine support to InvenTree.
    """

    NAME = 'ParametricBomPlugin'
    SLUG = 'parametric_bom'
    TITLE = _('Parametric BOM')
    DESCRIPTION = _(
        'Extends InvenTree with parametric/configure-to-order BOM management. '
        'Allows formula-driven quantities, conditional line items, product '
        'configuration, parameter templates, and rule-based constraints.'
    )
    AUTHOR = 'LiXin Intelligent Technology'
    VERSION = '0.1.0'
    PUBLISHER = 'LiXin Intelligent Technology'

    # Admin URL configuration
    NAVIGATION_TAB_NAME = TITLE
    NAVIGATION_TAB_ICON = 'fas fa-cogs'

    SETTINGS = {
        'FORMULA_TIMEOUT': {
            'name': _('Formula calculation timeout (ms)'),
            'description': _('Maximum time allowed for a single formula evaluation'),
            'default': 500,
            'validator': int,
            'units': 'ms',
        },
        'FORMULA_MAX_RECURSION': {
            'name': _('Max recursion depth'),
            'description': _('Maximum recursion depth for formula evaluation'),
            'default': 20,
            'validator': int,
        },
        'ENABLE_PARAM_INHERITANCE': {
            'name': _('Enable parameter inheritance'),
            'description': _(
                'Automatically pass parent parameters to child BOM levels'
            ),
            'default': True,
            'validator': bool,
        },
    }

    def setup_urls(self):
        """Register plugin URLs."""
        from django.urls import include, path

        return [
            path(
                'parametric_bom/',
                include('parametric_bom.urls'),
                name='parametric_bom',
            ),
        ]
