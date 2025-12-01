# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_add_promotion_matricule_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_radius_activated',
            field=models.BooleanField(default=False, help_text='Utilisateur activé dans RADIUS par un administrateur'),
        ),
    ]
