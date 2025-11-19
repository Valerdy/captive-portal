<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const activeConnections = ref(45)
const bandwidth = ref(245)
const cpuUsage = ref(42)
const memoryUsage = ref(68)

const realtimeActivity = ref([
  { time: new Date().toLocaleTimeString(), user: 'john_doe', action: 'Connexion', ip: '192.168.1.105' },
  { time: new Date(Date.now() - 30000).toLocaleTimeString(), user: 'jane_smith', action: 'Téléchargement', ip: '192.168.1.110' },
  { time: new Date(Date.now() - 60000).toLocaleTimeString(), user: 'user123', action: 'Navigation', ip: '192.168.1.115' }
])

let updateInterval: any

onMounted(() => {
  if (!authStore.isAdmin) {
    router.push('/')
    return
  }

  // Simuler des mises à jour en temps réel
  updateInterval = setInterval(() => {
    bandwidth.value = Math.floor(Math.random() * 300) + 150
    cpuUsage.value = Math.floor(Math.random() * 50) + 30
    memoryUsage.value = Math.floor(Math.random() * 40) + 50
  }, 3000)
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
})

function goBack() {
  router.push('/admin/dashboard')
}
</script>

<template>
  <div class="admin-monitoring">
    <header class="page-header">
      <button @click="goBack" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 12H5M5 12l7 7m-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Retour
      </button>

      <div class="header-info">
        <h1>Monitoring en temps réel</h1>
        <p>Surveillance de l'activité réseau</p>
      </div>
    </header>

    <main class="page-content">
      <!-- Métriques en temps réel -->
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-icon pulse">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="metric-info">
            <h3>{{ activeConnections }}</h3>
            <p>Connexions actives</p>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon bandwidth">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="metric-info">
            <h3>{{ bandwidth }} MB/s</h3>
            <p>Bande passante</p>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon cpu">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2"/>
              <rect x="9" y="9" width="6" height="6" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="metric-info">
            <h3>{{ cpuUsage }}%</h3>
            <p>CPU</p>
          </div>
          <div class="progress-bar">
            <div class="progress" :style="{ width: cpuUsage + '%' }"></div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon memory">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="metric-info">
            <h3>{{ memoryUsage }}%</h3>
            <p>Mémoire</p>
          </div>
          <div class="progress-bar">
            <div class="progress memory-progress" :style="{ width: memoryUsage + '%' }"></div>
          </div>
        </div>
      </div>

      <!-- Activité en temps réel -->
      <div class="activity-card">
        <div class="activity-header">
          <h2>Activité récente</h2>
          <span class="live-indicator">
            <span class="pulse-dot"></span>
            En direct
          </span>
        </div>

        <div class="activity-list">
          <div v-for="(activity, index) in realtimeActivity" :key="index" class="activity-item">
            <div class="activity-time">{{ activity.time }}</div>
            <div class="activity-content">
              <span class="activity-user">{{ activity.user }}</span>
              <span class="activity-action">{{ activity.action }}</span>
              <span class="activity-ip">{{ activity.ip }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.admin-monitoring {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  padding: 2rem;
  color: white;
}

.page-header {
  max-width: 1400px;
  margin: 0 auto 2rem;
}

.back-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 0.75rem 1.25rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  margin-bottom: 1.5rem;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(-4px);
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.header-info h1 {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
}

.header-info p {
  color: rgba(255, 255, 255, 0.6);
}

.page-content {
  max-width: 1400px;
  margin: 0 auto;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.75rem;
  position: relative;
  overflow: hidden;
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.metric-icon svg {
  width: 30px;
  height: 30px;
}

.metric-icon.pulse {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
  }
  50% {
    box-shadow: 0 0 40px rgba(16, 185, 129, 0.6);
  }
}

.metric-icon.bandwidth {
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
}

.metric-icon.cpu {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.metric-icon.memory {
  background: rgba(168, 85, 247, 0.1);
  color: #a855f7;
}

.metric-info h3 {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.25rem;
}

.metric-info p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.progress-bar {
  margin-top: 1rem;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  transition: width 0.5s ease;
  border-radius: 3px;
}

.memory-progress {
  background: linear-gradient(90deg, #a855f7, #c084fc);
}

.activity-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2rem;
}

.activity-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.activity-header h2 {
  font-size: 1.5rem;
  font-weight: 800;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 12px;
  color: #10b981;
  font-size: 0.85rem;
  font-weight: 600;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.activity-item:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(249, 115, 22, 0.3);
}

.activity-time {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  min-width: 100px;
}

.activity-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.activity-user {
  font-weight: 600;
  color: #60a5fa;
}

.activity-action {
  color: rgba(255, 255, 255, 0.8);
}

.activity-ip {
  margin-left: auto;
  padding: 0.375rem 0.875rem;
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.2);
  border-radius: 8px;
  color: #fb923c;
  font-size: 0.85rem;
  font-family: monospace;
}

@media (max-width: 768px) {
  .admin-monitoring {
    padding: 1rem;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .activity-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .activity-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .activity-ip {
    margin-left: 0;
  }
}
</style>
