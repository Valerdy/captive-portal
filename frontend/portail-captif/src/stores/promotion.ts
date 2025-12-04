import { defineStore } from 'pinia'
import { ref } from 'vue'
import { promotionService } from '@/services/promotion.service'
import type { Promotion } from '@/types'
import { getErrorMessage } from '@/services/api'

export const usePromotionStore = defineStore('promotion', () => {
  // State
  const promotions = ref<Promotion[]>([])
  const currentPromotion = ref<Promotion | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const totalCount = ref(0)

  // Actions
  async function fetchPromotions() {
    isLoading.value = true
    error.value = null

    try {
      const response = await promotionService.getPromotions()
      promotions.value = response.results
      totalCount.value = response.count
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchPromotionById(promotionId: number) {
    isLoading.value = true
    error.value = null

    try {
      currentPromotion.value = await promotionService.getPromotionById(promotionId)
      return currentPromotion.value
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createPromotion(promotionData: Partial<Promotion>) {
    isLoading.value = true
    error.value = null

    try {
      const newPromotion = await promotionService.createPromotion(promotionData)
      promotions.value.unshift(newPromotion)
      totalCount.value++
      return newPromotion
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updatePromotion(promotionId: number, promotionData: Partial<Promotion>) {
    isLoading.value = true
    error.value = null

    try {
      const updatedPromotion = await promotionService.updatePromotion(promotionId, promotionData)

      // Mettre à jour dans la liste
      const index = promotions.value.findIndex(p => p.id === promotionId)
      if (index !== -1) {
        promotions.value[index] = updatedPromotion
      }

      // Mettre à jour currentPromotion si c'est la même
      if (currentPromotion.value?.id === promotionId) {
        currentPromotion.value = updatedPromotion
      }

      return updatedPromotion
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deletePromotion(promotionId: number) {
    isLoading.value = true
    error.value = null

    try {
      await promotionService.deletePromotion(promotionId)

      // Retirer de la liste
      promotions.value = promotions.value.filter(p => p.id !== promotionId)
      totalCount.value--

      // Clear currentPromotion si c'était celui-là
      if (currentPromotion.value?.id === promotionId) {
        currentPromotion.value = null
      }
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function activatePromotionUsers(promotionId: number) {
    isLoading.value = true
    error.value = null

    try {
      const result = await promotionService.activatePromotionUsers(promotionId)
      return result
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deactivatePromotionUsers(promotionId: number) {
    isLoading.value = true
    error.value = null

    try {
      const result = await promotionService.deactivatePromotionUsers(promotionId)
      return result
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function togglePromotionStatus(promotionId: number) {
    isLoading.value = true
    error.value = null

    try {
      const result = await promotionService.togglePromotionStatus(promotionId)

      // Mettre à jour la promotion dans la liste
      const index = promotions.value.findIndex(p => p.id === promotionId)
      if (index !== -1) {
        promotions.value[index].is_active = result.is_active
      }

      return result
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

  function resetState() {
    promotions.value = []
    currentPromotion.value = null
    error.value = null
    totalCount.value = 0
  }

  return {
    // State
    promotions,
    currentPromotion,
    isLoading,
    error,
    totalCount,

    // Actions
    fetchPromotions,
    fetchPromotionById,
    createPromotion,
    updatePromotion,
    deletePromotion,
    activatePromotionUsers,
    deactivatePromotionUsers,
    togglePromotionStatus,
    clearError,
    resetState
  }
})
