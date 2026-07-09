# Generated manually — fixes IntegrityError on ParametricBomItem creation.
# The name_formula column exists in MySQL (from a previously reverted migration
# 0021 that was applied but whose file was deleted). The column is NOT NULL
# with no default, causing IntegrityError on INSERT.
# This migration adds a default value to match the Python model.
from django.db import migrations


class Migration(migrations.Migration):
    """Fix name_formula column default to match Python model."""

    dependencies = [
        ('parametric_bom', '0020_seed_project_roles'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE parametric_bom_parametricbomitem
                ALTER COLUMN name_formula SET DEFAULT '';
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
