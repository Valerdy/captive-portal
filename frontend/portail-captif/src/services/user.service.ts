import api from './api'
import type { User, PaginatedResponse, RadiusActivationResponse } from '@/types'

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
   * Activer un utilisateur (statut=1) dans RADIUS
   */
  async activateUserRadius(userId: number): Promise<void> {
    await api.post(`/api/core/users/${userId}/activate_radius/`)
  },

  /**
   * Désactiver un utilisateur (statut=0) dans RADIUS
   */
  async deactivateUserRadius(userId: number): Promise<void> {
    await api.post(`/api/core/users/${userId}/deactivate_radius/`)
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
  }
}
