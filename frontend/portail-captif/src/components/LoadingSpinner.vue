<script setup lang="ts">
interface Props {
  size?: 'small' | 'medium' | 'large'
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  color: '#dc2626'
})

const sizeClass = {
  small: '20px',
  medium: '40px',
  large: '60px'
}
</script>

<template>
  <div class="spinner-container">
    <div
      class="spinner"
      :style="{
        width: sizeClass[size],
        height: sizeClass[size],
        borderTopColor: color
      }"
    ></div>
  </div>
</template>

<style scoped>
.spinner-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.spinner {
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top-color: #dc2626;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
