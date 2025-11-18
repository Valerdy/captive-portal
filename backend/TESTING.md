# Guide de Test - Backend Captive Portal

Ce guide vous montre comment tester tous les endpoints du backend.

## Prérequis

1. Le serveur Django doit être en cours d'exécution :
```bash
cd /home/user/captive-portal/backend
source venv/bin/activate
python manage.py runserver
```

2. Les données de test doivent être chargées :
```bash
python create_test_data.py
```

## Variables d'environnement pour les tests

```bash
export API_URL="http://localhost:8000"
export ACCESS_TOKEN=""  # Sera rempli après login
```

## 1. Tests d'Authentification

### 1.1 Inscription d'un nouvel utilisateur

```bash
curl -X POST http://localhost:8000/api/core/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+1234567890"
  }'
```

**Réponse attendue** :
```json
{
  "user": {
    "id": 5,
    "username": "testuser",
    "email": "testuser@example.com",
    "first_name": "Test",
    "last_name": "User"
  },
  "tokens": {
    "refresh": "eyJ0eXAi...",
    "access": "eyJ0eXAi..."
  },
  "message": "User registered successfully"
}
```

### 1.2 Connexion (Login)

```bash
curl -X POST http://localhost:8000/api/core/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "password123"
  }'
```

**Sauvegardez le token d'accès** :
```bash
export ACCESS_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 1.3 Obtenir le profil utilisateur

```bash
curl -X GET http://localhost:8000/api/core/auth/profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 1.4 Mettre à jour le profil

```bash
curl -X PATCH http://localhost:8000/api/core/auth/profile/update/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jean",
    "last_name": "Dupont"
  }'
```

### 1.5 Rafraîchir le token

```bash
curl -X POST http://localhost:8000/api/core/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "VOTRE_REFRESH_TOKEN"
  }'
```

### 1.6 Déconnexion (Logout)

```bash
curl -X POST http://localhost:8000/api/core/auth/logout/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "VOTRE_REFRESH_TOKEN"
  }'
```

## 2. Tests des Utilisateurs

### 2.1 Lister tous les utilisateurs (Admin seulement)

```bash
curl -X GET http://localhost:8000/api/core/users/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 2.2 Obtenir l'utilisateur actuel

```bash
curl -X GET http://localhost:8000/api/core/users/me/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 2.3 Obtenir les devices d'un utilisateur

```bash
curl -X GET "http://localhost:8000/api/core/users/1/devices/" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 2.4 Obtenir les sessions d'un utilisateur

```bash
curl -X GET "http://localhost:8000/api/core/users/1/sessions/" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## 3. Tests des Devices

### 3.1 Lister tous les devices

```bash
curl -X GET http://localhost:8000/api/core/devices/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 3.2 Lister les devices actifs

```bash
curl -X GET http://localhost:8000/api/core/devices/active/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 3.3 Créer un nouveau device

```bash
curl -X POST http://localhost:8000/api/core/devices/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "AA:BB:CC:DD:EE:11",
    "device_type": "mobile",
    "hostname": "iPhone-Test",
    "user_agent": "Mozilla/5.0 (iPhone)"
  }'
```

### 3.4 Désactiver un device

```bash
curl -X POST http://localhost:8000/api/core/devices/1/deactivate/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## 4. Tests des Sessions

### 4.1 Lister toutes les sessions

```bash
curl -X GET http://localhost:8000/api/core/sessions/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 4.2 Lister les sessions actives

```bash
curl -X GET http://localhost:8000/api/core/sessions/active/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 4.3 Obtenir les statistiques de session

```bash
curl -X GET http://localhost:8000/api/core/sessions/statistics/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Réponse attendue** :
```json
{
  "total_sessions": 2,
  "active_sessions": 1,
  "total_data_transferred": 8798208,
  "average_session_duration_seconds": 3600.0,
  "average_session_duration_minutes": 60.0
}
```

### 4.4 Terminer une session

```bash
curl -X POST http://localhost:8000/api/core/sessions/1/terminate/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## 5. Tests des Vouchers

### 5.1 Lister tous les vouchers (Admin)

```bash
curl -X GET http://localhost:8000/api/core/vouchers/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 5.2 Lister les vouchers actifs

```bash
curl -X GET http://localhost:8000/api/core/vouchers/active/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 5.3 Créer un nouveau voucher (Admin)

```bash
curl -X POST http://localhost:8000/api/core/vouchers/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "NEWVOUCHER2024",
    "duration": 7200,
    "max_devices": 2,
    "valid_until": "2025-12-31T23:59:59Z"
  }'
```

### 5.4 Valider un voucher (Public)

```bash
curl -X POST http://localhost:8000/api/core/vouchers/validate/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "WELCOME2024"
  }'
```

### 5.5 Utiliser un voucher

```bash
curl -X POST http://localhost:8000/api/core/vouchers/redeem/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "WELCOME2024"
  }'
```

## 6. Tests Mikrotik

### 6.1 Lister les routeurs Mikrotik

```bash
curl -X GET http://localhost:8000/api/mikrotik/routers/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 6.2 Tester la connexion à un routeur

```bash
curl -X POST http://localhost:8000/api/mikrotik/routers/1/test_connection/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 6.3 Lister les utilisateurs hotspot

```bash
curl -X GET http://localhost:8000/api/mikrotik/hotspot-users/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 6.4 Lister les connexions actives

```bash
curl -X GET http://localhost:8000/api/mikrotik/active-connections/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 6.5 Déconnecter une session

```bash
curl -X POST http://localhost:8000/api/mikrotik/active-connections/1/disconnect/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 6.6 Consulter les logs Mikrotik

```bash
curl -X GET "http://localhost:8000/api/mikrotik/logs/?level=info" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## 7. Tests RADIUS

### 7.1 Lister les serveurs RADIUS

```bash
curl -X GET http://localhost:8000/api/radius/servers/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 7.2 Consulter les logs d'authentification

```bash
curl -X GET http://localhost:8000/api/radius/auth-logs/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 7.3 Consulter les tentatives échouées

```bash
curl -X GET http://localhost:8000/api/radius/auth-logs/failed/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 7.4 Consulter l'accounting RADIUS

```bash
curl -X GET http://localhost:8000/api/radius/accounting/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 7.5 Sessions actives RADIUS

```bash
curl -X GET http://localhost:8000/api/radius/accounting/active_sessions/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 7.6 Statistiques RADIUS

```bash
curl -X GET http://localhost:8000/api/radius/accounting/statistics/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## 8. Interface Admin Django

Accédez à l'interface d'administration Django :

```
URL: http://localhost:8000/admin/
Utilisateur: admin
Mot de passe: admin123
```

## 9. Tests avec Python Requests

Voir le script `test_api.py` pour des exemples de tests automatisés.

## 10. Tests de Pagination

Tous les endpoints de liste supportent la pagination :

```bash
curl -X GET "http://localhost:8000/api/core/sessions/?page=1&page_size=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## 11. Tests de Filtrage

Exemples de filtrage :

```bash
# Filtrer les logs Mikrotik par niveau
curl -X GET "http://localhost:8000/api/mikrotik/logs/?level=error" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Filtrer les logs RADIUS par username
curl -X GET "http://localhost:8000/api/radius/auth-logs/?username=john.doe" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Filtrer l'accounting par status_type
curl -X GET "http://localhost:8000/api/radius/accounting/?status_type=start" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Résolution des Problèmes

### Erreur 401 (Unauthorized)

Votre token a expiré. Reconnectez-vous pour obtenir un nouveau token.

### Erreur 403 (Forbidden)

Vous n'avez pas les permissions nécessaires. Certains endpoints requièrent un compte admin.

### Erreur 404 (Not Found)

Vérifiez que l'URL est correcte et que l'objet existe.

### Erreur 500 (Internal Server Error)

Vérifiez les logs du serveur Django pour plus de détails :
```bash
python manage.py runserver
```

## Notes

- Les tokens JWT expirent après 60 minutes par défaut
- Les refresh tokens expirent après 24 heures
- La pagination par défaut affiche 20 éléments par page
- Tous les timestamps sont en UTC
