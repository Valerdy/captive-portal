#!/usr/bin/env python
"""
Script de test de connexion MySQL pour FreeRADIUS

Ce script vérifie que Django peut se connecter à la base MySQL du serveur FreeRADIUS.
"""
import os
import sys
import django

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection
from django.conf import settings

def test_connection():
    """Tester la connexion à MySQL"""
    print("=" * 60)
    print("TEST DE CONNEXION MYSQL - FREERADIUS")
    print("=" * 60)

    # Afficher la configuration
    db_config = settings.DATABASES['default']
    print("\n📋 Configuration actuelle:")
    print(f"   Engine: {db_config['ENGINE']}")
    print(f"   Database: {db_config['NAME']}")
    print(f"   User: {db_config['USER']}")
    print(f"   Host: {db_config['HOST']}")
    print(f"   Port: {db_config['PORT']}")

    print("\n🔌 Test de connexion...")

    try:
        with connection.cursor() as cursor:
            # Test 1: Version MySQL
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            print(f"✅ Connexion MySQL réussie!")
            print(f"   Version MySQL: {version[0]}")

            # Test 2: Nom de la base actuelle
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()
            print(f"   Base de données: {db_name[0]}")

            # Test 3: Lister les tables
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print(f"\n📊 Tables disponibles ({len(tables)}):")

            # Tables FreeRADIUS attendues
            expected_tables = [
                'radacct', 'radcheck', 'radgroupcheck', 'radgroupreply',
                'radpostauth', 'radreply', 'radusergroup', 'nas'
            ]

            found_tables = [table[0] for table in tables]

            for table in found_tables:
                is_radius_table = '✓' if table in expected_tables else ' '
                print(f"   [{is_radius_table}] {table}")

            # Test 4: Vérifier quelques tables FreeRADIUS
            print("\n🔍 Vérification des tables FreeRADIUS:")

            # radcheck
            if 'radcheck' in found_tables:
                cursor.execute("SELECT COUNT(*) FROM radcheck;")
                count = cursor.fetchone()[0]
                print(f"   ✓ radcheck: {count} entrées")

            # radacct
            if 'radacct' in found_tables:
                cursor.execute("SELECT COUNT(*) FROM radacct;")
                count = cursor.fetchone()[0]
                print(f"   ✓ radacct: {count} entrées")

                cursor.execute("SELECT COUNT(*) FROM radacct WHERE acctstoptime IS NULL;")
                active = cursor.fetchone()[0]
                print(f"   ✓ Sessions actives: {active}")

            # nas
            if 'nas' in found_tables:
                cursor.execute("SELECT COUNT(*) FROM nas;")
                count = cursor.fetchone()[0]
                print(f"   ✓ nas: {count} entrées")

            print("\n" + "=" * 60)
            print("✅ TOUS LES TESTS SONT PASSÉS!")
            print("=" * 60)
            print("\n💡 Prochaines étapes:")
            print("   1. Créer les migrations: python manage.py makemigrations")
            print("   2. Appliquer les migrations: python manage.py migrate")
            print("   3. Créer un superuser: python manage.py createsuperuser")
            print("   4. Démarrer le serveur: python manage.py runserver")

            return True

    except Exception as e:
        print(f"\n❌ ERREUR DE CONNEXION:")
        print(f"   {str(e)}")
        print("\n💡 Solutions possibles:")
        print("   1. Vérifiez les paramètres dans le fichier .env")
        print("   2. Vérifiez que MySQL est démarré sur le serveur")
        print("   3. Vérifiez que l'utilisateur MySQL a les bonnes permissions")
        print("   4. Vérifiez que le firewall autorise les connexions (port 3306)")
        print("\n📖 Consultez MYSQL_CONFIG.md pour plus d'informations")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
