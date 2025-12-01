import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/auth.service'
import type { User, LoginCredentials, RegisterData } from '@/types'
import { getErrorMessage } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  // Les tokens sont dans les cookies HttpOnly, on vérifie juste la présence de l'utilisateur
  const isAuthenticated = computed(() => !!user.value)
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

      // Sauvegarder uniquement l'utilisateur dans le state et localStorage
      // Les tokens sont automatiquement stockés dans les cookies HttpOnly par le backend
      user.value = response.user
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

      // Sauvegarder uniquement l'utilisateur
      // Les tokens sont automatiquement stockés dans les cookies HttpOnly par le backend
      user.value = response.user
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
      // Le backend gère le refresh token depuis les cookies
      await authService.logout()
    } catch (err) {
      console.error('Logout error:', err)
      // On continue même si la requête échoue
    } finally {
      // Nettoyer le state et localStorage
      // Les cookies sont automatiquement supprimés par le backend
      user.value = null
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

      // Sauvegarder uniquement l'utilisateur
      // Les tokens sont automatiquement stockés dans les cookies HttpOnly par le backend
      user.value = response.user
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
    // Restaurer uniquement les informations utilisateur depuis localStorage
    // Les tokens sont dans les cookies HttpOnly et gérés automatiquement
    const storedUser = localStorage.getItem('user')

    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
      } catch {
        // Si le parsing échoue, nettoyer
        localStorage.removeItem('user')
      }
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    user,
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
