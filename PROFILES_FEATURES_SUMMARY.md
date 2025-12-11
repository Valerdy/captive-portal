# 📊 Récapitulatif des fonctionnalités de profils

## ✅ Fonctionnalités déjà implémentées

### 1. **Assigner un profil à une promotion** ✅ COMPLET

**Backend:**
- ✅ Modèle `Promotion` a le champ `profile` (ForeignKey vers Profile)
- ✅ Serializer expose `profile` et `profile_name`
- ✅ API `/api/core/promotions/` supporte le champ profile

**Frontend:**
- ✅ `AdminPromotionsView.vue` a le profileStore importé
- ✅ Sélecteur de profil dans la modal d'ajout (ligne 540-551)
- ✅ Sélecteur de profil dans la modal d'édition (ligne 596-608)
- ✅ Affiche les informations du profil (quota, bande passante)

**Utilisation:**
1. Aller dans **Admin > Promotions**
2. Créer/éditer une promotion
3. Sélectionner un profil dans la liste déroulante
4. Tous les utilisateurs de cette promotion hériteront de ce profil

---

### 2. **Profil individuel utilisateur** ✅ BACKEND OK, ❌ FRONTEND À AJOUTER

**Backend:**
- ✅ Modèle `User` a le champ `profile` (ForeignKey vers Profile)
- ✅ Méthode `get_effective_profile()` gère la priorité: profil user > profil promotion
- ✅ Serializer expose `profile`, `profile_name`, et `effective_profile`
- ✅ API `/api/core/users/` supporte le champ profile

**Frontend:**
- ❌ `AdminUsersView.vue` n'a PAS encore de sélecteur de profil
- ❌ Il faut ajouter le profileStore
- ❌ Il faut ajouter le champ profile à newUser
- ❌ Il faut ajouter le sélecteur dans les modals

**À implémenter:** Voir section "Modifications à apporter" ci-dessous

---

### 3. **Bande passante en Mbps** ✅ COMPLET

**Backend:**
- ✅ Modèle `Profile.bandwidth_upload` et `bandwidth_download` stockent en **Mbps** (changé de Kbps)
- ✅ Valeurs par défaut: 5 Mbps upload, 10 Mbps download
- ✅ Code d'activation RADIUS utilise directement les Mbps
- ✅ Format Mikrotik: `"5M/10M"` généré correctement

**Frontend:**
- ✅ Labels changés de "Kbps" en "Mbps"
- ✅ Valeurs par défaut ajustées (5 au lieu de 5120)
- ✅ Input step changé de 128 à 1
- ✅ Affichage: `{{ bandwidth }} Mbps`

**Migration:**
- ✅ Migration créée: `0002_convert_bandwidth_kbps_to_mbps.py`
- ⚠️ **À EXÉCUTER:** `python manage.py migrate`

---

## 🔧 Modifications à apporter

### Ajouter le sélecteur de profil dans AdminUsersView.vue

#### Étape 1: Importer le profileStore

```typescript
// Ligne 6, après usePromotionStore
import { useProfileStore } from '@/stores/profile'

// Ligne 16, après promotionStore
const profileStore = useProfileStore()
```

#### Étape 2: Ajouter profiles computed

```typescript
// Après const promotions = computed(...)
const profiles = computed(() => {
  if (!Array.isArray(profileStore.profiles)) return []
  return profileStore.profiles.filter(p => p && p.is_active)
})
```

#### Étape 3: Charger les profils dans onMounted

```typescript
onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    await Promise.all([
      userStore.fetchUsers(),
      promotionStore.fetchPromotions(),
      profileStore.fetchProfiles()  // AJOUTER CETTE LIGNE
    ])
  } catch (error: any) {
    // ...
  }
})
```

#### Étape 4: Ajouter profile à newUser

```typescript
const newUser = ref({
  password: '',
  password2: '',
  first_name: '',
  last_name: '',
  promotion: '' as number | string,
  profile: '' as number | string,  // AJOUTER CETTE LIGNE
  matricule: '',
  is_staff: false
})
```

#### Étape 5: Ajouter dans openAddModal

```typescript
function openAddModal() {
  newUser.value = {
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
    promotion: '',
    profile: '',  // AJOUTER CETTE LIGNE
    matricule: '',
    is_staff: false
  }
  showAddModal.value = true
}
```

#### Étape 6: Ajouter dans handleAddUser

```typescript
async function handleAddUser() {
  // Validation existante...

  try {
    const userData: any = {
      first_name: newUser.value.first_name,
      last_name: newUser.value.last_name,
      promotion: Number(newUser.value.promotion),
      matricule: newUser.value.matricule,
      password: newUser.value.password,
      password2: newUser.value.password2,
      is_staff: newUser.value.is_staff
    }

    // Ajouter le profil seulement s'il est sélectionné
    if (newUser.value.profile) {
      userData.profile = Number(newUser.value.profile)  // AJOUTER CES LIGNES
    }

    await userStore.createUser(userData)
    // ...
  }
}
```

#### Étape 7: Ajouter le sélecteur dans le HTML (modal d'ajout)

Ajouter après le champ Promotion (ligne ~807):

```html
<div class="form-group">
  <label>Profil RADIUS (optionnel)</label>
  <select v-model="newUser.profile">
    <option value="">Utiliser le profil de la promotion</option>
    <option v-for="profile in profiles" :key="profile.id" :value="profile.id">
      {{ profile.name }}
      ({{ profile.quota_type === 'limited' ? profile.data_volume_gb + ' Go' : 'Illimité' }})
    </option>
  </select>
  <small class="form-help">
    Si non défini, l'utilisateur héritera du profil de sa promotion
  </small>
</div>
```

#### Étape 8: Ajouter le sélecteur dans la modal d'édition

De même pour `selectedUser` dans la modal d'édition.

---

## 🎯 Hiérarchie des profils

La méthode `get_effective_profile()` gère automatiquement la priorité:

```
1. Profil individuel utilisateur (si défini)
   ⬇️
2. Profil de la promotion (si défini)
   ⬇️
3. None (pas de profil)
```

**Exemple:**
- Utilisateur `John` est dans la promotion `L3 Info`
- Promotion `L3 Info` a le profil `Étudiant Standard` (10 Go, 5/10 Mbps)
- Si on assigne le profil `VIP` directement à John
- ✅ John aura le profil `VIP` (priorité au profil individuel)
- ✅ Les autres utilisateurs de `L3 Info` auront `Étudiant Standard`

---

## 🚀 Activation RADIUS avec profils

Quand un utilisateur ou une promotion est activé(e):

1. Le système récupère le profil effectif via `user.get_effective_profile()`
2. Les paramètres RADIUS sont créés selon le profil:
   - **radcheck:** `Cleartext-Password`, `ChilliSpot-Max-Total-Octets` (si quota limité)
   - **radreply:** `Session-Timeout`, `Idle-Timeout`, `Mikrotik-Rate-Limit`
   - **radusergroup:** Affectation au groupe

3. Format de la bande passante:
   - Profil stocke: `bandwidth_upload=5`, `bandwidth_download=10` (en Mbps)
   - RADIUS reçoit: `Mikrotik-Rate-Limit = "5M/10M"`

---

## 📋 Migration à exécuter

Une migration a été créée pour convertir les données existantes de Kbps vers Mbps:

```bash
cd /home/user/captive-portal/backend
python manage.py migrate core 0002_convert_bandwidth_kbps_to_mbps
```

Cette migration:
- ✅ Divise toutes les valeurs existantes par 1024
- ✅ Exemple: 5120 Kbps → 5 Mbps, 10240 Kbps → 10 Mbps
- ✅ Réversible (rollback possible)
- ✅ Minimum de 1 Mbps garanti

---

## 🧪 Tests à effectuer après modifications

### Test 1: Profil sur promotion
1. Créer un profil "Test Student" (10 Mbps up/down, 50 Go)
2. Créer une promotion "Test Promo" avec ce profil
3. Créer un utilisateur dans cette promotion
4. Activer la promotion
5. Vérifier dans radreply: `Mikrotik-Rate-Limit = "10M/10M"`

### Test 2: Profil sur utilisateur (override)
1. Créer un profil "Test VIP" (50 Mbps up/down, illimité)
2. Assigner ce profil à un utilisateur spécifique
3. Activer l'utilisateur
4. Vérifier dans radreply: `Mikrotik-Rate-Limit = "50M/50M"`

### Test 3: Bande passante en Mbps
1. Créer un profil avec 15 Mbps upload, 25 Mbps download
2. Assigner à un utilisateur et activer
3. Vérifier dans radreply: `Mikrotik-Rate-Limit = "15M/25M"`

---

## 📊 État actuel

| Fonctionnalité | Backend | Frontend | Testé |
|----------------|---------|----------|-------|
| Profil sur promotion | ✅ | ✅ | ⚠️ |
| Profil sur utilisateur | ✅ | ❌ | ❌ |
| Bande passante Mbps | ✅ | ✅ | ⚠️ |
| Migration Kbps→Mbps | ✅ | - | ❌ |
| get_effective_profile() | ✅ | - | ⚠️ |
| Activation RADIUS avec profils | ✅ | - | ⚠️ |

**Légende:**
- ✅ Implémenté
- ❌ Pas implémenté
- ⚠️ À tester

---

## 📝 Prochaines étapes

1. ✅ **Exécuter la migration** (obligatoire avant test)
   ```bash
   python manage.py migrate
   ```

2. ⚠️ **Ajouter le sélecteur de profil dans AdminUsersView** (optionnel mais recommandé)
   - Suivre les étapes de la section "Modifications à apporter"

3. ✅ **Tester les fonctionnalités**
   - Suivre les tests de la section "Tests à effectuer"

4. ✅ **Commit et push**
   - Une fois les tests validés

---

## 💡 Notes importantes

- Le champ `profile` est **optionnel** sur User et Promotion
- Si aucun profil n'est défini, les valeurs par défaut sont utilisées
- La méthode `get_effective_profile()` retourne `None` si aucun profil n'est défini
- Le code d'activation gère correctement le cas `profile = None` avec des valeurs par défaut
- Les profils inactifs (`is_active=False`) ne sont pas affichés dans les sélecteurs
