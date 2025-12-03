import api from './api'

export interface Promotion {
  id: number
  name: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

class PromotionService {
  /**
   * Get all active promotions
   */
  async getPromotions(): Promise<Promotion[]> {
    const response = await api.get<Promotion[]>('/api/core/promotions/')
    return response.data
  }

  /**
   * Get promotion by ID
   */
  async getPromotion(id: number): Promise<Promotion> {
    const response = await api.get<Promotion>(`/api/core/promotions/${id}/`)
    return response.data
  }
}

export default new PromotionService()
