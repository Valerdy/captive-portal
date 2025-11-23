import api from './api'
import type { BlockedSite, PaginatedResponse } from '@/types'

export const siteService = {
  /**
   * Récupérer tous les sites bloqués (admin only)
   */
  async getSites(): Promise<PaginatedResponse<BlockedSite>> {
    const response = await api.get<PaginatedResponse<BlockedSite>>('/api/core/blocked-sites/')
    return response.data
  },

  /**
   * Récupérer un site bloqué par ID
   */
  async getSiteById(siteId: number): Promise<BlockedSite> {
    const response = await api.get<BlockedSite>(`/api/core/blocked-sites/${siteId}/`)
    return response.data
  },

  /**
   * Créer un nouveau site bloqué
   */
  async createSite(siteData: Partial<BlockedSite>): Promise<BlockedSite> {
    const response = await api.post<BlockedSite>('/api/core/blocked-sites/', siteData)
    return response.data
  },

  /**
   * Mettre à jour un site bloqué
   */
  async updateSite(siteId: number, siteData: Partial<BlockedSite>): Promise<BlockedSite> {
    const response = await api.patch<BlockedSite>(`/api/core/blocked-sites/${siteId}/`, siteData)
    return response.data
  },

  /**
   * Supprimer un site bloqué
   */
  async deleteSite(siteId: number): Promise<void> {
    await api.delete(`/api/core/blocked-sites/${siteId}/`)
  },

  /**
   * Récupérer tous les sites bloqués actifs
   */
  async getActiveSites(): Promise<BlockedSite[]> {
    const response = await api.get<BlockedSite[]>('/api/core/blocked-sites/active/')
    return response.data
  },

  /**
   * Récupérer la blacklist
   */
  async getBlacklist(): Promise<BlockedSite[]> {
    const response = await api.get<BlockedSite[]>('/api/core/blocked-sites/blacklist/')
    return response.data
  },

  /**
   * Récupérer la whitelist
   */
  async getWhitelist(): Promise<BlockedSite[]> {
    const response = await api.get<BlockedSite[]>('/api/core/blocked-sites/whitelist/')
    return response.data
  }
}
