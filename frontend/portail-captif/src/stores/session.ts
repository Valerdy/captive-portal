import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sessionService } from '@/services/session.service'
import type { Session, SessionStatistics } from '@/types'
import { getErrorMessage } from '@/services/api'

export const useSessionStore = defineStore('session', () => {
  // State
  const sessions = ref<Session[]>([])
  const activeSessions = ref<Session[]>([])
  const statistics = ref<SessionStatistics | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchSessions() {
    isLoading.value = true
    error.value = null

    try {
      const response = await sessionService.getSessions()
      sessions.value = response.results
      return response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchActiveSessions() {
    isLoading.value = true
    error.value = null

    try {
      activeSessions.value = await sessionService.getActiveSessions()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchStatistics() {
    isLoading.value = true
    error.value = null

    try {
      statistics.value = await sessionService.getStatistics()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function terminateSession(sessionId: number) {
    isLoading.value = true
    error.value = null

    try {
      await sessionService.terminateSession(sessionId)
      // Rafraîchir les données
      await fetchSessions()
      await fetchActiveSessions()
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
    sessions,
    activeSessions,
    statistics,
    isLoading,
    error,

    // Actions
    fetchSessions,
    fetchActiveSessions,
    fetchStatistics,
    terminateSession,
    clearError
  }
})
