<script setup lang="ts">
interface Props {
  modelValue: boolean
  title?: string
  maxWidth?: string
}

const props = withDefaults(defineProps<Props>(), {
  maxWidth: '500px'
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
}>()

function closeModal() {
  emit('update:modelValue', false)
  emit('close')
}

function handleOverlayClick(event: MouseEvent) {
  if (event.target === event.currentTarget) {
    closeModal()
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click="handleOverlayClick">
        <div class="modal-content" :style="{ maxWidth }" @click.stop>
          <button @click="closeModal" class="modal-close" aria-label="Fermer">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M18 6L6 18M6 6l12 12"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              />
            </svg>
          </button>

          <div v-if="title" class="modal-header">
            <h3>{{ title }}</h3>
          </div>

          <div class="modal-body">
            <slot></slot>
          </div>

          <div v-if="$slots.footer" class="modal-footer">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 24px;
  padding: 2.5rem;
  width: 100%;
  position: relative;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
}

.modal-close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  background: #f3f4f6;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.modal-close svg {
  width: 20px;
  height: 20px;
  color: #6b7280;
}

.modal-close:hover {
  background: #dc2626;
  transform: rotate(90deg);
}

.modal-close:hover svg {
  color: white;
}

.modal-header {
  margin-bottom: 1.5rem;
  padding-right: 2rem;
}

.modal-header h3 {
  color: #111827;
  font-size: 1.75rem;
  font-weight: 800;
  margin: 0;
}

.modal-body {
  color: #374151;
}

.modal-footer {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: translateY(40px) scale(0.9);
}

/* Responsive */
@media (max-width: 768px) {
  .modal-content {
    padding: 2rem 1.5rem;
  }

  .modal-header h3 {
    font-size: 1.5rem;
  }
}
</style>
