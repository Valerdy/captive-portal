#!/usr/bin/env python3
"""
Script pour nettoyer les tokens JWT d'un utilisateur
Permet ensuite de supprimer l'utilisateur si nécessaire
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
    except Exception as e:
        print_error(f"Erreur Django: {e}")
        return 1

    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

    User = get_user_model()

    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}{'NETTOYAGE DES TOKENS JWT'.center(70)}{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")

    # Demander le nom d'utilisateur
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        print_info("Utilisateurs avec des tokens:")
        users_with_tokens = User.objects.filter(
            outstandingtoken__isnull=False
        ).distinct()

        for user in users_with_tokens:
            token_count = OutstandingToken.objects.filter(user=user).count()
            print(f"  • {user.username} ({token_count} tokens)")

        print()
        username = input("Entrez le nom d'utilisateur à nettoyer (ou 'all' pour tous): ").strip()

    if not username:
        print_error("Nom d'utilisateur vide")
        return 1

    if username.lower() == 'all':
        print_warning("Suppression de TOUS les tokens JWT")
        confirm = input("Êtes-vous sûr? (oui/non): ").strip().lower()

        if confirm != 'oui':
            print_info("Opération annulée")
            return 0

        outstanding_count = OutstandingToken.objects.count()
        blacklisted_count = BlacklistedToken.objects.count()

        OutstandingToken.objects.all().delete()
        BlacklistedToken.objects.all().delete()

        print_success(f"{outstanding_count} OutstandingTokens supprimés")
        print_success(f"{blacklisted_count} BlacklistedTokens supprimés")
        print()
        print_info("Tous les utilisateurs devront se reconnecter")
        return 0

    # Trouver l'utilisateur
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print_error(f"Utilisateur '{username}' introuvable")
        return 1

    print(f"\n{BOLD}Utilisateur trouvé: {user.username}{RESET}")
    print(f"  Email: {user.email}")
    print()

    # Compter les tokens
    outstanding_tokens = OutstandingToken.objects.filter(user=user)
    outstanding_count = outstanding_tokens.count()

    if outstanding_count == 0:
        print_info("Aucun token trouvé pour cet utilisateur")
        return 0

    print_warning(f"{outstanding_count} token(s) trouvé(s)")
    print()

    for token in outstanding_tokens:
        print(f"  • Token ID: {token.id}")
        print(f"    Créé le: {token.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Expire le: {token.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # Vérifier si blacklisté
        try:
            blacklisted = BlacklistedToken.objects.get(token=token)
            print(f"    Status: {YELLOW}Blacklisté{RESET}")
        except BlacklistedToken.DoesNotExist:
            print(f"    Status: {GREEN}Actif{RESET}")

        print()

    confirm = input(f"Supprimer tous les tokens de '{username}'? (oui/non): ").strip().lower()

    if confirm != 'oui':
        print_info("Opération annulée")
        return 0

    # Supprimer les tokens
    deleted_count, _ = outstanding_tokens.delete()

    print()
    print_success(f"{deleted_count} token(s) supprimé(s)")
    print()
    print_info(f"L'utilisateur '{username}' devra se reconnecter")

    print()
    print(f"{BOLD}{'─'*70}{RESET}")
    print_info("Pour supprimer l'utilisateur dans pgAdmin maintenant:")
    print(f"  1. Ouvrez pgAdmin")
    print(f"  2. Naviguez vers captive_portal_db → Schemas → public → Tables → core_user")
    print(f"  3. Clic droit → View/Edit Data → All Rows")
    print(f"  4. Trouvez l'utilisateur '{username}'")
    print(f"  5. Clic droit sur la ligne → Delete Row")
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
