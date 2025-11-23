import { defineStore } from 'pinia'
import { ref } from 'vue'
import { siteService } from '@/services/site.service'
import type { BlockedSite } from '@/types'
import { getErrorMessage } from '@/services/api'

export const useSiteStore = defineStore('site', () => {
  // State
  const sites = ref<BlockedSite[]>([])
  const currentSite = ref<BlockedSite | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const totalCount = ref(0)

  // Actions
  async function fetchSites() {
    isLoading.value = true
    error.value = null

    try {
      const response = await siteService.getSites()
      sites.value = response.results
      totalCount.value = response.count
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchSiteById(siteId: number) {
    isLoading.value = true
    error.value = null

    try {
      currentSite.value = await siteService.getSiteById(siteId)
      return currentSite.value
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createSite(siteData: Partial<BlockedSite>) {
    isLoading.value = true
    error.value = null

    try {
      const newSite = await siteService.createSite(siteData)
      sites.value.unshift(newSite)
      totalCount.value++
      return newSite
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateSite(siteId: number, siteData: Partial<BlockedSite>) {
    isLoading.value = true
    error.value = null

    try {
      const updatedSite = await siteService.updateSite(siteId, siteData)

      // Mettre à jour dans la liste
      const index = sites.value.findIndex(s => s.id === siteId)
      if (index !== -1) {
        sites.value[index] = updatedSite
      }

      // Mettre à jour currentSite si c'est le même
      if (currentSite.value?.id === siteId) {
        currentSite.value = updatedSite
      }

      return updatedSite
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteSite(siteId: number) {
    isLoading.value = true
    error.value = null

    try {
      await siteService.deleteSite(siteId)

      // Supprimer de la liste
      sites.value = sites.value.filter(s => s.id !== siteId)
      totalCount.value--

      // Réinitialiser currentSite si c'est celui qui est supprimé
      if (currentSite.value?.id === siteId) {
        currentSite.value = null
      }
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchActiveSites() {
    isLoading.value = true
    error.value = null

    try {
      sites.value = await siteService.getActiveSites()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchBlacklist() {
    isLoading.value = true
    error.value = null

    try {
      sites.value = await siteService.getBlacklist()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchWhitelist() {
    isLoading.value = true
    error.value = null

    try {
      sites.value = await siteService.getWhitelist()
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
    sites,
    currentSite,
    isLoading,
    error,
    totalCount,
    // Actions
    fetchSites,
    fetchSiteById,
    createSite,
    updateSite,
    deleteSite,
    fetchActiveSites,
    fetchBlacklist,
    fetchWhitelist,
    clearError
  }
})
