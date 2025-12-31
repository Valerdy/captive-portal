# Generated manually for Fixes #7, #10, #12
# - AdminAuditLog: Journalisation des actions administrateur
# - SyncFailureLog: Suivi des échecs de synchronisation RADIUS/MikroTik

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_add_profile_radius_sync_fields'),
    ]

    operations = [
        # AdminAuditLog - Fix #10: Journalisation d'audit
        migrations.CreateModel(
            name='AdminAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admin_username', models.CharField(help_text="Username de l'admin (conservé si user supprimé)", max_length=150)),
                ('admin_ip', models.GenericIPAddressField(blank=True, help_text="Adresse IP de l'administrateur", null=True)),
                ('action_type', models.CharField(
                    choices=[
                        ('user_radius_activate', 'Activation RADIUS utilisateur'),
                        ('user_radius_deactivate', 'Désactivation RADIUS utilisateur'),
                        ('user_radius_reactivate', 'Réactivation RADIUS utilisateur'),
                        ('user_radius_sync', 'Synchronisation RADIUS utilisateur'),
                        ('profile_radius_enable', 'Activation RADIUS profil'),
                        ('profile_radius_disable', 'Désactivation RADIUS profil'),
                        ('profile_radius_sync', 'Synchronisation RADIUS profil'),
                        ('profile_create', 'Création profil'),
                        ('profile_update', 'Modification profil'),
                        ('profile_delete', 'Suppression profil'),
                        ('promotion_activate', 'Activation promotion'),
                        ('promotion_deactivate', 'Désactivation promotion'),
                        ('bulk_radius_enable', 'Activation RADIUS en masse'),
                        ('bulk_radius_disable', 'Désactivation RADIUS en masse'),
                        ('bulk_user_activate', 'Activation utilisateurs en masse'),
                        ('bulk_user_deactivate', 'Désactivation utilisateurs en masse'),
                        ('voucher_create', 'Création voucher'),
                        ('voucher_revoke', 'Révocation voucher'),
                        ('blocked_site_add', 'Ajout site bloqué'),
                        ('blocked_site_remove', 'Suppression site bloqué'),
                    ],
                    db_index=True,
                    help_text="Type d'action effectuée",
                    max_length=50
                )),
                ('severity', models.CharField(
                    choices=[
                        ('info', 'Information'),
                        ('warning', 'Avertissement'),
                        ('critical', 'Critique'),
                    ],
                    default='info',
                    help_text='Niveau de sévérité',
                    max_length=20
                )),
                ('target_model', models.CharField(help_text='Modèle cible (User, Profile, Promotion, etc.)', max_length=50)),
                ('target_id', models.IntegerField(blank=True, help_text="ID de l'objet cible", null=True)),
                ('target_repr', models.CharField(help_text='Représentation textuelle de la cible', max_length=255)),
                ('details', models.JSONField(default=dict, help_text="Détails de l'action (paramètres, résultats)")),
                ('success', models.BooleanField(default=True, help_text="L'action a-t-elle réussi?")),
                ('error_message', models.TextField(blank=True, help_text="Message d'erreur si échec", null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('admin_user', models.ForeignKey(
                    help_text="Administrateur ayant effectué l'action",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': "Log d'audit admin",
                'verbose_name_plural': "Logs d'audit admin",
                'db_table': 'admin_audit_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='adminauditlog',
            index=models.Index(fields=['action_type', 'created_at'], name='admin_audit_action__9a3f54_idx'),
        ),
        migrations.AddIndex(
            model_name='adminauditlog',
            index=models.Index(fields=['admin_user', 'created_at'], name='admin_audit_admin_u_5e7c91_idx'),
        ),
        migrations.AddIndex(
            model_name='adminauditlog',
            index=models.Index(fields=['target_model', 'target_id'], name='admin_audit_target__3d2a8e_idx'),
        ),

        # SyncFailureLog - Fix #7, #12: Suivi des échecs de sync
        migrations.CreateModel(
            name='SyncFailureLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_type', models.CharField(
                    choices=[
                        ('radius_user', 'Utilisateur → RADIUS'),
                        ('radius_profile', 'Profil → RADIUS Group'),
                        ('radius_group', 'Utilisateur → RADIUS Group'),
                        ('mikrotik_user', 'Utilisateur → MikroTik'),
                        ('mikrotik_profile', 'Profil → MikroTik'),
                        ('mikrotik_dns', 'Site bloqué → MikroTik DNS'),
                    ],
                    db_index=True,
                    max_length=30
                )),
                ('source_model', models.CharField(max_length=50)),
                ('source_id', models.IntegerField()),
                ('source_repr', models.CharField(max_length=255)),
                ('error_message', models.TextField(help_text="Message d'erreur détaillé")),
                ('error_traceback', models.TextField(blank=True, help_text='Traceback Python complet', null=True)),
                ('context', models.JSONField(default=dict, help_text="Contexte de l'opération (paramètres, état)")),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'En attente de retry'),
                        ('retrying', 'Retry en cours'),
                        ('resolved', 'Résolu'),
                        ('failed', 'Échec définitif'),
                        ('ignored', 'Ignoré'),
                    ],
                    db_index=True,
                    default='pending',
                    max_length=20
                )),
                ('retry_count', models.IntegerField(default=0, help_text='Nombre de tentatives de retry')),
                ('max_retries', models.IntegerField(default=3, help_text='Nombre maximum de retries')),
                ('next_retry_at', models.DateTimeField(blank=True, help_text='Date/heure du prochain retry', null=True)),
                ('resolved_at', models.DateTimeField(blank=True, help_text='Date/heure de résolution', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resolved_by', models.ForeignKey(
                    blank=True,
                    help_text="Admin ayant résolu l'échec",
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='resolved_sync_failures',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Échec de synchronisation',
                'verbose_name_plural': 'Échecs de synchronisation',
                'db_table': 'sync_failure_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='syncfailurelog',
            index=models.Index(fields=['sync_type', 'status'], name='sync_failur_sync_ty_2f8a3c_idx'),
        ),
        migrations.AddIndex(
            model_name='syncfailurelog',
            index=models.Index(fields=['source_model', 'source_id'], name='sync_failur_source__7d1e4f_idx'),
        ),
        migrations.AddIndex(
            model_name='syncfailurelog',
            index=models.Index(fields=['status', 'next_retry_at'], name='sync_failur_status_1a2b3c_idx'),
        ),
    ]
