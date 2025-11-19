<script setup lang="ts">
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()

function getIcon(type: string) {
  switch (type) {
    case 'success':
      return `<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`
    case 'error':
      return `<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>`
    case 'warning':
      return `<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>`
    default: // info
      return `<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><line x1="12" y1="16" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="12" y1="8" x2="12.01" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>`
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="notification in notificationStore.notifications"
          :key="notification.id"
          :class="['toast', `toast-${notification.type}`]"
          @click="notificationStore.removeNotification(notification.id)"
        >
          <svg
            class="toast-icon"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            v-html="getIcon(notification.type)"
          ></svg>
          <span class="toast-message">{{ notification.message }}</span>
          <button
            class="toast-close"
            @click.stop="notificationStore.removeNotification(notification.id)"
            aria-label="Fermer"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M18 6L6 18M6 6l12 12"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              />
            </svg>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 400px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  pointer-events: auto;
  min-width: 300px;
  transition: all 0.3s ease;
  border-left: 4px solid;
}

.toast:hover {
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.25);
  transform: translateX(-4px);
}

.toast-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.toast-message {
  flex: 1;
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.4;
}

.toast-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.toast-close svg {
  width: 18px;
  height: 18px;
}

.toast-close:hover {
  background: rgba(0, 0, 0, 0.05);
}

/* Toast types */
.toast-success {
  border-left-color: #10b981;
}

.toast-success .toast-icon,
.toast-success .toast-close {
  color: #10b981;
}

.toast-success .toast-message {
  color: #065f46;
}

.toast-error {
  border-left-color: #dc2626;
}

.toast-error .toast-icon,
.toast-error .toast-close {
  color: #dc2626;
}

.toast-error .toast-message {
  color: #991b1b;
}

.toast-warning {
  border-left-color: #f59e0b;
}

.toast-warning .toast-icon,
.toast-warning .toast-close {
  color: #f59e0b;
}

.toast-warning .toast-message {
  color: #92400e;
}

.toast-info {
  border-left-color: #3b82f6;
}

.toast-info .toast-icon,
.toast-info .toast-close {
  color: #3b82f6;
}

.toast-info .toast-message {
  color: #1e3a8a;
}

/* Transitions */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100px) scale(0.8);
}

/* Responsive */
@media (max-width: 768px) {
  .toast-container {
    right: 0.5rem;
    left: 0.5rem;
    max-width: none;
  }

  .toast {
    min-width: 0;
  }
}
</style>
