"""
Commande de synchronisation des domaines bloqués avec MikroTik.

Cette commande permet de :
- Synchroniser tous les domaines bloqués vers MikroTik
- Vérifier l'état de synchronisation
- Nettoyer les entrées orphelines sur MikroTik
- Importer les entrées DNS existantes depuis MikroTik

Usage:
    # Synchroniser tous les domaines en attente
    python manage.py sync_blocked_domains

    # Forcer la resynchronisation de tous les domaines
    python manage.py sync_blocked_domains --force

    # Vérifier l'état sans modifier
    python manage.py sync_blocked_domains --dry-run

    # Nettoyer les entrées orphelines sur MikroTik
    python manage.py sync_blocked_domains --cleanup

    # Importer les entrées depuis MikroTik
    python manage.py sync_blocked_domains --import

    # Afficher les statistiques uniquement
    python manage.py sync_blocked_domains --stats
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronise les domaines bloqués avec MikroTik DNS statique'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la resynchronisation de tous les domaines, même ceux déjà synchronisés'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer de modifications'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Supprime les entrées MikroTik orphelines (non présentes dans Django)'
        )
        parser.add_argument(
            '--import',
            dest='import_entries',
            action='store_true',
            help='Importe les entrées DNS non gérées depuis MikroTik'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Affiche uniquement les statistiques sans synchroniser'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche des informations détaillées'
        )

    def handle(self, *args, **options):
        from core.models import BlockedSite
        from mikrotik.dns_service import MikrotikDNSBlockingService

        dry_run = options['dry_run']
        force = options['force']
        cleanup = options['cleanup']
        import_entries = options['import_entries']
        stats_only = options['stats']
        verbose = options['verbose']

        if dry_run:
            self.stdout.write(self.style.WARNING('Mode simulation (--dry-run)'))

        # Initialiser le service
        try:
            service = MikrotikDNSBlockingService()

            # Tester la connexion
            success, message = service.test_connection()
            if not success:
                raise CommandError(f"Impossible de se connecter à MikroTik: {message}")

            self.stdout.write(self.style.SUCCESS(f"Connexion MikroTik établie"))

        except Exception as e:
            raise CommandError(f"Erreur de connexion MikroTik: {e}")

        # Afficher les statistiques
        if stats_only or verbose:
            self._display_stats(BlockedSite, service)
            if stats_only:
                return

        # Nettoyer les entrées orphelines
        if cleanup:
            self._cleanup_orphaned(service, dry_run, verbose)
            return

        # Importer les entrées depuis MikroTik
        if import_entries:
            self._import_entries(service, dry_run, verbose)
            return

        # Synchronisation principale
        self._sync_domains(BlockedSite, service, force, dry_run, verbose)

    def _display_stats(self, BlockedSite, service):
        """Affiche les statistiques de synchronisation"""
        total = BlockedSite.objects.count()
        active = BlockedSite.objects.filter(is_active=True).count()
        synced = BlockedSite.objects.filter(sync_status='synced').count()
        pending = BlockedSite.objects.filter(sync_status='pending').count()
        errors = BlockedSite.objects.filter(sync_status='error').count()

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.HTTP_INFO("STATISTIQUES DES SITES BLOQUÉS"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"Total des entrées:        {total}")
        self.stdout.write(f"Entrées actives:          {active}")
        self.stdout.write(f"Synchronisées:            {synced}")
        self.stdout.write(f"En attente:               {pending}")
        self.stdout.write(f"En erreur:                {errors}")

        # Statistiques par catégorie
        self.stdout.write("\nPar catégorie:")
        for choice in BlockedSite.CATEGORY_CHOICES:
            count = BlockedSite.objects.filter(category=choice[0]).count()
            if count > 0:
                self.stdout.write(f"  {choice[1]}: {count}")

        # Statistiques MikroTik
        try:
            mikrotik_entries = service.get_managed_entries()
            self.stdout.write(f"\nEntrées sur MikroTik:     {len(mikrotik_entries)}")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"\nImpossible de lire MikroTik: {e}"))

        self.stdout.write("=" * 50 + "\n")

    def _sync_domains(self, BlockedSite, service, force, dry_run, verbose):
        """Synchronise les domaines bloqués vers MikroTik"""
        self.stdout.write("\nSynchronisation des domaines bloqués...")

        # Récupérer les entrées à synchroniser
        if force:
            queryset = BlockedSite.objects.filter(is_active=True)
        else:
            queryset = BlockedSite.objects.filter(
                is_active=True,
                sync_status__in=['pending', 'error']
            )

        total = queryset.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Aucune entrée à synchroniser"))
            return

        self.stdout.write(f"Entrées à traiter: {total}")

        added = 0
        updated = 0
        errors = []

        for site in queryset:
            if verbose:
                self.stdout.write(f"  Traitement: {site.domain}...", ending='')

            if dry_run:
                if verbose:
                    action = "UPDATE" if site.mikrotik_id else "ADD"
                    self.stdout.write(self.style.WARNING(f" [{action}] (simulation)"))
                continue

            try:
                if site.mikrotik_id:
                    result = service.update_blocked_domain(site)
                    if result.get('success'):
                        updated += 1
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(" [OK - MIS À JOUR]"))
                    else:
                        errors.append((site.domain, result.get('error')))
                        if verbose:
                            self.stdout.write(self.style.ERROR(f" [ERREUR]"))
                else:
                    result = service.add_blocked_domain(site)
                    if result.get('success'):
                        added += 1
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(" [OK - AJOUTÉ]"))
                    else:
                        errors.append((site.domain, result.get('error')))
                        if verbose:
                            self.stdout.write(self.style.ERROR(f" [ERREUR]"))

            except Exception as e:
                errors.append((site.domain, str(e)))
                if verbose:
                    self.stdout.write(self.style.ERROR(f" [EXCEPTION]"))

        # Gérer les sites désactivés
        inactive_with_mikrotik = BlockedSite.objects.filter(
            is_active=False,
            mikrotik_id__isnull=False
        )
        removed = 0

        for site in inactive_with_mikrotik:
            if verbose:
                self.stdout.write(f"  Suppression: {site.domain}...", ending='')

            if dry_run:
                if verbose:
                    self.stdout.write(self.style.WARNING(" [REMOVE] (simulation)"))
                continue

            try:
                result = service.remove_blocked_domain(site)
                if result.get('success'):
                    removed += 1
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(" [OK - SUPPRIMÉ]"))
                else:
                    errors.append((site.domain, result.get('error')))
                    if verbose:
                        self.stdout.write(self.style.ERROR(f" [ERREUR]"))
            except Exception as e:
                errors.append((site.domain, str(e)))
                if verbose:
                    self.stdout.write(self.style.ERROR(f" [EXCEPTION]"))

        # Résumé
        self.stdout.write("\n" + "-" * 40)
        self.stdout.write(self.style.SUCCESS(f"Synchronisation terminée:"))
        self.stdout.write(f"  Ajoutés:    {added}")
        self.stdout.write(f"  Mis à jour: {updated}")
        self.stdout.write(f"  Supprimés:  {removed}")

        if errors:
            self.stdout.write(self.style.ERROR(f"  Erreurs:    {len(errors)}"))
            if verbose:
                for domain, error in errors:
                    self.stdout.write(self.style.ERROR(f"    - {domain}: {error}"))

    def _cleanup_orphaned(self, service, dry_run, verbose):
        """Nettoie les entrées orphelines sur MikroTik"""
        self.stdout.write("\nNettoyage des entrées orphelines sur MikroTik...")

        if dry_run:
            try:
                managed = service.get_managed_entries()
                from core.models import BlockedSite

                active_ids = set(
                    BlockedSite.objects.filter(is_active=True)
                    .values_list('id', flat=True)
                )

                orphaned = []
                for entry in managed:
                    site_id = service._parse_comment(entry.get('comment', ''))
                    if site_id and site_id not in active_ids:
                        orphaned.append(entry)

                self.stdout.write(
                    self.style.WARNING(
                        f"Mode simulation: {len(orphaned)} entrée(s) orpheline(s) trouvée(s)"
                    )
                )
                if verbose:
                    for entry in orphaned:
                        self.stdout.write(f"  - {entry.get('name') or entry.get('regexp')}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur: {e}"))
            return

        try:
            result = service.cleanup_orphaned_entries()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Nettoyage terminé: {result['checked']} vérifiée(s), "
                    f"{result['removed']} supprimée(s)"
                )
            )
            if result.get('errors'):
                for error in result['errors']:
                    self.stdout.write(
                        self.style.ERROR(f"  Erreur: {error}")
                    )
        except Exception as e:
            raise CommandError(f"Erreur lors du nettoyage: {e}")

    def _import_entries(self, service, dry_run, verbose):
        """Importe les entrées DNS depuis MikroTik"""
        self.stdout.write("\nImportation des entrées depuis MikroTik...")

        if dry_run:
            try:
                entries = service.get_all_dns_static_entries()
                managed = service.get_managed_entries()
                managed_ids = {
                    str(e.get('.id') or e.get('id'))
                    for e in managed
                }

                unmanaged = [
                    e for e in entries
                    if str(e.get('.id') or e.get('id')) not in managed_ids
                    and e.get('address') == '0.0.0.0'
                ]

                self.stdout.write(
                    self.style.WARNING(
                        f"Mode simulation: {len(unmanaged)} entrée(s) non gérée(s) trouvée(s)"
                    )
                )
                if verbose:
                    for entry in unmanaged:
                        domain = entry.get('name') or entry.get('regexp', '').strip('.*\\.$')
                        self.stdout.write(f"  - {domain}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur: {e}"))
            return

        try:
            result = service.sync_from_mikrotik(import_unmanaged=True)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Importation terminée: {result.get('verified', 0)} vérifiée(s), "
                    f"{result.get('imported', 0)} importée(s), "
                    f"{result.get('orphaned', 0)} orpheline(s)"
                )
            )
            if result.get('errors'):
                for error in result['errors']:
                    self.stdout.write(
                        self.style.ERROR(f"  Erreur: {error}")
                    )

        except Exception as e:
            raise CommandError(f"Erreur lors de l'importation: {e}")
