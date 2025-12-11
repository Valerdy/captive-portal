# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_add_back_is_radius_enabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text='Nom du profil (ex: Étudiant, Personnel, Invité)', max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text='Description du profil', null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Si désactivé, le profil ne peut pas être assigné')),
                ('bandwidth_upload', models.IntegerField(default=5120, help_text='Bande passante upload en Kbps (ex: 5120 = 5 Mbps)')),
                ('bandwidth_download', models.IntegerField(default=10240, help_text='Bande passante download en Kbps (ex: 10240 = 10 Mbps)')),
                ('quota_type', models.CharField(choices=[('unlimited', 'Illimité'), ('limited', 'Limité')], default='limited', help_text='Type de quota (illimité ou limité)', max_length=20)),
                ('data_volume', models.BigIntegerField(default=53687091200, help_text='Volume de données attribué en octets (ex: 53687091200 = 50 Go)')),
                ('validity_duration', models.IntegerField(choices=[(7, '7 jours'), (14, '14 jours'), (30, '30 jours'), (60, '60 jours'), (90, '90 jours'), (180, '180 jours'), (365, '365 jours')], default=30, help_text='Durée de validité du quota en jours')),
                ('session_timeout', models.IntegerField(default=28800, help_text='Durée maximale d\'une session en secondes (défaut: 8h)')),
                ('idle_timeout', models.IntegerField(default=600, help_text='Délai d\'inactivité avant déconnexion en secondes (défaut: 10min)')),
                ('simultaneous_use', models.IntegerField(default=1, help_text='Nombre de connexions simultanées autorisées')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, help_text='Administrateur ayant créé ce profil', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profiles_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profil',
                'verbose_name_plural': 'Profils',
                'db_table': 'profiles',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='promotion',
            name='profile',
            field=models.ForeignKey(blank=True, help_text='Profil RADIUS appliqué à tous les utilisateurs de cette promotion', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='promotions', to='core.profile'),
        ),
        migrations.AddField(
            model_name='user',
            name='profile',
            field=models.ForeignKey(blank=True, help_text='Profil RADIUS individuel (si non défini, utilise le profil de la promotion)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='core.profile'),
        ),
    ]
