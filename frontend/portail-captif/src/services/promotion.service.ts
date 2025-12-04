import api from './api'
import type { Promotion, PaginatedResponse } from '@/types'

export const promotionService = {
  /**
   * Récupérer toutes les promotions (admin only)
   */
  async getPromotions(): Promise<PaginatedResponse<Promotion>> {
    const response = await api.get<PaginatedResponse<Promotion>>('/api/core/promotions/')
    return response.data
  },

  /**
   * Récupérer une promotion par ID
   */
  async getPromotionById(promotionId: number): Promise<Promotion> {
    const response = await api.get<Promotion>(`/api/core/promotions/${promotionId}/`)
    return response.data
  },

  /**
   * Créer une nouvelle promotion (admin only)
   */
  async createPromotion(promotionData: Partial<Promotion>): Promise<Promotion> {
    const response = await api.post<Promotion>('/api/core/promotions/', promotionData)
    return response.data
  },

  /**
   * Mettre à jour une promotion
   */
  async updatePromotion(promotionId: number, promotionData: Partial<Promotion>): Promise<Promotion> {
    const response = await api.patch<Promotion>(`/api/core/promotions/${promotionId}/`, promotionData)
    return response.data
  },

  /**
   * Supprimer une promotion
   */
  async deletePromotion(promotionId: number): Promise<void> {
    await api.delete(`/api/core/promotions/${promotionId}/`)
  },

  /**
   * Activer tous les utilisateurs d'une promotion dans RADIUS
   */
  async activatePromotionUsers(promotionId: number): Promise<any> {
    const response = await api.post(`/api/core/promotions/${promotionId}/activate_users/`)
    return response.data
  },

  /**
   * Désactiver tous les utilisateurs d'une promotion dans RADIUS
   */
  async deactivatePromotionUsers(promotionId: number): Promise<any> {
    const response = await api.post(`/api/core/promotions/${promotionId}/deactivate_users/`)
    return response.data
  },

  /**
   * Toggle le statut de la promotion (active/inactive)
   */
  async togglePromotionStatus(promotionId: number): Promise<any> {
    const response = await api.post(`/api/core/promotions/${promotionId}/toggle_status/`)
    return response.data
  }
}
