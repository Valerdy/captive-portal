# Migration to add validators to Profile and ProfileAlert models

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_enhance_blocked_site_for_mikrotik'),
    ]

    operations = [
        # Add validators to Profile bandwidth fields
        migrations.AlterField(
            model_name='profile',
            name='bandwidth_upload',
            field=models.IntegerField(
                default=5,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(1000),
                ],
                help_text='Bande passante upload en Mbps (1-1000 Mbps)',
            ),
        ),
        migrations.AlterField(
            model_name='profile',
            name='bandwidth_download',
            field=models.IntegerField(
                default=10,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(1000),
                ],
                help_text='Bande passante download en Mbps (1-1000 Mbps)',
            ),
        ),

        # Add validators to ProfileAlert threshold fields
        migrations.AlterField(
            model_name='profilealert',
            name='threshold_percent',
            field=models.IntegerField(
                default=80,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
                help_text='Seuil en pourcentage pour déclencher l\'alerte (0-100%)',
            ),
        ),
        migrations.AlterField(
            model_name='profilealert',
            name='threshold_days',
            field=models.IntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                ],
                help_text='Nombre de jours avant expiration pour déclencher l\'alerte (min: 1 jour)',
            ),
        ),
    ]
