<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { usePromotionStore } from '@/stores/promotion'
import { useNotificationStore } from '@/stores/notification'
import { userService } from '@/services/user.service'
import AdminLayout from '@/layouts/AdminLayout.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()
const promotionStore = usePromotionStore()
const notificationStore = useNotificationStore()

const users = computed(() => userStore.users)
const isLoading = computed(() => userStore.isLoading)

const showAddModal = ref(false)
const showEditModal = ref(false)
const showActivationModal = ref(false)
const selectedUser = ref<any>(null)
const searchQuery = ref('')
const filterRole = ref('all')
const filterStatus = ref('all')
const filterRadiusStatus = ref('all')
const isDeleting = ref(false)
const isActivating = ref(false)

// Sélection multiple
const selectedUserIds = ref<number[]>([])
const selectAll = ref(false)

// Résultat d'activation
const activationResult = ref<any>(null)

const newUser = ref({
  password: '',
  password2: '',
  first_name: '',
  last_name: '',
  promotion_id: null as number | null,
  matricule: '',
  is_staff: false
})

// Filtrage des utilisateurs
const filteredUsers = computed(() => {
  let filtered = users.value

  // Filtre par recherche
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(u =>
      u.username?.toLowerCase().includes(query) ||
      u.email?.toLowerCase().includes(query) ||
      u.first_name?.toLowerCase().includes(query) ||
      u.last_name?.toLowerCase().includes(query) ||
      u.promotion_detail?.code?.toLowerCase().includes(query) ||
      u.promotion_detail?.name?.toLowerCase().includes(query) ||
      u.matricule?.toLowerCase().includes(query)
    )
  }

  // Filtre par rôle
  if (filterRole.value !== 'all') {
    if (filterRole.value === 'admin') {
      filtered = filtered.filter(u => u.is_staff || u.is_superuser)
    } else {
      filtered = filtered.filter(u => !u.is_staff && !u.is_superuser)
    }
  }

  // Filtre par statut Django
  if (filterStatus.value !== 'all') {
    if (filterStatus.value === 'active') {
      filtered = filtered.filter(u => u.is_active)
    } else {
      filtered = filtered.filter(u => !u.is_active)
    }
  }

  // Filtre par statut RADIUS
  if (filterRadiusStatus.value !== 'all') {
    if (filterRadiusStatus.value === 'activated') {
      filtered = filtered.filter(u => u.is_radius_activated)
    } else if (filterRadiusStatus.value === 'pending') {
      filtered = filtered.filter(u => u.is_active && !u.is_radius_activated)
    }
  }

  return filtered
})

// Utilisateurs en attente d'activation RADIUS
const pendingActivationUsers = computed(() =>
  users.value.filter(u => u.is_active && !u.is_radius_activated)
)

// Statistiques
const stats = computed(() => ({
  total: users.value.length,
  active: users.value.filter(u => u.is_active).length,
  radius_activated: users.value.filter(u => u.is_radius_activated).length,
  pending_activation: pendingActivationUsers.value.length,
  admins: users.value.filter(u => u.is_staff || u.is_superuser).length,
  regular: users.value.filter(u => !u.is_staff && !u.is_superuser).length
}))

onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    await Promise.all([
      userStore.fetchUsers(),
      promotionStore.fetchPromotions()
    ])
  } catch (error: any) {
    const message = error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors du chargement des données: ${message}`)
    console.error('Erreur chargement données:', error)
  }
})

// Gestion de la sélection multiple
function toggleSelectAll() {
  if (selectAll.value) {
    selectedUserIds.value = filteredUsers.value
      .filter(u => u.is_active && !u.is_radius_activated)
      .map(u => u.id)
  } else {
    selectedUserIds.value = []
  }
}

function toggleUserSelection(userId: number) {
  const index = selectedUserIds.value.indexOf(userId)
  if (index > -1) {
    selectedUserIds.value.splice(index, 1)
  } else {
    selectedUserIds.value.push(userId)
  }

  // Update selectAll status
  const selectableUsers = filteredUsers.value.filter(u => u.is_active && !u.is_radius_activated)
  selectAll.value = selectableUsers.length > 0 &&
                    selectedUserIds.value.length === selectableUsers.length
}

function isUserSelected(userId: number): boolean {
  return selectedUserIds.value.includes(userId)
}

function canSelectUser(user: any): boolean {
  return user.is_active && !user.is_radius_activated
}

// Activation RADIUS
async function handleActivateRadius(userIds: number[]) {
  if (userIds.length === 0) {
    notificationStore.warning('Aucun utilisateur sélectionné')
    return
  }

  if (!confirm(`Voulez-vous activer ${userIds.length} utilisateur(s) dans RADIUS ?`)) {
    return
  }

  isActivating.value = true
  try {
    const result = await userStore.activateUsersRadius(userIds)
    activationResult.value = result
    showActivationModal.value = true

    // Clear selection
    selectedUserIds.value = []
    selectAll.value = false

    if (result.summary.activated > 0) {
      notificationStore.success(`${result.summary.activated} utilisateur(s) activé(s) dans RADIUS`)
    }
    if (result.summary.failed > 0) {
      notificationStore.warning(`${result.summary.failed} échec(s) d'activation`)
    }
  } catch (error) {
    notificationStore.error(userStore.error || 'Erreur lors de l\'activation')
  } finally {
    isActivating.value = false
  }
}

function closeActivationModal() {
  showActivationModal.value = false
  activationResult.value = null
}

function openAddModal() {
  newUser.value = {
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
    promotion_id: null,
    matricule: '',
    is_staff: false
  }
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
}

// Fonction de validation de mot de passe
function isValidPassword(password: string): boolean {
  return password.length >= 8
}

async function handleAddUser() {
  // Validation des champs obligatoires
  if (!newUser.value.password || !newUser.value.password2 ||
      !newUser.value.first_name || !newUser.value.last_name ||
      !newUser.value.promotion_id || !newUser.value.matricule) {
    notificationStore.warning('Veuillez remplir tous les champs requis')
    return
  }

  // Validation de la force du mot de passe
  if (!isValidPassword(newUser.value.password)) {
    notificationStore.warning('Le mot de passe doit contenir au moins 8 caractères')
    return
  }

  // Validation de la confirmation du mot de passe
  if (newUser.value.password !== newUser.value.password2) {
    notificationStore.warning('Les mots de passe ne correspondent pas')
    return
  }

  try {
    // Générer username et email à partir du matricule (comme lors de l'inscription)
    const username = newUser.value.matricule
    const email = `${newUser.value.matricule}@student.ucac-icam.com`

    await userStore.createUser({
      username: username,
      email: email,
      password: newUser.value.password,
      password2: newUser.value.password2,
      first_name: newUser.value.first_name,
      last_name: newUser.value.last_name,
      promotion_id: newUser.value.promotion_id,
      matricule: newUser.value.matricule,
      is_staff: newUser.value.is_staff
    })

    notificationStore.success('Utilisateur ajouté avec succès')
    closeAddModal()
  } catch (error) {
    notificationStore.error(userStore.error || 'Erreur lors de l\'ajout')
  }
}

function handleEdit(user: any) {
  selectedUser.value = { ...user }
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  selectedUser.value = null
}

async function handleUpdateUser() {
  if (!selectedUser.value) return

  try {
    await userStore.updateUser(selectedUser.value.id, {
      username: selectedUser.value.username,
      email: selectedUser.value.email,
      first_name: selectedUser.value.first_name,
      last_name: selectedUser.value.last_name,
      is_staff: selectedUser.value.is_staff,
      is_active: selectedUser.value.is_active
    })

    notificationStore.success('Utilisateur modifié avec succès')
    closeEditModal()
  } catch (error) {
    notificationStore.error(userStore.error || 'Erreur lors de la modification')
  }
}

async function handleToggleActive(user: any) {
  try {
    await userStore.updateUser(user.id, {
      is_active: !user.is_active
    })
    notificationStore.success(`Utilisateur ${user.is_active ? 'désactivé' : 'activé'}`)
  } catch (error) {
    notificationStore.error('Erreur lors de la modification')
  }
}

async function handleDelete(user: any) {
  // Protection contre les double-clics
  if (isDeleting.value) {
    return
  }

  if (!confirm(`Voulez-vous vraiment supprimer l'utilisateur ${user.username} ?`)) {
    return
  }

  isDeleting.value = true
  try {
    await userStore.deleteUser(user.id)
    notificationStore.success('Utilisateur supprimé avec succès')
  } catch (error) {
    notificationStore.error('Erreur lors de la suppression')
  } finally {
    isDeleting.value = false
  }
}

// Activation/Désactivation RADIUS individuelle
async function handleActivateRadiusIndividual(userId: number) {
  if (!confirm('Activer l\'accès Internet pour cet utilisateur ?')) return

  isActivating.value = true
  try {
    await userService.activateUserRadius(userId)
    notificationStore.success('Utilisateur activé dans RADIUS')
    await userStore.fetchUsers()  // Recharger pour mettre à jour is_radius_enabled
  } catch (error: any) {
    const message = error?.response?.data?.message || 'Erreur lors de l\'activation'
    notificationStore.error(message)
  } finally {
    isActivating.value = false
  }
}

async function handleDeactivateRadiusIndividual(userId: number) {
  if (!confirm('Désactiver l\'accès Internet pour cet utilisateur ?')) return

  isActivating.value = true
  try {
    await userService.deactivateUserRadius(userId)
    notificationStore.success('Utilisateur désactivé dans RADIUS')
    await userStore.fetchUsers()  // Recharger pour mettre à jour is_radius_enabled
  } catch (error: any) {
    const message = error?.response?.data?.message || 'Erreur lors de la désactivation'
    notificationStore.error(message)
  } finally {
    isActivating.value = false
  }
}
</script>

<template>
  <AdminLayout activePage="users">
    <div class="content-header">
        <div>
          <h2 class="page-title">Gestion des utilisateurs</h2>
          <p class="page-subtitle">Créer, modifier et gérer les comptes utilisateurs</p>
        </div>
        <div class="header-actions">
          <button
            v-if="selectedUserIds.length > 0"
            @click="handleActivateRadius(selectedUserIds)"
            class="btn-success"
            :disabled="isActivating">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="currentColor"/>
            </svg>
            Activer dans Radius ({{ selectedUserIds.length }})
          </button>
          <button @click="openAddModal" class="btn-primary">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
              <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Nouvel utilisateur
          </button>
        </div>
      </div>

      <!-- Statistiques -->
      <div class="stats-row">
        <div class="stat-box">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">Total utilisateurs</div>
        </div>
        <div class="stat-box success">
          <div class="stat-value">{{ stats.active }}</div>
          <div class="stat-label">Actifs Django</div>
        </div>
        <div class="stat-box info">
          <div class="stat-value">{{ stats.radius_activated }}</div>
          <div class="stat-label">Activés RADIUS</div>
        </div>
        <div class="stat-box warning">
          <div class="stat-value">{{ stats.pending_activation }}</div>
          <div class="stat-label">En attente RADIUS</div>
        </div>
        <div class="stat-box danger">
          <div class="stat-value">{{ stats.admins }}</div>
          <div class="stat-label">Administrateurs</div>
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
            placeholder="Rechercher un utilisateur (nom, email, promotion, matricule)..."
            class="search-input"
          />
        </div>

        <div class="filter-group">
          <select v-model="filterRole" class="filter-select">
            <option value="all">Tous les rôles</option>
            <option value="admin">Administrateurs</option>
            <option value="user">Utilisateurs</option>
          </select>

          <select v-model="filterStatus" class="filter-select">
            <option value="all">Tous les statuts Django</option>
            <option value="active">Actifs</option>
            <option value="inactive">Inactifs</option>
          </select>

          <select v-model="filterRadiusStatus" class="filter-select">
            <option value="all">Tous les statuts RADIUS</option>
            <option value="activated">Activés RADIUS</option>
            <option value="pending">En attente RADIUS</option>
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
              <th style="width: 40px;">
                <input
                  type="checkbox"
                  v-model="selectAll"
                  @change="toggleSelectAll"
                  :disabled="pendingActivationUsers.length === 0"
                />
              </th>
              <th>ID</th>
              <th>Utilisateur</th>
              <th>Email</th>
              <th>Promotion/Matricule</th>
              <th>Rôle</th>
              <th>Statut Django</th>
              <th>Statut RADIUS</th>
              <th>Date d'inscription</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.id">
              <td>
                <input
                  type="checkbox"
                  :checked="isUserSelected(user.id)"
                  @change="toggleUserSelection(user.id)"
                  :disabled="!canSelectUser(user)"
                />
              </td>
              <td><span class="id-badge">{{ user.id }}</span></td>
              <td>
                <div class="user-cell">
                  <div class="user-avatar-sm">{{ user.username.charAt(0).toUpperCase() }}</div>
                  <div>
                    <div class="user-name-text">{{ user.username }}</div>
                    <div v-if="user.first_name || user.last_name" class="user-full-name">
                      {{ user.first_name }} {{ user.last_name }}
                    </div>
                  </div>
                </div>
              </td>
              <td>{{ user.email }}</td>
              <td>
                <div v-if="user.promotion_detail || user.matricule" class="info-cell">
                  <span v-if="user.promotion_detail" class="badge badge-light">
                    {{ user.promotion_detail.code }}
                  </span>
                  <span v-if="user.matricule" class="badge badge-light">{{ user.matricule }}</span>
                </div>
                <span v-else class="text-gray">-</span>
              </td>
              <td>
                <span v-if="user.is_staff || user.is_superuser" class="badge badge-danger">Admin</span>
                <span v-else class="badge badge-info">Utilisateur</span>
              </td>
              <td>
                <span v-if="user.is_active" class="badge badge-success">Actif</span>
                <span v-else class="badge badge-gray">Inactif</span>
              </td>
              <td>
                <span v-if="user.is_radius_activated" class="badge badge-success">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 14px; height: 14px; display: inline; margin-right: 4px;">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="currentColor"/>
                  </svg>
                  Activé
                </span>
                <span v-else-if="user.is_active" class="badge badge-warning">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 14px; height: 14px; display: inline; margin-right: 4px;">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                  En attente
                </span>
                <span v-else class="badge badge-gray">-</span>
              </td>
              <td>{{ new Date(user.date_joined).toLocaleDateString('fr-FR') }}</td>
              <td>
                <div class="action-buttons">
                  <!-- Bouton activation initiale RADIUS (pour les utilisateurs jamais activés) -->
                  <button
                    v-if="!user.is_radius_activated && user.is_active"
                    @click="handleActivateRadius([user.id])"
                    class="action-btn radius"
                    title="Activer dans RADIUS"
                    :disabled="isActivating">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="currentColor"/>
                    </svg>
                  </button>

                  <!-- Boutons enable/disable RADIUS individuels (pour les utilisateurs déjà activés) -->
                  <button
                    v-if="user.is_radius_activated && (!user.is_radius_enabled || user.is_radius_enabled === false)"
                    @click="handleActivateRadiusIndividual(user.id)"
                    class="action-btn radius-enable"
                    title="Activer l'accès Internet"
                    :disabled="isActivating">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <path d="M8 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>

                  <button
                    v-if="user.is_radius_activated && user.is_radius_enabled"
                    @click="handleDeactivateRadiusIndividual(user.id)"
                    class="action-btn radius-disable"
                    title="Désactiver l'accès Internet"
                    :disabled="isActivating">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </button>

                  <button @click="handleEdit(user)" class="action-btn edit" title="Modifier">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button @click="handleToggleActive(user)" :class="['action-btn', user.is_active ? 'danger' : 'success']" :title="user.is_active ? 'Désactiver' : 'Activer'">
                    <svg v-if="user.is_active" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button @click="handleDelete(user)" class="action-btn delete" title="Supprimer">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="filteredUsers.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
            <circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2"/>
          </svg>
          <h3>Aucun utilisateur trouvé</h3>
          <p>Aucun utilisateur ne correspond à vos critères de recherche</p>
        </div>
      </div>

    <!-- Modal Résultat d'activation -->
    <div v-if="showActivationModal && activationResult" class="modal-overlay" @click.self="closeActivationModal">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>Résultat de l'activation RADIUS</h3>
          <button @click="closeActivationModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="activation-summary">
            <div class="summary-card success">
              <div class="summary-icon">✓</div>
              <div class="summary-value">{{ activationResult.summary.activated }}</div>
              <div class="summary-label">Activé(s)</div>
            </div>
            <div class="summary-card danger" v-if="activationResult.summary.failed > 0">
              <div class="summary-icon">✗</div>
              <div class="summary-value">{{ activationResult.summary.failed }}</div>
              <div class="summary-label">Échec(s)</div>
            </div>
          </div>

          <div v-if="activationResult.activated_users.length > 0" class="activation-section">
            <h4 class="section-title">✅ Utilisateurs activés avec succès</h4>
            <div class="activation-note">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 16v-4M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <p><strong>{{ activationResult.important_note }}</strong></p>
            </div>
            <div class="activated-users-list">
              <div v-for="user in activationResult.activated_users" :key="user.id" class="activated-user-card">
                <div class="user-header">
                  <div class="user-info">
                    <strong>{{ user.username }}</strong>
                    <span class="user-name">{{ user.first_name }} {{ user.last_name }}</span>
                  </div>
                  <span class="badge badge-success">Activé</span>
                </div>
                <div class="user-details">
                  <div class="detail-item">
                    <span class="detail-label">Email:</span>
                    <span class="detail-value">{{ user.email }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Promotion:</span>
                    <span class="detail-value">{{ user.promotion }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Matricule:</span>
                    <span class="detail-value">{{ user.matricule }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Timeout session:</span>
                    <span class="detail-value">{{ user.session_timeout }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Bande passante:</span>
                    <span class="detail-value">{{ user.bandwidth_limit }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="activationResult.failed_users.length > 0" class="activation-section">
            <h4 class="section-title error">❌ Échecs d'activation</h4>
            <div class="failed-users-list">
              <div v-for="user in activationResult.failed_users" :key="user.id" class="failed-user-card">
                <div class="user-header">
                  <div class="user-info">
                    <strong>{{ user.username || `ID: ${user.id}` }}</strong>
                  </div>
                  <span class="badge badge-danger">Échec</span>
                </div>
                <div class="error-message">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                  {{ user.error }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeActivationModal" class="btn-primary">Fermer</button>
        </div>
      </div>
    </div>

    <!-- Modal Ajout -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Ajouter un utilisateur</h3>
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
              <label>Prénom *</label>
              <input v-model="newUser.first_name" type="text" placeholder="John" required />
            </div>
            <div class="form-group">
              <label>Nom *</label>
              <input v-model="newUser.last_name" type="text" placeholder="Doe" required />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Promotion *</label>
              <select v-model="newUser.promotion_id" required class="form-select">
                <option :value="null" disabled>Sélectionnez une promotion</option>
                <option
                  v-for="promo in promotionStore.promotions.filter(p => p.is_active)"
                  :key="promo.id"
                  :value="promo.id"
                >
                  {{ promo.code }} - {{ promo.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Matricule *</label>
              <input v-model="newUser.matricule" type="text" placeholder="Matricule étudiant" required />
            </div>
          </div>

          <div class="info-note">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 16v-4M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <p>Le nom d'utilisateur et l'email seront générés automatiquement à partir du matricule</p>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Mot de passe *</label>
              <input v-model="newUser.password" type="password" placeholder="••••••••" required />
            </div>
            <div class="form-group">
              <label>Confirmation du mot de passe *</label>
              <input v-model="newUser.password2" type="password" placeholder="••••••••" required />
            </div>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="newUser.is_staff" type="checkbox" />
              <span class="checkbox-text">
                <strong>Administrateur</strong>
                <small>L'utilisateur aura accès à l'administration</small>
              </span>
            </label>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeAddModal" class="btn-secondary">Annuler</button>
          <button @click="handleAddUser" class="btn-primary">Créer l'utilisateur</button>
        </div>
      </div>
    </div>

    <!-- Modal Édition -->
    <div v-if="showEditModal && selectedUser" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Modifier l'utilisateur</h3>
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
              <label>Nom d'utilisateur</label>
              <input v-model="selectedUser.username" type="text" />
            </div>
            <div class="form-group">
              <label>Email</label>
              <input v-model="selectedUser.email" type="email" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Prénom</label>
              <input v-model="selectedUser.first_name" type="text" />
            </div>
            <div class="form-group">
              <label>Nom</label>
              <input v-model="selectedUser.last_name" type="text" />
            </div>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="selectedUser.is_staff" type="checkbox" />
              <span class="checkbox-text">
                <strong>Administrateur</strong>
              </span>
            </label>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="selectedUser.is_active" type="checkbox" />
              <span class="checkbox-text">
                <strong>Compte actif</strong>
              </span>
            </label>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeEditModal" class="btn-secondary">Annuler</button>
          <button @click="handleUpdateUser" class="btn-primary">Enregistrer</button>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Contenu spécifique à la page utilisateurs */
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

.btn-success {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
  white-space: nowrap;
}

.btn-success:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-success svg {
  width: 20px;
  height: 20px;
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
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

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar-sm {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.user-name-text {
  font-weight: 600;
  color: #1F2937;
}

.user-full-name {
  font-size: 0.75rem;
  color: #9CA3AF;
}

.info-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
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
  display: inline-flex;
  align-items: center;
}

.badge-danger {
  background: #FEE2E2;
  color: #DC2626;
}

.badge-info {
  background: #DBEAFE;
  color: #3B82F6;
}

.badge-gray {
  background: #F3F4F6;
  color: #6B7280;
}

.badge-warning {
  background: #FEF3C7;
  color: #F59E0B;
  display: inline-flex;
  align-items: center;
}

.badge-light {
  background: #F3F4F6;
  color: #4B5563;
  font-weight: 500;
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

.action-btn.radius:hover:not(:disabled) {
  background: #D1FAE5;
  border-color: #10B981;
}

.action-btn.radius:hover:not(:disabled) svg {
  color: #10B981;
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

.modal-large {
  max-width: 900px;
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

.activation-summary {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-card {
  flex: 1;
  background: #F9FAFB;
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  border: 2px solid transparent;
}

.summary-card.success {
  background: #D1FAE5;
  border-color: #10B981;
}

.summary-card.danger {
  background: #FEE2E2;
  border-color: #DC2626;
}

.summary-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 2.5rem;
  font-weight: 800;
  color: #1F2937;
  margin-bottom: 0.25rem;
}

.summary-label {
  font-size: 0.875rem;
  color: #6B7280;
  font-weight: 600;
}

.activation-section {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #1F2937;
  margin-bottom: 1rem;
}

.section-title.error {
  color: #DC2626;
}

.activation-note {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: #EFF6FF;
  border: 1px solid #DBEAFE;
  border-left: 4px solid #3B82F6;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.activation-note svg {
  width: 24px;
  height: 24px;
  color: #3B82F6;
  flex-shrink: 0;
}

.activation-note p {
  font-size: 0.875rem;
  color: #1F2937;
  margin: 0;
}

.activated-users-list,
.failed-users-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.activated-user-card,
.failed-user-card {
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1rem;
}

.user-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.user-info strong {
  font-size: 1rem;
  font-weight: 700;
  color: #1F2937;
  display: block;
  margin-bottom: 0.25rem;
}

.user-name {
  font-size: 0.875rem;
  color: #6B7280;
}

.user-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.75rem;
  color: #6B7280;
  font-weight: 600;
}

.detail-value {
  font-size: 0.875rem;
  color: #1F2937;
  font-weight: 500;
}

.error-message {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #FEF2F2;
  border: 1px solid #FEE2E2;
  border-radius: 8px;
  color: #DC2626;
  font-size: 0.875rem;
}

.error-message svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
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
.form-group input[type="email"],
.form-group input[type="password"],
.form-group select.form-select {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
  background: white;
  cursor: pointer;
}

.form-group input:focus,
.form-group select.form-select:focus {
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
  margin-bottom: 1rem;
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

  .btn-primary,
  .btn-success {
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
    min-width: 1200px;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .user-details {
    grid-template-columns: 1fr;
  }
}
</style>
