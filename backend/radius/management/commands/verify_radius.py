"""
Commande de vérification des attributs RADIUS pour les utilisateurs.

Usage:
    # Vérifier un utilisateur spécifique
    python manage.py verify_radius --user=john

    # Vérifier tous les utilisateurs activés
    python manage.py verify_radius --all

    # Resynchroniser un utilisateur
    python manage.py verify_radius --user=john --resync

    # Afficher les attributs attendus pour un profil
    python manage.py verify_radius --profile="Étudiant"
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Vérifie et affiche les attributs RADIUS des utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Nom d\'utilisateur à vérifier'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Vérifier tous les utilisateurs activés dans RADIUS'
        )
        parser.add_argument(
            '--profile',
            type=str,
            help='Afficher les attributs attendus pour un profil'
        )
        parser.add_argument(
            '--resync',
            action='store_true',
            help='Resynchroniser les attributs RADIUS de l\'utilisateur'
        )
        parser.add_argument(
            '--fix-missing',
            action='store_true',
            help='Corriger les utilisateurs dont les attributs RADIUS sont manquants'
        )

    def handle(self, *args, **options):
        from core.models import User, Profile
        from radius.services import ProfileRadiusService

        if options['profile']:
            self._show_profile_attributes(options['profile'])
            return

        if options['user']:
            self._verify_user(options['user'], options['resync'])
            return

        if options['all']:
            self._verify_all_users(options['fix_missing'])
            return

        self.stdout.write(self.style.WARNING(
            'Aucune option spécifiée. Utilisez --user, --all ou --profile.'
        ))
        self.stdout.write('Exemple: python manage.py verify_radius --user=john')

    def _show_profile_attributes(self, profile_name):
        """Affiche les attributs RADIUS attendus pour un profil."""
        from core.models import Profile
        from radius.services import ProfileRadiusService

        try:
            profile = Profile.objects.get(name=profile_name)
        except Profile.DoesNotExist:
            raise CommandError(f"Profil '{profile_name}' non trouvé")

        self.stdout.write(self.style.SUCCESS(f'\n📋 Profil: {profile.name}'))
        self.stdout.write('=' * 60)

        # Informations du profil
        self.stdout.write(f'\nParamètres du profil:')
        self.stdout.write(f'  - Bande passante: ↓{profile.bandwidth_download}M / ↑{profile.bandwidth_upload}M')
        self.stdout.write(f'  - Session timeout: {profile.session_timeout}s ({profile.session_timeout // 3600}h)')
        self.stdout.write(f'  - Idle timeout: {profile.idle_timeout}s ({profile.idle_timeout // 60}min)')
        self.stdout.write(f'  - Connexions simultanées: {profile.simultaneous_use}')
        self.stdout.write(f'  - Type de quota: {profile.get_quota_type_display()}')
        if profile.quota_type == 'limited':
            self.stdout.write(f'  - Volume de données: {profile.data_volume_gb} Go')

        # Attributs radreply attendus
        self.stdout.write(self.style.NOTICE('\nAttributs RADREPLY (Access-Accept):'))
        radreply_attrs = ProfileRadiusService.get_radius_attributes_for_profile(profile)
        for attr in radreply_attrs:
            self.stdout.write(f"  {attr['attribute']} {attr['op']} {attr['value']}")

        # Attributs radcheck attendus
        self.stdout.write(self.style.NOTICE('\nAttributs RADCHECK (vérification):'))
        radcheck_attrs = ProfileRadiusService.get_radcheck_attributes_for_profile(profile)
        for attr in radcheck_attrs:
            self.stdout.write(f"  {attr['attribute']} {attr['op']} {attr['value']}")

        self.stdout.write('')

    def _verify_user(self, username, resync=False):
        """Vérifie les attributs RADIUS d'un utilisateur."""
        from core.models import User
        from radius.services import ProfileRadiusService

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"Utilisateur '{username}' non trouvé")

        self.stdout.write(self.style.SUCCESS(f'\n👤 Utilisateur: {username}'))
        self.stdout.write('=' * 60)

        # Statut de l'utilisateur
        self.stdout.write(f'\nStatut Django:')
        self.stdout.write(f'  - Actif: {user.is_active}')
        self.stdout.write(f'  - RADIUS activé: {user.is_radius_activated}')
        self.stdout.write(f'  - RADIUS enabled: {user.is_radius_enabled}')
        self.stdout.write(f'  - Statut: {user.get_radius_status_display()}')

        # Profil effectif
        profile = user.get_effective_profile()
        if profile:
            self.stdout.write(f'\nProfil effectif: {profile.name}')
            self.stdout.write(f'  - Source: {"Individuel" if user.profile else "Promotion (" + (user.promotion.name if user.promotion else "?") + ")"}')
        else:
            self.stdout.write(self.style.WARNING('\nAucun profil effectif!'))

        # Attributs RADIUS actuels
        attrs = ProfileRadiusService.get_user_radius_attributes(username)

        self.stdout.write(self.style.NOTICE('\nAttributs RADCHECK actuels:'))
        if attrs['radcheck']:
            for r in attrs['radcheck']:
                status = '✓' if r.get('statut') else '✗'
                value = r['value']
                if r['attribute'] == 'Cleartext-Password':
                    value = '*' * len(value) if value else '(vide)'
                self.stdout.write(f"  [{status}] {r['attribute']} {r['op']} {value}")
        else:
            self.stdout.write(self.style.ERROR('  Aucun attribut!'))

        self.stdout.write(self.style.NOTICE('\nAttributs RADREPLY actuels:'))
        if attrs['radreply']:
            for r in attrs['radreply']:
                self.stdout.write(f"  {r['attribute']} {r['op']} {r['value']}")
        else:
            self.stdout.write(self.style.ERROR('  Aucun attribut!'))

        self.stdout.write(self.style.NOTICE('\nGroupes RADIUS:'))
        if attrs['radusergroup']:
            for g in attrs['radusergroup']:
                self.stdout.write(f"  {g['groupname']} (priorité: {g['priority']})")
        else:
            self.stdout.write(self.style.WARNING('  Aucun groupe'))

        # Résumé
        self.stdout.write(self.style.NOTICE('\nRésumé:'))
        summary = attrs['summary']
        self.stdout.write(f"  - Mot de passe: {'✓' if summary['has_password'] else '✗'}")
        self.stdout.write(f"  - Activé: {'✓' if summary['is_enabled'] else '✗'}")
        self.stdout.write(f"  - Rate-Limit: {summary['rate_limit'] or 'Non défini'}")
        self.stdout.write(f"  - Session-Timeout: {summary['session_timeout'] or 'Non défini'}")
        self.stdout.write(f"  - Simultaneous-Use: {summary['simultaneous_use'] or 'Non défini'}")
        self.stdout.write(f"  - Quota: {summary['quota'] or 'Non défini'}")

        # Vérification de cohérence
        self._check_consistency(user, profile, attrs)

        # Resync si demandé
        if resync and profile:
            self.stdout.write(self.style.WARNING('\n🔄 Resynchronisation...'))
            try:
                ProfileRadiusService.sync_user_to_radius(user, profile)
                self.stdout.write(self.style.SUCCESS('✓ Resynchronisation réussie!'))

                # Afficher les nouveaux attributs
                new_attrs = ProfileRadiusService.get_user_radius_attributes(username)
                self.stdout.write(self.style.NOTICE('\nNouveaux attributs RADREPLY:'))
                for r in new_attrs['radreply']:
                    self.stdout.write(f"  {r['attribute']} {r['op']} {r['value']}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Erreur: {e}'))

        self.stdout.write('')

    def _check_consistency(self, user, profile, attrs):
        """Vérifie la cohérence entre le profil et les attributs RADIUS."""
        from radius.services import ProfileRadiusService

        issues = []

        if not profile:
            issues.append("Aucun profil assigné")
        else:
            expected_rate = ProfileRadiusService.get_mikrotik_rate_limit(profile)
            actual_rate = attrs['summary']['rate_limit']

            if actual_rate != expected_rate:
                issues.append(f"Rate-Limit incorrect: attendu '{expected_rate}', trouvé '{actual_rate}'")

            if attrs['summary']['session_timeout'] != str(profile.session_timeout):
                issues.append(
                    f"Session-Timeout incorrect: attendu '{profile.session_timeout}', "
                    f"trouvé '{attrs['summary']['session_timeout']}'"
                )

            if attrs['summary']['simultaneous_use'] != str(profile.simultaneous_use):
                issues.append(
                    f"Simultaneous-Use incorrect: attendu '{profile.simultaneous_use}', "
                    f"trouvé '{attrs['summary']['simultaneous_use']}'"
                )

        if not attrs['summary']['has_password']:
            issues.append("Pas de mot de passe dans radcheck")

        if user.is_radius_enabled and not attrs['summary']['is_enabled']:
            issues.append("Utilisateur activé dans Django mais désactivé dans RADIUS")

        if issues:
            self.stdout.write(self.style.ERROR('\n⚠️ Problèmes détectés:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f"  - {issue}"))
            self.stdout.write(self.style.WARNING('\n  Utilisez --resync pour corriger'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Configuration cohérente'))

    def _verify_all_users(self, fix_missing=False):
        """Vérifie tous les utilisateurs activés dans RADIUS."""
        from core.models import User
        from radius.services import ProfileRadiusService
        from radius.models import RadCheck

        users = User.objects.filter(
            is_radius_activated=True
        ).select_related('profile', 'promotion__profile')

        self.stdout.write(self.style.SUCCESS(f'\n📊 Vérification de {users.count()} utilisateurs'))
        self.stdout.write('=' * 60)

        stats = {
            'ok': 0,
            'missing_radreply': 0,
            'missing_radcheck': 0,
            'wrong_rate': 0,
            'no_profile': 0,
            'fixed': 0
        }

        for user in users:
            profile = user.get_effective_profile()
            attrs = ProfileRadiusService.get_user_radius_attributes(user.username)

            issues = []

            if not profile:
                issues.append('no_profile')
                stats['no_profile'] += 1

            if not attrs['radcheck']:
                issues.append('missing_radcheck')
                stats['missing_radcheck'] += 1

            if not attrs['radreply']:
                issues.append('missing_radreply')
                stats['missing_radreply'] += 1
            elif profile:
                expected_rate = ProfileRadiusService.get_mikrotik_rate_limit(profile)
                if attrs['summary']['rate_limit'] != expected_rate:
                    issues.append('wrong_rate')
                    stats['wrong_rate'] += 1

            if issues:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️ {user.username}: {', '.join(issues)}")
                )

                if fix_missing and profile and ('missing_radreply' in issues or 'wrong_rate' in issues):
                    try:
                        ProfileRadiusService.sync_user_to_radius(user, profile)
                        self.stdout.write(self.style.SUCCESS(f"     → Corrigé!"))
                        stats['fixed'] += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"     → Erreur: {e}"))
            else:
                stats['ok'] += 1

        # Résumé
        self.stdout.write(self.style.NOTICE('\n📈 Résumé:'))
        self.stdout.write(f"  - OK: {stats['ok']}")
        self.stdout.write(f"  - Sans profil: {stats['no_profile']}")
        self.stdout.write(f"  - Sans radcheck: {stats['missing_radcheck']}")
        self.stdout.write(f"  - Sans radreply: {stats['missing_radreply']}")
        self.stdout.write(f"  - Rate-limit incorrect: {stats['wrong_rate']}")
        if fix_missing:
            self.stdout.write(self.style.SUCCESS(f"  - Corrigés: {stats['fixed']}"))

        if stats['missing_radreply'] > 0 or stats['wrong_rate'] > 0:
            self.stdout.write(self.style.WARNING(
                '\n  Utilisez --fix-missing pour corriger les problèmes'
            ))

        self.stdout.write('')
