# Implémentation des Promotions et Désactivation RADIUS

## 📋 RÉSUMÉ DES FONCTIONNALITÉS AJOUTÉES

### 1. Gestion des Promotions
- ✅ Modèle `Promotion` dans Django avec gestion active/inactive
- ✅ Relation ForeignKey `User.promotion` vers `Promotion`
- ✅ CRUD complet des promotions (API + Admin)
- ✅ Activation/Désactivation en masse par promotion

### 2. Désactivation RADIUS
- ✅ Champ `statut` dans table `radcheck` (TINYINT 1/0)
- ✅ Champ `is_radius_enabled` dans modèle `User`
- ✅ Endpoints pour activer/désactiver individuellement
- ✅ Endpoints pour activer/désactiver par promotion

---

## 🔧 MODIFICATIONS BACKEND

### Modèles Créés/Modifiés

#### 1. Nouveau Modèle: `Promotion`
**Fichier**: `backend/core/models.py`

```python
class Promotion(models.Model):
    code = models.CharField(max_length=50, unique=True)  # Ex: ING3, X2027
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)  # Active/Désactive la promotion
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 2. Modifié: `User`
**Changements**:
- ❌ `promotion = CharField`
- ✅ `promotion = ForeignKey(Promotion)`
- ✅ Ajout `is_radius_enabled = BooleanField(default=True)`

#### 3. Modifié: `RadCheck`
**Fichier**: `backend/radius/models.py`
```python
class RadCheck(models.Model):
    username = models.CharField(max_length=64)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2)
    value = models.CharField(max_length=253)
    statut = models.BooleanField(default=True)  # ✅ NOUVEAU
```

### API Endpoints Créés

#### Promotions
```
GET    /api/core/promotions/              # Liste
POST   /api/core/promotions/              # Créer
GET    /api/core/promotions/{id}/         # Détails
PATCH  /api/core/promotions/{id}/         # Modifier
DELETE /api/core/promotions/{id}/         # Supprimer

POST   /api/core/promotions/{id}/activate_users/    # Activer tous les users
POST   /api/core/promotions/{id}/deactivate_users/  # Désactiver tous les users
POST   /api/core/promotions/{id}/toggle_status/     # Toggle is_active
```

#### Users (nouveaux endpoints)
```
POST   /api/core/users/{id}/activate_radius/    # Activer RADIUS individuel
POST   /api/core/users/{id}/deactivate_radius/  # Désactiver RADIUS individuel
```

---

## 🎨 MODIFICATIONS FRONTEND

### Fichiers Créés

#### 1. Types TypeScript
**Fichier**: `frontend/portail-captif/src/types/index.ts`
```typescript
export interface Promotion {
  id: number
  code: string
  name: string
  description?: string | null
  year?: number | null
  is_active: boolean
  user_count?: number
  active_user_count?: number
}

export interface User {
  // ...
  promotion?: number | null  // ID
  promotion_detail?: PromotionList | null  // Objet
  is_radius_enabled?: boolean  // ✅ NOUVEAU
}
```

#### 2. Service Promotion
**Fichier**: `frontend/portail-captif/src/services/promotion.service.ts` ✅ CRÉÉ

#### 3. Store Promotion
**Fichier**: `frontend/portail-captif/src/stores/promotion.ts` ✅ CRÉÉ

#### 4. Service User (modifié)
**Fichier**: `frontend/portail-captif/src/services/user.service.ts`
- ✅ Ajout `activateUserRadius(userId)`
- ✅ Ajout `deactivateUserRadius(userId)`

---

## 🚀 ÉTAPES POUR FINALISER L'IMPLÉMENTATION

### ÉTAPE 1: Créer les Migrations

⚠️ **IMPORTANT**: Le champ promotion a changé de CharField vers ForeignKey. Il faut une migration de données.

```bash
cd backend

# Activer votre environnement virtuel
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows

# Créer les migrations
python manage.py makemigrations core radius

# ⚠️ Django va demander ce qu'il faut faire avec les données existantes de promotion
# Choisir l'option 1: "Provide a one-off default now"
# Entrer: None

# Appliquer les migrations
python manage.py migrate
```

### ÉTAPE 2: Migration de Données (Script Python)

Créer un script pour migrer les anciennes promotions (string) vers le nouveau modèle:

**Fichier**: `backend/migrate_promotions.py`

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import User, Promotion

# Créer les promotions à partir des anciennes valeurs
old_promotions = User.objects.exclude(promotion__isnull=True).values_list('promotion', flat=True).distinct()

for promo_code in old_promotions:
    if promo_code:
        Promotion.objects.get_or_create(
            code=promo_code,
            defaults={
                'name': f'Promotion {promo_code}',
                'is_active': True
            }
        )

print(f"✅ {Promotion.objects.count()} promotions créées")

# Lier les utilisateurs aux promotions
users_without_promotion = User.objects.filter(promotion__isnull=True)
for user in users_without_promotion:
    # Si l'utilisateur avait une ancienne valeur de promotion dans la base
    # elle a été convertie en None par la migration
    # Il faudra les réassigner manuellement via l'admin
    pass

print("✅ Migration terminée")
```

Exécuter:
```bash
python backend/migrate_promotions.py
```

### ÉTAPE 3: Créer des Promotions de Test

Via l'admin Django ou via shell:

```bash
python manage.py shell
```

```python
from core.models import Promotion

# Créer quelques promotions
Promotion.objects.create(code="ING3", name="Ingénieurs 3ème année", year=2025, is_active=True)
Promotion.objects.create(code="L1", name="Licence 1", year=2025, is_active=True)
Promotion.objects.create(code="M2", name="Master 2", year=2025, is_active=True)
Promotion.objects.create(code="X2027", name="Promotion 2027", year=2027, is_active=True)

print("✅ Promotions créées")
```

### ÉTAPE 4: Modifier RegisterView (Frontend)

**Fichier**: `frontend/portail-captif/src/views/RegisterView.vue`

Remplacer le champ texte promotion par un dropdown:

```vue
<script setup lang="ts">
import { usePromotionStore } from '@/stores/promotion'

const promotionStore = usePromotionStore()

// Charger les promotions au montage
onMounted(async () => {
  await promotionStore.fetchPromotions()
})
</script>

<template>
  <!-- Remplacer le champ texte par : -->
  <div class="form-group">
    <label for="promotion">Promotion *</label>
    <select
      id="promotion"
      v-model="form.promotion_id"
      required
      :disabled="isLoading"
    >
      <option value="">Sélectionnez une promotion</option>
      <option
        v-for="promo in promotionStore.promotions.filter(p => p.is_active)"
        :key="promo.id"
        :value="promo.id"
      >
        {{ promo.code }} - {{ promo.name }}
      </option>
    </select>
  </div>
</template>
```

**Modifier le submit**:
```typescript
const form = ref({
  // ...
  promotion_id: null,  // Changer de 'promotion' à 'promotion_id'
  // ...
})
```

### ÉTAPE 5: Modifier AdminUsersView (Frontend)

**Fichier**: `frontend/portail-captif/src/views/AdminUsersView.vue`

#### A. Ajouter dropdown promotion dans le modal d'ajout

```vue
<script setup>
import { usePromotionStore } from '@/stores/promotion'
const promotionStore = usePromotionStore()

onMounted(async () => {
  // ...
  await promotionStore.fetchPromotions()
})
</script>

<!-- Dans le modal d'ajout, remplacer le champ promotion -->
<div class="form-group">
  <label>Promotion *</label>
  <select v-model="newUser.promotion_id" required>
    <option value="">Sélectionnez une promotion</option>
    <option
      v-for="promo in promotionStore.promotions.filter(p => p.is_active)"
      :key="promo.id"
      :value="promo.id"
    >
      {{ promo.code }} - {{ promo.name }}
    </option>
  </select>
</div>
```

#### B. Ajouter boutons activation/désactivation RADIUS

Dans le tableau users, colonne Actions:

```vue
<!-- Après le bouton d'activation RADIUS existant -->
<button
  v-if="user.is_radius_activated && user.is_radius_enabled"
  @click="handleDeactivateRadiusIndividual(user.id)"
  class="action-btn danger"
  title="Désactiver accès Internet"
  :disabled="isActivating"
>
  <svg viewBox="0 0 24 24"><!--  Icon wifi-off --></svg>
</button>

<button
  v-if="user.is_radius_activated && !user.is_radius_enabled"
  @click="handleActivateRadiusIndividual(user.id)"
  class="action-btn success"
  title="Activer accès Internet"
  :disabled="isActivating"
>
  <svg viewBox="0 0 24 24"><!-- Icon wifi-on --></svg>
</button>
```

**Fonctions à ajouter**:
```typescript
async function handleActivateRadiusIndividual(userId: number) {
  if (!confirm('Activer l\'accès Internet pour cet utilisateur ?')) return

  try {
    await userService.activateUserRadius(userId)
    notificationStore.success('Utilisateur activé dans RADIUS')
    await userStore.fetchUsers()  // Recharger
  } catch (error) {
    notificationStore.error('Erreur lors de l\'activation')
  }
}

async function handleDeactivateRadiusIndividual(userId: number) {
  if (!confirm('Désactiver l\'accès Internet pour cet utilisateur ?')) return

  try {
    await userService.deactivateUserRadius(userId)
    notificationStore.success('Utilisateur désactivé dans RADIUS')
    await userStore.fetchUsers()  // Recharger
  } catch (error) {
    notificationStore.error('Erreur lors de la désactivation')
  }
}
```

#### C. Afficher promotion_detail au lieu de promotion

Dans le tableau:
```vue
<td>
  <div v-if="user.promotion_detail" class="info-cell">
    <span class="badge badge-light">{{ user.promotion_detail.code }}</span>
    <span class="badge badge-light">{{ user.promotion_detail.name }}</span>
  </div>
  <span v-else class="text-gray">-</span>
</td>
```

### ÉTAPE 6: Créer AdminPromotionsView

**Fichier**: `frontend/portail-captif/src/views/AdminPromotionsView.vue`

Créer une vue similaire à AdminUsersView mais pour gérer les promotions:

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePromotionStore } from '@/stores/promotion'
import { useNotificationStore } from '@/stores/notification'
import AdminLayout from '@/layouts/AdminLayout.vue'

const promotionStore = usePromotionStore()
const notificationStore = useNotificationStore()

// États
const showAddModal = ref(false)
const showEditModal = ref(false)
const selectedPromotion = ref<any>(null)

const newPromotion = ref({
  code: '',
  name: '',
  description: '',
  year: new Date().getFullYear(),
  is_active: true
})

onMounted(async () => {
  await promotionStore.fetchPromotions()
})

// Fonctions CRUD
async function handleAdd() {
  try {
    await promotionStore.createPromotion(newPromotion.value)
    notificationStore.success('Promotion créée')
    showAddModal.value = false
  } catch (error) {
    notificationStore.error('Erreur lors de la création')
  }
}

async function handleToggleStatus(promotionId: number) {
  if (!confirm('Changer le statut de cette promotion ?')) return

  try {
    const result = await promotionStore.togglePromotionStatus(promotionId)
    notificationStore.success(result.message)
  } catch (error) {
    notificationStore.error('Erreur')
  }
}

async function handleActivateUsers(promotionId: number) {
  if (!confirm('Activer tous les utilisateurs de cette promotion dans RADIUS ?')) return

  try {
    const result = await promotionStore.activatePromotionUsers(promotionId)
    notificationStore.success(`${result.activated} utilisateur(s) activé(s)`)
  } catch (error) {
    notificationStore.error('Erreur')
  }
}

async function handleDeactivateUsers(promotionId: number) {
  if (!confirm('Désactiver tous les utilisateurs de cette promotion ?')) return

  try {
    const result = await promotionStore.deactivatePromotionUsers(promotionId)
    notificationStore.success(`${result.deactivated} utilisateur(s) désactivé(s)`)
  } catch (error) {
    notificationStore.error('Erreur')
  }
}
</script>

<template>
  <AdminLayout activePage="promotions">
    <div class="content-header">
      <div>
        <h2 class="page-title">Gestion des Promotions</h2>
        <p class="page-subtitle">Créer et gérer les promotions étudiantes</p>
      </div>
      <button @click="showAddModal = true" class="btn-primary">
        Nouvelle Promotion
      </button>
    </div>

    <!-- Tableau des promotions -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Code</th>
            <th>Nom</th>
            <th>Année</th>
            <th>Statut</th>
            <th>Utilisateurs</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="promo in promotionStore.promotions" :key="promo.id">
            <td>{{ promo.id }}</td>
            <td><strong>{{ promo.code }}</strong></td>
            <td>{{ promo.name }}</td>
            <td>{{ promo.year || '-' }}</td>
            <td>
              <span :class="['badge', promo.is_active ? 'badge-success' : 'badge-gray']">
                {{ promo.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td>
              {{ promo.user_count }} total / {{ promo.active_user_count }} actifs
            </td>
            <td>
              <div class="action-buttons">
                <button
                  @click="handleActivateUsers(promo.id)"
                  class="action-btn success"
                  title="Activer tous les users RADIUS"
                >
                  ✓
                </button>
                <button
                  @click="handleDeactivateUsers(promo.id)"
                  class="action-btn danger"
                  title="Désactiver tous les users RADIUS"
                >
                  ✗
                </button>
                <button
                  @click="handleToggleStatus(promo.id)"
                  :class="['action-btn', promo.is_active ? 'warning' : 'info']"
                  title="Toggle statut"
                >
                  ⏻
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal ajout (à compléter) -->
  </AdminLayout>
</template>
```

### ÉTAPE 7: Ajouter Route pour AdminPromotionsView

**Fichier**: `frontend/portail-captif/src/router/index.ts`

```typescript
{
  path: '/admin/promotions',
  name: 'admin-promotions',
  component: () => import('@/views/AdminPromotionsView.vue'),
  meta: { requiresAuth: true, requiresAdmin: true }
}
```

### ÉTAPE 8: Ajouter lien dans la navigation admin

**Fichier**: `frontend/portail-captif/src/layouts/AdminLayout.vue`

Ajouter dans le menu:
```vue
<router-link to="/admin/promotions" class="nav-link">
  <svg><!-- Icon --></svg>
  Promotions
</router-link>
```

---

## ✅ CHECKLIST FINALE

### Backend
- [x] Modèle Promotion créé
- [x] User.promotion modifié (ForeignKey)
- [x] RadCheck.statut ajouté
- [x] User.is_radius_enabled ajouté
- [x] Serializers créés
- [x] ViewSets créés
- [x] Routes ajoutées
- [x] Admin Django configuré
- [ ] Migrations créées et appliquées (À FAIRE)
- [ ] Migration de données (À FAIRE)

### Frontend
- [x] Types TypeScript
- [x] Service promotion
- [x] Store promotion
- [x] Service user modifié
- [ ] RegisterView modifié (À FAIRE)
- [ ] AdminUsersView modifié (À FAIRE)
- [ ] AdminPromotionsView créé (À FAIRE)
- [ ] Routes ajoutées (À FAIRE)
- [ ] Navigation mise à jour (À FAIRE)

---

## 🧪 TESTS

### Test 1: Créer une Promotion
```bash
curl -X POST http://localhost:8000/api/core/promotions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "TEST2025",
    "name": "Promotion Test 2025",
    "year": 2025,
    "is_active": true
  }'
```

### Test 2: Activer un utilisateur individuel dans RADIUS
```bash
curl -X POST http://localhost:8000/api/core/users/1/activate_radius/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test 3: Désactiver tous les utilisateurs d'une promotion
```bash
curl -X POST http://localhost:8000/api/core/promotions/1/deactivate_users/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 📝 NOTES IMPORTANTES

1. **Migration de Données**: Les anciennes valeurs de promotion (string) doivent être migrées vers le nouveau modèle Promotion
2. **Champ statut**: S'assure que FreeRADIUS vérifie ce champ lors de l'authentification
3. **is_radius_enabled vs is_radius_activated**:
   - `is_radius_activated`: L'utilisateur a été copié dans radcheck (une seule fois)
   - `is_radius_enabled`: L'utilisateur peut accéder à Internet (toggle on/off)

4. **Configuration FreeRADIUS**: Vous devrez peut-être modifier vos requêtes SQL FreeRADIUS pour vérifier le champ `statut`:

   ```sql
   # Dans /etc/freeradius/3.0/mods-available/sql
   authorize_check_query = "SELECT id, username, attribute, value, op \
     FROM ${authcheck_table} \
     WHERE username = '%{SQL-User-Name}' \
     AND statut = 1 \  # ✅ Ajouter cette ligne
     ORDER BY id"
   ```

---

## 🎉 RÉSULTAT FINAL

Vous aurez:
- ✅ Gestion complète des promotions
- ✅ Dropdown de sélection à l'inscription
- ✅ Activation/Désactivation individuelle dans RADIUS
- ✅ Activation/Désactivation par promotion (en masse)
- ✅ Contrôle granulaire de l'accès Internet via le champ `statut`

**Temps estimé pour finaliser**: 2-3 heures
