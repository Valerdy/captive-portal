<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { RouterView } from 'vue-router';
import ToastNotification from './components/ToastNotification.vue';

const isAppLoading = ref(true);

onMounted(() => {
  // Brief initial loading animation
  setTimeout(() => {
    isAppLoading.value = false;
  }, 800);
});
</script>

<template>
  <!-- Initial App Loading Screen -->
  <Transition name="fade">
    <div v-if="isAppLoading" class="app-loading-screen">
      <div class="loading-content">
        <div class="loading-logo">
          <div class="logo-ring outer"></div>
          <div class="logo-ring inner"></div>
          <div class="logo-center"></div>
        </div>
        <div class="loading-text">Chargement...</div>
      </div>
    </div>
  </Transition>

  <ToastNotification />
  <RouterView v-if="!isAppLoading" />
</template>

<style scoped>
.app-loading-screen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a0a12 0%, #0f0f1a 50%, #1a1a2e 100%);
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.loading-logo {
  position: relative;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-ring {
  position: absolute;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
}

.logo-ring.outer {
  width: 100%;
  height: 100%;
  border-top-color: #F29400;
  border-right-color: #F29400;
  animation: spin 1s linear infinite;
}

.logo-ring.inner {
  width: 60%;
  height: 60%;
  border-top-color: #008ecf;
  border-left-color: #008ecf;
  animation: spin 0.6s linear infinite reverse;
}

.logo-center {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #F29400 0%, #e53212 100%);
  animation: pulse 1s ease-in-out infinite;
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.5);
}

.loading-text {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 0.1em;
  text-transform: uppercase;
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

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
