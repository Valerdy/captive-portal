# Frontend Vue.js - Portail Captif

## 📋 État Actuel

### ✅ Complété (85%)

- **API Client** : Axios configuré avec intercepteurs JWT
- **Types TypeScript** : Tous les types pour User, Session, Device, Voucher
- **Services** : Services complets pour Auth, Sessions, Devices, Vouchers
- **Stores Pinia** : State management complet (auth, session, device, voucher)
- **Routing** : Router avec guards d'authentification
- **Pages** : Login et Dashboard fonctionnels

### 🚧 À Compléter

- Pages Register, Sessions, Devices, Vouchers, Profile
- Composants UI réutilisables
- Tests unitaires
- Gestion des erreurs améliorée

## 🚀 Démarrage

```bash
cd /home/user/captive-portal/frontend/portail-captif
npm install --ignore-scripts  # Si nécessaire
npm run dev
```

L'application sera disponible sur `http://localhost:5173`

## 📁 Structure

```
src/
├── types/
│   └── index.ts              # Tous les types TypeScript
├── services/
│   ├── api.ts                # Client Axios avec intercepteurs
│   ├── auth.service.ts       # Service d'authentification
│   ├── session.service.ts    # Service de sessions
│   ├── device.service.ts     # Service de devices
│   └── voucher.service.ts    # Service de vouchers
├── stores/
│   ├── auth.ts               # Store Pinia auth (user, tokens)
│   ├── session.ts            # Store Pinia sessions
│   ├── device.ts             # Store Pinia devices
│   └── voucher.ts            # Store Pinia vouchers
├── views/
│   ├── LoginView.vue         # Page de connexion ✅
│   ├── DashboardView.vue     # Dashboard utilisateur ✅
│   ├── RegisterView.vue      # Page d'inscription
│   ├── SessionsView.vue      # Gestion des sessions
│   ├── DevicesView.vue       # Gestion des devices
│   ├── VouchersView.vue      # Utilisation de vouchers
│   └── ProfileView.vue       # Profil utilisateur
└── router/
    └── index.ts              # Configuration du router ✅
```

## 🔑 Fonctionnalités Implémentées

### Authentification (Store Auth)
- ✅ Login avec JWT
- ✅ Register
- ✅ Logout avec blacklist token
- ✅ Auto-refresh token (via intercepteur)
- ✅ Persistence dans localStorage
- ✅ Initialisation auto au démarrage

### Sessions (Store Session)
- ✅ Liste des sessions
- ✅ Sessions actives
- ✅ Statistiques (total, actives, données, durée moyenne)
- ✅ Terminer une session

### Devices (Store Device)
- ✅ Liste des devices
- ✅ Devices actifs
- ✅ Désactiver un device

### Vouchers (Store Voucher)
- ✅ Liste des vouchers
- ✅ Vouchers actifs
- ✅ Validation de code
- ✅ Utilisation de code

## 🎨 Design

Le design actuel utilise :
- Gradient moderne (violet/bleu)
- Cards avec ombres légères
- Design responsive
- Transitions fluides

## 🔧 Configuration

### Variables d'Environnement (.env)

```env
VITE_API_URL=http://localhost:8000
```

### Routing et Guards

Le router configure automatiquement :
- Redirection vers `/login` si non authentifié
- Redirection vers `/` (dashboard) si déjà connecté et tentative d'accès à login/register
- Initialisation auto de l'auth depuis localStorage

## 📝 Utilisation des Stores

### Exemple : Login

```typescript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Login
await authStore.login({ username: 'user', password: 'pass' })

// Vérifier si authentifié
if (authStore.isAuthenticated) {
  // ...
}

// Accéder à l'utilisateur
console.log(authStore.user?.username)
```

### Exemple : Sessions

```typescript
import { useSessionStore } from '@/stores/session'

const sessionStore = useSessionStore()

// Récupérer les statistiques
await sessionStore.fetchStatistics()
console.log(sessionStore.statistics?.total_sessions)

// Sessions actives
await sessionStore.fetchActiveSessions()
console.log(sessionStore.activeSessions)
```

## 🧪 Tests

Pour tester l'intégration avec le backend :

1. Démarrer le backend Django :
```bash
cd /home/user/captive-portal/backend
source venv/bin/activate
python manage.py runserver
```

2. Démarrer le frontend :
```bash
cd /home/user/captive-portal/frontend/portail-captif
npm run dev
```

3. Accéder à http://localhost:5173/login

4. Se connecter avec :
- Username: `john.doe`
- Password: `password123`

## 🎯 Prochaines Étapes

1. **Compléter les pages manquantes** :
   - RegisterView.vue
   - SessionsView.vue
   - DevicesView.vue
   - VouchersView.vue
   - ProfileView.vue

2. **Ajouter des composants réutilisables** :
   - LoadingSpinner
   - ErrorAlert
   - DataTable
   - Modal
   - Card

3. **Améliorer l'UX** :
   - Notifications toast
   - Confirmations de suppression
   - Pagination pour les listes
   - Filtres et recherche

4. **Tests** :
   - Tests unitaires (Vitest)
   - Tests E2E (Cypress)

## 📊 Technologies Utilisées

- **Vue 3.5.22** avec Composition API
- **TypeScript 5.9.0**
- **Pinia 3.0.3** (state management)
- **Vue Router 4.6.3**
- **Axios** (HTTP client)
- **Vite** (build tool)

## ✨ Points Forts

- Architecture propre et scalable
- TypeScript pour la type-safety
- State management centralisé avec Pinia
- Auto-refresh des tokens JWT
- Persistence de la session
- Code modulaire et réutilisable
- Design moderne et responsive

---

**Frontend Captive Portal - Implémenté partiellement le 2025-11-18** 🚀
