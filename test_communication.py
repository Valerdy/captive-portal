#!/usr/bin/env python3
"""
Script de test de communication Backend-Frontend
Vérifie que le backend Django répond correctement aux requêtes du frontend
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
TIMEOUT = 5  # secondes

# Couleurs pour l'affichage
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_section(title):
    """Affiche un titre de section"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(message):
    """Affiche un message de succès"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    """Affiche un message d'erreur"""
    print(f"{RED}❌ {message}{RESET}")

def print_warning(message):
    """Affiche un avertissement"""
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_info(message):
    """Affiche une information"""
    print(f"{BLUE}ℹ️  {message}{RESET}")

def test_backend_alive():
    """Test 1: Vérifie que le backend est accessible"""
    print_section("TEST 1: Backend Accessible")

    try:
        response = requests.get(f"{BACKEND_URL}/admin/", timeout=TIMEOUT)
        if response.status_code in [200, 302]:
            print_success(f"Backend accessible à {BACKEND_URL}")
            return True
        else:
            print_error(f"Backend répond avec le code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Impossible de se connecter à {BACKEND_URL}")
        print_info("Vérifiez que le backend est démarré: python manage.py runserver")
        return False
    except requests.exceptions.Timeout:
        print_error("Timeout lors de la connexion au backend")
        return False
    except Exception as e:
        print_error(f"Erreur inattendue: {e}")
        return False

def test_cors_headers():
    """Test 2: Vérifie la configuration CORS"""
    print_section("TEST 2: Configuration CORS")

    try:
        headers = {
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type,authorization'
        }

        # OPTIONS request (preflight)
        response = requests.options(f"{BACKEND_URL}/api/core/auth/register/",
                                   headers=headers,
                                   timeout=TIMEOUT)

        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        cors_methods = response.headers.get('Access-Control-Allow-Methods')
        cors_headers = response.headers.get('Access-Control-Allow-Headers')

        if cors_origin:
            print_success(f"CORS Origin: {cors_origin}")
        else:
            print_error("Header Access-Control-Allow-Origin absent")

        if cors_methods:
            print_success(f"CORS Methods: {cors_methods}")
        else:
            print_warning("Header Access-Control-Allow-Methods absent")

        if cors_headers:
            print_success(f"CORS Headers: {cors_headers}")
        else:
            print_warning("Header Access-Control-Allow-Headers absent")

        return bool(cors_origin)

    except Exception as e:
        print_error(f"Erreur lors du test CORS: {e}")
        return False

def test_api_endpoints():
    """Test 3: Vérifie les endpoints API principaux"""
    print_section("TEST 3: Endpoints API")

    endpoints = [
        ('/api/core/auth/register/', 'POST', 'Inscription'),
        ('/api/core/auth/login/', 'POST', 'Connexion'),
        ('/api/core/sessions/', 'GET', 'Sessions'),
        ('/api/core/devices/', 'GET', 'Appareils'),
        ('/api/core/vouchers/', 'GET', 'Vouchers'),
    ]

    results = []

    for endpoint, method, description in endpoints:
        try:
            url = f"{BACKEND_URL}{endpoint}"

            if method == 'GET':
                response = requests.get(url, timeout=TIMEOUT)
            elif method == 'POST':
                response = requests.post(url, json={}, timeout=TIMEOUT)

            # Pour les endpoints protégés, 401 est acceptable (non authentifié)
            # Pour les endpoints publics, 200 ou 400 est acceptable
            if response.status_code in [200, 201, 400, 401]:
                print_success(f"{description}: {endpoint} (HTTP {response.status_code})")
                results.append(True)
            else:
                print_error(f"{description}: {endpoint} (HTTP {response.status_code})")
                results.append(False)

        except Exception as e:
            print_error(f"{description}: {endpoint} - Erreur: {e}")
            results.append(False)

    return all(results)

def test_authentication_flow():
    """Test 4: Teste le flux d'authentification complet"""
    print_section("TEST 4: Flux d'authentification")

    # Créer un utilisateur de test
    test_username = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    test_email = f"{test_username}@test.com"
    test_password = "TestPassword123!"

    print_info(f"Création d'un utilisateur de test: {test_username}")

    try:
        # 1. Inscription
        register_data = {
            "username": test_username,
            "email": test_email,
            "password": test_password,
            "password2": test_password,
            "first_name": "Test",
            "last_name": "User"
        }

        response = requests.post(
            f"{BACKEND_URL}/api/core/auth/register/",
            json=register_data,
            timeout=TIMEOUT
        )

        if response.status_code == 201:
            print_success("Inscription réussie")
            data = response.json()

            # Vérifier la présence des tokens
            if 'access' in data and 'refresh' in data:
                print_success("Tokens JWT reçus")
                access_token = data['access']
                refresh_token = data['refresh']

                # 2. Tester une requête authentifiée
                headers = {'Authorization': f'Bearer {access_token}'}
                profile_response = requests.get(
                    f"{BACKEND_URL}/api/core/profile/",
                    headers=headers,
                    timeout=TIMEOUT
                )

                if profile_response.status_code == 200:
                    print_success("Requête authentifiée réussie (profile)")
                    profile_data = profile_response.json()
                    print_info(f"Utilisateur: {profile_data.get('username')}")
                    return True
                else:
                    print_error(f"Requête authentifiée échouée: HTTP {profile_response.status_code}")
                    return False
            else:
                print_error("Tokens JWT non reçus")
                return False
        else:
            print_error(f"Inscription échouée: HTTP {response.status_code}")
            print_info(f"Réponse: {response.text}")
            return False

    except Exception as e:
        print_error(f"Erreur lors du test d'authentification: {e}")
        return False

def test_database_connection():
    """Test 5: Vérifie la connexion à la base de données"""
    print_section("TEST 5: Connexion Base de Données")

    print_info("Ce test nécessite d'exécuter une commande Django...")
    print_info("Il sera effectué manuellement si nécessaire")

    return True

def main():
    """Fonction principale"""
    print(f"\n{BLUE}╔{'='*58}╗{RESET}")
    print(f"{BLUE}║{' '*15}TEST DE COMMUNICATION{' '*22}║{RESET}")
    print(f"{BLUE}║{' '*13}Backend ↔ Frontend{' '*25}║{RESET}")
    print(f"{BLUE}╚{'='*58}╝{RESET}")

    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"Début des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Exécuter les tests
    results = {
        "Backend accessible": test_backend_alive(),
        "Configuration CORS": test_cors_headers(),
        "Endpoints API": test_api_endpoints(),
        "Authentification": test_authentication_flow(),
    }

    # Résumé
    print_section("RÉSUMÉ")

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = f"{GREEN}✅ PASSÉ{RESET}" if result else f"{RED}❌ ÉCHOUÉ{RESET}"
        print(f"{test_name}: {status}")

    print(f"\n{BLUE}{'='*60}{RESET}")
    percentage = (passed / total) * 100

    if percentage == 100:
        print(f"{GREEN}🎉 Tous les tests sont passés! ({passed}/{total}){RESET}")
        print(f"{GREEN}✅ Le backend et le frontend peuvent communiquer correctement{RESET}")
        return 0
    elif percentage >= 75:
        print(f"{YELLOW}⚠️  La plupart des tests sont passés ({passed}/{total}){RESET}")
        print(f"{YELLOW}Vérifiez les tests échoués ci-dessus{RESET}")
        return 1
    else:
        print(f"{RED}❌ Plusieurs tests ont échoué ({passed}/{total}){RESET}")
        print(f"{RED}Vérifiez la configuration du backend et du frontend{RESET}")
        return 2

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrompu par l'utilisateur{RESET}")
        sys.exit(130)
