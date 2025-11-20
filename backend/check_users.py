#!/usr/bin/env python3
"""
Script de diagnostic des utilisateurs et permissions
Vérifie les utilisateurs dans la base de données et leurs permissions
"""

import os
import sys
import django
from pathlib import Path

# Couleurs
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

def print_header(title):
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}{title.center(70)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}\n")

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ️  {message}{RESET}")

def main():
    # Configurer Django
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(BASE_DIR))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

    try:
        django.setup()
        print_success("Django configuré")
    except Exception as e:
        print_error(f"Erreur Django: {e}")
        return 1

    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

    User = get_user_model()

    print_header("LISTE DES UTILISATEURS")

    users = User.objects.all()

    if not users.exists():
        print_warning("Aucun utilisateur trouvé dans la base de données")
        return 1

    print(f"Nombre total d'utilisateurs: {users.count()}\n")

    for user in users:
        print(f"{BOLD}{'─'*70}{RESET}")
        print(f"{BOLD}Utilisateur #{user.id}: {user.username}{RESET}")
        print(f"{'─'*70}")

        print(f"  Email:           {user.email}")
        print(f"  Nom complet:     {user.first_name} {user.last_name}")
        print(f"  Téléphone:       {user.phone_number or 'N/A'}")
        print(f"  MAC:             {user.mac_address or 'N/A'}")
        print(f"  IP:              {user.ip_address or 'N/A'}")

        print(f"\n  {BOLD}Permissions:{RESET}")

        if user.is_superuser:
            print(f"    {GREEN}✅ Superuser (Accès complet){RESET}")
        else:
            print(f"    {RED}❌ Pas superuser{RESET}")

        if user.is_staff:
            print(f"    {GREEN}✅ Staff (Accès admin Django){RESET}")
        else:
            print(f"    {RED}❌ Pas staff{RESET}")

        if user.is_active:
            print(f"    {GREEN}✅ Compte actif{RESET}")
        else:
            print(f"    {RED}❌ Compte inactif{RESET}")

        print(f"\n  {BOLD}Accès:{RESET}")

        # Vérifier accès admin Django
        can_access_django_admin = user.is_staff and user.is_active
        if can_access_django_admin:
            print(f"    {GREEN}✅ Peut accéder à /admin (Django Admin){RESET}")
        else:
            print(f"    {RED}❌ Ne peut pas accéder à /admin{RESET}")

        # Vérifier accès admin frontend
        can_access_frontend_admin = (user.is_staff or user.is_superuser) and user.is_active
        if can_access_frontend_admin:
            print(f"    {GREEN}✅ Peut accéder au dashboard admin frontend{RESET}")
        else:
            print(f"    {RED}❌ Ne peut pas accéder au dashboard admin{RESET}")

        # Vérifier si c'est un utilisateur voucher
        if user.is_voucher_user:
            print(f"    {YELLOW}⚠️  Utilisateur voucher (temporaire){RESET}")
            print(f"    Code voucher: {user.voucher_code}")

        # Compter les tokens JWT
        token_count = OutstandingToken.objects.filter(user=user).count()
        print(f"\n  {BOLD}Tokens JWT:{RESET}")
        print(f"    Tokens actifs: {token_count}")

        print(f"\n  {BOLD}Dates:{RESET}")
        print(f"    Créé le:         {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Modifié le:      {user.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if user.last_login:
            print(f"    Dernière connexion: {user.last_login.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"    Dernière connexion: Jamais")

        print()

    # Vérifier s'il y a un admin
    print_header("VÉRIFICATION DES ADMINS")

    superusers = User.objects.filter(is_superuser=True, is_active=True)
    staff_users = User.objects.filter(is_staff=True, is_active=True)

    if superusers.exists():
        print_success(f"Superusers trouvés: {superusers.count()}")
        for user in superusers:
            print(f"  • {user.username} ({user.email})")
    else:
        print_warning("Aucun superuser actif trouvé")

    if staff_users.exists():
        print_success(f"Staff users trouvés: {staff_users.count()}")
        for user in staff_users:
            print(f"  • {user.username} ({user.email})")
    else:
        print_warning("Aucun staff user actif trouvé")

    # Recommandations
    print_header("RECOMMANDATIONS")

    problems_found = False

    for user in users:
        if not user.is_active:
            print_warning(f"L'utilisateur '{user.username}' est inactif")
            print(f"  Pour l'activer: python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); u = User.objects.get(username='{user.username}'); u.is_active = True; u.save(); print('Activé')\"")
            problems_found = True

        if user.is_staff and not user.is_superuser:
            print_info(f"L'utilisateur '{user.username}' est staff mais pas superuser")
            print(f"  Pour le promouvoir: python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); u = User.objects.get(username='{user.username}'); u.is_superuser = True; u.save(); print('Promu superuser')\"")

        if not user.is_staff and user.is_superuser:
            print_warning(f"L'utilisateur '{user.username}' est superuser mais pas staff")
            print(f"  Pour corriger: python manage.py shell -c \"from django.contrib.auth import get_user_model(); User = get_user_model(); u = User.objects.get(username='{user.username}'); u.is_staff = True; u.save(); print('Corrigé')\"")
            problems_found = True

    if not problems_found and superusers.exists():
        print_success("Aucun problème détecté !")
        print()
        print_info("Pour vous connecter:")
        print("  • Admin Django: http://localhost:8000/admin")
        print("  • Admin Frontend: http://localhost:5173 → Cliquez sur 'Admin' en haut à droite")

    # Test de connexion
    print_header("TEST DE CONNEXION")

    print_info("Pour tester la connexion d'un utilisateur:")
    print()

    for user in users:
        if user.is_active and (user.is_staff or user.is_superuser):
            print(f"Utilisateur: {user.username}")
            print(f"  curl -X POST http://localhost:8000/api/core/auth/login/ \\")
            print(f"    -H 'Content-Type: application/json' \\")
            print(f"    -d '{{\"username\": \"{user.username}\", \"password\": \"VOTRE_MOT_DE_PASSE\"}}'")
            print()

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Diagnostic interrompu{RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
