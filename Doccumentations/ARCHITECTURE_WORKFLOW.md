# 🏗️ Architecture et Workflow du Portail Captif - Explication Complète

Ce document explique en détail comment le projet est structuré et comment tout fonctionne ensemble.

---

## 📋 Table des Matières

1. [Vue d'Ensemble de l'Architecture](#vue-densemble-de-larchitecture)
2. [Stack Technologique](#stack-technologique)
3. [Architecture en Couches](#architecture-en-couches)
4. [Workflow Complet - Cas d'Usage](#workflow-complet---cas-dusage)
5. [Backend Django - Détails](#backend-django---détails)
6. [Frontend Vue.js - Détails](#frontend-vuejs---détails)
7. [Communication Backend ↔ Frontend](#communication-backend--frontend)
8. [Flux de Données](#flux-de-données)
9. [Sécurité et Authentification](#sécurité-et-authentification)
10. [Intégrations Externes](#intégrations-externes)
11. [Pourquoi Ces Choix ?](#pourquoi-ces-choix-)

---

## 1. Vue d'Ensemble de l'Architecture

### Schéma Global

```
┌─────────────────────────────────────────────────────────────────────┐
│                        UTILISATEUR FINAL                             │
│                     (Navigateur Web Chrome/Firefox)                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌───────────────────┐                   ┌───────────────────┐
│   FRONTEND        │                   │   BACKEND         │
│   Vue 3 + TS      │◄──── REST API ───►│   Django + DRF   │
│   Port 5173       │     (JSON/JWT)    │   Port 8000       │
│                   │                   │                   │
│ ┌───────────────┐ │                   │ ┌───────────────┐ │
│ │ Vue Router    │ │                   │ │ URL Router    │ │
│ │ (Navigation)  │ │                   │ │ (/api/...)    │ │
│ └───────────────┘ │                   │ └───────────────┘ │
│                   │                   │                   │
│ ┌───────────────┐ │                   │ ┌───────────────┐ │
│ │ Pinia Stores  │ │                   │ │ ViewSets      │ │
│ │ (State Mgmt)  │ │                   │ │ (API Logic)   │ │
│ └───────────────┘ │                   │ └───────────────┘ │
│                   │                   │                   │
│ ┌───────────────┐ │                   │ ┌───────────────┐ │
│ │ Axios         │ │                   │ │ Serializers   │ │
│ │ (HTTP Client) │ │                   │ │ (Data Format) │ │
│ └───────────────┘ │                   │ └───────────────┘ │
│                   │                   │                   │
│ ┌───────────────┐ │                   │ ┌───────────────┐ │
│ │ Components    │ │                   │ │ Models        │ │
│ │ (UI)          │ │                   │ │ (ORM)         │ │
│ └───────────────┘ │                   │ └───────────────┘ │
└───────────────────┘                   └─────────┬─────────┘
                                                  │
                                                  │ SQL
                                                  ▼
                                        ┌───────────────────┐
                                        │   PostgreSQL      │
                                        │   Base de Données │
                                        │                   │
                                        │ ┌───────────────┐ │
                                        │ │ Tables:       │ │
                                        │ │ - core_user   │ │
                                        │ │ - core_device │ │
                                        │ │ - core_session│ │
                                        │ │ - ...         │ │
                                        │ └───────────────┘ │
                                        └───────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    INTÉGRATIONS EXTERNES                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐      ┌──────────────────┐                   │
│  │   FreeRADIUS     │      │   Mikrotik       │                   │
│  │   Serveur RADIUS │      │   RouterOS       │                   │
│  │                  │      │                  │                   │
│  │ - Auth (1812)    │      │ - Hotspot API    │                   │
│  │ - Acct (1813)    │      │ - User Mgmt      │                   │
│  └──────────────────┘      └──────────────────┘                   │
│           ▲                         ▲                              │
│           │                         │                              │
│           └─────────┬───────────────┘                              │
│                     │                                              │
│                     │ Connexions depuis Django Backend             │
│                     │                                              │
└─────────────────────┴──────────────────────────────────────────────┘
```

---

## 2. Stack Technologique

### Frontend (Client Side)

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Vue.js** | 3.5.22 | Framework JavaScript réactif |
| **TypeScript** | 5.9.0 | Typage statique |
| **Pinia** | 3.0.3 | Gestion d'état (state management) |
| **Vue Router** | 4.6.3 | Navigation entre pages |
| **Axios** | 1.13.2 | Client HTTP pour appeler l'API |
| **Vite** | 6.3.2 | Build tool & dev server |

### Backend (Server Side)

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Django** | 5.2.8 | Framework web Python |
| **Django REST Framework** | 3.15.2 | API REST |
| **Simple JWT** | 5.4.0 | Authentification JWT |
| **PostgreSQL** | 16+ | Base de données relationnelle |
| **psycopg2** | 2.9.10 | Driver PostgreSQL pour Python |
| **pyrad** | 2.4 | Client RADIUS |
| **CORS Headers** | 4.6.0 | Gestion CORS |

---

## 3. Architecture en Couches

### Principe: Separation of Concerns

Le projet suit une architecture **3-tiers** (3 couches) classique:

```
┌─────────────────────────────────────────────────────────────┐
│  COUCHE PRÉSENTATION (Frontend - Vue.js)                    │
│  ───────────────────────────────────────────────────────    │
│  • Affichage de l'interface utilisateur                     │
│  • Gestion des interactions utilisateur                     │
│  • Validation côté client                                   │
│  • Navigation entre les pages                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ HTTP/REST API (JSON)
                      │ Authentification JWT
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  COUCHE LOGIQUE MÉTIER (Backend - Django)                   │
│  ───────────────────────────────────────────────────────    │
│  • Traitement des requêtes                                  │
│  • Logique métier (règles de gestion)                       │
│  • Authentification & autorisation                          │
│  • Validation des données                                   │
│  • Intégration avec services externes                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ SQL (ORM Django)
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  COUCHE DONNÉES (PostgreSQL)                                │
│  ───────────────────────────────────────────────────────    │
│  • Stockage persistant des données                          │
│  • Intégrité des données (contraintes)                      │
│  • Relations entre tables                                   │
│  • Transactions ACID                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Workflow Complet - Cas d'Usage

### Exemple: Un utilisateur veut se connecter

#### Étape par Étape

```
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: L'utilisateur ouvre le navigateur                          │
└──────────────────────────────────────────────────────────────────────┘

Utilisateur entre: http://localhost:5173

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2: Le serveur Vite (dev) envoie le HTML/CSS/JS au navigateur  │
└──────────────────────────────────────────────────────────────────────┘

Frontend (Vite Dev Server)
├─ Charge: index.html
├─ Charge: main.ts (point d'entrée)
├─ Charge: App.vue (composant racine)
├─ Initialise: Vue Router
├─ Initialise: Pinia stores
└─ Affiche: HomeView.vue (page d'accueil)

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3: L'utilisateur voit la page d'accueil                       │
└──────────────────────────────────────────────────────────────────────┘

HomeView.vue affiche:
├─ Logo UCAC-ICAM
├─ Boutons: "Créer un compte" / "Se connecter"
└─ Bouton "Admin" (en haut à droite)

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 4: L'utilisateur clique sur "Se connecter"                    │
└──────────────────────────────────────────────────────────────────────┘

Vue Router:
├─ Détecte le clic sur le bouton
├─ Navigation vers: /login
└─ Charge: LoginView.vue

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 5: LoginView.vue s'affiche                                    │
└──────────────────────────────────────────────────────────────────────┘

LoginView.vue:
├─ Affiche un formulaire avec:
│  ├─ Champ: Username
│  ├─ Champ: Password
│  └─ Bouton: "Se connecter"
└─ Attend que l'utilisateur remplisse le formulaire

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 6: L'utilisateur remplit le formulaire et clique "Connexion"  │
└──────────────────────────────────────────────────────────────────────┘

Données saisies:
├─ username: "valerdy"
└─ password: "Azerty1234@#"

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 7: Le composant appelle le store Pinia auth                   │
└──────────────────────────────────────────────────────────────────────┘

LoginView.vue:
└─ Appelle: authStore.login({ username, password })

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 8: Le store auth appelle le service auth                      │
└──────────────────────────────────────────────────────────────────────┘

stores/auth.ts:
├─ Fonction: async login(credentials)
└─ Appelle: authService.login(credentials)

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 9: Le service auth fait une requête HTTP vers l'API           │
└──────────────────────────────────────────────────────────────────────┘

services/auth.service.ts:
└─ Axios fait:
    POST http://localhost:8000/api/core/auth/login/
    Headers: { 'Content-Type': 'application/json' }
    Body: {
        "username": "valerdy",
        "password": "Azerty1234@#"
    }

        │ HTTP Request
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 10: Le backend Django reçoit la requête                       │
└──────────────────────────────────────────────────────────────────────┘

Django (backend/urls.py):
├─ Reçoit: POST /api/core/auth/login/
├─ Middleware CORS: Vérifie l'origine (http://localhost:5173) ✅
├─ URL Router: Route vers core.urls
└─ core/urls.py: Route vers views.login

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 11: La vue login traite la requête                            │
└──────────────────────────────────────────────────────────────────────┘

core/views.py - fonction login():
├─ Extrait: username = "valerdy", password = "Azerty1234@#"
├─ Authentifie avec Django:
│  └─ authenticate(username=username, password=password)
│     └─ Django vérifie dans la table core_user
│        ├─ Trouve l'utilisateur avec username="valerdy"
│        └─ Vérifie le hash du mot de passe (bcrypt/argon2)
│           └─ Match ✅
├─ Génère les tokens JWT:
│  ├─ access_token (expire dans 60 min)
│  └─ refresh_token (expire dans 24h)
└─ Retourne la réponse JSON

        │ SQL Query
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 12: PostgreSQL exécute la requête SQL                         │
└──────────────────────────────────────────────────────────────────────┘

PostgreSQL:
├─ Requête: SELECT * FROM core_user WHERE username = 'valerdy'
├─ Trouve: id=1, username="valerdy", is_staff=True, is_superuser=True
└─ Retourne les données à Django

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 13: Django sérialise les données et renvoie la réponse        │
└──────────────────────────────────────────────────────────────────────┘

Django Response:
├─ Status: 200 OK
├─ Headers: { 'Content-Type': 'application/json' }
└─ Body:
    {
        "user": {
            "id": 1,
            "username": "valerdy",
            "email": "valerdy@example.com",
            "is_staff": true,
            "is_superuser": true,
            "first_name": "Valerdy",
            "last_name": ""
        },
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }

        │ HTTP Response
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 14: Axios (frontend) reçoit la réponse                        │
└──────────────────────────────────────────────────────────────────────┘

services/auth.service.ts:
├─ Reçoit: response.data
└─ Retourne au store: { user, access, refresh }

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 15: Le store auth traite la réponse                           │
└──────────────────────────────────────────────────────────────────────┘

stores/auth.ts:
├─ Stocke l'utilisateur: user.value = response.user
├─ Stocke les tokens:
│  ├─ localStorage.setItem('access_token', response.access)
│  └─ localStorage.setItem('refresh_token', response.refresh)
└─ Affiche une notification de succès

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 16: LoginView réagit au succès                                │
└──────────────────────────────────────────────────────────────────────┘

LoginView.vue:
├─ Détecte: authStore.isAuthenticated = true
├─ Vue Router: Navigue vers /dashboard
└─ Charge: DashboardView.vue

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 17: DashboardView s'affiche                                   │
└──────────────────────────────────────────────────────────────────────┘

DashboardView.vue:
├─ Affiche: Bienvenue Valerdy !
├─ Affiche les statistiques:
│  ├─ Nombre de sessions
│  ├─ Nombre d'appareils
│  └─ Bande passante utilisée
└─ Charge les données depuis l'API (avec le token JWT)

        │
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 18: DashboardView charge les statistiques                     │
└──────────────────────────────────────────────────────────────────────┘

DashboardView.vue (onMounted):
└─ Appelle: sessionStore.fetchStatistics()

stores/session.ts:
└─ Appelle: sessionService.getStatistics()

services/session.service.ts:
└─ Axios fait:
    GET http://localhost:8000/api/core/sessions/statistics/
    Headers: {
        'Authorization': 'Bearer eyJ0eXAiOiJKV1Qi...'
    }

        │ HTTP Request (avec JWT)
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 19: Backend vérifie le JWT et retourne les stats              │
└──────────────────────────────────────────────────────────────────────┘

Django:
├─ Middleware JWT: Vérifie le token
│  ├─ Décode le JWT
│  ├─ Vérifie la signature (avec SECRET_KEY)
│  ├─ Vérifie l'expiration
│  └─ Charge l'utilisateur (user_id depuis le token)
├─ ViewSet SessionViewSet.statistics():
│  ├─ Filtre les sessions de l'utilisateur
│  ├─ Calcule les statistiques
│  └─ Retourne JSON
└─ Response:
    {
        "total_sessions": 15,
        "active_sessions": 2,
        "total_data_transferred": 1500000000,
        "average_session_duration": 3600
    }

        │ HTTP Response
        ▼

┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 20: Le Dashboard affiche les statistiques                     │
└──────────────────────────────────────────────────────────────────────┘

DashboardView.vue:
├─ Reçoit les stats du store
├─ Affiche dans l'UI:
│  ├─ 📊 15 sessions totales
│  ├─ ✅ 2 sessions actives
│  ├─ 📈 1.5 GB de données transférées
│  └─ ⏱️ Durée moyenne: 1h
└─ L'utilisateur voit son dashboard complet !
```

---

## 5. Backend Django - Détails

### Structure des Apps Django

Le backend est divisé en **3 applications Django** indépendantes:

#### A. App `core` (Gestion utilisateurs et sessions)

```
backend/core/
├── models.py           # Modèles de données
│   ├── User            # Utilisateur du portail
│   ├── Device          # Appareil connecté
│   ├── Session         # Session de connexion
│   └── Voucher         # Code d'accès temporaire
│
├── views.py            # Logique métier
│   ├── login()         # Authentification
│   ├── register()      # Inscription
│   ├── change_password()
│   └── ...
│
├── serializers.py      # Transformation données ↔ JSON
│   ├── UserSerializer
│   ├── DeviceSerializer
│   ├── SessionSerializer
│   └── VoucherSerializer
│
├── urls.py             # Routes API
│   ├── /api/core/auth/login/
│   ├── /api/core/auth/register/
│   ├── /api/core/users/
│   ├── /api/core/devices/
│   ├── /api/core/sessions/
│   └── /api/core/vouchers/
│
└── admin.py            # Interface admin Django
```

**Rôle:** Gère tout ce qui concerne les utilisateurs du portail captif.

---

#### B. App `mikrotik` (Intégration RouterOS)

```
backend/mikrotik/
├── models.py
│   ├── MikrotikRouter          # Config routeur Mikrotik
│   ├── MikrotikHotspotUser     # Utilisateur hotspot
│   ├── MikrotikActiveConnection # Connexion active
│   └── MikrotikLog             # Logs d'opérations
│
├── views.py
│   ├── RouterViewSet
│   ├── HotspotUserViewSet
│   └── ActiveConnectionViewSet
│
├── utils.py
│   └── MikrotikAgentClient     # Client HTTP pour agent Node.js
│
└── urls.py
    ├── /api/mikrotik/routers/
    ├── /api/mikrotik/hotspot-users/
    └── /api/mikrotik/active-connections/
```

**Rôle:** Gère l'intégration avec les routeurs Mikrotik via l'agent Node.js.

---

#### C. App `radius` (Intégration FreeRADIUS)

```
backend/radius/
├── models.py
│   ├── RadiusServer            # Config serveur RADIUS
│   ├── RadiusAuthLog           # Logs d'authentification
│   ├── RadiusAccounting        # Comptabilité sessions
│   └── RadiusClient            # NAS (Network Access Server)
│
├── views.py
│   ├── RadiusServerViewSet
│   ├── RadiusAuthLogViewSet
│   └── RadiusAccountingViewSet
│
└── urls.py
    ├── /api/radius/servers/
    ├── /api/radius/auth-logs/
    └── /api/radius/accounting/
```

**Rôle:** Gère l'intégration avec les serveurs RADIUS (authentification et comptabilité).

---

### Flux de Traitement d'une Requête Django

```
1. REQUÊTE HTTP arrive
   ↓
2. Middleware CORS vérifie l'origine
   ↓
3. URL Router trouve la route correspondante
   ↓
4. Middleware JWT vérifie le token (si requis)
   ↓
5. ViewSet/View fonction exécute la logique
   ↓
6. ORM Django interroge PostgreSQL
   ↓
7. Serializer transforme les objets en JSON
   ↓
8. RÉPONSE HTTP retournée au frontend
```

---

## 6. Frontend Vue.js - Détails

### Structure des Dossiers

```
frontend/portail-captif/src/
│
├── main.ts                 # Point d'entrée de l'application
│   ├── Crée l'app Vue
│   ├── Configure Pinia (stores)
│   ├── Configure Vue Router
│   └── Monte l'app dans #app
│
├── App.vue                 # Composant racine
│   ├── <router-view />     # Affiche la page courante
│   └── Contient le layout général
│
├── router/
│   └── index.ts            # Configuration des routes
│       ├── Route: / → HomeView
│       ├── Route: /login → LoginView
│       ├── Route: /dashboard → DashboardView (auth required)
│       ├── Route: /admin/* → AdminViews (admin required)
│       └── Navigation guards (vérification auth)
│
├── stores/                 # Pinia (State Management)
│   ├── auth.ts             # État de l'authentification
│   │   ├── State: user, accessToken, refreshToken
│   │   ├── Getters: isAuthenticated, isAdmin
│   │   └── Actions: login(), logout(), fetchProfile()
│   │
│   ├── session.ts          # État des sessions
│   │   ├── State: sessions[], activeSessions[], statistics
│   │   └── Actions: fetchSessions(), terminateSession()
│   │
│   ├── device.ts           # État des appareils
│   ├── voucher.ts          # État des vouchers
│   └── notification.ts     # Notifications toast
│
├── services/               # Couche d'abstraction API
│   ├── api.ts              # Configuration Axios
│   │   ├── Instance Axios avec baseURL
│   │   ├── Request interceptor (ajoute JWT)
│   │   └── Response interceptor (refresh token)
│   │
│   ├── auth.service.ts     # Appels API auth
│   │   ├── login()
│   │   ├── register()
│   │   └── changePassword()
│   │
│   ├── session.service.ts  # Appels API sessions
│   ├── device.service.ts   # Appels API devices
│   └── voucher.service.ts  # Appels API vouchers
│
├── views/                  # Pages de l'application
│   ├── HomeView.vue        # Page d'accueil
│   ├── LoginView.vue       # Page de connexion
│   ├── RegisterView.vue    # Page d'inscription
│   ├── DashboardView.vue   # Dashboard utilisateur
│   ├── SessionsView.vue    # Liste des sessions
│   ├── DevicesView.vue     # Liste des appareils
│   ├── ProfileView.vue     # Profil utilisateur
│   ├── VouchersView.vue    # Gestion vouchers
│   │
│   └── Admin/              # Pages admin
│       ├── AdminLoginView.vue
│       ├── AdminDashboardView.vue
│       ├── AdminUsersView.vue
│       ├── AdminMonitoringView.vue
│       ├── AdminSitesView.vue
│       └── AdminQuotasView.vue
│
├── components/             # Composants réutilisables
│   ├── DataTable.vue       # Table avec tri, pagination, export
│   ├── Modal.vue           # Fenêtre modale
│   └── ...
│
└── types/
    └── index.ts            # Types TypeScript
        ├── interface User
        ├── interface Session
        ├── interface Device
        └── interface Voucher
```

### Flux de Rendu d'une Page

```
1. URL change (ex: /login)
   ↓
2. Vue Router détecte le changement
   ↓
3. Navigation guard vérifie l'auth (si nécessaire)
   ↓
4. Router charge le composant (LoginView.vue)
   ↓
5. Composant monte (onMounted hook)
   ↓
6. Composant charge les données (via store)
   ↓
7. Store appelle le service
   ↓
8. Service fait la requête HTTP (Axios)
   ↓
9. Backend répond avec JSON
   ↓
10. Service retourne au store
   ↓
11. Store met à jour son state
   ↓
12. Vue détecte le changement (réactivité)
   ↓
13. Composant se re-rend avec les nouvelles données
```

---

## 7. Communication Backend ↔ Frontend

### Architecture REST API

```
Frontend                           Backend
   │                                 │
   │  POST /api/core/auth/login/    │
   ├────────────────────────────────>│
   │  { username, password }         │
   │                                 │
   │              200 OK             │
   │<────────────────────────────────┤
   │  { user, access, refresh }      │
   │                                 │
   │                                 │
   │  GET /api/core/sessions/        │
   │  Header: Authorization: Bearer TOKEN
   ├────────────────────────────────>│
   │                                 │
   │              200 OK             │
   │<────────────────────────────────┤
   │  { count, results: [...] }      │
   │                                 │
```

### Format des Données

**Requête (Frontend → Backend):**
```http
POST /api/core/auth/login/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Origin: http://localhost:5173

{
  "username": "valerdy",
  "password": "Azerty1234@#"
}
```

**Réponse (Backend → Frontend):**
```http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: http://localhost:5173

{
  "user": {
    "id": 1,
    "username": "valerdy",
    "email": "valerdy@example.com",
    "is_staff": true,
    "is_superuser": true
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzAwNTAwMDAwLCJpYXQiOjE3MDA0OTY0MDAsImp0aSI6IjEyMzQ1IiwidXNlcl9pZCI6MX0.signature",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## 8. Flux de Données

### Cas 1: Inscription d'un Nouvel Utilisateur

```
FRONTEND                          BACKEND                         DATABASE
   │                                │                                │
   │ 1. Utilisateur remplit         │                                │
   │    le formulaire               │                                │
   │                                │                                │
   │ 2. Clique "S'inscrire"         │                                │
   │                                │                                │
   │ 3. POST /api/core/auth/register/                               │
   │    { username, email,          │                                │
   │      password, ... }           │                                │
   ├───────────────────────────────>│                                │
   │                                │ 4. Valide les données          │
   │                                │    - Username unique ?         │
   │                                │    - Email valide ?            │
   │                                │    - Password assez long ?     │
   │                                │                                │
   │                                │ 5. Hash le mot de passe        │
   │                                │    (bcrypt/argon2)             │
   │                                │                                │
   │                                │ 6. INSERT INTO core_user       │
   │                                ├───────────────────────────────>│
   │                                │                                │
   │                                │    7. Retourne ID=1            │
   │                                │<───────────────────────────────┤
   │                                │                                │
   │                                │ 8. Génère tokens JWT           │
   │                                │    - access (60 min)           │
   │                                │    - refresh (24h)             │
   │                                │                                │
   │    9. 201 Created              │                                │
   │    { user, access, refresh }   │                                │
   │<───────────────────────────────┤                                │
   │                                │                                │
   │ 10. Stocke tokens dans         │                                │
   │     localStorage               │                                │
   │                                │                                │
   │ 11. Redirige vers /dashboard   │                                │
   │                                │                                │
   ▼                                ▼                                ▼
```

---

### Cas 2: Consultation des Sessions (Requête Authentifiée)

```
FRONTEND                          BACKEND                         DATABASE
   │                                │                                │
   │ 1. DashboardView monte         │                                │
   │                                │                                │
   │ 2. sessionStore.fetchSessions()│                                │
   │                                │                                │
   │ 3. GET /api/core/sessions/     │                                │
   │    Header: Authorization:      │                                │
   │    Bearer eyJ0eXAiOiJKV1...    │                                │
   ├───────────────────────────────>│                                │
   │                                │ 4. Middleware JWT vérifie      │
   │                                │    - Decode le token           │
   │                                │    - Vérifie signature         │
   │                                │    - Vérifie expiration        │
   │                                │    - Extrait user_id=1         │
   │                                │                                │
   │                                │ 5. SELECT * FROM core_session  │
   │                                │    WHERE user_id = 1           │
   │                                ├───────────────────────────────>│
   │                                │                                │
   │                                │    6. Retourne 5 sessions      │
   │                                │<───────────────────────────────┤
   │                                │                                │
   │                                │ 7. Sérialise en JSON           │
   │                                │                                │
   │    8. 200 OK                   │                                │
   │    { count: 5, results: [...] }│                                │
   │<───────────────────────────────┤                                │
   │                                │                                │
   │ 9. Store met à jour state      │                                │
   │    sessions.value = results    │                                │
   │                                │                                │
   │ 10. Vue re-rend automatiquement│                                │
   │     (réactivité)               │                                │
   │                                │                                │
   │ 11. L'utilisateur voit ses     │                                │
   │     sessions dans la table     │                                │
   │                                │                                │
   ▼                                ▼                                ▼
```

---

### Cas 3: Refresh du Token JWT (Auto)

```
FRONTEND (Axios Interceptor)      BACKEND
   │                                │
   │ 1. Requête API quelconque      │
   │    avec access token expiré    │
   ├───────────────────────────────>│
   │                                │ 2. Vérifie JWT
   │                                │    → Expiré !
   │                                │
   │    3. 401 Unauthorized         │
   │<───────────────────────────────┤
   │                                │
   │ 4. Response Interceptor        │
   │    détecte le 401              │
   │                                │
   │ 5. POST /api/core/auth/token/refresh/
   │    { refresh: "eyJ0eXA..." }   │
   ├───────────────────────────────>│
   │                                │ 6. Vérifie refresh token
   │                                │    → Valide ✅
   │                                │
   │                                │ 7. Génère nouveau access
   │                                │
   │    8. 200 OK                   │
   │    { access: "newToken..." }   │
   │<───────────────────────────────┤
   │                                │
   │ 9. Stocke le nouveau token     │
   │    localStorage.setItem(...)   │
   │                                │
   │ 10. RETRY la requête originale │
   │     avec le nouveau token      │
   ├───────────────────────────────>│
   │                                │ 11. Token valide ✅
   │                                │
   │    12. 200 OK                  │
   │    { data }                    │
   │<───────────────────────────────┤
   │                                │
   │ 13. L'utilisateur ne voit rien │
   │     (transparent)              │
   │                                │
   ▼                                ▼
```

**Avantage:** L'utilisateur reste connecté sans interruption !

---

## 9. Sécurité et Authentification

### Principe JWT (JSON Web Token)

#### Structure d'un JWT

```
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzAwNTAwMDAwLCJpYXQiOjE3MDA0OTY0MDAsImp0aSI6IjEyMzQ1IiwidXNlcl9pZCI6MX0.T3EqPg7FgHmSH5jJ3kF_signature
│────────────────────────────────│──────────────────────────────────────────────────────────────────────────────────────│─────────────────────────────────
         HEADER                                           PAYLOAD                                                               SIGNATURE
      (Base64)                                         (Base64)                                                              (HMAC SHA256)
```

**Header:**
```json
{
  "typ": "JWT",
  "alg": "HS256"
}
```

**Payload:**
```json
{
  "token_type": "access",
  "exp": 1700500000,    // Expiration timestamp
  "iat": 1700496400,    // Issued at timestamp
  "jti": "12345",       // JWT ID (unique)
  "user_id": 1          // ID de l'utilisateur
}
```

**Signature:**
```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  SECRET_KEY
)
```

---

### Flux de Sécurité

#### 1. Connexion Initiale

```
1. Frontend envoie: { username, password }
   ↓
2. Backend vérifie:
   - Username existe ?
   - Hash du password match ?
   ↓
3. Si OK, génère:
   - access_token (60 min)
   - refresh_token (24h)
   ↓
4. Frontend stocke:
   - localStorage.setItem('access_token', ...)
   - localStorage.setItem('refresh_token', ...)
```

---

#### 2. Requêtes Authentifiées

```
1. Frontend (Axios Interceptor):
   config.headers.Authorization = `Bearer ${access_token}`
   ↓
2. Backend (JWT Middleware):
   - Extrait le token du header
   - Décode le JWT
   - Vérifie la signature avec SECRET_KEY
   - Vérifie l'expiration
   - Charge l'utilisateur (user_id depuis payload)
   ↓
3. Si valide:
   request.user = User(id=1, username="valerdy", ...)
   ↓
4. La vue peut accéder à request.user
```

---

#### 3. Expiration et Refresh

```
Access Token Expire (après 60 min):
   ↓
Backend retourne: 401 Unauthorized
   ↓
Frontend (Response Interceptor):
   - Détecte le 401
   - Envoie refresh_token au backend
   - Reçoit nouveau access_token
   - Retry la requête
   ↓
Si Refresh Token aussi expiré (après 24h):
   - Déconnecte l'utilisateur
   - Redirige vers /login
```

---

### Protection CSRF

**Django** inclut une protection CSRF automatique, mais pour les API REST, nous utilisons:
- **JWT** au lieu des cookies de session
- **CORS Headers** pour contrôler les origines autorisées

Configuration CORS (`backend/.env`):
```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

Seuls ces domaines peuvent faire des requêtes à l'API !

---

### Hash des Mots de Passe

Django utilise **Argon2** (ou bcrypt) pour hasher les mots de passe:

```python
# Lors de la création d'un utilisateur
user.set_password("Azerty1234@#")
# → Stocke: "$argon2id$v=19$m=102400,t=2,p=8$salt$hash"

# Lors de la vérification
user.check_password("Azerty1234@#")
# → True si match, False sinon
```

Le mot de passe en clair n'est **jamais stocké** en base !

---

## 10. Intégrations Externes

### A. FreeRADIUS (Authentification RADIUS)

```
Django Backend                    FreeRADIUS Server
   │                                    │
   │ 1. Utilisateur se connecte         │
   │                                    │
   │ 2. Backend envoie requête RADIUS   │
   │    (pyrad library)                 │
   ├───────────────────────────────────>│
   │    Packet: Access-Request          │
   │    - Username: valerdy             │
   │    - Password: Azerty1234@#        │
   │    - NAS-IP-Address: 192.168.1.1   │
   │                                    │
   │                                    │ 3. FreeRADIUS vérifie
   │                                    │    dans sa base MySQL
   │                                    │
   │    4. Access-Accept                │
   │<───────────────────────────────────┤
   │    - Session-Timeout: 3600         │
   │    - Bandwidth-Limit: 1000000      │
   │                                    │
   │ 5. Backend crée session            │
   │    dans PostgreSQL                 │
   │                                    │
   │ 6. Backend envoie Accounting-Start │
   ├───────────────────────────────────>│
   │                                    │
   │    ... Utilisateur navigue ...     │
   │                                    │
   │ 7. Backend envoie Accounting-Stop  │
   │    (à la déconnexion)              │
   ├───────────────────────────────────>│
   │    - Bytes-In: 50000000            │
   │    - Bytes-Out: 20000000           │
   │    - Session-Time: 3542            │
   │                                    │
   ▼                                    ▼
```

---

### B. Mikrotik RouterOS

```
Django Backend              Node.js Agent           Mikrotik Router
   │                             │                        │
   │ 1. Admin crée un user       │                        │
   │                             │                        │
   │ 2. POST /api/mikrotik/      │                        │
   │    hotspot-users/           │                        │
   │    { username, password }   │                        │
   │                             │                        │
   │                             │ 3. HTTP POST           │
   │                             │    /api/mikrotik/      │
   │                             │    hotspot/users       │
   │<───────────────────────────>│                        │
   │                             │                        │
   │                             │ 4. RouterOS API Call   │
   │                             ├───────────────────────>│
   │                             │    /ip/hotspot/user/add│
   │                             │    name=valerdy        │
   │                             │    password=***        │
   │                             │                        │
   │                             │    5. User created     │
   │                             │<───────────────────────┤
   │                             │                        │
   │    6. 201 Created           │                        │
   │<───────────────────────────>│                        │
   │                             │                        │
   │ 7. Stocke dans PostgreSQL   │                        │
   │    (MikrotikHotspotUser)    │                        │
   │                             │                        │
   ▼                             ▼                        ▼
```

**Pourquoi un Agent Node.js ?**
- La bibliothèque RouterOS API fonctionne mieux en Node.js
- Isolation: Si l'agent crash, le backend continue de fonctionner
- Scalabilité: Peut gérer plusieurs routeurs simultanément

---

## 11. Pourquoi Ces Choix ?

### A. Pourquoi Vue.js 3 (et pas React ou Angular) ?

✅ **Avantages:**
- **Légèreté:** Plus petit bundle size que React
- **Performance:** Virtual DOM optimisé
- **Composition API:** Code plus organisé et réutilisable
- **TypeScript:** Support natif excellent
- **Courbe d'apprentissage:** Plus facile à prendre en main
- **Réactivité:** Système de réactivité très intuitif

❌ **Inconvénients:**
- Écosystème légèrement plus petit que React
- Moins de jobs (mais en croissance)

---

### B. Pourquoi Django (et pas Flask ou FastAPI) ?

✅ **Avantages:**
- **Batteries included:** Admin, ORM, Auth déjà intégrés
- **Django REST Framework:** Excellent pour créer des APIs
- **ORM Puissant:** Facilite les requêtes SQL complexes
- **Admin Django:** Interface d'administration automatique
- **Sécurité:** Protection CSRF, XSS, SQL Injection par défaut
- **Maturité:** Framework très stable, grande communauté

❌ **Inconvénients:**
- Plus lourd que Flask ou FastAPI
- Moins performant en async (mais suffisant pour ce projet)

---

### C. Pourquoi PostgreSQL (et pas MySQL ou MongoDB) ?

✅ **Avantages:**
- **Performance:** Excellent pour les requêtes complexes
- **Intégrité:** Contraintes FK strictes
- **JSON Support:** Peut stocker du JSON natif
- **Full-text Search:** Recherche avancée intégrée
- **Transactions ACID:** Garanties fortes
- **Open Source:** Gratuit, pas de restrictions

❌ **Inconvénients:**
- Légèrement plus complexe que SQLite
- Nécessite un serveur dédié

**Pourquoi pas MySQL ?**
- PostgreSQL a de meilleures performances pour les JOINs complexes
- Support JSON plus avancé
- Respect plus strict des standards SQL

**Pourquoi pas MongoDB ?**
- Nous avons besoin de relations (utilisateur ↔ sessions ↔ appareils)
- Les bases relationnelles sont mieux adaptées

---

### D. Pourquoi JWT (et pas Sessions) ?

✅ **Avantages:**
- **Stateless:** Le backend n'a pas besoin de stocker les sessions
- **Scalabilité:** Facile d'ajouter des serveurs backend
- **API-First:** Parfait pour les SPA (Single Page Applications)
- **Mobile-Friendly:** Fonctionne facilement avec des apps mobiles
- **Décentralisé:** Peut être vérifié sans DB query

❌ **Inconvénients:**
- Légèrement plus complexe que les sessions Django
- Impossible de révoquer un token avant expiration (sauf blacklist)

---

### E. Pourquoi Pinia (et pas Vuex) ?

✅ **Avantages:**
- **Plus Simple:** API plus intuitive que Vuex
- **TypeScript:** Support natif excellent
- **Composition API:** S'intègre mieux avec Vue 3
- **DevTools:** Excellent support dans Vue DevTools
- **Modulaire:** Pas de mutations explicites

**Vuex** est l'ancienne solution, **Pinia** est le nouveau standard pour Vue 3.

---

### F. Pourquoi Axios (et pas Fetch) ?

✅ **Avantages:**
- **Interceptors:** Facile d'ajouter JWT automatiquement
- **Timeout:** Support natif
- **Cancel Requests:** Peut annuler des requêtes en cours
- **Auto JSON:** Parse automatiquement le JSON
- **Progress:** Peut suivre l'upload/download progress

**Fetch** est natif au navigateur, mais Axios offre plus de fonctionnalités.

---

## 🎯 Résumé de l'Architecture

### Séparation des Responsabilités

```
┌──────────────────────────────────────────────────┐
│ FRONTEND (Vue.js)                                │
│ ───────────────────────────────────────────────  │
│ • Affichage UI                                   │
│ • Validation côté client                         │
│ • Navigation                                     │
│ • Gestion d'état local (Pinia)                   │
└──────────────────┬───────────────────────────────┘
                   │
                   │ REST API (JSON)
                   │ Authentification JWT
                   │
┌──────────────────▼───────────────────────────────┐
│ BACKEND (Django)                                 │
│ ───────────────────────────────────────────────  │
│ • Logique métier                                 │
│ • Validation serveur                             │
│ • Authentification & autorisation                │
│ • Intégration services externes                  │
└──────────────────┬───────────────────────────────┘
                   │
                   │ SQL (ORM)
                   │
┌──────────────────▼───────────────────────────────┐
│ DATABASE (PostgreSQL)                            │
│ ───────────────────────────────────────────────  │
│ • Persistance des données                        │
│ • Intégrité référentielle                        │
│ • Transactions                                   │
└──────────────────────────────────────────────────┘
```

---

### Technologies Clés

| Couche | Technologie | Rôle |
|--------|-------------|------|
| **Présentation** | Vue 3 + TypeScript | Interface utilisateur |
| **State Management** | Pinia | Gestion d'état global |
| **Routing** | Vue Router | Navigation SPA |
| **HTTP Client** | Axios | Appels API |
| **API** | Django REST Framework | Endpoints REST |
| **Authentication** | Simple JWT | Tokens JWT |
| **ORM** | Django ORM | Abstraction base de données |
| **Database** | PostgreSQL | Stockage persistant |
| **RADIUS** | pyrad | Client RADIUS |
| **Mikrotik** | routeros-api (Node.js) | API RouterOS |

---

**C'est ainsi que tout le système fonctionne ensemble ! 🚀**

Chaque composant a un rôle bien défini, et ils communiquent via des interfaces claires (REST API, SQL).

---

**Version:** 1.0.0
**Dernière mise à jour:** 2025-11-20
