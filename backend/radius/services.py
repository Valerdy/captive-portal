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

    Attributs RADIUS mappés vers radreply (envoyés dans Access-Accept):
    - Mikrotik-Rate-Limit: Format MikroTik "downloadM/uploadM" (ex: "10M/5M")
    - Session-Timeout: Durée max de session en secondes
    - Idle-Timeout: Délai d'inactivité en secondes
    - ChilliSpot-Max-Total-Octets: Quota total en octets (pour compatibilité)
    - Mikrotik-Total-Limit: Quota total en octets (attribut MikroTik natif)

    Attributs RADIUS mappés vers radcheck (vérification avant auth):
    - Cleartext-Password: Mot de passe en clair
    - Simultaneous-Use: Nombre de connexions simultanées autorisées
    """

    # Liste des attributs radreply à gérer (pour suppression avant mise à jour)
    MANAGED_RADREPLY_ATTRIBUTES = [
        'Mikrotik-Rate-Limit',
        'Session-Timeout',
        'Idle-Timeout',
        'ChilliSpot-Max-Total-Octets',
        'Mikrotik-Total-Limit',
        'WISPr-Bandwidth-Max-Up',
        'WISPr-Bandwidth-Max-Down',
    ]

    # Liste des attributs radcheck à gérer (sauf Cleartext-Password)
    MANAGED_RADCHECK_ATTRIBUTES = [
        'Simultaneous-Use',
        'Max-Total-Octets',
    ]

    @classmethod
    def get_mikrotik_rate_limit(cls, profile: Profile) -> str:
        """
        Génère la valeur Mikrotik-Rate-Limit au format MikroTik Hotspot.

        Format MikroTik: rx-rate/tx-rate
        - rx = ce que l'utilisateur reçoit = download
        - tx = ce que l'utilisateur envoie = upload

        Exemple: "10M/5M" pour 10 Mbps download / 5 Mbps upload
        """
        download = profile.bandwidth_download
        upload = profile.bandwidth_upload
        return f"{download}M/{upload}M"

    @classmethod
    def get_radius_attributes_for_profile(cls, profile: Profile) -> List[Dict[str, str]]:
        """
        Génère tous les attributs RADIUS pour un profil donné.
        Ces attributs sont écrits dans radreply et envoyés dans Access-Accept.

        Attributs générés:
        - Mikrotik-Rate-Limit: Bande passante au format MikroTik "downloadM/uploadM"
        - Session-Timeout: Durée max de session en secondes
        - Idle-Timeout: Délai d'inactivité en secondes
        - ChilliSpot-Max-Total-Octets: Quota total (si limité)
        - Mikrotik-Total-Limit: Quota total format MikroTik (si limité)

        Returns:
            Liste de dictionnaires {attribute, op, value}
        """
        attributes = []

        # =====================================================================
        # BANDE PASSANTE - Format MikroTik uniquement
        # =====================================================================
        # MikroTik Hotspot utilise Mikrotik-Rate-Limit pour appliquer la QoS
        attributes.append({
            'attribute': 'Mikrotik-Rate-Limit',
            'op': ':=',  # := pour écraser toute valeur existante
            'value': cls.get_mikrotik_rate_limit(profile)
        })

        # =====================================================================
        # SESSION-TIMEOUT - Durée maximale de session
        # =====================================================================
        attributes.append({
            'attribute': 'Session-Timeout',
            'op': ':=',
            'value': str(profile.session_timeout)
        })

        # =====================================================================
        # IDLE-TIMEOUT - Délai d'inactivité avant déconnexion
        # =====================================================================
        attributes.append({
            'attribute': 'Idle-Timeout',
            'op': ':=',
            'value': str(profile.idle_timeout)
        })

        # =====================================================================
        # QUOTA - Uniquement si le profil a un quota limité
        # =====================================================================
        if profile.quota_type == 'limited' and profile.data_volume > 0:
            # ChilliSpot-Max-Total-Octets pour compatibilité avec différents NAS
            attributes.append({
                'attribute': 'ChilliSpot-Max-Total-Octets',
                'op': ':=',
                'value': str(profile.data_volume)
            })

            # Mikrotik-Total-Limit pour MikroTik natif
            attributes.append({
                'attribute': 'Mikrotik-Total-Limit',
                'op': ':=',
                'value': str(profile.data_volume)
            })

        return attributes

    @classmethod
    def get_radcheck_attributes_for_profile(cls, profile: Profile) -> List[Dict[str, str]]:
        """
        Génère les attributs radcheck pour un profil donné.
        Ces attributs sont vérifiés AVANT l'authentification.

        Attributs générés:
        - Simultaneous-Use: Nombre de connexions simultanées autorisées

        Note: Cleartext-Password est géré séparément car il dépend de l'utilisateur.

        Returns:
            Liste de dictionnaires {attribute, op, value}
        """
        attributes = []

        # =====================================================================
        # SIMULTANEOUS-USE - Limite de connexions simultanées
        # =====================================================================
        attributes.append({
            'attribute': 'Simultaneous-Use',
            'op': ':=',
            'value': str(profile.simultaneous_use)
        })

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

        Gère:
        - Cleartext-Password: Mot de passe pour authentification
        - Simultaneous-Use: Limite de connexions simultanées

        Les attributs gérés (sauf Cleartext-Password) sont d'abord supprimés
        puis recréés pour garantir la cohérence.
        """
        username = user.username

        # =====================================================================
        # 1. CLEARTEXT-PASSWORD - Authentification
        # =====================================================================
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

        # =====================================================================
        # 2. SUPPRIMER les anciens attributs gérés (sauf Cleartext-Password)
        # =====================================================================
        RadCheck.objects.filter(
            username=username,
            attribute__in=cls.MANAGED_RADCHECK_ATTRIBUTES
        ).delete()

        # =====================================================================
        # 3. CRÉER les nouveaux attributs depuis le profil
        # =====================================================================
        radcheck_attributes = cls.get_radcheck_attributes_for_profile(profile)

        for attr in radcheck_attributes:
            RadCheck.objects.create(
                username=username,
                attribute=attr['attribute'],
                op=attr['op'],
                value=attr['value'],
                statut=True
            )

        logger.debug(f"Updated radcheck for {username}: {len(radcheck_attributes)} profile attributes")

    @classmethod
    def _update_radreply(cls, username: str, profile: Profile) -> None:
        """
        Met à jour les entrées radreply pour un utilisateur.

        Les attributs radreply sont envoyés dans Access-Accept et appliqués par le NAS.
        Pour MikroTik, ces attributs contrôlent la QoS, les timeouts et les quotas.

        Processus:
        1. Supprimer TOUS les attributs gérés pour cet utilisateur
        2. Créer les nouveaux attributs basés sur le profil

        Cela garantit qu'aucun ancien attribut ne reste actif.
        """
        # =====================================================================
        # 1. SUPPRIMER les anciens attributs gérés
        # =====================================================================
        # Supprime uniquement les attributs que nous gérons pour éviter
        # d'effacer d'éventuels attributs personnalisés ajoutés manuellement
        RadReply.objects.filter(
            username=username,
            attribute__in=cls.MANAGED_RADREPLY_ATTRIBUTES
        ).delete()

        # =====================================================================
        # 2. CRÉER les nouveaux attributs depuis le profil
        # =====================================================================
        attributes = cls.get_radius_attributes_for_profile(profile)

        for attr in attributes:
            RadReply.objects.create(
                username=username,
                attribute=attr['attribute'],
                op=attr['op'],
                value=attr['value']
            )

        logger.debug(
            f"Updated radreply for {username}: "
            f"Mikrotik-Rate-Limit={cls.get_mikrotik_rate_limit(profile)}, "
            f"Session-Timeout={profile.session_timeout}, "
            f"Idle-Timeout={profile.idle_timeout}"
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
    def get_user_radius_attributes(cls, username: str) -> Dict[str, Any]:
        """
        Récupère tous les attributs RADIUS d'un utilisateur pour inspection.

        Utile pour le debugging et la vérification de la configuration.

        Returns:
            Dictionnaire avec les attributs radcheck, radreply et radusergroup
        """
        radcheck = list(RadCheck.objects.filter(
            username=username
        ).values('attribute', 'op', 'value', 'statut'))

        radreply = list(RadReply.objects.filter(
            username=username
        ).values('attribute', 'op', 'value'))

        radusergroup = list(RadUserGroup.objects.filter(
            username=username
        ).values('groupname', 'priority'))

        return {
            'username': username,
            'radcheck': radcheck,
            'radreply': radreply,
            'radusergroup': radusergroup,
            'summary': {
                'has_password': any(r['attribute'] == 'Cleartext-Password' for r in radcheck),
                'is_enabled': any(
                    r['attribute'] == 'Cleartext-Password' and r['statut']
                    for r in radcheck
                ),
                'simultaneous_use': next(
                    (r['value'] for r in radcheck if r['attribute'] == 'Simultaneous-Use'),
                    None
                ),
                'rate_limit': next(
                    (r['value'] for r in radreply if r['attribute'] == 'Mikrotik-Rate-Limit'),
                    None
                ),
                'session_timeout': next(
                    (r['value'] for r in radreply if r['attribute'] == 'Session-Timeout'),
                    None
                ),
                'quota': next(
                    (r['value'] for r in radreply if r['attribute'] == 'ChilliSpot-Max-Total-Octets'),
                    None
                ),
            }
        }

    @classmethod
    @transaction.atomic
    def remove_user_from_radius(cls, username: str) -> Dict[str, Any]:
        """
        Supprime complètement un utilisateur de RADIUS.

        Supprime toutes les entrées dans radcheck, radreply et radusergroup.

        Args:
            username: Le nom d'utilisateur à supprimer

        Returns:
            Dictionnaire avec le nombre d'entrées supprimées
        """
        deleted_radcheck = RadCheck.objects.filter(username=username).delete()[0]
        deleted_radreply = RadReply.objects.filter(username=username).delete()[0]
        deleted_radusergroup = RadUserGroup.objects.filter(username=username).delete()[0]

        logger.info(
            f"Removed user {username} from RADIUS: "
            f"{deleted_radcheck} radcheck, {deleted_radreply} radreply, "
            f"{deleted_radusergroup} radusergroup entries"
        )

        return {
            'success': True,
            'deleted': {
                'radcheck': deleted_radcheck,
                'radreply': deleted_radreply,
                'radusergroup': deleted_radusergroup
            }
        }

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
