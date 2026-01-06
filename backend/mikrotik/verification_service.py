"""
Service de vérification de l'application des profils RADIUS sur MikroTik.

Ce service permet de comparer les attributs RADIUS attendus (configurés dans Django/FreeRADIUS)
avec les attributs réellement appliqués sur le routeur MikroTik pour les utilisateurs connectés.

Workflow:
1. Récupère les sessions actives du hotspot MikroTik via l'agent
2. Pour chaque session, identifie l'utilisateur Django correspondant
3. Récupère les attributs attendus depuis FreeRADIUS (radgroupreply via radusergroup)
4. Compare avec les attributs réellement appliqués par MikroTik
5. Retourne un rapport détaillé avec statut (OK/WARNING/ERROR)

Auteur: Claude
Date: 2024-01-06
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from django.utils import timezone
from django.db import models

from .utils import MikrotikAgentClient
from core.models import User, AdminAuditLog
from radius.models import (
    RadUserGroup, RadGroupReply, RadGroupCheck,
    RadCheck, RadReply
)

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Statut de vérification d'un profil RADIUS."""
    OK = "ok"               # Tous les attributs correspondent
    WARNING = "warning"     # Différences mineures (ex: timeout légèrement différent)
    ERROR = "error"         # Différences majeures ou erreur de vérification
    NOT_CONNECTED = "not_connected"  # Utilisateur non connecté
    MIKROTIK_ERROR = "mikrotik_error"  # Erreur de communication MikroTik


@dataclass
class AttributeComparison:
    """Comparaison d'un attribut RADIUS."""
    attribute_name: str
    expected_value: Optional[str]
    actual_value: Optional[str]
    matches: bool
    difference_type: Optional[str] = None  # 'missing', 'mismatch', 'extra'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserVerificationResult:
    """Résultat de la vérification pour un utilisateur."""
    user_id: int
    username: str
    status: str
    profile_expected: Optional[str]
    groupname_radius: Optional[str]
    session_info: Optional[Dict[str, Any]]
    expected_attributes: List[Dict[str, str]]
    actual_attributes: List[Dict[str, str]]
    comparisons: List[Dict[str, Any]]
    differences: List[Dict[str, Any]]
    error_message: Optional[str] = None
    verified_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RadiusVerificationService:
    """
    Service de vérification de l'application des profils RADIUS.

    Vérifie que les attributs RADIUS configurés dans Django/FreeRADIUS
    sont correctement appliqués aux utilisateurs connectés sur MikroTik.
    """

    # Mapping des attributs RADIUS vers MikroTik
    # Les noms peuvent différer entre FreeRADIUS et MikroTik
    RADIUS_TO_MIKROTIK_MAPPING = {
        'Mikrotik-Rate-Limit': 'rate-limit',
        'Session-Timeout': 'session-timeout',
        'Idle-Timeout': 'idle-timeout',
        'Mikrotik-Total-Limit': 'limit-bytes-total',
        'ChilliSpot-Max-Total-Octets': 'limit-bytes-total',
        'WISPr-Bandwidth-Max-Up': 'limit-bytes-out',
        'WISPr-Bandwidth-Max-Down': 'limit-bytes-in',
    }

    # Attributs critiques qui doivent absolument correspondre
    CRITICAL_ATTRIBUTES = [
        'Mikrotik-Rate-Limit',
        'Mikrotik-Total-Limit',
    ]

    def __init__(self):
        """Initialise le service de vérification."""
        self.mikrotik_client = MikrotikAgentClient()

    def verify_user(self, user_id: int) -> UserVerificationResult:
        """
        Vérifie l'application du profil RADIUS pour un utilisateur spécifique.

        Args:
            user_id: ID de l'utilisateur Django à vérifier

        Returns:
            UserVerificationResult avec le détail de la vérification
        """
        try:
            # 1. Récupérer l'utilisateur Django
            try:
                user = User.objects.select_related(
                    'profile', 'promotion', 'promotion__profile'
                ).get(id=user_id)
            except User.DoesNotExist:
                return self._error_result(
                    user_id=user_id,
                    username="",
                    error=f"Utilisateur avec ID {user_id} non trouvé"
                )

            # 2. Vérifier si l'utilisateur est activé dans RADIUS
            if not user.is_radius_activated:
                return self._error_result(
                    user_id=user_id,
                    username=user.username,
                    error="Utilisateur non activé dans RADIUS"
                )

            # 3. Récupérer le profil effectif
            effective_profile = user.get_effective_profile()
            profile_name = effective_profile.name if effective_profile else None

            # 4. Récupérer les attributs attendus depuis FreeRADIUS
            expected_attrs = self._get_expected_attributes(user.username)

            # 5. Récupérer la session active sur MikroTik
            session_info, mikrotik_error = self._get_user_session(user.username)

            if mikrotik_error:
                return UserVerificationResult(
                    user_id=user_id,
                    username=user.username,
                    status=VerificationStatus.MIKROTIK_ERROR.value,
                    profile_expected=profile_name,
                    groupname_radius=expected_attrs.get('groupname'),
                    session_info=None,
                    expected_attributes=expected_attrs.get('attributes', []),
                    actual_attributes=[],
                    comparisons=[],
                    differences=[],
                    error_message=mikrotik_error,
                    verified_at=timezone.now().isoformat()
                )

            if not session_info:
                return UserVerificationResult(
                    user_id=user_id,
                    username=user.username,
                    status=VerificationStatus.NOT_CONNECTED.value,
                    profile_expected=profile_name,
                    groupname_radius=expected_attrs.get('groupname'),
                    session_info=None,
                    expected_attributes=expected_attrs.get('attributes', []),
                    actual_attributes=[],
                    comparisons=[],
                    differences=[],
                    error_message="Utilisateur non connecté au hotspot",
                    verified_at=timezone.now().isoformat()
                )

            # 6. Extraire les attributs appliqués depuis la session MikroTik
            actual_attrs = self._extract_session_attributes(session_info)

            # 7. Comparer les attributs
            comparisons, differences = self._compare_attributes(
                expected_attrs.get('attributes', []),
                actual_attrs
            )

            # 8. Déterminer le statut global
            status = self._determine_status(differences)

            return UserVerificationResult(
                user_id=user_id,
                username=user.username,
                status=status.value,
                profile_expected=profile_name,
                groupname_radius=expected_attrs.get('groupname'),
                session_info=session_info,
                expected_attributes=expected_attrs.get('attributes', []),
                actual_attributes=actual_attrs,
                comparisons=comparisons,
                differences=differences,
                error_message=None,
                verified_at=timezone.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'utilisateur {user_id}: {e}")
            return self._error_result(
                user_id=user_id,
                username="",
                error=f"Erreur interne: {str(e)}"
            )

    def verify_all_connected_users(self) -> Dict[str, Any]:
        """
        Vérifie l'application des profils RADIUS pour tous les utilisateurs connectés.

        Returns:
            Rapport de vérification pour tous les utilisateurs connectés
        """
        results = {
            'verified_at': timezone.now().isoformat(),
            'mikrotik_available': True,
            'total_sessions': 0,
            'verified_users': 0,
            'status_summary': {
                'ok': 0,
                'warning': 0,
                'error': 0,
                'not_found': 0
            },
            'users': [],
            'errors': []
        }

        try:
            # 1. Récupérer toutes les sessions actives
            response = self.mikrotik_client.get_active_connections()
            sessions = response.get('connections', response.get('active', []))

            if not isinstance(sessions, list):
                sessions = []

            results['total_sessions'] = len(sessions)

            # 2. Vérifier chaque session
            for session in sessions:
                username = session.get('user', session.get('username', ''))
                if not username:
                    continue

                # Trouver l'utilisateur Django
                try:
                    user = User.objects.get(username=username)
                    verification = self.verify_user(user.id)
                    results['users'].append(verification.to_dict())
                    results['verified_users'] += 1

                    # Mettre à jour le résumé
                    if verification.status == VerificationStatus.OK.value:
                        results['status_summary']['ok'] += 1
                    elif verification.status == VerificationStatus.WARNING.value:
                        results['status_summary']['warning'] += 1
                    else:
                        results['status_summary']['error'] += 1

                except User.DoesNotExist:
                    results['status_summary']['not_found'] += 1
                    results['users'].append({
                        'username': username,
                        'status': 'not_found',
                        'error_message': f"Utilisateur '{username}' non trouvé dans Django"
                    })

        except Exception as e:
            logger.error(f"Erreur lors de la vérification en masse: {e}")
            results['mikrotik_available'] = False
            results['errors'].append(str(e))

        return results

    def verify_profile_users(self, profile_id: int) -> Dict[str, Any]:
        """
        Vérifie l'application d'un profil pour tous les utilisateurs qui l'utilisent.

        Args:
            profile_id: ID du profil à vérifier

        Returns:
            Rapport de vérification pour tous les utilisateurs du profil
        """
        from core.models import Profile
        from django.db.models import Q

        results = {
            'verified_at': timezone.now().isoformat(),
            'profile_id': profile_id,
            'profile_name': None,
            'total_users': 0,
            'connected_users': 0,
            'status_summary': {
                'ok': 0,
                'warning': 0,
                'error': 0,
                'not_connected': 0
            },
            'users': [],
            'errors': []
        }

        try:
            # 1. Récupérer le profil
            profile = Profile.objects.get(id=profile_id)
            results['profile_name'] = profile.name

            # 2. Trouver tous les utilisateurs avec ce profil
            # (direct ou via promotion)
            users = User.objects.filter(
                Q(profile_id=profile_id) |
                (Q(profile__isnull=True) & Q(promotion__profile_id=profile_id))
            ).filter(
                is_radius_activated=True,
                is_active=True
            )

            results['total_users'] = users.count()

            # 3. Vérifier chaque utilisateur
            for user in users:
                verification = self.verify_user(user.id)
                results['users'].append(verification.to_dict())

                if verification.status == VerificationStatus.OK.value:
                    results['status_summary']['ok'] += 1
                    results['connected_users'] += 1
                elif verification.status == VerificationStatus.WARNING.value:
                    results['status_summary']['warning'] += 1
                    results['connected_users'] += 1
                elif verification.status == VerificationStatus.NOT_CONNECTED.value:
                    results['status_summary']['not_connected'] += 1
                else:
                    results['status_summary']['error'] += 1

        except Profile.DoesNotExist:
            results['errors'].append(f"Profil avec ID {profile_id} non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du profil {profile_id}: {e}")
            results['errors'].append(str(e))

        return results

    def _get_expected_attributes(self, username: str) -> Dict[str, Any]:
        """
        Récupère les attributs RADIUS attendus pour un utilisateur.

        Args:
            username: Nom d'utilisateur RADIUS

        Returns:
            Dictionnaire avec groupname et liste des attributs attendus
        """
        result = {
            'groupname': None,
            'attributes': []
        }

        # 1. Trouver le groupe de l'utilisateur (profil)
        user_group = RadUserGroup.objects.filter(
            username=username,
            groupname__startswith='profile_'
        ).order_by('priority').first()

        if not user_group:
            return result

        result['groupname'] = user_group.groupname

        # 2. Récupérer les attributs du groupe (radgroupreply)
        group_replies = RadGroupReply.objects.filter(
            groupname=user_group.groupname
        )

        for reply in group_replies:
            result['attributes'].append({
                'attribute': reply.attribute,
                'value': reply.value,
                'op': reply.op,
                'source': 'radgroupreply'
            })

        # 3. Récupérer les attributs individuels (radreply) - prioritaires
        user_replies = RadReply.objects.filter(username=username)

        for reply in user_replies:
            result['attributes'].append({
                'attribute': reply.attribute,
                'value': reply.value,
                'op': reply.op,
                'source': 'radreply'
            })

        return result

    def _get_user_session(self, username: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Récupère la session active d'un utilisateur sur MikroTik.

        Args:
            username: Nom d'utilisateur à chercher

        Returns:
            Tuple (session_info, error_message)
        """
        try:
            response = self.mikrotik_client.get_active_connections()
            sessions = response.get('connections', response.get('active', []))

            if not isinstance(sessions, list):
                return None, None

            # Chercher la session de l'utilisateur
            for session in sessions:
                session_user = session.get('user', session.get('username', ''))
                if session_user == username:
                    return session, None

            return None, None

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la session MikroTik: {e}")
            return None, f"Erreur MikroTik: {str(e)}"

    def _extract_session_attributes(self, session: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extrait les attributs appliqués depuis une session MikroTik.

        Args:
            session: Données de session MikroTik

        Returns:
            Liste des attributs extraits
        """
        attributes = []

        # Mapping des champs MikroTik vers les attributs RADIUS
        mikrotik_to_radius = {
            'rate-limit': 'Mikrotik-Rate-Limit',
            'limit-bytes-total': 'Mikrotik-Total-Limit',
            'session-timeout': 'Session-Timeout',
            'idle-timeout': 'Idle-Timeout',
            'uptime': 'Session-Time',
            'bytes-in': 'Acct-Input-Octets',
            'bytes-out': 'Acct-Output-Octets',
        }

        for mk_key, radius_attr in mikrotik_to_radius.items():
            # Essayer différentes variantes de clé (camelCase, kebab-case, snake_case)
            value = None
            for key_variant in [mk_key, mk_key.replace('-', '_'), mk_key.replace('-', '')]:
                if key_variant in session:
                    value = session[key_variant]
                    break

            if value is not None:
                attributes.append({
                    'attribute': radius_attr,
                    'value': str(value),
                    'source': 'mikrotik_session'
                })

        # Ajouter le profil si présent
        profile = session.get('profile', session.get('user-profile'))
        if profile:
            attributes.append({
                'attribute': 'User-Profile',
                'value': profile,
                'source': 'mikrotik_session'
            })

        return attributes

    def _compare_attributes(
        self,
        expected: List[Dict[str, str]],
        actual: List[Dict[str, str]]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Compare les attributs attendus avec les attributs réels.

        Args:
            expected: Liste des attributs attendus
            actual: Liste des attributs réellement appliqués

        Returns:
            Tuple (comparisons, differences)
        """
        comparisons = []
        differences = []

        # Créer des dictionnaires pour faciliter la recherche
        expected_dict = {attr['attribute']: attr['value'] for attr in expected}
        actual_dict = {attr['attribute']: attr['value'] for attr in actual}

        # Comparer les attributs attendus
        for attr_name, expected_value in expected_dict.items():
            # Trouver l'attribut correspondant dans MikroTik
            actual_value = actual_dict.get(attr_name)

            # Gérer le mapping des noms d'attributs
            if actual_value is None and attr_name in self.RADIUS_TO_MIKROTIK_MAPPING:
                mk_name = self.RADIUS_TO_MIKROTIK_MAPPING[attr_name]
                # Chercher avec le nom MikroTik
                for ak, av in actual_dict.items():
                    if mk_name.lower() in ak.lower():
                        actual_value = av
                        break

            matches = self._values_match(expected_value, actual_value, attr_name)

            comparison = AttributeComparison(
                attribute_name=attr_name,
                expected_value=expected_value,
                actual_value=actual_value,
                matches=matches,
                difference_type=None if matches else ('missing' if actual_value is None else 'mismatch')
            )

            comparisons.append(comparison.to_dict())

            if not matches:
                differences.append({
                    'attribute': attr_name,
                    'expected': expected_value,
                    'actual': actual_value,
                    'type': comparison.difference_type,
                    'is_critical': attr_name in self.CRITICAL_ATTRIBUTES
                })

        return comparisons, differences

    def _values_match(
        self,
        expected: Optional[str],
        actual: Optional[str],
        attr_name: str
    ) -> bool:
        """
        Compare deux valeurs d'attribut avec tolérance selon le type.

        Args:
            expected: Valeur attendue
            actual: Valeur réelle
            attr_name: Nom de l'attribut pour déterminer le type de comparaison

        Returns:
            True si les valeurs correspondent
        """
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False

        # Normaliser les valeurs
        expected_str = str(expected).strip().lower()
        actual_str = str(actual).strip().lower()

        # Comparaison exacte par défaut
        if expected_str == actual_str:
            return True

        # Comparaisons spécifiques par type d'attribut
        if 'rate-limit' in attr_name.lower():
            # Comparer les rate-limits (format: "10M/5M" ou "10m/5m")
            return self._compare_rate_limits(expected_str, actual_str)

        if 'timeout' in attr_name.lower():
            # Comparer les timeouts avec tolérance de 5%
            return self._compare_numeric_with_tolerance(expected_str, actual_str, 0.05)

        if 'bytes' in attr_name.lower() or 'octets' in attr_name.lower():
            # Comparer les quotas avec tolérance de 1%
            return self._compare_numeric_with_tolerance(expected_str, actual_str, 0.01)

        return False

    def _compare_rate_limits(self, expected: str, actual: str) -> bool:
        """Compare deux rate-limits en normalisant le format."""
        def normalize_rate(rate_str: str) -> str:
            return rate_str.lower().replace(' ', '').replace('k', 'k').replace('m', 'm')

        return normalize_rate(expected) == normalize_rate(actual)

    def _compare_numeric_with_tolerance(
        self,
        expected: str,
        actual: str,
        tolerance: float
    ) -> bool:
        """Compare deux valeurs numériques avec une tolérance."""
        try:
            exp_val = float(''.join(c for c in expected if c.isdigit() or c == '.'))
            act_val = float(''.join(c for c in actual if c.isdigit() or c == '.'))

            if exp_val == 0:
                return act_val == 0

            diff_percent = abs(exp_val - act_val) / exp_val
            return diff_percent <= tolerance
        except (ValueError, ZeroDivisionError):
            return False

    def _determine_status(self, differences: List[Dict]) -> VerificationStatus:
        """
        Détermine le statut global de vérification basé sur les différences.

        Args:
            differences: Liste des différences trouvées

        Returns:
            VerificationStatus approprié
        """
        if not differences:
            return VerificationStatus.OK

        # Vérifier s'il y a des différences critiques
        critical_diffs = [d for d in differences if d.get('is_critical', False)]

        if critical_diffs:
            return VerificationStatus.ERROR

        return VerificationStatus.WARNING

    def _error_result(
        self,
        user_id: int,
        username: str,
        error: str
    ) -> UserVerificationResult:
        """Crée un résultat d'erreur."""
        return UserVerificationResult(
            user_id=user_id,
            username=username,
            status=VerificationStatus.ERROR.value,
            profile_expected=None,
            groupname_radius=None,
            session_info=None,
            expected_attributes=[],
            actual_attributes=[],
            comparisons=[],
            differences=[],
            error_message=error,
            verified_at=timezone.now().isoformat()
        )

    def log_verification(
        self,
        admin_user: Optional[User],
        verification_type: str,
        target_id: int,
        result: Dict[str, Any]
    ) -> None:
        """
        Journalise une vérification pour audit.

        Args:
            admin_user: Utilisateur admin qui a lancé la vérification
            verification_type: Type de vérification ('user', 'profile', 'bulk')
            target_id: ID de la cible vérifiée
            result: Résultat de la vérification
        """
        try:
            AdminAuditLog.log_action(
                admin_user=admin_user,
                action_type=f'radius_verify_{verification_type}',
                target=None,
                details={
                    'target_id': target_id,
                    'verification_type': verification_type,
                    'status': result.get('status', 'unknown'),
                    'differences_count': len(result.get('differences', [])),
                    'verified_at': result.get('verified_at')
                },
                severity='info'
            )
        except Exception as e:
            logger.error(f"Erreur lors de la journalisation de la vérification: {e}")


# Instance singleton pour utilisation globale
radius_verification_service = RadiusVerificationService()
