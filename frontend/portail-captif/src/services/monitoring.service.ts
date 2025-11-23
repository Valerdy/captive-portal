import api from './api'

export interface MonitoringMetrics {
  cpu_usage: number
  memory_usage: number
  bandwidth: number
  active_connections: number
  active_devices: number
  recent_activity: RecentActivity[]
  psutil_available: boolean
  timestamp: string
}

export interface RecentActivity {
  time: string
  user: string
  action: string
  ip: string
}

export const monitoringService = {
  /**
   * Récupérer les métriques de monitoring en temps réel (admin only)
   */
  async getMetrics(): Promise<MonitoringMetrics> {
    const response = await api.get<MonitoringMetrics>('/api/core/admin/monitoring/metrics/')
    return response.data
  }
}
