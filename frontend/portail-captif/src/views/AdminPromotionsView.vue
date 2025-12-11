<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePromotionStore } from '@/stores/promotion'
import { useNotificationStore } from '@/stores/notification'
import AdminLayout from '@/layouts/AdminLayout.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import type { Promotion } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const promotionStore = usePromotionStore()
const notificationStore = useNotificationStore()

const promotions = computed(() => promotionStore.promotions)
const isLoading = computed(() => promotionStore.isLoading)

const showAddModal = ref(false)
const showEditModal = ref(false)
const selectedPromotion = ref<Promotion | null>(null)
const searchQuery = ref('')
const filterStatus = ref('all')
const isDeleting = ref(false)
const isActivating = ref(false)
const expandedPromotion = ref<number | null>(null)
const promotionUsers = ref<any[]>([])
const isLoadingUsers = ref(false)

const newPromotion = ref({
  code: '',
  name: '',
  description: '',
  year: null as number | null,
  is_active: true
})

// Filtrage des promotions
const filteredPromotions = computed(() => {
  let filtered = promotions.value

  // Filtre par recherche
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(p =>
      p.code?.toLowerCase().includes(query) ||
      p.name?.toLowerCase().includes(query) ||
      p.description?.toLowerCase().includes(query) ||
      p.year?.toString().includes(query)
    )
  }

  // Filtre par statut
  if (filterStatus.value !== 'all') {
    if (filterStatus.value === 'active') {
      filtered = filtered.filter(p => p.is_active)
    } else {
      filtered = filtered.filter(p => !p.is_active)
    }
  }

  return filtered
})

// Statistiques
const stats = computed(() => ({
  total: promotions.value.length,
  active: promotions.value.filter(p => p.is_active).length,
  inactive: promotions.value.filter(p => !p.is_active).length,
  total_users: promotions.value.reduce((sum, p) => sum + (p.user_count || 0), 0),
  total_active_users: promotions.value.reduce((sum, p) => sum + (p.active_user_count || 0), 0)
}))

onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    await promotionStore.fetchPromotions()
  } catch (error: any) {
    const message = error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors du chargement: ${message}`)
    console.error('Erreur chargement promotions:', error)
  }
})

function openAddModal() {
  newPromotion.value = {
    code: '',
    name: '',
    description: '',
    year: null,
    is_active: true
  }
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
}

async function handleAddPromotion() {
  // Validation
  if (!newPromotion.value.code || !newPromotion.value.name) {
    notificationStore.warning('Veuillez remplir tous les champs requis')
    return
  }

  try {
    await promotionStore.createPromotion({
      code: newPromotion.value.code,
      name: newPromotion.value.name,
      description: newPromotion.value.description || null,
      year: newPromotion.value.year,
      is_active: newPromotion.value.is_active
    })

    notificationStore.success('Promotion créée avec succès')
    closeAddModal()
  } catch (error) {
    notificationStore.error(promotionStore.error || 'Erreur lors de la création')
  }
}

function handleEdit(promotion: Promotion) {
  selectedPromotion.value = { ...promotion }
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  selectedPromotion.value = null
}

async function handleUpdatePromotion() {
  if (!selectedPromotion.value) return

  try {
    await promotionStore.updatePromotion(selectedPromotion.value.id, {
      code: selectedPromotion.value.code,
      name: selectedPromotion.value.name,
      description: selectedPromotion.value.description,
      year: selectedPromotion.value.year,
      is_active: selectedPromotion.value.is_active
    })

    notificationStore.success('Promotion modifiée avec succès')
    closeEditModal()
  } catch (error) {
    notificationStore.error(promotionStore.error || 'Erreur lors de la modification')
  }
}

async function handleToggleStatus(promotion: Promotion) {
  try {
    await promotionStore.togglePromotionStatus(promotion.id)
    notificationStore.success(`Promotion ${promotion.is_active ? 'désactivée' : 'activée'}`)
  } catch (error) {
    notificationStore.error('Erreur lors de la modification')
  }
}

async function handleDelete(promotion: Promotion) {
  if (isDeleting.value) return

  if (!confirm(`Voulez-vous vraiment supprimer la promotion "${promotion.code}" ?\n\nAttention: Cette action peut affecter ${promotion.user_count || 0} utilisateur(s).`)) {
    return
  }

  isDeleting.value = true
  try {
    await promotionStore.deletePromotion(promotion.id)
    notificationStore.success('Promotion supprimée avec succès')
  } catch (error) {
    notificationStore.error('Erreur lors de la suppression')
  } finally {
    isDeleting.value = false
  }
}

async function handleActivatePromotionUsers(promotion: Promotion) {
  if (isActivating.value) return

  if (!confirm(`Activer l'accès Internet pour tous les utilisateurs de "${promotion.code}" ?\n\nCela activera ${promotion.user_count || 0} utilisateur(s) dans RADIUS.`)) {
    return
  }

  isActivating.value = true
  try {
    const result = await promotionStore.activatePromotionUsers(promotion.id)
    notificationStore.success(`${result.users_enabled || 0} utilisateur(s) activé(s) dans RADIUS`)
    await promotionStore.fetchPromotions() // Rafraîchir pour mettre à jour les compteurs

    // Rafraîchir la liste des utilisateurs si la promotion est ouverte
    if (expandedPromotion.value === promotion.id) {
      const data = await promotionStore.getPromotionUsers(promotion.id)
      promotionUsers.value = data.users || []
    }
  } catch (error: any) {
    const message = error?.response?.data?.message || 'Erreur lors de l\'activation'
    notificationStore.error(message)
  } finally {
    isActivating.value = false
  }
}

async function handleDeactivatePromotionUsers(promotion: Promotion) {
  if (isActivating.value) return

  if (!confirm(`Désactiver l'accès Internet pour tous les utilisateurs de "${promotion.code}" ?\n\nCela désactivera ${promotion.user_count || 0} utilisateur(s) dans RADIUS.`)) {
    return
  }

  isActivating.value = true
  try {
    const result = await promotionStore.deactivatePromotionUsers(promotion.id)
    notificationStore.success(`${result.users_disabled || 0} utilisateur(s) désactivé(s) dans RADIUS`)
    await promotionStore.fetchPromotions() // Rafraîchir pour mettre à jour les compteurs

    // Rafraîchir la liste des utilisateurs si la promotion est ouverte
    if (expandedPromotion.value === promotion.id) {
      const data = await promotionStore.getPromotionUsers(promotion.id)
      promotionUsers.value = data.users || []
    }
  } catch (error: any) {
    const message = error?.response?.data?.message || 'Erreur lors de la désactivation'
    notificationStore.error(message)
  } finally {
    isActivating.value = false
  }
}

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
</script>

<template>
  <AdminLayout activePage="promotions">
    <div class="content-header">
      <div>
        <h2 class="page-title">Gestion des promotions</h2>
        <p class="page-subtitle">Créer, modifier et gérer les promotions</p>
      </div>
      <div class="header-actions">
        <button @click="openAddModal" class="btn-primary">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <line x1="12" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Nouvelle promotion
        </button>
      </div>
    </div>

    <!-- Statistiques -->
    <div class="stats-row">
      <div class="stat-box">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">Total promotions</div>
      </div>
      <div class="stat-box success">
        <div class="stat-value">{{ stats.active }}</div>
        <div class="stat-label">Actives</div>
      </div>
      <div class="stat-box danger">
        <div class="stat-value">{{ stats.inactive }}</div>
        <div class="stat-label">Inactives</div>
      </div>
      <div class="stat-box info">
        <div class="stat-value">{{ stats.total_users }}</div>
        <div class="stat-label">Total utilisateurs</div>
      </div>
      <div class="stat-box warning">
        <div class="stat-value">{{ stats.total_active_users }}</div>
        <div class="stat-label">Utilisateurs actifs</div>
      </div>
    </div>

    <!-- Filtres et recherche -->
    <div class="filters-section">
      <div class="search-box">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
          <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Rechercher une promotion (code, nom, année)..."
          class="search-input"
        />
      </div>

      <div class="filter-group">
        <select v-model="filterStatus" class="filter-select">
          <option value="all">Tous les statuts</option>
          <option value="active">Actives</option>
          <option value="inactive">Inactives</option>
        </select>
      </div>
    </div>

    <!-- Table -->
    <div v-if="isLoading" class="loading-container">
      <LoadingSpinner />
    </div>

    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Code</th>
            <th>Nom</th>
            <th>Année</th>
            <th>Utilisateurs</th>
            <th>Utilisateurs actifs</th>
            <th>Statut</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="promotion in filteredPromotions" :key="promotion.id">
            <tr @click="togglePromotionExpand(promotion)"
                class="cursor-pointer hover:bg-gray-50">
              <td><span class="id-badge">{{ promotion.id }}</span></td>
              <td>
                <span class="code-badge">{{ promotion.code }}</span>
              </td>
              <td>
                <div class="name-cell">
                  <div class="name-text">{{ promotion.name }}</div>
                  <div v-if="promotion.description" class="description-text">
                    {{ promotion.description }}
                  </div>
                </div>
              </td>
              <td>
                <span v-if="promotion.year" class="year-badge">{{ promotion.year }}</span>
                <span v-else class="text-gray">-</span>
              </td>
              <td>
                <span class="count-badge">{{ promotion.user_count || 0 }}</span>
              </td>
              <td>
                <span class="count-badge active">{{ promotion.active_user_count || 0 }}</span>
              </td>
              <td>
                <span v-if="promotion.is_active" class="badge badge-success">Active</span>
                <span v-else class="badge badge-gray">Inactive</span>
              </td>
              <td>
                <div class="action-buttons">
                  <button
                    v-if="promotion.user_count && promotion.user_count > 0"
                    @click.stop="handleActivatePromotionUsers(promotion)"
                    class="action-btn radius-enable"
                    title="Activer tous les utilisateurs dans RADIUS"
                    :disabled="isActivating">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <path d="M8 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>

                  <button
                    v-if="promotion.user_count && promotion.user_count > 0"
                    @click.stop="handleDeactivatePromotionUsers(promotion)"
                    class="action-btn radius-disable"
                    title="Désactiver tous les utilisateurs dans RADIUS"
                    :disabled="isActivating">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </button>

                  <button @click.stop="handleEdit(promotion)" class="action-btn edit" title="Modifier">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>

                  <button
                    @click.stop="handleToggleStatus(promotion)"
                    :class="['action-btn', promotion.is_active ? 'danger' : 'success']"
                    :title="promotion.is_active ? 'Désactiver' : 'Activer'">
                    <svg v-if="promotion.is_active" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>

                  <button @click.stop="handleDelete(promotion)" class="action-btn delete" title="Supprimer">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </td>
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
          </template>
        </tbody>
      </table>

      <div v-if="filteredPromotions.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
          <line x1="12" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <h3>Aucune promotion trouvée</h3>
        <p>Aucune promotion ne correspond à vos critères de recherche</p>
      </div>
    </div>

    <!-- Modal Ajout -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Ajouter une promotion</h3>
          <button @click="closeAddModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>Code *</label>
              <input v-model="newPromotion.code" type="text" placeholder="Ex: ING3, L1, M2..." required />
            </div>
            <div class="form-group">
              <label>Année</label>
              <input v-model.number="newPromotion.year" type="number" placeholder="2024" min="2000" max="2100" />
            </div>
          </div>

          <div class="form-group">
            <label>Nom *</label>
            <input v-model="newPromotion.name" type="text" placeholder="Nom complet de la promotion" required />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea v-model="newPromotion.description" rows="3" placeholder="Description optionnelle"></textarea>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="newPromotion.is_active" type="checkbox" />
              <span class="checkbox-text">
                <strong>Promotion active</strong>
                <small>Les promotions actives sont visibles lors de l'inscription</small>
              </span>
            </label>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeAddModal" class="btn-secondary">Annuler</button>
          <button @click="handleAddPromotion" class="btn-primary">Créer la promotion</button>
        </div>
      </div>
    </div>

    <!-- Modal Édition -->
    <div v-if="showEditModal && selectedPromotion" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Modifier la promotion</h3>
          <button @click="closeEditModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>Code *</label>
              <input v-model="selectedPromotion.code" type="text" required />
            </div>
            <div class="form-group">
              <label>Année</label>
              <input v-model.number="selectedPromotion.year" type="number" min="2000" max="2100" />
            </div>
          </div>

          <div class="form-group">
            <label>Nom *</label>
            <input v-model="selectedPromotion.name" type="text" required />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea v-model="selectedPromotion.description" rows="3"></textarea>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="selectedPromotion.is_active" type="checkbox" />
              <span class="checkbox-text">
                <strong>Promotion active</strong>
                <small>Les promotions actives sont visibles lors de l'inscription</small>
              </span>
            </label>
          </div>

          <div v-if="selectedPromotion.user_count && selectedPromotion.user_count > 0" class="info-note">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 16v-4M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <p>Cette promotion contient {{ selectedPromotion.user_count }} utilisateur(s)</p>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeEditModal" class="btn-secondary">Annuler</button>
          <button @click="handleUpdatePromotion" class="btn-primary">Enregistrer</button>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Contenu spécifique à la page promotions */
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 1rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.page-title {
  font-size: 1.875rem;
  font-weight: 800;
  color: #1F2937;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  font-size: 1rem;
  color: #6B7280;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
  white-space: nowrap;
}

.btn-primary svg {
  width: 20px;
  height: 20px;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

/* Statistiques */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-box {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
  border-left: 4px solid #6B7280;
}

.stat-box.success {
  border-left-color: #10B981;
}

.stat-box.danger {
  border-left-color: #DC2626;
}

.stat-box.info {
  border-left-color: #3B82F6;
}

.stat-box.warning {
  border-left-color: #F59E0B;
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  color: #1F2937;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #6B7280;
  font-weight: 500;
}

/* Filtres */
.filters-section {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 250px;
  position: relative;
  display: flex;
  align-items: center;
}

.search-box svg {
  position: absolute;
  left: 1rem;
  width: 20px;
  height: 20px;
  color: #9CA3AF;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 3rem;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #F97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

.filter-group {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.filter-select {
  padding: 0.75rem 1rem;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #1F2937;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 180px;
}

.filter-select:focus {
  outline: none;
  border-color: #F97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

/* Table */
.table-container {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
}

.data-table th {
  padding: 1rem 1.5rem;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 700;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  color: #1F2937;
  border-bottom: 1px solid #F3F4F6;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: #F9FAFB;
}

.id-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  background: #F3F4F6;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6B7280;
}

.code-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  color: white;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 700;
  letter-spacing: 0.025em;
}

.name-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.name-text {
  font-weight: 600;
  color: #1F2937;
}

.description-text {
  font-size: 0.75rem;
  color: #9CA3AF;
}

.year-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  background: #EFF6FF;
  color: #3B82F6;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.count-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  background: #F3F4F6;
  color: #6B7280;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
}

.count-badge.active {
  background: #D1FAE5;
  color: #10B981;
}

.text-gray {
  color: #9CA3AF;
}

.badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-success {
  background: #D1FAE5;
  color: #10B981;
}

.badge-gray {
  background: #F3F4F6;
  color: #6B7280;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn svg {
  width: 16px;
  height: 16px;
  color: #6B7280;
}

.action-btn.radius-enable:hover:not(:disabled) {
  background: #D1FAE5;
  border-color: #10B981;
}

.action-btn.radius-enable:hover:not(:disabled) svg {
  color: #10B981;
}

.action-btn.radius-disable:hover:not(:disabled) {
  background: #FEF3C7;
  border-color: #F59E0B;
}

.action-btn.radius-disable:hover:not(:disabled) svg {
  color: #F59E0B;
}

.action-btn.edit:hover {
  background: #EFF6FF;
  border-color: #3B82F6;
}

.action-btn.edit:hover svg {
  color: #3B82F6;
}

.action-btn.success:hover {
  background: #D1FAE5;
  border-color: #10B981;
}

.action-btn.success:hover svg {
  color: #10B981;
}

.action-btn.danger:hover {
  background: #FEE2E2;
  border-color: #DC2626;
}

.action-btn.danger:hover svg {
  color: #DC2626;
}

.action-btn.delete:hover {
  background: #FEE2E2;
  border-color: #DC2626;
}

.action-btn.delete:hover svg {
  color: #DC2626;
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: #D1D5DB;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1F2937;
  margin-bottom: 0.5rem;
}

.empty-state p {
  font-size: 0.875rem;
  color: #6B7280;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1F2937;
}

.modal-close {
  width: 36px;
  height: 36px;
  border: none;
  background: #F3F4F6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close svg {
  width: 20px;
  height: 20px;
  color: #6B7280;
}

.modal-close:hover {
  background: #FEE2E2;
}

.modal-close:hover svg {
  color: #DC2626;
}

.modal-body {
  padding: 2rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #F97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

.checkbox-group {
  margin-top: 1.5rem;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  margin-top: 2px;
  cursor: pointer;
  accent-color: #DC2626;
}

.checkbox-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.checkbox-text strong {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1F2937;
}

.checkbox-text small {
  font-size: 0.75rem;
  color: #6B7280;
}

.info-note {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background: #EFF6FF;
  border: 1px solid #DBEAFE;
  border-left: 4px solid #3B82F6;
  border-radius: 8px;
  margin-top: 1rem;
}

.info-note svg {
  width: 20px;
  height: 20px;
  color: #3B82F6;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-note p {
  font-size: 0.875rem;
  color: #1F2937;
  margin: 0;
}

.modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid #E5E7EB;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #F3F4F6;
  color: #374151;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #E5E7EB;
}

.loading-container {
  padding: 4rem 0;
  display: flex;
  justify-content: center;
}

/* Responsive */
@media (max-width: 768px) {
  .content-header {
    flex-direction: column;
    gap: 1rem;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  .btn-primary {
    width: 100%;
    justify-content: center;
  }

  .filters-section {
    flex-direction: column;
  }

  .filter-group {
    width: 100%;
    flex-direction: column;
  }

  .filter-select {
    width: 100%;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .table-container {
    overflow-x: auto;
  }

  .data-table {
    min-width: 900px;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}

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
</style>
