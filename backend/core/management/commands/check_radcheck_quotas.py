"""
Commande pour vérifier les quotas basés sur radcheck.quota et radacct,
et désactiver automatiquement les utilisateurs qui ont atteint leurs limites.

Cette commande implémente un système de quotas simple:
1. Le quota est défini dans radcheck.quota (en octets, ex: 53687091200 = 50 Go)
2. La consommation est calculée depuis radacct (acctinputoctets + acctoutputoctets)
3. Quand consommation >= quota, l'utilisateur est désactivé (statut=0)
4. Un log de déconnexion est créé avec les détails

Usage:
    python manage.py check_radcheck_quotas
    python manage.py check_radcheck_quotas --dry-run  # Mode test
    python manage.py check_radcheck_quotas --verbose  # Mode détaillé
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Q
from core.models import User, UserDisconnectionLog
from radius.models import RadCheck, RadAcct


class Command(BaseCommand):
    help = "Vérifie les quotas radcheck.quota contre radacct et désactive les utilisateurs"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode test: affiche les actions sans les effectuer',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche plus de détails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']

        self.stdout.write(self.style.WARNING('='*70))
        self.stdout.write(self.style.WARNING('VÉRIFICATION DES QUOTAS RADCHECK'))
        self.stdout.write(self.style.WARNING('='*70))

        if dry_run:
            self.stdout.write(self.style.NOTICE('\n🔍 MODE DRY-RUN: Aucune modification ne sera effectuée\n'))
        else:
            self.stdout.write(self.style.NOTICE('\n⚠️  MODE RÉEL: Les utilisateurs seront désactivés\n'))

        # Statistiques
        stats = {
            'total_checked': 0,
            'quota_exceeded': 0,
            'already_disconnected': 0,
            'no_quota_defined': 0,
            'no_usage': 0,
        }

        # Récupérer tous les utilisateurs avec un quota défini dans radcheck
        # On cherche les entrées radcheck avec quota défini (not NULL)
        users_with_quota = RadCheck.objects.filter(
            attribute='Cleartext-Password',  # L'entrée principale
            quota__isnull=False,  # Quota défini
            statut=True  # Actuellement actifs
        ).values_list('username', flat=True).distinct()

        self.stdout.write(f"✓ {len(users_with_quota)} utilisateurs avec quota trouvés\n"))

        for username in users_with_quota:
            stats['total_checked'] += 1

            if verbose:
                self.stdout.write(f"\n[{stats['total_checked']}] Vérification: {username}")

            # Récupérer le quota défini dans radcheck
            radcheck_entry = RadCheck.objects.filter(
                username=username,
                attribute='Cleartext-Password'
            ).first()

            if not radcheck_entry or not radcheck_entry.quota:
                stats['no_quota_defined'] += 1
                if verbose:
                    self.stdout.write(f"  ⊘ Quota non défini, passage")
                continue

            quota_limit = radcheck_entry.quota

            # Calculer la consommation totale depuis radacct
            # Somme de tous les acctinputoctets + acctoutputoctets pour cet utilisateur
            usage_stats = RadAcct.objects.filter(
                username=username
            ).aggregate(
                total_input=Sum('acctinputoctets'),
                total_output=Sum('acctoutputoctets')
            )

            total_input = usage_stats['total_input'] or 0
            total_output = usage_stats['total_output'] or 0
            quota_used = total_input + total_output

            if quota_used == 0:
                stats['no_usage'] += 1
                if verbose:
                    self.stdout.write(f"  ⊘ Aucune consommation enregistrée")
                continue

            # Calculer le pourcentage utilisé
            quota_percent = (quota_used / quota_limit * 100) if quota_limit > 0 else 0

            if verbose:
                quota_used_gb = quota_used / (1024**3)
                quota_limit_gb = quota_limit / (1024**3)
                self.stdout.write(f"  📊 Quota: {quota_used_gb:.2f} Go / {quota_limit_gb:.2f} Go ({quota_percent:.1f}%)")

            # Vérifier si le quota est dépassé
            if quota_used >= quota_limit:
                stats['quota_exceeded'] += 1

                # Récupérer l'utilisateur Django (si existe)
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    user = None
                    if verbose:
                        self.stdout.write(f"  ⚠️  Utilisateur Django non trouvé, désactivation RADIUS uniquement")

                # Vérifier si déjà un log actif
                if user:
                    existing_log = UserDisconnectionLog.objects.filter(
                        user=user,
                        is_active=True
                    ).first()

                    if existing_log:
                        stats['already_disconnected'] += 1
                        if verbose:
                            self.stdout.write(f"  ⊗ Déjà un log de déconnexion actif")
                        continue

                quota_used_gb = quota_used / (1024**3)
                quota_limit_gb = quota_limit / (1024**3)
                description = f"Quota dépassé: {quota_used_gb:.2f} Go / {quota_limit_gb:.2f} Go"

                if not dry_run:
                    try:
                        with transaction.atomic():
                            # Désactiver l'utilisateur dans radcheck (statut=0)
                            updated = RadCheck.objects.filter(username=username).update(statut=False)

                            # Créer le log de déconnexion (si l'utilisateur Django existe)
                            if user:
                                UserDisconnectionLog.objects.create(
                                    user=user,
                                    reason='quota_exceeded',
                                    description=description,
                                    quota_used=quota_used,
                                    quota_limit=quota_limit,
                                    is_active=True
                                )

                            self.stdout.write(self.style.ERROR(
                                f"  ✗ DÉSACTIVÉ: {username} - {description}"
                            ))
                            self.stdout.write(f"     → {updated} entrée(s) radcheck mises à jour (statut=0)")

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"  ✗ ERREUR lors de la désactivation de {username}: {str(e)}"
                        ))

                else:
                    self.stdout.write(self.style.WARNING(
                        f"  [DRY-RUN] Désactiverait: {username} - {description}"
                    ))

            else:
                if verbose:
                    remaining_gb = (quota_limit - quota_used) / (1024**3)
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ OK: {remaining_gb:.2f} Go restants ({100-quota_percent:.1f}%)"
                    ))

        # Afficher les statistiques finales
        self.stdout.write(self.style.WARNING('\n' + '='*70))
        self.stdout.write(self.style.WARNING('STATISTIQUES'))
        self.stdout.write(self.style.WARNING('='*70))

        self.stdout.write(f"\n📊 Utilisateurs vérifiés: {stats['total_checked']}")
        self.stdout.write(f"⊘ Sans quota défini: {stats['no_quota_defined']}")
        self.stdout.write(f"⊘ Sans consommation: {stats['no_usage']}")
        self.stdout.write(f"⊗ Déjà déconnectés: {stats['already_disconnected']}")

        if not dry_run:
            self.stdout.write(f"\n🔴 Total désactivés: {stats['quota_exceeded']}")
        else:
            self.stdout.write(f"\n🟡 Seraient désactivés: {stats['quota_exceeded']}")

        self.stdout.write(self.style.SUCCESS('\n✅ Vérification terminée'))
        self.stdout.write(self.style.WARNING('='*70 + '\n'))

        if dry_run:
            self.stdout.write(self.style.NOTICE(
                '💡 Exécutez sans --dry-run pour effectuer les désactivations'
            ))
