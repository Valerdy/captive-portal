import { defineStore } from 'pinia'
import { ref } from 'vue'
import { profileService } from '@/services/profile.service'
import type { Profile } from '@/types'

function getErrorMessage(error: any): string {
  if (error?.response?.data?.detail) {
    return error.response.data.detail
  }
  if (error?.response?.data?.message) {
    return error.response.data.message
  }
  if (error?.message) {
    return error.message
  }
  return 'Une erreur est survenue'
}

export const useProfileStore = defineStore('profile', () => {
  const profiles = ref<Profile[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchProfiles(params: { is_active?: boolean } = {}) {
    isLoading.value = true
    error.value = null
    try {
      profiles.value = await profileService.list(params)
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchActiveProfiles() {
    isLoading.value = true
    error.value = null
    try {
      profiles.value = await profileService.active()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createProfile(data: Partial<Profile>) {
    isLoading.value = true
    error.value = null
    try {
      const newProfile = await profileService.create(data)
      profiles.value.push(newProfile)
      return newProfile
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateProfile(id: number, data: Partial<Profile>) {
    isLoading.value = true
    error.value = null
    try {
      const updated = await profileService.update(id, data)
      const idx = profiles.value.findIndex(p => p.id === id)
      if (idx !== -1) {
        profiles.value[idx] = updated
      }
      return updated
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteProfile(id: number) {
    isLoading.value = true
    error.value = null
    try {
      await profileService.delete(id)
      profiles.value = profiles.value.filter(p => p.id !== id)
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getProfileUsers(id: number) {
    error.value = null
    try {
      const data = await profileService.getUsers(id)
      return data
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    }
  }

  async function getProfilePromotions(id: number) {
    error.value = null
    try {
      const data = await profileService.getPromotions(id)
      return data
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    profiles,
    isLoading,
    error,
    fetchProfiles,
    fetchActiveProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
    getProfileUsers,
    getProfilePromotions,
    clearError
  }
})
