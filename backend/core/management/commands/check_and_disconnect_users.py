"""
Commande pour vérifier les quotas et désactiver automatiquement les utilisateurs
qui ont atteint leurs limites.

Cette commande doit être exécutée périodiquement (via cron ou celery) pour:
1. Vérifier les quotas de données de chaque utilisateur actif
2. Vérifier les durées de session
3. Vérifier les limites périodiques (journalières, hebdomadaires, mensuelles)
4. Désactiver les utilisateurs qui ont atteint leurs limites (statut=0 dans radcheck)
5. Créer des logs de déconnexion avec les raisons

Usage:
    python manage.py check_and_disconnect_users
    python manage.py check_and_disconnect_users --dry-run  # Mode test
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from core.models import User, UserProfileUsage, UserDisconnectionLog
from radius.models import RadCheck, RadAcct


class Command(BaseCommand):
    help = "Vérifie les quotas et désactive les utilisateurs ayant atteint leurs limites"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test: affiche les actions sans les effectuer',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche plus de détails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']

        self.stdout.write(self.style.WARNING('='*70))
        self.stdout.write(self.style.WARNING('VÉRIFICATION ET DÉSACTIVATION AUTOMATIQUE DES UTILISATEURS'))
        self.stdout.write(self.style.WARNING('='*70))

        if dry_run:
            self.stdout.write(self.style.NOTICE('\n🔍 MODE DRY-RUN: Aucune modification ne sera effectuée\n'))
        else:
            self.stdout.write(self.style.NOTICE('\n⚠️  MODE RÉEL: Les utilisateurs seront désactivés\n'))

        # Statistiques
        stats = {
            'total_checked': 0,
            'quota_exceeded': 0,
            'daily_limit': 0,
            'weekly_limit': 0,
            'monthly_limit': 0,
            'validity_expired': 0,
            'session_expired': 0,
            'already_disconnected': 0,
        }

        # Récupérer tous les utilisateurs actifs avec RADIUS activé
        active_users = User.objects.filter(
            is_active=True,
            is_radius_activated=True
        ).select_related('profile', 'promotion__profile')

        self.stdout.write(f"✓ {active_users.count()} utilisateurs actifs trouvés\n")

        for user in active_users:
            stats['total_checked'] += 1

            if verbose:
                self.stdout.write(f"\n[{stats['total_checked']}] Vérification: {user.username} ({user.first_name} {user.last_name})")

            # Récupérer le profil effectif
            profile = user.get_effective_profile()
            if not profile:
                if verbose:
                    self.stdout.write(f"  ⊘ Aucun profil assigné, passage")
                continue

            # Vérifier si l'utilisateur est déjà déconnecté
            existing_disconnection = UserDisconnectionLog.objects.filter(
                user=user,
                is_active=True
            ).first()

            if existing_disconnection:
                stats['already_disconnected'] += 1
                if verbose:
                    self.stdout.write(f"  ⊗ Déjà déconnecté: {existing_disconnection.get_reason_display()}")
                continue

            # Variables pour tracking
            should_disconnect = False
            reason = None
            description = None
            quota_used = None
            quota_limit = None

            # 1. Vérifier le quota de données (si quota limité)
            if profile.quota_type == 'limited':
                try:
                    usage = UserProfileUsage.objects.get(user=user, profile=profile)
                    quota_used = usage.total_input + usage.total_output
                    quota_limit = profile.data_volume

                    if quota_used >= quota_limit:
                        should_disconnect = True
                        reason = 'quota_exceeded'
                        description = f"Quota dépassé: {usage.format_data_size(quota_used)} / {usage.format_data_size(quota_limit)}"
                        stats['quota_exceeded'] += 1

                        if verbose:
                            self.stdout.write(self.style.ERROR(f"  ✗ QUOTA DÉPASSÉ: {description}"))

                except UserProfileUsage.DoesNotExist:
                    if verbose:
                        self.stdout.write(f"  ⊘ Pas de données d'usage")

            # 2. Vérifier les limites périodiques
            if not should_disconnect:
                try:
                    usage = UserProfileUsage.objects.get(user=user, profile=profile)

                    # Limite journalière
                    if profile.daily_limit and usage.daily_input + usage.daily_output >= profile.daily_limit:
                        should_disconnect = True
                        reason = 'daily_limit'
                        description = f"Limite journalière atteinte: {usage.format_data_size(usage.daily_input + usage.daily_output)} / {usage.format_data_size(profile.daily_limit)}"
                        stats['daily_limit'] += 1

                    # Limite hebdomadaire
                    elif profile.weekly_limit and usage.weekly_input + usage.weekly_output >= profile.weekly_limit:
                        should_disconnect = True
                        reason = 'weekly_limit'
                        description = f"Limite hebdomadaire atteinte: {usage.format_data_size(usage.weekly_input + usage.weekly_output)} / {usage.format_data_size(profile.weekly_limit)}"
                        stats['weekly_limit'] += 1

                    # Limite mensuelle
                    elif profile.monthly_limit and usage.monthly_input + usage.monthly_output >= profile.monthly_limit:
                        should_disconnect = True
                        reason = 'monthly_limit'
                        description = f"Limite mensuelle atteinte: {usage.format_data_size(usage.monthly_input + usage.monthly_output)} / {usage.format_data_size(profile.monthly_limit)}"
                        stats['monthly_limit'] += 1

                    if should_disconnect and verbose:
                        self.stdout.write(self.style.ERROR(f"  ✗ LIMITE ATTEINTE: {description}"))

                except UserProfileUsage.DoesNotExist:
                    pass

            # 3. Vérifier la durée de validité
            if not should_disconnect and profile.validity_duration:
                try:
                    usage = UserProfileUsage.objects.get(user=user, profile=profile)
                    days_remaining = usage.days_remaining()

                    if days_remaining is not None and days_remaining <= 0:
                        should_disconnect = True
                        reason = 'validity_expired'
                        description = f"Durée de validité expirée (dépassée de {abs(days_remaining)} jours)"
                        stats['validity_expired'] += 1

                        if verbose:
                            self.stdout.write(self.style.ERROR(f"  ✗ VALIDITÉ EXPIRÉE: {description}"))

                except UserProfileUsage.DoesNotExist:
                    pass

            # 4. Effectuer la déconnexion si nécessaire
            if should_disconnect:
                if not dry_run:
                    try:
                        with transaction.atomic():
                            # Mettre à jour statut=0 dans radcheck pour toutes les entrées de cet utilisateur
                            updated = RadCheck.objects.filter(username=user.username).update(statut=False)

                            # Créer le log de déconnexion
                            UserDisconnectionLog.objects.create(
                                user=user,
                                reason=reason,
                                description=description,
                                quota_used=quota_used,
                                quota_limit=quota_limit,
                                is_active=True
                            )

                            self.stdout.write(self.style.ERROR(f"  ✗ DÉSACTIVÉ: {user.username} - {description}"))
                            self.stdout.write(f"     → {updated} entrée(s) RadCheck mises à jour (statut=0)")

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ✗ ERREUR lors de la désactivation: {str(e)}"))

                else:
                    self.stdout.write(self.style.WARNING(f"  [DRY-RUN] Désactiverait: {user.username} - {description}"))

            else:
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f"  ✓ OK: Aucune limite atteinte"))

        # Afficher les statistiques finales
        self.stdout.write(self.style.WARNING('\n' + '='*70))
        self.stdout.write(self.style.WARNING('STATISTIQUES'))
        self.stdout.write(self.style.WARNING('='*70))

        self.stdout.write(f"\n📊 Utilisateurs vérifiés: {stats['total_checked']}")
        self.stdout.write(f"⊗ Déjà déconnectés: {stats['already_disconnected']}")

        if not dry_run:
            total_disconnected = (stats['quota_exceeded'] + stats['daily_limit'] +
                                 stats['weekly_limit'] + stats['monthly_limit'] +
                                 stats['validity_expired'] + stats['session_expired'])
            self.stdout.write(f"\n🔴 Total désactivés: {total_disconnected}")
        else:
            total_would_disconnect = (stats['quota_exceeded'] + stats['daily_limit'] +
                                      stats['weekly_limit'] + stats['monthly_limit'] +
                                      stats['validity_expired'] + stats['session_expired'])
            self.stdout.write(f"\n🟡 Seraient désactivés: {total_would_disconnect}")

        self.stdout.write(f"   - Quota dépassé: {stats['quota_exceeded']}")
        self.stdout.write(f"   - Limite journalière: {stats['daily_limit']}")
        self.stdout.write(f"   - Limite hebdomadaire: {stats['weekly_limit']}")
        self.stdout.write(f"   - Limite mensuelle: {stats['monthly_limit']}")
        self.stdout.write(f"   - Validité expirée: {stats['validity_expired']}")
        self.stdout.write(f"   - Session expirée: {stats['session_expired']}")

        self.stdout.write(self.style.SUCCESS('\n✅ Vérification terminée'))
        self.stdout.write(self.style.WARNING('='*70 + '\n'))

        if dry_run:
            self.stdout.write(self.style.NOTICE('💡 Exécutez sans --dry-run pour effectuer les désactivations'))
