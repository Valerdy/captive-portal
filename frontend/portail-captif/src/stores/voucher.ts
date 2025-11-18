import { defineStore } from 'pinia'
import { ref } from 'vue'
import { voucherService } from '@/services/voucher.service'
import type { Voucher } from '@/types'
import { getErrorMessage } from '@/services/api'

export const useVoucherStore = defineStore('voucher', () => {
  // State
  const vouchers = ref<Voucher[]>([])
  const activeVouchers = ref<Voucher[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchVouchers() {
    isLoading.value = true
    error.value = null

    try {
      const response = await voucherService.getVouchers()
      vouchers.value = response.results
      return response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchActiveVouchers() {
    isLoading.value = true
    error.value = null

    try {
      activeVouchers.value = await voucherService.getActiveVouchers()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function validateVoucher(code: string) {
    isLoading.value = true
    error.value = null

    try {
      const validation = await voucherService.validateVoucher(code)
      return validation
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function redeemVoucher(code: string) {
    isLoading.value = true
    error.value = null

    try {
      const result = await voucherService.redeemVoucher(code)
      // Rafraîchir les vouchers
      await fetchVouchers()
      await fetchActiveVouchers()
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

  return {
    // State
    vouchers,
    activeVouchers,
    isLoading,
    error,

    // Actions
    fetchVouchers,
    fetchActiveVouchers,
    validateVoucher,
    redeemVoucher,
    clearError
  }
})
