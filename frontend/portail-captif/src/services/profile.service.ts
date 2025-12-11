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
  }
}
