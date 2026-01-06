<script setup lang="ts">
interface Props {
  message: string
  dismissible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  dismissible: false
})

const emit = defineEmits<{
  dismiss: []
}>()

function handleDismiss() {
  emit('dismiss')
}
</script>

<template>
  <div class="error-alert">
    <div class="error-glow"></div>
    <div class="error-icon-wrapper">
      <svg class="error-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" />
        <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      </svg>
    </div>
    <span class="error-message">{{ message }}</span>
    <button v-if="dismissible" @click="handleDismiss" class="error-close" aria-label="Fermer">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.error-alert {
  background: rgba(229, 50, 18, 0.1);
  border: 1px solid rgba(229, 50, 18, 0.3);
  padding: 1rem 1.25rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
  overflow: hidden;
  animation: slideDown 0.3s ease-out;
  box-shadow: 0 4px 20px rgba(229, 50, 18, 0.15);
}

.error-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 80px;
  height: 100%;
  background: linear-gradient(90deg, rgba(229, 50, 18, 0.15) 0%, transparent 100%);
  pointer-events: none;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.error-icon-wrapper {
  width: 36px;
  height: 36px;
  background: rgba(229, 50, 18, 0.15);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.error-icon {
  width: 20px;
  height: 20px;
  color: #e53212;
}

.error-message {
  flex: 1;
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.9);
}

.error-close {
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

.error-close svg {
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.5);
}

.error-close:hover {
  background: #e53212;
  border-color: #e53212;
}

.error-close:hover svg {
  color: white;
}
</style>
