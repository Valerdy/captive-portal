"""
Service de synchronisation des profils Django vers MikroTik Hotspot.

Ce service gère:
- Création/mise à jour des profils hotspot sur MikroTik
- Synchronisation des utilisateurs avec leur profil effectif
- Détection et import des profils MikroTik existants
- Mise à jour automatique lors des changements de profil

Architecture:
    Django Profile → MikroTik Hotspot User Profile
    Django User → MikroTik Hotspot User (avec profile assigné)

Le rate-limit MikroTik est au format: rx-rate[/tx-rate] [rx-burst-rate/tx-burst-rate] ...
Où rx = download (ce que reçoit le client), tx = upload (ce qu'envoie le client)
"""

from django.db import transaction
from django.utils import timezone
from django.conf import settings
from typing import Dict, Any, List, Optional, Tuple
import logging

from .utils import MikrotikAgentClient
from .models import MikrotikRouter, MikrotikHotspotUser, MikrotikLog

logger = logging.getLogger(__name__)


class MikrotikProfileSyncService:
    """
    Service pour synchroniser les profils Django avec MikroTik Hotspot.

    Fonctionnalités:
    - Crée des profils hotspot correspondant aux profils Django
    - Synchronise les utilisateurs avec le bon profil hotspot
    - Gère les changements de profil (utilisateur ou promotion)
    - Détecte et importe les profils MikroTik existants
    """

    # Préfixe pour identifier les profils gérés par Django
    PROFILE_PREFIX = 'cp-'  # captive-portal prefix

    # Profil par défaut MikroTik
    DEFAULT_PROFILE = 'default'

    def __init__(self, router: Optional[MikrotikRouter] = None):
        """
        Initialise le service de synchronisation.

        Args:
            router: Router MikroTik spécifique (utilise le premier actif si non fourni)
        """
        self.router = router or self._get_default_router()
        self.client = MikrotikAgentClient()

    def _get_default_router(self) -> Optional[MikrotikRouter]:
        """Récupère le premier routeur actif."""
        return MikrotikRouter.objects.filter(is_active=True).first()

    def _log_operation(
        self,
        operation: str,
        message: str,
        level: str = 'info',
        details: Optional[Dict] = None
    ):
        """Log une opération dans la base de données."""
        if self.router:
            MikrotikLog.objects.create(
                router=self.router,
                operation=operation,
                message=message,
                level=level,
                details=details
            )
        logger.log(
            getattr(logging, level.upper(), logging.INFO),
            f"[MikroTik] {operation}: {message}"
        )

    def _get_mikrotik_profile_name(self, profile) -> str:
        """
        Génère le nom du profil MikroTik à partir du profil Django.

        Args:
            profile: Instance Profile Django

        Returns:
            Nom du profil MikroTik (ex: "cp-etudiant-standard")
        """
        # Nettoyer le nom pour MikroTik (pas d'espaces, caractères spéciaux)
        clean_name = profile.name.lower()
        clean_name = clean_name.replace(' ', '-')
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '-')
        return f"{self.PROFILE_PREFIX}{clean_name}"

    def _build_rate_limit(self, profile) -> str:
        """
        Construit la chaîne rate-limit pour MikroTik.

        Format MikroTik: rx/tx où rx=download, tx=upload
        Exemple: "10M/5M" = 10 Mbps download, 5 Mbps upload

        Args:
            profile: Instance Profile Django

        Returns:
            Chaîne rate-limit MikroTik
        """
        download = profile.bandwidth_download
        upload = profile.bandwidth_upload
        return f"{download}M/{upload}M"

    def _build_profile_data(self, profile) -> Dict[str, Any]:
        """
        Construit les données du profil pour l'API MikroTik.

        Args:
            profile: Instance Profile Django

        Returns:
            Dictionnaire des paramètres du profil hotspot
        """
        data = {
            'name': self._get_mikrotik_profile_name(profile),
            'rate-limit': self._build_rate_limit(profile),
            'session-timeout': f"{profile.session_timeout}s",
            'idle-timeout': f"{profile.idle_timeout}s",
            'shared-users': str(profile.simultaneous_use),
            'comment': f"Django Profile: {profile.name} (ID: {profile.id})"
        }

        # Ajouter le keepalive-timeout si session_timeout > 0
        if profile.session_timeout > 0:
            data['keepalive-timeout'] = '2m'

        return data

    # =========================================================================
    # Gestion des profils MikroTik
    # =========================================================================

    def get_all_hotspot_profiles(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les profils hotspot depuis MikroTik.

        Returns:
            Liste des profils hotspot
        """
        try:
            result = self.client.get_hotspot_profiles()
            return result.get('profiles', [])
        except Exception as e:
            self._log_operation(
                'get_profiles',
                f"Erreur: {e}",
                level='error'
            )
            return []

    def get_managed_profiles(self) -> List[Dict[str, Any]]:
        """
        Récupère uniquement les profils gérés par Django (préfixe cp-).

        Returns:
            Liste des profils gérés
        """
        profiles = self.get_all_hotspot_profiles()
        return [p for p in profiles if p.get('name', '').startswith(self.PROFILE_PREFIX)]

    def get_default_profile(self) -> Optional[Dict[str, Any]]:
        """
        Récupère le profil par défaut de MikroTik.

        Returns:
            Profil par défaut ou None
        """
        profiles = self.get_all_hotspot_profiles()
        for p in profiles:
            if p.get('name') == self.DEFAULT_PROFILE:
                return p
        return profiles[0] if profiles else None

    def create_hotspot_profile(self, profile) -> Dict[str, Any]:
        """
        Crée un profil hotspot sur MikroTik.

        Args:
            profile: Instance Profile Django

        Returns:
            Résultat de l'opération
        """
        profile_name = self._get_mikrotik_profile_name(profile)
        profile_data = self._build_profile_data(profile)

        try:
            result = self.client._make_request(
                'POST',
                '/api/mikrotik/hotspot/profiles',
                profile_data
            )

            self._log_operation(
                'create_profile',
                f"Profil '{profile_name}' créé",
                details={'profile_id': profile.id, 'mikrotik_data': profile_data}
            )

            return {
                'success': True,
                'profile_name': profile_name,
                'mikrotik_id': result.get('.id') or result.get('id')
            }

        except Exception as e:
            error_msg = str(e)

            # Si le profil existe déjà, le mettre à jour
            if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                return self.update_hotspot_profile(profile)

            self._log_operation(
                'create_profile',
                f"Erreur création '{profile_name}': {e}",
                level='error'
            )
            return {
                'success': False,
                'error': error_msg
            }

    def update_hotspot_profile(self, profile) -> Dict[str, Any]:
        """
        Met à jour un profil hotspot existant sur MikroTik.

        Args:
            profile: Instance Profile Django

        Returns:
            Résultat de l'opération
        """
        profile_name = self._get_mikrotik_profile_name(profile)
        profile_data = self._build_profile_data(profile)

        try:
            result = self.client._make_request(
                'PUT',
                f'/api/mikrotik/hotspot/profiles/{profile_name}',
                profile_data
            )

            self._log_operation(
                'update_profile',
                f"Profil '{profile_name}' mis à jour",
                details={'profile_id': profile.id}
            )

            return {
                'success': True,
                'profile_name': profile_name
            }

        except Exception as e:
            self._log_operation(
                'update_profile',
                f"Erreur mise à jour '{profile_name}': {e}",
                level='error'
            )
            return {
                'success': False,
                'error': str(e)
            }

    def delete_hotspot_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Supprime un profil hotspot de MikroTik.

        Args:
            profile_name: Nom du profil MikroTik

        Returns:
            Résultat de l'opération
        """
        try:
            self.client._make_request(
                'DELETE',
                f'/api/mikrotik/hotspot/profiles/{profile_name}'
            )

            self._log_operation(
                'delete_profile',
                f"Profil '{profile_name}' supprimé"
            )

            return {'success': True}

        except Exception as e:
            self._log_operation(
                'delete_profile',
                f"Erreur suppression '{profile_name}': {e}",
                level='error'
            )
            return {
                'success': False,
                'error': str(e)
            }

    def sync_profile(self, profile) -> Dict[str, Any]:
        """
        Synchronise un profil Django vers MikroTik (crée ou met à jour).

        Args:
            profile: Instance Profile Django

        Returns:
            Résultat de l'opération
        """
        profile_name = self._get_mikrotik_profile_name(profile)

        # Vérifier si le profil existe
        existing_profiles = self.get_all_hotspot_profiles()
        profile_exists = any(
            p.get('name') == profile_name
            for p in existing_profiles
        )

        if profile_exists:
            return self.update_hotspot_profile(profile)
        else:
            return self.create_hotspot_profile(profile)

    @transaction.atomic
    def sync_all_profiles(self) -> Dict[str, Any]:
        """
        Synchronise tous les profils Django actifs vers MikroTik.

        Returns:
            Statistiques de synchronisation
        """
        from core.models import Profile

        stats = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'errors': []
        }

        profiles = Profile.objects.filter(is_active=True)
        stats['total'] = profiles.count()

        existing_profiles = self.get_all_hotspot_profiles()
        existing_names = {p.get('name') for p in existing_profiles}

        for profile in profiles:
            profile_name = self._get_mikrotik_profile_name(profile)

            if profile_name in existing_names:
                result = self.update_hotspot_profile(profile)
                if result.get('success'):
                    stats['updated'] += 1
            else:
                result = self.create_hotspot_profile(profile)
                if result.get('success'):
                    stats['created'] += 1

            if not result.get('success'):
                stats['errors'].append({
                    'profile': profile.name,
                    'error': result.get('error')
                })

        self._log_operation(
            'sync_all_profiles',
            f"Sync terminée: {stats['created']} créés, {stats['updated']} mis à jour, {len(stats['errors'])} erreurs"
        )

        return stats

    # =========================================================================
    # Gestion des utilisateurs hotspot
    # =========================================================================

    def get_hotspot_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un utilisateur hotspot depuis MikroTik.

        Args:
            username: Nom d'utilisateur

        Returns:
            Données de l'utilisateur ou None
        """
        try:
            result = self.client._make_request(
                'GET',
                f'/api/mikrotik/hotspot/users/{username}'
            )
            return result
        except Exception:
            return None

    def create_hotspot_user(self, user, profile=None) -> Dict[str, Any]:
        """
        Crée un utilisateur hotspot sur MikroTik.

        Args:
            user: Instance User Django
            profile: Profile à utiliser (optionnel, utilise get_effective_profile)

        Returns:
            Résultat de l'opération
        """
        effective_profile = profile or user.get_effective_profile()

        if not effective_profile:
            return {
                'success': False,
                'error': 'Aucun profil effectif pour cet utilisateur'
            }

        if not user.cleartext_password:
            return {
                'success': False,
                'error': 'Mot de passe en clair requis pour MikroTik'
            }

        profile_name = self._get_mikrotik_profile_name(effective_profile)

        data = {
            'username': user.username,
            'password': user.cleartext_password,
            'profile': profile_name,
            'comment': f"Django User ID: {user.id}"
        }

        # Ajouter MAC si disponible
        if user.mac_address:
            data['mac_address'] = user.mac_address

        try:
            result = self.client.create_hotspot_user(**data)

            # Sauvegarder dans MikrotikHotspotUser
            if self.router:
                MikrotikHotspotUser.objects.update_or_create(
                    router=self.router,
                    username=user.username,
                    defaults={
                        'user': user,
                        'password': user.cleartext_password,
                        'mac_address': user.mac_address,
                        'rate_limit': self._build_rate_limit(effective_profile),
                        'is_active': True,
                        'last_sync': timezone.now()
                    }
                )

            self._log_operation(
                'create_hotspot_user',
                f"Utilisateur '{user.username}' créé avec profil '{profile_name}'"
            )

            return {
                'success': True,
                'username': user.username,
                'profile': profile_name
            }

        except Exception as e:
            error_msg = str(e)

            # Si l'utilisateur existe, le mettre à jour
            if 'already exists' in error_msg.lower():
                return self.update_hotspot_user(user, profile)

            self._log_operation(
                'create_hotspot_user',
                f"Erreur création '{user.username}': {e}",
                level='error'
            )
            return {
                'success': False,
                'error': error_msg
            }

    def update_hotspot_user(self, user, profile=None) -> Dict[str, Any]:
        """
        Met à jour un utilisateur hotspot sur MikroTik.

        Args:
            user: Instance User Django
            profile: Profile à utiliser (optionnel)

        Returns:
            Résultat de l'opération
        """
        effective_profile = profile or user.get_effective_profile()

        if not effective_profile:
            return {
                'success': False,
                'error': 'Aucun profil effectif'
            }

        profile_name = self._get_mikrotik_profile_name(effective_profile)

        try:
            # Mettre à jour le profil de l'utilisateur
            self.client.update_hotspot_user(
                username=user.username,
                profile=profile_name,
                disabled=not user.is_radius_enabled
            )

            # Mettre à jour MikrotikHotspotUser local
            if self.router:
                MikrotikHotspotUser.objects.filter(
                    router=self.router,
                    username=user.username
                ).update(
                    rate_limit=self._build_rate_limit(effective_profile),
                    is_disabled=not user.is_radius_enabled,
                    last_sync=timezone.now()
                )

            self._log_operation(
                'update_hotspot_user',
                f"Utilisateur '{user.username}' mis à jour avec profil '{profile_name}'"
            )

            return {
                'success': True,
                'username': user.username,
                'profile': profile_name
            }

        except Exception as e:
            self._log_operation(
                'update_hotspot_user',
                f"Erreur mise à jour '{user.username}': {e}",
                level='error'
            )
            return {
                'success': False,
                'error': str(e)
            }

    def disable_hotspot_user(self, username: str) -> Dict[str, Any]:
        """
        Désactive un utilisateur hotspot sur MikroTik.

        Args:
            username: Nom d'utilisateur

        Returns:
            Résultat de l'opération
        """
        try:
            self.client.update_hotspot_user(
                username=username,
                disabled=True
            )

            if self.router:
                MikrotikHotspotUser.objects.filter(
                    router=self.router,
                    username=username
                ).update(is_disabled=True, last_sync=timezone.now())

            self._log_operation(
                'disable_hotspot_user',
                f"Utilisateur '{username}' désactivé"
            )

            return {'success': True}

        except Exception as e:
            self._log_operation(
                'disable_hotspot_user',
                f"Erreur désactivation '{username}': {e}",
                level='error'
            )
            return {
                'success': False,
                'error': str(e)
            }

    def enable_hotspot_user(self, username: str) -> Dict[str, Any]:
        """
        Réactive un utilisateur hotspot sur MikroTik.

        Args:
            username: Nom d'utilisateur

        Returns:
            Résultat de l'opération
        """
        try:
            self.client.update_hotspot_user(
                username=username,
                disabled=False
            )

            if self.router:
                MikrotikHotspotUser.objects.filter(
                    router=self.router,
                    username=username
                ).update(is_disabled=False, last_sync=timezone.now())

            self._log_operation(
                'enable_hotspot_user',
                f"Utilisateur '{username}' réactivé"
            )

            return {'success': True}

        except Exception as e:
            self._log_operation(
                'enable_hotspot_user',
                f"Erreur réactivation '{username}': {e}",
                level='error'
            )
            return {
                'success': False,
                'error': str(e)
            }

    def delete_hotspot_user(self, username: str) -> Dict[str, Any]:
        """
        Supprime un utilisateur hotspot de MikroTik.

        Args:
            username: Nom d'utilisateur

        Returns:
            Résultat de l'opération
        """
        try:
            self.client.delete_hotspot_user(username)

            if self.router:
                MikrotikHotspotUser.objects.filter(
                    router=self.router,
                    username=username
                ).delete()

            self._log_operation(
                'delete_hotspot_user',
                f"Utilisateur '{username}' supprimé"
            )

            return {'success': True}

        except Exception as e:
            self._log_operation(
                'delete_hotspot_user',
                f"Erreur suppression '{username}': {e}",
                level='error'
            )
            return {
                'success': False,
                'error': str(e)
            }

    # =========================================================================
    # Synchronisation complète utilisateur
    # =========================================================================

    def sync_user(self, user) -> Dict[str, Any]:
        """
        Synchronise complètement un utilisateur vers MikroTik.

        Crée le profil hotspot si nécessaire, puis crée ou met à jour l'utilisateur.

        Args:
            user: Instance User Django

        Returns:
            Résultat de l'opération
        """
        if not user.is_radius_activated:
            return {
                'success': False,
                'error': 'Utilisateur non activé dans RADIUS'
            }

        profile = user.get_effective_profile()
        if not profile:
            return {
                'success': False,
                'error': 'Aucun profil assigné'
            }

        # 1. S'assurer que le profil existe sur MikroTik
        profile_result = self.sync_profile(profile)
        if not profile_result.get('success'):
            return {
                'success': False,
                'error': f"Erreur sync profil: {profile_result.get('error')}"
            }

        # 2. Créer ou mettre à jour l'utilisateur hotspot
        existing_user = self.get_hotspot_user(user.username)

        if existing_user:
            return self.update_hotspot_user(user, profile)
        else:
            return self.create_hotspot_user(user, profile)

    @transaction.atomic
    def sync_all_users(self) -> Dict[str, Any]:
        """
        Synchronise tous les utilisateurs RADIUS activés vers MikroTik.

        Returns:
            Statistiques de synchronisation
        """
        from core.models import User

        stats = {
            'total': 0,
            'synced': 0,
            'skipped': 0,
            'errors': []
        }

        # D'abord synchroniser tous les profils
        profile_stats = self.sync_all_profiles()

        # Puis synchroniser les utilisateurs
        users = User.objects.filter(
            is_radius_activated=True,
            is_active=True
        ).select_related('profile', 'promotion__profile')

        stats['total'] = users.count()

        for user in users:
            profile = user.get_effective_profile()

            if not profile:
                stats['skipped'] += 1
                continue

            result = self.sync_user(user)

            if result.get('success'):
                stats['synced'] += 1
            else:
                stats['errors'].append({
                    'user': user.username,
                    'error': result.get('error')
                })

        self._log_operation(
            'sync_all_users',
            f"Sync terminée: {stats['synced']} synchronisés, {stats['skipped']} ignorés, {len(stats['errors'])} erreurs"
        )

        return stats

    def sync_promotion_users(self, promotion) -> Dict[str, Any]:
        """
        Synchronise tous les utilisateurs d'une promotion vers MikroTik.

        Args:
            promotion: Instance Promotion Django

        Returns:
            Statistiques de synchronisation
        """
        if not promotion.profile:
            return {
                'success': False,
                'error': 'La promotion n\'a pas de profil assigné'
            }

        stats = {
            'total': 0,
            'synced': 0,
            'errors': []
        }

        # S'assurer que le profil existe
        self.sync_profile(promotion.profile)

        users = promotion.users.filter(
            is_radius_activated=True,
            is_active=True,
            profile__isnull=True  # Seulement ceux qui n'ont pas de profil individuel
        )

        stats['total'] = users.count()

        for user in users:
            result = self.sync_user(user)

            if result.get('success'):
                stats['synced'] += 1
            else:
                stats['errors'].append({
                    'user': user.username,
                    'error': result.get('error')
                })

        return stats

    # =========================================================================
    # Import depuis MikroTik
    # =========================================================================

    def import_mikrotik_profile(self, mikrotik_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Importe un profil MikroTik vers Django.

        Args:
            mikrotik_profile: Données du profil MikroTik

        Returns:
            Résultat de l'import avec le profil Django créé
        """
        from core.models import Profile

        name = mikrotik_profile.get('name', 'Imported Profile')

        # Parser le rate-limit
        rate_limit = mikrotik_profile.get('rate-limit', '')
        upload_mbps = 5
        download_mbps = 10

        if rate_limit:
            parts = rate_limit.split('/')
            if len(parts) >= 2:
                try:
                    download_mbps = self._parse_rate(parts[0])
                    upload_mbps = self._parse_rate(parts[1].split()[0] if parts[1] else '5M')
                except (ValueError, IndexError):
                    pass

        # Parser les timeouts
        session_timeout = self._parse_time(mikrotik_profile.get('session-timeout', '8h'))
        idle_timeout = self._parse_time(mikrotik_profile.get('idle-timeout', '10m'))
        shared_users = int(mikrotik_profile.get('shared-users', '1') or '1')

        try:
            profile, created = Profile.objects.update_or_create(
                name=f"[Import] {name}",
                defaults={
                    'bandwidth_upload': upload_mbps,
                    'bandwidth_download': download_mbps,
                    'session_timeout': session_timeout,
                    'idle_timeout': idle_timeout,
                    'simultaneous_use': shared_users,
                    'description': f"Importé depuis MikroTik: {name}"
                }
            )

            return {
                'success': True,
                'profile': profile,
                'created': created
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_rate(self, rate_str: str) -> int:
        """Parse une chaîne de taux MikroTik en Mbps."""
        rate_str = rate_str.strip().upper()
        if rate_str.endswith('M'):
            return int(float(rate_str[:-1]))
        elif rate_str.endswith('K'):
            return max(1, int(float(rate_str[:-1]) / 1024))
        elif rate_str.endswith('G'):
            return int(float(rate_str[:-1]) * 1024)
        else:
            try:
                return max(1, int(float(rate_str)) // (1024 * 1024))
            except ValueError:
                return 1

    def _parse_time(self, time_str: str) -> int:
        """Parse une chaîne de temps MikroTik en secondes."""
        if not time_str:
            return 0

        time_str = time_str.lower().strip()
        total_seconds = 0

        # Format: 1d2h3m4s
        import re

        days = re.search(r'(\d+)d', time_str)
        hours = re.search(r'(\d+)h', time_str)
        minutes = re.search(r'(\d+)m', time_str)
        seconds = re.search(r'(\d+)s', time_str)

        if days:
            total_seconds += int(days.group(1)) * 86400
        if hours:
            total_seconds += int(hours.group(1)) * 3600
        if minutes:
            total_seconds += int(minutes.group(1)) * 60
        if seconds:
            total_seconds += int(seconds.group(1))

        # Si aucun format reconnu, essayer de parser comme nombre de secondes
        if total_seconds == 0:
            try:
                total_seconds = int(time_str)
            except ValueError:
                pass

        return total_seconds

    def import_all_mikrotik_profiles(self) -> Dict[str, Any]:
        """
        Importe tous les profils MikroTik non gérés vers Django.

        Returns:
            Statistiques d'import
        """
        stats = {
            'total': 0,
            'imported': 0,
            'skipped': 0,
            'errors': []
        }

        profiles = self.get_all_hotspot_profiles()
        stats['total'] = len(profiles)

        for profile in profiles:
            name = profile.get('name', '')

            # Ignorer les profils déjà gérés par Django
            if name.startswith(self.PROFILE_PREFIX):
                stats['skipped'] += 1
                continue

            result = self.import_mikrotik_profile(profile)

            if result.get('success'):
                stats['imported'] += 1
            else:
                stats['errors'].append({
                    'profile': name,
                    'error': result.get('error')
                })

        return stats


class FullProfileSyncService:
    """
    Service de haut niveau pour la synchronisation complète des profils.

    Coordonne la synchronisation entre:
    - Django Profile → FreeRADIUS (radcheck/radreply)
    - Django Profile → MikroTik Hotspot Profile
    - Django User → FreeRADIUS + MikroTik
    """

    def __init__(self):
        from radius.services import ProfileRadiusService
        self.radius_service = ProfileRadiusService
        self.mikrotik_service = MikrotikProfileSyncService()

    @transaction.atomic
    def sync_user_full(self, user, profile=None) -> Dict[str, Any]:
        """
        Synchronise complètement un utilisateur vers FreeRADIUS et MikroTik.

        Args:
            user: Instance User Django
            profile: Profile à appliquer (optionnel)

        Returns:
            Résultat combiné de la synchronisation
        """
        results = {
            'radius': None,
            'mikrotik': None,
            'success': False
        }

        effective_profile = profile or user.get_effective_profile()

        if not effective_profile:
            return {
                **results,
                'error': 'Aucun profil assigné'
            }

        # 1. Synchroniser avec FreeRADIUS
        try:
            self.radius_service.sync_user_to_radius(user, effective_profile)
            results['radius'] = {'success': True}
        except Exception as e:
            results['radius'] = {'success': False, 'error': str(e)}

        # 2. Synchroniser avec MikroTik
        mikrotik_result = self.mikrotik_service.sync_user(user)
        results['mikrotik'] = mikrotik_result

        # Succès global si au moins RADIUS réussit
        results['success'] = results['radius'].get('success', False)

        return results

    @transaction.atomic
    def sync_profile_change(self, user, old_profile, new_profile, changed_by=None) -> Dict[str, Any]:
        """
        Gère le changement de profil d'un utilisateur.

        Args:
            user: Utilisateur concerné
            old_profile: Ancien profil
            new_profile: Nouveau profil
            changed_by: Admin ayant effectué le changement

        Returns:
            Résultat de la synchronisation
        """
        from core.models import ProfileHistory

        # Créer l'historique
        ProfileHistory.objects.create(
            user=user,
            old_profile=old_profile,
            new_profile=new_profile,
            changed_by=changed_by,
            change_type='updated' if old_profile else 'assigned'
        )

        # Synchroniser avec le nouveau profil
        return self.sync_user_full(user, new_profile)

    @transaction.atomic
    def sync_promotion_change(self, promotion, old_profile, new_profile) -> Dict[str, Any]:
        """
        Gère le changement de profil d'une promotion.

        Synchronise tous les utilisateurs de la promotion qui n'ont pas
        de profil individuel.

        Args:
            promotion: Promotion concernée
            old_profile: Ancien profil de la promotion
            new_profile: Nouveau profil de la promotion

        Returns:
            Statistiques de synchronisation
        """
        stats = {
            'total': 0,
            'synced': 0,
            'errors': []
        }

        # Utilisateurs sans profil individuel (utilisent le profil promotion)
        users = promotion.users.filter(
            is_radius_activated=True,
            is_active=True,
            profile__isnull=True
        )

        stats['total'] = users.count()

        for user in users:
            result = self.sync_user_full(user, new_profile)

            if result.get('success'):
                stats['synced'] += 1
            else:
                stats['errors'].append({
                    'user': user.username,
                    'error': result.get('error')
                })

        return stats

    def sync_all(self) -> Dict[str, Any]:
        """
        Synchronise tout: profils et utilisateurs.

        Returns:
            Statistiques globales
        """
        # 1. Synchroniser tous les profils vers MikroTik
        profile_stats = self.mikrotik_service.sync_all_profiles()

        # 2. Synchroniser tous les utilisateurs
        user_stats = self.mikrotik_service.sync_all_users()

        return {
            'profiles': profile_stats,
            'users': user_stats
        }
