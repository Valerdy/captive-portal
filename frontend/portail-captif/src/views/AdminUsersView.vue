<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { usePromotionStore } from '@/stores/promotion'
import { useProfileStore } from '@/stores/profile'
import { useNotificationStore } from '@/stores/notification'
import { userService } from '@/services/user.service'
import { type VerificationResult } from '@/services/profile.service'
import AdminLayout from '@/layouts/AdminLayout.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()
const promotionStore = usePromotionStore()
const profileStore = useProfileStore()
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
const isDeactivating = ref(false)

// Sélection multiple
const selectedUserIds = ref<number[]>([])
const selectAll = ref(false)

// Résultat d'activation
const activationResult = ref<any>(null)

// Variables pour la vérification RADIUS
const showUserVerificationModal = ref(false)
const isVerifyingUser = ref(false)
const userVerificationResult = ref<VerificationResult | null>(null)
const verifyingUserId = ref<number | null>(null)

const newUser = ref({
  password: '',
  password2: '',
  first_name: '',
  last_name: '',
  promotion: '' as number | string,
  profile: '' as number | string,
  matricule: '',
  is_staff: false
})

const promotions = computed(() => {
  if (!Array.isArray(promotionStore.promotions)) return []
  return promotionStore.promotions.filter(p => p && p.is_active)
})

const allPromotions = computed(() => {
  if (!Array.isArray(promotionStore.promotions)) return []
  return promotionStore.promotions
})

const profiles = computed(() => {
  if (!Array.isArray(profileStore.profiles)) return []
  return profileStore.profiles.filter(p => p && p.is_active)
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
      (u.promotion_name || '').toLowerCase().includes(query) ||
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
      promotionStore.fetchPromotions(),
      profileStore.fetchProfiles()
    ])
  } catch (error: any) {
    const message = error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors du chargement des données: ${message}`)
    console.error('Erreur chargement données:', error)
  }
})

async function handleTogglePromotion(promo: any) {
  try {
    if (promo.is_active) {
      await promotionStore.deactivatePromotion(promo.id)
      notificationStore.success(`Promotion ${promo.name} désactivée (RADIUS)`)
    } else {
      await promotionStore.activatePromotion(promo.id)
      notificationStore.success(`Promotion ${promo.name} activée (RADIUS)`)
    }
  } catch (error) {
    notificationStore.error(promotionStore.error || 'Erreur lors du changement de statut promotion')
  }
}

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

    // Rafraîchir la liste des utilisateurs pour afficher les statuts à jour
    await userStore.fetchUsers()

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

async function handleDeactivateRadius(userId: number) {
  isDeactivating.value = true
  try {
    await userStore.deactivateUserRadius(userId)
    notificationStore.success('Utilisateur désactivé dans RADIUS')
  } catch (error) {
    notificationStore.error(userStore.error || 'Erreur lors de la désactivation')
  } finally {
    isDeactivating.value = false
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
    promotion: '',
    profile: '',
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
      !newUser.value.promotion || !newUser.value.matricule) {
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

    const userData: any = {
      username: username,
      email: email,
      password: newUser.value.password,
      password2: newUser.value.password2,
      first_name: newUser.value.first_name,
      last_name: newUser.value.last_name,
      promotion: Number(newUser.value.promotion),
      matricule: newUser.value.matricule,
      is_staff: newUser.value.is_staff
    }

    // Ajouter le profil seulement s'il est sélectionné
    if (newUser.value.profile) {
      userData.profile = Number(newUser.value.profile)
    }

    await userStore.createUser(userData)

    notificationStore.success('Utilisateur ajouté avec succès')
    closeAddModal()
  } catch (error) {
    notificationStore.error(userStore.error || 'Erreur lors de l\'ajout')
  }
}

function handleEdit(user: any) {
  selectedUser.value = {
    ...user,
    promotion: user.promotion ?? null,
    profile: user.profile ?? null
  }
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
      promotion: selectedUser.value.promotion,
      profile: selectedUser.value.profile || null,
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

// Vérification RADIUS pour un utilisateur individuel
async function handleVerifyUserRadius(user: any) {
  if (isVerifyingUser.value) return

  selectedUser.value = user
  verifyingUserId.value = user.id
  isVerifyingUser.value = true
  showUserVerificationModal.value = true
  userVerificationResult.value = null

  try {
    const result = await userService.verifyRadiusProfile(user.id)
    userVerificationResult.value = result

    if (result.success) {
      if (result.status === 'OK') {
        notificationStore.success('Profil RADIUS vérifié avec succès')
      } else if (result.status === 'WARNING') {
        notificationStore.warning('Différences détectées dans le profil RADIUS')
      } else if (result.status === 'ERROR') {
        notificationStore.error('Erreurs dans l\'application du profil RADIUS')
      } else if (result.status === 'NOT_CONNECTED') {
        notificationStore.info('Utilisateur non connecté au hotspot')
      }
    } else {
      notificationStore.error(result.error || 'Erreur lors de la vérification')
    }
  } catch (error: any) {
    const message = error?.response?.data?.error || error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors de la vérification: ${message}`)
    console.error('Erreur vérification RADIUS:', error)
    userVerificationResult.value = {
      success: false,
      error: message
    }
  } finally {
    isVerifyingUser.value = false
    verifyingUserId.value = null
  }
}

function closeUserVerificationModal() {
  showUserVerificationModal.value = false
  userVerificationResult.value = null
}

function getStatusBadgeClass(status: string): string {
  switch (status) {
    case 'OK':
      return 'badge-success'
    case 'WARNING':
      return 'badge-warning'
    case 'ERROR':
      return 'badge-danger'
    case 'NOT_CONNECTED':
      return 'badge-gray'
    default:
      return 'badge-gray'
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case 'OK':
      return 'OK'
    case 'WARNING':
      return 'Avertissement'
    case 'ERROR':
      return 'Erreur'
    case 'NOT_CONNECTED':
      return 'Non connecté'
    default:
      return status
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

      <!-- Promotions -->
      <div class="promo-card">
        <div class="promo-header">
          <h3>Promotions</h3>
          <p class="text-gray">Activer/Désactiver l'accès RADIUS par promotion</p>
        </div>
        <div class="promo-list">
          <div v-for="promo in allPromotions" :key="promo.id" class="promo-item">
            <div>
              <div class="promo-name">{{ promo.name }}</div>
              <div class="promo-status" :class="promo.is_active ? 'active' : 'inactive'">
                {{ promo.is_active ? 'Active' : 'Désactivée' }}
              </div>
            </div>
            <button
              class="btn-ghost"
              :class="promo.is_active ? 'danger' : 'success'"
              @click="handleTogglePromotion(promo)"
            >
              {{ promo.is_active ? 'Désactiver' : 'Activer' }}
            </button>
          </div>
          <div v-if="allPromotions.length === 0" class="text-gray">Aucune promotion trouvée</div>
        </div>
      </div>

      <!-- Table -->
      <div class="table-container">
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
                <div v-if="user.promotion_name || user.matricule" class="info-cell">
                  <span v-if="user.promotion_name" class="badge badge-light">{{ user.promotion_name }}</span>
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
                  <!-- Verification button for RADIUS activated users -->
                  <button
                    v-if="user.is_radius_activated"
                    @click="handleVerifyUserRadius(user)"
                    class="action-btn verify"
                    :class="{ verifying: verifyingUserId === user.id }"
                    :disabled="isVerifyingUser"
                    title="Vérifier l'application du profil RADIUS"
                  >
                    <svg v-if="verifyingUserId === user.id" class="spinner" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-dasharray="32" stroke-dashoffset="32"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9c1.5 0 2.91.37 4.15 1.02" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      <path d="M22 4L12 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="2 3"/>
                    </svg>
                  </button>
                  <button
                    v-if="user.is_radius_activated"
                    @click="handleDeactivateRadius(user.id)"
                    class="action-btn danger"
                    title="Désactiver dans RADIUS"
                    :disabled="isDeactivating">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <line x1="7" y1="12" x2="17" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
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
              <select v-model="newUser.promotion" required>
                <option value="" disabled>Choisir une promotion</option>
                <option v-for="promo in promotions" :key="promo.id" :value="promo.id">
                  {{ promo.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Matricule *</label>
              <input v-model="newUser.matricule" type="text" placeholder="Matricule étudiant" required />
            </div>
          </div>

          <div class="form-group">
            <label>Profil RADIUS (optionnel)</label>
            <select v-model="newUser.profile">
              <option value="">Utiliser le profil de la promotion</option>
              <option v-for="profile in profiles" :key="profile.id" :value="profile.id">
                {{ profile.name }}
                ({{ profile.quota_type === 'limited' ? profile.data_volume_gb + ' Go' : 'Illimité' }} - {{ profile.bandwidth_upload_mbps }}/{{ profile.bandwidth_download_mbps }} Mbps)
              </option>
            </select>
            <small class="form-help">
              Si non défini, l'utilisateur héritera du profil de sa promotion. Le profil individuel a priorité sur le profil de la promotion.
            </small>
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

          <div class="form-row">
            <div class="form-group">
              <label>Promotion</label>
              <select v-model="selectedUser.promotion">
                <option :value="null">Aucune</option>
                <option v-for="promo in promotions" :key="promo.id" :value="promo.id">
                  {{ promo.name }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Profil RADIUS (optionnel)</label>
            <select v-model="selectedUser.profile">
              <option :value="null">Utiliser le profil de la promotion</option>
              <option v-for="profile in profiles" :key="profile.id" :value="profile.id">
                {{ profile.name }}
                ({{ profile.quota_type === 'limited' ? profile.data_volume_gb + ' Go' : 'Illimité' }} - {{ profile.bandwidth_upload_mbps }}/{{ profile.bandwidth_download_mbps }} Mbps)
              </option>
            </select>
            <small class="form-help">
              Si non défini, l'utilisateur héritera du profil de sa promotion. Le profil individuel a priorité sur le profil de la promotion.
            </small>
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

    <!-- Modal Vérification RADIUS Utilisateur -->
    <div v-if="showUserVerificationModal" class="modal-overlay" @click.self="closeUserVerificationModal">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>Vérification RADIUS : {{ selectedUser?.username }}</h3>
          <button @click="closeUserVerificationModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <!-- Loading -->
          <div v-if="isVerifyingUser" class="loading-container">
            <LoadingSpinner />
            <p class="loading-text">Vérification en cours...</p>
          </div>

          <!-- Error -->
          <div v-else-if="userVerificationResult && !userVerificationResult.success" class="error-container">
            <div class="error-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <h4>Erreur lors de la vérification</h4>
            <p>{{ userVerificationResult.error }}</p>
          </div>

          <!-- Results -->
          <div v-else-if="userVerificationResult && userVerificationResult.success">
            <!-- Status Badge -->
            <div class="verification-status-header">
              <span class="badge large" :class="getStatusBadgeClass(userVerificationResult.status || '')">
                {{ getStatusLabel(userVerificationResult.status || '') }}
              </span>
            </div>

            <!-- User Info -->
            <div class="verification-info">
              <p><strong>Utilisateur :</strong> {{ userVerificationResult.username }}</p>
              <p><strong>Profil :</strong> {{ userVerificationResult.profile_name || 'Non défini' }}</p>
              <p v-if="userVerificationResult.message"><strong>Message :</strong> {{ userVerificationResult.message }}</p>
              <p v-if="userVerificationResult.verified_at"><strong>Vérifié à :</strong> {{ new Date(userVerificationResult.verified_at).toLocaleString('fr-FR') }}</p>
            </div>

            <!-- Not Connected Message -->
            <div v-if="userVerificationResult.status === 'NOT_CONNECTED'" class="not-connected-message">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 16v-4M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <p>Cet utilisateur n'est pas actuellement connecté au hotspot. La vérification ne peut être effectuée que pour les utilisateurs connectés.</p>
            </div>

            <!-- Attributes Comparison -->
            <div v-if="userVerificationResult.expected_attributes || userVerificationResult.actual_attributes" class="attributes-section">
              <h4 class="section-title">Comparaison des attributs</h4>

              <div class="attributes-grid">
                <!-- Expected Attributes -->
                <div class="attributes-card">
                  <h5>Attributs attendus (FreeRADIUS)</h5>
                  <div v-if="userVerificationResult.expected_attributes && Object.keys(userVerificationResult.expected_attributes).length > 0">
                    <div v-for="(value, key) in userVerificationResult.expected_attributes" :key="key" class="attribute-item">
                      <code>{{ key }}</code>
                      <span>{{ value }}</span>
                    </div>
                  </div>
                  <div v-else class="empty-attributes">Aucun attribut</div>
                </div>

                <!-- Actual Attributes -->
                <div class="attributes-card">
                  <h5>Attributs réels (MikroTik)</h5>
                  <div v-if="userVerificationResult.actual_attributes && Object.keys(userVerificationResult.actual_attributes).length > 0">
                    <div v-for="(value, key) in userVerificationResult.actual_attributes" :key="key" class="attribute-item">
                      <code>{{ key }}</code>
                      <span>{{ value }}</span>
                    </div>
                  </div>
                  <div v-else class="empty-attributes">Aucun attribut (utilisateur non connecté)</div>
                </div>
              </div>
            </div>

            <!-- Differences Table -->
            <div v-if="userVerificationResult.differences && userVerificationResult.differences.length > 0" class="differences-section">
              <h4 class="section-title">Différences détectées</h4>
              <div class="differences-table">
                <table>
                  <thead>
                    <tr>
                      <th>Attribut</th>
                      <th>Attendu</th>
                      <th>Actuel</th>
                      <th>Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="diff in userVerificationResult.differences" :key="diff.attribute" :class="diff.status">
                      <td><code>{{ diff.attribute }}</code></td>
                      <td>{{ diff.expected ?? '-' }}</td>
                      <td>{{ diff.actual ?? '-' }}</td>
                      <td>
                        <span class="diff-status" :class="diff.status">
                          {{ diff.status === 'match' ? '✓' : diff.status === 'mismatch' ? '✗' : '?' }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeUserVerificationModal" class="btn-secondary">Fermer</button>
          <button
            v-if="userVerificationResult?.success && selectedUser"
            @click="handleVerifyUserRadius(selectedUser)"
            class="btn-primary"
            :disabled="isVerifyingUser"
          >
            Actualiser
          </button>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Contenu spécifique à la page utilisateurs - Dark Theme */
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
  font-family: 'Orbitron', monospace;
  font-size: 1.875rem;
  font-weight: 800;
  color: #F29400;
  margin-bottom: 0.5rem;
  text-shadow: 0 0 20px rgba(242, 148, 0, 0.3);
}

.page-subtitle {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.6);
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #F29400 0%, #008ecf 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(242, 148, 0, 0.3);
  white-space: nowrap;
}

.btn-primary svg {
  width: 20px;
  height: 20px;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(242, 148, 0, 0.4);
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
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
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
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

/* Statistiques */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-box {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  border-left: 4px solid #636362;
  transition: all 0.3s;
}

.stat-box:hover {
  border-color: rgba(0, 142, 207, 0.3);
  box-shadow: 0 8px 32px rgba(0, 142, 207, 0.15);
}

.stat-box.success {
  border-left-color: #10B981;
}

.stat-box.danger {
  border-left-color: #e53212;
}

.stat-box.info {
  border-left-color: #008ecf;
}

.stat-box.warning {
  border-left-color: #F29400;
}

.promo-card {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1rem;
  margin: 1.5rem 0;
}

.promo-header {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.promo-header h3 {
  font-family: 'Orbitron', monospace;
  color: #008ecf;
}

.promo-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.promo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.2);
  transition: all 0.3s;
}

.promo-item:hover {
  border-color: rgba(0, 142, 207, 0.3);
}

.promo-name {
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.promo-status {
  font-size: 12px;
}

.promo-status.active {
  color: #10B981;
}

.promo-status.inactive {
  color: #e53212;
}

.stat-value {
  font-family: 'Orbitron', monospace;
  font-size: 2rem;
  font-weight: 800;
  color: #F29400;
  margin-bottom: 0.25rem;
  text-shadow: 0 0 15px rgba(242, 148, 0, 0.3);
}

.stat-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
}

/* Filtres */
.filters-section {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
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
  color: rgba(255, 255, 255, 0.4);
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 3rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 0.875rem;
  background: rgba(0, 0, 0, 0.3);
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.search-input:focus {
  outline: none;
  border-color: #008ecf;
  box-shadow: 0 0 15px rgba(0, 142, 207, 0.2);
}

.filter-group {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.filter-select {
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.3s;
  min-width: 180px;
}

.filter-select:focus {
  outline: none;
  border-color: #008ecf;
  box-shadow: 0 0 15px rgba(0, 142, 207, 0.2);
}

/* Table */
.table-container {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: rgba(0, 142, 207, 0.1);
  border-bottom: 1px solid rgba(0, 142, 207, 0.2);
}

.data-table th {
  padding: 1rem 1.5rem;
  text-align: left;
  font-family: 'Orbitron', monospace;
  font-size: 0.75rem;
  font-weight: 600;
  color: #008ecf;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.data-table td {
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: rgba(0, 142, 207, 0.05);
}

.id-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  background: rgba(0, 142, 207, 0.2);
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #008ecf;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar-sm {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #F29400 0%, #008ecf 100%);
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
  color: rgba(255, 255, 255, 0.95);
}

.user-full-name {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.info-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.text-gray {
  color: rgba(255, 255, 255, 0.5);
}

.badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-success {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
  display: inline-flex;
  align-items: center;
}

.badge-danger {
  background: rgba(229, 50, 18, 0.2);
  color: #e53212;
}

.badge-info {
  background: rgba(0, 142, 207, 0.2);
  color: #008ecf;
}

.badge-gray {
  background: rgba(99, 99, 98, 0.3);
  color: rgba(255, 255, 255, 0.6);
}

.badge-warning {
  background: rgba(242, 148, 0, 0.2);
  color: #F29400;
  display: inline-flex;
  align-items: center;
}

.badge-light {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
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
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn svg {
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.6);
}

.action-btn.radius:hover:not(:disabled) {
  background: rgba(16, 185, 129, 0.2);
  border-color: #10B981;
}

.action-btn.radius:hover:not(:disabled) svg {
  color: #10B981;
}

.action-btn.radius-enable:hover:not(:disabled) {
  background: rgba(16, 185, 129, 0.2);
  border-color: #10B981;
}

.action-btn.radius-enable:hover:not(:disabled) svg {
  color: #10B981;
}

.action-btn.radius-disable:hover:not(:disabled) {
  background: rgba(242, 148, 0, 0.2);
  border-color: #F29400;
}

.action-btn.radius-disable:hover:not(:disabled) svg {
  color: #F29400;
}

.action-btn.edit:hover {
  background: rgba(0, 142, 207, 0.2);
  border-color: #008ecf;
}

.action-btn.edit:hover svg {
  color: #008ecf;
}

.action-btn.success:hover {
  background: rgba(16, 185, 129, 0.2);
  border-color: #10B981;
}

.action-btn.success:hover svg {
  color: #10B981;
}

.action-btn.danger:hover {
  background: rgba(229, 50, 18, 0.2);
  border-color: #e53212;
}

.action-btn.danger:hover svg {
  color: #e53212;
}

.action-btn.delete:hover {
  background: rgba(229, 50, 18, 0.2);
  border-color: #e53212;
}

.action-btn.delete:hover svg {
  color: #e53212;
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: rgba(255, 255, 255, 0.3);
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-family: 'Orbitron', monospace;
  font-size: 1.125rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 0.5rem;
}

.empty-state p {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: rgba(15, 15, 25, 0.95);
  border: 1px solid rgba(0, 142, 207, 0.2);
  border-radius: 16px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 50px rgba(0, 142, 207, 0.2);
}

.modal-large {
  max-width: 900px;
}

.modal-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  font-family: 'Orbitron', monospace;
  font-size: 1.25rem;
  font-weight: 700;
  color: #008ecf;
}

.modal-close {
  width: 36px;
  height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.modal-close svg {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.6);
}

.modal-close:hover {
  background: rgba(229, 50, 18, 0.2);
  border-color: #e53212;
}

.modal-close:hover svg {
  color: #e53212;
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
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  border: 2px solid transparent;
}

.summary-card.success {
  background: rgba(16, 185, 129, 0.15);
  border-color: #10B981;
}

.summary-card.danger {
  background: rgba(229, 50, 18, 0.15);
  border-color: #e53212;
}

.summary-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-family: 'Orbitron', monospace;
  font-size: 2.5rem;
  font-weight: 800;
  color: #F29400;
  margin-bottom: 0.25rem;
}

.summary-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 600;
}

.activation-section {
  margin-bottom: 2rem;
}

.section-title {
  font-family: 'Orbitron', monospace;
  font-size: 1.125rem;
  font-weight: 700;
  color: #008ecf;
  margin-bottom: 1rem;
}

.section-title.error {
  color: #e53212;
}

.activation-note {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: rgba(0, 142, 207, 0.1);
  border: 1px solid rgba(0, 142, 207, 0.2);
  border-left: 4px solid #008ecf;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.activation-note svg {
  width: 24px;
  height: 24px;
  color: #008ecf;
  flex-shrink: 0;
}

.activation-note p {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
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
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
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
  color: rgba(255, 255, 255, 0.95);
  display: block;
  margin-bottom: 0.25rem;
}

.user-name {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
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
  color: rgba(255, 255, 255, 0.5);
  font-weight: 600;
}

.detail-value {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.error-message {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(229, 50, 18, 0.15);
  border: 1px solid rgba(229, 50, 18, 0.3);
  border-radius: 8px;
  color: #e53212;
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
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.5rem;
}

.form-group input[type="text"],
.form-group input[type="email"],
.form-group input[type="password"],
.form-group select,
.form-group select.form-select {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.3s;
  background: rgba(0, 0, 0, 0.3);
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
}

.form-group input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.form-group input:focus,
.form-group select:focus,
.form-group select.form-select:focus {
  outline: none;
  border-color: #008ecf;
  box-shadow: 0 0 15px rgba(0, 142, 207, 0.2);
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
  accent-color: #F29400;
}

.checkbox-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.checkbox-text strong {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.checkbox-text small {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.info-note {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(0, 142, 207, 0.1);
  border: 1px solid rgba(0, 142, 207, 0.2);
  border-left: 4px solid #008ecf;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.info-note svg {
  width: 20px;
  height: 20px;
  color: #008ecf;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-note p {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
}

.loading-container {
  padding: 4rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-text {
  margin-top: 1rem;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.875rem;
}

/* Verification Button */
.action-btn.verify:hover:not(:disabled) {
  background: rgba(0, 142, 207, 0.2);
  border-color: #008ecf;
}

.action-btn.verify:hover:not(:disabled) svg {
  color: #008ecf;
}

.action-btn.verify.verifying {
  background: rgba(0, 142, 207, 0.2);
  border-color: #008ecf;
}

.action-btn .spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Verification Modal Styles */
.error-container {
  text-align: center;
  padding: 2rem;
}

.error-icon svg {
  width: 48px;
  height: 48px;
  color: #e53212;
  margin-bottom: 1rem;
}

.error-container h4 {
  font-family: 'Orbitron', monospace;
  font-size: 1.125rem;
  font-weight: 600;
  color: #e53212;
  margin-bottom: 0.5rem;
}

.error-container p {
  color: rgba(255, 255, 255, 0.6);
}

.verification-status-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.badge.large {
  font-size: 1rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
}

.verification-info {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.verification-info p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
}

.not-connected-message {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: rgba(99, 99, 98, 0.2);
  border: 1px solid rgba(99, 99, 98, 0.3);
  border-left: 4px solid #636362;
  border-radius: 8px;
  margin: 1.5rem 0;
}

.not-connected-message svg {
  width: 24px;
  height: 24px;
  color: rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}

.not-connected-message p {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.attributes-section {
  margin-top: 1.5rem;
}

.attributes-section .section-title {
  font-family: 'Orbitron', monospace;
  font-size: 0.875rem;
  font-weight: 700;
  color: #008ecf;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(0, 142, 207, 0.2);
}

.attributes-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.attributes-card {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
}

.attributes-card h5 {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.8125rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.75rem;
}

.attribute-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.attribute-item:last-child {
  border-bottom: none;
}

.attribute-item code {
  background: rgba(0, 142, 207, 0.2);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.75rem;
  color: #008ecf;
}

.attribute-item span {
  font-size: 0.8125rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.empty-attributes {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.8125rem;
  font-style: italic;
}

.differences-section {
  margin-top: 1.5rem;
}

.differences-table {
  overflow-x: auto;
}

.differences-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.differences-table th,
.differences-table td {
  padding: 0.5rem;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.differences-table th {
  background: rgba(0, 142, 207, 0.1);
  font-weight: 600;
  color: #008ecf;
  text-transform: uppercase;
  font-size: 0.6875rem;
}

.differences-table tr.match {
  background: rgba(16, 185, 129, 0.1);
}

.differences-table tr.mismatch {
  background: rgba(229, 50, 18, 0.1);
}

.differences-table tr.missing {
  background: rgba(242, 148, 0, 0.1);
}

.differences-table code {
  background: rgba(0, 142, 207, 0.2);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.75rem;
  color: #008ecf;
}

.diff-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.75rem;
}

.diff-status.match {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.diff-status.mismatch {
  background: rgba(229, 50, 18, 0.2);
  color: #e53212;
}

.diff-status.missing {
  background: rgba(242, 148, 0, 0.2);
  color: #F29400;
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

  .attributes-grid {
    grid-template-columns: 1fr;
  }
}
</style>
