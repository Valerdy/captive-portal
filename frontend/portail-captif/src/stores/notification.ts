import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Notification {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
}

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref<Notification[]>([])

  function addNotification(
    message: string,
    type: Notification['type'] = 'info',
    duration: number = 5000
  ) {
    const id = Date.now().toString() + Math.random().toString(36).substring(2, 9)
    const notification: Notification = {
      id,
      message,
      type,
      duration
    }

    notifications.value.push(notification)

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, duration)
    }

    return id
  }

  function removeNotification(id: string) {
    const index = notifications.value.findIndex((n) => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }

  function success(message: string, duration?: number) {
    return addNotification(message, 'success', duration)
  }

  function error(message: string, duration?: number) {
    return addNotification(message, 'error', duration)
  }

  function warning(message: string, duration?: number) {
    return addNotification(message, 'warning', duration)
  }

  function info(message: string, duration?: number) {
    return addNotification(message, 'info', duration)
  }

  function clearAll() {
    notifications.value = []
  }

  return {
    notifications,
    addNotification,
    removeNotification,
    success,
    error,
    warning,
    info,
    clearAll
  }
})
