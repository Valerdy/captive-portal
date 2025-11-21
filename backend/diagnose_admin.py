#!/usr/bin/env python
"""
Script de diagnostic pour l'authentification admin
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import authenticate
from core.models import User

def diagnose_admin_auth():
    print("=" * 60)
    print("DIAGNOSTIC D'AUTHENTIFICATION ADMIN")
    print("=" * 60)
    print()

    # Demander les identifiants
    username = input("Entrez le nom d'utilisateur à tester: ").strip()

    if not username:
        print("❌ Nom d'utilisateur vide!")
        return

    # Chercher l'utilisateur
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"❌ Utilisateur '{username}' n'existe pas dans la base de données!")
        print()
        print("Utilisateurs disponibles:")
        for u in User.objects.all():
            print(f"  - {u.username} (staff={u.is_staff}, superuser={u.is_superuser}, active={u.is_active})")
        return

    print(f"✅ Utilisateur trouvé: {username}")
    print()
    print("INFORMATIONS SUR L'UTILISATEUR:")
    print(f"  - ID: {user.id}")
    print(f"  - Username: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - First Name: {user.first_name}")
    print(f"  - Last Name: {user.last_name}")
    print(f"  - is_active: {user.is_active} {'✅' if user.is_active else '❌'}")
    print(f"  - is_staff: {user.is_staff} {'✅' if user.is_staff else '❌'}")
    print(f"  - is_superuser: {user.is_superuser} {'✅' if user.is_superuser else '✅' if user.is_staff else '❌'}")
    print(f"  - Date joined: {user.date_joined}")
    print(f"  - Last login: {user.last_login}")
    print(f"  - Password hash: {user.password[:20]}...")
    print()

    # Vérifications
    issues = []

    if not user.is_active:
        issues.append("❌ L'utilisateur n'est PAS ACTIF (is_active=False)")
        issues.append("   Solution: Activer l'utilisateur avec: user.is_active = True; user.save()")

    if not user.is_staff and not user.is_superuser:
        issues.append("❌ L'utilisateur N'A PAS les droits administrateur")
        issues.append("   Solution: Donner les droits avec: user.is_staff = True; user.save()")

    if not user.password or not user.password.startswith('pbkdf2_sha256'):
        issues.append("❌ Le mot de passe semble mal hashé ou vide")
        issues.append("   Solution: Réinitialiser le mot de passe")

    if issues:
        print("PROBLÈMES DÉTECTÉS:")
        for issue in issues:
            print(issue)
        print()
    else:
        print("✅ Aucun problème de configuration détecté")
        print()

    # Test d'authentification
    print("TEST D'AUTHENTIFICATION:")
    print()
    password = input("Entrez le mot de passe à tester (ne sera pas affiché): ")

    if not password:
        print("❌ Mot de passe vide!")
        return

    print()
    print("Test d'authentification en cours...")

    # Test avec authenticate()
    auth_user = authenticate(username=username, password=password)

    print()
    if auth_user is not None:
        print("✅ AUTHENTIFICATION RÉUSSIE!")
        print(f"   L'utilisateur {username} peut se connecter")

        if auth_user.is_staff or auth_user.is_superuser:
            print("✅ L'utilisateur a les droits administrateur")
            print()
            print("CONCLUSION:")
            print("L'authentification devrait fonctionner. Si elle ne fonctionne pas sur le frontend,")
            print("le problème pourrait être:")
            print("  1. Un problème de CORS")
            print("  2. Un problème avec les tokens JWT")
            print("  3. Un problème de configuration du frontend")
        else:
            print("❌ L'utilisateur N'A PAS les droits administrateur")
            print()
            print("SOLUTION:")
            print(f"Exécutez: python backend/fix_admin_user.py {username}")
    else:
        print("❌ AUTHENTIFICATION ÉCHOUÉE!")
        print()
        print("CAUSES POSSIBLES:")
        print("  1. Le mot de passe est incorrect")
        print("  2. L'utilisateur n'est pas actif (is_active=False)")
        print("  3. Le mot de passe est mal hashé dans la base de données")
        print()
        print("SOLUTION:")
        print(f"Réinitialisez le mot de passe avec: python backend/manage.py changepassword {username}")
        print("Ou créez un nouveau superuser: python backend/manage.py createsuperuser")

    print()
    print("=" * 60)

if __name__ == '__main__':
    try:
        diagnose_admin_auth()
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
