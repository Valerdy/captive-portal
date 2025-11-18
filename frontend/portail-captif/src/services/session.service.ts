import api from './api'
import type { Session, SessionStatistics, PaginatedResponse } from '@/types'

export const sessionService = {
  /**
   * Obtenir toutes les sessions
   */
  async getSessions(): Promise<PaginatedResponse<Session>> {
    const response = await api.get<PaginatedResponse<Session>>('/api/core/sessions/')
    return response.data
  },

  /**
   * Obtenir les sessions actives
   */
  async getActiveSessions(): Promise<Session[]> {
    const response = await api.get<Session[]>('/api/core/sessions/active/')
    return response.data
  },

  /**
   * Obtenir les statistiques de session
   */
  async getStatistics(): Promise<SessionStatistics> {
    const response = await api.get<SessionStatistics>('/api/core/sessions/statistics/')
    return response.data
  },

  /**
   * Terminer une session
   */
  async terminateSession(sessionId: number): Promise<{ status: string }> {
    const response = await api.post(`/api/core/sessions/${sessionId}/terminate/`)
    return response.data
  }
}
