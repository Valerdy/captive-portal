#!/usr/bin/env python
"""
Script de test automatisé pour l'API Captive Portal
Usage: python test_api.py
"""
import requests
import json
from typing import Dict, Any, Optional


class CaptivePortalAPI:
    """Client pour tester l'API Captive Portal"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def _headers(self, auth: bool = True) -> Dict[str, str]:
        """Générer les headers HTTP"""
        headers = {"Content-Type": "application/json"}
        if auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _print_response(self, name: str, response: requests.Response):
        """Afficher la réponse de manière formatée"""
        print(f"\n{'='*60}")
        print(f"Test: {name}")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        try:
            data = response.json()
            print(f"Response:\n{json.dumps(data, indent=2)}")
        except:
            print(f"Response: {response.text}")

    # Authentification
    def register(self, username: str, password: str, **kwargs) -> Dict[str, Any]:
        """Inscription d'un nouvel utilisateur"""
        url = f"{self.base_url}/api/core/auth/register/"
        data = {
            "username": username,
            "password": password,
            "email": kwargs.get("email", f"{username}@example.com"),
            **kwargs
        }
        response = requests.post(url, json=data, headers=self._headers(auth=False))
        self._print_response(f"Register: {username}", response)

        if response.status_code == 201:
            result = response.json()
            self.access_token = result["tokens"]["access"]
            self.refresh_token = result["tokens"]["refresh"]

        return response.json() if response.ok else {}

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Connexion utilisateur"""
        url = f"{self.base_url}/api/core/auth/login/"
        data = {"username": username, "password": password}
        response = requests.post(url, json=data, headers=self._headers(auth=False))
        self._print_response(f"Login: {username}", response)

        if response.status_code == 200:
            result = response.json()
            self.access_token = result["tokens"]["access"]
            self.refresh_token = result["tokens"]["refresh"]

        return response.json() if response.ok else {}

    def get_profile(self) -> Dict[str, Any]:
        """Obtenir le profil utilisateur"""
        url = f"{self.base_url}/api/core/auth/profile/"
        response = requests.get(url, headers=self._headers())
        self._print_response("Get Profile", response)
        return response.json() if response.ok else {}

    def update_profile(self, **kwargs) -> Dict[str, Any]:
        """Mettre à jour le profil"""
        url = f"{self.base_url}/api/core/auth/profile/update/"
        response = requests.patch(url, json=kwargs, headers=self._headers())
        self._print_response("Update Profile", response)
        return response.json() if response.ok else {}

    # Users
    def list_users(self) -> Dict[str, Any]:
        """Lister les utilisateurs"""
        url = f"{self.base_url}/api/core/users/"
        response = requests.get(url, headers=self._headers())
        self._print_response("List Users", response)
        return response.json() if response.ok else {}

    def get_current_user(self) -> Dict[str, Any]:
        """Obtenir l'utilisateur actuel"""
        url = f"{self.base_url}/api/core/users/me/"
        response = requests.get(url, headers=self._headers())
        self._print_response("Get Current User", response)
        return response.json() if response.ok else {}

    # Devices
    def list_devices(self) -> Dict[str, Any]:
        """Lister les devices"""
        url = f"{self.base_url}/api/core/devices/"
        response = requests.get(url, headers=self._headers())
        self._print_response("List Devices", response)
        return response.json() if response.ok else {}

    def list_active_devices(self) -> Dict[str, Any]:
        """Lister les devices actifs"""
        url = f"{self.base_url}/api/core/devices/active/"
        response = requests.get(url, headers=self._headers())
        self._print_response("List Active Devices", response)
        return response.json() if response.ok else {}

    def create_device(self, mac_address: str, device_type: str, **kwargs) -> Dict[str, Any]:
        """Créer un nouveau device"""
        url = f"{self.base_url}/api/core/devices/"
        data = {
            "mac_address": mac_address,
            "device_type": device_type,
            **kwargs
        }
        response = requests.post(url, json=data, headers=self._headers())
        self._print_response(f"Create Device: {mac_address}", response)
        return response.json() if response.ok else {}

    # Sessions
    def list_sessions(self) -> Dict[str, Any]:
        """Lister les sessions"""
        url = f"{self.base_url}/api/core/sessions/"
        response = requests.get(url, headers=self._headers())
        self._print_response("List Sessions", response)
        return response.json() if response.ok else {}

    def list_active_sessions(self) -> Dict[str, Any]:
        """Lister les sessions actives"""
        url = f"{self.base_url}/api/core/sessions/active/"
        response = requests.get(url, headers=self._headers())
        self._print_response("List Active Sessions", response)
        return response.json() if response.ok else {}

    def get_session_statistics(self) -> Dict[str, Any]:
        """Obtenir les statistiques de session"""
        url = f"{self.base_url}/api/core/sessions/statistics/"
        response = requests.get(url, headers=self._headers())
        self._print_response("Session Statistics", response)
        return response.json() if response.ok else {}

    # Vouchers
    def list_vouchers(self) -> Dict[str, Any]:
        """Lister les vouchers"""
        url = f"{self.base_url}/api/core/vouchers/"
        response = requests.get(url, headers=self._headers())
        self._print_response("List Vouchers", response)
        return response.json() if response.ok else {}

    def list_active_vouchers(self) -> Dict[str, Any]:
        """Lister les vouchers actifs"""
        url = f"{self.base_url}/api/core/vouchers/active/"
        response = requests.get(url, headers=self._headers())
        self._print_response("List Active Vouchers", response)
        return response.json() if response.ok else {}

    def validate_voucher(self, code: str) -> Dict[str, Any]:
        """Valider un code voucher"""
        url = f"{self.base_url}/api/core/vouchers/validate/"
        response = requests.post(
            url,
            json={"code": code},
            headers=self._headers(auth=False)
        )
        self._print_response(f"Validate Voucher: {code}", response)
        return response.json() if response.ok else {}

    def redeem_voucher(self, code: str) -> Dict[str, Any]:
        """Utiliser un code voucher"""
        url = f"{self.base_url}/api/core/vouchers/redeem/"
        response = requests.post(url, json={"code": code}, headers=self._headers())
        self._print_response(f"Redeem Voucher: {code}", response)
        return response.json() if response.ok else {}

    # Mikrotik
    def list_routers(self) -> Dict[str, Any]:
        """Lister les routeurs Mikrotik"""
        url = f"{self.base_url}/api/mikrotik/routers/"
        response = requests.get(url, headers=self._headers())
        self._print_response("List Mikrotik Routers", response)
        return response.json() if response.ok else {}

    def test_router_connection(self, router_id: int) -> Dict[str, Any]:
        """Tester la connexion à un routeur"""
        url = f"{self.base_url}/api/mikrotik/routers/{router_id}/test_connection/"
        response = requests.post(url, headers=self._headers())
        self._print_response(f"Test Router Connection: {router_id}", response)
        return response.json() if response.ok else {}

    def list_mikrotik_logs(self, level: Optional[str] = None) -> Dict[str, Any]:
        """Lister les logs Mikrotik"""
        url = f"{self.base_url}/api/mikrotik/logs/"
        if level:
            url += f"?level={level}"
        response = requests.get(url, headers=self._headers())
        self._print_response(f"List Mikrotik Logs (level={level})", response)
        return response.json() if response.ok else {}

    # RADIUS
    def list_radius_servers(self) -> Dict[str, Any]:
        """Lister les serveurs RADIUS"""
        url = f"{self.base_url}/api/radius/servers/"
        response = requests.get(url, headers=self._headers())
        self._print_response("List RADIUS Servers", response)
        return response.json() if response.ok else {}

    def list_radius_auth_logs(self) -> Dict[str, Any]:
        """Lister les logs d'authentification RADIUS"""
        url = f"{self.base_url}/api/radius/auth-logs/"
        response = requests.get(url, headers=self._headers())
        self._print_response("List RADIUS Auth Logs", response)
        return response.json() if response.ok else {}

    def get_radius_statistics(self) -> Dict[str, Any]:
        """Obtenir les statistiques RADIUS"""
        url = f"{self.base_url}/api/radius/accounting/statistics/"
        response = requests.get(url, headers=self._headers())
        self._print_response("RADIUS Statistics", response)
        return response.json() if response.ok else {}


def run_tests():
    """Exécuter tous les tests"""
    print("\n" + "="*60)
    print(" 🚀 Tests de l'API Captive Portal")
    print("="*60)

    api = CaptivePortalAPI()

    print("\n📝 Section 1: Tests d'Authentification")
    print("-" * 60)

    # Test login avec un utilisateur existant
    api.login("john.doe", "password123")

    # Test get profile
    api.get_profile()

    # Test update profile
    api.update_profile(phone_number="+9999999999")

    # Test get current user
    api.get_current_user()

    print("\n👥 Section 2: Tests des Users")
    print("-" * 60)
    api.list_users()

    print("\n📱 Section 3: Tests des Devices")
    print("-" * 60)
    api.list_devices()
    api.list_active_devices()

    print("\n🔗 Section 4: Tests des Sessions")
    print("-" * 60)
    api.list_sessions()
    api.list_active_sessions()
    api.get_session_statistics()

    print("\n🎟️ Section 5: Tests des Vouchers")
    print("-" * 60)
    api.list_vouchers()
    api.list_active_vouchers()
    api.validate_voucher("WELCOME2024")

    print("\n🌐 Section 6: Tests Mikrotik")
    print("-" * 60)

    # Se connecter en tant qu'admin pour les tests Mikrotik
    api.login("admin", "admin123")
    api.list_routers()
    api.list_mikrotik_logs()

    print("\n🔐 Section 7: Tests RADIUS")
    print("-" * 60)
    api.list_radius_servers()
    api.list_radius_auth_logs()
    api.get_radius_statistics()

    print("\n" + "="*60)
    print("✅ Tests terminés!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        run_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ Erreur: Impossible de se connecter au serveur.")
        print("Assurez-vous que le serveur Django est en cours d'exécution:")
        print("  cd /home/user/captive-portal/backend")
        print("  source venv/bin/activate")
        print("  python manage.py runserver\n")
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}\n")
