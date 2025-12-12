# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_add_profile_usage_history_alerts'),
    ]

    operations = [
        # Create UserDisconnectionLog model
        migrations.CreateModel(
            name='UserDisconnectionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(
                    max_length=50,
                    choices=[
                        ('quota_exceeded', 'Quota de données dépassé'),
                        ('session_expired', 'Session expirée'),
                        ('daily_limit', 'Limite journalière atteinte'),
                        ('weekly_limit', 'Limite hebdomadaire atteinte'),
                        ('monthly_limit', 'Limite mensuelle atteinte'),
                        ('idle_timeout', 'Délai d\'inactivité dépassé'),
                        ('validity_expired', 'Durée de validité expirée'),
                        ('manual', 'Désactivation manuelle par admin'),
                    ],
                    help_text='Raison de la déconnexion'
                )),
                ('description', models.TextField(
                    blank=True,
                    help_text='Description détaillée de la raison (ex: "Quota dépassé: 55 Go / 50 Go")'
                )),
                ('disconnected_at', models.DateTimeField(
                    auto_now_add=True,
                    help_text='Date et heure de la déconnexion automatique'
                )),
                ('reconnected_at', models.DateTimeField(
                    null=True,
                    blank=True,
                    help_text='Date et heure de la réactivation (null si toujours déconnecté)'
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='True si la déconnexion est toujours active, False si l\'utilisateur a été réactivé'
                )),
                ('quota_used', models.BigIntegerField(
                    null=True,
                    blank=True,
                    help_text='Quota utilisé au moment de la déconnexion (en octets)'
                )),
                ('quota_limit', models.BigIntegerField(
                    null=True,
                    blank=True,
                    help_text='Limite de quota configurée (en octets)'
                )),
                ('session_duration', models.IntegerField(
                    null=True,
                    blank=True,
                    help_text='Durée de session au moment de la déconnexion (en secondes)'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='disconnection_logs',
                    to=settings.AUTH_USER_MODEL,
                    help_text='Utilisateur qui a été déconnecté'
                )),
                ('reconnected_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    blank=True,
                    related_name='reconnections_performed',
                    to=settings.AUTH_USER_MODEL,
                    help_text='Administrateur qui a réactivé l\'utilisateur'
                )),
            ],
            options={
                'verbose_name': 'Log de déconnexion',
                'verbose_name_plural': 'Logs de déconnexion',
                'db_table': 'user_disconnection_logs',
                'ordering': ['-disconnected_at'],
                'indexes': [
                    models.Index(fields=['user', 'is_active'], name='idx_user_active'),
                    models.Index(fields=['disconnected_at'], name='idx_disconnected_at'),
                    models.Index(fields=['reason'], name='idx_reason'),
                ],
            },
        ),
    ]
