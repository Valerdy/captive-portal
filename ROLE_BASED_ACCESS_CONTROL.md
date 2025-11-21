# 🎯 Système de Contrôle d'Accès Basé sur les Rôles (RBAC)

## 📋 Vue d'Ensemble

Ce document décrit le système complet de gestion des rôles et des permissions implémenté dans le portail captif.

### Rôles Disponibles

| Rôle | Description | Accès |
|------|-------------|-------|
| **admin** | Administrateur | Accès complet à toutes les fonctionnalités |
| **user** | Utilisateur standard | Accès limité aux fonctionnalités de base |

---

## 🏗️ Architecture

### 1. Modèle de Données

**Modèle `Role`** (`backend/core/models.py`)

```python
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Modèle `User`** (étendu)

```python
class User(AbstractUser):
    # ... champs existants ...
    role = models.ForeignKey(Role, on_delete=models.PROTECT, default=get_default_role)

    # Méthodes utiles
    def get_role_name(self):
        """Retourne 'admin' si is_staff/is_superuser, sinon 'user'"""

    def is_admin(self):
        """Vérifie si l'utilisateur est admin"""

    def is_regular_user(self):
        """Vérifie si l'utilisateur est un utilisateur standard"""
```

### 2. Synchronisation Automatique

**Signals** (`backend/core/signals.py`)

Le système synchronise automatiquement les rôles avec les flags Django :

```python
@receiver(pre_save, sender=User)
def sync_role_with_permissions(sender, instance, **kwargs):
    if instance.is_staff or instance.is_superuser:
        instance.role = admin_role
    else:
        instance.role = user_role
```

**Règle de Mapping :**
- `is_staff=True` OU `is_superuser=True` → rôle **admin**
- Sinon → rôle **user**

---

## 🔐 Permissions Backend (Django REST Framework)

### Permissions Personnalisées

**Fichier :** `backend/core/permissions.py`

#### 1. `IsAdmin`
```python
class IsAdmin(permissions.BasePermission):
    """Accès uniquement aux administrateurs"""
```

**Usage :** Protéger les endpoints admin uniquement

#### 2. `IsAdminOrReadOnly`
```python
class IsAdminOrReadOnly(permissions.BasePermission):
    """Admins : accès complet, autres : lecture seule"""
```

**Usage :** Permettre la lecture à tous, modification aux admins

#### 3. `IsOwnerOrAdmin`
```python
class IsOwnerOrAdmin(permissions.BasePermission):
    """Accès au propriétaire ou aux admins"""
```

**Usage :** Protéger les ressources utilisateur (devices, sessions)

#### 4. `IsAuthenticatedUser`
```python
class IsAuthenticatedUser(permissions.BasePermission):
    """Utilisateur authentifié (admin ou user)"""
```

**Usage :** Routes nécessitant simplement d'être connecté

### Application dans les ViewSets

**Exemple : UserViewSet**

```python
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedUser]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]  # Inscription publique
        elif self.action == 'list':
            return [IsAdmin()]  # Liste : admins seulement
        elif self.action in ['retrieve', 'update']:
            return [IsOwnerOrAdmin()]  # Modification : owner ou admin
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return User.objects.all()  # Admins voient tout
        return User.objects.filter(id=user.id)  # Users voient eux-mêmes
```

### Permissions par ViewSet

| ViewSet | Liste | Détail | Création | Modification | Suppression |
|---------|-------|--------|----------|--------------|-------------|
| **User** | Admin | Owner/Admin | Public | Owner/Admin | Owner/Admin |
| **Device** | Owner/Admin | Owner/Admin | Owner/Admin | Owner/Admin | Owner/Admin |
| **Session** | Owner/Admin | Owner/Admin | Owner/Admin | Owner/Admin | Owner/Admin |
| **Voucher** | Admin | Admin | Admin | Admin | Admin |

---

## 🛡️ Décorateurs pour Vues Django

**Fichier :** `backend/core/decorators.py`

### 1. `@role_required('admin', 'user')`

```python
@role_required('admin')
def my_admin_view(request):
    # Uniquement accessible aux admins
    ...
```

### 2. `@admin_required`

```python
@admin_required
def admin_dashboard(request):
    # Raccourci pour @role_required('admin')
    ...
```

### 3. `@user_required`

```python
@user_required
def user_profile(request):
    # N'importe quel utilisateur authentifié
    ...
```

### 4. `@owner_or_admin_required(get_object_func)`

```python
def get_device(device_id):
    return Device.objects.get(id=device_id)

@owner_or_admin_required(get_device)
def device_detail(request, device_id):
    # Propriétaire ou admin
    ...
```

---

## 🎨 Frontend (Vue.js)

### Types TypeScript

**Fichier :** `frontend/portail-captif/src/types/index.ts`

```typescript
export interface User {
  id: number
  username: string
  email: string
  is_staff?: boolean
  is_superuser?: boolean
  role_name?: string  // 'admin' | 'user'
  // ... autres champs
}
```

### Auth Store

**Fichier :** `frontend/portail-captif/src/stores/auth.ts`

```typescript
// Getters
const isAdmin = computed(() => {
  if (user.value?.role_name) {
    return user.value.role_name === 'admin'
  }
  return user.value?.is_staff || user.value?.is_superuser || false
})

const userRole = computed(() =>
  user.value?.role_name || (isAdmin.value ? 'admin' : 'user')
)
```

### Vue Router Guards

**Fichier :** `frontend/portail-captif/src/router/index.ts`

```typescript
// Métadonnées de route
meta: {
  requiresAuth: true,    // Nécessite d'être connecté
  requiresAdmin: true    // Nécessite le rôle admin
}

// Navigation Guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'home' })  // Redirection si pas admin
  } else {
    next()
  }
})
```

### Routes par Rôle

#### Routes **User** (accessible par user ET admin)

```typescript
{
  path: '/dashboard',
  meta: { requiresAuth: true }  // Pas requiresAdmin
}
{
  path: '/devices',
  meta: { requiresAuth: true }
}
{
  path: '/sessions',
  meta: { requiresAuth: true }
}
{
  path: '/profile',
  meta: { requiresAuth: true }
}
```

#### Routes **Admin** (accessible uniquement par admin)

```typescript
{
  path: '/admin/dashboard',
  meta: { requiresAuth: true, requiresAdmin: true }
}
{
  path: '/admin/users',
  meta: { requiresAuth: true, requiresAdmin: true }
}
{
  path: '/admin/monitoring',
  meta: { requiresAuth: true, requiresAdmin: true }
}
{
  path: '/admin/sites',
  meta: { requiresAuth: true, requiresAdmin: true }
}
{
  path: '/admin/quotas',
  meta: { requiresAuth: true, requiresAdmin: true }
}
```

---

## 🚀 Installation et Configuration

### Étape 1 : Appliquer les Migrations

```bash
cd backend
python setup_roles.py
```

Ce script va :
1. ✅ Générer les migrations pour le modèle Role
2. ✅ Appliquer toutes les migrations
3. ✅ Créer les rôles par défaut (admin, user)
4. ✅ Synchroniser les utilisateurs existants
5. ✅ Vérifier la configuration

**OU manuellement :**

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### Étape 2 : Créer les Rôles Manuellement (si nécessaire)

```bash
python manage.py shell
```

```python
from core.models import Role

# Créer le rôle admin
Role.objects.create(
    name='admin',
    description='Administrator with full access'
)

# Créer le rôle user
Role.objects.create(
    name='user',
    description='Standard user with basic access'
)
```

### Étape 3 : Synchroniser les Utilisateurs Existants

```python
from core.models import User, Role

admin_role = Role.objects.get(name='admin')
user_role = Role.objects.get(name='user')

for user in User.objects.all():
    if user.is_staff or user.is_superuser:
        user.role = admin_role
    else:
        user.role = user_role
    user.save()
```

### Étape 4 : Redémarrer le Backend

```bash
# Arrêter le serveur (Ctrl+C)
python manage.py runserver 0.0.0.0:8000
```

---

## 📝 Utilisation

### Créer un Utilisateur Admin

```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: ********
```

➡️ Cet utilisateur aura automatiquement le rôle **admin**.

### Créer un Utilisateur Regular

**Via l'API (Inscription) :**

```bash
curl -X POST http://localhost:8000/api/core/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password123",
    "password2": "secure_password123"
  }'
```

➡️ Cet utilisateur aura automatiquement le rôle **user**.

**Via Django Admin (par un admin) :**

1. Accéder à http://localhost:8000/admin/
2. Aller dans "Users"
3. Cliquer "Add user"
4. Remplir les informations
5. ⚠️ Ne PAS cocher `is_staff` ou `is_superuser` pour un user standard

### Promouvoir un Utilisateur en Admin

```python
from core.models import User

user = User.objects.get(username='john_doe')
user.is_staff = True
user.save()  # Le signal synchronisera automatiquement le rôle
```

---

## 🔍 API Response Examples

### Login Response

```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "is_active": true,
    "is_staff": true,
    "is_superuser": true,
    "role_name": "admin",
    "role_detail": {
      "id": 1,
      "name": "admin",
      "description": "Administrator with full access"
    },
    "date_joined": "2025-11-21T10:00:00Z"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Login successful"
}
```

### User List (Admin)

```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role_name": "admin",
      "is_active": true
    },
    {
      "id": 2,
      "username": "john_doe",
      "email": "john@example.com",
      "role_name": "user",
      "is_active": true
    }
  ]
}
```

---

## 🧪 Tests

### Tester les Permissions API

```bash
# 1. Créer un admin et un user
python manage.py createsuperuser  # admin
# Puis inscription normale pour user

# 2. Tester l'accès à la liste des utilisateurs (admin only)
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/api/core/users/
# ✅ Devrait retourner tous les users

curl -H "Authorization: Bearer <user_token>" \
  http://localhost:8000/api/core/users/
# ❌ Devrait retourner 403 Forbidden

# 3. Tester l'accès aux devices (owner ou admin)
curl -H "Authorization: Bearer <user_token>" \
  http://localhost:8000/api/core/devices/
# ✅ Devrait retourner uniquement les devices du user

curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/api/core/devices/
# ✅ Devrait retourner tous les devices
```

### Tester les Redirections Frontend

1. **Utilisateur Regular :**
   - Se connecter via `/login`
   - Devrait être redirigé vers `/dashboard`
   - Tenter d'accéder à `/admin/dashboard`
   - Devrait être redirigé vers `/` (home)

2. **Administrateur :**
   - Se connecter via `/admin/login`
   - Devrait être redirigé vers `/admin/dashboard`
   - Peut accéder à toutes les routes `/admin/*`
   - Peut aussi accéder aux routes user (`/dashboard`, `/devices`, etc.)

---

## 📊 Matrice de Permissions

### API Endpoints

| Endpoint | Public | User | Admin |
|----------|--------|------|-------|
| `POST /auth/register/` | ✅ | ✅ | ✅ |
| `POST /auth/login/` | ✅ | ✅ | ✅ |
| `GET /auth/profile/` | ❌ | ✅ | ✅ |
| `GET /users/` | ❌ | ❌ | ✅ |
| `GET /users/{id}/` | ❌ | ✅ (si owner) | ✅ |
| `PUT /users/{id}/` | ❌ | ✅ (si owner) | ✅ |
| `DELETE /users/{id}/` | ❌ | ✅ (si owner) | ✅ |
| `GET /devices/` | ❌ | ✅ (ses devices) | ✅ (tous) |
| `GET /sessions/` | ❌ | ✅ (ses sessions) | ✅ (toutes) |
| `GET /vouchers/` | ❌ | ❌ | ✅ |

### Pages Frontend

| Page | Public | User | Admin |
|------|--------|------|-------|
| `/` (Home) | ✅ | ✅ | ✅ |
| `/login` | ✅ | ❌ | ❌ |
| `/register` | ✅ | ❌ | ❌ |
| `/dashboard` | ❌ | ✅ | ✅ |
| `/devices` | ❌ | ✅ | ✅ |
| `/sessions` | ❌ | ✅ | ✅ |
| `/profile` | ❌ | ✅ | ✅ |
| `/admin/dashboard` | ❌ | ❌ | ✅ |
| `/admin/users` | ❌ | ❌ | ✅ |
| `/admin/monitoring` | ❌ | ❌ | ✅ |

---

## 🔧 Dépannage

### Problème : Utilisateur ne peut pas se connecter

**Diagnostic :**
```bash
cd backend
python diagnose_admin.py
```

**Vérifications :**
- ✅ Utilisateur existe
- ✅ `is_active = True`
- ✅ Role assigné correctement
- ✅ Mot de passe correct

### Problème : Rôle ne se synchronise pas

**Solution :**
```python
from core.models import User, Role

user = User.objects.get(username='john_doe')
user.is_staff = True
user.save()  # Force la synchronisation via le signal
```

### Problème : Migration échoue

**Erreur possible :** `Role matching query does not exist`

**Solution :**
1. Supprimer les migrations récentes :
   ```bash
   cd backend/core/migrations
   # Supprimer 000X_role_*.py
   ```

2. Recréer les migrations :
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. Créer les rôles manuellement (voir Étape 2)

### Problème : Frontend ne redirige pas correctement

**Vérifications :**
1. Le backend retourne bien `role_name` dans la réponse :
   ```bash
   curl -X POST http://localhost:8000/api/core/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"password"}'
   # Vérifier que "role_name": "admin" est présent
   ```

2. Le frontend stocke bien les données :
   ```javascript
   // Dans la console du navigateur
   console.log(localStorage.getItem('user'))
   // Doit contenir role_name
   ```

3. Vider le cache et localStorage :
   ```javascript
   localStorage.clear()
   // Puis se reconnecter
   ```

---

## 📚 Fichiers Importants

### Backend

| Fichier | Description |
|---------|-------------|
| `core/models.py` | Modèles Role et User |
| `core/signals.py` | Synchronisation automatique des rôles |
| `core/permissions.py` | Permissions DRF personnalisées |
| `core/decorators.py` | Décorateurs pour vues Django |
| `core/serializers.py` | Serializers incluant role_name |
| `core/viewsets.py` | ViewSets avec permissions |
| `core/apps.py` | Enregistrement des signals |
| `setup_roles.py` | Script d'installation |

### Frontend

| Fichier | Description |
|---------|-------------|
| `src/types/index.ts` | Types TypeScript (User) |
| `src/stores/auth.ts` | Store Pinia (isAdmin, userRole) |
| `src/router/index.ts` | Vue Router avec guards |
| `src/views/AdminLoginView.vue` | Page de connexion admin |
| `src/views/LoginView.vue` | Page de connexion user |

---

## 🎯 Bonnes Pratiques

### Sécurité

1. ✅ **Toujours vérifier les permissions côté backend**
   - Le frontend peut être contourné
   - Le backend est la seule source de vérité

2. ✅ **Utiliser les permissions DRF dans les ViewSets**
   ```python
   permission_classes = [IsAdmin]  # Jamais de trust du frontend
   ```

3. ✅ **Filtrer les querysets selon le rôle**
   ```python
   def get_queryset(self):
       if self.request.user.is_admin():
           return Model.objects.all()
       return Model.objects.filter(user=self.request.user)
   ```

4. ✅ **Ne jamais exposer is_staff/is_superuser en écriture**
   ```python
   read_only_fields = ['is_staff', 'is_superuser', 'role']
   ```

### Performance

1. ✅ **Utiliser select_related pour optimiser les requêtes**
   ```python
   User.objects.select_related('role').all()
   ```

2. ✅ **Cacher les permissions dans le frontend**
   ```typescript
   const isAdmin = computed(() => ...)  // Computed property
   ```

### Extensibilité

1. ✅ **Ajouter de nouveaux rôles facilement**
   ```python
   # Dans models.py
   ROLE_CHOICES = [
       ('admin', 'Administrator'),
       ('user', 'User'),
       ('moderator', 'Moderator'),  # Nouveau rôle
   ]
   ```

2. ✅ **Créer des permissions réutilisables**
   ```python
   class IsModeratorOrAdmin(permissions.BasePermission):
       def has_permission(self, request, view):
           return request.user.get_role_name() in ['admin', 'moderator']
   ```

---

## 📞 Support

Pour toute question ou problème :

1. Consulter la section **Dépannage**
2. Vérifier les logs du backend
3. Vérifier la console du navigateur (F12)
4. Exécuter `python diagnose_admin.py`
5. Consulter `ADMIN_AUTH_FIX.md` pour les problèmes d'authentification

---

**Version:** 1.0.0
**Date:** 2025-11-21
**Auteur:** Claude Code Assistant
**Projet:** UCAC-ICAM Portail Captif
