import api from './api'
import type {
  LoginCredentials,
  LoginResponse,
  RegisterData,
  User
} from '@/types'

export const authService = {
  /**
   * Connexion utilisateur
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/api/core/auth/login/', credentials)
    return response.data
  },

  /**
   * Inscription utilisateur
   */
  async register(data: RegisterData): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/api/core/auth/register/', data)
    return response.data
  },

  /**
   * Déconnexion utilisateur
   */
  async logout(refreshToken: string): Promise<void> {
    await api.post('/api/core/auth/logout/', {
      refresh_token: refreshToken
    })
  },

  /**
   * Obtenir le profil utilisateur actuel
   */
  async getProfile(): Promise<User> {
    const response = await api.get<User>('/api/core/auth/profile/')
    return response.data
  },

  /**
   * Mettre à jour le profil utilisateur
   */
  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await api.patch<User>('/api/core/auth/profile/update/', data)
    return response.data
  },

  /**
   * Rafraîchir le token d'accès
   */
  async refreshToken(refreshToken: string): Promise<{ access: string; refresh: string }> {
    const response = await api.post('/api/core/auth/token/refresh/', {
      refresh: refreshToken
    })
    return response.data
  }
}
