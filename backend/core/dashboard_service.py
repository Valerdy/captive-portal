"""
Service Dashboard - Statistiques et métriques temps réel

Ce service agrège les données de :
- radacct (sessions, bande passante, comptabilité FreeRADIUS)
- radusergroup (association utilisateurs-groupes)
- radgroupreply (attributs de profils)
- core.models (utilisateurs, profils, promotions)

Architecture :
    FreeRADIUS (radacct) → DashboardService → API REST → Frontend
"""

from django.db import models
from django.db.models import Count, Sum, F, Q, Avg
from django.db.models.functions import TruncDate, TruncHour, Coalesce
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta, datetime
from typing import Dict, Any, List, Optional
import logging

from radius.models import RadAcct, RadUserGroup, RadGroupReply, RadCheck
from core.models import User, Profile, Promotion, Device, Session

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service principal pour les statistiques du dashboard administrateur.

    Fonctionnalités:
    - Statistiques globales (cartes du dashboard)
    - Graphique bande passante 24h
    - Activité utilisateurs 7 jours
    - Top utilisateurs consommateurs
    - Top profils consommateurs
    - Historique utilisateur par matricule
    """

    # Durée du cache en secondes (5 minutes pour les stats fréquentes)
    CACHE_TTL_SHORT = 300  # 5 minutes
    CACHE_TTL_LONG = 900   # 15 minutes

    # =========================================================================
    # 1. STATISTIQUES GLOBALES (Cartes du dashboard)
    # =========================================================================

    @classmethod
    def get_global_statistics(cls) -> Dict[str, Any]:
        """
        Récupère toutes les statistiques globales pour les cartes du dashboard.

        Returns:
            Dict avec:
            - total_users: Nombre total d'utilisateurs
            - active_users: Utilisateurs avec sessions actives
            - total_sessions: Nombre de sessions en cours
            - connected_devices: Nombre d'appareils connectés (MAC uniques)
            - bandwidth_today: Bande passante consommée aujourd'hui
            - bandwidth_total: Bande passante totale
            - profiles_count: Nombre de profils créés
            - profiles_with_quota: Nombre de profils avec quota limité
        """
        cache_key = 'dashboard_global_stats'
        cached = cache.get(cache_key)
        if cached:
            return cached

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Statistiques utilisateurs Django
        total_users = User.objects.filter(is_active=True, role='user').count()

        # Utilisateurs activés dans RADIUS (is_radius_activated=True)
        radius_activated_users = User.objects.filter(
            is_active=True,
            role='user',
            is_radius_activated=True
        ).count()

        # Sessions actives (radacct.acctstoptime IS NULL)
        active_sessions_data = RadAcct.objects.filter(
            acctstoptime__isnull=True
        ).aggregate(
            session_count=Count('radacctid'),
            unique_users=Count('username', distinct=True),
            unique_macs=Count('callingstationid', distinct=True)
        )

        # Bande passante aujourd'hui
        bandwidth_today = RadAcct.objects.filter(
            acctstarttime__gte=today_start
        ).aggregate(
            total_input=Coalesce(Sum('acctinputoctets'), 0),
            total_output=Coalesce(Sum('acctoutputoctets'), 0)
        )

        # Bande passante totale (toutes sessions)
        bandwidth_total = RadAcct.objects.aggregate(
            total_input=Coalesce(Sum('acctinputoctets'), 0),
            total_output=Coalesce(Sum('acctoutputoctets'), 0)
        )

        # Statistiques profils
        profiles_count = Profile.objects.filter(is_active=True).count()
        profiles_with_quota = Profile.objects.filter(
            is_active=True,
            quota_type='limited'
        ).count()
        profiles_unlimited = profiles_count - profiles_with_quota

        result = {
            'total_users': total_users,
            'active_users': active_sessions_data['unique_users'] or 0,  # Connectés actuellement au WiFi
            'online_users': active_sessions_data['unique_users'] or 0,  # Alias pour compatibilité
            'total_sessions': active_sessions_data['session_count'] or 0,
            'connected_devices': active_sessions_data['unique_macs'] or 0,
            'bandwidth_today': {
                'input': bandwidth_today['total_input'] or 0,
                'output': bandwidth_today['total_output'] or 0,
                'total': (bandwidth_today['total_input'] or 0) + (bandwidth_today['total_output'] or 0),
                'total_gb': round(((bandwidth_today['total_input'] or 0) + (bandwidth_today['total_output'] or 0)) / (1024**3), 2)
            },
            'bandwidth_total': {
                'input': bandwidth_total['total_input'] or 0,
                'output': bandwidth_total['total_output'] or 0,
                'total': (bandwidth_total['total_input'] or 0) + (bandwidth_total['total_output'] or 0),
                'total_gb': round(((bandwidth_total['total_input'] or 0) + (bandwidth_total['total_output'] or 0)) / (1024**3), 2)
            },
            'profiles_count': profiles_count,
            'profiles_with_quota': profiles_with_quota,
            'profiles_unlimited': profiles_unlimited,
            'timestamp': now.isoformat()
        }

        cache.set(cache_key, result, cls.CACHE_TTL_SHORT)
        return result

    # =========================================================================
    # 2. GRAPHIQUE BANDE PASSANTE 24H
    # =========================================================================

    @classmethod
    def get_bandwidth_24h(
        cls,
        interval_hours: int = 4,
        profile_id: Optional[int] = None,
        promotion_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Récupère la consommation de bande passante par tranche horaire sur 24h.

        Args:
            interval_hours: Intervalle en heures (défaut: 4h)
            profile_id: Filtrer par profil (optionnel)
            promotion_id: Filtrer par promotion (optionnel)

        Returns:
            Dict avec:
            - intervals: Liste des intervalles avec timestamp et consommation
            - total: Total sur 24h
            - filter_applied: Filtre appliqué (all/profile/promotion)
        """
        now = timezone.now()
        start_24h = now - timedelta(hours=24)

        # Base queryset
        queryset = RadAcct.objects.filter(
            acctstarttime__gte=start_24h
        )

        filter_applied = 'all'
        filter_name = None

        # Filtrer par profil
        if profile_id:
            try:
                profile = Profile.objects.get(id=profile_id)
                # Obtenir les utilisateurs de ce profil
                usernames = list(User.objects.filter(
                    Q(profile_id=profile_id) | Q(promotion__profile_id=profile_id)
                ).values_list('username', flat=True))
                queryset = queryset.filter(username__in=usernames)
                filter_applied = 'profile'
                filter_name = profile.name
            except Profile.DoesNotExist:
                pass

        # Filtrer par promotion
        elif promotion_id:
            try:
                promotion = Promotion.objects.get(id=promotion_id)
                usernames = list(promotion.users.values_list('username', flat=True))
                queryset = queryset.filter(username__in=usernames)
                filter_applied = 'promotion'
                filter_name = promotion.name
            except Promotion.DoesNotExist:
                pass

        # Générer les intervalles
        intervals = []
        num_intervals = 24 // interval_hours

        for i in range(num_intervals):
            interval_start = start_24h + timedelta(hours=i * interval_hours)
            interval_end = interval_start + timedelta(hours=interval_hours)

            # Agrégation pour cet intervalle
            data = queryset.filter(
                acctstarttime__gte=interval_start,
                acctstarttime__lt=interval_end
            ).aggregate(
                input_bytes=Coalesce(Sum('acctinputoctets'), 0),
                output_bytes=Coalesce(Sum('acctoutputoctets'), 0),
                session_count=Count('radacctid')
            )

            total_bytes = (data['input_bytes'] or 0) + (data['output_bytes'] or 0)

            intervals.append({
                'start': interval_start.isoformat(),
                'end': interval_end.isoformat(),
                'label': f"{interval_start.strftime('%Hh')}-{interval_end.strftime('%Hh')}",
                'input_bytes': data['input_bytes'] or 0,
                'output_bytes': data['output_bytes'] or 0,
                'total_bytes': total_bytes,
                'total_mb': round(total_bytes / (1024**2), 2),
                'sessions': data['session_count'] or 0
            })

        # Calcul du total
        total_data = queryset.aggregate(
            total_input=Coalesce(Sum('acctinputoctets'), 0),
            total_output=Coalesce(Sum('acctoutputoctets'), 0)
        )

        total_bytes = (total_data['total_input'] or 0) + (total_data['total_output'] or 0)

        return {
            'intervals': intervals,
            'total': {
                'input_bytes': total_data['total_input'] or 0,
                'output_bytes': total_data['total_output'] or 0,
                'total_bytes': total_bytes,
                'total_mb': round(total_bytes / (1024**2), 2),
                'total_gb': round(total_bytes / (1024**3), 2)
            },
            'filter_applied': filter_applied,
            'filter_name': filter_name,
            'interval_hours': interval_hours,
            'period_start': start_24h.isoformat(),
            'period_end': now.isoformat()
        }

    # =========================================================================
    # 3. ACTIVITÉ UTILISATEURS 7 JOURS
    # =========================================================================

    @classmethod
    def get_user_activity_7days(cls) -> Dict[str, Any]:
        """
        Récupère le nombre d'utilisateurs actifs par jour sur les 7 derniers jours.

        Returns:
            Dict avec:
            - days: Liste des jours avec date et nombre d'utilisateurs actifs
            - total_unique_users: Total d'utilisateurs uniques sur la période
            - average_daily: Moyenne journalière
        """
        cache_key = 'dashboard_user_activity_7days'
        cached = cache.get(cache_key)
        if cached:
            return cached

        now = timezone.now()
        start_7days = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

        # Agrégation par jour
        daily_activity = RadAcct.objects.filter(
            acctstarttime__gte=start_7days
        ).annotate(
            day=TruncDate('acctstarttime')
        ).values('day').annotate(
            unique_users=Count('username', distinct=True),
            total_sessions=Count('radacctid'),
            total_bytes=Coalesce(Sum('acctinputoctets'), 0) + Coalesce(Sum('acctoutputoctets'), 0)
        ).order_by('day')

        # Construire la liste des 7 jours
        days_data = {}
        for entry in daily_activity:
            if entry['day']:
                days_data[entry['day'].isoformat()] = {
                    'unique_users': entry['unique_users'],
                    'total_sessions': entry['total_sessions'],
                    'total_bytes': entry['total_bytes']
                }

        # Générer tous les jours de la semaine (même sans données)
        days = []
        day_names_fr = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam']

        for i in range(7):
            day_date = (now - timedelta(days=6-i)).date()
            day_key = day_date.isoformat()
            day_name = day_names_fr[day_date.weekday() + 1 if day_date.weekday() < 6 else 0]

            data = days_data.get(day_key, {
                'unique_users': 0,
                'total_sessions': 0,
                'total_bytes': 0
            })

            days.append({
                'date': day_key,
                'day_name': day_name,
                'day_full': day_date.strftime('%d/%m'),
                'unique_users': data['unique_users'],
                'total_sessions': data['total_sessions'],
                'total_mb': round(data['total_bytes'] / (1024**2), 2) if data['total_bytes'] else 0
            })

        # Total d'utilisateurs uniques sur la période
        total_unique = RadAcct.objects.filter(
            acctstarttime__gte=start_7days
        ).values('username').distinct().count()

        # Moyenne journalière
        active_days = [d for d in days if d['unique_users'] > 0]
        average_daily = round(sum(d['unique_users'] for d in days) / 7, 1) if days else 0

        result = {
            'days': days,
            'total_unique_users': total_unique,
            'average_daily': average_daily,
            'period_start': start_7days.isoformat(),
            'period_end': now.isoformat()
        }

        cache.set(cache_key, result, cls.CACHE_TTL_SHORT)
        return result

    # =========================================================================
    # 4. TOP UTILISATEURS CONSOMMATEURS
    # =========================================================================

    @classmethod
    def get_top_consumers(
        cls,
        limit: int = 10,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Récupère les utilisateurs qui consomment le plus de bande passante.

        Args:
            limit: Nombre d'utilisateurs à retourner (défaut: 10)
            period_days: Période d'analyse en jours (défaut: 30)

        Returns:
            Dict avec:
            - users: Liste des top consommateurs avec détails
            - total_bandwidth: Bande passante totale de la période
        """
        now = timezone.now()
        start_date = now - timedelta(days=period_days)

        # Agrégation par utilisateur
        top_users_raw = RadAcct.objects.filter(
            acctstarttime__gte=start_date
        ).values('username').annotate(
            total_input=Coalesce(Sum('acctinputoctets'), 0),
            total_output=Coalesce(Sum('acctoutputoctets'), 0),
            total_sessions=Count('radacctid'),
            total_session_time=Coalesce(Sum('acctsessiontime'), 0),
            last_seen=models.Max('acctstarttime')
        ).annotate(
            total_bytes=F('total_input') + F('total_output')
        ).order_by('-total_bytes')[:limit]

        # Enrichir avec les données Django
        users = []
        for entry in top_users_raw:
            username = entry['username']
            total_bytes = entry['total_bytes'] or 0

            # Chercher l'utilisateur Django correspondant
            try:
                user = User.objects.select_related('profile', 'promotion').get(username=username)
                user_data = {
                    'id': user.id,
                    'username': username,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or username,
                    'matricule': user.matricule,
                    'email': user.email,
                    'profile_name': user.profile.name if user.profile else (
                        user.promotion.profile.name if user.promotion and user.promotion.profile else 'Aucun'
                    ),
                    'promotion_name': user.promotion.name if user.promotion else None,
                    'is_radius_activated': user.is_radius_activated
                }
            except User.DoesNotExist:
                user_data = {
                    'id': None,
                    'username': username,
                    'full_name': username,
                    'matricule': None,
                    'email': None,
                    'profile_name': 'Inconnu',
                    'promotion_name': None,
                    'is_radius_activated': None
                }

            users.append({
                **user_data,
                'total_bytes': total_bytes,
                'total_mb': round(total_bytes / (1024**2), 2),
                'total_gb': round(total_bytes / (1024**3), 2),
                'download_bytes': entry['total_input'] or 0,
                'upload_bytes': entry['total_output'] or 0,
                'total_sessions': entry['total_sessions'],
                'total_session_hours': round((entry['total_session_time'] or 0) / 3600, 1),
                'last_seen': entry['last_seen'].isoformat() if entry['last_seen'] else None
            })

        # Total de la période
        total = RadAcct.objects.filter(
            acctstarttime__gte=start_date
        ).aggregate(
            total_input=Coalesce(Sum('acctinputoctets'), 0),
            total_output=Coalesce(Sum('acctoutputoctets'), 0)
        )

        total_bytes = (total['total_input'] or 0) + (total['total_output'] or 0)

        return {
            'users': users,
            'total_bandwidth': {
                'bytes': total_bytes,
                'mb': round(total_bytes / (1024**2), 2),
                'gb': round(total_bytes / (1024**3), 2)
            },
            'period_days': period_days,
            'period_start': start_date.isoformat(),
            'period_end': now.isoformat()
        }

    # =========================================================================
    # 5. TOP PROFILS CONSOMMATEURS
    # =========================================================================

    @classmethod
    def get_top_profiles(cls, limit: int = 10) -> Dict[str, Any]:
        """
        Récupère les profils les plus consommateurs de bande passante.

        Args:
            limit: Nombre de profils à retourner (défaut: 10)

        Returns:
            Dict avec:
            - profiles: Liste des profils avec stats
        """
        # Récupérer tous les profils actifs
        profiles = Profile.objects.filter(is_active=True)

        profile_stats = []

        for profile in profiles:
            # Utilisateurs de ce profil (direct + via promotion)
            direct_users = list(User.objects.filter(
                profile=profile,
                is_active=True
            ).values_list('username', flat=True))

            promo_users = list(User.objects.filter(
                promotion__profile=profile,
                profile__isnull=True,
                is_active=True
            ).values_list('username', flat=True))

            all_usernames = list(set(direct_users + promo_users))

            if not all_usernames:
                profile_stats.append({
                    'id': profile.id,
                    'name': profile.name,
                    'user_count': 0,
                    'active_users': 0,
                    'total_bytes': 0,
                    'total_mb': 0,
                    'total_gb': 0,
                    'bandwidth_limit': f"{profile.bandwidth_download}/{profile.bandwidth_upload} Mbps",
                    'quota_type': profile.quota_type
                })
                continue

            # Statistiques des sessions pour ces utilisateurs (30 derniers jours)
            start_date = timezone.now() - timedelta(days=30)

            stats = RadAcct.objects.filter(
                username__in=all_usernames,
                acctstarttime__gte=start_date
            ).aggregate(
                total_input=Coalesce(Sum('acctinputoctets'), 0),
                total_output=Coalesce(Sum('acctoutputoctets'), 0),
                active_users=Count('username', distinct=True)
            )

            total_bytes = (stats['total_input'] or 0) + (stats['total_output'] or 0)

            profile_stats.append({
                'id': profile.id,
                'name': profile.name,
                'user_count': len(all_usernames),
                'active_users': stats['active_users'] or 0,
                'total_bytes': total_bytes,
                'total_mb': round(total_bytes / (1024**2), 2),
                'total_gb': round(total_bytes / (1024**3), 2),
                'bandwidth_limit': f"{profile.bandwidth_download}/{profile.bandwidth_upload} Mbps",
                'quota_type': profile.quota_type,
                'session_timeout_hours': round(profile.session_timeout / 3600, 1)
            })

        # Trier par consommation totale
        profile_stats.sort(key=lambda x: x['total_bytes'], reverse=True)

        return {
            'profiles': profile_stats[:limit],
            'total_profiles': len(profile_stats)
        }

    # =========================================================================
    # 6. HISTORIQUE UTILISATEUR PAR MATRICULE
    # =========================================================================

    @classmethod
    def get_user_history(
        cls,
        matricule: Optional[str] = None,
        username: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Récupère l'historique complet d'un utilisateur via son matricule.

        Args:
            matricule: Matricule de l'utilisateur
            username: Nom d'utilisateur (alternative au matricule)
            user_id: ID de l'utilisateur (alternative)
            limit: Nombre de sessions à retourner (défaut: 50)

        Returns:
            Dict avec:
            - user: Informations de l'utilisateur
            - sessions: Historique des sessions
            - stats: Statistiques agrégées
            - current_session: Session active si existante
        """
        # Trouver l'utilisateur
        user = None
        if user_id:
            try:
                user = User.objects.select_related('profile', 'promotion').get(id=user_id)
            except User.DoesNotExist:
                pass
        elif matricule:
            try:
                user = User.objects.select_related('profile', 'promotion').get(matricule=matricule)
            except User.DoesNotExist:
                pass
        elif username:
            try:
                user = User.objects.select_related('profile', 'promotion').get(username=username)
            except User.DoesNotExist:
                pass

        if not user:
            return {
                'error': 'Utilisateur non trouvé',
                'user': None,
                'sessions': [],
                'stats': None,
                'current_session': None
            }

        # Récupérer les sessions de radacct
        sessions_raw = RadAcct.objects.filter(
            username=user.username
        ).order_by('-acctstarttime')[:limit]

        sessions = []
        for session in sessions_raw:
            total_bytes = (session.acctinputoctets or 0) + (session.acctoutputoctets or 0)

            sessions.append({
                'session_id': session.acctsessionid,
                'start_time': session.acctstarttime.isoformat() if session.acctstarttime else None,
                'stop_time': session.acctstoptime.isoformat() if session.acctstoptime else None,
                'duration_seconds': session.acctsessiontime or 0,
                'duration_formatted': cls._format_duration(session.acctsessiontime or 0),
                'is_active': session.acctstoptime is None,
                'download_bytes': session.acctinputoctets or 0,
                'upload_bytes': session.acctoutputoctets or 0,
                'total_bytes': total_bytes,
                'total_mb': round(total_bytes / (1024**2), 2),
                'ip_address': session.framedipaddress,
                'mac_address': session.callingstationid,
                'nas_ip': session.nasipaddress,
                'terminate_cause': session.acctterminatecause
            })

        # Statistiques globales
        all_sessions = RadAcct.objects.filter(username=user.username)
        stats_data = all_sessions.aggregate(
            total_sessions=Count('radacctid'),
            total_input=Coalesce(Sum('acctinputoctets'), 0),
            total_output=Coalesce(Sum('acctoutputoctets'), 0),
            total_time=Coalesce(Sum('acctsessiontime'), 0),
            first_session=models.Min('acctstarttime'),
            last_session=models.Max('acctstarttime')
        )

        total_bytes = (stats_data['total_input'] or 0) + (stats_data['total_output'] or 0)

        # Session active
        current_session = None
        active = all_sessions.filter(acctstoptime__isnull=True).first()
        if active:
            active_bytes = (active.acctinputoctets or 0) + (active.acctoutputoctets or 0)
            current_session = {
                'session_id': active.acctsessionid,
                'start_time': active.acctstarttime.isoformat() if active.acctstarttime else None,
                'duration_seconds': active.acctsessiontime or 0,
                'duration_formatted': cls._format_duration(active.acctsessiontime or 0),
                'download_bytes': active.acctinputoctets or 0,
                'upload_bytes': active.acctoutputoctets or 0,
                'total_mb': round(active_bytes / (1024**2), 2),
                'ip_address': active.framedipaddress,
                'mac_address': active.callingstationid
            }

        # Profil effectif
        effective_profile = user.get_effective_profile() if hasattr(user, 'get_effective_profile') else user.profile

        return {
            'user': {
                'id': user.id,
                'username': user.username,
                'matricule': user.matricule,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'email': user.email,
                'profile': {
                    'id': effective_profile.id if effective_profile else None,
                    'name': effective_profile.name if effective_profile else 'Aucun'
                } if effective_profile else None,
                'promotion': {
                    'id': user.promotion.id,
                    'name': user.promotion.name
                } if user.promotion else None,
                'is_radius_activated': user.is_radius_activated,
                'is_radius_enabled': user.is_radius_enabled,
                'created_at': user.created_at.isoformat() if user.created_at else None
            },
            'sessions': sessions,
            'stats': {
                'total_sessions': stats_data['total_sessions'] or 0,
                'total_bytes': total_bytes,
                'total_mb': round(total_bytes / (1024**2), 2),
                'total_gb': round(total_bytes / (1024**3), 2),
                'download_gb': round((stats_data['total_input'] or 0) / (1024**3), 2),
                'upload_gb': round((stats_data['total_output'] or 0) / (1024**3), 2),
                'total_hours': round((stats_data['total_time'] or 0) / 3600, 1),
                'first_connection': stats_data['first_session'].isoformat() if stats_data['first_session'] else None,
                'last_connection': stats_data['last_session'].isoformat() if stats_data['last_session'] else None
            },
            'current_session': current_session
        }

    # =========================================================================
    # 7. RECHERCHE UTILISATEUR
    # =========================================================================

    @classmethod
    def search_users(cls, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche des utilisateurs par matricule, nom ou email.

        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats

        Returns:
            Liste d'utilisateurs correspondants
        """
        if not query or len(query) < 2:
            return []

        users = User.objects.filter(
            Q(matricule__icontains=query) |
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).select_related('profile', 'promotion')[:limit]

        return [
            {
                'id': u.id,
                'username': u.username,
                'matricule': u.matricule,
                'full_name': f"{u.first_name} {u.last_name}".strip() or u.username,
                'email': u.email,
                'promotion': u.promotion.name if u.promotion else None,
                'profile': u.profile.name if u.profile else (
                    u.promotion.profile.name if u.promotion and u.promotion.profile else None
                ),
                'is_radius_activated': u.is_radius_activated
            }
            for u in users
        ]

    # =========================================================================
    # 8. SESSIONS ACTIVES EN TEMPS RÉEL
    # =========================================================================

    @classmethod
    def get_active_sessions(cls, limit: int = 100) -> Dict[str, Any]:
        """
        Récupère les sessions actuellement actives.

        Returns:
            Dict avec liste des sessions actives et statistiques
        """
        active_sessions = RadAcct.objects.filter(
            acctstoptime__isnull=True
        ).order_by('-acctstarttime')[:limit]

        sessions = []
        for session in active_sessions:
            total_bytes = (session.acctinputoctets or 0) + (session.acctoutputoctets or 0)

            # Chercher l'utilisateur Django
            try:
                user = User.objects.select_related('promotion').get(username=session.username)
                user_info = {
                    'id': user.id,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'matricule': user.matricule,
                    'promotion': user.promotion.name if user.promotion else None
                }
            except User.DoesNotExist:
                user_info = {
                    'id': None,
                    'full_name': session.username,
                    'matricule': None,
                    'promotion': None
                }

            # Calculer la durée depuis le début
            duration = 0
            if session.acctstarttime:
                duration = int((timezone.now() - session.acctstarttime).total_seconds())

            sessions.append({
                'session_id': session.acctsessionid,
                'username': session.username,
                'user': user_info,
                'start_time': session.acctstarttime.isoformat() if session.acctstarttime else None,
                'duration_seconds': duration,
                'duration_formatted': cls._format_duration(duration),
                'download_mb': round((session.acctinputoctets or 0) / (1024**2), 2),
                'upload_mb': round((session.acctoutputoctets or 0) / (1024**2), 2),
                'total_mb': round(total_bytes / (1024**2), 2),
                'ip_address': session.framedipaddress,
                'mac_address': session.callingstationid,
                'nas_ip': session.nasipaddress
            })

        # Statistiques des sessions actives
        stats = RadAcct.objects.filter(
            acctstoptime__isnull=True
        ).aggregate(
            total_count=Count('radacctid'),
            unique_users=Count('username', distinct=True),
            unique_devices=Count('callingstationid', distinct=True),
            total_download=Coalesce(Sum('acctinputoctets'), 0),
            total_upload=Coalesce(Sum('acctoutputoctets'), 0)
        )

        total_bytes = (stats['total_download'] or 0) + (stats['total_upload'] or 0)

        return {
            'sessions': sessions,
            'stats': {
                'total_sessions': stats['total_count'] or 0,
                'unique_users': stats['unique_users'] or 0,
                'unique_devices': stats['unique_devices'] or 0,
                'total_bandwidth_mb': round(total_bytes / (1024**2), 2),
                'total_bandwidth_gb': round(total_bytes / (1024**3), 2)
            },
            'timestamp': timezone.now().isoformat()
        }

    # =========================================================================
    # MÉTHODES UTILITAIRES
    # =========================================================================

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Formate une durée en secondes en format lisible."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    @classmethod
    def clear_cache(cls):
        """Efface le cache du dashboard."""
        cache.delete('dashboard_global_stats')
        cache.delete('dashboard_user_activity_7days')
        logger.info("Cache du dashboard effacé")
