"""Migration: Replace single `mode` field with independent enable_* booleans.

Version 0006 — 2026-06-11

Converts:
  mode='qty_formula'  → enable_qty_formula=True
  mode='conditional'  → enable_qty_formula=True, enable_conditional=True
  mode='candidate'     → enable_candidate=True
  mode='variant'      → enable_variant=True
  mode='specification' → enable_specification=True
  mode='supplier'     → enable_supplier=True
  mode='structure'    → enable_structure=True
  mode='standard'     → all False (no parametric behavior)
"""

from django.db import migrations, models


def convert_mode_to_flags(apps, schema_editor):
    """Convert existing mode values to enable_* boolean flags."""
    ParametricBomItem = apps.get_model('parametric_bom', 'ParametricBomItem')

    # Mode → flags mapping
    MODE_MAP = {
        'qty_formula':     {'enable_qty_formula': True},
        'conditional':     {'enable_qty_formula': True, 'enable_conditional': True},
        'candidate':       {'enable_candidate': True},
        'variant':         {'enable_variant': True},
        'specification':   {'enable_specification': True},
        'supplier':        {'enable_supplier': True},
        'structure':       {'enable_structure': True},
        'standard':        {},
    }

    for item in ParametricBomItem.objects.all():
        old_mode = item.mode or 'standard'
        flags = MODE_MAP.get(old_mode, {})
        for field, value in flags.items():
            setattr(item, field, value)
        item.save(update_fields=list(flags.keys()))


def reverse_conversion(apps, schema_editor):
    """Reconstruct mode from enable_* flags (lossy but usable)."""
    ParametricBomItem = apps.get_model('parametric_bom', 'ParametricBomItem')

    # Priority order: if multiple flags are set, pick the first match
    FLAG_TO_MODE = [
        (['enable_structure'], 'structure'),
        (['enable_supplier'], 'supplier'),
        (['enable_specification'], 'specification'),
        (['enable_variant'], 'variant'),
        (['enable_candidate'], 'candidate'),
        (['enable_conditional'], 'conditional'),
        (['enable_qty_formula'], 'qty_formula'),
    ]

    for item in ParametricBomItem.objects.all():
        new_mode = 'standard'
        for flags, mode in FLAG_TO_MODE:
            if any(getattr(item, f, False) for f in flags):
                new_mode = mode
                break
        item.mode = new_mode
        item.save(update_fields=['mode'])


class Migration(migrations.Migration):
    """Replace mode field with independent boolean flags."""

    dependencies = [
        ('parametric_bom', '0005_partparameterconfig_step_value'),
    ]

    operations = [
        # 1. Add boolean fields (allow null temporarily for existing rows)
        migrations.AddField(
            model_name='parametricbomitem',
            name='enable_qty_formula',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable qty formula',
                help_text='Use a formula to compute dynamic quantity',
            ),
        ),
        migrations.AddField(
            model_name='parametricbomitem',
            name='enable_conditional',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable conditional include',
                help_text='Use a condition formula to decide if this item is included',
            ),
        ),
        migrations.AddField(
            model_name='parametricbomitem',
            name='enable_candidate',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable candidate parts',
                help_text='Select from a list of candidate parts',
            ),
        ),
        migrations.AddField(
            model_name='parametricbomitem',
            name='enable_variant',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable variant generation',
                help_text='Generate a variant from a template part',
            ),
        ),
        migrations.AddField(
            model_name='parametricbomitem',
            name='enable_specification',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable specification',
                help_text='Outsource by specification description',
            ),
        ),
        migrations.AddField(
            model_name='parametricbomitem',
            name='enable_supplier',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable supplier selection',
                help_text='Select supplier dynamically',
            ),
        ),
        migrations.AddField(
            model_name='parametricbomitem',
            name='enable_structure',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable structure control',
                help_text='Control sub-assembly structure',
            ),
        ),
        # 2. Convert existing mode values to flags
        migrations.RunPython(convert_mode_to_flags, reverse_conversion),
        # 3. Remove the old mode field
        migrations.RemoveField(
            model_name='parametricbomitem',
            name='mode',
        ),
    ]
