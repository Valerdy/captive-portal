import api from './api'
import type { Device, PaginatedResponse } from '@/types'

export const deviceService = {
  /**
   * Obtenir tous les devices
   */
  async getDevices(): Promise<PaginatedResponse<Device>> {
    const response = await api.get<PaginatedResponse<Device>>('/api/core/devices/')
    return response.data
  },

  /**
   * Obtenir les devices actifs
   */
  async getActiveDevices(): Promise<Device[]> {
    const response = await api.get<Device[]>('/api/core/devices/active/')
    return response.data
  },

  /**
   * Désactiver un device
   */
  async deactivateDevice(deviceId: number): Promise<{ status: string }> {
    const response = await api.post(`/api/core/devices/${deviceId}/deactivate/`)
    return response.data
  }
}
