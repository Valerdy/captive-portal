import { defineStore } from 'pinia'
import { ref } from 'vue'
import { promotionService } from '@/services/promotion.service'
import type { Promotion } from '@/types'
import { getErrorMessage } from '@/services/api'

export const usePromotionStore = defineStore('promotion', () => {
  const promotions = ref<Promotion[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchPromotions(params: { is_active?: boolean } = {}) {
    isLoading.value = true
    error.value = null
    try {
      promotions.value = await promotionService.list(params)
      return promotions.value
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchActivePromotions() {
    // Méthode publique pour récupérer les promotions actives (utilisée pour l'inscription)
    isLoading.value = true
    error.value = null
    try {
      const activePromotions = await promotionService.active()
      promotions.value = activePromotions
      return activePromotions
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createPromotion(data: Partial<Promotion>) {
    isLoading.value = true
    error.value = null
    try {
      const promo = await promotionService.create(data)
      promotions.value.push(promo)
      return promo
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function activatePromotion(id: number) {
    isLoading.value = true
    error.value = null
    try {
      await promotionService.activate(id)
      const idx = promotions.value.findIndex(p => p.id === id)
      if (idx !== -1) promotions.value[idx].is_active = true
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deactivatePromotion(id: number) {
    isLoading.value = true
    error.value = null
    try {
      await promotionService.deactivate(id)
      const idx = promotions.value.findIndex(p => p.id === id)
      if (idx !== -1) promotions.value[idx].is_active = false
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updatePromotion(id: number, data: Partial<Promotion>) {
    isLoading.value = true
    error.value = null
    try {
      const updated = await promotionService.update(id, data)
      const idx = promotions.value.findIndex(p => p.id === id)
      if (idx !== -1) promotions.value[idx] = updated
      return updated
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deletePromotion(id: number) {
    isLoading.value = true
    error.value = null
    try {
      await promotionService.delete(id)
      promotions.value = promotions.value.filter(p => p.id !== id)
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function togglePromotionStatus(id: number) {
    isLoading.value = true
    error.value = null
    try {
      const updated = await promotionService.toggleStatus(id)
      const idx = promotions.value.findIndex(p => p.id === id)
      if (idx !== -1) promotions.value[idx] = updated
      return updated
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getPromotionUsers(id: number) {
    error.value = null
    try {
      const data = await promotionService.getUsers(id)
      return data
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    }
  }

  async function activatePromotionUsers(id: number) {
    error.value = null
    try {
      const result = await promotionService.activate(id)
      await fetchPromotions() // Rafraîchir les promotions
      return result
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    }
  }

  async function deactivatePromotionUsers(id: number) {
    error.value = null
    try {
      const result = await promotionService.deactivate(id)
      await fetchPromotions() // Rafraîchir les promotions
      return result
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    promotions,
    isLoading,
    error,
    fetchPromotions,
    fetchActivePromotions,
    createPromotion,
    updatePromotion,
    deletePromotion,
    activatePromotion,
    deactivatePromotion,
    togglePromotionStatus,
    getPromotionUsers,
    activatePromotionUsers,
    deactivatePromotionUsers,
    clearError
  }
})

