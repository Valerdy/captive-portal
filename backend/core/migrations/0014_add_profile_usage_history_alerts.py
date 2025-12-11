# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_add_profile_model'),
    ]

    operations = [
        # Add periodic limits to Profile model
        migrations.AddField(
            model_name='profile',
            name='daily_limit',
            field=models.BigIntegerField(blank=True, default=5368709120, help_text='Limite journalière en octets (ex: 5368709120 = 5 Go)', null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='weekly_limit',
            field=models.BigIntegerField(blank=True, default=32212254720, help_text='Limite hebdomadaire en octets (ex: 32212254720 = 30 Go)', null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='monthly_limit',
            field=models.BigIntegerField(blank=True, default=128849018880, help_text='Limite mensuelle en octets (ex: 128849018880 = 120 Go)', null=True),
        ),

        # Create UserProfileUsage model
        migrations.CreateModel(
            name='UserProfileUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('used_today', models.BigIntegerField(default=0, help_text='Consommation aujourd\'hui en octets')),
                ('used_week', models.BigIntegerField(default=0, help_text='Consommation cette semaine en octets')),
                ('used_month', models.BigIntegerField(default=0, help_text='Consommation ce mois en octets')),
                ('used_total', models.BigIntegerField(default=0, help_text='Consommation totale depuis l\'activation du profil actuel en octets')),
                ('last_daily_reset', models.DateTimeField(default=django.utils.timezone.now, help_text='Date du dernier reset journalier')),
                ('last_weekly_reset', models.DateTimeField(default=django.utils.timezone.now, help_text='Date du dernier reset hebdomadaire')),
                ('last_monthly_reset', models.DateTimeField(default=django.utils.timezone.now, help_text='Date du dernier reset mensuel')),
                ('activation_date', models.DateTimeField(default=django.utils.timezone.now, help_text='Date d\'activation du profil actuel (pour validity_duration)')),
                ('is_exceeded', models.BooleanField(default=False, help_text='True si un quota est dépassé')),
                ('is_active', models.BooleanField(default=True, help_text='Active le suivi de consommation')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(help_text='Utilisateur dont on suit la consommation', on_delete=django.db.models.deletion.CASCADE, related_name='profile_usage', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Utilisation de profil',
                'verbose_name_plural': 'Utilisations de profils',
                'db_table': 'user_profile_usage',
                'ordering': ['-created_at'],
            },
        ),

        # Create ProfileHistory model
        migrations.CreateModel(
            name='ProfileHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changed_at', models.DateTimeField(default=django.utils.timezone.now, help_text='Date du changement')),
                ('reason', models.TextField(blank=True, help_text='Raison du changement (optionnel)', null=True)),
                ('change_type', models.CharField(choices=[('assigned', 'Assignation'), ('updated', 'Modification'), ('removed', 'Suppression')], default='assigned', help_text='Type de changement', max_length=20)),
                ('user', models.ForeignKey(help_text='Utilisateur dont le profil a été modifié', on_delete=django.db.models.deletion.CASCADE, related_name='profile_history', to=settings.AUTH_USER_MODEL)),
                ('old_profile', models.ForeignKey(blank=True, help_text='Ancien profil (null si premier profil)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='history_as_old', to='core.profile')),
                ('new_profile', models.ForeignKey(blank=True, help_text='Nouveau profil (null si suppression)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='history_as_new', to='core.profile')),
                ('changed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profile_changes_made', help_text='Administrateur qui a effectué le changement', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Historique de profil',
                'verbose_name_plural': 'Historiques de profils',
                'db_table': 'profile_history',
                'ordering': ['-changed_at'],
            },
        ),

        # Create ProfileAlert model
        migrations.CreateModel(
            name='ProfileAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_type', models.CharField(choices=[('quota_warning', 'Avertissement quota'), ('quota_critical', 'Quota critique'), ('expiry_warning', 'Avertissement expiration'), ('expiry_imminent', 'Expiration imminente')], help_text='Type d\'alerte', max_length=20)),
                ('threshold_percent', models.IntegerField(default=80, help_text='Seuil en pourcentage pour déclencher l\'alerte (ex: 80 = alerte à 80%)')),
                ('threshold_days', models.IntegerField(blank=True, help_text='Nombre de jours avant expiration pour déclencher l\'alerte (pour expiry alerts)', null=True)),
                ('notification_method', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS'), ('system', 'Notification système'), ('all', 'Tous les canaux')], default='system', help_text='Méthode de notification', max_length=20)),
                ('is_active', models.BooleanField(default=True, help_text='Active ou désactive cette alerte')),
                ('message_template', models.TextField(blank=True, help_text='Template du message (peut contenir {username}, {percent}, {remaining_gb}, etc.)', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('profile', models.ForeignKey(help_text='Profil concerné par l\'alerte', on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='core.profile')),
                ('created_by', models.ForeignKey(blank=True, help_text='Administrateur ayant créé cette alerte', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alerts_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Alerte de profil',
                'verbose_name_plural': 'Alertes de profils',
                'db_table': 'profile_alerts',
                'ordering': ['-created_at'],
                'unique_together': {('profile', 'alert_type', 'threshold_percent')},
            },
        ),
    ]
