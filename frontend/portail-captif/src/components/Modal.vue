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
          <!-- Glow effect -->
          <div class="modal-glow"></div>

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
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.modal-content {
  background: rgba(15, 15, 25, 0.95);
  border-radius: 20px;
  padding: 2.5rem;
  width: 100%;
  position: relative;
  border: 1px solid rgba(242, 148, 0, 0.2);
  box-shadow:
    0 25px 60px rgba(0, 0, 0, 0.5),
    0 0 40px rgba(242, 148, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

.modal-glow {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(242, 148, 0, 0.15) 0%, transparent 70%);
  pointer-events: none;
}

.modal-close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10;
}

.modal-close svg {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: #e53212;
  border-color: #e53212;
  transform: rotate(90deg);
  box-shadow: 0 0 20px rgba(229, 50, 18, 0.4);
}

.modal-close:hover svg {
  color: white;
}

.modal-header {
  margin-bottom: 1.5rem;
  padding-right: 3rem;
  position: relative;
}

.modal-header h3 {
  font-family: 'Orbitron', sans-serif;
  color: #ffffff;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.02em;
  text-shadow: 0 0 20px rgba(242, 148, 0, 0.3);
}

.modal-body {
  color: rgba(255, 255, 255, 0.8);
  font-family: 'Inter', sans-serif;
  position: relative;
  z-index: 1;
}

.modal-footer {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  position: relative;
  z-index: 1;
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
    font-size: 1.25rem;
  }
}
</style>
