#!/usr/bin/env python
"""
Liste tous les utilisateurs avec leurs permissions
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import User

def list_all_users():
    print("=" * 80)
    print("LISTE DE TOUS LES UTILISATEURS")
    print("=" * 80)
    print()

    users = User.objects.all().order_by('-is_superuser', '-is_staff', 'username')

    if not users.exists():
        print("❌ Aucun utilisateur trouvé dans la base de données!")
        print()
        print("Pour créer un superuser:")
        print("  python backend/manage.py createsuperuser")
        return

    print(f"Total: {users.count()} utilisateur(s)")
    print()

    # En-tête du tableau
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Active':<8} {'Staff':<8} {'Super':<8} {'Voucher':<10}")
    print("-" * 80)

    for user in users:
        active_icon = "✅" if user.is_active else "❌"
        staff_icon = "✅" if user.is_staff else "❌"
        super_icon = "✅" if user.is_superuser else "❌"
        voucher = "Yes" if user.is_voucher_user else "No"

        print(f"{user.id:<5} {user.username:<20} {user.email:<30} {active_icon:<8} {staff_icon:<8} {super_icon:<8} {voucher:<10}")

    print()
    print("=" * 80)
    print()
    print("LÉGENDE:")
    print("  Active  - L'utilisateur peut se connecter")
    print("  Staff   - L'utilisateur peut accéder à l'admin Django")
    print("  Super   - L'utilisateur a tous les droits (superuser)")
    print("  Voucher - L'utilisateur s'est connecté via un code voucher")
    print()
    print("ACCÈS ADMIN FRONTEND:")
    print("  Pour accéder à /admin/login, l'utilisateur doit avoir:")
    print("  - Active = ✅ (is_active = True)")
    print("  - Staff = ✅ OU Super = ✅ (is_staff = True OU is_superuser = True)")
    print()

    # Compter les admins
    admins = users.filter(is_active=True).filter(is_staff=True) | users.filter(is_active=True).filter(is_superuser=True)
    admin_count = admins.distinct().count()

    if admin_count == 0:
        print("⚠️  ATTENTION: Aucun administrateur actif trouvé!")
        print()
        print("Pour créer un administrateur:")
        print("  python backend/manage.py createsuperuser")
        print()
        print("Ou pour donner les droits admin à un utilisateur existant:")
        print("  python backend/fix_admin_user.py <username>")
    else:
        print(f"✅ {admin_count} administrateur(s) actif(s) trouvé(s):")
        for admin in admins:
            role = "Superuser" if admin.is_superuser else "Staff"
            print(f"  - {admin.username} ({role})")
    print()

if __name__ == '__main__':
    try:
        list_all_users()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
