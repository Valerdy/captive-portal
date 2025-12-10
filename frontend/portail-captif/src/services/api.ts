import axios from 'axios'
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { APIError } from '@/types'

// Configuration de l'URL de base de l'API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Création de l'instance axios
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000, // 10 secondes
  withCredentials: true // Important: Permet l'envoi des cookies HttpOnly
})

// Intercepteur de requête - Plus besoin de gérer manuellement les tokens
// Les cookies HttpOnly sont automatiquement inclus dans les requêtes
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Les cookies sont automatiquement envoyés grâce à withCredentials: true
    // Pas besoin de gérer manuellement les tokens
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Intercepteur de réponse pour gérer les erreurs
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<APIError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Vérifier si on est sur une route publique
    const currentPath = window.location.pathname
    const publicRoutes = ['/login', '/register', '/', '/vouchers']
    const isPublicRoute = publicRoutes.some(route => currentPath === route || currentPath.startsWith(route + '/'))

    // Si l'erreur est 401 (Unauthorized) et qu'on n'a pas déjà retry
    // Ne pas essayer de rafraîchir le token si on est sur une route publique
    if (error.response?.status === 401 && !originalRequest._retry && !isPublicRoute) {
      originalRequest._retry = true

      try {
        // Tentative de refresh du token via l'endpoint refresh
        // Les cookies (refresh_token) sont automatiquement envoyés
        const response = await axios.post(
          `${API_BASE_URL}/api/core/auth/token/refresh/`,
          {}, // Body vide car le refresh_token est dans les cookies
          { withCredentials: true } // Important pour envoyer les cookies
        )

        // Si le refresh réussit, le serveur a mis à jour les cookies
        // On peut directement retry la requête originale
        if (response.status === 200) {
          return api(originalRequest)
        }

        throw new Error('Refresh token failed')
      } catch (refreshError) {
        // Si le refresh échoue, déconnecter l'utilisateur
        console.error('Échec du refresh token:', refreshError)
        localStorage.removeItem('user') // On garde seulement les métadonnées utilisateur
        
        // Rediriger vers /login seulement si on n'est pas déjà sur une route publique
        if (!isPublicRoute) {
          window.location.href = '/login'
        }
        
        return Promise.reject(refreshError)
      }
    }

    // Pour les routes publiques ou si le refresh n'est pas nécessaire, rejeter l'erreur directement
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
