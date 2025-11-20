#!/usr/bin/env python3
"""
Script de test de connexion PostgreSQL
Vérifie que Django peut se connecter à PostgreSQL avec les paramètres du .env
"""

import os
import sys
import django
from pathlib import Path

# Couleurs pour l'affichage
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

def print_header(title):
    """Affiche un titre de section"""
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}{title.center(70)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}\n")

def print_success(message):
    """Affiche un message de succès"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    """Affiche un message d'erreur"""
    print(f"{RED}❌ {message}{RESET}")

def print_warning(message):
    """Affiche un avertissement"""
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_info(message):
    """Affiche une information"""
    print(f"{BLUE}ℹ️  {message}{RESET}")

def test_postgresql_connection():
    """Test de connexion PostgreSQL"""

    print_header("TEST DE CONNEXION POSTGRESQL")

    # Configurer Django
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(BASE_DIR))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

    try:
        django.setup()
        print_success("Django configuré avec succès")
    except Exception as e:
        print_error(f"Erreur lors de la configuration de Django: {e}")
        return False

    # Importer après django.setup()
    from django.conf import settings
    from django.db import connection

    # Afficher la configuration
    print_header("CONFIGURATION DATABASE")

    db_config = settings.DATABASES['default']

    print_info(f"Engine:   {db_config['ENGINE']}")
    print_info(f"Database: {db_config['NAME']}")
    print_info(f"User:     {db_config['USER']}")
    print_info(f"Host:     {db_config['HOST']}")
    print_info(f"Port:     {db_config['PORT']}")

    if db_config['ENGINE'] != 'django.db.backends.postgresql':
        print_error("Le moteur de base de données n'est pas PostgreSQL!")
        print_warning("Vérifiez que DB_ENGINE=django.db.backends.postgresql dans .env")
        return False

    print_success("Configuration PostgreSQL détectée")

    # Test de connexion
    print_header("TEST DE CONNEXION")

    try:
        # Tester la connexion
        with connection.cursor() as cursor:
            # Version PostgreSQL
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print_success("Connexion PostgreSQL établie!")
            print_info(f"Version: {version.split(',')[0]}")

            # Nom de la base de données
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            print_success(f"Base de données connectée: {db_name}")

            # Utilisateur actuel
            cursor.execute("SELECT current_user;")
            current_user = cursor.fetchone()[0]
            print_success(f"Utilisateur connecté: {current_user}")

    except Exception as e:
        print_error(f"Erreur de connexion: {e}")
        print()
        print_warning("Vérifications à effectuer:")
        print("  1. PostgreSQL est-il installé et démarré?")
        print("  2. La base de données existe-t-elle? (Créez-la avec pgAdmin)")
        print("  3. Les credentials sont-ils corrects dans .env?")
        print("  4. Le port 5432 est-il accessible?")
        print()
        print_info("Commandes utiles:")
        print("  - Vérifier le service: services.msc → PostgreSQL")
        print("  - Créer DB avec pgAdmin: Databases → Create → Database")
        print("  - Tester connexion: psql -U postgres -h localhost")
        return False

    # Lister les tables
    print_header("TABLES EXISTANTES")

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()

            if tables:
                print_success(f"Nombre de tables: {len(tables)}")
                print()
                for table in tables:
                    print(f"  • {table[0]}")
            else:
                print_warning("Aucune table trouvée")
                print_info("Exécutez 'python manage.py migrate' pour créer les tables")

    except Exception as e:
        print_error(f"Erreur lors de la récupération des tables: {e}")

    # Vérifier les migrations
    print_header("STATUT DES MIGRATIONS")

    try:
        from django.db.migrations.executor import MigrationExecutor
        from django.db import DEFAULT_DB_ALIAS, connections

        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        if plan:
            print_warning(f"Il y a {len(plan)} migration(s) en attente")
            print_info("Exécutez: python manage.py migrate")
        else:
            print_success("Toutes les migrations sont appliquées")

    except Exception as e:
        print_warning(f"Impossible de vérifier les migrations: {e}")
        print_info("Assurez-vous que les migrations sont appliquées: python manage.py migrate")

    # Vérifier les apps Django
    print_header("APPLICATIONS DJANGO")

    installed_apps = [
        'core', 'mikrotik', 'radius'
    ]

    for app in installed_apps:
        if app in settings.INSTALLED_APPS:
            print_success(f"App '{app}' installée")
        else:
            print_error(f"App '{app}' manquante")

    # Statistiques de la base de données
    print_header("STATISTIQUES BASE DE DONNÉES")

    try:
        with connection.cursor() as cursor:
            # Taille de la base de données
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """)
            db_size = cursor.fetchone()[0]
            print_info(f"Taille de la base: {db_size}")

            # Nombre de connexions actives
            cursor.execute("""
                SELECT count(*)
                FROM pg_stat_activity
                WHERE datname = current_database();
            """)
            active_connections = cursor.fetchone()[0]
            print_info(f"Connexions actives: {active_connections}")

    except Exception as e:
        print_warning(f"Impossible de récupérer les statistiques: {e}")

    # Résumé final
    print_header("RÉSUMÉ")

    print_success("✅ PostgreSQL est configuré et fonctionnel!")
    print()
    print_info("Prochaines étapes:")
    print("  1. Appliquer les migrations: python manage.py migrate")
    print("  2. Créer un superuser: python manage.py createsuperuser")
    print("  3. Démarrer le serveur: python manage.py runserver")
    print()

    return True

def main():
    """Fonction principale"""
    try:
        success = test_postgresql_connection()
        return 0 if success else 1

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrompu par l'utilisateur{RESET}")
        return 130

    except Exception as e:
        print_error(f"Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
