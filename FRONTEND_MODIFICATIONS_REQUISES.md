# Modifications pour AdminPromotionsView.vue

## MODIFICATIONS REQUISES

### 1. Dans <script setup>, après la ligne 25 (après `const isActivating = ref(false)`), ajouter:

```typescript
const expandedPromotion = ref<number | null>(null)
const promotionUsers = ref<any[]>([])
const isLoadingUsers = ref(false)
```

### 2. Après la fonction `handleDeactivatePromotionUsers` (ligne ~218), ajouter:

```typescript
async function togglePromotionExpand(promotion: Promotion) {
  if (expandedPromotion.value === promotion.id) {
    expandedPromotion.value = null
    promotionUsers.value = []
  } else {
    expandedPromotion.value = promotion.id
    isLoadingUsers.value = true
    try {
      const data = await promotionStore.getPromotionUsers(promotion.id)
      promotionUsers.value = data.users || []
    } catch (error: any) {
      notificationStore.error('Erreur lors du chargement des utilisateurs')
    } finally {
      isLoadingUsers.value = false
    }
  }
}
```

### 3. Modifier les handlers (lignes 181-218) pour utiliser les VRAIES méthodes:

**REMPLACER:**
```typescript
async function handleActivatePromotionUsers(promotion: Promotion) {
  if (isActivating.value) return

  if (!confirm(`Activer l'accès Internet pour tous les utilisateurs de "${promotion.code}" ?\n\nCela activera ${promotion.user_count || 0} utilisateur(s) dans RADIUS.`)) {
    return
  }

  isActivating.value = true
  try {
    const result = await promotionStore.activatePromotionUsers(promotion.id)
    notificationStore.success(`${result.activated_count || 0} utilisateur(s) activé(s) dans RADIUS`)
    await promotionStore.fetchPromotions()
  } catch (error: any) {
    const message = error?.response?.data?.message || 'Erreur lors de l\'activation'
    notificationStore.error(message)
  } finally {
    isActivating.value = false
  }
}
```

**PAR:**
```typescript
async function handleActivatePromotionUsers(promotion: Promotion) {
  if (isActivating.value) return

  if (!confirm(`Activer l'accès Internet pour TOUS les utilisateurs de "${promotion.name}" ?\n\nCela CRÉERA les entrées RADIUS pour ${promotion.user_count || 0} utilisateur(s).`)) {
    return
  }

  isActivating.value = true
  try {
    const result = await promotionStore.activatePromotionUsers(promotion.id)
    const count = result.users_enabled || 0
    notificationStore.success(`${count} utilisateur(s) créé(s) dans RADIUS`)
    // Recharger les utilisateurs si la promotion est dépliée
    if (expandedPromotion.value === promotion.id) {
      await togglePromotionExpand(promotion)
      await togglePromotionExpand(promotion)
    }
  } catch (error: any) {
    notificationStore.error(error?.response?.data?.message || 'Erreur lors de l\'activation')
  } finally {
    isActivating.value = false
  }
}
```

ET

```typescript
async function handleDeactivatePromotionUsers(promotion: Promotion) {
  if (isActivating.value) return

  if (!confirm(`Désactiver l'accès Internet pour TOUS les utilisateurs de "${promotion.name}" ?\n\nCela SUPPRIMERA les entrées RADIUS pour ${promotion.user_count || 0} utilisateur(s).`)) {
    return
  }

  isActivating.value = true
  try {
    const result = await promotionStore.deactivatePromotionUsers(promotion.id)
    const count = result.users_disabled || 0
    notificationStore.success(`${count} utilisateur(s) supprimé(s) de RADIUS`)
    // Recharger les utilisateurs si la promotion est dépliée
    if (expandedPromotion.value === promotion.id) {
      await togglePromotionExpand(promotion)
      await togglePromotionExpand(promotion)
    }
  } catch (error: any) {
    notificationStore.error(error?.response?.data?.message || 'Erreur lors de la désactivation')
  } finally {
    isActivating.value = false
  }
}
```

### 4. Dans <template>, juste APRÈS chaque balise de fermeture de la rangée principale `</tr>` (ligne 391), ajouter:

```vue
<!-- Rangée déroulable pour les utilisateurs -->
<tr v-if="expandedPromotion === promotion.id" class="expanded-row">
  <td colspan="8" class="users-container">
    <div v-if="isLoadingUsers" class="loading-users">
      <LoadingSpinner />
      <p>Chargement des utilisateurs...</p>
    </div>

    <div v-else-if="promotionUsers.length === 0" class="no-users">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
      </svg>
      <p>Aucun utilisateur dans cette promotion</p>
    </div>

    <div v-else class="users-list">
      <div class="users-header">
        <h4>Utilisateurs de {{ promotion.name }} ({{ promotionUsers.length }})</h4>
      </div>

      <div class="users-grid">
        <div v-for="user in promotionUsers" :key="user.id" class="user-card">
          <div class="user-avatar">
            {{ user.first_name?.charAt(0) || 'U' }}{{ user.last_name?.charAt(0) || '?' }}
          </div>

          <div class="user-info">
            <div class="user-name">{{ user.first_name }} {{ user.last_name }}</div>
            <div class="user-username">@{{ user.username }}</div>
            <div v-if="user.matricule" class="user-matricule">Matricule: {{ user.matricule }}</div>
          </div>

          <div class="user-status">
            <span v-if="user.can_access_radius" class="status-badge active">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              WiFi actif
            </span>
            <span v-else class="status-badge inactive">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              {{ user.radius_status }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </td>
</tr>
```

### 5. Modifier la rangée principale `<tr>` (ligne 309) pour qu'elle soit cliquable:

**REMPLACER:**
```vue
<tr v-for="promotion in filteredPromotions" :key="promotion.id">
```

**PAR:**
```vue
<tr v-for="promotion in filteredPromotions" :key="promotion.id"
    @click="togglePromotionExpand(promotion)"
    class="cursor-pointer"
    :class="{ 'selected': expandedPromotion === promotion.id }">
```

### 6. Dans <style scoped>, à la FIN (avant </style>, ligne 1175), ajouter:

```css
/* Liste déroulable d'utilisateurs */
.cursor-pointer {
  cursor: pointer;
}

.data-table tbody tr.cursor-pointer:hover {
  background: #F3F4F6;
}

.data-table tbody tr.selected {
  background: #FEF3C7;
}

.expanded-row {
  background: #F9FAFB !important;
}

.expanded-row:hover {
  background: #F9FAFB !important;
}

.users-container {
  padding: 2rem !important;
}

.loading-users {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
  color: #6B7280;
}

.no-users {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
  color: #9CA3AF;
}

.no-users svg {
  width: 48px;
  height: 48px;
  color: #D1D5DB;
}

.users-list {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.users-header {
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #E5E7EB;
}

.users-header h4 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #1F2937;
  margin: 0;
}

.users-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  transition: all 0.2s;
}

.user-card:hover {
  border-color: #F97316;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.15);
  transform: translateY(-2px);
}

.user-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: #1F2937;
  font-size: 0.9375rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 0.25rem;
}

.user-username {
  font-size: 0.8125rem;
  color: #6B7280;
  font-family: 'Courier New', monospace;
}

.user-matricule {
  font-size: 0.75rem;
  color: #9CA3AF;
  margin-top: 0.25rem;
}

.user-status {
  flex-shrink: 0;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem;
  border-radius: 8px;
  font-size: 0.8125rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge svg {
  width: 16px;
  height: 16px;
}

.status-badge.active {
  background: #D1FAE5;
  color: #10B981;
  border: 1px solid #A7F3D0;
}

.status-badge.inactive {
  background: #FEE2E2;
  color: #DC2626;
  border: 1px solid #FECACA;
}

@media (max-width: 768px) {
  .users-grid {
    grid-template-columns: 1fr;
  }

  .user-card {
    flex-direction: column;
    text-align: center;
  }

  .user-info {
    width: 100%;
  }

  .user-status {
    width: 100%;
  }

  .status-badge {
    justify-content: center;
  }
}
```

## RÉSUMÉ DES MODIFICATIONS

1. ✅ Backend: Logique activate/deactivate corrigée (CRÉER/SUPPRIMER dans RADIUS)
2. ✅ Frontend Services: Méthodes ajoutées (getUsers, update, delete, etc.)
3. ✅ Frontend Stores: Store complet avec toutes les opérations
4. ⏳ Frontend Vue: À modifier selon les instructions ci-dessus

## TEST

Après modification:
1. Cliquer sur une ligne de promotion → Liste des utilisateurs s'affiche
2. Cliquer sur "Activer" → Crée les entrées RADIUS pour TOUS les utilisateurs
3. Cliquer sur "Désactiver" → Supprime les entrées RADIUS pour TOUS les utilisateurs
4. Les utilisateurs affichent leur statut RADIUS en temps réel

