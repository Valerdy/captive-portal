/**
 * Dashboard Store - Gestion de l'état du dashboard administrateur
 *
 * Ce store centralise toutes les données du dashboard et gère:
 * - Les statistiques globales (cartes)
 * - La bande passante 24h
 * - L'activité utilisateurs 7 jours
 * - Les top consommateurs
 * - Les top profils
 * - L'historique utilisateur
 * - Les sessions actives
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import dashboardService from '@/services/dashboard.service'
import type {
  GlobalStatistics,
  Bandwidth24hResponse,
  UserActivity7DaysResponse,
  TopConsumersResponse,
  TopProfilesResponse,
  UserHistoryResponse,
  ActiveSessionsResponse,
  SearchUserResult
} from '@/services/dashboard.service'

function getErrorMessage(error: any): string {
  if (error?.response?.data?.detail) {
    return error.response.data.detail
  }
  if (error?.response?.data?.message) {
    return error.response.data.message
  }
  if (error?.response?.data?.error) {
    return error.response.data.error
  }
  if (error?.message) {
    return error.message
  }
  return 'Une erreur est survenue'
}

export const useDashboardStore = defineStore('dashboard', () => {
  // =========================================================================
  // STATE
  // =========================================================================

  // Statistiques globales
  const globalStats = ref<GlobalStatistics | null>(null)

  // Bande passante 24h
  const bandwidth24h = ref<Bandwidth24hResponse | null>(null)
  const bandwidthFilter = ref<{
    type: 'all' | 'profile' | 'promotion'
    id?: number
  }>({ type: 'all' })

  // Activité utilisateurs 7 jours
  const userActivity = ref<UserActivity7DaysResponse | null>(null)

  // Top consommateurs
  const topConsumers = ref<TopConsumersResponse | null>(null)
  const topConsumersPeriod = ref(30) // jours

  // Top profils
  const topProfiles = ref<TopProfilesResponse | null>(null)

  // Historique utilisateur sélectionné
  const selectedUserHistory = ref<UserHistoryResponse | null>(null)

  // Sessions actives
  const activeSessions = ref<ActiveSessionsResponse | null>(null)

  // Résultats de recherche utilisateur
  const searchResults = ref<SearchUserResult[]>([])

  // États de chargement
  const isLoadingStats = ref(false)
  const isLoadingBandwidth = ref(false)
  const isLoadingActivity = ref(false)
  const isLoadingTopConsumers = ref(false)
  const isLoadingTopProfiles = ref(false)
  const isLoadingUserHistory = ref(false)
  const isLoadingActiveSessions = ref(false)
  const isSearching = ref(false)

  // Erreurs
  const error = ref<string | null>(null)

  // Auto-refresh
  const refreshInterval = ref<number | null>(null)

  // =========================================================================
  // COMPUTED
  // =========================================================================

  const isLoading = computed(() => {
    return isLoadingStats.value ||
      isLoadingBandwidth.value ||
      isLoadingActivity.value ||
      isLoadingTopConsumers.value ||
      isLoadingTopProfiles.value
  })

  // Données formatées pour les graphiques
  const bandwidthChartData = computed(() => {
    if (!bandwidth24h.value) return { labels: [], data: [] }

    return {
      labels: bandwidth24h.value.intervals.map(i => i.label),
      data: bandwidth24h.value.intervals.map(i => i.total_mb)
    }
  })

  const userActivityChartData = computed(() => {
    if (!userActivity.value) return { labels: [], data: [] }

    return {
      labels: userActivity.value.days.map(d => d.day_name),
      data: userActivity.value.days.map(d => d.unique_users)
    }
  })

  // =========================================================================
  // ACTIONS
  // =========================================================================

  /**
   * Charge les statistiques globales
   */
  async function fetchGlobalStats() {
    isLoadingStats.value = true
    error.value = null
    try {
      globalStats.value = await dashboardService.getGlobalStatistics()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoadingStats.value = false
    }
  }

  /**
   * Charge les données de bande passante 24h
   */
  async function fetchBandwidth24h(
    interval: number = 4,
    profileId?: number,
    promotionId?: number
  ) {
    isLoadingBandwidth.value = true
    error.value = null
    try {
      bandwidth24h.value = await dashboardService.getBandwidth24h(
        interval,
        profileId,
        promotionId
      )

      // Mettre à jour le filtre actif
      if (profileId) {
        bandwidthFilter.value = { type: 'profile', id: profileId }
      } else if (promotionId) {
        bandwidthFilter.value = { type: 'promotion', id: promotionId }
      } else {
        bandwidthFilter.value = { type: 'all' }
      }
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoadingBandwidth.value = false
    }
  }

  /**
   * Charge l'activité utilisateurs 7 jours
   */
  async function fetchUserActivity() {
    isLoadingActivity.value = true
    error.value = null
    try {
      userActivity.value = await dashboardService.getUserActivity7Days()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoadingActivity.value = false
    }
  }

  /**
   * Charge les top consommateurs
   */
  async function fetchTopConsumers(limit: number = 10, period: number = 30) {
    isLoadingTopConsumers.value = true
    error.value = null
    try {
      topConsumersPeriod.value = period
      topConsumers.value = await dashboardService.getTopConsumers(limit, period)
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoadingTopConsumers.value = false
    }
  }

  /**
   * Charge les top profils
   */
  async function fetchTopProfiles(limit: number = 10) {
    isLoadingTopProfiles.value = true
    error.value = null
    try {
      topProfiles.value = await dashboardService.getTopProfiles(limit)
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoadingTopProfiles.value = false
    }
  }

  /**
   * Charge l'historique d'un utilisateur
   */
  async function fetchUserHistory(
    identifier: string | number,
    type: 'matricule' | 'username' | 'user_id' = 'matricule',
    limit: number = 50
  ) {
    isLoadingUserHistory.value = true
    error.value = null
    try {
      selectedUserHistory.value = await dashboardService.getUserHistory(
        identifier,
        type,
        limit
      )
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoadingUserHistory.value = false
    }
  }

  /**
   * Charge les sessions actives
   */
  async function fetchActiveSessions(limit: number = 100) {
    isLoadingActiveSessions.value = true
    error.value = null
    try {
      activeSessions.value = await dashboardService.getActiveSessions(limit)
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoadingActiveSessions.value = false
    }
  }

  /**
   * Recherche des utilisateurs
   */
  async function searchUsers(query: string, limit: number = 20) {
    if (query.length < 2) {
      searchResults.value = []
      return
    }

    isSearching.value = true
    error.value = null
    try {
      searchResults.value = await dashboardService.searchUsers(query, limit)
    } catch (err) {
      error.value = getErrorMessage(err)
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }

  /**
   * Efface l'historique utilisateur sélectionné
   */
  function clearSelectedUserHistory() {
    selectedUserHistory.value = null
  }

  /**
   * Efface les résultats de recherche
   */
  function clearSearchResults() {
    searchResults.value = []
  }

  /**
   * Charge toutes les données du dashboard
   */
  async function fetchAllDashboardData() {
    error.value = null

    // Charger en parallèle pour de meilleures performances
    await Promise.all([
      fetchGlobalStats(),
      fetchBandwidth24h(),
      fetchUserActivity(),
      fetchTopConsumers(),
      fetchTopProfiles()
    ])
  }

  /**
   * Démarre le rafraîchissement automatique
   * @param intervalMs Intervalle en millisecondes (défaut: 30 secondes)
   */
  function startAutoRefresh(intervalMs: number = 30000) {
    stopAutoRefresh()

    refreshInterval.value = window.setInterval(async () => {
      try {
        // Rafraîchir uniquement les stats et sessions actives
        await Promise.all([
          fetchGlobalStats(),
          fetchActiveSessions()
        ])
      } catch (err) {
        console.error('Erreur lors du rafraîchissement automatique:', err)
      }
    }, intervalMs)
  }

  /**
   * Arrête le rafraîchissement automatique
   */
  function stopAutoRefresh() {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
      refreshInterval.value = null
    }
  }

  /**
   * Efface le cache du dashboard (côté backend)
   */
  async function clearCache() {
    try {
      await dashboardService.clearCache()
      // Recharger les données
      await fetchAllDashboardData()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    }
  }

  /**
   * Reset le store
   */
  function $reset() {
    stopAutoRefresh()
    globalStats.value = null
    bandwidth24h.value = null
    userActivity.value = null
    topConsumers.value = null
    topProfiles.value = null
    selectedUserHistory.value = null
    activeSessions.value = null
    searchResults.value = []
    error.value = null
  }

  return {
    // State
    globalStats,
    bandwidth24h,
    bandwidthFilter,
    userActivity,
    topConsumers,
    topConsumersPeriod,
    topProfiles,
    selectedUserHistory,
    activeSessions,
    searchResults,

    // Loading states
    isLoading,
    isLoadingStats,
    isLoadingBandwidth,
    isLoadingActivity,
    isLoadingTopConsumers,
    isLoadingTopProfiles,
    isLoadingUserHistory,
    isLoadingActiveSessions,
    isSearching,

    // Error
    error,

    // Computed
    bandwidthChartData,
    userActivityChartData,

    // Actions
    fetchGlobalStats,
    fetchBandwidth24h,
    fetchUserActivity,
    fetchTopConsumers,
    fetchTopProfiles,
    fetchUserHistory,
    fetchActiveSessions,
    searchUsers,
    clearSelectedUserHistory,
    clearSearchResults,
    fetchAllDashboardData,
    startAutoRefresh,
    stopAutoRefresh,
    clearCache,
    $reset
  }
})
