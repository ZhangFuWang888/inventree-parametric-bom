# Generated migration - add supplier_part_id to ProjectItem

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parametric_bom', '0035_part_snapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectitem',
            name='supplier_part_id',
            field=models.IntegerField(
                blank=True,
                help_text='Selected supplier part for this item; editable until batch is completed',
                null=True,
                verbose_name='Supplier part ID',
            ),
        ),
    ]
