#!/usr/bin/env python
"""
Script de test pour l'inscription utilisateur avec création FreeRADIUS
"""
import os
import sys
import django
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_register():
    """Test l'endpoint d'inscription"""
    print("=" * 70)
    print("TEST D'INSCRIPTION UTILISATEUR + FREERADIUS")
    print("=" * 70)
    print()

    # Supprimer l'utilisateur test s'il existe déjà
    User.objects.filter(username='testuser').delete()

    # Créer un client de test
    client = Client()

    # Données de test
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'password2': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '+237600000000'
    }

    print("📤 Envoi de la requête d'inscription...")
    print(f"   URL: /api/core/auth/register/")
    print(f"   Données: {json.dumps(data, indent=2)}")
    print()

    # Envoyer la requête
    response = client.post(
        '/api/core/auth/register/',
        data=json.dumps(data),
        content_type='application/json'
    )

    print(f"📥 Réponse reçue:")
    print(f"   Status: {response.status_code}")
    print()

    if response.status_code == 201:
        print("✅ INSCRIPTION RÉUSSIE!")
        print()
        response_data = response.json()
        print("Données de réponse:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        print()

        # Vérifier dans FreeRADIUS
        from radius.models import RadCheck, RadReply, RadUserGroup

        print("🔍 Vérification dans FreeRADIUS:")

        radcheck = RadCheck.objects.filter(username='testuser')
        print(f"   radcheck: {radcheck.count()} entrée(s)")
        for entry in radcheck:
            print(f"      - {entry.attribute} {entry.op} {entry.value}")

        radreply = RadReply.objects.filter(username='testuser')
        print(f"   radreply: {radreply.count()} entrée(s)")
        for entry in radreply:
            print(f"      - {entry.attribute} {entry.op} {entry.value}")

        radusergroup = RadUserGroup.objects.filter(username='testuser')
        print(f"   radusergroup: {radusergroup.count()} entrée(s)")
        for entry in radusergroup:
            print(f"      - {entry.username} -> {entry.groupname}")

        print()
        print("✅ L'utilisateur peut maintenant se connecter au portail captif Mikrotik!")
        print(f"   Username: {data['username']}")
        print(f"   Password: {data['password']}")

    else:
        print("❌ ERREUR D'INSCRIPTION")
        print()
        try:
            error_data = response.json()
            print("Détails de l'erreur:")
            print(json.dumps(error_data, indent=2, ensure_ascii=False))
        except:
            print(f"Contenu brut: {response.content.decode()}")

    print()
    print("=" * 70)


if __name__ == '__main__':
    try:
        test_register()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
