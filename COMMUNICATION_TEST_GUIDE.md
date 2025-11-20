# 🔗 Guide de Vérification de la Communication Backend ↔ Frontend

Ce guide vous explique comment vérifier que votre backend Django et votre frontend Vue.js communiquent correctement.

---

## 📋 Table des Matières

1. [Vérification Rapide (5 minutes)](#vérification-rapide)
2. [Configuration Actuelle](#configuration-actuelle)
3. [Tests Automatisés](#tests-automatisés)
4. [Tests Manuels](#tests-manuels)
5. [Résolution de Problèmes](#résolution-de-problèmes)
6. [Tests depuis le Navigateur](#tests-depuis-le-navigateur)

---

## 🚀 Vérification Rapide

### Étape 1: Vérifier que le Backend fonctionne

```bash
# Se placer dans le dossier backend
cd backend

# Activer l'environnement virtuel
source venv/bin/activate

# Démarrer le serveur Django
python manage.py runserver 0.0.0.0:8000
```

**Résultat attendu:**
```
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```

**✅ Test rapide:** Ouvrez http://localhost:8000/admin dans votre navigateur. Vous devriez voir la page de connexion Django admin.

---

### Étape 2: Vérifier que le Frontend fonctionne

**Ouvrez un nouveau terminal** (gardez le backend qui tourne)

```bash
# Se placer dans le dossier frontend
cd frontend/portail-captif

# Installer les dépendances (si ce n'est pas déjà fait)
npm install

# Démarrer le serveur de développement
npm run dev
```

**Résultat attendu:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

**✅ Test rapide:** Ouvrez http://localhost:5173 dans votre navigateur. Vous devriez voir la page d'accueil du portail captif.

---

### Étape 3: Test de Communication

**Gardez les deux serveurs qui tournent**, puis dans un troisième terminal:

```bash
# À la racine du projet
cd /home/user/captive-portal

# Rendre le script exécutable
chmod +x test_communication.py

# Exécuter le script de test
python3 test_communication.py
```

**Résultat attendu:**
```
✅ Backend accessible à http://localhost:8000
✅ CORS Origin: http://localhost:5173
✅ Inscription réussie
✅ Tokens JWT reçus
✅ Requête authentifiée réussie

🎉 Tous les tests sont passés! (4/4)
✅ Le backend et le frontend peuvent communiquer correctement
```

---

## ⚙️ Configuration Actuelle

### Configuration Backend

**Fichier:** `backend/.env`

```env
# URL du backend
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# CORS - Origines autorisées pour le frontend
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000

# Base de données MySQL
DB_ENGINE=django.db.backends.mysql
DB_NAME=radius
DB_USER=radius
DB_PASSWORD=radpass
DB_HOST=localhost
DB_PORT=3306
```

**Points importants:**
- Le backend écoute sur le port **8000**
- CORS autorise les requêtes depuis **localhost:5173** (frontend)
- MySQL est configuré pour FreeRADIUS

---

### Configuration Frontend

**Fichier:** `frontend/portail-captif/.env`

```env
# URL de l'API Backend
VITE_API_URL=http://localhost:8000
```

**Fichier:** `frontend/portail-captif/src/services/api.ts`

```typescript
// Configuration de l'URL de base de l'API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Instance Axios avec intercepteurs JWT
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
})
```

**Points importants:**
- Le frontend fait des requêtes vers **http://localhost:8000**
- Les tokens JWT sont automatiquement ajoutés aux requêtes
- Le refresh token est géré automatiquement en cas de 401

---

## 🧪 Tests Automatisés

### Script de Test Complet

Le script `test_communication.py` effectue les tests suivants:

1. **Backend Accessible** - Vérifie que le serveur Django répond
2. **Configuration CORS** - Vérifie que les headers CORS sont corrects
3. **Endpoints API** - Teste les principaux endpoints (auth, sessions, devices, etc.)
4. **Authentification** - Teste le flux complet d'inscription et de connexion
5. **Tokens JWT** - Vérifie que les tokens sont bien reçus et fonctionnels

**Utilisation:**

```bash
# Installer les dépendances (si nécessaire)
pip install requests

# Exécuter les tests
python3 test_communication.py
```

**Interprétation des résultats:**

- ✅ **PASSÉ** - Le test a réussi
- ❌ **ÉCHOUÉ** - Le test a échoué, voir les détails
- ⚠️ **ATTENTION** - Test partiellement réussi

---

## 🔍 Tests Manuels

### Test 1: Vérifier le Backend avec curl

```bash
# Test de santé du backend
curl http://localhost:8000/admin/

# Test de l'endpoint d'inscription
curl -X POST http://localhost:8000/api/core/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Résultat attendu:** Vous devriez recevoir un JSON avec les tokens:
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJh...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJh..."
}
```

---

### Test 2: Vérifier CORS avec curl

```bash
# Test preflight CORS
curl -X OPTIONS http://localhost:8000/api/core/auth/register/ \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,authorization" \
  -v
```

**Recherchez dans la réponse:**
```
< Access-Control-Allow-Origin: http://localhost:5173
< Access-Control-Allow-Methods: POST, OPTIONS
< Access-Control-Allow-Headers: authorization, content-type
```

---

### Test 3: Tester les Endpoints Protégés

```bash
# 1. S'inscrire et récupérer le token
TOKEN=$(curl -s -X POST http://localhost:8000/api/core/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "email": "test2@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }' | jq -r '.access')

# 2. Utiliser le token pour accéder au profil
curl http://localhost:8000/api/core/profile/ \
  -H "Authorization: Bearer $TOKEN"
```

**Résultat attendu:** Vos informations de profil en JSON.

---

## 🌐 Tests depuis le Navigateur

### Test avec la Console Développeur

1. **Ouvrez le frontend** dans Chrome/Firefox: http://localhost:5173

2. **Ouvrez la Console Développeur** (F12)

3. **Collez ce code** pour tester l'API:

```javascript
// Test d'inscription
fetch('http://localhost:8000/api/core/auth/register/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'browsertest',
    email: 'browser@test.com',
    password: 'TestPass123!',
    password2: 'TestPass123!',
    first_name: 'Browser',
    last_name: 'Test'
  })
})
.then(res => res.json())
.then(data => {
  console.log('✅ Inscription réussie:', data);

  // Tester une requête authentifiée
  return fetch('http://localhost:8000/api/core/profile/', {
    headers: {
      'Authorization': `Bearer ${data.access}`
    }
  });
})
.then(res => res.json())
.then(profile => {
  console.log('✅ Profil récupéré:', profile);
})
.catch(err => {
  console.error('❌ Erreur:', err);
});
```

**Résultat attendu dans la console:**
```
✅ Inscription réussie: {user: {...}, access: "...", refresh: "..."}
✅ Profil récupéré: {id: 1, username: "browsertest", ...}
```

---

### Test avec l'Onglet Network

1. **Ouvrez l'onglet Network** (F12 → Network)

2. **Créez un compte** depuis l'interface (bouton "Créer un compte")

3. **Vérifiez les requêtes:**
   - Une requête `POST` vers `/api/core/auth/register/`
   - **Status:** 201 Created
   - **Response:** Contient les tokens JWT
   - **Headers:** Vérifiez `Access-Control-Allow-Origin`

4. **Vérifiez les requêtes suivantes** (navigation dans le dashboard):
   - Chaque requête doit avoir le header `Authorization: Bearer ...`
   - **Status:** 200 OK pour les requêtes réussies
   - **Status:** 401 Unauthorized si le token est invalide

---

## 🐛 Résolution de Problèmes

### Problème 1: CORS Error dans le navigateur

**Symptôme:**
```
Access to fetch at 'http://localhost:8000/api/...' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

**Solutions:**

1. **Vérifiez que le backend est démarré**
   ```bash
   curl http://localhost:8000/admin/
   ```

2. **Vérifiez la configuration CORS dans backend/.env**
   ```env
   CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
   ```

3. **Redémarrez le backend après modification du .env**
   ```bash
   # Arrêtez avec Ctrl+C, puis relancez
   python manage.py runserver
   ```

4. **Vérifiez que corsheaders est installé**
   ```bash
   pip list | grep django-cors-headers
   ```
   Si absent:
   ```bash
   pip install django-cors-headers
   ```

---

### Problème 2: Backend ne démarre pas

**Symptôme:**
```
django.db.utils.OperationalError: (2003, "Can't connect to MySQL server...")
```

**Solutions:**

1. **Vérifiez que MySQL est démarré**
   ```bash
   sudo systemctl status mysql
   # ou
   sudo service mysql status
   ```

2. **Testez la connexion MySQL**
   ```bash
   python backend/test_mysql_connection.py
   ```

3. **Si MySQL n'est pas disponible, utilisez SQLite temporairement**

   Modifiez `backend/.env`:
   ```env
   DB_ENGINE=django.db.backends.sqlite3
   DB_NAME=db.sqlite3
   ```

4. **Appliquez les migrations**
   ```bash
   cd backend
   python manage.py migrate
   ```

---

### Problème 3: Frontend ne trouve pas l'API

**Symptôme:**
```
Network Error
Error: connect ECONNREFUSED 127.0.0.1:8000
```

**Solutions:**

1. **Vérifiez que VITE_API_URL est correct**

   Fichier `frontend/portail-captif/.env`:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

2. **Redémarrez le frontend après modification**
   ```bash
   # Arrêtez avec Ctrl+C
   npm run dev
   ```

3. **Vérifiez que le backend écoute sur 0.0.0.0:8000**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

4. **Testez la connexion depuis le serveur frontend**
   ```bash
   curl http://localhost:8000/admin/
   ```

---

### Problème 4: Token JWT non accepté

**Symptôme:**
```
401 Unauthorized
{"detail": "Given token not valid for any token type"}
```

**Solutions:**

1. **Vérifiez que le token n'a pas expiré**

   Par défaut, les tokens expirent après 60 minutes. Reconnectez-vous.

2. **Vérifiez le format du token dans les requêtes**

   Le header doit être:
   ```
   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJh...
   ```

3. **Vérifiez la configuration JWT dans backend/.env**
   ```env
   JWT_ACCESS_TOKEN_LIFETIME=60
   JWT_REFRESH_TOKEN_LIFETIME=1440
   ```

4. **Nettoyez le localStorage du navigateur**

   Console développeur:
   ```javascript
   localStorage.clear()
   ```
   Puis reconnectez-vous.

---

### Problème 5: Requêtes lentes

**Symptôme:**
Les requêtes prennent plus de 5 secondes à répondre.

**Solutions:**

1. **Vérifiez les logs du backend** pour voir les requêtes SQL

   Les logs Django affichent chaque requête SQL en mode DEBUG.

2. **Optimisez les requêtes dans views.py**

   Utilisez `select_related()` et `prefetch_related()` pour éviter le N+1 problem.

3. **Activez la mise en cache**

   Ajoutez Redis pour mettre en cache les requêtes fréquentes.

4. **Vérifiez la connexion réseau**
   ```bash
   ping localhost
   ```

---

## 📊 Checklist de Vérification

Utilisez cette checklist pour vérifier que tout fonctionne:

### Backend ✅

- [ ] Le serveur Django démarre sans erreur
- [ ] L'admin Django est accessible: http://localhost:8000/admin
- [ ] La base de données est connectée (MySQL ou SQLite)
- [ ] Les migrations sont appliquées: `python manage.py migrate`
- [ ] Un superuser est créé: `python manage.py createsuperuser`
- [ ] CORS est configuré avec `http://localhost:5173`
- [ ] Les endpoints API répondent (test avec curl ou script)

### Frontend ✅

- [ ] Le serveur Vite démarre sans erreur
- [ ] La page d'accueil s'affiche: http://localhost:5173
- [ ] Le fichier `.env` contient `VITE_API_URL=http://localhost:8000`
- [ ] Les dépendances sont installées: `npm install`
- [ ] Aucune erreur CORS dans la console navigateur
- [ ] L'inscription fonctionne depuis l'interface
- [ ] La connexion fonctionne depuis l'interface
- [ ] Le dashboard affiche les données après connexion

### Communication ✅

- [ ] Le script `test_communication.py` passe tous les tests
- [ ] Les requêtes API apparaissent dans l'onglet Network
- [ ] Les tokens JWT sont stockés dans localStorage
- [ ] Les requêtes authentifiées incluent le header Authorization
- [ ] Le refresh token fonctionne automatiquement (pas de déconnexion abrupte)

---

## 🎯 Tests de Bout en Bout

### Scénario 1: Nouvel Utilisateur

1. **Ouvrir le frontend**: http://localhost:5173
2. **Cliquer sur "Créer un compte"**
3. **Remplir le formulaire d'inscription**
4. **Soumettre** → Vous devriez être connecté automatiquement
5. **Vérifier** que le dashboard s'affiche avec vos informations

### Scénario 2: Utilisateur Existant

1. **Cliquer sur "Connexion"** (si vous avez été déconnecté)
2. **Entrer vos identifiants**
3. **Se connecter** → Dashboard s'affiche
4. **Naviguer** entre Sessions, Appareils, Vouchers, Profil
5. **Vérifier** que les données se chargent correctement

### Scénario 3: Administrateur

1. **Cliquer sur "Admin"** en haut à droite
2. **Entrer les identifiants admin** (superuser)
3. **Accéder au dashboard admin**
4. **Vérifier** que toutes les sections admin sont accessibles:
   - Dashboard
   - Gestion des utilisateurs
   - Monitoring
   - Sites bloqués
   - Quotas

---

## 🔧 Configuration Avancée

### Accès depuis une autre machine sur le réseau

**Backend:**

1. Modifier `backend/.env`:
   ```env
   ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,192.168.x.x
   CORS_ALLOWED_ORIGINS=http://localhost:5173,http://192.168.x.x:5173
   ```

2. Démarrer sur toutes les interfaces:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

**Frontend:**

1. Modifier `frontend/portail-captif/.env`:
   ```env
   VITE_API_URL=http://192.168.x.x:8000
   ```

2. Démarrer avec --host:
   ```bash
   npm run dev -- --host
   ```

3. Accéder depuis l'autre machine:
   ```
   http://192.168.x.x:5173
   ```

---

## 📚 Ressources

- **Documentation Django CORS**: https://github.com/adamchainz/django-cors-headers
- **Documentation Django REST Framework**: https://www.django-rest-framework.org/
- **Documentation JWT**: https://django-rest-framework-simplejwt.readthedocs.io/
- **Documentation Axios**: https://axios-http.com/docs/intro
- **Documentation Vite**: https://vitejs.dev/guide/env-and-mode.html

---

## ✅ Conclusion

Si tous les tests passent, votre backend et votre frontend communiquent correctement ! 🎉

Vous pouvez maintenant:
1. Connecter le backend à votre serveur FreeRADIUS (voir `MYSQL_CONFIG.md`)
2. Déployer en production (voir `DEPLOYMENT_GUIDE.md`)
3. Personnaliser les fonctionnalités selon vos besoins

**En cas de problème persistant**, consultez les logs:
- **Backend**: Les logs s'affichent dans le terminal où Django tourne
- **Frontend**: Ouvrez la console développeur (F12) dans le navigateur
