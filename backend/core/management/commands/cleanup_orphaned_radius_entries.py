"""
Commande de nettoyage des entrées RADIUS orphelines.

Cette commande supprime toutes les entrées dans les tables RADIUS
(radcheck, radreply, radusergroup) qui n'ont pas d'utilisateur
correspondant dans la table User.

Usage:
    python manage.py cleanup_orphaned_radius_entries
    python manage.py cleanup_orphaned_radius_entries --dry-run  # Affiche sans supprimer
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import User
from radius.models import RadCheck, RadReply, RadUserGroup


class Command(BaseCommand):
    help = "Nettoie les entrées RADIUS orphelines (sans utilisateur correspondant dans User)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les entrées à supprimer sans les supprimer réellement',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.WARNING('='*70))
        self.stdout.write(self.style.WARNING('NETTOYAGE DES ENTRÉES RADIUS ORPHELINES'))
        self.stdout.write(self.style.WARNING('='*70))

        if dry_run:
            self.stdout.write(self.style.NOTICE('\n🔍 MODE DRY-RUN: Aucune donnée ne sera supprimée\n'))
        else:
            self.stdout.write(self.style.NOTICE('\n⚠️  MODE RÉEL: Les données seront supprimées\n'))

        # Récupérer tous les usernames valides dans User
        valid_usernames = set(User.objects.values_list('username', flat=True))
        self.stdout.write(f"✓ {len(valid_usernames)} utilisateurs valides trouvés dans User\n")

        # Statistiques
        stats = {
            'radcheck_deleted': 0,
            'radreply_deleted': 0,
            'radusergroup_deleted': 0,
        }

        orphaned_usernames = set()

        # 1. Vérifier RadCheck
        self.stdout.write(self.style.HTTP_INFO('\n[1/3] Analyse de RadCheck...'))
        radcheck_orphans = RadCheck.objects.exclude(username__in=valid_usernames)
        count = radcheck_orphans.count()

        if count > 0:
            orphaned_usernames.update(radcheck_orphans.values_list('username', flat=True))
            self.stdout.write(f"  ⚠️  {count} entrées orphelines trouvées:")

            # Afficher les 10 premières entrées orphelines
            for entry in radcheck_orphans[:10]:
                self.stdout.write(f"      - {entry.username}: {entry.attribute} {entry.op} {entry.value}")

            if count > 10:
                self.stdout.write(f"      ... et {count - 10} autres")

        # 2. Vérifier RadReply
        self.stdout.write(self.style.HTTP_INFO('\n[2/3] Analyse de RadReply...'))
        radreply_orphans = RadReply.objects.exclude(username__in=valid_usernames)
        count = radreply_orphans.count()

        if count > 0:
            orphaned_usernames.update(radreply_orphans.values_list('username', flat=True))
            self.stdout.write(f"  ⚠️  {count} entrées orphelines trouvées:")

            for entry in radreply_orphans[:10]:
                self.stdout.write(f"      - {entry.username}: {entry.attribute} {entry.op} {entry.value}")

            if count > 10:
                self.stdout.write(f"      ... et {count - 10} autres")

        # 3. Vérifier RadUserGroup
        self.stdout.write(self.style.HTTP_INFO('\n[3/3] Analyse de RadUserGroup...'))
        radusergroup_orphans = RadUserGroup.objects.exclude(username__in=valid_usernames)
        count = radusergroup_orphans.count()

        if count > 0:
            orphaned_usernames.update(radusergroup_orphans.values_list('username', flat=True))
            self.stdout.write(f"  ⚠️  {count} entrées orphelines trouvées:")

            for entry in radusergroup_orphans[:10]:
                self.stdout.write(f"      - {entry.username} -> groupe: {entry.groupname}")

            if count > 10:
                self.stdout.write(f"      ... et {count - 10} autres")

        # Résumé des usernames orphelins
        if orphaned_usernames:
            self.stdout.write(self.style.WARNING(f'\n📋 {len(orphaned_usernames)} utilisateur(s) orphelin(s) détecté(s):'))
            for username in sorted(orphaned_usernames):
                self.stdout.write(f"    - {username}")

        # Suppression si pas en dry-run
        if not dry_run and orphaned_usernames:
            confirm = input(f"\n⚠️  Confirmer la suppression de {len(orphaned_usernames)} utilisateur(s) orphelin(s)? (yes/no): ")

            if confirm.lower() == 'yes':
                self.stdout.write(self.style.NOTICE('\n🗑️  Suppression en cours...\n'))

                try:
                    with transaction.atomic():
                        # Supprimer RadCheck
                        deleted = RadCheck.objects.exclude(username__in=valid_usernames).delete()
                        stats['radcheck_deleted'] = deleted[0] if deleted else 0
                        self.stdout.write(f"  ✓ RadCheck: {stats['radcheck_deleted']} entrées supprimées")

                        # Supprimer RadReply
                        deleted = RadReply.objects.exclude(username__in=valid_usernames).delete()
                        stats['radreply_deleted'] = deleted[0] if deleted else 0
                        self.stdout.write(f"  ✓ RadReply: {stats['radreply_deleted']} entrées supprimées")

                        # Supprimer RadUserGroup
                        deleted = RadUserGroup.objects.exclude(username__in=valid_usernames).delete()
                        stats['radusergroup_deleted'] = deleted[0] if deleted else 0
                        self.stdout.write(f"  ✓ RadUserGroup: {stats['radusergroup_deleted']} entrées supprimées")

                    self.stdout.write(self.style.SUCCESS('\n✅ Nettoyage terminé avec succès!'))

                    total_deleted = sum(stats.values())
                    self.stdout.write(self.style.SUCCESS(f'📊 Total: {total_deleted} entrées supprimées'))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'\n❌ Erreur lors de la suppression: {str(e)}'))
                    return
            else:
                self.stdout.write(self.style.WARNING('\n🚫 Suppression annulée'))

        elif not orphaned_usernames:
            self.stdout.write(self.style.SUCCESS('\n✅ Aucune entrée orpheline trouvée! Base de données propre.'))

        elif dry_run:
            self.stdout.write(self.style.NOTICE('\n💡 Exécutez sans --dry-run pour supprimer ces entrées'))

        self.stdout.write(self.style.WARNING('\n' + '='*70 + '\n'))
