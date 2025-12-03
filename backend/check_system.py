#!/usr/bin/env python
"""
Script de diagnostic du système
Usage: python check_system.py
"""
import os
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from core.models import Promotion, User

def check_migrations():
    """Vérifie que toutes les migrations sont appliquées"""
    print("=== Vérification des migrations ===\n")

    with connection.cursor() as cursor:
        # Vérifier si la table promotions existe
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = 'promotions'
        """)
        promotions_table_exists = cursor.fetchone()[0] > 0

        if promotions_table_exists:
            print("✅ Table 'promotions' existe")
        else:
            print("❌ Table 'promotions' n'existe PAS")
            print("   → Exécutez: python manage.py migrate")
            return False

        # Vérifier si le champ cleartext_password existe dans users
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = 'users'
            AND column_name = 'cleartext_password'
        """)
        cleartext_field_exists = cursor.fetchone()[0] > 0

        if cleartext_field_exists:
            print("✅ Champ 'cleartext_password' existe dans users")
        else:
            print("❌ Champ 'cleartext_password' n'existe PAS dans users")
            print("   → Exécutez: python manage.py migrate")
            return False

    return True

def check_promotions():
    """Vérifie les promotions dans la base de données"""
    print("\n=== Vérification des promotions ===\n")

    try:
        count = Promotion.objects.count()
        active_count = Promotion.objects.filter(is_active=True).count()

        print(f"Total promotions: {count}")
        print(f"Promotions actives: {active_count}")

        if count == 0:
            print("\n⚠️  Aucune promotion trouvée!")
            print("   → Exécutez: python init_promotions.py")
            return False

        print("\nPromotions actives:")
        for promo in Promotion.objects.filter(is_active=True).order_by('name'):
            print(f"  - {promo.name}: {promo.description}")

        return True

    except Exception as e:
        print(f"❌ Erreur lors de la vérification des promotions: {e}")
        return False

def check_api_endpoint():
    """Vérifie que l'endpoint API est configuré"""
    print("\n=== Vérification de la configuration API ===\n")

    # Vérifier les URLs
    from django.urls import get_resolver
    from django.urls.resolvers import URLPattern, URLResolver

    def get_all_urls(urlpatterns, prefix=''):
        urls = []
        for pattern in urlpatterns:
            if isinstance(pattern, URLResolver):
                urls += get_all_urls(pattern.url_patterns, prefix + str(pattern.pattern))
            elif isinstance(pattern, URLPattern):
                urls.append(prefix + str(pattern.pattern))
        return urls

    resolver = get_resolver()
    all_urls = get_all_urls(resolver.url_patterns)

    # Chercher l'endpoint promotions
    promotions_urls = [url for url in all_urls if 'promotion' in url.lower()]

    if promotions_urls:
        print("✅ Endpoint(s) promotions trouvé(s):")
        for url in promotions_urls:
            print(f"   - {url}")
    else:
        print("❌ Aucun endpoint promotions trouvé")
        print("   → Vérifiez core/urls.py")
        return False

    return True

def check_users():
    """Vérifie quelques utilisateurs"""
    print("\n=== Vérification des utilisateurs ===\n")

    try:
        total = User.objects.count()
        with_cleartext = User.objects.exclude(cleartext_password__isnull=True).exclude(cleartext_password='').count()
        radius_activated = User.objects.filter(is_radius_activated=True).count()

        print(f"Total utilisateurs: {total}")
        print(f"Avec cleartext_password: {with_cleartext}")
        print(f"Activés RADIUS: {radius_activated}")

        return True

    except Exception as e:
        print(f"❌ Erreur lors de la vérification des utilisateurs: {e}")
        return False

def main():
    print("=" * 60)
    print("DIAGNOSTIC DU SYSTÈME PORTAIL CAPTIF")
    print("=" * 60 + "\n")

    checks = [
        ("Migrations", check_migrations),
        ("Promotions", check_promotions),
        ("API Endpoint", check_api_endpoint),
        ("Utilisateurs", check_users),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Erreur lors de la vérification '{name}': {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Résumé final
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60 + "\n")

    for name, result in results:
        status = "✅ OK" if result else "❌ ÉCHEC"
        print(f"{name}: {status}")

    all_ok = all(result for _, result in results)

    if all_ok:
        print("\n🎉 Tous les tests sont passés!")
    else:
        print("\n⚠️  Certains tests ont échoué. Consultez les messages ci-dessus.")
        print("\nActions recommandées:")
        print("1. Appliquer les migrations: python manage.py migrate")
        print("2. Initialiser les promotions: python init_promotions.py")
        print("3. Redémarrer le serveur Django")

if __name__ == '__main__':
    main()
