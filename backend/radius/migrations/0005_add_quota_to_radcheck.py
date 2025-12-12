# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radius', '0004_add_statut_to_radcheck'),
    ]

    operations = [
        migrations.AddField(
            model_name='radcheck',
            name='quota',
            field=models.BigIntegerField(
                blank=True,
                help_text='Quota de données en octets (ex: 53687091200 = 50 Go). NULL = illimité',
                null=True
            ),
        ),
    ]
