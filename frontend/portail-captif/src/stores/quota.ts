import { defineStore } from 'pinia'
import { ref } from 'vue'
import { quotaService } from '@/services/quota.service'
import type { UserQuota } from '@/types'
import { getErrorMessage } from '@/services/api'

export const useQuotaStore = defineStore('quota', () => {
  // State
  const quotas = ref<UserQuota[]>([])
  const currentQuota = ref<UserQuota | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const totalCount = ref(0)

  // Actions
  async function fetchQuotas() {
    isLoading.value = true
    error.value = null

    try {
      const response = await quotaService.getQuotas()
      quotas.value = response.results
      totalCount.value = response.count
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchQuotaById(quotaId: number) {
    isLoading.value = true
    error.value = null

    try {
      currentQuota.value = await quotaService.getQuotaById(quotaId)
      return currentQuota.value
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createQuota(quotaData: Partial<UserQuota>) {
    isLoading.value = true
    error.value = null

    try {
      const newQuota = await quotaService.createQuota(quotaData)
      quotas.value.unshift(newQuota)
      totalCount.value++
      return newQuota
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createQuotaForUser(userId: number, limits?: {
    daily_limit?: number
    weekly_limit?: number
    monthly_limit?: number
  }) {
    isLoading.value = true
    error.value = null

    try {
      const newQuota = await quotaService.createQuotaForUser(userId, limits)
      quotas.value.unshift(newQuota)
      totalCount.value++
      return newQuota
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateQuota(quotaId: number, quotaData: Partial<UserQuota>) {
    isLoading.value = true
    error.value = null

    try {
      const updatedQuota = await quotaService.updateQuota(quotaId, quotaData)

      // Mettre à jour dans la liste
      const index = quotas.value.findIndex(q => q.id === quotaId)
      if (index !== -1) {
        quotas.value[index] = updatedQuota
      }

      // Mettre à jour currentQuota si c'est le même
      if (currentQuota.value?.id === quotaId) {
        currentQuota.value = updatedQuota
      }

      return updatedQuota
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteQuota(quotaId: number) {
    isLoading.value = true
    error.value = null

    try {
      await quotaService.deleteQuota(quotaId)

      // Supprimer de la liste
      quotas.value = quotas.value.filter(q => q.id !== quotaId)
      totalCount.value--

      // Réinitialiser currentQuota si c'est celui qui est supprimé
      if (currentQuota.value?.id === quotaId) {
        currentQuota.value = null
      }
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function resetDaily(quotaId: number) {
    isLoading.value = true
    error.value = null

    try {
      const updatedQuota = await quotaService.resetDaily(quotaId)

      // Mettre à jour dans la liste
      const index = quotas.value.findIndex(q => q.id === quotaId)
      if (index !== -1) {
        quotas.value[index] = updatedQuota
      }

      return updatedQuota
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function resetWeekly(quotaId: number) {
    isLoading.value = true
    error.value = null

    try {
      const updatedQuota = await quotaService.resetWeekly(quotaId)

      // Mettre à jour dans la liste
      const index = quotas.value.findIndex(q => q.id === quotaId)
      if (index !== -1) {
        quotas.value[index] = updatedQuota
      }

      return updatedQuota
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function resetMonthly(quotaId: number) {
    isLoading.value = true
    error.value = null

    try {
      const updatedQuota = await quotaService.resetMonthly(quotaId)

      // Mettre à jour dans la liste
      const index = quotas.value.findIndex(q => q.id === quotaId)
      if (index !== -1) {
        quotas.value[index] = updatedQuota
      }

      return updatedQuota
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function resetAll(quotaId: number) {
    isLoading.value = true
    error.value = null

    try {
      const updatedQuota = await quotaService.resetAll(quotaId)

      // Mettre à jour dans la liste
      const index = quotas.value.findIndex(q => q.id === quotaId)
      if (index !== -1) {
        quotas.value[index] = updatedQuota
      }

      return updatedQuota
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchExceededQuotas() {
    isLoading.value = true
    error.value = null

    try {
      quotas.value = await quotaService.getExceededQuotas()
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
    quotas,
    currentQuota,
    isLoading,
    error,
    totalCount,
    // Actions
    fetchQuotas,
    fetchQuotaById,
    createQuota,
    createQuotaForUser,
    updateQuota,
    deleteQuota,
    resetDaily,
    resetWeekly,
    resetMonthly,
    resetAll,
    fetchExceededQuotas,
    clearError
  }
})
