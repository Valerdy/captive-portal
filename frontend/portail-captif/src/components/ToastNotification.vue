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
          <div class="toast-glow"></div>
          <div class="toast-icon-wrapper">
            <svg
              class="toast-icon"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              v-html="getIcon(notification.type)"
            ></svg>
          </div>
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.toast-container {
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 420px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: rgba(15, 15, 25, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 14px;
  box-shadow:
    0 15px 40px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  cursor: pointer;
  pointer-events: auto;
  min-width: 320px;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.toast::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.toast:hover {
  transform: translateX(-8px);
  box-shadow:
    0 20px 50px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.toast-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100px;
  height: 100%;
  pointer-events: none;
  opacity: 0.3;
}

.toast-icon-wrapper {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.toast-icon {
  width: 20px;
  height: 20px;
}

.toast-message {
  flex: 1;
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.9);
}

.toast-close {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  padding: 0.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.toast-close svg {
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.4);
}

.toast-close:hover {
  background: rgba(255, 255, 255, 0.1);
}

.toast-close:hover svg {
  color: rgba(255, 255, 255, 0.8);
}

/* Toast types */
.toast-success::before {
  background: linear-gradient(180deg, #10b981 0%, #059669 100%);
}

.toast-success .toast-icon-wrapper {
  background: rgba(16, 185, 129, 0.15);
}

.toast-success .toast-icon {
  color: #10b981;
}

.toast-success .toast-glow {
  background: linear-gradient(90deg, rgba(16, 185, 129, 0.2) 0%, transparent 100%);
}

.toast-error::before {
  background: linear-gradient(180deg, #e53212 0%, #dc2626 100%);
}

.toast-error .toast-icon-wrapper {
  background: rgba(229, 50, 18, 0.15);
}

.toast-error .toast-icon {
  color: #e53212;
}

.toast-error .toast-glow {
  background: linear-gradient(90deg, rgba(229, 50, 18, 0.2) 0%, transparent 100%);
}

.toast-warning::before {
  background: linear-gradient(180deg, #F29400 0%, #ea580c 100%);
}

.toast-warning .toast-icon-wrapper {
  background: rgba(242, 148, 0, 0.15);
}

.toast-warning .toast-icon {
  color: #F29400;
}

.toast-warning .toast-glow {
  background: linear-gradient(90deg, rgba(242, 148, 0, 0.2) 0%, transparent 100%);
}

.toast-info::before {
  background: linear-gradient(180deg, #008ecf 0%, #0284c7 100%);
}

.toast-info .toast-icon-wrapper {
  background: rgba(0, 142, 207, 0.15);
}

.toast-info .toast-icon {
  color: #008ecf;
}

.toast-info .toast-glow {
  background: linear-gradient(90deg, rgba(0, 142, 207, 0.2) 0%, transparent 100%);
}

/* Transitions */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100px) scale(0.9);
}

/* Responsive */
@media (max-width: 768px) {
  .toast-container {
    right: 0.75rem;
    left: 0.75rem;
    max-width: none;
  }

  .toast {
    min-width: 0;
  }
}
</style>
