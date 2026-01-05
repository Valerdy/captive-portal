import api from './api'
import type { Profile } from '@/types'

export const profileService = {
  /**
   * Récupère la liste de tous les profils
   */
  async list(params: { is_active?: boolean } = {}): Promise<Profile[]> {
    const response = await api.get<any>('/api/core/profiles/', { params })
    // Django REST Framework retourne {count, results} pour les listes paginées
    return Array.isArray(response.data) ? response.data : (response.data.results || [])
  },

  /**
   * Récupère la liste des profils actifs uniquement
   */
  async active(): Promise<Profile[]> {
    const response = await api.get<any>('/api/core/profiles/active/')
    // Django REST Framework retourne {count, results} pour les listes paginées
    return Array.isArray(response.data) ? response.data : (response.data.results || [])
  },

  /**
   * Récupère un profil par son ID
   */
  async get(id: number): Promise<Profile> {
    const response = await api.get<Profile>(`/api/core/profiles/${id}/`)
    return response.data
  },

  /**
   * Crée un nouveau profil
   */
  async create(data: Partial<Profile>): Promise<Profile> {
    const response = await api.post<Profile>('/api/core/profiles/', data)
    return response.data
  },

  /**
   * Met à jour un profil existant
   */
  async update(id: number, data: Partial<Profile>): Promise<Profile> {
    const response = await api.patch<Profile>(`/api/core/profiles/${id}/`, data)
    return response.data
  },

  /**
   * Supprime un profil
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/api/core/profiles/${id}/`)
  },

  /**
   * Récupère la liste des utilisateurs utilisant ce profil
   */
  async getUsers(id: number): Promise<any> {
    const response = await api.get(`/api/core/profiles/${id}/users/`)
    return response.data
  },

  /**
   * Récupère la liste des promotions utilisant ce profil
   */
  async getPromotions(id: number): Promise<any> {
    const response = await api.get(`/api/core/profiles/${id}/promotions/`)
    return response.data
  },

  /**
   * Récupère les statistiques globales de tous les profils
   */
  async getStatistics(): Promise<any> {
    const response = await api.get('/api/core/profiles/statistics/')
    return response.data
  },

  /**
   * Récupère les statistiques détaillées d'un profil spécifique
   */
  async getStatisticsDetail(id: number): Promise<any> {
    const response = await api.get(`/api/core/profiles/${id}/statistics_detail/`)
    return response.data
  },

  /**
   * Assigne ce profil à un utilisateur individuel
   */
  async assignToUser(profileId: number, userId: number): Promise<any> {
    const response = await api.post(`/api/core/profiles/${profileId}/assign_to_user/`, {
      user_id: userId
    })
    return response.data
  },

  /**
   * Assigne ce profil à une promotion et synchronise tous ses utilisateurs
   */
  async assignToPromotion(profileId: number, promotionId: number): Promise<any> {
    const response = await api.post(`/api/core/profiles/${profileId}/assign_to_promotion/`, {
      promotion_id: promotionId
    })
    return response.data
  },

  /**
   * Retire ce profil d'un utilisateur
   */
  async removeFromUser(profileId: number, userId: number): Promise<any> {
    const response = await api.post(`/api/core/profiles/${profileId}/remove_from_user/`, {
      user_id: userId
    })
    return response.data
  },

  /**
   * Force la synchronisation de tous les utilisateurs de ce profil vers RADIUS
   * @deprecated Utiliser activateInRadius ou syncProfile à la place
   */
  async syncToRadius(profileId: number): Promise<any> {
    const response = await api.post(`/api/core/profiles/${profileId}/sync_to_radius/`)
    return response.data
  },

  // ============================================================================
  // RADIUS Sync API - Nouvelles méthodes de synchronisation
  // ============================================================================

  /**
   * Active un profil dans RADIUS et synchronise les données.
   * C'est la méthode principale à utiliser pour le bouton "Activer dans RADIUS".
   */
  async activateInRadius(profileId: number): Promise<{
    success: boolean
    message?: string
    profile_id?: number
    profile_name?: string
    groupname?: string
    users_synced?: number
    errors?: string[]
    error?: string
  }> {
    const response = await api.post(`/api/radius/sync/profile/${profileId}/activate/`)
    return response.data
  },

  /**
   * Désactive un profil dans RADIUS.
   */
  async deactivateInRadius(profileId: number): Promise<{
    success: boolean
    message?: string
    removed_group?: string
    affected_users?: string[]
    error?: string
  }> {
    const response = await api.post(`/api/radius/sync/profile/${profileId}/deactivate/`)
    return response.data
  },

  /**
   * Synchronise un profil spécifique vers RADIUS (sans changer is_radius_enabled).
   */
  async syncProfile(profileId: number): Promise<{
    success: boolean
    profile_id?: number
    profile_name?: string
    group_sync?: {
      groupname: string
      reply_attributes: number
      check_attributes: number
      success: boolean
    }
    users_sync?: {
      total: number
      synced: number
      errors: any[]
    }
    errors?: string[]
    error?: string
  }> {
    const response = await api.post(`/api/radius/sync/profile/${profileId}/sync/`)
    return response.data
  },

  /**
   * Synchronise tous les profils actifs vers RADIUS.
   */
  async syncAllProfiles(): Promise<{
    success: boolean
    total_profiles: number
    synced_profiles: number
    errors: any[]
    details: any[]
  }> {
    const response = await api.post('/api/radius/sync/all-profiles/')
    return response.data
  },

  /**
   * Synchronise tous les utilisateurs vers leurs groupes RADIUS.
   */
  async syncAllUsers(): Promise<{
    success: boolean
    total: number
    assigned: number
    no_profile: number
    errors: any[]
  }> {
    const response = await api.post('/api/radius/sync/all-users/')
    return response.data
  },

  /**
   * Synchronisation complète: tous les profils + tous les utilisateurs.
   */
  async syncFull(): Promise<{
    success: boolean
    profiles: {
      total: number
      synced: number
      errors: number
    }
    users: {
      total: number
      assigned: number
      no_profile: number
      errors: number
    }
  }> {
    const response = await api.post('/api/radius/sync/full/')
    return response.data
  },

  /**
   * Retourne le statut global de synchronisation RADIUS.
   */
  async getSyncStatus(): Promise<{
    profiles: {
      total: number
      synced: number
      pending: number
    }
    users: {
      total_activated: number
      in_radius_groups: number
    }
    last_check: string
  }> {
    const response = await api.get('/api/radius/sync/status/')
    return response.data
  }
}
