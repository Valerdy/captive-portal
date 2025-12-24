"""
Service de blocage DNS via MikroTik.

Ce service gère la synchronisation des domaines bloqués avec les entrées DNS statiques
du routeur MikroTik. Le blocage fonctionne en redirigeant les domaines vers 0.0.0.0.

Architecture:
- Django BlockedSite model -> MikroTik DNS static entries
- Synchronisation bidirectionnelle possible via sync_from_mikrotik()
- Support des wildcards via regexp MikroTik

Sécurité:
- Les credentials MikroTik doivent être stockés dans les variables d'environnement
- Utiliser un compte API avec permissions minimales (/ip/dns/static seulement)
- Activer SSL si possible (port 8729 au lieu de 8728)

Usage:
    from mikrotik.dns_service import MikrotikDNSBlockingService

    # Ajouter un blocage
    service = MikrotikDNSBlockingService()
    result = service.add_blocked_domain(blocked_site)

    # Synchroniser tous les domaines
    result = service.sync_all_domains()
"""

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from typing import Dict, Any, List, Optional, Tuple
import logging
import re

from .utils import MikrotikAgentClient

logger = logging.getLogger(__name__)


class MikrotikDNSBlockingService:
    """
    Service pour gérer les entrées DNS statiques sur MikroTik.

    Le blocage DNS fonctionne en créant des entrées statiques qui résolvent
    les domaines bloqués vers 0.0.0.0, ce qui empêche l'accès au site.

    Cette méthode est efficace pour HTTP et HTTPS car le blocage se fait
    avant même que la connexion TCP soit établie.
    """

    # Adresse de redirection pour les domaines bloqués
    BLOCK_ADDRESS = '0.0.0.0'

    # Commentaire préfixe pour identifier les entrées gérées par Django
    COMMENT_PREFIX = 'captive-portal-block:'

    def __init__(self, agent_client: Optional[MikrotikAgentClient] = None):
        """
        Initialise le service de blocage DNS.

        Args:
            agent_client: Client MikroTik Agent (optionnel, créé si non fourni)
        """
        self.client = agent_client or MikrotikAgentClient()

    def _make_dns_request(
        self,
        method: str,
        action: str = '',
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Effectue une requête vers l'API DNS de l'agent MikroTik.

        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE)
            action: Action spécifique (ex: 'static', 'static/123')
            data: Données de la requête

        Returns:
            Réponse de l'API
        """
        endpoint = f'/api/mikrotik/dns/{action}' if action else '/api/mikrotik/dns'
        return self.client._make_request(method, endpoint, data)

    def test_connection(self) -> Tuple[bool, str]:
        """
        Teste la connexion au routeur MikroTik.

        Returns:
            Tuple (succès, message)
        """
        try:
            result = self.client.test_connection()
            return True, "Connexion réussie"
        except Exception as e:
            logger.error(f"Test de connexion MikroTik échoué: {e}")
            return False, str(e)

    def get_all_dns_static_entries(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les entrées DNS statiques du MikroTik.

        Returns:
            Liste des entrées DNS statiques
        """
        try:
            result = self._make_dns_request('GET', 'static')
            return result.get('entries', [])
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des entrées DNS: {e}")
            raise

    def get_managed_entries(self) -> List[Dict[str, Any]]:
        """
        Récupère uniquement les entrées DNS gérées par le portail captif.

        Returns:
            Liste des entrées avec le commentaire préfixe
        """
        entries = self.get_all_dns_static_entries()
        return [
            entry for entry in entries
            if entry.get('comment', '').startswith(self.COMMENT_PREFIX)
        ]

    def _build_comment(self, blocked_site) -> str:
        """
        Construit le commentaire pour une entrée DNS.

        Args:
            blocked_site: Instance BlockedSite

        Returns:
            Commentaire formaté
        """
        parts = [self.COMMENT_PREFIX, str(blocked_site.id)]
        if blocked_site.reason:
            parts.append(f"| {blocked_site.reason[:50]}")
        return ''.join(parts)

    def _parse_comment(self, comment: str) -> Optional[int]:
        """
        Parse le commentaire pour extraire l'ID du BlockedSite.

        Args:
            comment: Commentaire de l'entrée DNS

        Returns:
            ID du BlockedSite ou None
        """
        if not comment or not comment.startswith(self.COMMENT_PREFIX):
            return None
        try:
            # Format: "captive-portal-block:123| reason"
            id_part = comment[len(self.COMMENT_PREFIX):].split('|')[0].strip()
            return int(id_part)
        except (ValueError, IndexError):
            return None

    def add_blocked_domain(self, blocked_site) -> Dict[str, Any]:
        """
        Ajoute un domaine bloqué au DNS MikroTik.

        Args:
            blocked_site: Instance BlockedSite

        Returns:
            Résultat de l'opération avec 'success', 'mikrotik_id', 'error'
        """
        if not blocked_site.is_active:
            return {
                'success': False,
                'error': 'Le site n\'est pas actif'
            }

        # Préparer les données pour l'API
        dns_name = blocked_site.get_dns_name()
        is_wildcard = blocked_site.domain.startswith('*.')

        data = {
            'name': dns_name,
            'address': self.BLOCK_ADDRESS,
            'comment': self._build_comment(blocked_site),
            'disabled': False
        }

        # Pour les wildcards, utiliser regexp
        if is_wildcard:
            # MikroTik regexp: .*\.example\.com$
            escaped_name = dns_name.replace('.', r'\.')
            data['regexp'] = f".*\\.{escaped_name}$"
            del data['name']  # On utilise regexp au lieu de name

        try:
            result = self._make_dns_request('POST', 'static', data)

            mikrotik_id = result.get('id') or result.get('.id')
            if mikrotik_id:
                blocked_site.mark_synced(str(mikrotik_id))
                logger.info(f"Domaine bloqué ajouté: {blocked_site.domain} (ID: {mikrotik_id})")
                return {
                    'success': True,
                    'mikrotik_id': mikrotik_id,
                    'domain': blocked_site.domain
                }
            else:
                error_msg = "L'API n'a pas retourné d'ID"
                blocked_site.mark_error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }

        except Exception as e:
            error_msg = str(e)
            blocked_site.mark_error(error_msg)
            logger.error(f"Erreur lors de l'ajout du domaine {blocked_site.domain}: {e}")
            return {
                'success': False,
                'error': error_msg
            }

    def remove_blocked_domain(self, blocked_site) -> Dict[str, Any]:
        """
        Supprime un domaine bloqué du DNS MikroTik.

        Args:
            blocked_site: Instance BlockedSite

        Returns:
            Résultat de l'opération
        """
        if not blocked_site.mikrotik_id:
            return {
                'success': True,
                'message': 'Aucune entrée MikroTik à supprimer'
            }

        try:
            self._make_dns_request('DELETE', f'static/{blocked_site.mikrotik_id}')
            logger.info(f"Domaine débloqué: {blocked_site.domain} (ID: {blocked_site.mikrotik_id})")

            # Réinitialiser l'état de sync
            blocked_site.mikrotik_id = None
            blocked_site.sync_status = 'pending'
            blocked_site.save(update_fields=['mikrotik_id', 'sync_status'])

            return {
                'success': True,
                'domain': blocked_site.domain
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erreur lors de la suppression du domaine {blocked_site.domain}: {e}")
            return {
                'success': False,
                'error': error_msg
            }

    def update_blocked_domain(self, blocked_site) -> Dict[str, Any]:
        """
        Met à jour une entrée DNS existante sur MikroTik.

        Si l'entrée n'existe pas, elle est créée.
        Si is_active est False, l'entrée est supprimée.

        Args:
            blocked_site: Instance BlockedSite

        Returns:
            Résultat de l'opération
        """
        # Si désactivé, supprimer l'entrée MikroTik
        if not blocked_site.is_active:
            if blocked_site.mikrotik_id:
                return self.remove_blocked_domain(blocked_site)
            return {'success': True, 'message': 'Site inactif, rien à faire'}

        # Si pas d'ID MikroTik, créer l'entrée
        if not blocked_site.mikrotik_id:
            return self.add_blocked_domain(blocked_site)

        # Mettre à jour l'entrée existante
        dns_name = blocked_site.get_dns_name()
        is_wildcard = blocked_site.domain.startswith('*.')

        data = {
            'comment': self._build_comment(blocked_site),
            'disabled': False
        }

        if is_wildcard:
            escaped_name = dns_name.replace('.', r'\.')
            data['regexp'] = f".*\\.{escaped_name}$"
        else:
            data['name'] = dns_name
            data['address'] = self.BLOCK_ADDRESS

        try:
            self._make_dns_request(
                'PUT',
                f'static/{blocked_site.mikrotik_id}',
                data
            )
            blocked_site.mark_synced(blocked_site.mikrotik_id)
            logger.info(f"Domaine mis à jour: {blocked_site.domain}")
            return {
                'success': True,
                'domain': blocked_site.domain
            }

        except Exception as e:
            # Si l'entrée n'existe plus, la recréer
            if 'not found' in str(e).lower() or '404' in str(e):
                blocked_site.mikrotik_id = None
                return self.add_blocked_domain(blocked_site)

            error_msg = str(e)
            blocked_site.mark_error(error_msg)
            logger.error(f"Erreur lors de la mise à jour du domaine {blocked_site.domain}: {e}")
            return {
                'success': False,
                'error': error_msg
            }

    def sync_all_domains(self, force: bool = False) -> Dict[str, Any]:
        """
        Synchronise tous les domaines bloqués vers MikroTik.

        Args:
            force: Si True, resynchronise même les entrées déjà synchronisées

        Returns:
            Statistiques de synchronisation
        """
        from core.models import BlockedSite

        stats = {
            'total': 0,
            'added': 0,
            'updated': 0,
            'removed': 0,
            'errors': [],
            'skipped': 0
        }

        # Récupérer les entrées à synchroniser
        if force:
            blocked_sites = BlockedSite.objects.filter(is_active=True)
        else:
            blocked_sites = BlockedSite.objects.filter(
                is_active=True,
                sync_status__in=['pending', 'error']
            )

        stats['total'] = blocked_sites.count()
        logger.info(f"Synchronisation de {stats['total']} domaines bloqués...")

        for site in blocked_sites:
            if site.mikrotik_id and not force:
                result = self.update_blocked_domain(site)
                if result.get('success'):
                    stats['updated'] += 1
            else:
                result = self.add_blocked_domain(site)
                if result.get('success'):
                    stats['added'] += 1

            if not result.get('success'):
                stats['errors'].append({
                    'domain': site.domain,
                    'error': result.get('error')
                })

        # Gérer les sites désactivés (supprimer du MikroTik)
        inactive_sites = BlockedSite.objects.filter(
            is_active=False,
            mikrotik_id__isnull=False
        )

        for site in inactive_sites:
            result = self.remove_blocked_domain(site)
            if result.get('success'):
                stats['removed'] += 1
            else:
                stats['errors'].append({
                    'domain': site.domain,
                    'error': result.get('error')
                })

        logger.info(
            f"Synchronisation terminée: {stats['added']} ajoutés, "
            f"{stats['updated']} mis à jour, {stats['removed']} supprimés, "
            f"{len(stats['errors'])} erreurs"
        )

        return stats

    def sync_from_mikrotik(self, import_unmanaged: bool = False) -> Dict[str, Any]:
        """
        Synchronise l'état de la base depuis MikroTik.

        Vérifie que les entrées MikroTik correspondent à la base Django
        et met à jour les ID/status si nécessaire.

        Args:
            import_unmanaged: Si True, importe aussi les entrées non gérées

        Returns:
            Statistiques de synchronisation
        """
        from core.models import BlockedSite

        stats = {
            'verified': 0,
            'orphaned': 0,
            'imported': 0,
            'errors': []
        }

        try:
            mikrotik_entries = self.get_all_dns_static_entries()
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

        # Index des entrées MikroTik par ID
        mikrotik_by_id = {
            str(entry.get('.id') or entry.get('id')): entry
            for entry in mikrotik_entries
        }

        # Vérifier les BlockedSite existants
        for site in BlockedSite.objects.filter(is_active=True):
            if site.mikrotik_id and site.mikrotik_id in mikrotik_by_id:
                # L'entrée existe, marquer comme synchronisée
                if site.sync_status != 'synced':
                    site.mark_synced(site.mikrotik_id)
                stats['verified'] += 1
            elif site.mikrotik_id:
                # L'entrée n'existe plus sur MikroTik
                site.mark_pending()
                stats['orphaned'] += 1

        # Importer les entrées non gérées si demandé
        if import_unmanaged:
            managed_entries = self.get_managed_entries()
            managed_ids = {
                str(e.get('.id') or e.get('id'))
                for e in managed_entries
            }

            for entry in mikrotik_entries:
                entry_id = str(entry.get('.id') or entry.get('id'))
                if entry_id not in managed_ids:
                    # Entrée non gérée avec address 0.0.0.0
                    if entry.get('address') == self.BLOCK_ADDRESS:
                        domain = entry.get('name') or entry.get('regexp', '').strip('.*\\.$')
                        if domain:
                            try:
                                site, created = BlockedSite.objects.get_or_create(
                                    domain=domain,
                                    defaults={
                                        'type': 'blacklist',
                                        'reason': 'Importé depuis MikroTik',
                                        'mikrotik_id': entry_id,
                                        'sync_status': 'synced',
                                        'last_sync_at': timezone.now()
                                    }
                                )
                                if created:
                                    stats['imported'] += 1
                            except Exception as e:
                                stats['errors'].append({
                                    'domain': domain,
                                    'error': str(e)
                                })

        return stats

    def cleanup_orphaned_entries(self) -> Dict[str, Any]:
        """
        Supprime les entrées MikroTik orphelines (non présentes dans la base Django).

        Returns:
            Statistiques de nettoyage
        """
        from core.models import BlockedSite

        stats = {
            'checked': 0,
            'removed': 0,
            'errors': []
        }

        try:
            managed_entries = self.get_managed_entries()
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

        # IDs des BlockedSite actifs
        active_ids = set(
            BlockedSite.objects.filter(is_active=True)
            .values_list('id', flat=True)
        )

        for entry in managed_entries:
            stats['checked'] += 1
            site_id = self._parse_comment(entry.get('comment', ''))

            if site_id and site_id not in active_ids:
                # Entrée orpheline, supprimer
                entry_id = entry.get('.id') or entry.get('id')
                try:
                    self._make_dns_request('DELETE', f'static/{entry_id}')
                    stats['removed'] += 1
                    logger.info(f"Entrée orpheline supprimée: {entry.get('name')}")
                except Exception as e:
                    stats['errors'].append({
                        'entry_id': entry_id,
                        'error': str(e)
                    })

        return stats


class MikrotikDNSConfigHelper:
    """
    Aide à la configuration du DNS MikroTik pour le blocage.

    Cette classe fournit les commandes MikroTik nécessaires pour:
    - Configurer le serveur DNS
    - Forcer l'utilisation du DNS du routeur
    - Configurer les règles de redirection DNS
    """

    @staticmethod
    def get_dns_server_commands() -> List[str]:
        """
        Retourne les commandes pour configurer le serveur DNS MikroTik.

        Ces commandes activent le serveur DNS et permettent les requêtes distantes.
        """
        return [
            # Activer le serveur DNS avec cache
            "/ip dns set allow-remote-requests=yes cache-size=4096KiB",

            # Définir les serveurs DNS upstream (exemple avec Cloudflare et Google)
            "/ip dns set servers=1.1.1.1,8.8.8.8",

            # Vérifier la configuration
            "/ip dns print",
        ]

    @staticmethod
    def get_dns_redirect_commands(lan_interface: str = "bridge") -> List[str]:
        """
        Retourne les commandes pour forcer l'utilisation du DNS du routeur.

        Ces règles NAT redirigent toutes les requêtes DNS (port 53) vers le routeur,
        empêchant les utilisateurs de contourner le blocage en utilisant d'autres DNS.

        Args:
            lan_interface: Interface LAN (bridge, ether2, etc.)
        """
        return [
            # Rediriger les requêtes DNS UDP vers le routeur
            f"/ip firewall nat add chain=dstnat protocol=udp dst-port=53 "
            f"in-interface={lan_interface} action=redirect to-ports=53 "
            f"comment=\"Force DNS to router (UDP)\"",

            # Rediriger les requêtes DNS TCP vers le routeur
            f"/ip firewall nat add chain=dstnat protocol=tcp dst-port=53 "
            f"in-interface={lan_interface} action=redirect to-ports=53 "
            f"comment=\"Force DNS to router (TCP)\"",

            # Bloquer DoH/DoT pour empêcher le contournement (optionnel)
            f"/ip firewall filter add chain=forward protocol=tcp dst-port=853 "
            f"in-interface={lan_interface} action=drop "
            f"comment=\"Block DNS over TLS\"",
        ]

    @staticmethod
    def get_api_user_commands(
        username: str = "captive-portal-api",
        password: str = "CHANGE_ME_SECURE_PASSWORD",
        allowed_address: str = "0.0.0.0/0"
    ) -> List[str]:
        """
        Retourne les commandes pour créer un utilisateur API avec permissions minimales.

        IMPORTANT: Changez le mot de passe par défaut!

        Args:
            username: Nom d'utilisateur API
            password: Mot de passe (à changer!)
            allowed_address: Adresse IP autorisée (0.0.0.0/0 = toutes)
        """
        return [
            # Créer un groupe avec permissions minimales
            "/user group add name=captive-portal-dns "
            "policy=api,read,write,!ftp,!local,!password,!policy,!reboot,!sensitive,!sniff,!ssh,!telnet,!test,!web,!winbox",

            # Créer l'utilisateur
            f"/user add name={username} password={password} "
            f"group=captive-portal-dns address={allowed_address} "
            f"comment=\"API user for Captive Portal DNS blocking\"",

            # Activer le service API REST (si pas déjà fait)
            "/ip service enable api",
            "/ip service set api port=8728",

            # Pour SSL (recommandé en production):
            # "/ip service enable api-ssl",
            # "/ip service set api-ssl port=8729",
        ]

    @staticmethod
    def get_example_static_entry_commands() -> List[str]:
        """
        Retourne des exemples de commandes pour les entrées DNS statiques.
        """
        return [
            # Blocage simple d'un domaine
            "/ip dns static add name=facebook.com address=0.0.0.0 "
            "comment=\"captive-portal-block:1| Social network\"",

            # Blocage avec regexp pour sous-domaines
            "/ip dns static add regexp=\".*\\\\.tiktok\\\\.com$\" address=0.0.0.0 "
            "comment=\"captive-portal-block:2| TikTok and subdomains\"",

            # Lister les entrées
            "/ip dns static print",

            # Supprimer une entrée par ID
            "/ip dns static remove [find where comment~\"captive-portal-block:1\"]",
        ]

    @staticmethod
    def get_full_setup_script(
        lan_interface: str = "bridge",
        api_username: str = "captive-portal-api",
        api_password: str = "CHANGE_ME"
    ) -> str:
        """
        Génère un script complet de configuration MikroTik.

        Args:
            lan_interface: Interface LAN
            api_username: Nom d'utilisateur API
            api_password: Mot de passe API

        Returns:
            Script MikroTik complet
        """
        helper = MikrotikDNSConfigHelper

        lines = [
            "# ============================================",
            "# Configuration MikroTik pour le blocage DNS",
            "# Portail Captif - Script de configuration",
            "# ============================================",
            "",
            "# 1. Configuration du serveur DNS",
            "# --------------------------------",
        ]
        lines.extend(helper.get_dns_server_commands())

        lines.extend([
            "",
            "# 2. Redirection DNS forcée",
            "# -------------------------",
        ])
        lines.extend(helper.get_dns_redirect_commands(lan_interface))

        lines.extend([
            "",
            "# 3. Création de l'utilisateur API",
            "# ---------------------------------",
            "# IMPORTANT: Changez le mot de passe!",
        ])
        lines.extend(helper.get_api_user_commands(api_username, api_password))

        lines.extend([
            "",
            "# 4. Vérification",
            "# ---------------",
            "/ip dns print",
            "/ip firewall nat print where comment~\"DNS\"",
            "/user print where name=" + api_username,
            "",
            "# Script terminé",
        ])

        return "\n".join(lines)
