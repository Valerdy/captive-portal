#!/usr/bin/env python
"""
Script de débogage pour tester l'inscription
"""
import os
import sys
import django

# Configuration Django
sys.path.insert(0, '/home/user/captive-portal/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.serializers import UserSerializer
from rest_framework.test import APIClient
import json

# Test avec le client API
client = APIClient()

# Données de test (avec mot de passe FAIBLE pour voir si c'est le problème)
test_data_weak = {
    "username": "testuser3",
    "email": "test3@example.com",
    "password": "test123",
    "password2": "test123",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+237600000003"
}

print("=" * 70)
print("TEST 1: Mot de passe FAIBLE")
print("=" * 70)
response = client.post('/api/core/auth/register/', test_data_weak, format='json')
print(f"Status: {response.status_code}")
print(f"Réponse: {json.dumps(response.data, indent=2, ensure_ascii=False)}")
print()

# Test avec mot de passe FORT
test_data_strong = {
    "username": "testuser4",
    "email": "test4@example.com",
    "password": "TestPassword123!Strong",
    "password2": "TestPassword123!Strong",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+237600000004"
}

print("=" * 70)
print("TEST 2: Mot de passe FORT")
print("=" * 70)
response = client.post('/api/core/auth/register/', test_data_strong, format='json')
print(f"Status: {response.status_code}")
print(f"Réponse: {json.dumps(response.data, indent=2, ensure_ascii=False)}")
print()

# Test avec champs vides
test_data_empty = {
    "username": "",
    "email": "",
    "password": "",
    "password2": "",
    "first_name": "",
    "last_name": "",
    "phone_number": ""
}

print("=" * 70)
print("TEST 3: Champs VIDES")
print("=" * 70)
response = client.post('/api/core/auth/register/', test_data_empty, format='json')
print(f"Status: {response.status_code}")
print(f"Réponse: {json.dumps(response.data, indent=2, ensure_ascii=False)}")
