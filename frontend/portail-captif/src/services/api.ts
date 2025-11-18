import axios, type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { APIError } from '@/types'

// Configuration de l'URL de base de l'API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Création de l'instance axios
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000 // 10 secondes
})

// Intercepteur de requête pour ajouter le token JWT
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Intercepteur de réponse pour gérer les erreurs et le refresh token
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<APIError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Si l'erreur est 401 (Unauthorized) et qu'on n'a pas déjà retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          // Tentative de refresh du token
          const response = await axios.post(`${API_BASE_URL}/api/core/auth/token/refresh/`, {
            refresh: refreshToken
          })

          const { access } = response.data
          localStorage.setItem('access_token', access)

          // Retry la requête originale avec le nouveau token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access}`
          }
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Si le refresh échoue, déconnecter l'utilisateur
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api

// Helper pour extraire les messages d'erreur
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<APIError>
    if (axiosError.response?.data) {
      const data = axiosError.response.data
      if (data.detail) return data.detail
      if (data.message) return data.message
      if (data.errors) {
        const firstError = Object.values(data.errors)[0]
        return Array.isArray(firstError) ? firstError[0] : String(firstError)
      }
    }
    return axiosError.message
  }
  return 'Une erreur inattendue s\'est produite'
}
