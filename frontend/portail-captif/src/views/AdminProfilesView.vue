<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { useUserStore } from '@/stores/user'
import { usePromotionStore } from '@/stores/promotion'
import { useNotificationStore } from '@/stores/notification'
import { profileService, type ProfileVerificationResult, type VerificationResult } from '@/services/profile.service'
import AdminLayout from '@/layouts/AdminLayout.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import type { Profile } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const profileStore = useProfileStore()
const userStore = useUserStore()
const promotionStore = usePromotionStore()
const notificationStore = useNotificationStore()

const profiles = computed(() => profileStore.profiles)
const isLoading = computed(() => profileStore.isLoading)

const showAddModal = ref(false)
const showEditModal = ref(false)
const showDetailsModal = ref(false)
const selectedProfile = ref<Profile | null>(null)
const searchQuery = ref('')
const filterStatus = ref('all')
const filterQuotaType = ref('all')
const isDeleting = ref(false)
const isSyncingRadius = ref<number | null>(null) // ID du profil en cours de sync

// Variables pour les détails du profil (utilisateurs et promotions)
const profileUsers = ref<any[]>([])
const profilePromotions = ref<any[]>([])
const isLoadingDetails = ref(false)

// Variables pour la vérification RADIUS
const showVerificationModal = ref(false)
const isVerifying = ref(false)
const verificationResult = ref<ProfileVerificationResult | null>(null)

const newProfile = ref({
  name: '',
  description: '',
  bandwidth_upload: 5,  // 5 Mbps par défaut
  bandwidth_download: 10,  // 10 Mbps par défaut
  quota_type: 'limited' as 'unlimited' | 'limited',
  data_volume: 53687091200,  // 50 Go par défaut
  validity_duration: 30,
  session_timeout: 28800,  // 8 heures
  idle_timeout: 600,  // 10 minutes
  simultaneous_use: 1,
  is_active: true,
  assign_to_promotions: [] as number[],
  assign_to_users: [] as number[]
})

const promotions = computed(() => {
  if (!Array.isArray(promotionStore.promotions)) return []
  return promotionStore.promotions.filter(p => p && p.is_active)
})

const users = computed(() => {
  if (!Array.isArray(userStore.users)) return []
  return userStore.users.filter(u => u && u.is_active && !u.is_staff)
})

// Durées disponibles
const durationOptions = [
  { value: 7, label: '7 jours' },
  { value: 14, label: '14 jours' },
  { value: 30, label: '30 jours' },
  { value: 60, label: '60 jours' },
  { value: 90, label: '90 jours' },
  { value: 180, label: '180 jours' },
  { value: 365, label: '365 jours' }
]

// Filtrage des profils
const filteredProfiles = computed(() => {
  // S'assurer que profiles.value est bien un tableau
  if (!Array.isArray(profiles.value)) {
    return []
  }

  let filtered = profiles.value

  // Filtre par recherche
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(p =>
      p && (
        p.name?.toLowerCase().includes(query) ||
        p.description?.toLowerCase().includes(query)
      )
    )
  }

  // Filtre par statut
  if (filterStatus.value !== 'all') {
    if (filterStatus.value === 'active') {
      filtered = filtered.filter(p => p && p.is_active)
    } else {
      filtered = filtered.filter(p => p && !p.is_active)
    }
  }

  // Filtre par type de quota
  if (filterQuotaType.value !== 'all') {
    filtered = filtered.filter(p => p && p.quota_type === filterQuotaType.value)
  }

  // Filtrer les valeurs null ou undefined
  return filtered.filter(p => p != null)
})

// Statistiques
const stats = computed(() => {
  // S'assurer que profiles.value est bien un tableau
  if (!Array.isArray(profiles.value)) {
    return { total: 0, active: 0, inactive: 0, limited: 0, unlimited: 0 }
  }

  return {
    total: profiles.value.length,
    active: profiles.value.filter(p => p && p.is_active).length,
    inactive: profiles.value.filter(p => p && !p.is_active).length,
    limited: profiles.value.filter(p => p && p.quota_type === 'limited').length,
    unlimited: profiles.value.filter(p => p && p.quota_type === 'unlimited').length
  }
})

onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    await Promise.all([
      profileStore.fetchProfiles(),
      promotionStore.fetchPromotions(),
      userStore.fetchUsers()
    ])
  } catch (error: any) {
    const message = error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors du chargement: ${message}`)
    console.error('Erreur chargement profils:', error)
  }
})

function openAddModal() {
  newProfile.value = {
    name: '',
    description: '',
    bandwidth_upload: 5,
    bandwidth_download: 10,
    quota_type: 'limited',
    data_volume: 53687091200,
    validity_duration: 30,
    session_timeout: 28800,
    idle_timeout: 600,
    simultaneous_use: 1,
    is_active: true,
    assign_to_promotions: [],
    assign_to_users: []
  }
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
}

async function handleAddProfile() {
  // Validation
  if (!newProfile.value.name) {
    notificationStore.warning('Veuillez remplir le nom du profil')
    return
  }

  try {
    await profileStore.createProfile(newProfile.value)
    notificationStore.success('Profil créé avec succès')
    closeAddModal()
  } catch (error) {
    notificationStore.error(profileStore.error || 'Erreur lors de la création')
  }
}

// Variables pour l'édition avec assignation
const editAssignPromotions = ref<number[]>([])
const editAssignUsers = ref<number[]>([])
const isLoadingAssignments = ref(false)

async function handleEdit(profile: Profile) {
  selectedProfile.value = { ...profile }
  editAssignPromotions.value = []
  editAssignUsers.value = []
  showEditModal.value = true

  // Charger les assignations actuelles
  isLoadingAssignments.value = true
  try {
    const [usersData, promotionsData] = await Promise.all([
      profileStore.getProfileUsers(profile.id),
      profileStore.getProfilePromotions(profile.id)
    ])
    // Extraire les IDs des utilisateurs et promotions actuellement assignés
    editAssignUsers.value = (usersData.users || []).map((u: any) => u.id)
    editAssignPromotions.value = (promotionsData.promotions || []).map((p: any) => p.id)
  } catch (error) {
    console.error('Erreur lors du chargement des assignations:', error)
  } finally {
    isLoadingAssignments.value = false
  }
}

function closeEditModal() {
  showEditModal.value = false
  selectedProfile.value = null
}

async function handleUpdateProfile() {
  if (!selectedProfile.value) return

  try {
    await profileStore.updateProfile(selectedProfile.value.id, {
      name: selectedProfile.value.name,
      description: selectedProfile.value.description,
      bandwidth_upload: selectedProfile.value.bandwidth_upload,
      bandwidth_download: selectedProfile.value.bandwidth_download,
      quota_type: selectedProfile.value.quota_type,
      data_volume: selectedProfile.value.data_volume,
      validity_duration: selectedProfile.value.validity_duration,
      session_timeout: selectedProfile.value.session_timeout,
      idle_timeout: selectedProfile.value.idle_timeout,
      simultaneous_use: selectedProfile.value.simultaneous_use,
      is_active: selectedProfile.value.is_active,
      assign_to_promotions: editAssignPromotions.value,
      assign_to_users: editAssignUsers.value
    })

    notificationStore.success('Profil modifié avec succès')
    closeEditModal()
  } catch (error) {
    notificationStore.error(profileStore.error || 'Erreur lors de la modification')
  }
}

async function handleDelete(profile: Profile) {
  if (isDeleting.value) return

  if (!confirm(`Voulez-vous vraiment supprimer le profil "${profile.name}" ?\n\nAttention: Cette action peut affecter ${profile.users_count || 0} utilisateur(s) et ${profile.promotions_count || 0} promotion(s).`)) {
    return
  }

  isDeleting.value = true
  try {
    await profileStore.deleteProfile(profile.id)
    notificationStore.success('Profil supprimé avec succès')
  } catch (error) {
    notificationStore.error('Erreur lors de la suppression')
  } finally {
    isDeleting.value = false
  }
}

async function handleViewDetails(profile: Profile) {
  selectedProfile.value = profile
  isLoadingDetails.value = true
  showDetailsModal.value = true

  try {
    const [usersData, promotionsData] = await Promise.all([
      profileStore.getProfileUsers(profile.id),
      profileStore.getProfilePromotions(profile.id)
    ])
    profileUsers.value = usersData.users || []
    profilePromotions.value = promotionsData.promotions || []
  } catch (error) {
    notificationStore.error('Erreur lors du chargement des détails')
  } finally {
    isLoadingDetails.value = false
  }
}

function closeDetailsModal() {
  showDetailsModal.value = false
  selectedProfile.value = null
  profileUsers.value = []
  profilePromotions.value = []
}

// Fonctions utilitaires
function formatBandwidth(kbps: number): string {
  return `${(kbps / 1024).toFixed(2)} Mbps`
}

function formatDataVolume(bytes: number): string {
  return `${(bytes / (1024 ** 3)).toFixed(2)} Go`
}

function formatDuration(days: number): string {
  if (days === 7) return '7 jours (1 semaine)'
  if (days === 14) return '14 jours (2 semaines)'
  if (days === 30) return '30 jours (1 mois)'
  if (days === 60) return '60 jours (2 mois)'
  if (days === 90) return '90 jours (3 mois)'
  if (days === 180) return '180 jours (6 mois)'
  if (days === 365) return '365 jours (1 an)'
  return `${days} jours`
}

function formatSeconds(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours}h${minutes > 0 ? ` ${minutes}min` : ''}`
  return `${minutes}min`
}

// Activation dans RADIUS
async function handleActivateInRadius(profile: Profile) {
  if (isSyncingRadius.value !== null) return

  if (!profile.is_active) {
    notificationStore.warning('Le profil doit être actif pour être activé dans RADIUS')
    return
  }

  isSyncingRadius.value = profile.id
  try {
    const result = await profileService.activateInRadius(profile.id)
    if (result.success) {
      notificationStore.success(
        `Profil "${profile.name}" activé dans RADIUS. ${result.users_synced || 0} utilisateur(s) synchronisé(s).`
      )
      // Rafraîchir la liste des profils
      await profileStore.fetchProfiles()
    } else {
      notificationStore.error(result.error || 'Erreur lors de l\'activation dans RADIUS')
    }
  } catch (error: any) {
    const message = error?.response?.data?.error || error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors de l'activation RADIUS: ${message}`)
    console.error('Erreur activation RADIUS:', error)
  } finally {
    isSyncingRadius.value = null
  }
}

async function handleDeactivateInRadius(profile: Profile) {
  if (isSyncingRadius.value !== null) return

  if (!confirm(`Voulez-vous vraiment désactiver le profil "${profile.name}" de RADIUS ?\n\nLes utilisateurs de ce profil ne pourront plus se connecter via RADIUS.`)) {
    return
  }

  isSyncingRadius.value = profile.id
  try {
    const result = await profileService.deactivateInRadius(profile.id)
    if (result.success) {
      notificationStore.success(`Profil "${profile.name}" désactivé de RADIUS`)
      // Rafraîchir la liste des profils
      await profileStore.fetchProfiles()
    } else {
      notificationStore.error(result.error || 'Erreur lors de la désactivation dans RADIUS')
    }
  } catch (error: any) {
    const message = error?.response?.data?.error || error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors de la désactivation RADIUS: ${message}`)
    console.error('Erreur désactivation RADIUS:', error)
  } finally {
    isSyncingRadius.value = null
  }
}

// Vérification de l'application des profils RADIUS
async function handleVerifyProfile(profile: Profile) {
  if (isVerifying.value) return

  selectedProfile.value = profile
  isVerifying.value = true
  showVerificationModal.value = true
  verificationResult.value = null

  try {
    const result = await profileService.verifyProfile(profile.id)
    verificationResult.value = result

    if (result.success && result.summary) {
      const { ok, warning, error } = result.summary
      if (error > 0) {
        notificationStore.warning(`Vérification terminée: ${error} erreur(s) détectée(s)`)
      } else if (warning > 0) {
        notificationStore.warning(`Vérification terminée: ${warning} avertissement(s)`)
      } else if (ok > 0) {
        notificationStore.success(`Vérification réussie: ${ok} utilisateur(s) OK`)
      } else {
        notificationStore.info('Aucun utilisateur connecté à vérifier')
      }
    } else if (!result.success) {
      notificationStore.error(result.error || 'Erreur lors de la vérification')
    }
  } catch (error: any) {
    const message = error?.response?.data?.error || error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors de la vérification: ${message}`)
    console.error('Erreur vérification RADIUS:', error)
    verificationResult.value = {
      success: false,
      error: message
    }
  } finally {
    isVerifying.value = false
  }
}

function closeVerificationModal() {
  showVerificationModal.value = false
  verificationResult.value = null
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
  <AdminLayout activePage="profiles">
    <div class="content-header">
      <div>
        <h2 class="page-title">Gestion des profils</h2>
        <p class="page-subtitle">Créer, modifier et gérer les profils d'abonnement</p>
      </div>
      <div class="header-actions">
        <button @click="openAddModal" class="btn-primary">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <line x1="12" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Nouveau profil
        </button>
      </div>
    </div>

    <!-- Statistiques -->
    <div class="stats-row">
      <div class="stat-box">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">Total profils</div>
      </div>
      <div class="stat-box success">
        <div class="stat-value">{{ stats.active }}</div>
        <div class="stat-label">Actifs</div>
      </div>
      <div class="stat-box danger">
        <div class="stat-value">{{ stats.inactive }}</div>
        <div class="stat-label">Inactifs</div>
      </div>
      <div class="stat-box info">
        <div class="stat-value">{{ stats.limited }}</div>
        <div class="stat-label">Quota limité</div>
      </div>
      <div class="stat-box warning">
        <div class="stat-value">{{ stats.unlimited }}</div>
        <div class="stat-label">Quota illimité</div>
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
          placeholder="Rechercher un profil (nom, description)..."
          class="search-input"
        />
      </div>

      <div class="filter-group">
        <select v-model="filterStatus" class="filter-select">
          <option value="all">Tous les statuts</option>
          <option value="active">Actifs</option>
          <option value="inactive">Inactifs</option>
        </select>

        <select v-model="filterQuotaType" class="filter-select">
          <option value="all">Tous les quotas</option>
          <option value="limited">Quota limité</option>
          <option value="unlimited">Quota illimité</option>
        </select>
      </div>
    </div>

    <!-- Table -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nom</th>
            <th>Bande passante</th>
            <th>Quota</th>
            <th>Durée</th>
            <th>Utilisation</th>
            <th>Statut</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="profile in filteredProfiles" :key="profile.id">
            <td><span class="id-badge">{{ profile.id }}</span></td>
            <td>
              <div class="name-cell">
                <div class="name-text">{{ profile.name }}</div>
                <div v-if="profile.description" class="description-text">
                  {{ profile.description }}
                </div>
              </div>
            </td>
            <td>
              <div class="bandwidth-cell">
                <span class="bandwidth-badge upload">↑ {{ profile.bandwidth_upload_mbps }} Mbps</span>
                <span class="bandwidth-badge download">↓ {{ profile.bandwidth_download_mbps }} Mbps</span>
              </div>
            </td>
            <td>
              <div v-if="profile.quota_type === 'limited'" class="quota-cell">
                <span class="quota-badge limited">{{ profile.data_volume_gb }} Go</span>
              </div>
              <div v-else class="quota-cell">
                <span class="quota-badge unlimited">Illimité</span>
              </div>
            </td>
            <td>
              <span class="duration-badge">{{ profile.validity_duration }} jours</span>
            </td>
            <td>
              <div class="usage-cell">
                <span class="usage-badge">{{ profile.users_count || 0 }} utilisateurs</span>
                <span class="usage-badge">{{ profile.promotions_count || 0 }} promotions</span>
              </div>
            </td>
            <td>
              <span v-if="profile.is_active" class="badge badge-success">Actif</span>
              <span v-else class="badge badge-gray">Inactif</span>
            </td>
            <td>
              <div class="action-buttons">
                <button @click="handleViewDetails(profile)" class="action-btn info" title="Voir les détails">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    <path d="M12 16v-4M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </button>

                <button
                  @click="handleVerifyProfile(profile)"
                  class="action-btn verify"
                  :disabled="isVerifying"
                  title="Vérifier l'application du profil RADIUS"
                >
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9c1.5 0 2.91.37 4.15 1.02" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    <path d="M22 4L12 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="2 3"/>
                  </svg>
                </button>

                <button
                  @click="handleActivateInRadius(profile)"
                  class="action-btn radius"
                  :class="{ syncing: isSyncingRadius === profile.id }"
                  :disabled="isSyncingRadius !== null || !profile.is_active"
                  :title="profile.is_active ? 'Activer dans RADIUS' : 'Le profil doit être actif'"
                >
                  <svg v-if="isSyncingRadius === profile.id" class="spinner" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-dasharray="32" stroke-dashoffset="32"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                    <path d="M12 1v4M12 19v4M23 12h-4M5 12H1M20.5 3.5l-2.8 2.8M6.3 17.7l-2.8 2.8M20.5 20.5l-2.8-2.8M6.3 6.3L3.5 3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </button>

                <button @click="handleEdit(profile)" class="action-btn edit" title="Modifier">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>

                <button @click="handleDelete(profile)" class="action-btn delete" title="Supprimer">
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

      <div v-if="filteredProfiles.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
          <line x1="12" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <h3>Aucun profil trouvé</h3>
        <p>Aucun profil ne correspond à vos critères de recherche</p>
      </div>
    </div>

    <!-- Modal Ajout -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>Ajouter un profil</h3>
          <button @click="closeAddModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-section">
            <h4 class="section-title">Informations de base</h4>

            <div class="form-group">
              <label>Nom du profil *</label>
              <input v-model="newProfile.name" type="text" placeholder="Ex: Étudiant, Personnel, Invité..." required />
            </div>

            <div class="form-group">
              <label>Description</label>
              <textarea v-model="newProfile.description" rows="2" placeholder="Description optionnelle"></textarea>
            </div>

            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input v-model="newProfile.is_active" type="checkbox" />
                <span class="checkbox-text">
                  <strong>Profil actif</strong>
                  <small>Les profils actifs peuvent être assignés aux utilisateurs et promotions</small>
                </span>
              </label>
            </div>
          </div>

          <div class="form-section">
            <h4 class="section-title">Bande passante</h4>

            <div class="form-row">
              <div class="form-group">
                <label>Upload (Mbps) *</label>
                <input v-model.number="newProfile.bandwidth_upload" type="number" min="1" step="1" required />
                <small class="help-text">{{ newProfile.bandwidth_upload }} Mbps</small>
              </div>
              <div class="form-group">
                <label>Download (Mbps) *</label>
                <input v-model.number="newProfile.bandwidth_download" type="number" min="1" step="1" required />
                <small class="help-text">{{ newProfile.bandwidth_download }} Mbps</small>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4 class="section-title">Quota de données</h4>

            <div class="form-group">
              <label>Type de quota *</label>
              <select v-model="newProfile.quota_type" required>
                <option value="limited">Limité</option>
                <option value="unlimited">Illimité</option>
              </select>
            </div>

            <div v-if="newProfile.quota_type === 'limited'" class="form-row">
              <div class="form-group">
                <label>Volume de données (octets) *</label>
                <input v-model.number="newProfile.data_volume" type="number" min="1073741824" step="1073741824" required />
                <small class="help-text">{{ formatDataVolume(newProfile.data_volume) }}</small>
              </div>
              <div class="form-group">
                <label>Durée de validité *</label>
                <select v-model.number="newProfile.validity_duration" required>
                  <option v-for="opt in durationOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4 class="section-title">Paramètres de session RADIUS</h4>

            <div class="form-row">
              <div class="form-group">
                <label>Session timeout (secondes)</label>
                <input v-model.number="newProfile.session_timeout" type="number" min="60" step="60" />
                <small class="help-text">{{ formatSeconds(newProfile.session_timeout) }}</small>
              </div>
              <div class="form-group">
                <label>Idle timeout (secondes)</label>
                <input v-model.number="newProfile.idle_timeout" type="number" min="60" step="60" />
                <small class="help-text">{{ formatSeconds(newProfile.idle_timeout) }}</small>
              </div>
            </div>

            <div class="form-group">
              <label>Connexions simultanées</label>
              <input v-model.number="newProfile.simultaneous_use" type="number" min="1" max="10" />
              <small class="help-text">Nombre de connexions simultanées autorisées</small>
            </div>
          </div>

          <div class="form-section">
            <h4 class="section-title">Assigner ce profil à (optionnel)</h4>
            <p class="section-description">Sélectionnez les promotions et/ou utilisateurs qui utiliseront ce profil automatiquement</p>

            <div class="form-group">
              <label>Promotions</label>
              <select v-model="newProfile.assign_to_promotions" multiple size="5">
                <option v-for="promo in promotions" :key="promo.id" :value="promo.id">
                  {{ promo.name }} ({{ promo.user_count || 0 }} utilisateurs)
                </option>
              </select>
              <small class="form-help">Maintenez Ctrl/Cmd pour sélectionner plusieurs promotions</small>
            </div>

            <div class="form-group">
              <label>Utilisateurs individuels</label>
              <select v-model="newProfile.assign_to_users" multiple size="5">
                <option v-for="user in users" :key="user.id" :value="user.id">
                  {{ user.first_name }} {{ user.last_name }} ({{ user.username }})
                </option>
              </select>
              <small class="form-help">Maintenez Ctrl/Cmd pour sélectionner plusieurs utilisateurs</small>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeAddModal" class="btn-secondary">Annuler</button>
          <button @click="handleAddProfile" class="btn-primary">Créer le profil</button>
        </div>
      </div>
    </div>

    <!-- Modal Édition -->
    <div v-if="showEditModal && selectedProfile" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>Modifier le profil</h3>
          <button @click="closeEditModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <!-- Même structure que le modal d'ajout mais avec selectedProfile au lieu de newProfile -->
          <div class="form-section">
            <h4 class="section-title">Informations de base</h4>

            <div class="form-group">
              <label>Nom du profil *</label>
              <input v-model="selectedProfile.name" type="text" required />
            </div>

            <div class="form-group">
              <label>Description</label>
              <textarea v-model="selectedProfile.description" rows="2"></textarea>
            </div>

            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input v-model="selectedProfile.is_active" type="checkbox" />
                <span class="checkbox-text">
                  <strong>Profil actif</strong>
                  <small>Les profils actifs peuvent être assignés aux utilisateurs et promotions</small>
                </span>
              </label>
            </div>
          </div>

          <div class="form-section">
            <h4 class="section-title">Bande passante</h4>

            <div class="form-row">
              <div class="form-group">
                <label>Upload (Mbps) *</label>
                <input v-model.number="selectedProfile.bandwidth_upload" type="number" min="1" step="1" required />
                <small class="help-text">{{ selectedProfile.bandwidth_upload }} Mbps</small>
              </div>
              <div class="form-group">
                <label>Download (Mbps) *</label>
                <input v-model.number="selectedProfile.bandwidth_download" type="number" min="1" step="1" required />
                <small class="help-text">{{ selectedProfile.bandwidth_download }} Mbps</small>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4 class="section-title">Quota de données</h4>

            <div class="form-group">
              <label>Type de quota *</label>
              <select v-model="selectedProfile.quota_type" required>
                <option value="limited">Limité</option>
                <option value="unlimited">Illimité</option>
              </select>
            </div>

            <div v-if="selectedProfile.quota_type === 'limited'" class="form-row">
              <div class="form-group">
                <label>Volume de données (octets) *</label>
                <input v-model.number="selectedProfile.data_volume" type="number" min="1073741824" step="1073741824" required />
                <small class="help-text">{{ formatDataVolume(selectedProfile.data_volume) }}</small>
              </div>
              <div class="form-group">
                <label>Durée de validité *</label>
                <select v-model.number="selectedProfile.validity_duration" required>
                  <option v-for="opt in durationOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4 class="section-title">Paramètres de session RADIUS</h4>

            <div class="form-row">
              <div class="form-group">
                <label>Session timeout (secondes)</label>
                <input v-model.number="selectedProfile.session_timeout" type="number" min="60" step="60" />
                <small class="help-text">{{ formatSeconds(selectedProfile.session_timeout) }}</small>
              </div>
              <div class="form-group">
                <label>Idle timeout (secondes)</label>
                <input v-model.number="selectedProfile.idle_timeout" type="number" min="60" step="60" />
                <small class="help-text">{{ formatSeconds(selectedProfile.idle_timeout) }}</small>
              </div>
            </div>

            <div class="form-group">
              <label>Connexions simultanées</label>
              <input v-model.number="selectedProfile.simultaneous_use" type="number" min="1" max="10" />
              <small class="help-text">Nombre de connexions simultanées autorisées</small>
            </div>
          </div>

          <div class="form-section">
            <h4 class="section-title">Assigner ce profil à</h4>
            <p class="section-description">Modifiez les promotions et/ou utilisateurs qui utilisent ce profil</p>

            <div v-if="isLoadingAssignments" class="loading-assignments">
              <LoadingSpinner />
              <span>Chargement des assignations...</span>
            </div>

            <template v-else>
              <div class="form-group">
                <label>Promotions</label>
                <select v-model="editAssignPromotions" multiple size="5">
                  <option v-for="promo in promotions" :key="promo.id" :value="promo.id">
                    {{ promo.name }} ({{ promo.user_count || 0 }} utilisateurs)
                  </option>
                </select>
                <small class="form-help">Maintenez Ctrl/Cmd pour sélectionner plusieurs promotions</small>
              </div>

              <div class="form-group">
                <label>Utilisateurs individuels</label>
                <select v-model="editAssignUsers" multiple size="5">
                  <option v-for="user in users" :key="user.id" :value="user.id">
                    {{ user.first_name }} {{ user.last_name }} ({{ user.username }})
                  </option>
                </select>
                <small class="form-help">Maintenez Ctrl/Cmd pour sélectionner plusieurs utilisateurs</small>
              </div>
            </template>
          </div>

          <div v-if="selectedProfile.users_count && selectedProfile.users_count > 0" class="info-note">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 16v-4M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <p>Ce profil est utilisé par {{ selectedProfile.users_count }} utilisateur(s) et {{ selectedProfile.promotions_count || 0 }} promotion(s)</p>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeEditModal" class="btn-secondary">Annuler</button>
          <button @click="handleUpdateProfile" class="btn-primary">Enregistrer</button>
        </div>
      </div>
    </div>

    <!-- Modal Détails -->
    <div v-if="showDetailsModal && selectedProfile" class="modal-overlay" @click.self="closeDetailsModal">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>Détails du profil : {{ selectedProfile.name }}</h3>
          <button @click="closeDetailsModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div v-if="isLoadingDetails" class="loading-container">
            <LoadingSpinner />
          </div>

          <div v-else>
            <div class="details-section">
              <h4 class="section-title">Paramètres du profil</h4>
              <div class="details-grid">
                <div class="detail-item">
                  <span class="detail-label">Bande passante :</span>
                  <span class="detail-value">↑{{ selectedProfile.bandwidth_upload_mbps }} Mbps / ↓{{ selectedProfile.bandwidth_download_mbps }} Mbps</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Quota :</span>
                  <span class="detail-value">{{ selectedProfile.quota_type === 'limited' ? `${selectedProfile.data_volume_gb} Go` : 'Illimité' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Durée de validité :</span>
                  <span class="detail-value">{{ formatDuration(selectedProfile.validity_duration) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Session timeout :</span>
                  <span class="detail-value">{{ formatSeconds(selectedProfile.session_timeout) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Idle timeout :</span>
                  <span class="detail-value">{{ formatSeconds(selectedProfile.idle_timeout) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Connexions simultanées :</span>
                  <span class="detail-value">{{ selectedProfile.simultaneous_use }}</span>
                </div>
              </div>
            </div>

            <div class="details-section">
              <h4 class="section-title">Promotions ({{ profilePromotions.length }})</h4>
              <div v-if="profilePromotions.length === 0" class="empty-message">
                Aucune promotion n'utilise ce profil
              </div>
              <div v-else class="list-grid">
                <div v-for="promo in profilePromotions" :key="promo.id" class="list-item">
                  <div class="list-item-name">{{ promo.name }}</div>
                  <div class="list-item-meta">{{ promo.user_count }} utilisateurs</div>
                </div>
              </div>
            </div>

            <div class="details-section">
              <h4 class="section-title">Utilisateurs directs ({{ profileUsers.length }})</h4>
              <div v-if="profileUsers.length === 0" class="empty-message">
                Aucun utilisateur n'a ce profil assigné directement
              </div>
              <div v-else class="list-grid">
                <div v-for="user in profileUsers" :key="user.id" class="list-item">
                  <div class="list-item-name">{{ user.first_name }} {{ user.last_name }}</div>
                  <div class="list-item-meta">@{{ user.username }} <span v-if="user.promotion">({{ user.promotion.name }})</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeDetailsModal" class="btn-secondary">Fermer</button>
        </div>
      </div>
    </div>

    <!-- Modal Vérification RADIUS -->
    <div v-if="showVerificationModal" class="modal-overlay" @click.self="closeVerificationModal">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>Vérification RADIUS : {{ selectedProfile?.name }}</h3>
          <button @click="closeVerificationModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <!-- Loading -->
          <div v-if="isVerifying" class="loading-container">
            <LoadingSpinner />
            <p class="loading-text">Vérification en cours...</p>
          </div>

          <!-- Error -->
          <div v-else-if="verificationResult && !verificationResult.success" class="error-container">
            <div class="error-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <h4>Erreur lors de la vérification</h4>
            <p>{{ verificationResult.error }}</p>
          </div>

          <!-- Results -->
          <div v-else-if="verificationResult && verificationResult.success">
            <!-- Summary -->
            <div class="verification-summary">
              <div class="summary-card success" v-if="verificationResult.summary?.ok">
                <div class="summary-icon">✓</div>
                <div class="summary-value">{{ verificationResult.summary.ok }}</div>
                <div class="summary-label">OK</div>
              </div>
              <div class="summary-card warning" v-if="verificationResult.summary?.warning">
                <div class="summary-icon">!</div>
                <div class="summary-value">{{ verificationResult.summary.warning }}</div>
                <div class="summary-label">Avertissements</div>
              </div>
              <div class="summary-card danger" v-if="verificationResult.summary?.error">
                <div class="summary-icon">✗</div>
                <div class="summary-value">{{ verificationResult.summary.error }}</div>
                <div class="summary-label">Erreurs</div>
              </div>
              <div class="summary-card gray" v-if="verificationResult.summary?.not_connected">
                <div class="summary-icon">○</div>
                <div class="summary-value">{{ verificationResult.summary.not_connected }}</div>
                <div class="summary-label">Non connectés</div>
              </div>
            </div>

            <!-- Info -->
            <div class="verification-info">
              <p><strong>Profil :</strong> {{ verificationResult.profile_name }}</p>
              <p><strong>Utilisateurs du profil :</strong> {{ verificationResult.total_users }}</p>
              <p><strong>Utilisateurs connectés :</strong> {{ verificationResult.connected_users }}</p>
            </div>

            <!-- No connected users -->
            <div v-if="!verificationResult.results || verificationResult.results.length === 0" class="empty-message">
              <p>Aucun utilisateur de ce profil n'est actuellement connecté au hotspot.</p>
            </div>

            <!-- User Results -->
            <div v-else class="verification-results">
              <h4 class="section-title">Résultats par utilisateur</h4>
              <div class="results-list">
                <div
                  v-for="result in verificationResult.results"
                  :key="result.user_id"
                  class="result-card"
                  :class="result.status?.toLowerCase()"
                >
                  <div class="result-header">
                    <div class="result-user">
                      <strong>{{ result.username }}</strong>
                      <span class="badge" :class="getStatusBadgeClass(result.status || '')">
                        {{ getStatusLabel(result.status || '') }}
                      </span>
                    </div>
                    <span class="result-profile">{{ result.profile_name }}</span>
                  </div>

                  <!-- Message -->
                  <div v-if="result.message" class="result-message">
                    {{ result.message }}
                  </div>

                  <!-- Differences Table -->
                  <div v-if="result.differences && result.differences.length > 0" class="differences-table">
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
                        <tr v-for="diff in result.differences" :key="diff.attribute" :class="diff.status">
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
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeVerificationModal" class="btn-secondary">Fermer</button>
          <button
            v-if="verificationResult?.success && selectedProfile"
            @click="handleVerifyProfile(selectedProfile)"
            class="btn-primary"
            :disabled="isVerifying"
          >
            Actualiser
          </button>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family:Rajdhani:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

/* Contenu spécifique à la page profils - Thème Futuriste Sombre */
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
  font-family: 'Orbitron', sans-serif;
  font-size: 1.875rem;
  font-weight: 700;
  color: #ffffff;
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
  background: linear-gradient(135deg, #e53212 0%, #F29400 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(242, 148, 0, 0.3);
  white-space: nowrap;
}

.btn-primary svg {
  width: 20px;
  height: 20px;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(242, 148, 0, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
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
  transition: all 0.3s ease;
}

.stat-box:hover {
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
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

.stat-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.search-input:focus {
  outline: none;
  border-color: #008ecf;
  background: rgba(0, 142, 207, 0.1);
  box-shadow: 0 0 20px rgba(0, 142, 207, 0.2);
}

.filter-group {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.filter-select {
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 180px;
}

.filter-select option {
  background: #0f0f19;
  color: rgba(255, 255, 255, 0.9);
}

.filter-select:focus {
  outline: none;
  border-color: #008ecf;
  box-shadow: 0 0 20px rgba(0, 142, 207, 0.2);
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
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.75rem;
  font-weight: 700;
  color: #008ecf;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.data-table td {
  padding: 1rem 1.5rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.85);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: rgba(0, 142, 207, 0.08);
}

.id-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.6);
}

.name-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.name-text {
  font-weight: 600;
  color: #ffffff;
}

.description-text {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.bandwidth-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.bandwidth-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.bandwidth-badge.upload {
  background: rgba(0, 142, 207, 0.15);
  color: #008ecf;
  border: 1px solid rgba(0, 142, 207, 0.3);
}

.bandwidth-badge.download {
  background: rgba(16, 185, 129, 0.15);
  color: #10B981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.quota-cell {
  display: flex;
  flex-direction: column;
}

.quota-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.quota-badge.limited {
  background: rgba(242, 148, 0, 0.15);
  color: #F29400;
  border: 1px solid rgba(242, 148, 0, 0.3);
}

.quota-badge.unlimited {
  background: rgba(16, 185, 129, 0.15);
  color: #10B981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.duration-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  background: rgba(0, 142, 207, 0.15);
  color: #008ecf;
  border: 1px solid rgba(0, 142, 207, 0.3);
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.usage-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.usage-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-success {
  background: rgba(16, 185, 129, 0.15);
  color: #10B981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-gray {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
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
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.action-btn svg {
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.5);
}

.action-btn.info:hover {
  background: rgba(0, 142, 207, 0.15);
  border-color: #008ecf;
  box-shadow: 0 0 15px rgba(0, 142, 207, 0.3);
}

.action-btn.info:hover svg {
  color: #008ecf;
}

.action-btn.edit:hover {
  background: rgba(0, 142, 207, 0.15);
  border-color: #008ecf;
  box-shadow: 0 0 15px rgba(0, 142, 207, 0.3);
}

.action-btn.edit:hover svg {
  color: #008ecf;
}

.action-btn.delete:hover {
  background: rgba(229, 50, 18, 0.15);
  border-color: #e53212;
  box-shadow: 0 0 15px rgba(229, 50, 18, 0.3);
}

.action-btn.delete:hover svg {
  color: #e53212;
}

.action-btn.radius:hover:not(:disabled) {
  background: rgba(242, 148, 0, 0.15);
  border-color: #F29400;
  box-shadow: 0 0 15px rgba(242, 148, 0, 0.3);
}

.action-btn.radius:hover:not(:disabled) svg {
  color: #F29400;
}

.action-btn.radius.syncing {
  background: rgba(242, 148, 0, 0.15);
  border-color: #F29400;
}

.action-btn.radius.syncing svg {
  color: #F29400;
}

.action-btn .spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: rgba(255, 255, 255, 0.2);
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.125rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0.5rem;
}

.empty-state p {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.4);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: rgba(15, 15, 25, 0.95);
  border: 1px solid rgba(0, 142, 207, 0.2);
  border-radius: 20px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow:
    0 25px 60px rgba(0, 0, 0, 0.5),
    0 0 40px rgba(0, 142, 207, 0.1);
}

.modal-content.modal-large {
  max-width: 800px;
}

.modal-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: #ffffff;
}

.modal-close {
  width: 36px;
  height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.modal-close svg {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.5);
}

.modal-close:hover {
  background: rgba(229, 50, 18, 0.2);
  border-color: #e53212;
  transform: rotate(90deg);
}

.modal-close:hover svg {
  color: #e53212;
}

.modal-body {
  padding: 2rem;
}

.form-section {
  margin-bottom: 2rem;
}

.section-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  font-weight: 700;
  color: #008ecf;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(0, 142, 207, 0.3);
}

.section-description {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 1rem;
  line-height: 1.5;
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
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
}

.form-group textarea {
  resize: vertical;
}

.form-group select option {
  background: #0f0f19;
  color: rgba(255, 255, 255, 0.9);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #008ecf;
  background: rgba(0, 142, 207, 0.1);
  box-shadow: 0 0 20px rgba(0, 142, 207, 0.2);
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.help-text {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  font-style: italic;
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
  font-family: 'Inter', sans-serif;
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
  border-radius: 10px;
  margin-top: 1rem;
}

.info-note svg {
  width: 20px;
  height: 20px;
  color: #008ecf;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-note p {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.8);
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.loading-container {
  padding: 4rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-assignments {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.875rem;
}

.form-help {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

/* Détails */
.details-section {
  margin-bottom: 2rem;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.detail-item {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.detail-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-value {
  display: block;
  margin-top: 0.25rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  color: #ffffff;
}

.list-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 0.75rem;
}

.list-item {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  transition: all 0.3s ease;
}

.list-item:hover {
  border-color: #008ecf;
  background: rgba(0, 142, 207, 0.08);
}

.list-item-name {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  color: #ffffff;
}

.list-item-meta {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 0.25rem;
}

.empty-message {
  padding: 2rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.875rem;
  font-style: italic;
}

/* Verification Button */
.action-btn.verify:hover:not(:disabled) {
  background: rgba(0, 142, 207, 0.15);
  border-color: #008ecf;
  box-shadow: 0 0 15px rgba(0, 142, 207, 0.3);
}

.action-btn.verify:hover:not(:disabled) svg {
  color: #008ecf;
}

/* Verification Modal */
.loading-text {
  margin-top: 1rem;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.875rem;
}

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
  font-family: 'Orbitron', sans-serif;
  font-size: 1.125rem;
  font-weight: 600;
  color: #e53212;
  margin-bottom: 0.5rem;
}

.error-container p {
  color: rgba(255, 255, 255, 0.5);
}

.verification-summary {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.summary-card {
  flex: 1;
  min-width: 120px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  border: 2px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.summary-card.success {
  background: rgba(16, 185, 129, 0.1);
  border-color: #10B981;
}

.summary-card.warning {
  background: rgba(242, 148, 0, 0.1);
  border-color: #F29400;
}

.summary-card.danger {
  background: rgba(229, 50, 18, 0.1);
  border-color: #e53212;
}

.summary-card.gray {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.2);
}

.summary-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 0.25rem;
}

.summary-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 600;
  text-transform: uppercase;
}

.verification-info {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.verification-info p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
}

.verification-results {
  margin-top: 1.5rem;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1rem;
  border-left: 4px solid rgba(255, 255, 255, 0.3);
}

.result-card.ok {
  border-left-color: #10B981;
  background: rgba(16, 185, 129, 0.08);
}

.result-card.warning {
  border-left-color: #F29400;
  background: rgba(242, 148, 0, 0.08);
}

.result-card.error {
  border-left-color: #e53212;
  background: rgba(229, 50, 18, 0.08);
}

.result-card.not_connected {
  border-left-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.03);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.result-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.result-user strong {
  font-size: 0.9375rem;
  color: #ffffff;
}

.result-profile {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.result-message {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
}

.badge-warning {
  background: rgba(242, 148, 0, 0.15);
  color: #F29400;
  border: 1px solid rgba(242, 148, 0, 0.3);
}

.badge-danger {
  background: rgba(229, 50, 18, 0.15);
  color: #e53212;
  border: 1px solid rgba(229, 50, 18, 0.3);
}

.differences-table {
  margin-top: 0.75rem;
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.differences-table th {
  background: rgba(0, 142, 207, 0.1);
  font-weight: 600;
  color: #008ecf;
  text-transform: uppercase;
  font-size: 0.6875rem;
}

.differences-table td {
  color: rgba(255, 255, 255, 0.8);
}

.differences-table tr.match {
  background: rgba(16, 185, 129, 0.05);
}

.differences-table tr.mismatch {
  background: rgba(229, 50, 18, 0.05);
}

.differences-table tr.missing {
  background: rgba(242, 148, 0, 0.05);
}

.differences-table code {
  background: rgba(255, 255, 255, 0.1);
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

/* Scrollbar dark */
.modal-content::-webkit-scrollbar,
.table-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.modal-content::-webkit-scrollbar-track,
.table-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
}

.modal-content::-webkit-scrollbar-thumb,
.table-container::-webkit-scrollbar-thumb {
  background: rgba(0, 142, 207, 0.3);
  border-radius: 3px;
}

.modal-content::-webkit-scrollbar-thumb:hover,
.table-container::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 142, 207, 0.5);
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
    min-width: 1000px;
  }

  .form-row,
  .details-grid,
  .list-grid {
    grid-template-columns: 1fr;
  }

  .modal-content.modal-large {
    max-width: 100%;
  }
}
</style>
