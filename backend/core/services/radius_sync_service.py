"""
Service centralisé pour la synchronisation FreeRADIUS.
Expose une API simple pour déclencher les synchronisations depuis l'interface web.

Ce service encapsule les appels aux services RADIUS existants et fournit:
- Une interface unifiée pour sync_profiles et sync_radius_groups
- Un suivi des résultats de synchronisation
- Une gestion des erreurs cohérente
"""
import logging
from typing import Dict, Any, Optional, List
from django.db import transaction
from django.utils import timezone

from core.models import Profile, User, Promotion
from radius.services import (
    RadiusProfileGroupService,
    ProfileRadiusService,
    PromotionRadiusService
)

logger = logging.getLogger(__name__)


class RadiusSyncService:
    """
    Service centralisé pour la synchronisation RADIUS.

    Utilisé par:
    - Les endpoints API pour déclencher des syncs manuels
    - Les commandes Django (sync_profiles, sync_radius_groups)
    - Les signaux Django lors de modifications de profils
    """

    @classmethod
    def sync_profile(cls, profile_id: int) -> Dict[str, Any]:
        """
        Synchronise un profil spécifique vers FreeRADIUS.

        Cette méthode:
        1. Crée/met à jour les entrées radgroupreply et radgroupcheck
        2. Met à jour tous les utilisateurs utilisant ce profil

        Args:
            profile_id: ID du profil à synchroniser

        Returns:
            Dict avec le résultat de la synchronisation
        """
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return {
                'success': False,
                'error': f'Profil avec ID {profile_id} non trouvé'
            }

        return cls.sync_profile_instance(profile)

    @classmethod
    @transaction.atomic
    def sync_profile_instance(cls, profile: Profile) -> Dict[str, Any]:
        """
        Synchronise une instance de profil vers FreeRADIUS.
        """
        results = {
            'success': True,
            'profile_id': profile.id,
            'profile_name': profile.name,
            'timestamp': timezone.now().isoformat(),
            'group_sync': None,
            'users_sync': None,
            'errors': []
        }

        try:
            # 1. Synchroniser le profil vers radgroupreply/radgroupcheck
            group_result = RadiusProfileGroupService.sync_profile_to_radius_group(profile)
            results['group_sync'] = {
                'groupname': group_result.get('groupname'),
                'reply_attributes': group_result.get('reply_attributes', 0),
                'check_attributes': group_result.get('check_attributes', 0),
                'success': group_result.get('success', False)
            }

            # Mettre à jour le profil Django
            # Note: is_synced_to_radius est une propriété calculée basée sur radius_group_name et last_radius_sync
            profile.radius_group_name = group_result.get('groupname')
            profile.last_radius_sync = timezone.now()
            profile.save(update_fields=['radius_group_name', 'last_radius_sync'])

        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Erreur sync groupe: {str(e)}")
            logger.error(f"Erreur sync profil {profile.name} vers groupe RADIUS: {e}")

        try:
            # 2. Synchroniser les utilisateurs utilisant ce profil
            users_result = cls._sync_profile_users(profile)
            results['users_sync'] = users_result

        except Exception as e:
            results['errors'].append(f"Erreur sync utilisateurs: {str(e)}")
            logger.error(f"Erreur sync utilisateurs du profil {profile.name}: {e}")

        if results['errors']:
            results['success'] = False

        logger.info(f"Sync profil '{profile.name}': {results}")
        return results

    @classmethod
    def _sync_profile_users(cls, profile: Profile) -> Dict[str, Any]:
        """
        Synchronise tous les utilisateurs utilisant un profil spécifique.

        Inclut:
        - Utilisateurs avec profil direct (User.profile = profile)
        - Utilisateurs via promotion (User.promotion.profile = profile)
        """
        from django.db.models import Q

        # Utilisateurs directs
        direct_users = User.objects.filter(
            profile=profile,
            is_radius_activated=True,
            is_active=True
        )

        # Utilisateurs via promotion
        promotion_users = User.objects.filter(
            Q(profile__isnull=True) &
            Q(promotion__profile=profile) &
            Q(is_radius_activated=True) &
            Q(is_active=True)
        )

        synced = 0
        errors = []

        # Sync utilisateurs directs
        for user in direct_users:
            try:
                RadiusProfileGroupService.sync_user_profile_group(user)
                synced += 1
            except Exception as e:
                errors.append({'user': user.username, 'error': str(e)})

        # Sync utilisateurs via promotion
        for user in promotion_users:
            try:
                RadiusProfileGroupService.sync_user_profile_group(user)
                synced += 1
            except Exception as e:
                errors.append({'user': user.username, 'error': str(e)})

        return {
            'total': direct_users.count() + promotion_users.count(),
            'direct_users': direct_users.count(),
            'promotion_users': promotion_users.count(),
            'synced': synced,
            'errors': errors
        }

    @classmethod
    def sync_all_profiles(cls) -> Dict[str, Any]:
        """
        Synchronise tous les profils actifs vers FreeRADIUS.

        Équivalent à: python manage.py sync_radius_groups --profiles-only
        """
        profiles = Profile.objects.filter(is_active=True)

        results = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'total_profiles': profiles.count(),
            'synced_profiles': 0,
            'errors': [],
            'details': []
        }

        for profile in profiles:
            try:
                result = RadiusProfileGroupService.sync_profile_to_radius_group(profile)

                if result.get('success'):
                    results['synced_profiles'] += 1

                    # Mettre à jour le profil Django
                    # Note: is_synced_to_radius est une propriété calculée
                    profile.radius_group_name = result.get('groupname')
                    profile.last_radius_sync = timezone.now()
                    profile.save(update_fields=['radius_group_name', 'last_radius_sync'])

                results['details'].append({
                    'profile_id': profile.id,
                    'profile_name': profile.name,
                    'groupname': result.get('groupname'),
                    'success': result.get('success', False)
                })

            except Exception as e:
                results['errors'].append({
                    'profile': profile.name,
                    'error': str(e)
                })

        if results['errors']:
            results['success'] = False

        logger.info(
            f"Sync tous profils: {results['synced_profiles']}/{results['total_profiles']}, "
            f"{len(results['errors'])} erreurs"
        )

        return results

    @classmethod
    def sync_all_users(cls) -> Dict[str, Any]:
        """
        Synchronise tous les utilisateurs RADIUS vers leurs groupes de profil.

        Équivalent à: python manage.py sync_radius_groups --users-only
        """
        result = RadiusProfileGroupService.sync_all_users_to_groups()
        result['timestamp'] = timezone.now().isoformat()
        return result

    @classmethod
    def sync_all(cls) -> Dict[str, Any]:
        """
        Synchronisation complète: profils + utilisateurs.

        Équivalent à: python manage.py sync_radius_groups
        """
        results = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'profiles': None,
            'users': None
        }

        # 1. Synchroniser les profils
        profiles_result = cls.sync_all_profiles()
        results['profiles'] = {
            'total': profiles_result.get('total_profiles', 0),
            'synced': profiles_result.get('synced_profiles', 0),
            'errors': len(profiles_result.get('errors', []))
        }

        # 2. Synchroniser les utilisateurs
        users_result = cls.sync_all_users()
        results['users'] = {
            'total': users_result.get('total', 0),
            'assigned': users_result.get('assigned', 0),
            'no_profile': users_result.get('no_profile', 0),
            'errors': len(users_result.get('errors', []))
        }

        if results['profiles']['errors'] > 0 or results['users']['errors'] > 0:
            results['success'] = False

        return results

    @classmethod
    def sync_user(cls, user_id: int) -> Dict[str, Any]:
        """
        Synchronise un utilisateur spécifique vers FreeRADIUS.
        """
        try:
            user = User.objects.select_related(
                'profile', 'promotion', 'promotion__profile'
            ).get(id=user_id)
        except User.DoesNotExist:
            return {
                'success': False,
                'error': f'Utilisateur avec ID {user_id} non trouvé'
            }

        return cls.sync_user_instance(user)

    @classmethod
    def sync_user_instance(cls, user: User) -> Dict[str, Any]:
        """
        Synchronise une instance utilisateur vers FreeRADIUS.
        """
        if not user.is_radius_activated:
            return {
                'success': False,
                'error': f"L'utilisateur {user.username} n'est pas activé dans RADIUS"
            }

        profile = user.get_effective_profile()
        if not profile:
            return {
                'success': False,
                'error': f"L'utilisateur {user.username} n'a pas de profil effectif"
            }

        try:
            # Sync vers groupe RADIUS
            group_result = RadiusProfileGroupService.sync_user_profile_group(user)

            # Sync attributs individuels (radcheck/radreply)
            ProfileRadiusService.sync_user_to_radius(user, profile)

            return {
                'success': True,
                'username': user.username,
                'profile': profile.name,
                'groupname': group_result.get('groupname'),
                'timestamp': timezone.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Erreur sync utilisateur {user.username}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    def sync_promotion(cls, promotion_id: int) -> Dict[str, Any]:
        """
        Synchronise tous les utilisateurs d'une promotion.
        """
        try:
            promotion = Promotion.objects.select_related('profile').get(id=promotion_id)
        except Promotion.DoesNotExist:
            return {
                'success': False,
                'error': f'Promotion avec ID {promotion_id} non trouvée'
            }

        if not promotion.profile:
            return {
                'success': False,
                'error': f"La promotion '{promotion.name}' n'a pas de profil assigné"
            }

        result = PromotionRadiusService.sync_promotion_users(promotion)
        result['promotion_name'] = promotion.name
        result['profile_name'] = promotion.profile.name
        result['timestamp'] = timezone.now().isoformat()

        return result

    @classmethod
    def get_sync_status(cls) -> Dict[str, Any]:
        """
        Retourne le statut global de synchronisation RADIUS.
        """
        from django.db.models import Count, Q

        profiles = Profile.objects.filter(is_active=True)
        users = User.objects.filter(is_radius_activated=True, is_active=True)

        # Compter les profils synchronisés
        synced_profiles = profiles.filter(is_synced_to_radius=True).count()

        # Compter les utilisateurs avec groupe RADIUS
        from radius.models import RadUserGroup
        users_in_groups = RadUserGroup.objects.filter(
            groupname__startswith='profile_'
        ).values('username').distinct().count()

        return {
            'profiles': {
                'total': profiles.count(),
                'synced': synced_profiles,
                'pending': profiles.count() - synced_profiles
            },
            'users': {
                'total_activated': users.count(),
                'in_radius_groups': users_in_groups
            },
            'last_check': timezone.now().isoformat()
        }

    @classmethod
    def activate_profile_in_radius(cls, profile_id: int) -> Dict[str, Any]:
        """
        Active un profil dans RADIUS (is_radius_enabled=True) et synchronise.

        C'est l'endpoint principal appelé par le bouton "Activer dans RADIUS".
        """
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return {
                'success': False,
                'error': f'Profil avec ID {profile_id} non trouvé'
            }

        if not profile.is_active:
            return {
                'success': False,
                'error': f"Le profil '{profile.name}' doit être actif pour l'activer dans RADIUS"
            }

        # Activer le profil
        profile.is_radius_enabled = True
        profile.save(update_fields=['is_radius_enabled'])

        # Synchroniser
        sync_result = cls.sync_profile_instance(profile)

        return {
            'success': sync_result['success'],
            'message': f"Profil '{profile.name}' activé et synchronisé dans RADIUS",
            'profile_id': profile.id,
            'profile_name': profile.name,
            'groupname': sync_result.get('group_sync', {}).get('groupname'),
            'users_synced': sync_result.get('users_sync', {}).get('synced', 0),
            'errors': sync_result.get('errors', []),
            'timestamp': timezone.now().isoformat()
        }

    @classmethod
    def deactivate_profile_in_radius(cls, profile_id: int) -> Dict[str, Any]:
        """
        Désactive un profil dans RADIUS et supprime son groupe.
        """
        try:
            profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return {
                'success': False,
                'error': f'Profil avec ID {profile_id} non trouvé'
            }

        # Désactiver le profil
        # Note: is_synced_to_radius est une propriété, on efface radius_group_name
        profile.is_radius_enabled = False
        profile.radius_group_name = None
        profile.last_radius_sync = None
        profile.save(update_fields=['is_radius_enabled', 'radius_group_name', 'last_radius_sync'])

        # Supprimer du groupe RADIUS
        try:
            result = RadiusProfileGroupService.remove_profile_from_radius_group(profile)

            return {
                'success': True,
                'message': f"Profil '{profile.name}' désactivé de RADIUS",
                'profile_id': profile.id,
                'profile_name': profile.name,
                'removed_group': result.get('groupname'),
                'affected_users': result.get('affected_users', []),
                'timestamp': timezone.now().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Instance singleton
radius_sync_service = RadiusSyncService()
