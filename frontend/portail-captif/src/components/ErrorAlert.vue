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
    <svg class="error-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" />
      <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
    </svg>
    <span class="error-message">{{ message }}</span>
    <button v-if="dismissible" @click="handleDismiss" class="error-close" aria-label="Fermer">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.error-alert {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border: 2px solid #f87171;
  color: #991b1b;
  padding: 1rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
  animation: slideDown 0.3s ease-out;
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

.error-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: #dc2626;
}

.error-message {
  flex: 1;
  font-size: 0.95rem;
  line-height: 1.4;
}

.error-close {
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
  color: #991b1b;
}

.error-close svg {
  width: 18px;
  height: 18px;
}

.error-close:hover {
  background: rgba(153, 27, 27, 0.1);
}
</style>
