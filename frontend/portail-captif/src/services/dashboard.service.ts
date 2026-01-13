/**
 * Service Dashboard - Communication avec l'API backend
 *
 * Ce service gère toutes les requêtes API pour le dashboard administrateur.
 * Il communique avec les endpoints /api/core/dashboard/
 */

import api from './api'

// ============================================================================
// TYPES
// ============================================================================

export interface BandwidthData {
  input: number
  output: number
  total: number
  total_gb: number
}

export interface GlobalStatistics {
  total_users: number
  active_users: number  // Utilisateurs activés RADIUS
  online_users: number  // Utilisateurs actuellement connectés
  total_sessions: number
  connected_devices: number
  bandwidth_today: BandwidthData
  bandwidth_total: BandwidthData
  profiles_count: number
  profiles_with_quota: number
  profiles_unlimited: number
  timestamp: string
}

export interface BandwidthInterval {
  start: string
  end: string
  label: string
  input_bytes: number
  output_bytes: number
  total_bytes: number
  total_mb: number
  sessions: number
}

export interface Bandwidth24hResponse {
  intervals: BandwidthInterval[]
  total: {
    input_bytes: number
    output_bytes: number
    total_bytes: number
    total_mb: number
    total_gb: number
  }
  filter_applied: 'all' | 'profile' | 'promotion'
  filter_name: string | null
  interval_hours: number
  period_start: string
  period_end: string
}

export interface DayActivity {
  date: string
  day_name: string
  day_full: string
  unique_users: number
  total_sessions: number
  total_mb: number
}

export interface UserActivity7DaysResponse {
  days: DayActivity[]
  total_unique_users: number
  average_daily: number
  period_start: string
  period_end: string
}

export interface TopConsumer {
  id: number | null
  username: string
  full_name: string
  matricule: string | null
  email: string | null
  profile_name: string
  promotion_name: string | null
  is_radius_activated: boolean | null
  total_bytes: number
  total_mb: number
  total_gb: number
  download_bytes: number
  upload_bytes: number
  total_sessions: number
  total_session_hours: number
  last_seen: string | null
}

export interface TopConsumersResponse {
  users: TopConsumer[]
  total_bandwidth: {
    bytes: number
    mb: number
    gb: number
  }
  period_days: number
  period_start: string
  period_end: string
}

export interface TopProfile {
  id: number
  name: string
  user_count: number
  active_users: number
  total_bytes: number
  total_mb: number
  total_gb: number
  bandwidth_limit: string
  quota_type: string
  session_timeout_hours?: number
}

export interface TopProfilesResponse {
  profiles: TopProfile[]
  total_profiles: number
}

export interface UserSession {
  session_id: string
  start_time: string | null
  stop_time: string | null
  duration_seconds: number
  duration_formatted: string
  is_active: boolean
  download_bytes: number
  upload_bytes: number
  total_bytes: number
  total_mb: number
  ip_address: string | null
  mac_address: string | null
  nas_ip: string | null
  terminate_cause: string | null
}

export interface UserHistoryStats {
  total_sessions: number
  total_bytes: number
  total_mb: number
  total_gb: number
  download_gb: number
  upload_gb: number
  total_hours: number
  first_connection: string | null
  last_connection: string | null
}

export interface UserHistoryResponse {
  user: {
    id: number
    username: string
    matricule: string | null
    full_name: string
    email: string | null
    profile: { id: number; name: string } | null
    promotion: { id: number; name: string } | null
    is_radius_activated: boolean
    is_radius_enabled: boolean
    created_at: string | null
  }
  sessions: UserSession[]
  stats: UserHistoryStats
  current_session: {
    session_id: string
    start_time: string | null
    duration_seconds: number
    duration_formatted: string
    download_bytes: number
    upload_bytes: number
    total_mb: number
    ip_address: string | null
    mac_address: string | null
  } | null
  error?: string
}

export interface SearchUserResult {
  id: number
  username: string
  matricule: string | null
  full_name: string
  email: string | null
  promotion: string | null
  profile: string | null
  is_radius_activated: boolean
}

export interface ActiveSession {
  session_id: string
  username: string
  user: {
    id: number | null
    full_name: string
    matricule: string | null
    promotion: string | null
  }
  start_time: string | null
  duration_seconds: number
  duration_formatted: string
  download_mb: number
  upload_mb: number
  total_mb: number
  ip_address: string | null
  mac_address: string | null
  nas_ip: string | null
}

export interface ActiveSessionsResponse {
  sessions: ActiveSession[]
  stats: {
    total_sessions: number
    unique_users: number
    unique_devices: number
    total_bandwidth_mb: number
    total_bandwidth_gb: number
  }
  timestamp: string
}

// ============================================================================
// SERVICE
// ============================================================================

const DASHBOARD_BASE_URL = '/api/core/dashboard'

export const dashboardService = {
  /**
   * Récupère les statistiques globales pour les cartes du dashboard
   */
  async getGlobalStatistics(): Promise<GlobalStatistics> {
    const response = await api.get<GlobalStatistics>(`${DASHBOARD_BASE_URL}/stats/`)
    return response.data
  },

  /**
   * Récupère la consommation de bande passante sur 24h
   * @param interval Intervalle en heures (défaut: 4)
   * @param profileId Filtrer par profil (optionnel)
   * @param promotionId Filtrer par promotion (optionnel)
   */
  async getBandwidth24h(
    interval: number = 4,
    profileId?: number,
    promotionId?: number
  ): Promise<Bandwidth24hResponse> {
    const params: Record<string, string | number> = { interval }
    if (profileId) params.profile_id = profileId
    if (promotionId) params.promotion_id = promotionId

    const response = await api.get<Bandwidth24hResponse>(
      `${DASHBOARD_BASE_URL}/bandwidth-24h/`,
      { params }
    )
    return response.data
  },

  /**
   * Récupère l'activité utilisateurs sur 7 jours
   */
  async getUserActivity7Days(): Promise<UserActivity7DaysResponse> {
    const response = await api.get<UserActivity7DaysResponse>(
      `${DASHBOARD_BASE_URL}/user-activity/`
    )
    return response.data
  },

  /**
   * Récupère les top consommateurs de bande passante
   * @param limit Nombre d'utilisateurs (défaut: 10)
   * @param period Période en jours (défaut: 30)
   */
  async getTopConsumers(limit: number = 10, period: number = 30): Promise<TopConsumersResponse> {
    const response = await api.get<TopConsumersResponse>(
      `${DASHBOARD_BASE_URL}/top-consumers/`,
      { params: { limit, period } }
    )
    return response.data
  },

  /**
   * Récupère les top profils consommateurs
   * @param limit Nombre de profils (défaut: 10)
   */
  async getTopProfiles(limit: number = 10): Promise<TopProfilesResponse> {
    const response = await api.get<TopProfilesResponse>(
      `${DASHBOARD_BASE_URL}/top-profiles/`,
      { params: { limit } }
    )
    return response.data
  },

  /**
   * Récupère l'historique complet d'un utilisateur
   * @param identifier Identifiant (matricule, username ou user_id)
   * @param type Type d'identifiant ('matricule' | 'username' | 'user_id')
   * @param limit Nombre de sessions (défaut: 50)
   */
  async getUserHistory(
    identifier: string | number,
    type: 'matricule' | 'username' | 'user_id' = 'matricule',
    limit: number = 50
  ): Promise<UserHistoryResponse> {
    const params: Record<string, string | number> = { limit }
    params[type] = identifier

    const response = await api.get<UserHistoryResponse>(
      `${DASHBOARD_BASE_URL}/user-history/`,
      { params }
    )
    return response.data
  },

  /**
   * Recherche des utilisateurs
   * @param query Terme de recherche (min 2 caractères)
   * @param limit Nombre de résultats (défaut: 20)
   */
  async searchUsers(query: string, limit: number = 20): Promise<SearchUserResult[]> {
    const response = await api.get<{ users: SearchUserResult[]; count: number }>(
      `${DASHBOARD_BASE_URL}/search-users/`,
      { params: { q: query, limit } }
    )
    return response.data.users
  },

  /**
   * Récupère les sessions actives en temps réel
   * @param limit Nombre de sessions (défaut: 100)
   */
  async getActiveSessions(limit: number = 100): Promise<ActiveSessionsResponse> {
    const response = await api.get<ActiveSessionsResponse>(
      `${DASHBOARD_BASE_URL}/active-sessions/`,
      { params: { limit } }
    )
    return response.data
  },

  /**
   * Efface le cache du dashboard
   */
  async clearCache(): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>(`${DASHBOARD_BASE_URL}/clear-cache/`)
    return response.data
  }
}

export default dashboardService
