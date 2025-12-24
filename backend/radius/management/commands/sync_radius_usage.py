"""
Commande Django pour synchroniser la consommation depuis FreeRADIUS.

Usage:
    python manage.py sync_radius_usage

Cette commande doit être exécutée régulièrement via crontab:
    */10 * * * * cd /path/to/project && python manage.py sync_radius_usage
"""

from django.core.management.base import BaseCommand
from radius.services import QuotaEnforcementService


class Command(BaseCommand):
    help = 'Synchronise les données de consommation depuis radacct vers Django'

    def handle(self, *args, **options):
        self.stdout.write('Synchronisation de la consommation...')

        try:
            result = QuotaEnforcementService.sync_usage_from_radacct()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Synchronisation terminée:\n"
                    f"  - Utilisateurs vérifiés: {result['total']}\n"
                    f"  - Utilisateurs mis à jour: {result['updated']}\n"
                    f"  - Erreurs: {len(result['errors'])}"
                )
            )

            if result['errors']:
                self.stdout.write(self.style.WARNING('Erreurs:'))
                for error in result['errors']:
                    self.stdout.write(f"  - {error['user']}: {error['error']}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {e}'))
            raise
