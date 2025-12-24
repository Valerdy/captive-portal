#!/usr/bin/env python3
"""
Script pour corriger les permissions d'un utilisateur admin
Rend un utilisateur superuser et staff
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

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ️  {message}{RESET}")

def main():
    # Configurer Django
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(BASE_DIR))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

    try:
        django.setup()
    except Exception as e:
        print_error(f"Erreur Django: {e}")
        return 1

    from django.contrib.auth import get_user_model

    User = get_user_model()

    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}{'CORRECTION DES PERMISSIONS ADMIN'.center(70)}{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")

    # Demander le nom d'utilisateur
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        print_info("Utilisateurs existants:")
        for user in User.objects.all():
            status = []
            if user.is_superuser:
                status.append("superuser")
            if user.is_staff:
                status.append("staff")
            if not user.is_active:
                status.append("inactif")

            status_str = f" ({', '.join(status)})" if status else ""
            print(f"  • {user.username}{status_str}")

        print()
        username = input("Entrez le nom d'utilisateur à corriger: ").strip()

    if not username:
        print_error("Nom d'utilisateur vide")
        return 1

    # Trouver l'utilisateur
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print_error(f"Utilisateur '{username}' introuvable")
        return 1

    print(f"\n{BOLD}Utilisateur trouvé: {user.username}{RESET}")
    print(f"  Email: {user.email}")
    print()

    # Afficher l'état actuel
    print(f"{BOLD}État actuel:{RESET}")
    print(f"  is_superuser: {user.is_superuser}")
    print(f"  is_staff:     {user.is_staff}")
    print(f"  is_active:    {user.is_active}")
    print()

    # Modifier les permissions
    modified = False

    if not user.is_superuser:
        user.is_superuser = True
        print_success("✓ is_superuser = True")
        modified = True
    else:
        print_info("is_superuser déjà True")

    if not user.is_staff:
        user.is_staff = True
        print_success("✓ is_staff = True")
        modified = True
    else:
        print_info("is_staff déjà True")

    if not user.is_active:
        user.is_active = True
        print_success("✓ is_active = True")
        modified = True
    else:
        print_info("is_active déjà True")

    if modified:
        user.save()
        print()
        print_success(f"Utilisateur '{username}' mis à jour avec succès!")
    else:
        print()
        print_info("Aucune modification nécessaire")

    print()
    print(f"{BOLD}Nouvel état:{RESET}")
    print(f"  is_superuser: {GREEN}{user.is_superuser}{RESET}")
    print(f"  is_staff:     {GREEN}{user.is_staff}{RESET}")
    print(f"  is_active:    {GREEN}{user.is_active}{RESET}")

    print()
    print(f"{BOLD}{'─'*70}{RESET}")
    print(f"{BOLD}L'utilisateur '{username}' peut maintenant:{RESET}")
    print(f"  {GREEN}✅{RESET} Accéder à l'admin Django: http://localhost:8000/admin")
    print(f"  {GREEN}✅{RESET} Accéder au dashboard admin frontend: http://localhost:5173")
    print(f"  {GREEN}✅{RESET} Gérer tous les utilisateurs")
    print(f"  {GREEN}✅{RESET} Accéder à toutes les fonctionnalités admin")
    print(f"{BOLD}{'─'*70}{RESET}\n")

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Opération annulée{RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
