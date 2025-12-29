"""
Script de diagnostic RADIUS pour vérifier la configuration.

Usage:
    python manage.py shell < verify_radius_config.py

Ou dans le shell Django:
    exec(open('verify_radius_config.py').read())
"""
from django.db import connection
from radius.models import RadGroupReply, RadGroupCheck, RadUserGroup, RadCheck
from radius.services import RadiusProfileGroupService
from core.models import Profile, User

def print_section(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def verify_radius_config():
    print_section("DIAGNOSTIC RADIUS - ARCHITECTURE GROUP-BASED")

    # 1. Vérifier les profils Django
    print_section("1. PROFILS DJANGO")
    profiles = Profile.objects.filter(is_active=True)
    print(f"Profils actifs: {profiles.count()}")
    for p in profiles:
        groupname = RadiusProfileGroupService.get_group_name(p)
        print(f"  - {p.name} (ID: {p.id}) → {groupname}")
        print(f"    Débit: {p.bandwidth_download}M/{p.bandwidth_upload}M")
        print(f"    Quota: {p.data_volume / (1024**3):.1f} Go ({p.quota_type})")
        print(f"    Session: {p.session_timeout}s, Idle: {p.idle_timeout}s")

    # 2. Vérifier radgroupreply
    print_section("2. RADGROUPREPLY (Attributs de groupe)")
    groups = RadGroupReply.objects.filter(groupname__startswith='profile_').values('groupname').distinct()
    print(f"Groupes configurés: {groups.count()}")

    for g in groups:
        attrs = RadGroupReply.objects.filter(groupname=g['groupname']).order_by('priority')
        print(f"\n  {g['groupname']}:")
        for attr in attrs:
            print(f"    {attr.attribute} {attr.op} {attr.value}")

    # 3. Vérifier radgroupcheck
    print_section("3. RADGROUPCHECK (Vérifications de groupe)")
    checks = RadGroupCheck.objects.filter(groupname__startswith='profile_')
    print(f"Entrées: {checks.count()}")
    for c in checks:
        print(f"  {c.groupname}: {c.attribute} {c.op} {c.value}")

    # 4. Vérifier radusergroup
    print_section("4. RADUSERGROUP (Assignations utilisateur → groupe)")
    usergroups = RadUserGroup.objects.filter(groupname__startswith='profile_').order_by('groupname', 'priority')
    print(f"Assignations: {usergroups.count()}")

    by_group = {}
    for ug in usergroups:
        if ug.groupname not in by_group:
            by_group[ug.groupname] = []
        by_group[ug.groupname].append(f"{ug.username} (p:{ug.priority})")

    for group, users in by_group.items():
        print(f"\n  {group}:")
        print(f"    Utilisateurs: {', '.join(users[:5])}")
        if len(users) > 5:
            print(f"    ... et {len(users) - 5} autres")

    # 5. Utilisateurs sans groupe profil
    print_section("5. UTILISATEURS SANS GROUPE PROFIL")
    activated_users = User.objects.filter(is_radius_activated=True, is_active=True)
    users_with_groups = set(RadUserGroup.objects.filter(
        groupname__startswith='profile_'
    ).values_list('username', flat=True))

    without_groups = []
    for user in activated_users:
        if user.username not in users_with_groups:
            profile = user.get_effective_profile()
            without_groups.append(f"{user.username} (profile: {profile.name if profile else 'AUCUN'})")

    if without_groups:
        print(f"Utilisateurs activés SANS groupe profil: {len(without_groups)}")
        for u in without_groups[:10]:
            print(f"  ⚠️  {u}")
        if len(without_groups) > 10:
            print(f"  ... et {len(without_groups) - 10} autres")
    else:
        print("✅ Tous les utilisateurs activés ont un groupe profil")

    # 6. Vérification radcheck
    print_section("6. RADCHECK (Authentification)")
    radcheck_count = RadCheck.objects.filter(attribute='Cleartext-Password').count()
    enabled_count = RadCheck.objects.filter(attribute='Cleartext-Password', statut=True).count()
    print(f"Utilisateurs dans radcheck: {radcheck_count}")
    print(f"  - Activés (statut=1): {enabled_count}")
    print(f"  - Désactivés (statut=0): {radcheck_count - enabled_count}")

    # 7. Résumé
    print_section("RÉSUMÉ")
    issues = []

    if groups.count() != profiles.count():
        issues.append(f"Groupes RADIUS ({groups.count()}) != Profils Django ({profiles.count()})")

    if without_groups:
        issues.append(f"{len(without_groups)} utilisateurs activés sans groupe profil")

    if not RadGroupReply.objects.filter(attribute='Mikrotik-Rate-Limit').exists():
        issues.append("Aucun attribut Mikrotik-Rate-Limit trouvé")

    if issues:
        print("⚠️  PROBLÈMES DÉTECTÉS:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n💡 Solution: Exécutez 'python manage.py sync_radius_groups'")
    else:
        print("✅ Configuration RADIUS correcte!")
        print("\n📝 Pour tester un utilisateur:")
        print("   radtest <username> <password> localhost 0 testing123")

if __name__ == "__main__" or True:
    verify_radius_config()
