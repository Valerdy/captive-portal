"""
Service de synchronisation des profils vers FreeRADIUS.
Gère le mapping des attributs Django Profile vers les tables RADIUS.
"""

from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from typing import Optional, Dict, Any, List, Tuple
import logging

from .models import RadCheck, RadReply, RadUserGroup, RadAcct
from core.models import User, Profile, Promotion, UserProfileUsage, UserDisconnectionLog

logger = logging.getLogger(__name__)


class ProfileRadiusService:
    """
    Service principal pour la synchronisation des profils vers FreeRADIUS.

    Attributs RADIUS mappés:
    - WISPr-Bandwidth-Max-Up: Bande passante upload en bps
    - WISPr-Bandwidth-Max-Down: Bande passante download en bps
    - Mikrotik-Rate-Limit: Format MikroTik pour bande passante (rx/tx)
    - Session-Timeout: Durée max de session en secondes
    - Idle-Timeout: Délai d'inactivité en secondes
    - Simultaneous-Use: Nombre de connexions simultanées
    - Max-Total-Octets: Quota total en octets (radcheck)
    """

    # Mapping des attributs de profil vers RADIUS
    RADIUS_ATTRIBUTES = {
        'bandwidth_upload': {
            'attribute': 'WISPr-Bandwidth-Max-Up',
            'op': '=',
            'transform': lambda mbps: str(mbps * 1024 * 1024)  # Mbps -> bps
        },
        'bandwidth_download': {
            'attribute': 'WISPr-Bandwidth-Max-Down',
            'op': '=',
            'transform': lambda mbps: str(mbps * 1024 * 1024)  # Mbps -> bps
        },
        'session_timeout': {
            'attribute': 'Session-Timeout',
            'op': '=',
            'transform': lambda seconds: str(seconds)
        },
        'idle_timeout': {
            'attribute': 'Idle-Timeout',
            'op': '=',
            'transform': lambda seconds: str(seconds)
        },
        'simultaneous_use': {
            'attribute': 'Simultaneous-Use',
            'op': ':=',
            'transform': lambda count: str(count)
        },
    }

    @classmethod
    def get_mikrotik_rate_limit(cls, profile: Profile) -> str:
        """
        Génère la valeur Mikrotik-Rate-Limit au format MikroTik.
        Format: rx-rate[/tx-rate] où rx=download, tx=upload
        Exemple: "10M/5M" pour 10 Mbps down / 5 Mbps up
        """
        upload = profile.bandwidth_upload
        download = profile.bandwidth_download
        return f"{download}M/{upload}M"

    @classmethod
    def get_radius_attributes_for_profile(cls, profile: Profile) -> List[Dict[str, str]]:
        """
        Génère tous les attributs RADIUS pour un profil donné.

        Returns:
            Liste de dictionnaires {attribute, op, value}
        """
        attributes = []

        # Attributs WISPr pour bande passante
        attributes.append({
            'attribute': 'WISPr-Bandwidth-Max-Up',
            'op': '=',
            'value': str(profile.bandwidth_upload * 1024 * 1024)  # Mbps -> bps
        })
        attributes.append({
            'attribute': 'WISPr-Bandwidth-Max-Down',
            'op': '=',
            'value': str(profile.bandwidth_download * 1024 * 1024)  # Mbps -> bps
        })

        # Format MikroTik pour compatibilité Hotspot
        attributes.append({
            'attribute': 'Mikrotik-Rate-Limit',
            'op': '=',
            'value': cls.get_mikrotik_rate_limit(profile)
        })

        # Session-Timeout
        attributes.append({
            'attribute': 'Session-Timeout',
            'op': '=',
            'value': str(profile.session_timeout)
        })

        # Idle-Timeout
        attributes.append({
            'attribute': 'Idle-Timeout',
            'op': '=',
            'value': str(profile.idle_timeout)
        })

        # Simultaneous-Use (dans radcheck, pas radreply)
        # Géré séparément car c'est un check, pas un reply

        return attributes

    @classmethod
    @transaction.atomic
    def sync_user_to_radius(cls, user: User, profile: Optional[Profile] = None) -> bool:
        """
        Synchronise un utilisateur vers FreeRADIUS avec son profil effectif.

        Args:
            user: L'utilisateur à synchroniser
            profile: Profil à appliquer (si None, utilise get_effective_profile())

        Returns:
            True si la synchronisation a réussi
        """
        if not user.is_radius_activated:
            logger.warning(f"User {user.username} is not RADIUS activated, skipping sync")
            return False

        # Déterminer le profil effectif
        effective_profile = profile or user.get_effective_profile()

        if not effective_profile:
            logger.warning(f"User {user.username} has no effective profile")
            return False

        username = user.username

        try:
            # 1. Mettre à jour radcheck avec le quota et Simultaneous-Use
            cls._update_radcheck(user, effective_profile)

            # 2. Mettre à jour radreply avec les attributs du profil
            cls._update_radreply(username, effective_profile)

            # 3. Mettre à jour radusergroup
            cls._update_radusergroup(username, user.role)

            logger.info(f"Successfully synced user {username} with profile {effective_profile.name}")
            return True

        except Exception as e:
            logger.error(f"Error syncing user {username} to RADIUS: {e}")
            raise

    @classmethod
    def _update_radcheck(cls, user: User, profile: Profile) -> None:
        """
        Met à jour les entrées radcheck pour un utilisateur.
        Gère: Cleartext-Password, statut, quota, Simultaneous-Use
        """
        username = user.username

        # Mettre à jour l'entrée principale du mot de passe
        radcheck, created = RadCheck.objects.get_or_create(
            username=username,
            attribute='Cleartext-Password',
            defaults={
                'op': ':=',
                'value': user.cleartext_password or '',
                'statut': user.is_radius_enabled,
                'quota': profile.data_volume if profile.quota_type == 'limited' else None
            }
        )

        if not created:
            radcheck.value = user.cleartext_password or ''
            radcheck.statut = user.is_radius_enabled
            radcheck.quota = profile.data_volume if profile.quota_type == 'limited' else None
            radcheck.save()

        # Ajouter/Mettre à jour Simultaneous-Use
        RadCheck.objects.update_or_create(
            username=username,
            attribute='Simultaneous-Use',
            defaults={
                'op': ':=',
                'value': str(profile.simultaneous_use),
                'statut': True
            }
        )

        # Ajouter Max-Total-Octets si quota limité
        if profile.quota_type == 'limited':
            RadCheck.objects.update_or_create(
                username=username,
                attribute='Max-Total-Octets',
                defaults={
                    'op': ':=',
                    'value': str(profile.data_volume),
                    'statut': True
                }
            )
        else:
            # Supprimer l'attribut si quota illimité
            RadCheck.objects.filter(
                username=username,
                attribute='Max-Total-Octets'
            ).delete()

    @classmethod
    def _update_radreply(cls, username: str, profile: Profile) -> None:
        """
        Met à jour les entrées radreply pour un utilisateur.
        """
        # Supprimer les anciennes entrées
        RadReply.objects.filter(username=username).delete()

        # Créer les nouvelles entrées
        attributes = cls.get_radius_attributes_for_profile(profile)
        for attr in attributes:
            RadReply.objects.create(
                username=username,
                attribute=attr['attribute'],
                op=attr['op'],
                value=attr['value']
            )

    @classmethod
    def _update_radusergroup(cls, username: str, role: str) -> None:
        """
        Met à jour l'appartenance aux groupes RADIUS.
        """
        # Supprimer les anciennes appartenances
        RadUserGroup.objects.filter(username=username).delete()

        # Créer la nouvelle appartenance
        RadUserGroup.objects.create(
            username=username,
            groupname=role,
            priority=1
        )

    @classmethod
    @transaction.atomic
    def activate_user_radius(cls, user: User, activated_by: Optional[User] = None) -> Dict[str, Any]:
        """
        Active un utilisateur dans RADIUS (première provisioning).

        Args:
            user: L'utilisateur à activer
            activated_by: L'admin qui effectue l'activation

        Returns:
            Dictionnaire avec le statut de l'opération
        """
        if user.is_radius_activated:
            return {
                'success': False,
                'error': 'Utilisateur déjà activé dans RADIUS'
            }

        if not user.cleartext_password:
            return {
                'success': False,
                'error': 'Mot de passe en clair requis pour activation RADIUS'
            }

        profile = user.get_effective_profile()
        if not profile:
            return {
                'success': False,
                'error': 'Aucun profil assigné à cet utilisateur'
            }

        try:
            # Créer les entrées RADIUS
            cls.sync_user_to_radius(user, profile)

            # Marquer l'utilisateur comme activé
            user.is_radius_activated = True
            user.is_radius_enabled = True
            user.save()

            # Créer/réinitialiser le suivi d'utilisation
            usage, created = UserProfileUsage.objects.get_or_create(
                user=user,
                defaults={'activation_date': timezone.now()}
            )
            if not created:
                usage.reset_all()

            logger.info(f"User {user.username} activated in RADIUS by {activated_by}")

            return {
                'success': True,
                'message': f"Utilisateur {user.username} activé dans RADIUS",
                'profile': profile.name
            }

        except Exception as e:
            logger.error(f"Error activating user {user.username}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    @transaction.atomic
    def deactivate_user_radius(cls, user: User, reason: str = 'manual',
                               deactivated_by: Optional[User] = None) -> Dict[str, Any]:
        """
        Désactive l'accès RADIUS d'un utilisateur.

        Args:
            user: L'utilisateur à désactiver
            reason: Raison de la désactivation
            deactivated_by: L'admin qui effectue la désactivation
        """
        if not user.is_radius_activated:
            return {
                'success': False,
                'error': 'Utilisateur non activé dans RADIUS'
            }

        try:
            # Mettre à jour le statut dans radcheck
            RadCheck.objects.filter(
                username=user.username,
                attribute='Cleartext-Password'
            ).update(statut=False)

            # Marquer comme désactivé dans Django
            user.is_radius_enabled = False
            user.save()

            # Logger la déconnexion
            usage = getattr(user, 'profile_usage', None)
            UserDisconnectionLog.objects.create(
                user=user,
                reason=reason,
                description=f"Désactivé par {deactivated_by.username if deactivated_by else 'système'}",
                quota_used=usage.used_total if usage else None,
                quota_limit=user.get_effective_profile().data_volume if user.get_effective_profile() else None
            )

            logger.info(f"User {user.username} deactivated in RADIUS: {reason}")

            return {
                'success': True,
                'message': f"Accès RADIUS désactivé pour {user.username}"
            }

        except Exception as e:
            logger.error(f"Error deactivating user {user.username}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    @transaction.atomic
    def reactivate_user_radius(cls, user: User, reactivated_by: Optional[User] = None) -> Dict[str, Any]:
        """
        Réactive l'accès RADIUS d'un utilisateur précédemment désactivé.
        """
        if not user.is_radius_activated:
            return {
                'success': False,
                'error': 'Utilisateur non provisionné dans RADIUS'
            }

        if user.is_radius_enabled:
            return {
                'success': False,
                'error': 'Utilisateur déjà actif'
            }

        try:
            # Réactiver dans radcheck
            RadCheck.objects.filter(
                username=user.username,
                attribute='Cleartext-Password'
            ).update(statut=True)

            # Marquer comme actif dans Django
            user.is_radius_enabled = True
            user.save()

            # Marquer les logs de déconnexion comme résolus
            UserDisconnectionLog.objects.filter(
                user=user,
                is_active=True
            ).update(
                is_active=False,
                reconnected_at=timezone.now(),
                reconnected_by=reactivated_by
            )

            logger.info(f"User {user.username} reactivated in RADIUS by {reactivated_by}")

            return {
                'success': True,
                'message': f"Accès RADIUS réactivé pour {user.username}"
            }

        except Exception as e:
            logger.error(f"Error reactivating user {user.username}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class PromotionRadiusService:
    """
    Service pour la gestion des promotions dans RADIUS.
    Permet d'activer/désactiver en masse les utilisateurs d'une promotion.
    """

    @classmethod
    @transaction.atomic
    def sync_promotion_users(cls, promotion: Promotion) -> Dict[str, Any]:
        """
        Synchronise tous les utilisateurs d'une promotion avec le profil de la promotion.

        Args:
            promotion: La promotion à synchroniser

        Returns:
            Dictionnaire avec les statistiques de synchronisation
        """
        if not promotion.profile:
            return {
                'success': False,
                'error': 'La promotion n\'a pas de profil assigné'
            }

        users = promotion.users.filter(is_radius_activated=True)
        synced = 0
        errors = []

        for user in users:
            try:
                ProfileRadiusService.sync_user_to_radius(user, promotion.profile)
                synced += 1
            except Exception as e:
                errors.append({
                    'user': user.username,
                    'error': str(e)
                })

        return {
            'success': len(errors) == 0,
            'total': users.count(),
            'synced': synced,
            'errors': errors
        }

    @classmethod
    @transaction.atomic
    def activate_promotion(cls, promotion: Promotion, activated_by: Optional[User] = None) -> Dict[str, Any]:
        """
        Active tous les utilisateurs d'une promotion dans RADIUS.
        """
        if not promotion.profile:
            return {
                'success': False,
                'error': 'La promotion n\'a pas de profil assigné'
            }

        users = promotion.users.filter(
            is_radius_activated=False,
            is_active=True,
            cleartext_password__isnull=False
        ).exclude(cleartext_password='')

        activated = 0
        errors = []

        for user in users:
            result = ProfileRadiusService.activate_user_radius(user, activated_by)
            if result['success']:
                activated += 1
            else:
                errors.append({
                    'user': user.username,
                    'error': result.get('error', 'Unknown error')
                })

        return {
            'success': True,
            'total': users.count(),
            'activated': activated,
            'errors': errors
        }

    @classmethod
    @transaction.atomic
    def deactivate_promotion(cls, promotion: Promotion, reason: str = 'manual',
                             deactivated_by: Optional[User] = None) -> Dict[str, Any]:
        """
        Désactive tous les utilisateurs d'une promotion dans RADIUS.
        """
        users = promotion.users.filter(
            is_radius_activated=True,
            is_radius_enabled=True
        )

        deactivated = 0
        errors = []

        for user in users:
            result = ProfileRadiusService.deactivate_user_radius(user, reason, deactivated_by)
            if result['success']:
                deactivated += 1
            else:
                errors.append({
                    'user': user.username,
                    'error': result.get('error', 'Unknown error')
                })

        return {
            'success': True,
            'total': users.count(),
            'deactivated': deactivated,
            'errors': errors
        }


class QuotaEnforcementService:
    """
    Service de vérification et d'application des quotas.
    Utilisé par les tâches périodiques pour désactiver les utilisateurs dépassant leurs quotas.
    """

    @classmethod
    def check_user_quota(cls, user: User) -> Dict[str, Any]:
        """
        Vérifie si un utilisateur a dépassé son quota.

        Returns:
            Dictionnaire avec le statut du quota
        """
        profile = user.get_effective_profile()
        if not profile:
            return {'exceeded': False, 'reason': None}

        usage = getattr(user, 'profile_usage', None)
        if not usage:
            return {'exceeded': False, 'reason': None}

        # Vérifier le quota total
        if profile.quota_type == 'limited':
            if usage.used_total >= profile.data_volume:
                return {
                    'exceeded': True,
                    'reason': 'quota_exceeded',
                    'used': usage.used_total,
                    'limit': profile.data_volume
                }

        # Vérifier les limites périodiques
        if profile.daily_limit and usage.used_today >= profile.daily_limit:
            return {
                'exceeded': True,
                'reason': 'daily_limit',
                'used': usage.used_today,
                'limit': profile.daily_limit
            }

        if profile.weekly_limit and usage.used_week >= profile.weekly_limit:
            return {
                'exceeded': True,
                'reason': 'weekly_limit',
                'used': usage.used_week,
                'limit': profile.weekly_limit
            }

        if profile.monthly_limit and usage.used_month >= profile.monthly_limit:
            return {
                'exceeded': True,
                'reason': 'monthly_limit',
                'used': usage.used_month,
                'limit': profile.monthly_limit
            }

        return {'exceeded': False, 'reason': None}

    @classmethod
    def check_user_validity(cls, user: User) -> Dict[str, Any]:
        """
        Vérifie si le profil d'un utilisateur a expiré.
        """
        profile = user.get_effective_profile()
        if not profile:
            return {'expired': False, 'reason': None}

        usage = getattr(user, 'profile_usage', None)
        if not usage:
            return {'expired': False, 'reason': None}

        expiry_date = usage.activation_date + timedelta(days=profile.validity_duration)
        if timezone.now() > expiry_date:
            return {
                'expired': True,
                'reason': 'validity_expired',
                'expiry_date': expiry_date,
                'days_overdue': (timezone.now() - expiry_date).days
            }

        return {'expired': False, 'reason': None}

    @classmethod
    @transaction.atomic
    def enforce_quotas(cls) -> Dict[str, Any]:
        """
        Vérifie et applique les quotas pour tous les utilisateurs actifs.
        Désactive ceux qui ont dépassé leurs quotas ou dont le profil a expiré.

        Cette méthode est appelée par la tâche périodique.
        """
        users = User.objects.filter(
            is_radius_activated=True,
            is_radius_enabled=True
        ).select_related('profile', 'promotion__profile', 'profile_usage')

        disabled_quota = 0
        disabled_validity = 0
        errors = []

        for user in users:
            try:
                # Vérifier le quota
                quota_status = cls.check_user_quota(user)
                if quota_status['exceeded']:
                    ProfileRadiusService.deactivate_user_radius(
                        user,
                        reason=quota_status['reason']
                    )
                    disabled_quota += 1
                    continue

                # Vérifier la validité
                validity_status = cls.check_user_validity(user)
                if validity_status['expired']:
                    ProfileRadiusService.deactivate_user_radius(
                        user,
                        reason='validity_expired'
                    )
                    disabled_validity += 1

            except Exception as e:
                errors.append({
                    'user': user.username,
                    'error': str(e)
                })

        logger.info(f"Quota enforcement: {disabled_quota} quota exceeded, {disabled_validity} expired")

        return {
            'total_checked': users.count(),
            'disabled_quota': disabled_quota,
            'disabled_validity': disabled_validity,
            'errors': errors
        }

    @classmethod
    def sync_usage_from_radacct(cls) -> Dict[str, Any]:
        """
        Synchronise les données de consommation depuis radacct vers UserProfileUsage.

        Cette méthode récupère les données de session FreeRADIUS et met à jour
        les compteurs de consommation dans Django.
        """
        from django.db.models import Sum
        from django.db.models.functions import Coalesce

        users = User.objects.filter(
            is_radius_activated=True
        ).select_related('profile_usage')

        updated = 0
        errors = []

        for user in users:
            try:
                # Récupérer la consommation totale depuis radacct
                acct_data = RadAcct.objects.filter(
                    username=user.username
                ).aggregate(
                    total_input=Coalesce(Sum('acctinputoctets'), 0),
                    total_output=Coalesce(Sum('acctoutputoctets'), 0)
                )

                total_bytes = acct_data['total_input'] + acct_data['total_output']

                # Mettre à jour UserProfileUsage
                usage, created = UserProfileUsage.objects.get_or_create(
                    user=user,
                    defaults={'used_total': total_bytes}
                )

                if not created and usage.used_total != total_bytes:
                    # Calculer la différence pour les compteurs périodiques
                    delta = total_bytes - usage.used_total
                    if delta > 0:
                        usage.used_today += delta
                        usage.used_week += delta
                        usage.used_month += delta
                    usage.used_total = total_bytes
                    usage.check_exceeded()
                    usage.save()
                    updated += 1

            except Exception as e:
                errors.append({
                    'user': user.username,
                    'error': str(e)
                })

        logger.info(f"Usage sync: {updated} users updated from radacct")

        return {
            'total': users.count(),
            'updated': updated,
            'errors': errors
        }


class ProfileAssignmentService:
    """
    Service pour l'assignation de profils aux utilisateurs et promotions.
    """

    @classmethod
    @transaction.atomic
    def assign_profile_to_user(cls, user: User, profile: Profile,
                                assigned_by: Optional[User] = None) -> Dict[str, Any]:
        """
        Assigne un profil à un utilisateur individuel.
        """
        from core.models import ProfileHistory

        old_profile = user.profile
        user.profile = profile
        user.save()

        # Créer l'historique
        ProfileHistory.objects.create(
            user=user,
            old_profile=old_profile,
            new_profile=profile,
            changed_by=assigned_by,
            change_type='assigned' if not old_profile else 'updated'
        )

        # Synchroniser avec RADIUS si l'utilisateur est activé
        if user.is_radius_activated:
            ProfileRadiusService.sync_user_to_radius(user, profile)

        return {
            'success': True,
            'message': f"Profil '{profile.name}' assigné à {user.username}"
        }

    @classmethod
    @transaction.atomic
    def assign_profile_to_promotion(cls, promotion: Promotion, profile: Profile,
                                     assigned_by: Optional[User] = None) -> Dict[str, Any]:
        """
        Assigne un profil à une promotion et synchronise tous ses utilisateurs.
        """
        old_profile = promotion.profile
        promotion.profile = profile
        promotion.save()

        # Synchroniser tous les utilisateurs de la promotion
        result = PromotionRadiusService.sync_promotion_users(promotion)

        return {
            'success': result['success'],
            'message': f"Profil '{profile.name}' assigné à la promotion {promotion.name}",
            'synced_users': result.get('synced', 0),
            'errors': result.get('errors', [])
        }

    @classmethod
    @transaction.atomic
    def remove_profile_from_user(cls, user: User, removed_by: Optional[User] = None) -> Dict[str, Any]:
        """
        Retire le profil individuel d'un utilisateur.
        L'utilisateur utilisera alors le profil de sa promotion.
        """
        from core.models import ProfileHistory

        old_profile = user.profile
        if not old_profile:
            return {
                'success': False,
                'error': 'Aucun profil individuel à retirer'
            }

        user.profile = None
        user.save()

        # Créer l'historique
        ProfileHistory.objects.create(
            user=user,
            old_profile=old_profile,
            new_profile=None,
            changed_by=removed_by,
            change_type='removed'
        )

        # Synchroniser avec le profil de la promotion
        if user.is_radius_activated:
            new_profile = user.get_effective_profile()
            if new_profile:
                ProfileRadiusService.sync_user_to_radius(user, new_profile)

        return {
            'success': True,
            'message': f"Profil retiré de {user.username}"
        }


class MikrotikProfileService:
    """
    Service pour la détection et synchronisation des profils MikroTik.
    Communique avec l'agent MikroTik Node.js.
    """

    MIKROTIK_AGENT_URL = 'http://localhost:3001'

    @classmethod
    def get_hotspot_profiles(cls) -> List[Dict[str, Any]]:
        """
        Récupère la liste des profils Hotspot depuis MikroTik.
        """
        import requests

        try:
            response = requests.get(
                f"{cls.MIKROTIK_AGENT_URL}/api/mikrotik/hotspot/profiles",
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('profiles', [])
        except requests.RequestException as e:
            logger.error(f"Error fetching MikroTik profiles: {e}")
            return []

    @classmethod
    def get_default_profile(cls) -> Optional[Dict[str, Any]]:
        """
        Récupère le profil par défaut du Hotspot MikroTik.
        """
        profiles = cls.get_hotspot_profiles()
        for profile in profiles:
            if profile.get('name') == 'default' or profile.get('default', False):
                return profile
        return profiles[0] if profiles else None

    @classmethod
    def map_mikrotik_to_django_profile(cls, mikrotik_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mappe les paramètres d'un profil MikroTik vers les champs Django Profile.
        """
        # Parser rate-limit si présent (format: "rx/tx" ou "rx/tx rx/tx")
        rate_limit = mikrotik_profile.get('rate-limit', '')
        upload_mbps = 5  # défaut
        download_mbps = 10  # défaut

        if rate_limit:
            parts = rate_limit.split('/')
            if len(parts) >= 2:
                try:
                    download_mbps = cls._parse_rate(parts[0])
                    upload_mbps = cls._parse_rate(parts[1].split()[0])
                except (ValueError, IndexError):
                    pass

        return {
            'name': mikrotik_profile.get('name', 'Imported Profile'),
            'bandwidth_upload': upload_mbps,
            'bandwidth_download': download_mbps,
            'session_timeout': int(mikrotik_profile.get('session-timeout', 28800)),
            'idle_timeout': int(mikrotik_profile.get('idle-timeout', 600)),
            'simultaneous_use': 1,
        }

    @classmethod
    def _parse_rate(cls, rate_str: str) -> int:
        """
        Parse une chaîne de taux MikroTik (ex: "10M", "5k") en Mbps.
        """
        rate_str = rate_str.strip().upper()
        if rate_str.endswith('M'):
            return int(rate_str[:-1])
        elif rate_str.endswith('K'):
            return max(1, int(rate_str[:-1]) // 1024)
        elif rate_str.endswith('G'):
            return int(rate_str[:-1]) * 1024
        else:
            # Assume bits per second
            try:
                return max(1, int(rate_str) // (1024 * 1024))
            except ValueError:
                return 1
