import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userService } from '@/services/user.service'
import type { User } from '@/types'
import { getErrorMessage } from '@/services/api'

export const useUserStore = defineStore('user', () => {
  // State
  const users = ref<User[]>([])
  const currentUser = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const totalCount = ref(0)

  // Actions
  async function fetchUsers() {
    isLoading.value = true
    error.value = null

    try {
      const response = await userService.getUsers()
      users.value = response.results
      totalCount.value = response.count
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUserById(userId: number) {
    isLoading.value = true
    error.value = null

    try {
      currentUser.value = await userService.getUserById(userId)
      return currentUser.value
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createUser(userData: Partial<User>) {
    isLoading.value = true
    error.value = null

    try {
      const newUser = await userService.createUser(userData)
      users.value.unshift(newUser)
      totalCount.value++
      return newUser
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateUser(userId: number, userData: Partial<User>) {
    isLoading.value = true
    error.value = null

    try {
      const updatedUser = await userService.updateUser(userId, userData)

      // Mettre à jour dans la liste
      const index = users.value.findIndex(u => u.id === userId)
      if (index !== -1) {
        users.value[index] = updatedUser
      }

      // Mettre à jour currentUser si c'est le même
      if (currentUser.value?.id === userId) {
        currentUser.value = updatedUser
      }

      return updatedUser
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteUser(userId: number) {
    isLoading.value = true
    error.value = null

    try {
      await userService.deleteUser(userId)

      // Retirer de la liste
      users.value = users.value.filter(u => u.id !== userId)
      totalCount.value--

      // Clear currentUser si c'était celui-là
      if (currentUser.value?.id === userId) {
        currentUser.value = null
      }
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getUserDevices(userId: number) {
    isLoading.value = true
    error.value = null

    try {
      return await userService.getUserDevices(userId)
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getUserSessions(userId: number) {
    isLoading.value = true
    error.value = null

    try {
      return await userService.getUserSessions(userId)
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function activateUsersRadius(userIds: number[]) {
    isLoading.value = true
    error.value = null

    try {
      const result = await userService.activateUsersRadius(userIds)

      // Mettre à jour les utilisateurs activés dans la liste
      result.activated_users.forEach((activatedUser) => {
        const index = users.value.findIndex(u => u.id === activatedUser.id)
        if (index !== -1) {
          users.value[index].is_radius_activated = true
        }
      })

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
    users.value = []
    currentUser.value = null
    error.value = null
    totalCount.value = 0
  }

  return {
    // State
    users,
    currentUser,
    isLoading,
    error,
    totalCount,

    // Actions
    fetchUsers,
    fetchUserById,
    createUser,
    updateUser,
    deleteUser,
    getUserDevices,
    getUserSessions,
    activateUsersRadius,
    clearError,
    resetState
  }
})
