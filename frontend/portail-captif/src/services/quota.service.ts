import api from './api'
import type { UserQuota, PaginatedResponse } from '@/types'

export const quotaService = {
  /**
   * Récupérer tous les quotas (admin only)
   */
  async getQuotas(): Promise<PaginatedResponse<UserQuota>> {
    const response = await api.get<PaginatedResponse<UserQuota>>('/api/core/user-quotas/')
    return response.data
  },

  /**
   * Récupérer un quota par ID
   */
  async getQuotaById(quotaId: number): Promise<UserQuota> {
    const response = await api.get<UserQuota>(`/api/core/user-quotas/${quotaId}/`)
    return response.data
  },

  /**
   * Créer un quota pour un utilisateur
   */
  async createQuota(quotaData: Partial<UserQuota>): Promise<UserQuota> {
    const response = await api.post<UserQuota>('/api/core/user-quotas/', quotaData)
    return response.data
  },

  /**
   * Créer un quota pour un utilisateur spécifique (avec user_id)
   */
  async createQuotaForUser(userId: number, limits?: {
    daily_limit?: number
    weekly_limit?: number
    monthly_limit?: number
  }): Promise<UserQuota> {
    const response = await api.post<UserQuota>('/api/core/user-quotas/create_for_user/', {
      user_id: userId,
      ...limits
    })
    return response.data
  },

  /**
   * Mettre à jour un quota
   */
  async updateQuota(quotaId: number, quotaData: Partial<UserQuota>): Promise<UserQuota> {
    const response = await api.patch<UserQuota>(`/api/core/user-quotas/${quotaId}/`, quotaData)
    return response.data
  },

  /**
   * Supprimer un quota
   */
  async deleteQuota(quotaId: number): Promise<void> {
    await api.delete(`/api/core/user-quotas/${quotaId}/`)
  },

  /**
   * Réinitialiser l'usage quotidien
   */
  async resetDaily(quotaId: number): Promise<UserQuota> {
    const response = await api.post<any>(`/api/core/user-quotas/${quotaId}/reset_daily/`)
    return response.data.quota
  },

  /**
   * Réinitialiser l'usage hebdomadaire
   */
  async resetWeekly(quotaId: number): Promise<UserQuota> {
    const response = await api.post<any>(`/api/core/user-quotas/${quotaId}/reset_weekly/`)
    return response.data.quota
  },

  /**
   * Réinitialiser l'usage mensuel
   */
  async resetMonthly(quotaId: number): Promise<UserQuota> {
    const response = await api.post<any>(`/api/core/user-quotas/${quotaId}/reset_monthly/`)
    return response.data.quota
  },

  /**
   * Réinitialiser tous les compteurs
   */
  async resetAll(quotaId: number): Promise<UserQuota> {
    const response = await api.post<any>(`/api/core/user-quotas/${quotaId}/reset_all/`)
    return response.data.quota
  },

  /**
   * Récupérer les quotas dépassés
   */
  async getExceededQuotas(): Promise<UserQuota[]> {
    const response = await api.get<UserQuota[]>('/api/core/user-quotas/exceeded/')
    return response.data
  }
}
