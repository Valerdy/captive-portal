import api from './api'
import type { Promotion } from '@/types'

export const promotionService = {
  async list(params: { is_active?: boolean } = {}): Promise<Promotion[]> {
    const response = await api.get('/api/core/promotions/', { params })
    const data: any = response.data
    // Normaliser la réponse pour supporter la pagination DRF
    if (Array.isArray(data)) return data as Promotion[]
    if (data?.results) return data.results as Promotion[]
    return []
  },

  async active(): Promise<Promotion[]> {
    // Endpoint public pour lister les promotions actives (utilisé pour l'inscription)
    const response = await api.get<Promotion[]>('/api/core/promotions/active/')
    return response.data
  },

  async create(data: Partial<Promotion>): Promise<Promotion> {
    const response = await api.post<Promotion>('/api/core/promotions/', data)
    return response.data
  },

  async update(id: number, data: Partial<Promotion>): Promise<Promotion> {
    const response = await api.patch<Promotion>(`/api/core/promotions/${id}/`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/core/promotions/${id}/`)
  },

  async toggleStatus(id: number): Promise<Promotion> {
    const response = await api.post<Promotion>(`/api/core/promotions/${id}/toggle_status/`)
    return response.data
  },

  async activate(id: number): Promise<any> {
    const response = await api.post(`/api/core/promotions/${id}/activate/`)
    return response.data
  },

  async deactivate(id: number): Promise<any> {
    const response = await api.post(`/api/core/promotions/${id}/deactivate/`)
    return response.data
  },

  async getUsers(id: number): Promise<any> {
    const response = await api.get(`/api/core/promotions/${id}/users/`)
    return response.data
  },

  async activateUsers(id: number): Promise<any> {
    const response = await api.post(`/api/core/promotions/${id}/activate_users/`)
    return response.data
  },

  async deactivateUsers(id: number): Promise<any> {
    const response = await api.post(`/api/core/promotions/${id}/deactivate_users/`)
    return response.data
  }
}

