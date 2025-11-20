# 🌐 Portail Captif - Guide de Démarrage

Système de portail captif avec authentification, gestion de sessions et intégration FreeRADIUS/Mikrotik.

---

## 🏗️ Architecture

- **Backend:** Django 5.2.8 + Django REST Framework + JWT Authentication
- **Frontend:** Vue 3 + TypeScript + Pinia + Vite
- **Base de données:** PostgreSQL (pgAdmin)
- **Intégrations:** FreeRADIUS, Mikrotik RouterOS

---

## 📋 Prérequis

### Windows

1. **Python 3.11+**
   - https://www.python.org/downloads/

2. **Node.js 18+**
   - https://nodejs.org/

3. **PostgreSQL + pgAdmin**
   - https://www.postgresql.org/download/windows/
   - Notez le mot de passe lors de l'installation !

4. **Git** (optionnel)
   - https://git-scm.com/downloads

---

## 🚀 Démarrage Rapide (Windows)

### Étape 1: Créer la Base de Données PostgreSQL

1. **Ouvrez pgAdmin 4**
2. **Connectez-vous** au serveur PostgreSQL (avec votre mot de passe)
3. **Clic droit** sur "Databases" → **Create** → **Database**
4. **Remplissez:**
   - Name: `captive_portal_db`
   - Owner: `postgres`
   - Encoding: `UTF8`
5. **Cliquez "Save"**

✅ Base de données créée !

---

### Étape 2: Configuration Automatique du Backend

**Double-cliquez sur:** `setup_postgresql.bat`

Le script va automatiquement:
- ✅ Créer l'environnement virtuel Python
- ✅ Installer toutes les dépendances
- ✅ Configurer PostgreSQL dans `.env`
- ✅ Tester la connexion
- ✅ Appliquer les migrations
- ✅ Créer les tables dans PostgreSQL

**Le script vous demandera le mot de passe PostgreSQL.**

---

### Étape 3: Créer un Administrateur

**Double-cliquez sur:** `create_admin.bat`

Cela crée un superuser:
- **Username:** `admin`
- **Password:** `admin123`

---

### Étape 4: Démarrer le Backend

**Double-cliquez sur:** `start_with_postgresql.bat`

Ou manuellement:
```bash
cd backend
venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

✅ Backend disponible sur: **http://localhost:8000**

---

### Étape 5: Démarrer le Frontend

**Nouveau terminal:**

```bash
cd frontend\portail-captif
npm install
npm run dev
```

✅ Frontend disponible sur: **http://localhost:5173**

---

## ✅ Vérifier que Tout Fonctionne

### 1. Backend Django Admin
**Ouvrez:** http://localhost:8000/admin

**Connectez-vous avec:**
- Username: `admin`
- Password: `admin123`

✅ Vous devriez voir l'interface d'administration Django

---

### 2. Frontend Portail Captif
**Ouvrez:** http://localhost:5173

✅ Vous devriez voir la page d'accueil du portail

---

### 3. Test Complet

1. **Cliquez sur "Créer un compte"**
2. **Remplissez le formulaire d'inscription**
3. **Soumettez**
4. ✅ Vous devriez être connecté et redirigé vers le dashboard

**Vérifier dans pgAdmin:**
- Développez `captive_portal_db` → Schemas → public → Tables
- Clic droit sur `core_user` → View/Edit Data → All Rows
- ✅ Votre utilisateur doit apparaître !

---

## 🧪 Test de Communication Backend ↔ Frontend

**Pendant que backend et frontend tournent:**

```bash
python test_communication.py
```

Ce script teste automatiquement:
- ✅ Backend accessible
- ✅ CORS configuré correctement
- ✅ Endpoints API fonctionnels
- ✅ Authentification JWT
- ✅ Communication complète

**Résultat attendu:**
```
🎉 Tous les tests sont passés! (4/4)
✅ Le backend et le frontend peuvent communiquer correctement
```

---

## 📁 Structure du Projet

```
captive-portal/
├── backend/                    # Django Backend
│   ├── core/                  # App principale (User, Device, Session, Voucher)
│   ├── mikrotik/              # App Mikrotik (Router, HotspotUser)
│   ├── radius/                # App RADIUS (Server, AuthLog, Accounting)
│   ├── manage.py              # CLI Django
│   └── .env                   # Configuration (PostgreSQL)
│
├── frontend/portail-captif/   # Vue 3 Frontend
│   ├── src/
│   │   ├── views/            # Pages (Home, Login, Dashboard, Admin...)
│   │   ├── stores/           # Pinia stores (auth, session, device...)
│   │   ├── services/         # API services
│   │   └── router/           # Vue Router
│   └── .env                   # Configuration (VITE_API_URL)
│
├── Scripts Windows:
│   ├── setup_postgresql.bat          # Configuration PostgreSQL
│   ├── start_with_postgresql.bat     # Démarrage backend
│   ├── create_admin.bat              # Créer superuser
│   └── test_communication.py         # Tests
│
└── Documentation/
    ├── README.md                      # Ce fichier
    ├── PROJECT_ANALYSIS.md            # Analyse complète
    ├── POSTGRESQL_CONFIG.md           # Guide PostgreSQL détaillé
    ├── COMMUNICATION_TEST_GUIDE.md    # Guide de tests
    └── DEPLOYMENT_GUIDE.md            # Déploiement production
```

---

## 🎯 Fonctionnalités

### Utilisateurs
- ✅ Inscription / Connexion
- ✅ Gestion de profil
- ✅ Changement de mot de passe
- ✅ Authentification JWT avec refresh automatique

### Sessions
- ✅ Liste des sessions (actives et historiques)
- ✅ Statistiques de bande passante
- ✅ Terminer une session
- ✅ Export CSV

### Appareils
- ✅ Liste des appareils connectés
- ✅ Détection automatique (MAC, IP, type)
- ✅ Désactivation d'appareils
- ✅ Historique de connexion

### Vouchers
- ✅ Codes d'accès temporaires
- ✅ Validation et utilisation
- ✅ Limite de durée et d'appareils
- ✅ Gestion admin

### Administration
- ✅ Dashboard avec statistiques
- ✅ Gestion des utilisateurs (CRUD)
- ✅ Monitoring en temps réel
- ✅ Gestion des sites bloqués
- ✅ Quotas de bande passante

---

## 🔧 Configuration

### Backend (.env)

Le fichier `backend/.env` est automatiquement créé par `setup_postgresql.bat`.

**Configuration PostgreSQL:**
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=captive_portal_db
DB_USER=postgres
DB_PASSWORD=votre_password
DB_HOST=localhost
DB_PORT=5432
```

**Modifier manuellement si nécessaire.**

---

### Frontend (.env)

Le fichier `frontend/portail-captif/.env` contient:
```env
VITE_API_URL=http://localhost:8000
```

**Modifier si le backend est sur une autre machine.**

---

## 🐛 Résolution de Problèmes

### Backend ne démarre pas

**Erreur PostgreSQL:**
```bash
# Vérifier que PostgreSQL est démarré
services.msc → postgresql-x64-16 → Démarrer

# Tester la connexion
cd backend
venv\Scripts\activate
python test_postgresql_connection.py
```

**Voir:** `POSTGRESQL_CONFIG.md` pour une aide détaillée

---

### Frontend ne trouve pas l'API

**Erreur CORS ou ERR_CONNECTION_REFUSED:**

1. Vérifiez que le backend tourne sur :8000
2. Vérifiez `frontend/portail-captif/.env`
3. Redémarrez le frontend après modification du .env

**Voir:** `COMMUNICATION_TEST_GUIDE.md` pour plus de tests

---

### Port déjà utilisé

**Backend (port 8000):**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Frontend (port 5173):**
```bash
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

---

## 📊 Modèles de Base de Données

Le projet utilise **12 modèles** répartis en 3 apps:

### Core (4 modèles)
- **User** - Utilisateurs du portail
- **Device** - Appareils connectés
- **Session** - Sessions de connexion
- **Voucher** - Codes d'accès temporaires

### Mikrotik (4 modèles)
- **MikrotikRouter** - Routeurs Mikrotik
- **MikrotikHotspotUser** - Utilisateurs hotspot
- **MikrotikActiveConnection** - Connexions actives
- **MikrotikLog** - Logs d'opérations

### RADIUS (4 modèles)
- **RadiusServer** - Serveurs RADIUS
- **RadiusAuthLog** - Logs d'authentification
- **RadiusAccounting** - Comptabilité des sessions
- **RadiusClient** - NAS (Network Access Servers)

**Voir:** `PROJECT_ANALYSIS.md` pour les détails complets

---

## 🌐 API Endpoints

**Authentication:**
- `POST /api/core/auth/register/` - Inscription
- `POST /api/core/auth/login/` - Connexion
- `POST /api/core/auth/logout/` - Déconnexion
- `GET /api/core/auth/profile/` - Profil utilisateur
- `POST /api/core/auth/password/change/` - Changer mot de passe

**Resources:**
- `/api/core/users/` - Utilisateurs
- `/api/core/devices/` - Appareils
- `/api/core/sessions/` - Sessions
- `/api/core/vouchers/` - Vouchers

**Mikrotik:**
- `/api/mikrotik/routers/` - Routeurs
- `/api/mikrotik/hotspot-users/` - Utilisateurs hotspot
- `/api/mikrotik/active-connections/` - Connexions actives

**RADIUS:**
- `/api/radius/servers/` - Serveurs RADIUS
- `/api/radius/auth-logs/` - Logs d'authentification
- `/api/radius/accounting/` - Comptabilité

**Voir:** `PROJECT_ANALYSIS.md` pour la liste complète

---

## 📚 Documentation Complète

| Document | Description |
|----------|-------------|
| **README.md** | Ce fichier - Démarrage rapide |
| **PROJECT_ANALYSIS.md** | Analyse exhaustive du projet (26KB) |
| **POSTGRESQL_CONFIG.md** | Guide PostgreSQL détaillé (23KB) |
| **COMMUNICATION_TEST_GUIDE.md** | Tests Backend↔Frontend (16KB) |
| **DEPLOYMENT_GUIDE.md** | Déploiement en production |
| **WINDOWS_TROUBLESHOOTING.md** | Résolution de problèmes Windows |

---

## 🚀 Déploiement en Production

**Voir:** `DEPLOYMENT_GUIDE.md`

Points clés:
- ✅ Changer `SECRET_KEY` dans `.env`
- ✅ Mettre `DEBUG=False`
- ✅ Configurer `ALLOWED_HOSTS`
- ✅ Utiliser Gunicorn/uWSGI
- ✅ Configurer Nginx/Apache
- ✅ Activer HTTPS (SSL/TLS)
- ✅ Configurer les sauvegardes automatiques

---

## 🔐 Sécurité

- ✅ Authentification JWT avec rotation des tokens
- ✅ Mots de passe hashés avec Argon2
- ✅ CORS configuré
- ✅ Protection CSRF
- ✅ Validation des entrées
- ✅ Rate limiting (à configurer en production)

---

## 📞 Support

**Documentation:**
- Consultez les fichiers `.md` dans le projet
- Vérifiez `WINDOWS_TROUBLESHOOTING.md` pour les erreurs courantes

**Logs:**
- **Backend:** Terminal où `manage.py runserver` tourne
- **Frontend:** Console navigateur (F12)
- **PostgreSQL:** pgAdmin → Tools → Server Logs

---

## ✅ Checklist de Démarrage

- [ ] PostgreSQL installé et démarré
- [ ] Base de données `captive_portal_db` créée dans pgAdmin
- [ ] `setup_postgresql.bat` exécuté avec succès
- [ ] `create_admin.bat` exécuté
- [ ] Backend démarre sans erreur (:8000)
- [ ] Frontend démarre sans erreur (:5173)
- [ ] http://localhost:8000/admin accessible
- [ ] http://localhost:5173 accessible
- [ ] Inscription fonctionne
- [ ] Connexion fonctionne
- [ ] Dashboard affiche les données
- [ ] `test_communication.py` passe tous les tests ✅

---

## 📈 Statistiques du Projet

- **7000+ lignes de code**
- **3 applications Django** (core, mikrotik, radius)
- **12 modèles de base de données**
- **50+ endpoints API REST**
- **14 vues/pages frontend** (8 utilisateur + 6 admin)
- **5 stores Pinia** pour la gestion d'état
- **30+ fichiers de documentation**

---

## 🎉 C'est Parti !

1. **Créez la base dans pgAdmin**
2. **Exécutez `setup_postgresql.bat`**
3. **Exécutez `create_admin.bat`**
4. **Lancez `start_with_postgresql.bat`**
5. **Dans un autre terminal: `cd frontend\portail-captif && npm run dev`**
6. **Ouvrez http://localhost:5173**

**Bon développement ! 🚀**

---

**Version:** 1.0.0
**Dernière mise à jour:** 2025-11-20
