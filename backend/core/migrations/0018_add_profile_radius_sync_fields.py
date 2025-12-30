# Generated manually for Option C: Profile RADIUS sync control

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_add_validators_to_profile_and_alerts'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_radius_enabled',
            field=models.BooleanField(
                default=False,
                help_text="Si activé, le profil est synchronisé vers FreeRADIUS (radgroupreply)"
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='radius_group_name',
            field=models.CharField(
                blank=True,
                help_text="Nom du groupe RADIUS (généré automatiquement)",
                max_length=64,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='last_radius_sync',
            field=models.DateTimeField(
                blank=True,
                help_text="Date de la dernière synchronisation vers RADIUS",
                null=True
            ),
        ),
    ]
