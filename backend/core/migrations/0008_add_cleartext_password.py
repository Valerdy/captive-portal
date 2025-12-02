# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_remove_preregistration_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cleartext_password',
            field=models.CharField(
                blank=True,
                help_text='Mot de passe en clair (UNIQUEMENT pour activation RADIUS - RISQUE DE SÉCURITÉ)',
                max_length=128,
                null=True
            ),
        ),
    ]
