"""Configuration workflow service — manages the config lifecycle.

Provides the business logic for:
  - Status transitions (draft → completed → released → obsolete)
  - Parameter CRUD within a configuration
  - Batch set parameters from a dict
  - Lock/unlock checking based on status
  - Snapshot of current parameter values
  - Full configuration detail with params, BOM, cost, rules
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils import timezone

import structlog

from parametric_bom.models import (
    ConfigParameterValue,
    ConfigStatusChoices,
    ParametricRule,
    ParametricBomItem,
    ProductConfiguration,
)

logger = structlog.get_logger('inventree')


# ──────────────────────────────────────────────
#  Status Transition Logic
# ──────────────────────────────────────────────

# Allowed transitions: current_status → {set of allowed next statuses}
_ALLOWED_TRANSITIONS = {
    ConfigStatusChoices.DRAFT: {ConfigStatusChoices.COMPLETED},
    ConfigStatusChoices.COMPLETED: {ConfigStatusChoices.RELEASED},
    ConfigStatusChoices.RELEASED: {ConfigStatusChoices.OBSOLETE},
    ConfigStatusChoices.OBSOLETE: set(),  # terminal state
}


def _validate_transition(
    current: str,
    target: str,
) -> Optional[str]:
    """Check whether moving from *current* to *target* is allowed.

    Returns an error message string if invalid, or None if allowed.
    """
    allowed = _ALLOWED_TRANSITIONS.get(current)
    if allowed is None:
        return f"Unknown current status '{current}'."
    if target not in allowed:
        return (
            f"Cannot transition from '{current}' to '{target}'. "
            f"Allowed targets from '{current}': "
            f"{', '.join(sorted(allowed)) or '(none — terminal state)'}."
        )
    return None


def transition_status(
    config: ProductConfiguration,
    new_status: str,
) -> Dict[str, Any]:
    """Transition *config* to *new_status*.

    Returns a dict:
        success (bool)
        config (dict) — serialized config (id, title, status, …)
        error  (str)  — error message on failure
    """
    from parametric_bom.serializers import ProductConfigurationSerializer

    error = _validate_transition(config.status, new_status)
    if error:
        logger.warning("config_transition_denied", config_id=config.pk, error=error)
        return {"success": False, "error": error}

    old_status = config.status
    config.status = new_status
    config.save(update_fields=["status", "updated_at"])

    logger.info(
        "config_transitioned",
        config_id=config.pk,
        from_status=old_status,
        to_status=new_status,
    )

    serializer = ProductConfigurationSerializer(config)
    return {"success": True, "config": serializer.data}


def status_is_locked(status: str) -> bool:
    """Return True if a configuration at *status* should be read-only."""
    return status in {
        ConfigStatusChoices.COMPLETED,
        ConfigStatusChoices.RELEASED,
        ConfigStatusChoices.OBSOLETE,
    }


def can_edit_parameters(config: ProductConfiguration) -> bool:
    """Return True if parameters can be edited in this config's status."""
    return config.status == ConfigStatusChoices.DRAFT


def can_delete(config: ProductConfiguration) -> bool:
    """Return True if the config can be deleted."""
    return config.status == ConfigStatusChoices.DRAFT


# ──────────────────────────────────────────────
#  Parameter CRUD
# ──────────────────────────────────────────────


def set_parameters(
    config: ProductConfiguration,
    params_dict: Dict[str, str],
) -> Dict[str, Any]:
    """Batch-set parameter values on *config*.

    *params_dict* maps parameter template names -> values.
    Works only for draft configurations.

    Creates new ConfigParameterValue rows or updates existing ones.

    Returns:
        success (bool)
        parameters (list) — current parameter values after update
        error (str)       — error message on failure
    """
    if not can_edit_parameters(config):
        return {
            "success": False,
            "error": (
                f"Cannot edit parameters — configuration status is "
                f"'{config.status}'. Only 'draft' configurations "
                f"accept parameter changes."
            ),
        }

    from common.models import ParameterTemplate

    results: List[Dict[str, Any]] = []
    errors: List[str] = []

    template_names = list(params_dict.keys())
    templates = {
        t.name: t
        for t in ParameterTemplate.objects.filter(name__in=template_names)
    }

    with transaction.atomic():
        for name, value in params_dict.items():
            template = templates.get(name)
            if template is None:
                errors.append(f"Parameter template '{name}' not found.")
                continue

            param_value, _created = ConfigParameterValue.objects.update_or_create(
                config=config,
                template=template,
                defaults={
                    "value": str(value) if value is not None else "",
                    "source": "manual",
                },
            )
            results.append(
                {
                    "template_name": name,
                    "template_id": template.pk,
                    "value": param_value.value,
                    "source": param_value.source,
                    "created": _created,
                }
            )

    if errors:
        logger.warning(
            "config_set_params_partial",
            config_id=config.pk,
            errors=errors,
        )

    return {
        "success": len(errors) == 0,
        "parameters": results,
        "errors": errors if errors else None,
    }


def delete_parameter(config: ProductConfiguration, template_id: int) -> Dict[str, Any]:
    """Delete a single parameter value from a draft configuration.

    Args:
        config: The ProductConfiguration instance.
        template_id: PK of the ParameterTemplate to remove.

    Returns:
        success (bool)
        error (str, optional)
    """
    if not can_edit_parameters(config):
        return {
            "success": False,
            "error": f"Cannot delete parameters in status '{config.status}'.",
        }

    deleted, _ = ConfigParameterValue.objects.filter(
        config=config,
        template_id=template_id,
    ).delete()

    if deleted == 0:
        return {
            "success": False,
            "error": f"Parameter with template_id={template_id} not found.",
        }

    return {"success": True, "deleted": True}


# ──────────────────────────────────────────────
#  Snapshot
# ──────────────────────────────────────────────


def snapshot_parameters(config: ProductConfiguration) -> Dict[str, Any]:
    """Snapshot current parameter values into *config.params_snapshot*.

    Returns:
        success (bool)
        snapshot (dict | None)
        error (str, optional)
    """
    qs = ConfigParameterValue.objects.filter(config=config).select_related("template")
    snapshot = {pv.template.name: pv.value for pv in qs}

    config.params_snapshot = snapshot
    config.save(update_fields=["params_snapshot", "updated_at"])

    logger.info("config_snapshot_taken", config_id=config.pk, count=len(snapshot))

    return {"success": True, "snapshot": snapshot}


# ──────────────────────────────────────────────
#  Configuration Detail
# ──────────────────────────────────────────────


def get_configuration_detail(config_id: int) -> Dict[str, Any]:
    """Fetch full detail for a configuration by ID.

    Returns:
        success (bool)
        config (dict)       — serialized ProductConfiguration
        parameters (list)   — all ConfigParameterValue rows
        bom (dict | None)   — generated BOM snapshot
        cost (str | None)   — total cost as string
        rules (list)        — applicable ParametricRule rows
        error (str, optional)
    """
    from parametric_bom.serializers import (
        ConfigParameterValueSerializer,
        ProductConfigurationSerializer,
    )

    try:
        config = ProductConfiguration.objects.select_related(
            "template_part",
            "created_by",
        ).prefetch_related(
            "parameter_values__template",
        ).get(pk=config_id)
    except ProductConfiguration.DoesNotExist:
        return {"success": False, "error": f"Configuration {config_id} not found."}

    # Serialize config
    config_ser = ProductConfigurationSerializer(config).data

    # Serialize parameters
    params_qs = (
        ConfigParameterValue.objects
        .filter(config=config)
        .select_related("template")
        .order_by("template__name")
    )
    params_ser = ConfigParameterValueSerializer(params_qs, many=True).data

    # Applicable rules (based on template_part)
    rules_qs = ParametricRule.objects.filter(
        product_part=config.template_part,
        enabled=True,
    ).select_related("target_param").order_by("priority")

    rules_data = [
        {
            "id": r.pk,
            "rule_type": r.rule_type,
            "condition_formula": r.condition_formula,
            "target_param": r.target_param_id,
            "target_param_name": r.target_param.name if r.target_param else None,
            "action": r.action,
            "value_formula": r.value_formula,
            "error_message": r.error_message,
            "priority": r.priority,
        }
        for r in rules_qs
    ]

    return {
        "success": True,
        "config": config_ser,
        "parameters": params_ser,
        "parameter_count": len(params_ser),
        "bom": config.generated_bom,
        "cost": str(config.total_cost) if config.total_cost is not None else None,
        "rules": rules_data,
        "status": config.status,
        "is_locked": status_is_locked(config.status),
        "can_edit": can_edit_parameters(config),
        "can_delete": can_delete(config),
    }
