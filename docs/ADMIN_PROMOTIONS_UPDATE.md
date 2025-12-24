# Modifications AdminPromotionsView.vue

## 1. Script: Ajouter après la ligne 25 (après isActivating)

```typescript
const expandedPromotion = ref<number | null>(null)
const promotionUsers = ref<any[]>([])
const isLoadingUsers = ref(false)
```

## 2. Script: Ajouter cette fonction après handleDeactivatePromotionUsers

```typescript
async function togglePromotionExpand(promotion: Promotion) {
  if (expandedPromotion.value === promotion.id) {
    // Fermer si déjà ouvert
    expandedPromotion.value = null
    promotionUsers.value = []
  } else {
    // Ouvrir et charger les utilisateurs
    expandedPromotion.value = promotion.id
    isLoadingUsers.value = true
    try {
      const data = await promotionStore.getPromotionUsers(promotion.id)
      promotionUsers.value = data.users || []
    } catch (error: any) {
      notificationStore.error('Erreur lors du chargement des utilisateurs')
      console.error(error)
    } finally {
      isLoadingUsers.value = false
    }
  }
}
```

## 3. Template: Remplacer la rangée du tableau (ligne 309 à 391)

Ajouter après chaque </tr> principal :

```vue
<!-- Rangée principale -->
<tr v-for="promotion in filteredPromotions" :key="promotion.id"
    @click="togglePromotionExpand(promotion)"
    class="cursor-pointer hover:bg-gray-50">
  <!-- ... contenu existant ... -->
</tr>

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
      <h4>Utilisateurs de la promotion {{ promotion.name }} ({{ promotionUsers.length }})</h4>

      <div class="users-grid">
        <div v-for="user in promotionUsers" :key="user.id" class="user-card">
          <div class="user-avatar">
            {{ user.first_name?.charAt(0) || 'U' }}{{ user.last_name?.charAt(0) || '?' }}
          </div>

          <div class="user-info">
            <div class="user-name">{{ user.first_name }} {{ user.last_name }}</div>
            <div class="user-username">@{{ user.username }}</div>
            <div v-if="user.matricule" class="user-matricule">{{ user.matricule }}</div>
          </div>

          <div class="user-status">
            <span v-if="user.can_access_radius" class="status-badge active">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Accès WiFi actif
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

## 4. Styles: Ajouter à la fin du <style scoped>

```css
/* Rangée déroulable */
.cursor-pointer {
  cursor: pointer;
}

.expanded-row {
  background: #F9FAFB;
}

.users-container {
  padding: 2rem;
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

.users-list h4 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #1F2937;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #E5E7EB;
}

.users-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  transition: all 0.2s;
}

.user-card:hover {
  border-color: #F97316;
  box-shadow: 0 2px 8px rgba(249, 115, 22, 0.1);
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: #1F2937;
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-username {
  font-size: 0.75rem;
  color: #6B7280;
  margin-top: 0.125rem;
}

.user-matricule {
  font-size: 0.75rem;
  color: #9CA3AF;
  margin-top: 0.125rem;
}

.user-status {
  flex-shrink: 0;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge svg {
  width: 14px;
  height: 14px;
}

.status-badge.active {
  background: #D1FAE5;
  color: #10B981;
}

.status-badge.inactive {
  background: #FEE2E2;
  color: #DC2626;
}
```
