<script setup lang="ts">
interface Props {
  size?: 'small' | 'medium' | 'large'
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  color: '#F29400'
})

const sizeClass = {
  small: '24px',
  medium: '48px',
  large: '72px'
}
</script>

<template>
  <div class="spinner-container">
    <div class="spinner-wrapper" :style="{ width: sizeClass[size], height: sizeClass[size] }">
      <!-- Outer ring -->
      <div class="spinner-ring outer" :style="{ borderTopColor: color }"></div>
      <!-- Inner ring -->
      <div class="spinner-ring inner" :style="{ borderTopColor: '#008ecf' }"></div>
      <!-- Center dot -->
      <div class="spinner-center" :style="{ background: color }"></div>
      <!-- Glow effect -->
      <div class="spinner-glow" :style="{ background: `radial-gradient(circle, ${color}40 0%, transparent 70%)` }"></div>
    </div>
  </div>
</template>

<style scoped>
.spinner-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.spinner-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner-ring {
  position: absolute;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
}

.spinner-ring.outer {
  width: 100%;
  height: 100%;
  border-top-color: #F29400;
  animation: spin 1s linear infinite;
}

.spinner-ring.inner {
  width: 60%;
  height: 60%;
  border-top-color: #008ecf;
  animation: spin 0.6s linear infinite reverse;
}

.spinner-center {
  width: 20%;
  height: 20%;
  border-radius: 50%;
  animation: pulse 1s ease-in-out infinite;
  box-shadow: 0 0 15px currentColor;
}

.spinner-glow {
  position: absolute;
  width: 150%;
  height: 150%;
  border-radius: 50%;
  animation: glow 2s ease-in-out infinite;
  pointer-events: none;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(0.8);
    opacity: 0.6;
  }
}

@keyframes glow {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.1);
  }
}
</style>
