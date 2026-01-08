import api from './api'
import type { User, PaginatedResponse, RadiusActivationResponse } from '@/types'
import type { VerificationResult } from './profile.service'

export const userService = {
  /**
   * Récupérer tous les utilisateurs (admin only)
   */
  async getUsers(): Promise<PaginatedResponse<User>> {
    const response = await api.get<PaginatedResponse<User>>('/api/core/users/')
    return response.data
  },

  /**
   * Récupérer un utilisateur par ID
   */
  async getUserById(userId: number): Promise<User> {
    const response = await api.get<User>(`/api/core/users/${userId}/`)
    return response.data
  },

  /**
   * Créer un nouvel utilisateur (admin only)
   */
  async createUser(userData: Partial<User>): Promise<User> {
    const response = await api.post<User>('/api/core/users/', userData)
    return response.data
  },

  /**
   * Mettre à jour un utilisateur
   */
  async updateUser(userId: number, userData: Partial<User>): Promise<User> {
    const response = await api.patch<User>(`/api/core/users/${userId}/`, userData)
    return response.data
  },

  /**
   * Supprimer un utilisateur
   */
  async deleteUser(userId: number): Promise<void> {
    await api.delete(`/api/core/users/${userId}/`)
  },

  /**
   * Récupérer les devices d'un utilisateur
   */
  async getUserDevices(userId: number): Promise<any[]> {
    const response = await api.get(`/api/core/users/${userId}/devices/`)
    return response.data
  },

  /**
   * Récupérer les sessions d'un utilisateur
   */
  async getUserSessions(userId: number): Promise<any[]> {
    const response = await api.get(`/api/core/users/${userId}/sessions/`)
    return response.data
  },

  /**
   * Activer un ou plusieurs utilisateurs dans RADIUS (admin only)
   * L'utilisateur reste dans la table users (Django) ET est copié dans radcheck (RADIUS)
   */
  async activateUsersRadius(userIds: number[]): Promise<RadiusActivationResponse> {
    const response = await api.post<RadiusActivationResponse>(
      '/api/core/admin/users/activate/',
      { user_ids: userIds }
    )
    return response.data
  },

  /**
   * Activer un utilisateur individuellement dans RADIUS (toggle statut)
   * Permet l'accès Internet via RADIUS
   */
  async activateUserRadius(userId: number): Promise<any> {
    const response = await api.post(`/api/core/users/${userId}/activate_radius/`)
    return response.data
  },

  /**
   * Désactiver un utilisateur individuellement dans RADIUS (toggle statut)
   * Bloque l'accès Internet via RADIUS
   */
  async deactivateUserRadius(userId: number): Promise<any> {
    const response = await api.post(`/api/core/users/${userId}/deactivate_radius/`)
    return response.data
  },

  /**
   * Vérifie l'application du profil RADIUS pour un utilisateur spécifique.
   * Compare les attributs attendus (FreeRADIUS) avec les attributs réels (MikroTik).
   * Timeout augmenté car cette opération dépend de services externes (MikroTik Agent).
   */
  async verifyRadiusProfile(userId: number): Promise<VerificationResult> {
    const response = await api.get(`/api/radius/sync/verify/user/${userId}/`, {
      timeout: 60000 // 60 secondes pour les opérations de vérification
    })
    return response.data
  }
}
