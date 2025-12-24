"""
Commande Django pour vérifier et appliquer les quotas utilisateurs.

Usage:
    python manage.py check_quotas

Cette commande doit être exécutée régulièrement via crontab:
    */5 * * * * cd /path/to/project && python manage.py check_quotas
"""

from django.core.management.base import BaseCommand
from radius.tasks import check_and_enforce_quotas


class Command(BaseCommand):
    help = 'Vérifie les quotas utilisateurs et désactive ceux qui les ont dépassés'

    def handle(self, *args, **options):
        self.stdout.write('Vérification des quotas en cours...')

        try:
            result = check_and_enforce_quotas()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Vérification terminée:\n"
                    f"  - Utilisateurs vérifiés: {result['total_checked']}\n"
                    f"  - Désactivés (quota): {result['disabled_quota']}\n"
                    f"  - Désactivés (expiration): {result['disabled_validity']}\n"
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
