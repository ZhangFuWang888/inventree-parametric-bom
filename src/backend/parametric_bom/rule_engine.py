"""Rule Engine Service — Evaluate parametric rules against product configurations.

Takes a ProductConfiguration (or Part + params dict), fetches all enabled
ParametricRules for that part ordered by priority, evaluates each rule's
condition_formula, and performs the action when the condition is met.

Actions:
  - SET_VALUE: Override the parameter value with computed value
  - SET_MIN:   Enforce a minimum value constraint
  - SET_MAX:   Enforce a maximum value constraint
  - SHOW:      Mark a parameter as visible
  - HIDE:      Mark a parameter as hidden
  - REQUIRE:   Add a validation requirement (e.g., param must have a value)

Phase 2 — Rule Engine Module.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import structlog

from parametric_bom.formula_engine import evaluate as eval_formula
from parametric_bom.formula_engine.errors import (
    EvaluationError,
    ParseError,
    ReferenceError,
    TimeoutError as FormulaTimeoutError,
)

logger = structlog.get_logger('inventree')

# ──────────────────────────────────────────────
#  Type Aliases
# ──────────────────────────────────────────────

ParamMap = Dict[str, Any]


# ──────────────────────────────────────────────
#  Response structure
# ──────────────────────────────────────────────


class RuleEvaluationResult:
    """Result of evaluating all rules for a configuration."""

    def __init__(self):
        self.valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.constraints: List[Dict[str, Any]] = []
        self.param_overrides: Dict[str, Any] = {}
        self.param_visibility: Dict[str, bool] = {}
        self.param_requirements: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict for API responses."""
        return {
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'constraints': self.constraints,
            'param_overrides': self.param_overrides,
            'param_visibility': self.param_visibility,
            'param_requirements': self.param_requirements,
        }


# ──────────────────────────────────────────────
#  Core: Evaluate rules for a part + params
# ──────────────────────────────────────────────


def evaluate_rules(
    part,
    params: ParamMap,
    timeout_ms: int = 500,
) -> Dict[str, Any]:
    """Evaluate all enabled ParametricRules for a given part and parameter context.

    Args:
        part: A Part model instance (the product template).
        params: Dict of param_name → value (user-provided + computed).
        timeout_ms: Max evaluation time per formula (ms).

    Returns:
        Dict with keys:
            valid (bool):          True if no errors and all constraints satisfied.
            errors (list[str]):    Fatal evaluation errors.
            warnings (list[str]):  Non-fatal warnings.
            constraints (list[dict]): Constraint violations with messages.
            param_overrides (dict): Action SET_VALUE / SET_MIN / SET_MAX overrides.
            param_visibility (dict): Action SHOW / HIDE results {param_name: visible}.
            param_requirements (list[str]): Parameter names that REQUIRE a value.
    """
    from parametric_bom.models import ParametricRule

    result = RuleEvaluationResult()

    # Fetch all enabled rules for this part, ordered by priority
    rules = ParametricRule.objects.filter(
        product_part=part,
        enabled=True,
    ).select_related('target_param').order_by('priority')

    if not rules.exists():
        logger.info('No parametric rules found for part', part_id=part.pk)
        return result.to_dict()

    # Build evaluation context — use computed params including overrides as they accumulate
    eval_context: ParamMap = dict(params)

    for rule in rules:
        try:
            _evaluate_single_rule(rule, eval_context, result, timeout_ms)
        except (ParseError, ReferenceError, EvaluationError, FormulaTimeoutError) as e:
            result.errors.append(
                f"Rule #{rule.pk} ({rule.get_rule_type_display()}): {e}"
            )
            # Accumulate overrides back into eval_context for subsequent rules
            _merge_overrides(eval_context, result)
            continue

        # Merge overrides into eval_context so later rules see computed values
        _merge_overrides(eval_context, result)

    # Determine overall validity
    if result.errors:
        result.valid = False

    return result.to_dict()


def _merge_overrides(eval_context: ParamMap, result: RuleEvaluationResult) -> None:
    """Merge param_overrides into the evaluation context."""
    for key, value in result.param_overrides.items():
        eval_context[key] = value


def _evaluate_single_rule(
    rule,
    context: ParamMap,
    result: RuleEvaluationResult,
    timeout_ms: int,
) -> None:
    """Evaluate a single ParametricRule instance.

    Args:
        rule: ParametricRule model instance.
        context: Current parameter context (includes prior overrides).
        result: RuleEvaluationResult being accumulated.
        timeout_ms: Formula evaluation timeout.
    """
    from parametric_bom.formula_engine import evaluate as eval_formula

    # 1) Evaluate condition formula
    condition_met = _evaluate_condition(rule, context, timeout_ms)

    if condition_met is None:
        # Condition evaluation failed — skip this rule with a warning
        result.warnings.append(
            f"Rule #{rule.pk}: condition evaluation skipped due to error"
        )
        return

    if not condition_met:
        # Condition not satisfied — skip this rule
        return

    # 2) Condition is met — execute the action
    target_name = rule.target_param.name if rule.target_param else None

    if rule.action == 'set_value':
        _action_set_value(rule, target_name, context, result, timeout_ms)

    elif rule.action == 'set_min':
        _action_set_min(rule, target_name, context, result, timeout_ms)

    elif rule.action == 'set_max':
        _action_set_max(rule, target_name, context, result, timeout_ms)

    elif rule.action == 'show':
        _action_show(target_name, result)

    elif rule.action == 'hide':
        _action_hide(target_name, result)

    elif rule.action == 'require':
        _action_require(target_name, result)

    else:
        result.warnings.append(
            f"Rule #{rule.pk}: unknown action '{rule.action}'"
        )


def _evaluate_condition(
    rule,
    context: ParamMap,
    timeout_ms: int,
) -> Optional[bool]:
    """Evaluate the condition formula of a rule.

    Returns:
        True if condition is met, False if not met.
        None if condition formula is empty (always active) or on error.
    """
    formula = rule.condition_formula

    # Empty formula = always active
    if not formula or not formula.strip():
        return None  # signals "always active"

    try:
        raw_result = eval_formula(
            formula,
            context={'param': context},
            timeout_ms=timeout_ms,
        )
        return bool(raw_result)
    except (ParseError, ReferenceError, EvaluationError, FormulaTimeoutError) as e:
        logger.warning(
            'Rule condition evaluation failed',
            rule_id=rule.pk,
            formula=formula,
            error=str(e),
        )
        return None


# ──────────────────────────────────────────────
#  Action Implementations
# ──────────────────────────────────────────────


def _action_set_value(
    rule,
    target_name: Optional[str],
    context: ParamMap,
    result: RuleEvaluationResult,
    timeout_ms: int,
) -> None:
    """SET_VALUE: Override parameter value with computed formula result."""
    if not target_name:
        result.errors.append(f"Rule #{rule.pk}: SET_VALUE requires a target_param")
        return

    if not rule.value_formula or not rule.value_formula.strip():
        result.errors.append(
            f"Rule #{rule.pk}: SET_VALUE requires a value_formula"
        )
        return

    try:
        computed = eval_formula(
            rule.value_formula,
            context={'param': context},
            timeout_ms=timeout_ms,
        )
        result.param_overrides[target_name] = computed
        logger.debug(
            'Rule SET_VALUE',
            rule_id=rule.pk,
            target=target_name,
            value=computed,
        )
    except (ParseError, ReferenceError, EvaluationError, FormulaTimeoutError) as e:
        result.errors.append(
            f"Rule #{rule.pk} SET_VALUE ({target_name}): {e}"
        )


def _action_set_min(
    rule,
    target_name: Optional[str],
    context: ParamMap,
    result: RuleEvaluationResult,
    timeout_ms: int,
) -> None:
    """SET_MIN: Enforce a minimum value constraint.

    If the current parameter value is below the computed minimum, record
    a constraint violation.
    """
    if not target_name:
        result.errors.append(f"Rule #{rule.pk}: SET_MIN requires a target_param")
        return

    if not rule.value_formula or not rule.value_formula.strip():
        result.errors.append(
            f"Rule #{rule.pk}: SET_MIN requires a value_formula"
        )
        return

    try:
        min_val = eval_formula(
            rule.value_formula,
            context={'param': context},
            timeout_ms=timeout_ms,
        )
        min_val = float(min_val)

        current_val = context.get(target_name)
        if current_val is not None:
            try:
                current_num = float(current_val)
                if current_num < min_val:
                    constraint = {
                        'rule_id': rule.pk,
                        'param': target_name,
                        'message': rule.error_message or (
                            f'{target_name} must be at least {min_val} '
                            f'(current: {current_num})'
                        ),
                        'min_value': min_val,
                        'current_value': current_num,
                    }
                    result.constraints.append(constraint)
                    result.valid = False
            except (ValueError, TypeError):
                pass

        result.param_overrides[f'{target_name}__min'] = min_val

    except (ParseError, ReferenceError, EvaluationError, FormulaTimeoutError) as e:
        result.errors.append(
            f"Rule #{rule.pk} SET_MIN ({target_name}): {e}"
        )


def _action_set_max(
    rule,
    target_name: Optional[str],
    context: ParamMap,
    result: RuleEvaluationResult,
    timeout_ms: int,
) -> None:
    """SET_MAX: Enforce a maximum value constraint."""
    if not target_name:
        result.errors.append(f"Rule #{rule.pk}: SET_MAX requires a target_param")
        return

    if not rule.value_formula or not rule.value_formula.strip():
        result.errors.append(
            f"Rule #{rule.pk}: SET_MAX requires a value_formula"
        )
        return

    try:
        max_val = eval_formula(
            rule.value_formula,
            context={'param': context},
            timeout_ms=timeout_ms,
        )
        max_val = float(max_val)

        current_val = context.get(target_name)
        if current_val is not None:
            try:
                current_num = float(current_val)
                if current_num > max_val:
                    constraint = {
                        'rule_id': rule.pk,
                        'param': target_name,
                        'message': rule.error_message or (
                            f'{target_name} must be at most {max_val} '
                            f'(current: {current_num})'
                        ),
                        'max_value': max_val,
                        'current_value': current_num,
                    }
                    result.constraints.append(constraint)
                    result.valid = False
            except (ValueError, TypeError):
                pass

        result.param_overrides[f'{target_name}__max'] = max_val

    except (ParseError, ReferenceError, EvaluationError, FormulaTimeoutError) as e:
        result.errors.append(
            f"Rule #{rule.pk} SET_MAX ({target_name}): {e}"
        )


def _action_show(target_name: Optional[str], result: RuleEvaluationResult) -> None:
    """SHOW: Mark a parameter as visible."""
    if not target_name:
        result.warnings.append("SHOW action requires a target_param")
        return
    result.param_visibility[target_name] = True


def _action_hide(target_name: Optional[str], result: RuleEvaluationResult) -> None:
    """HIDE: Mark a parameter as hidden."""
    if not target_name:
        result.warnings.append("HIDE action requires a target_param")
        return
    result.param_visibility[target_name] = False


def _action_require(target_name: Optional[str], result: RuleEvaluationResult) -> None:
    """REQUIRE: Record that a parameter must have a value."""
    if not target_name:
        result.warnings.append("REQUIRE action requires a target_param")
        return
    result.param_requirements.append(target_name)


# ──────────────────────────────────────────────
#  Convenience: Evaluate from config
# ──────────────────────────────────────────────


def evaluate_config_rules(
    config,
    timeout_ms: int = 500,
) -> Dict[str, Any]:
    """Evaluate all rules for a ProductConfiguration.

    Args:
        config: A ProductConfiguration instance.
        timeout_ms: Formula evaluation timeout.

    Returns:
        Same dict as evaluate_rules().
    """
    from parametric_bom.models import ConfigParameterValue

    template_part = config.template_part

    # Collect parameter values from the configuration
    params: ParamMap = {}
    param_values = ConfigParameterValue.objects.filter(
        config=config,
    ).select_related('template')

    for pv in param_values:
        params[pv.template.name] = _coerce_param_value(pv.value)

    return evaluate_rules(template_part, params, timeout_ms)


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────


def _coerce_param_value(val: Any) -> Any:
    """Coerce a raw value to a reasonable Python type."""
    if val is None:
        return None
    if isinstance(val, (int, float, bool)):
        return val
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        # Try integer
        try:
            return int(val)
        except ValueError:
            pass
        # Try float
        try:
            return float(val)
        except ValueError:
            pass
        # Try boolean
        if val.lower() in ('true', 'yes', '1'):
            return True
        if val.lower() in ('false', 'no', '0'):
            return False
    return val
