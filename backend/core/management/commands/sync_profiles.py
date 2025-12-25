"""
Commande de gestion pour synchroniser les profils vers RADIUS et MikroTik.

Usage:
    # Synchroniser tous les profils et utilisateurs
    python manage.py sync_profiles

    # Synchroniser uniquement les profils (pas les utilisateurs)
    python manage.py sync_profiles --profiles-only

    # Synchroniser uniquement les utilisateurs
    python manage.py sync_profiles --users-only

    # Synchroniser un utilisateur spécifique
    python manage.py sync_profiles --user=john

    # Synchroniser une promotion spécifique
    python manage.py sync_profiles --promotion="L3 Informatique"

    # Importer les profils depuis MikroTik
    python manage.py sync_profiles --import-from-mikrotik

    # Forcer la resynchronisation
    python manage.py sync_profiles --force
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Synchronise les profils vers RADIUS et MikroTik'

    def add_arguments(self, parser):
        parser.add_argument(
            '--profiles-only',
            action='store_true',
            help='Synchroniser uniquement les profils (pas les utilisateurs)'
        )
        parser.add_argument(
            '--users-only',
            action='store_true',
            help='Synchroniser uniquement les utilisateurs'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Synchroniser un utilisateur spécifique (username)'
        )
        parser.add_argument(
            '--promotion',
            type=str,
            help='Synchroniser une promotion spécifique (nom)'
        )
        parser.add_argument(
            '--profile',
            type=str,
            help='Synchroniser un profil spécifique (nom)'
        )
        parser.add_argument(
            '--import-from-mikrotik',
            action='store_true',
            help='Importer les profils existants depuis MikroTik vers Django'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la resynchronisation même si déjà synchronisé'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher les actions sans les exécuter'
        )
        parser.add_argument(
            '--radius-only',
            action='store_true',
            help='Synchroniser uniquement avec RADIUS (pas MikroTik)'
        )
        parser.add_argument(
            '--mikrotik-only',
            action='store_true',
            help='Synchroniser uniquement avec MikroTik (pas RADIUS)'
        )

    def handle(self, *args, **options):
        from core.models import User, Profile, Promotion
        from radius.services import ProfileRadiusService, PromotionRadiusService
        from mikrotik.profile_service import MikrotikProfileSyncService, FullProfileSyncService

        self.stdout.write(self.style.NOTICE('=' * 70))
        self.stdout.write(self.style.NOTICE('SYNCHRONISATION DES PROFILS'))
        self.stdout.write(self.style.NOTICE(f'Date: {timezone.now()}'))
        self.stdout.write(self.style.NOTICE('=' * 70))

        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode DRY-RUN activé - Aucune modification ne sera effectuée'))

        # Import depuis MikroTik
        if options['import_from_mikrotik']:
            self._import_from_mikrotik(dry_run)
            return

        # Synchronisation d'un utilisateur spécifique
        if options['user']:
            self._sync_single_user(options['user'], options, dry_run)
            return

        # Synchronisation d'une promotion spécifique
        if options['promotion']:
            self._sync_single_promotion(options['promotion'], options, dry_run)
            return

        # Synchronisation d'un profil spécifique
        if options['profile']:
            self._sync_single_profile(options['profile'], options, dry_run)
            return

        # Synchronisation complète
        self._sync_all(options, dry_run)

    def _import_from_mikrotik(self, dry_run):
        """Importe les profils depuis MikroTik."""
        from mikrotik.profile_service import MikrotikProfileSyncService

        self.stdout.write('\n📥 Import des profils depuis MikroTik...')

        service = MikrotikProfileSyncService()

        if dry_run:
            profiles = service.get_all_hotspot_profiles()
            self.stdout.write(f'Profils trouvés: {len(profiles)}')
            for p in profiles:
                if not p.get('name', '').startswith(service.PROFILE_PREFIX):
                    self.stdout.write(f"  - {p.get('name')}: rate-limit={p.get('rate-limit')}")
            return

        result = service.import_all_mikrotik_profiles()

        self.stdout.write(f"Total: {result['total']}")
        self.stdout.write(self.style.SUCCESS(f"Importés: {result['imported']}"))
        self.stdout.write(f"Ignorés (déjà gérés): {result['skipped']}")

        if result.get('errors'):
            self.stdout.write(self.style.ERROR(f"Erreurs: {len(result['errors'])}"))
            for error in result['errors']:
                self.stdout.write(f"  - {error['profile']}: {error['error']}")

    def _sync_single_user(self, username, options, dry_run):
        """Synchronise un utilisateur spécifique."""
        from core.models import User
        from radius.services import ProfileRadiusService
        from mikrotik.profile_service import MikrotikProfileSyncService

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"Utilisateur '{username}' non trouvé")

        profile = user.get_effective_profile()
        if not profile:
            raise CommandError(f"Aucun profil assigné à '{username}'")

        self.stdout.write(f"\n👤 Synchronisation de l'utilisateur: {username}")
        self.stdout.write(f"   Profil effectif: {profile.name}")
        self.stdout.write(f"   RADIUS activé: {user.is_radius_activated}")
        self.stdout.write(f"   RADIUS enabled: {user.is_radius_enabled}")

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN: Aucune modification'))
            return

        # RADIUS
        if not options['mikrotik_only']:
            if user.is_radius_activated:
                try:
                    ProfileRadiusService.sync_user_to_radius(user, profile)
                    self.stdout.write(self.style.SUCCESS('   ✓ RADIUS synchronisé'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ✗ RADIUS erreur: {e}'))
            else:
                self.stdout.write('   ⚠ RADIUS non activé, ignoré')

        # MikroTik
        if not options['radius_only']:
            try:
                service = MikrotikProfileSyncService()
                result = service.sync_user(user)
                if result.get('success'):
                    self.stdout.write(self.style.SUCCESS('   ✓ MikroTik synchronisé'))
                else:
                    self.stdout.write(self.style.ERROR(f"   ✗ MikroTik erreur: {result.get('error')}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ MikroTik erreur: {e}'))

    def _sync_single_promotion(self, promotion_name, options, dry_run):
        """Synchronise une promotion spécifique."""
        from core.models import Promotion
        from radius.services import PromotionRadiusService
        from mikrotik.profile_service import MikrotikProfileSyncService

        try:
            promotion = Promotion.objects.get(name=promotion_name)
        except Promotion.DoesNotExist:
            raise CommandError(f"Promotion '{promotion_name}' non trouvée")

        if not promotion.profile:
            raise CommandError(f"Aucun profil assigné à la promotion '{promotion_name}'")

        users = promotion.users.filter(is_radius_activated=True, is_active=True)

        self.stdout.write(f"\n🎓 Synchronisation de la promotion: {promotion.name}")
        self.stdout.write(f"   Profil: {promotion.profile.name}")
        self.stdout.write(f"   Utilisateurs actifs: {users.count()}")

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN: Aucune modification'))
            for user in users[:10]:
                self.stdout.write(f"   - {user.username}")
            if users.count() > 10:
                self.stdout.write(f"   ... et {users.count() - 10} autres")
            return

        # RADIUS
        if not options['mikrotik_only']:
            try:
                result = PromotionRadiusService.sync_promotion_users(promotion)
                self.stdout.write(self.style.SUCCESS(f"   ✓ RADIUS: {result.get('synced', 0)} utilisateurs synchronisés"))
                if result.get('errors'):
                    for error in result['errors']:
                        self.stdout.write(self.style.ERROR(f"     ✗ {error['user']}: {error['error']}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ RADIUS erreur: {e}'))

        # MikroTik
        if not options['radius_only']:
            try:
                service = MikrotikProfileSyncService()
                result = service.sync_promotion_users(promotion)
                self.stdout.write(self.style.SUCCESS(f"   ✓ MikroTik: {result.get('synced', 0)} utilisateurs synchronisés"))
                if result.get('errors'):
                    for error in result['errors']:
                        self.stdout.write(self.style.ERROR(f"     ✗ {error['user']}: {error['error']}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ MikroTik erreur: {e}'))

    def _sync_single_profile(self, profile_name, options, dry_run):
        """Synchronise un profil spécifique vers MikroTik."""
        from core.models import Profile
        from mikrotik.profile_service import MikrotikProfileSyncService

        try:
            profile = Profile.objects.get(name=profile_name)
        except Profile.DoesNotExist:
            raise CommandError(f"Profil '{profile_name}' non trouvé")

        self.stdout.write(f"\n📋 Synchronisation du profil: {profile.name}")
        self.stdout.write(f"   Bande passante: ↓{profile.bandwidth_download}M / ↑{profile.bandwidth_upload}M")
        self.stdout.write(f"   Session timeout: {profile.session_timeout}s")
        self.stdout.write(f"   Connexions simultanées: {profile.simultaneous_use}")

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN: Aucune modification'))
            return

        if not options['radius_only']:
            try:
                service = MikrotikProfileSyncService()
                result = service.sync_profile(profile)
                if result.get('success'):
                    self.stdout.write(self.style.SUCCESS('   ✓ MikroTik synchronisé'))
                else:
                    self.stdout.write(self.style.ERROR(f"   ✗ MikroTik erreur: {result.get('error')}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ MikroTik erreur: {e}'))

    def _sync_all(self, options, dry_run):
        """Synchronise tous les profils et utilisateurs."""
        from core.models import User, Profile, Promotion
        from radius.services import ProfileRadiusService
        from mikrotik.profile_service import MikrotikProfileSyncService, FullProfileSyncService

        profiles_only = options['profiles_only']
        users_only = options['users_only']
        radius_only = options['radius_only']
        mikrotik_only = options['mikrotik_only']

        # Stats
        stats = {
            'profiles_synced': 0,
            'users_synced': 0,
            'errors': []
        }

        # === Profils ===
        if not users_only:
            profiles = Profile.objects.filter(is_active=True)
            self.stdout.write(f"\n📋 Profils à synchroniser: {profiles.count()}")

            if dry_run:
                for profile in profiles:
                    self.stdout.write(f"   - {profile.name}: ↓{profile.bandwidth_download}M / ↑{profile.bandwidth_upload}M")
            else:
                if not radius_only:
                    service = MikrotikProfileSyncService()
                    for profile in profiles:
                        try:
                            result = service.sync_profile(profile)
                            if result.get('success'):
                                stats['profiles_synced'] += 1
                                self.stdout.write(self.style.SUCCESS(f"   ✓ {profile.name}"))
                            else:
                                stats['errors'].append({
                                    'type': 'profile',
                                    'name': profile.name,
                                    'error': result.get('error')
                                })
                                self.stdout.write(self.style.ERROR(f"   ✗ {profile.name}: {result.get('error')}"))
                        except Exception as e:
                            stats['errors'].append({
                                'type': 'profile',
                                'name': profile.name,
                                'error': str(e)
                            })
                            self.stdout.write(self.style.ERROR(f"   ✗ {profile.name}: {e}"))

        # === Utilisateurs ===
        if not profiles_only:
            users = User.objects.filter(
                is_radius_activated=True,
                is_active=True
            ).select_related('profile', 'promotion__profile')

            self.stdout.write(f"\n👥 Utilisateurs à synchroniser: {users.count()}")

            if dry_run:
                for user in users[:20]:
                    profile = user.get_effective_profile()
                    profile_name = profile.name if profile else 'Aucun'
                    self.stdout.write(f"   - {user.username}: {profile_name}")
                if users.count() > 20:
                    self.stdout.write(f"   ... et {users.count() - 20} autres")
            else:
                mikrotik_service = MikrotikProfileSyncService() if not radius_only else None

                for user in users:
                    profile = user.get_effective_profile()
                    if not profile:
                        continue

                    try:
                        # RADIUS
                        if not mikrotik_only:
                            ProfileRadiusService.sync_user_to_radius(user, profile)

                        # MikroTik
                        if mikrotik_service:
                            mikrotik_service.sync_user(user)

                        stats['users_synced'] += 1

                    except Exception as e:
                        stats['errors'].append({
                            'type': 'user',
                            'name': user.username,
                            'error': str(e)
                        })

                self.stdout.write(self.style.SUCCESS(f"   ✓ {stats['users_synced']} utilisateurs synchronisés"))

        # === Résumé ===
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('RÉSUMÉ'))
        self.stdout.write('=' * 70)

        if not dry_run:
            self.stdout.write(f"Profils synchronisés: {stats['profiles_synced']}")
            self.stdout.write(f"Utilisateurs synchronisés: {stats['users_synced']}")

            if stats['errors']:
                self.stdout.write(self.style.ERROR(f"Erreurs: {len(stats['errors'])}"))
                for error in stats['errors'][:10]:
                    self.stdout.write(f"  - [{error['type']}] {error['name']}: {error['error']}")
                if len(stats['errors']) > 10:
                    self.stdout.write(f"  ... et {len(stats['errors']) - 10} autres erreurs")
            else:
                self.stdout.write(self.style.SUCCESS('Aucune erreur!'))
        else:
            self.stdout.write(self.style.WARNING('DRY-RUN terminé - Aucune modification effectuée'))
