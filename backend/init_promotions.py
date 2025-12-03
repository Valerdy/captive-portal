#!/usr/bin/env python
"""
Script pour initialiser les promotions dans la base de données
Usage: python init_promotions.py
"""
import os
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Promotion

def init_promotions():
    """Initialise les promotions par défaut"""
    promotions_data = [
        {'name': 'L1', 'description': 'Licence 1ère année'},
        {'name': 'L2', 'description': 'Licence 2ème année'},
        {'name': 'L3', 'description': 'Licence 3ème année'},
        {'name': 'M1', 'description': 'Master 1ère année'},
        {'name': 'M2', 'description': 'Master 2ème année'},
        {'name': 'ING1', 'description': 'Ingénieur 1ère année'},
        {'name': 'ING2', 'description': 'Ingénieur 2ème année'},
        {'name': 'ING3', 'description': 'Ingénieur 3ème année'},
        {'name': 'ING4', 'description': 'Ingénieur 4ème année'},
        {'name': 'ING5', 'description': 'Ingénieur 5ème année'},
        {'name': 'PREPA1', 'description': 'Prépa 1ère année'},
        {'name': 'PREPA2', 'description': 'Prépa 2ème année'},
        {'name': 'DOCTORAT', 'description': 'Doctorat'},
    ]

    print("=== Initialisation des promotions ===\n")

    created_count = 0
    existing_count = 0

    for promo_data in promotions_data:
        promo, created = Promotion.objects.get_or_create(
            name=promo_data['name'],
            defaults={
                'description': promo_data['description'],
                'is_active': True
            }
        )

        if created:
            created_count += 1
            print(f"✅ Créé: {promo.name} - {promo.description}")
        else:
            existing_count += 1
            print(f"ℹ️  Existe déjà: {promo.name} - {promo.description}")

    print(f"\n=== Résumé ===")
    print(f"Promotions créées: {created_count}")
    print(f"Promotions existantes: {existing_count}")
    print(f"Total: {Promotion.objects.count()}")

    print("\n=== Liste des promotions actives ===")
    active_promotions = Promotion.objects.filter(is_active=True).order_by('name')
    for promo in active_promotions:
        print(f"  - {promo.name}: {promo.description}")

    return created_count, existing_count

if __name__ == '__main__':
    try:
        created, existing = init_promotions()
        print("\n✅ Initialisation terminée avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
