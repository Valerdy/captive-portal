import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/auth.service'
import type { User, LoginCredentials, RegisterData } from '@/types'
import { getErrorMessage } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isAdmin = computed(() => {
    // Use role_name if available, fallback to is_staff/is_superuser
    if (user.value?.role_name) {
      return user.value.role_name === 'admin'
    }
    return user.value?.is_staff || user.value?.is_superuser || false
  })
  const userRole = computed(() => user.value?.role_name || (isAdmin.value ? 'admin' : 'user'))

  // Actions
  async function login(credentials: LoginCredentials) {
    isLoading.value = true
    error.value = null

    try {
      const response = await authService.login(credentials)

      // Sauvegarder dans le state
      user.value = response.user
      accessToken.value = response.tokens.access
      refreshToken.value = response.tokens.refresh

      // Sauvegarder dans localStorage
      localStorage.setItem('access_token', response.tokens.access)
      localStorage.setItem('refresh_token', response.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(response.user))

      return response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function register(data: RegisterData) {
    isLoading.value = true
    error.value = null

    try {
      const response = await authService.register(data)

      // Sauvegarder dans le state
      user.value = response.user
      accessToken.value = response.tokens.access
      refreshToken.value = response.tokens.refresh

      // Sauvegarder dans localStorage
      localStorage.setItem('access_token', response.tokens.access)
      localStorage.setItem('refresh_token', response.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(response.user))

      return response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    isLoading.value = true
    error.value = null

    try {
      if (refreshToken.value) {
        await authService.logout(refreshToken.value)
      }
    } catch (err) {
      console.error('Logout error:', err)
      // On continue même si la requête échoue
    } finally {
      // Nettoyer le state et localStorage
      user.value = null
      accessToken.value = null
      refreshToken.value = null

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')

      isLoading.value = false
    }
  }

  async function fetchProfile() {
    isLoading.value = true
    error.value = null

    try {
      const profile = await authService.getProfile()
      user.value = profile
      localStorage.setItem('user', JSON.stringify(profile))
      return profile
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateProfile(data: Partial<User>) {
    isLoading.value = true
    error.value = null

    try {
      const updatedUser = await authService.updateProfile(data)
      user.value = updatedUser
      localStorage.setItem('user', JSON.stringify(updatedUser))
      return updatedUser
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function adminLogin(username: string, password: string) {
    isLoading.value = true
    error.value = null

    try {
      const response = await authService.login({ username, password })

      // Vérifier si l'utilisateur a les droits admin
      if (!response.user.is_staff && !response.user.is_superuser) {
        error.value = 'Accès refusé : droits administrateur requis'
        throw new Error('Accès refusé : droits administrateur requis')
      }

      // Sauvegarder dans le state
      user.value = response.user
      accessToken.value = response.tokens.access
      refreshToken.value = response.tokens.refresh

      // Sauvegarder dans localStorage
      localStorage.setItem('access_token', response.tokens.access)
      localStorage.setItem('refresh_token', response.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(response.user))

      return response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function changePassword(data: { current_password: string; new_password: string; confirm_password: string }) {
    isLoading.value = true
    error.value = null

    try {
      await authService.changePassword(data)
      return true
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function initializeAuth() {
    // Restaurer depuis localStorage au démarrage
    const storedToken = localStorage.getItem('access_token')
    const storedRefreshToken = localStorage.getItem('refresh_token')
    const storedUser = localStorage.getItem('user')

    if (storedToken && storedRefreshToken && storedUser) {
      accessToken.value = storedToken
      refreshToken.value = storedRefreshToken
      try {
        user.value = JSON.parse(storedUser)
      } catch {
        // Si le parsing échoue, nettoyer
        localStorage.clear()
      }
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    user,
    accessToken,
    refreshToken,
    isLoading,
    error,

    // Getters
    isAuthenticated,
    isAdmin,
    userRole,

    // Actions
    login,
    register,
    logout,
    fetchProfile,
    updateProfile,
    adminLogin,
    changePassword,
    initializeAuth,
    clearError
  }
})
