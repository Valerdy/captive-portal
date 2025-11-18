import api from './api'
import type { Voucher, VoucherValidation, PaginatedResponse } from '@/types'

export const voucherService = {
  /**
   * Obtenir tous les vouchers
   */
  async getVouchers(): Promise<PaginatedResponse<Voucher>> {
    const response = await api.get<PaginatedResponse<Voucher>>('/api/core/vouchers/')
    return response.data
  },

  /**
   * Obtenir les vouchers actifs
   */
  async getActiveVouchers(): Promise<Voucher[]> {
    const response = await api.get<Voucher[]>('/api/core/vouchers/active/')
    return response.data
  },

  /**
   * Valider un code voucher
   */
  async validateVoucher(code: string): Promise<VoucherValidation> {
    const response = await api.post<VoucherValidation>('/api/core/vouchers/validate/', { code })
    return response.data
  },

  /**
   * Utiliser un code voucher
   */
  async redeemVoucher(code: string): Promise<{ status: string; message: string; duration: number }> {
    const response = await api.post('/api/core/vouchers/redeem/', { code })
    return response.data
  }
}
