<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { useProfileStore } from '@/stores/profile'
import { usePromotionStore } from '@/stores/promotion'
import { useNotificationStore } from '@/stores/notification'
import AdminLayout from '@/layouts/AdminLayout.vue'
import VueApexCharts from 'vue3-apexcharts'

const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()
const profileStore = useProfileStore()
const promotionStore = usePromotionStore()
const notificationStore = useNotificationStore()

const isLoading = ref(true)

// Filtres pour le graphique bande passante
const bandwidthFilterType = ref<'all' | 'profile' | 'promotion'>('all')
const selectedProfileId = ref<number | null>(null)
const selectedPromotionId = ref<number | null>(null)

// Recherche utilisateur
const userSearchQuery = ref('')
const showUserHistory = ref(false)

// Statistiques globales depuis le store
const stats = computed(() => dashboardStore.globalStats)

// Graphique de bande passante (24h)
const bandwidthChartOptions = computed(() => ({
  chart: {
    type: 'area',
    height: 350,
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif',
    background: 'transparent'
  },
  colors: ['#F97316'],
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 3 },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.7,
      opacityTo: 0.2,
      stops: [0, 90, 100]
    }
  },
  xaxis: {
    categories: dashboardStore.bandwidthChartData.labels,
    labels: { style: { colors: '#6B7280', fontSize: '12px' } }
  },
  yaxis: {
    labels: {
      style: { colors: '#6B7280', fontSize: '12px' },
      formatter: (val: number) => `${val.toFixed(1)} MB`
    }
  },
  grid: { borderColor: 'rgba(255,255,255,0.1)' },
  tooltip: {
    theme: 'dark',
    y: { formatter: (val: number) => `${val.toFixed(2)} MB` }
  }
}))

const bandwidthChartSeries = computed(() => [
  { name: 'Bande passante', data: dashboardStore.bandwidthChartData.data }
])

// Graphique d'activité utilisateur (7 jours)
const userActivityChartOptions = computed(() => ({
  chart: {
    type: 'bar',
    height: 350,
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif',
    background: 'transparent'
  },
  colors: ['#DC2626'],
  plotOptions: {
    bar: {
      borderRadius: 8,
      columnWidth: '60%'
    }
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: dashboardStore.userActivityChartData.labels,
    labels: { style: { colors: '#6B7280', fontSize: '12px' } }
  },
  yaxis: {
    labels: {
      style: { colors: '#6B7280', fontSize: '12px' },
      formatter: (val: number) => `${Math.round(val)}`
    }
  },
  grid: { borderColor: 'rgba(255,255,255,0.1)' },
  tooltip: {
    theme: 'dark',
    y: { formatter: (val: number) => `${val} utilisateurs` }
  }
}))

const userActivityChartSeries = computed(() => [
  { name: 'Utilisateurs actifs', data: dashboardStore.userActivityChartData.data }
])

// Watcher pour les changements de filtre bande passante
watch([bandwidthFilterType, selectedProfileId, selectedPromotionId], async () => {
  try {
    if (bandwidthFilterType.value === 'profile' && selectedProfileId.value) {
      await dashboardStore.fetchBandwidth24h(4, selectedProfileId.value, undefined)
    } else if (bandwidthFilterType.value === 'promotion' && selectedPromotionId.value) {
      await dashboardStore.fetchBandwidth24h(4, undefined, selectedPromotionId.value)
    } else {
      await dashboardStore.fetchBandwidth24h(4)
    }
  } catch (error) {
    console.error('Erreur lors du chargement des données de bande passante:', error)
  }
})

// Recherche utilisateur avec debounce
let searchTimeout: number | null = null
watch(userSearchQuery, (query) => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = window.setTimeout(() => {
    if (query.length >= 2) {
      dashboardStore.searchUsers(query)
    } else {
      dashboardStore.clearSearchResults()
    }
  }, 300)
})

// Sélectionner un utilisateur pour voir son historique
async function selectUser(userId: number) {
  try {
    await dashboardStore.fetchUserHistory(userId, 'user_id')
    showUserHistory.value = true
    dashboardStore.clearSearchResults()
    userSearchQuery.value = ''
  } catch (error: any) {
    notificationStore.error('Erreur lors du chargement de l\'historique utilisateur')
  }
}

// Fermer le modal historique
function closeUserHistory() {
  showUserHistory.value = false
  dashboardStore.clearSelectedUserHistory()
}

// Formater les bytes en unités lisibles
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Formater la date
function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    // Charger les profils et promotions pour les filtres
    await Promise.all([
      profileStore.fetchActiveProfiles(),
      promotionStore.fetchPromotions()
    ])

    // Charger toutes les données du dashboard
    await dashboardStore.fetchAllDashboardData()

    // Démarrer le rafraîchissement automatique (30 secondes)
    dashboardStore.startAutoRefresh(30000)
  } catch (error: any) {
    const message = error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors du chargement des données du dashboard: ${message}`)
    console.error('Erreur chargement dashboard:', error)
  } finally {
    isLoading.value = false
  }
})

onUnmounted(() => {
  dashboardStore.stopAutoRefresh()
  if (searchTimeout) clearTimeout(searchTimeout)
})
</script>

<template>
  <AdminLayout activePage="dashboard">
    <div class="content-wrapper">
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Chargement des statistiques...</p>
      </div>

      <template v-else>
        <!-- Cartes de statistiques -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon users">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ stats?.total_users || 0 }}</h3>
              <p>Utilisateurs totaux</p>
              <span class="stat-badge success">{{ stats?.active_users || 0 }} actifs</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon sessions">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ stats?.total_sessions || 0 }}</h3>
              <p>Sessions totales</p>
              <span class="stat-badge info">{{ stats?.total_sessions || 0 }} en cours</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon devices">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="5" y="2" width="14" height="20" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="18" x2="12.01" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ stats?.connected_devices || 0 }}</h3>
              <p>Appareils enregistrés</p>
              <span class="stat-badge warning">{{ stats?.connected_devices || 0 }} connectés</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon bandwidth">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ stats?.bandwidth_today?.total_gb || 0 }} GB</h3>
              <p>Bande passante (aujourd'hui)</p>
              <span class="stat-badge danger">Total: {{ stats?.bandwidth_total?.total_gb || 0 }} GB</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon profiles">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ stats?.profiles_count || 0 }}</h3>
              <p>Profils créés</p>
              <span class="stat-badge success">{{ stats?.profiles_count || 0 }} actifs</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon quota">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ stats?.profiles_with_quota || 0 }}</h3>
              <p>Profils avec quota limité</p>
              <span class="stat-badge warning">{{ stats?.profiles_unlimited || 0 }} illimités</span>
            </div>
          </div>
        </div>

        <!-- Graphiques -->
        <div class="charts-section">
          <div class="chart-card">
            <div class="chart-header">
              <div class="chart-title-row">
                <div>
                  <h2>Bande passante sur 24h</h2>
                  <p class="chart-subtitle">Consommation par période de 4 heures</p>
                </div>
                <div class="chart-filters">
                  <select v-model="bandwidthFilterType" class="filter-select">
                    <option value="all">Tous</option>
                    <option value="profile">Par profil</option>
                    <option value="promotion">Par promotion</option>
                  </select>
                  <select
                    v-if="bandwidthFilterType === 'profile'"
                    v-model="selectedProfileId"
                    class="filter-select"
                  >
                    <option :value="null">Sélectionner un profil</option>
                    <option
                      v-for="profile in profileStore.profiles"
                      :key="profile.id"
                      :value="profile.id"
                    >
                      {{ profile.name }}
                    </option>
                  </select>
                  <select
                    v-if="bandwidthFilterType === 'promotion'"
                    v-model="selectedPromotionId"
                    class="filter-select"
                  >
                    <option :value="null">Sélectionner une promotion</option>
                    <option
                      v-for="promotion in promotionStore.promotions"
                      :key="promotion.id"
                      :value="promotion.id"
                    >
                      {{ promotion.name }}
                    </option>
                  </select>
                </div>
              </div>
              <div v-if="dashboardStore.bandwidth24h?.filter_name" class="active-filter">
                Filtre: {{ dashboardStore.bandwidth24h.filter_name }}
              </div>
            </div>
            <div class="chart-body">
              <VueApexCharts
                v-if="dashboardStore.bandwidthChartData.data.length > 0"
                type="area"
                height="350"
                :options="bandwidthChartOptions"
                :series="bandwidthChartSeries"
              />
              <div v-else class="no-data">Aucune donnée disponible</div>
            </div>
          </div>

          <div class="chart-card">
            <div class="chart-header">
              <h2>Activité utilisateurs (7 jours)</h2>
              <p class="chart-subtitle">Nombre d'utilisateurs actifs par jour</p>
            </div>
            <div class="chart-body">
              <VueApexCharts
                v-if="dashboardStore.userActivityChartData.data.length > 0"
                type="bar"
                height="350"
                :options="userActivityChartOptions"
                :series="userActivityChartSeries"
              />
              <div v-else class="no-data">Aucune donnée disponible</div>
            </div>
          </div>
        </div>

        <!-- Top utilisateurs et profils -->
        <div class="top-sections">
          <!-- Top consommateurs -->
          <div class="top-card">
            <div class="top-header">
              <h2>Top utilisateurs consommateurs</h2>
              <p class="top-subtitle">30 derniers jours</p>
            </div>
            <div class="top-body">
              <div v-if="dashboardStore.topConsumers?.users?.length" class="top-list">
                <div
                  v-for="(user, index) in dashboardStore.topConsumers.users.slice(0, 5)"
                  :key="user.username"
                  class="top-item"
                  @click="user.id && selectUser(user.id)"
                >
                  <div class="top-rank">{{ index + 1 }}</div>
                  <div class="top-info">
                    <div class="top-name">{{ user.full_name }}</div>
                    <div class="top-details">
                      <span v-if="user.matricule">{{ user.matricule }}</span>
                      <span v-if="user.profile_name" class="profile-badge">{{ user.profile_name }}</span>
                    </div>
                  </div>
                  <div class="top-value">
                    <div class="value-main">{{ user.total_gb.toFixed(2) }} GB</div>
                    <div class="value-sub">{{ user.total_sessions }} sessions</div>
                  </div>
                </div>
              </div>
              <div v-else class="no-data">Aucune donnée disponible</div>
            </div>
          </div>

          <!-- Top profils -->
          <div class="top-card">
            <div class="top-header">
              <h2>Top profils consommateurs</h2>
              <p class="top-subtitle">Par bande passante totale</p>
            </div>
            <div class="top-body">
              <div v-if="dashboardStore.topProfiles?.profiles?.length" class="top-list">
                <div
                  v-for="(profile, index) in dashboardStore.topProfiles.profiles.slice(0, 5)"
                  :key="profile.id"
                  class="top-item"
                >
                  <div class="top-rank">{{ index + 1 }}</div>
                  <div class="top-info">
                    <div class="top-name">{{ profile.name }}</div>
                    <div class="top-details">
                      <span>{{ profile.user_count }} utilisateurs</span>
                      <span class="profile-badge">{{ profile.bandwidth_limit }}</span>
                    </div>
                  </div>
                  <div class="top-value">
                    <div class="value-main">{{ profile.total_gb.toFixed(2) }} GB</div>
                    <div class="value-sub">{{ profile.active_users }} actifs</div>
                  </div>
                </div>
              </div>
              <div v-else class="no-data">Aucune donnée disponible</div>
            </div>
          </div>
        </div>

        <!-- Recherche utilisateur -->
        <div class="user-search-section">
          <div class="search-card">
            <div class="search-header">
              <h2>Recherche utilisateur</h2>
              <p class="search-subtitle">Rechercher par matricule, nom ou email</p>
            </div>
            <div class="search-body">
              <div class="search-input-wrapper">
                <svg class="search-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <input
                  v-model="userSearchQuery"
                  type="text"
                  placeholder="Entrez un matricule, nom ou email..."
                  class="search-input"
                />
                <div v-if="dashboardStore.isSearching" class="search-spinner"></div>
              </div>

              <!-- Résultats de recherche -->
              <div v-if="dashboardStore.searchResults.length > 0" class="search-results">
                <div
                  v-for="user in dashboardStore.searchResults"
                  :key="user.id"
                  class="search-result-item"
                  @click="selectUser(user.id)"
                >
                  <div class="result-info">
                    <div class="result-name">{{ user.full_name }}</div>
                    <div class="result-details">
                      <span v-if="user.matricule">{{ user.matricule }}</span>
                      <span v-if="user.email">{{ user.email }}</span>
                    </div>
                  </div>
                  <div class="result-badges">
                    <span v-if="user.promotion" class="badge promotion">{{ user.promotion }}</span>
                    <span v-if="user.profile" class="badge profile">{{ user.profile }}</span>
                    <span :class="['badge', user.is_radius_activated ? 'active' : 'inactive']">
                      {{ user.is_radius_activated ? 'Actif' : 'Inactif' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Modal historique utilisateur -->
    <Teleport to="body">
      <div v-if="showUserHistory && dashboardStore.selectedUserHistory" class="modal-overlay" @click.self="closeUserHistory">
        <div class="modal-content user-history-modal">
          <div class="modal-header">
            <h2>Historique utilisateur</h2>
            <button class="close-btn" @click="closeUserHistory">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Informations utilisateur -->
            <div class="user-info-section">
              <div class="user-main-info">
                <h3>{{ dashboardStore.selectedUserHistory.user.full_name }}</h3>
                <div class="user-details">
                  <span v-if="dashboardStore.selectedUserHistory.user.matricule">
                    Matricule: {{ dashboardStore.selectedUserHistory.user.matricule }}
                  </span>
                  <span v-if="dashboardStore.selectedUserHistory.user.email">
                    {{ dashboardStore.selectedUserHistory.user.email }}
                  </span>
                </div>
                <div class="user-badges">
                  <span v-if="dashboardStore.selectedUserHistory.user.promotion" class="badge">
                    {{ dashboardStore.selectedUserHistory.user.promotion.name }}
                  </span>
                  <span v-if="dashboardStore.selectedUserHistory.user.profile" class="badge">
                    {{ dashboardStore.selectedUserHistory.user.profile.name }}
                  </span>
                </div>
              </div>

              <!-- Stats résumées -->
              <div class="user-stats-grid">
                <div class="user-stat">
                  <div class="stat-value">{{ dashboardStore.selectedUserHistory.stats.total_sessions }}</div>
                  <div class="stat-label">Sessions totales</div>
                </div>
                <div class="user-stat">
                  <div class="stat-value">{{ dashboardStore.selectedUserHistory.stats.total_gb.toFixed(2) }} GB</div>
                  <div class="stat-label">Données totales</div>
                </div>
                <div class="user-stat">
                  <div class="stat-value">{{ dashboardStore.selectedUserHistory.stats.total_hours.toFixed(1) }}h</div>
                  <div class="stat-label">Temps total</div>
                </div>
                <div class="user-stat">
                  <div class="stat-value">{{ dashboardStore.selectedUserHistory.stats.download_gb.toFixed(2) }} GB</div>
                  <div class="stat-label">Download</div>
                </div>
              </div>
            </div>

            <!-- Session active -->
            <div v-if="dashboardStore.selectedUserHistory.current_session" class="active-session-section">
              <h4>Session active</h4>
              <div class="active-session-info">
                <span class="active-indicator"></span>
                <span>En cours depuis {{ dashboardStore.selectedUserHistory.current_session.duration_formatted }}</span>
                <span>{{ dashboardStore.selectedUserHistory.current_session.total_mb.toFixed(2) }} MB</span>
                <span>IP: {{ dashboardStore.selectedUserHistory.current_session.ip_address || '-' }}</span>
              </div>
            </div>

            <!-- Historique des sessions -->
            <div class="sessions-history">
              <h4>Historique des sessions</h4>
              <div class="sessions-table">
                <table>
                  <thead>
                    <tr>
                      <th>Début</th>
                      <th>Fin</th>
                      <th>Durée</th>
                      <th>Données</th>
                      <th>IP</th>
                      <th>Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="session in dashboardStore.selectedUserHistory.sessions"
                      :key="session.session_id"
                      :class="{ active: session.is_active }"
                    >
                      <td>{{ formatDate(session.start_time) }}</td>
                      <td>{{ session.is_active ? '-' : formatDate(session.stop_time) }}</td>
                      <td>{{ session.duration_formatted }}</td>
                      <td>{{ session.total_mb.toFixed(2) }} MB</td>
                      <td>{{ session.ip_address || '-' }}</td>
                      <td>
                        <span :class="['status-badge', session.is_active ? 'active' : 'closed']">
                          {{ session.is_active ? 'Active' : (session.terminate_cause || 'Terminée') }}
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
    </Teleport>
  </AdminLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family:Inter:wght@300;400;500;600;700;800&display=swap');

/* Contenu spécifique au dashboard - Dark Theme */
.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 1rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(242, 148, 0, 0.2);
  border-top-color: #F29400;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Statistiques */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  transition: all 0.3s;
}

.stat-card:hover {
  border-color: rgba(0, 142, 207, 0.3);
  box-shadow: 0 8px 32px rgba(0, 142, 207, 0.15);
  transform: translateY(-2px);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
}

.stat-icon.users {
  background: rgba(0, 142, 207, 0.2);
  color: #008ecf;
}

.stat-icon.sessions {
  background: rgba(242, 148, 0, 0.2);
  color: #F29400;
}

.stat-icon.devices {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.stat-icon.bandwidth {
  background: rgba(229, 50, 18, 0.2);
  color: #e53212;
}

.stat-icon.profiles {
  background: rgba(162, 56, 130, 0.2);
  color: #a23882;
}

.stat-icon.quota {
  background: rgba(162, 56, 130, 0.2);
  color: #a23882;
}

.stat-content {
  flex: 1;
}

.stat-content h3 {
  font-family: 'Orbitron', monospace;
  font-size: 2rem;
  font-weight: 800;
  color: #F29400;
  line-height: 1;
  margin-bottom: 0.5rem;
  text-shadow: 0 0 15px rgba(242, 148, 0, 0.3);
}

.stat-content p {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
  margin-bottom: 0.75rem;
}

.stat-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.stat-badge.success {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.stat-badge.info {
  background: rgba(0, 142, 207, 0.2);
  color: #008ecf;
}

.stat-badge.warning {
  background: rgba(242, 148, 0, 0.2);
  color: #F29400;
}

.stat-badge.danger {
  background: rgba(229, 50, 18, 0.2);
  color: #e53212;
}

/* Graphiques */
.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
}

.chart-card {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
}

.chart-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.chart-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
}

.chart-header h2 {
  font-family: 'Orbitron', monospace;
  font-size: 1.125rem;
  font-weight: 700;
  color: #008ecf;
  margin-bottom: 0.25rem;
}

.chart-subtitle {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
}

.chart-filters {
  display: flex;
  gap: 0.5rem;
}

.filter-select {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.5rem 1rem;
  color: #fff;
  font-size: 0.875rem;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: #008ecf;
}

.active-filter {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #F29400;
}

.chart-body {
  margin: 0 -0.5rem;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 350px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 1rem;
}

/* Top sections */
.top-sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.top-card {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
}

.top-header {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.top-header h2 {
  font-family: 'Orbitron', monospace;
  font-size: 1rem;
  font-weight: 700;
  color: #008ecf;
  margin-bottom: 0.25rem;
}

.top-subtitle {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.top-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.top-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.top-rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(242, 148, 0, 0.2);
  color: #F29400;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.875rem;
}

.top-info {
  flex: 1;
  min-width: 0;
}

.top-name {
  font-weight: 600;
  color: #fff;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-details {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.profile-badge {
  background: rgba(0, 142, 207, 0.2);
  color: #008ecf;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

.top-value {
  text-align: right;
}

.value-main {
  font-family: 'Orbitron', monospace;
  font-weight: 700;
  color: #F29400;
}

.value-sub {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

/* User search section */
.user-search-section {
  margin-top: 1rem;
}

.search-card {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
}

.search-header {
  margin-bottom: 1rem;
}

.search-header h2 {
  font-family: 'Orbitron', monospace;
  font-size: 1rem;
  font-weight: 700;
  color: #008ecf;
  margin-bottom: 0.25rem;
}

.search-subtitle {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 1rem;
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.4);
}

.search-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1rem 1rem 1rem 3rem;
  color: #fff;
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: #008ecf;
}

.search-spinner {
  position: absolute;
  right: 1rem;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(242, 148, 0, 0.2);
  border-top-color: #F29400;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.search-results {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.search-result-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.result-name {
  font-weight: 600;
  color: #fff;
  margin-bottom: 0.25rem;
}

.result-details {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.result-badges {
  display: flex;
  gap: 0.5rem;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.badge.promotion {
  background: rgba(162, 56, 130, 0.2);
  color: #a23882;
}

.badge.profile {
  background: rgba(0, 142, 207, 0.2);
  color: #008ecf;
}

.badge.active {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.badge.inactive {
  background: rgba(229, 50, 18, 0.2);
  color: #e53212;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-content {
  background: rgba(15, 15, 25, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h2 {
  font-family: 'Orbitron', monospace;
  font-size: 1.25rem;
  font-weight: 700;
  color: #008ecf;
}

.close-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.6);
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
}

/* User history modal specific */
.user-info-section {
  margin-bottom: 1.5rem;
}

.user-main-info h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 0.5rem;
}

.user-details {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 0.75rem;
}

.user-badges {
  display: flex;
  gap: 0.5rem;
}

.user-badges .badge {
  background: rgba(0, 142, 207, 0.2);
  color: #008ecf;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
}

.user-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-top: 1.5rem;
}

.user-stat {
  background: rgba(255, 255, 255, 0.02);
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
}

.stat-value {
  font-family: 'Orbitron', monospace;
  font-size: 1.25rem;
  font-weight: 700;
  color: #F29400;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.active-session-section {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.active-session-section h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #10B981;
  margin-bottom: 0.5rem;
}

.active-session-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.8);
}

.active-indicator {
  width: 8px;
  height: 8px;
  background: #10B981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.sessions-history h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 1rem;
}

.sessions-table {
  overflow-x: auto;
}

.sessions-table table {
  width: 100%;
  border-collapse: collapse;
}

.sessions-table th,
.sessions-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.sessions-table th {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}

.sessions-table td {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.8);
}

.sessions-table tr.active {
  background: rgba(16, 185, 129, 0.05);
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.status-badge.active {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.status-badge.closed {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
}

/* Responsive */
@media (max-width: 1024px) {
  .charts-section {
    grid-template-columns: 1fr;
  }

  .top-sections {
    grid-template-columns: 1fr;
  }

  .user-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .chart-title-row {
    flex-direction: column;
  }

  .chart-filters {
    width: 100%;
  }

  .filter-select {
    flex: 1;
  }
}
</style>
