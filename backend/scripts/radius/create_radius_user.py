#!/usr/bin/env python
"""
Script pour créer un utilisateur RADIUS pour le portail captif Mikrotik
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from radius.models import RadCheck, RadReply, RadUserGroup
from django.db import transaction


def create_radius_user(username, password, groupname='user', session_timeout=3600, bandwidth_limit=None):
    """
    Crée un utilisateur RADIUS complet pour le portail captif Mikrotik

    Args:
        username: Nom d'utilisateur
        password: Mot de passe
        groupname: Groupe ('admin' ou 'user')
        session_timeout: Timeout en secondes (default: 3600 = 1h)
        bandwidth_limit: Limite de bande passante Mikrotik (ex: "10M/10M")
    """
    print("=" * 70)
    print("CRÉATION D'UTILISATEUR RADIUS POUR PORTAIL CAPTIF MIKROTIK")
    print("=" * 70)
    print()

    try:
        with transaction.atomic():
            # 1. Créer l'entrée d'authentification dans radcheck
            check, created = RadCheck.objects.update_or_create(
                username=username,
                attribute='Cleartext-Password',
                defaults={
                    'value': password,
                    'op': ':='
                }
            )

            if created:
                print(f"✅ Authentification créée pour '{username}'")
            else:
                print(f"🔄 Authentification mise à jour pour '{username}'")

            # 2. Créer le timeout de session dans radreply
            RadReply.objects.update_or_create(
                username=username,
                attribute='Session-Timeout',
                defaults={
                    'value': str(session_timeout),
                    'op': '='
                }
            )
            print(f"✅ Session timeout: {session_timeout}s ({session_timeout//60} min)")

            # 3. Ajouter la limite de bande passante si spécifiée
            if bandwidth_limit:
                RadReply.objects.update_or_create(
                    username=username,
                    attribute='Mikrotik-Rate-Limit',
                    defaults={
                        'value': bandwidth_limit,
                        'op': '='
                    }
                )
                print(f"✅ Limite de bande passante: {bandwidth_limit}")

            # 4. Assigner au groupe
            RadUserGroup.objects.update_or_create(
                username=username,
                groupname=groupname,
                defaults={
                    'priority': 0
                }
            )
            print(f"✅ Groupe assigné: {groupname}")

        print()
        print("=" * 70)
        print(f"✅ UTILISATEUR '{username}' CRÉÉ AVEC SUCCÈS !")
        print("=" * 70)
        print()
        print("📋 INFORMATIONS DE CONNEXION:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Groupe: {groupname}")
        print(f"   Session: {session_timeout//60} minutes")
        if bandwidth_limit:
            print(f"   Bande passante: {bandwidth_limit}")
        print()
        print("🌐 Vous pouvez maintenant vous connecter au portail captif Mikrotik !")
        print()

        return True

    except Exception as e:
        print(f"❌ ERREUR lors de la création: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_radius_users():
    """Liste tous les utilisateurs RADIUS"""
    print("\n" + "=" * 70)
    print("LISTE DES UTILISATEURS RADIUS")
    print("=" * 70)

    usernames = RadCheck.objects.values_list('username', flat=True).distinct()

    if not usernames:
        print("❌ Aucun utilisateur trouvé")
        return

    print(f"\nTotal: {usernames.count()} utilisateur(s)\n")
    print(f"{'Username':<20} {'Groupe':<15} {'Session':<15} {'Bande passante':<15}")
    print("-" * 70)

    for username in usernames:
        group = RadUserGroup.objects.filter(username=username).first()
        timeout = RadReply.objects.filter(username=username, attribute='Session-Timeout').first()
        bandwidth = RadReply.objects.filter(username=username, attribute='Mikrotik-Rate-Limit').first()

        groupname = group.groupname if group else 'N/A'
        session = f"{int(timeout.value)//60} min" if timeout else 'N/A'
        bw = bandwidth.value if bandwidth else 'N/A'

        print(f"{username:<20} {groupname:<15} {session:<15} {bw:<15}")

    print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python create_radius_user.py <username> <password> [groupe] [timeout] [bandwidth]")
        print()
        print("Exemples:")
        print("  python create_radius_user.py client01 password123")
        print("  python create_radius_user.py admin admin123 admin")
        print("  python create_radius_user.py client02 pass123 user 7200 10M/10M")
        print()
        print("Arguments:")
        print("  username     : Nom d'utilisateur (requis)")
        print("  password     : Mot de passe (requis)")
        print("  groupe       : admin ou user (défaut: user)")
        print("  timeout      : Durée session en secondes (défaut: 3600)")
        print("  bandwidth    : Limite bande passante Mikrotik (ex: 10M/10M)")
        print()
        print("Pour lister les utilisateurs:")
        print("  python create_radius_user.py --list")
        sys.exit(1)

    if sys.argv[1] == '--list':
        list_radius_users()
        sys.exit(0)

    username = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else input("Entrez le mot de passe: ")
    groupname = sys.argv[3] if len(sys.argv) > 3 else 'user'
    session_timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 3600
    bandwidth_limit = sys.argv[5] if len(sys.argv) > 5 else None

    success = create_radius_user(
        username=username,
        password=password,
        groupname=groupname,
        session_timeout=session_timeout,
        bandwidth_limit=bandwidth_limit
    )

    sys.exit(0 if success else 1)
