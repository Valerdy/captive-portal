import { defineStore } from 'pinia'
import { ref } from 'vue'
import { deviceService } from '@/services/device.service'
import type { Device } from '@/types'
import { getErrorMessage } from '@/services/api'

export const useDeviceStore = defineStore('device', () => {
  // State
  const devices = ref<Device[]>([])
  const activeDevices = ref<Device[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchDevices() {
    isLoading.value = true
    error.value = null

    try {
      const response = await deviceService.getDevices()
      devices.value = response.results
      return response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchActiveDevices() {
    isLoading.value = true
    error.value = null

    try {
      activeDevices.value = await deviceService.getActiveDevices()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deactivateDevice(deviceId: number) {
    isLoading.value = true
    error.value = null

    try {
      await deviceService.deactivateDevice(deviceId)
      // Rafraîchir les données
      await fetchDevices()
      await fetchActiveDevices()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    devices,
    activeDevices,
    isLoading,
    error,

    // Actions
    fetchDevices,
    fetchActiveDevices,
    deactivateDevice,
    clearError
  }
})
