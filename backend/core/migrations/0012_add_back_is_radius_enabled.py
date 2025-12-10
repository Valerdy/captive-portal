# Generated manually on 2025-12-10
# Re-adds is_radius_enabled field to User model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_remove_user_is_radius_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_radius_enabled',
            field=models.BooleanField(
                default=True,
                help_text="Contrôle si l'utilisateur peut actuellement accéder au WiFi (toggle on/off)"
            ),
        ),
    ]
