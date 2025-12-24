# Generated migration for BlockedSite MikroTik integration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_add_user_disconnection_log'),
    ]

    operations = [
        # Rename url field to domain
        migrations.RenameField(
            model_name='blockedsite',
            old_name='url',
            new_name='domain',
        ),

        # Add category field
        migrations.AddField(
            model_name='blockedsite',
            name='category',
            field=models.CharField(
                choices=[
                    ('social', 'Réseaux sociaux'),
                    ('streaming', 'Streaming vidéo'),
                    ('gaming', 'Jeux en ligne'),
                    ('adult', 'Contenu adulte'),
                    ('gambling', "Jeux d'argent"),
                    ('malware', 'Malware/Phishing'),
                    ('ads', 'Publicités'),
                    ('other', 'Autre'),
                ],
                default='other',
                help_text='Catégorie du site pour le regroupement et les statistiques',
                max_length=20,
            ),
        ),

        # Add profile FK for per-profile blocking
        migrations.AddField(
            model_name='blockedsite',
            name='profile',
            field=models.ForeignKey(
                blank=True,
                help_text='Profil concerné (laisser vide pour bloquer globalement)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='blocked_sites',
                to='core.profile',
            ),
        ),

        # Add promotion FK for per-promotion blocking
        migrations.AddField(
            model_name='blockedsite',
            name='promotion',
            field=models.ForeignKey(
                blank=True,
                help_text='Promotion concernée (laisser vide pour bloquer globalement)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='blocked_sites',
                to='core.promotion',
            ),
        ),

        # Add MikroTik sync fields
        migrations.AddField(
            model_name='blockedsite',
            name='mikrotik_id',
            field=models.CharField(
                blank=True,
                help_text="ID de l'entrée DNS statique sur MikroTik (géré automatiquement)",
                max_length=50,
                null=True,
            ),
        ),

        migrations.AddField(
            model_name='blockedsite',
            name='sync_status',
            field=models.CharField(
                choices=[
                    ('pending', 'En attente'),
                    ('synced', 'Synchronisé'),
                    ('error', 'Erreur'),
                ],
                default='pending',
                help_text='État de la synchronisation avec MikroTik',
                max_length=20,
            ),
        ),

        migrations.AddField(
            model_name='blockedsite',
            name='last_sync_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Date de la dernière synchronisation réussie',
                null=True,
            ),
        ),

        migrations.AddField(
            model_name='blockedsite',
            name='last_sync_error',
            field=models.TextField(
                blank=True,
                help_text="Dernier message d'erreur de synchronisation",
                null=True,
            ),
        ),

        # Add indexes
        migrations.AddIndex(
            model_name='blockedsite',
            index=models.Index(fields=['sync_status'], name='blocked_sit_sync_st_idx'),
        ),

        migrations.AddIndex(
            model_name='blockedsite',
            index=models.Index(fields=['category'], name='blocked_sit_categor_idx'),
        ),

        # Add constraint: profile OR promotion, not both
        migrations.AddConstraint(
            model_name='blockedsite',
            constraint=models.CheckConstraint(
                check=~models.Q(
                    ('profile__isnull', False),
                    ('promotion__isnull', False),
                ),
                name='blocked_site_profile_or_promotion_not_both',
            ),
        ),

        # Update help texts for existing fields
        migrations.AlterField(
            model_name='blockedsite',
            name='domain',
            field=models.CharField(
                db_index=True,
                help_text='Domaine à bloquer (ex: facebook.com). Utilisez le préfixe * pour les sous-domaines (*.example.com)',
                max_length=255,
                unique=True,
            ),
        ),

        migrations.AlterField(
            model_name='blockedsite',
            name='reason',
            field=models.CharField(
                blank=True,
                help_text='Raison du blocage (visible dans les logs)',
                max_length=255,
                null=True,
            ),
        ),

        migrations.AlterField(
            model_name='blockedsite',
            name='is_active',
            field=models.BooleanField(
                default=True,
                help_text="Désactiver pour suspendre temporairement le blocage sans supprimer l'entrée",
            ),
        ),

        # Update model meta
        migrations.AlterModelOptions(
            name='blockedsite',
            options={
                'ordering': ['-added_date'],
                'verbose_name': 'Site bloqué',
                'verbose_name_plural': 'Sites bloqués',
            },
        ),
    ]
